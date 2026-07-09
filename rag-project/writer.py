import re
from datetime import date as _date
from datetime import timedelta
from pathlib import Path

import yaml
from langchain_core.messages import HumanMessage

from model import RetrospectiveEntry, TilEntry, WilEntry

BASE_DIR = Path(__file__).parent
TIL_DIR = BASE_DIR / "data" / "til"
WIL_DIR = BASE_DIR / "data" / "wil"
RETROSPECTIVE_DIR = BASE_DIR / "data" / "retrospective"

TIL_PROMPT_PATH = BASE_DIR / "prompts" / "til.md"
WIL_PROMPT_PATH = BASE_DIR / "prompts" / "wil.md"
RETROSPECTIVE_PROMPT_PATH = BASE_DIR / "prompts" / "retrospective.md"


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"\s+", "-", text.strip())
    slug = re.sub(r"[^\w\-가-힣]", "", slug)
    return slug[:max_len].strip("-") or "untitled"


def _fill(template: str, values: dict[str, str]) -> str:
    for placeholder, value in values.items():
        template = template.replace(placeholder, value)
    return template


def _generate(llm, prompt_template: str, values: dict[str, str]) -> str:
    """프롬프트 템플릿 안에 생성 지침과 자체 점검 기준을 같이 적어두고, 모델이 한 번의
    완성 안에서 초안 작성과 스스로 점검·교정을 끝내게 한다 (호출은 항상 1회)."""
    prompt = _fill(prompt_template, values)
    return llm.invoke([HumanMessage(content=prompt)]).content


def _save(out_path: Path, content: str) -> str:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return f"저장 완료: {out_path.relative_to(BASE_DIR)}\n\n{content}"


def _read_til_entries(paths: list[Path]) -> str:
    blocks = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        _, frontmatter, body = raw.split("---", 2)
        meta = yaml.safe_load(frontmatter)
        blocks.append(f"### {meta['date']} — {meta['topic']}\n{body.strip()}")
    return "\n\n".join(blocks)


def make_writer(llm):
    til_prompt = TIL_PROMPT_PATH.read_text(encoding="utf-8")
    wil_prompt = WIL_PROMPT_PATH.read_text(encoding="utf-8")
    retrospective_prompt = RETROSPECTIVE_PROMPT_PATH.read_text(encoding="utf-8")

    def write_til(
        topic: str,
        learned: str,
        stuck: str = "",
        related_concepts: list[str] | str | None = None,
    ) -> str:
        """오늘 학습 내용을 구조화해 data/til/에 저장한다(Today I Learned). 날짜는 서버가 직접 오늘 날짜로 채운다(LLM에 맡기지 않음)."""
        if isinstance(related_concepts, str):
            related_concepts = [c.strip() for c in related_concepts.split(",") if c.strip()]
        related_concepts = related_concepts or []
        today = _date.today()
        date_str = today.isoformat()

        entry = TilEntry(
            date=today,
            topic=topic,
            learned=learned,
            stuck=stuck or None,
            related_concepts=related_concepts,
        )

        body = _generate(llm, til_prompt, {
            "{date}": date_str,
            "{topic}": topic,
            "{learned}": learned,
            "{stuck}": stuck or "(없음)",
            "{related_concepts}": ", ".join(related_concepts) if related_concepts else "(없음)",
        })

        frontmatter = yaml.safe_dump(
            entry.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        )

        saved_content = f"---\n{frontmatter}---\n\n{body}\n"
        return _save(TIL_DIR / f"{date_str}-{_slugify(topic)}.md", saved_content)

    def write_wil(as_of: str | None = None) -> str:
        """data/til/*.md 중 이번 주(월요일 시작) 분량을 종합해 data/wil/{end}.md로 저장한다(Week I Learned).
        as_of를 안 주면 오늘을 기준일로 삼는다. 범위는 기준일이 속한 주의 월요일부터 기준일까지라서,
        주중(예: 금요일)에 호출하면 그 주 월~금만, 일요일에 호출하면 월~일 전체가 담긴다."""
        end = _date.fromisoformat(as_of) if as_of else _date.today()
        start = end - timedelta(days=end.weekday())      

        paths = []
        for path in sorted(TIL_DIR.glob("*.md")):
            try:
                d = _date.fromisoformat(path.stem[:10])  # 파일명이 "YYYY-MM-DD-키워드"라 앞 10자만 날짜
            except ValueError:
                continue
            if start <= d <= end:
                paths.append(path)

        if not paths:
            return f"{start}~{end} 사이 저장된 TIL이 없음"

        til_entries = _read_til_entries(paths)
        body = _generate(llm, wil_prompt, {"{til_entries}": til_entries})

        entry = WilEntry(
            start=start,
            end=end,
            source_files=[str(p.relative_to(BASE_DIR)) for p in paths],
        )
        frontmatter = yaml.safe_dump(
            entry.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        )

        saved_content = f"---\n{frontmatter}---\n\n{body}\n"
        return _save(WIL_DIR / f"{end.isoformat()}.md", saved_content)

    def write_retrospective(
        topic: str,
        difficulties: str,
        reflections: str,
        decisions: str = "",
        problem_solving: str = "",
        future_plans: str = "",
    ) -> str:
        """대화로 직접 엘리시트한 회고를 정리해 data/retrospective/에 저장한다.
        프로젝트 회고·학습 회고·전반적 회고 모두 가능 — wil_synthesize와 무관하게 독립적으로 동작한다.
        날짜는 서버가 직접 오늘 날짜로 채운다(LLM에 맡기지 않음)."""
        today = _date.today()
        date_str = today.isoformat()


        body = _generate(llm, retrospective_prompt, {
            "{topic}": topic,
            "{decisions}": decisions or "(없음)",
            "{problem_solving}": problem_solving or "(없음)",
            "{difficulties}": difficulties,
            "{reflections}": reflections,
            "{future_plans}": future_plans or "(없음)",
        })

        entry = RetrospectiveEntry(
            date=today,
            topic=topic,
            difficulties=difficulties,
            reflections=reflections,
            decisions=decisions or None,
            problem_solving=problem_solving or None,
            future_plans=future_plans or None,
        )
        frontmatter = yaml.safe_dump(
            entry.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        )

        saved_content = f"---\n{frontmatter}---\n\n# {topic}\n\n{body}\n"
        return _save(RETROSPECTIVE_DIR / f"{date_str}-{_slugify(topic)}.md", saved_content)

    return write_til, write_wil, write_retrospective
