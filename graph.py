import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from retrival import load_chunks, build_bm25_index, build_vector_entries, search_with_rerank

load_dotenv()
entries, metadata = load_chunks()
bm25 = build_bm25_index(entries)
embeddings = build_vector_entries(entries, metadata)
MAX_ATTEMPTS = 2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




class GraphState(TypedDict):
    query: str
    topic: str
    stage: str          # "start" | "awaiting_answer" | "done"
    response: str
    check_question: str
    understanding: str  # "correct" | "partial" | "wrong"
    attempts: int
    explanation: str


def entry_decision(state: GraphState) -> str:
    return "evaluate" if state.get("stage") == "awaiting_answer" else "explain"


def explain_node(state: GraphState) -> dict:
    attempts = state.get("attempts", 0)
    topic = state.get("topic") or state["query"]
    results = search_with_rerank(topic, entries, bm25, embeddings, top_k=3, candidate_pool=10)
    context = "\n\n".join(entry for entry, _ in results)

    rephrase_hint = "" if attempts == 0 else (
        "The student didn't understand your last explanation — explain it again, "
        "differently: use a simpler example or a different angle."
    )
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": (
                "You are a CBSE Class 10 Social Science teacher. Explain the concept "
                "clearly using ONLY the retrieved textbook context below. Keep it "
                "concise and exam-focused. " + rephrase_hint
            )},
            {"role": "user", "content": f"Topic: {topic}\n\nTextbook context: {context}"}
        ]
    )
    explanation = completion.choices[0].message.content
    return {"topic": topic, "response": explanation, "attempts": attempts + 1}


def comprehension_check_node(state: GraphState) -> dict:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": (
                "Based on the explanation below, ask ONE short question that checks "
                "whether the student understood the concept. Just the question, no preamble."
            )},
            {"role": "user", "content": state["response"]}
        ]
    )
    question = completion.choices[0].message.content
    return {
        "check_question": question,
        "explanation": state["response"],
        "response": f"{state['response']}\n\nQuick check: {question}",
        "stage": "awaiting_answer",
    }


def evaluate_understanding_node(state: GraphState) -> dict:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": (
                "Judge the student's answer to the comprehension question. "
                "Reply with exactly one word: correct, partial, or wrong."
            )},
            {"role": "user", "content": (
                f"Question: {state['check_question']}\nStudent's answer: {state['query']}"
            )}
        ]
    )
    verdict = completion.choices[0].message.content.strip().lower()
    return {"understanding": verdict}


def understanding_decision(state: GraphState) -> str:
    if state["understanding"] == "correct":
        return "done"
    if state["attempts"] < MAX_ATTEMPTS:
        return "reexplain"
    return "give_up"


def done_node(state: GraphState) -> dict:
    return {"response": "Great, you've got it! Ready for the next topic.", "stage": "done"}


def give_up_node(state: GraphState) -> dict:
    return {
        "response": f"Let's move on for now — here's the key idea: {state['explanation']}",
        "stage": "done",
    }


graph = StateGraph(GraphState)
graph.add_node("explain", explain_node)
graph.add_node("check", comprehension_check_node)
graph.add_node("evaluate", evaluate_understanding_node)
graph.add_node("done", done_node)
graph.add_node("give_up", give_up_node)

graph.add_conditional_edges(START, entry_decision, {"explain": "explain", "evaluate": "evaluate"})
graph.add_edge("explain", "check")
graph.add_edge("check", END)
graph.add_conditional_edges("evaluate", understanding_decision, {
    "done": "done", "reexplain": "explain", "give_up": "give_up"
})
graph.add_edge("done", END)
graph.add_edge("give_up", END)

app = graph.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "2"}}

    result = app.invoke({"query": "why did nationalism rise in Europe?", "stage": "start", "attempts": 0}, config=config)
    print(result["response"])

    while result.get("stage") != "done":
        answer = input("\n--- your answer ---\n")
        result = app.invoke({"query": answer}, config=config)
        print(f"\n[verdict: {result.get('understanding')}]")
        print(result["response"])