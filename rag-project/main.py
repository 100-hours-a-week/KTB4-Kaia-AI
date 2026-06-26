from contextlib import asynccontextmanager
from glob import glob
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
import chromadb

# .env 파일을 읽어서 시스템의 환경 변수로 설정
load_dotenv()


def build_llm():
    provider = os.getenv("LLM_PROVIDER", "google").lower()
    print(f"LLM Provider: {provider}")
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gemma4:e2b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    return ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def build_rag_chain():
    # 인덱싱
    from pathlib import Path
    cs231n_dir = Path("../cs231n")
    pdf_docs = []
    for p in sorted(cs231n_dir.glob("*.pdf")):
        pdf_docs.extend(PyPDFLoader(str(p)).load())

    print(f"로딩된 Document 수: {len(pdf_docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    split_docs = splitter.split_documents(pdf_docs)
    print(f"분할된 chunk 수: {len(split_docs)}")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    CHROMA_COLLECTION = "cs231n-lectures"
    chroma_client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )

    existing = {c.name for c in chroma_client.list_collections()}
    if CHROMA_COLLECTION in existing:
        vectorstore = Chroma(
            client=chroma_client,
            collection_name=CHROMA_COLLECTION,
            embedding_function=embeddings,
        )
    else:
        vectorstore = Chroma.from_documents(
            split_docs,
            embeddings,
            client=chroma_client,
            collection_name=CHROMA_COLLECTION,
        )

    # RAG
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "다음 문서를 근거로 사용자 질문에 답하세요. "
         "근거가 부족하면 '주어진 자료에서는 확인할 수 없습니다.'라고 답하세요.\n\n"
         "{context}"),
        ("human", "{question}"),
    ])

    llm = build_llm()

    def format_docs(ds):
        return "\n\n".join(d.page_content for d in ds)

    rag = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI 앱 초기화 시점에 인덱싱 + RAG 체인 구성
    app.state.rag = build_rag_chain()
    yield


app = FastAPI(lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    answer = app.state.rag.invoke(req.question)
    return QueryResponse(answer=answer)
