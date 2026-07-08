"""/converse 라우터 — 대화형 입력을 받아 에이전트(질문 응답 또는 학습일지 기록)를 실행한다."""
from fastapi import APIRouter, Request

from controllers import rag as rag_controller
from schemas import ConverseRequest, ConverseResponse, ThreadHistoryResponse

router = APIRouter()


@router.post("/converse", response_model=ConverseResponse)
def converse(req: ConverseRequest, request: Request) -> ConverseResponse:
    # 에이전트 그래프는 서버 시작 시 lifespan에서 1회 구성돼 app.state.agent에 보관됨
    agent_graph = request.app.state.agent
    return rag_controller.converse(agent_graph, req.message, req.thread_id)


@router.get("/threads/{thread_id}", response_model=ThreadHistoryResponse)
def thread_history(thread_id: str, request: Request) -> ThreadHistoryResponse:
    # MemorySaver에 이 thread_id로 실제 뭐가 쌓여있는지 확인하는 디버그용 엔드포인트
    return rag_controller.get_thread_history(request.app.state.agent, thread_id)
