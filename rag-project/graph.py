from pathlib import Path

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from state import GraphState
from rag import _build_embeddings, _build_llm, _get_vectorstore, PROMPT, REWRITE_PROMPT
from nodes import make_nodes, route_after_grade

AGENT_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "agent-system.md"


def build_rag_graph():
    embeddings = _build_embeddings()
    vectorstore = _get_vectorstore(embeddings)
    llm = _build_llm()

    retrieve_node, generate_node, grade_docs_node, rewrite_query_node = make_nodes(
        vectorstore, PROMPT, REWRITE_PROMPT, llm
    )

    graph = StateGraph(GraphState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade_docs", grade_docs_node)
    graph.add_node("rewrite_query", rewrite_query_node)
    graph.add_node("generate", generate_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "grade_docs")
    graph.add_conditional_edges(
        "grade_docs",
        route_after_grade,
        {"generate": "generate", "rewrite_query": "rewrite_query"},
    )
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", END)

    return graph.compile()


def build_agent_graph():
    """질문엔 answer_question, 회고형 발화엔 journal_write를 LLM이 스스로 골라 호출하는 대화형 에이전트."""
    from tools import make_tools  # graph.py <-> tools.py 순환 import 방지

    llm = _build_llm()
    tools = make_tools(llm)
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = AGENT_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    def agent_node(state: MessagesState):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=MemorySaver())


# if __name__ == "__main__":
#     g = build_rag_graph()
#     result = g.invoke({"question": "What is the main challenge of image classification?"})
#     print(result)
