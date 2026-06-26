from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import chromadb
import time
import os
from pathlib import Path


class RateLimitedEmbeddings(GoogleGenerativeAIEmbeddings):
    """Free tier는 100 RPM 제한이 있어, 배치 사이에 1초 슬립을 삽입한다."""

    def embed_documents(self, texts):
        batch_size = 90  # 100 RPM 여유분 확보
        results = []
        for i in range(0, len(texts), batch_size):
            if i > 0:
                time.sleep(1.0)
            batch = texts[i:i + batch_size]
            print(f"  임베딩 중... {min(i + batch_size, len(texts))}/{len(texts)}")
            results.extend(super().embed_documents(batch))
        return results

load_dotenv()

# 인덱싱
print("문서 로딩 및 인덱싱 시작...")

CS231N_DIR = Path("../cs231n")
pdf_paths = sorted(CS231N_DIR.glob("*.pdf"))
pdf_docs = []
for p in pdf_paths:
    pdf_docs.extend(PyPDFLoader(str(p)).load())

docs = pdf_docs
print(f"로딩된 Document 수: {len(docs)}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)
split_docs = splitter.split_documents(docs)
print(f"분할된 chunk 수: {len(split_docs)}")

embeddings = RateLimitedEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# ChromaDB 원격 서버 연결
# 사용 전 서버 실행 필요: chroma run --path ./chroma_data --port 8000
CHROMA_COLLECTION = "cs231n-lectures"
chroma_client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8000")),
)

existing = {c.name for c in chroma_client.list_collections()}
if CHROMA_COLLECTION in existing:
    print(f"기존 컬렉션 '{CHROMA_COLLECTION}' 재사용 (임베딩 생략)")
    vectorstore = Chroma(
        client=chroma_client,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
    )
else:
    print(f"새 컬렉션 '{CHROMA_COLLECTION}' 생성 및 임베딩 중...")
    vectorstore = Chroma.from_documents(
        split_docs,
        embeddings,
        client=chroma_client,
        collection_name=CHROMA_COLLECTION,
    )

print("인덱싱 완료")

# RAG
print("RAG 파이프라인 시작...")
# Retriever를 통해 관련 문서를 검색하고, LLM을 통해 답변을 생성하는 RAG 파이프라인 구성
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Augmented Generation을 위한 Prompt 구성
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "다음 문서를 근거로 사용자 질문에 답하세요. "
     "근거가 부족하면 '주어진 자료에서는 확인할 수 없습니다.'라고 답하세요.\n\n"
     "{context}"),
    ("human", "{question}"),
])

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


llm = build_llm()

def format_docs(ds):
    return "\n\n".join(d.page_content for d in ds)

rag = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print(rag.invoke("What is the main challenge of image classification?"))

print("RAG 파이프라인 완료")

# 평가
from langsmith.evaluation import evaluate
from langsmith import Client

DATASET_NAME = "cs231n-rag-eval"

client = Client()

EVAL_QUESTIONS = [
    {
        "question": "What is the main challenge of image classification compared to other classification tasks?",
        "answer":   "Image classification faces the semantic gap and viewpoint variation, illumination changes, deformation, occlusion, background clutter, and intra-class variation, making it hard to write explicit rules for recognizing objects.",
    },
    {
        "question": "How does backpropagation compute gradients in a neural network?",
        "answer":   "Backpropagation applies the chain rule recursively from the loss output back through each layer, computing the gradient of the loss with respect to each parameter by multiplying local gradients along the computational graph.",
    },
    {
        "question": "What is the role of batch normalization in training deep neural networks?",
        "answer":   "Batch normalization normalizes activations within each mini-batch to have zero mean and unit variance, then applies learnable scale and shift parameters. This reduces internal covariate shift, allows higher learning rates, and acts as a regularizer.",
    },
    {
        "question": "What architectural innovation allowed ResNet to train very deep networks?",
        "answer":   "ResNet introduced residual (skip) connections that let gradients flow directly through identity shortcuts, making it possible to train networks with hundreds of layers without vanishing gradient problems.",
    },
    {
        "question": "How does a convolutional layer differ from a fully connected layer?",
        "answer":   "A convolutional layer applies shared filter weights locally across the spatial dimensions of the input, preserving spatial structure and drastically reducing parameters, while a fully connected layer connects every input neuron to every output neuron with independent weights.",
    },
]
print(f"검증 질문 수: {len(EVAL_QUESTIONS)}")

existing = [d for d in client.list_datasets(dataset_name=DATASET_NAME)]

inputs  = [{"question": ex["question"]} for ex in EVAL_QUESTIONS]
outputs = [{"answer":   ex["answer"]}   for ex in EVAL_QUESTIONS]

if existing:
    dataset = existing[0]
    print(f"기존 Dataset 사용: {dataset.id}")
else:
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="CS231n 강의 슬라이드 기반 RAG 답변 품질 평가용",
    )
    print(f"새 Dataset 생성: {dataset.id}")
    client.create_examples(
        dataset_id=dataset.id,
        inputs=inputs,
        outputs=outputs,
    )
    print(f"Example {len(EVAL_QUESTIONS)}건 추가 완료")

loaded = client.read_dataset(dataset_name=DATASET_NAME)

examples = list(client.list_examples(dataset_id=loaded.id))
print(f"총 Example 수: {len(examples)}")

for ex in examples[:3]:
    print("Q:", ex.inputs["question"])
    print("A:", ex.outputs["answer"] if ex.outputs else "(없음)")
    print()

def target(inputs):
    return {"answer": rag.invoke(inputs["question"])}

def contains_expected_keyword(run, example):
    pred = run.outputs.get("answer", "")
    expected = example.outputs.get("answer", "")

    # === 기대 답변에서 명사로 보이는 단어 한두 개를 키워드로 사용 ===
    keywords = [w for w in expected.split() if len(w) >= 2][:2]
    hit = all(k in pred for k in keywords)

    return {
        "key": "contains_expected_keyword",
        "score": 1 if hit else 0,
        "comment": f"필수 키워드 {keywords} 포함 여부",
    }

JUDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "당신은 답변 품질을 평가하는 채점자입니다.\n"
     "아래 기대 답변(reference)과 모델 답변(prediction)을 비교하고,\n"
     "의미가 일치하면 1, 부분적으로만 일치하면 0.5, 무관하면 0을 점수로 매기세요.\n"
     "응답은 반드시 첫 줄에 0/0.5/1 중 하나의 숫자만, 둘째 줄부터 짧은 이유를 적으세요."),
    ("human",
     "질문: {question}\n\n"
     "기대 답변: {reference}\n\n"
     "모델 답변: {prediction}"),
])

judge_chain = JUDGE_PROMPT | llm | StrOutputParser()

def llm_judge(run, example):
    reply = judge_chain.invoke({
        "question": example.inputs["question"],
        "reference": example.outputs["answer"],
        "prediction": run.outputs["answer"],
    })
    # === 첫 줄의 숫자만 점수로 사용 ===
    first_line = reply.strip().splitlines()[0].strip()
    try:
        score = float(first_line)
    except ValueError:
        score = 0
    return {
        "key": "llm_judge_semantic_match",
        "score": score,
        "comment": reply,
    }

result = evaluate(
    target,
    data=DATASET_NAME,
    evaluators=[contains_expected_keyword, llm_judge],
    experiment_prefix="v1-baseline",
)

print(result)