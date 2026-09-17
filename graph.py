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
    stage: str          # "start" | "awaiting_answer" | "ready_for_next" | "chapter_done"
    response: str
    check_question: str
    understanding: str  # "correct" | "partial" | "wrong"
    attempts: int
    explanation: str
    mode: str            # "learning" | "exam" (exam not built yet)
    subtopics: list
    subtopic_index: int


def entry_decision(state: GraphState) -> str:
    stage = state.get("stage")
    if stage == "awaiting_answer":
        return "evaluate"
    if stage == "ready_for_next":
        return "advance"
    return "explain"

def advance_node(state:GraphState)->dict:
    next_index = state["subtopic_index"] + 1
    if next_index < len(state["subtopics"]):
        return{
            "subtopic_index":next_index,
            "topic":state["subtopics"][next_index],
            "attempts":0,
            "stage":"start"
            
        }
    else:
        return{
            "stage":"chapter_done",
            "response":"You've completed all subtopics in this chapter. Great job!"
        }
        
def advance_decision(state: GraphState) -> str:
    return "next_subtopic" if state["stage"] == "start" else "finished"


def give_up_node(state: GraphState) -> dict:
    return {
        "response": f"Let's move on for now — here's the key idea: {state['explanation']}\n\nSay anything to continue.",
        "stage": "ready_for_next",
    }


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
    return {"response": "Great, you've got it! Say anything to move to the next topic.", "stage": "ready_for_next"}



graph = StateGraph(GraphState)
graph.add_node("explain", explain_node)
graph.add_node("check", comprehension_check_node)
graph.add_node("evaluate", evaluate_understanding_node)
graph.add_node("done", done_node)
graph.add_node("give_up", give_up_node)
graph.add_node("advance", advance_node)

graph.add_conditional_edges(START, entry_decision, {"explain": "explain", "evaluate": "evaluate","advance": "advance"})
graph.add_edge("explain", "check")
graph.add_edge("check", END)
graph.add_conditional_edges("evaluate", understanding_decision, {
    "done": "done", "reexplain": "explain", "give_up": "give_up"
})
graph.add_edge("done", END)
graph.add_edge("give_up", END)
graph.add_conditional_edges("advance", advance_decision, {"next_subtopic": "explain", "finished": END})

app = graph.compile(checkpointer=InMemorySaver())

CHAPTER_1_SUBTOPICS = [
    "The French Revolution and the first expressions of nationalism",
    "Napoleon and the Napoleonic Code",
    "New Conservatism after 1815 — the Congress of Vienna and the conservative order",
    "Making of Nationalism — culture, folklore, and visualizing the nation",
    "The Strange Case of Britain — a different path to nationhood",
    "Economic hardship and the 1830s-1848 revolutions",
    "The Unification of Germany",
    "The Unification of Italy",
    "Nationalism and Imperialism — the Balkans crisis and the road to WWI",
]


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "3"}}

    result = app.invoke({
        "query": "",
        "mode": "learning",
        "subtopics": CHAPTER_1_SUBTOPICS,
        "subtopic_index": 0,
        "topic": CHAPTER_1_SUBTOPICS[0],
        "stage": "start",
        "attempts": 0,
    }, config=config)
    print(result["response"])

    while result.get("stage") != "chapter_done":
        answer = input("\n--- your input ---\n")
        result = app.invoke({"query": answer}, config=config)
        print(f"\n[stage: {result.get('stage')}, verdict: {result.get('understanding')}]")
        print(result["response"])