from pydantic import BaseModel, Field


class ConverseRequest(BaseModel):
    message: str = Field(min_length=1, description="user message")
    thread_id: str = Field(min_length=1, description="대화 세션을 구분하는 id (클라이언트가 생성/보관)")


class SavedDocument(BaseModel):
    path: str
    content: str


class ConverseResponse(BaseModel):
    answer: str
    tools_used: list[str] = Field(description="이번 턴에 호출된 tool 이름 목록 (없으면 빈 리스트)")
    documents: list[SavedDocument] = Field(default_factory=list, description="이번 턴에 저장된 문서(journal_write 등)")


class CorpusResponse(BaseModel):
    count: int
    topics: list[str]


class ThreadMessage(BaseModel):
    type: str
    content: str


class ThreadHistoryResponse(BaseModel):
    thread_id: str
    messages: list[ThreadMessage]
