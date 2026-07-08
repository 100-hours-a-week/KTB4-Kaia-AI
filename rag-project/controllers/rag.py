"""RAG 에이전트 컨트롤러 — 에이전트 그래프 호출과 응답 변환을 담당."""
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from schemas import ConverseResponse, SavedDocument, ThreadHistoryResponse, ThreadMessage

# writer.write_daily가 "저장 완료: {path}\n\n{내용}" 형식으로 반환하는 tool 이름들
_DOCUMENT_TOOLS = {"journal_write"}


def _extract_documents(tool_messages) -> list[SavedDocument]:
    documents = []
    for m in tool_messages:
        if m.name not in _DOCUMENT_TOOLS:
            continue
        header, _, content = m.content.partition("\n\n")
        path = header.removeprefix("저장 완료: ")
        documents.append(SavedDocument(path=path, content=content))
    return documents


def converse(agent_graph, message: str, thread_id: str) -> ConverseResponse:
    """에이전트 그래프를 호출해 답변과 이번 턴에 쓰인 tool 목록/저장된 문서를 반환. 실패 시 500으로 변환."""
    config = {"configurable": {"thread_id": thread_id}}
    try:
        # 이번 턴 이전까지 쌓인 메시지 수 — tools_used를 이번 턴 것만으로 한정하기 위한 기준점
        prior_messages = agent_graph.get_state(config).values.get("messages", [])
        result = agent_graph.invoke({"messages": [HumanMessage(content=message)]}, config=config)
    except Exception as exc:  # LLM/tool 호출 실패 등
        raise HTTPException(status_code=500, detail=f"에이전트 실행 실패: {exc}") from exc

    new_messages = result["messages"][len(prior_messages):]
    tool_messages = [m for m in new_messages if m.type == "tool"]
    tools_used = [m.name for m in tool_messages]
    print(f"[converse] thread={thread_id} tools_used={tools_used}")  # 로컬 개발 중 터미널에서 바로 확인

    return ConverseResponse(
        answer=result["messages"][-1].content,
        tools_used=tools_used,
        documents=_extract_documents(tool_messages),
    )


def get_thread_history(agent_graph, thread_id: str) -> ThreadHistoryResponse:
    """MemorySaver가 이 thread_id로 실제 뭘 들고 있는지 그대로 보여준다 — 메모리 확인용."""
    config = {"configurable": {"thread_id": thread_id}}
    messages = agent_graph.get_state(config).values.get("messages", [])
    return ThreadHistoryResponse(
        thread_id=thread_id,
        messages=[ThreadMessage(type=m.type, content=str(m.content)) for m in messages],
    )
