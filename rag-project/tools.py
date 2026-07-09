from langchain_core.tools import tool

from graph import build_rag_graph
from writer import make_writer


def make_tools(llm):
    """agent 그래프가 bind_tools로 물릴 tool 목록. QA 그래프(재검색 루프 포함)와 writer 함수들을 각각 하나의 tool로 감싼다."""
    qa_graph = build_rag_graph()

    @tool
    def answer_question(question: str) -> str:
        """문서 코퍼스를 검색해 질문에 답한다.
        사용자가 개념을 묻거나, 설명을 요청하거나, "~가 뭐야", "~는 어떻게 동작해" 같은 질문을 할 때 사용한다.
        오늘 공부한 내용을 기록하려는 요청에는 사용하지 않는다."""
        result = qa_graph.invoke({"question": question})
        sources = ", ".join(result.get("sources", [])) or "없음"
        return f"{result['answer']}\n\n(출처: {sources})"

    write_til, write_wil, write_retrospective = make_writer(llm)

    @tool
    def til_write(
        topic: str,
        learned: str,
        stuck: str = "",
        related_concepts: list[str] | str | None = None,
    ) -> str:
        """사용자가 오늘(TIL, Today I Learned) 공부한 내용을 회고하듯 이야기했을 때, 그 내용을 구조화해 저장한다.
        "오늘 ~공부했어", "~를 배웠는데 ~에서 막혔어" 같은 회고형 발화에서만 사용한다.
        이번 "주" 전체를 회고하거나 정리해달라는 요청에는 쓰지 않는다 — 그건 wil_synthesize/retrospective_write의 몫이다.
        질문에 답하는 용도가 아니다 — 정보를 찾아달라는 요청에는 answer_question을 쓴다.
        날짜는 서버가 자동으로 오늘 날짜를 채우니 신경 쓰지 않는다.
        stuck/related_concepts는 언급이 없으면 빈 값으로 둔다.
        related_concepts에 여러 개념이 있으면 쉼표로 구분된 문자열도 괜찮다 (예: "LoRA, Quantization")."""
        return write_til(topic, learned, stuck, related_concepts)

    @tool
    def wil_synthesize() -> str:
        """이번 주(월요일 시작, 오늘까지) til_write로 쌓인 학습 기록을 콘텐츠 중심으로 종합해 주간 요약(WIL, Week I Learned — 이번 주 학습 지도·흐름·연결된 개념)으로 저장한다.
        "이번 주 정리해줘", "주간 요약해줘" 같은, 오늘 하루가 아니라 한 주 전체의 학습 내용을 묻는 요청에서 사용한다.
        retrospective_write와는 독립적인 tool이다 — 회고를 쓰기 위해 이걸 먼저 호출할 필요는 없다.
        인자 없음 — 범위(이번 주 월요일~오늘)는 서버가 자동으로 계산한다."""
        return write_wil()

    @tool
    def retrospective_write(
        topic: str,
        difficulties: str,
        reflections: str,
        decisions: str = "",
        problem_solving: str = "",
        future_plans: str = "",
    ) -> str:
        """사용자와의 대화에서 직접 엘리시트한 회고를 정리해 저장한다. 프로젝트 회고, 학습 회고, 그 외 어떤 기간/작업에 대한 회고든 다 된다.
        "이번 주 회고 써줘", "이번 프로젝트 회고 정리하고 싶어", "회고 쓰는 거 도와줘" 같은 요청에서 사용한다.
        wil_synthesize와 무관하게 독립적으로 동작한다 — wil_synthesize를 먼저 호출할 필요 없다.
        topic: 이 회고가 무엇에 대한 것인지 (예: "Week 8 — LangGraph 마이그레이션", "이번 주 CS231n 학습").
        difficulties/reflections는 필수, decisions(설계 결정과 이유)/problem_solving(해결 경험)/future_plans(앞으로 하고 싶은 것)는 대화에서 나온 만큼만 채우고 없으면 빈 값으로 둔다.
        날짜는 서버가 자동으로 오늘 날짜를 채운다."""
        return write_retrospective(topic, difficulties, reflections, decisions, problem_solving, future_plans)

    return [answer_question, til_write, wil_synthesize, retrospective_write]
