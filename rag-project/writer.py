import re
from datetime import date as _date
from datetime import timedelta
from pathlib import Path

import yaml
from langchain_core.messages import HumanMessage

from model import JournalEntry

BASE_DIR = Path(__file__).parent
JOURNAL_DIR = BASE_DIR / "data" / "journal"
SYNTHESIS_DIR = BASE_DIR / "data" / "synthesis"
TIL_DIR = SYNTHESIS_DIR / "til"

DAILY_PROMPT_PATH = BASE_DIR / "prompts" / "daily.md"
WEEKLY_PROMPT_PATH = BASE_DIR / "prompts" / "weekly.md"
TIL_PROMPT_PATH = BASE_DIR / "prompts" / "til.md"


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"\s+", "-", text.strip())
    slug = re.sub(r"[^\w\-가-힣]", "", slug)
    return slug[:max_len].strip("-") or "untitled"


def _read_journal_entries(paths: list[Path]) -> str:
    blocks = []
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        _, frontmatter, body = raw.split("---", 2)
        meta = yaml.safe_load(frontmatter)
        blocks.append(f"### {meta['date']} — {meta['topic']}\n{body.strip()}")
    return "\n\n".join(blocks)


def make_writer(llm):
    def write_daily(
        topic: str,
        learned: str,
        stuck: str = "",
        related_concepts: list[str] | None = None,
    ) -> str:
        """오늘 학습 내용을 구조화해 data/journal/에 저장한다. 날짜는 서버가 직접 오늘 날짜로 채운다(LLM에 맡기지 않음)."""
        related_concepts = related_concepts or []
        today = _date.today()
        date_str = today.isoformat()

        entry = JournalEntry(
            date=today,
            topic=topic,
            learned=learned,
            stuck=stuck or None,
            related_concepts=related_concepts,
        )

        prompt = DAILY_PROMPT_PATH.read_text(encoding="utf-8").format(
            date=date_str,
            topic=topic,
            learned=learned,
            stuck=stuck or "(없음)",
            related_concepts=", ".join(related_concepts) if related_concepts else "(없음)",
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        body = response.content

        frontmatter = yaml.safe_dump(
            entry.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        )

        saved_content = f"---\n{frontmatter}---\n\n{body}\n"
        JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        out_path = JOURNAL_DIR / f"{date_str}-{_slugify(topic)}.md"
        out_path.write_text(saved_content, encoding="utf-8")

        # 첫 줄엔 경로, 그 다음 빈 줄 뒤엔 저장된 문서 전문 — 컨트롤러가 이 형식으로 파싱해 API 응답에 그대로 실음
        return f"저장 완료: {out_path.relative_to(BASE_DIR)}\n\n{saved_content}"

    def write_weekly(as_of: str | None = None) -> str:
        """data/journal/*.md 중 최근 7일치를 종합해 data/synthesis/{end}.md로 저장한다."""
        end = _date.fromisoformat(as_of) if as_of else _date.today()
        start = end - timedelta(days=6)

        paths = []
        for path in sorted(JOURNAL_DIR.glob("*.md")):
            try:
                d = _date.fromisoformat(path.stem[:10])  # 파일명이 "YYYY-MM-DD-키워드"라 앞 10자만 날짜
            except ValueError:
                continue
            if start <= d <= end:
                paths.append(path)

        if not paths:
            return f"{start}~{end} 사이 저장된 일지가 없음"

        daily_entries = _read_journal_entries(paths)
        prompt = WEEKLY_PROMPT_PATH.read_text(encoding="utf-8").format(daily_entries=daily_entries)
        response = llm.invoke([HumanMessage(content=prompt)])

        SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = SYNTHESIS_DIR / f"{end.isoformat()}.md"
        out_path.write_text(response.content + "\n", encoding="utf-8")

        return f"저장 완료: {out_path.relative_to(BASE_DIR)} ({len(paths)}개 일지 종합)"

    def write_til(weekly_date: str) -> str:
        """data/synthesis/{weekly_date}.md를 메타인지 회고로 재구성해 data/synthesis/til/{weekly_date}.md로 저장한다."""
        weekly_path = SYNTHESIS_DIR / f"{weekly_date}.md"
        if not weekly_path.exists():
            return f"weekly 산출물 없음: {weekly_path.relative_to(BASE_DIR)}"

        weekly_summary = weekly_path.read_text(encoding="utf-8")
        prompt = TIL_PROMPT_PATH.read_text(encoding="utf-8").format(weekly_summary=weekly_summary)
        response = llm.invoke([HumanMessage(content=prompt)])

        TIL_DIR.mkdir(parents=True, exist_ok=True)
        out_path = TIL_DIR / f"{weekly_date}.md"
        out_path.write_text(response.content + "\n", encoding="utf-8")

        return f"저장 완료: {out_path.relative_to(BASE_DIR)}"

    return write_daily, write_weekly, write_til
