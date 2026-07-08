from langchain_core.tools import tool

from graph import build_rag_graph
from writer import make_writer


def make_tools(llm):
    """agent 그래프가 bind_tools로 물릴 tool 목록. QA 그래프(재검색 루프 포함)와 write_daily를 각각 하나의 tool로 감싼다."""
    qa_graph = build_rag_graph()

    @tool
    def answer_question(question: str) -> str:
        """문서 코퍼스를 검색해 질문에 답한다.
        사용자가 개념을 묻거나, 설명을 요청하거나, "~가 뭐야", "~는 어떻게 동작해" 같은 질문을 할 때 사용한다.
        오늘 공부한 내용을 기록하려는 요청에는 사용하지 않는다."""
        result = qa_graph.invoke({"question": question})
        sources = ", ".join(result.get("sources", [])) or "없음"
        return f"{result['answer']}\n\n(출처: {sources})"

    write_daily, _write_weekly, _write_til = make_writer(llm)

    @tool
    def journal_write(
        topic: str,
        learned: str,
        stuck: str = "",
        related_concepts: list[str] | None = None,
    ) -> str:
        """사용자가 오늘 공부한 내용을 회고하듯 이야기했을 때, 그 내용을 학습일지로 구조화해 저장한다.
        "오늘 ~공부했어", "~를 배웠는데 ~에서 막혔어" 같은 회고형 발화에서만 사용한다.
        질문에 답하는 용도가 아니다 — 정보를 찾아달라는 요청에는 answer_question을 쓴다.
        날짜는 서버가 자동으로 오늘 날짜를 채우니 신경 쓰지 않는다.
        stuck/related_concepts는 언급이 없으면 빈 값으로 둔다."""
        return write_daily(topic, learned, stuck, related_concepts)

    return [answer_question, journal_write]
