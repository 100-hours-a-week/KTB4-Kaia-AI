from rag import RELEVANCE_THRESHOLD, TOP_K, _extract_sources
from state import GraphState


def make_nodes(vectorstore, prompt, rewrite_prompt, llm):
    def retrieve_node(state: GraphState):
        results = vectorstore.similarity_search_with_relevance_scores(state["question"], k=TOP_K)
        return {
            "document": [doc for doc, _ in results],
            "doc_scores": [score for _, score in results],
        }

    def generate_node(state: GraphState):
        context = "\n\n".join(d.page_content for d in state["document"])
        messages = prompt.invoke({"context": context, "question": state["question"]}).to_messages()
        response = llm.invoke(messages)
        return {
            "answer": response.content,
            "sources": _extract_sources(state["document"]),
        }

    def grade_docs_node(state: GraphState):
        scores = state.get("doc_scores") or []
        top1 = scores[0] if scores else 0.0
        return {"is_relevant": top1 >= RELEVANCE_THRESHOLD}

    def rewrite_query_node(state: GraphState):
        context = "\n\n".join(d.page_content for d in state["document"])
        messages = rewrite_prompt.invoke({"context": context, "question": state["question"]}).to_messages()
        response = llm.invoke(messages)
        return {
            "question": response.content.strip(),
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return retrieve_node, generate_node, grade_docs_node, rewrite_query_node


def route_after_grade(state: GraphState):
    """grade_docs 다음 분기: 관련 있으면 generate, 없으면 retry_count<2 한도 내에서 rewrite_query."""
    if state.get("is_relevant", True):
        return "generate"
    if state.get("retry_count", 0) >= 2:
        return "generate"
    return "rewrite_query"
