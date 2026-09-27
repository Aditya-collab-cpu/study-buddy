import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from graph import app as graph_app, CHAPTER_1_SUBTOPICS,client
from fastapi.middleware.cors import CORSMiddleware



api = FastAPI()



api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RespondRequest(BaseModel):
    answer:str
    thread_id:str
    
class AskRequest(BaseModel):
    selected_text:str
    context:str
    mode: str = "explain"       # "explain" | "simplify" | "followup"
    previous_answer: str = ""
    follow_up: str = ""

class ChatRequest(BaseModel):
    messages:list
    context:str
    
class StartRequest(BaseModel):
    thread_id:str
    
@api.post("/ask")
def ask_doubt(req: AskRequest):
    if req.mode == "simplify":
        system = (
              "You are a CBSE Class 10 Social Science teacher. Rewrite the selected text "
              "in simpler words that are easy to remember. No jargon, 2-3 sentences max, "
              "use an everyday analogy if helpful."
          )
        user_msg = f"Selected text: {req.selected_text}\n\nLesson context: {req.context}"
    elif req.mode == "followup":
        system = (
              "You are a CBSE Class 10 Social Science teacher. The student has a follow-up "
              "question about an explanation they just received. Answer briefly (2-4 sentences) "
              "using ONLY the lesson context below."
          )
        user_msg = (
              f"Selected text: {req.selected_text}\n\n"
              f"Previous explanation: {req.previous_answer}\n\n"
              f"Student's follow-up: {req.follow_up}\n\n"
              f"Lesson context: {req.context}"
          )
    else:
        system = (
              "You are a CBSE Class 10 Social Science teacher. A student selected a "
              "phrase from their lesson because they didn't understand it. Explain it "
              "clearly and briefly (2-4 sentences), using ONLY the lesson context below."
          )
        user_msg = f"Selected text: {req.selected_text}\n\nLesson context: {req.context}"
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg}
        ]
    )
    
    return {"answer": completion.choices[0].message.content}
    

@api.post("/start")
def start_session(req:StartRequest):
    thread_id = req.thread_id
    config = {"configurable":{"thread_id": thread_id}}
    
    existing = graph_app.get_state(config)
    if existing.values.get("subtopics"):
        result = existing.values
    else:
        result = graph_app.invoke({
        "query":"",
        "mode":"learning",
        "subtopics": CHAPTER_1_SUBTOPICS,
        "subtopic_index": 0,
        "topic": CHAPTER_1_SUBTOPICS[0],
        "stage":"start",
        "attempts":0,
        }, config = config)
         
   
    return {
        "thread_id": thread_id,
        "response": result.get("response"),
        "explanation": result.get("explanation"),
        "check_question": result.get("check_question"),
        "stage": result.get("stage"),
        "subtopics": result.get("subtopics"),
        "subtopic_index": result.get("subtopic_index"),
    }


@api.post("/respond")
def respond(req: RespondRequest):
    config = {"configurable":{"thread_id": req.thread_id}}
    result = graph_app.invoke({"query":req.answer}, config = config)

    return {
        "response": result.get("response"),
        "explanation": result.get("explanation"),
        "check_question": result.get("check_question"),
        "stage": result.get("stage"),
        "understanding": result.get("understanding"),
        "subtopics": result.get("subtopics"),
        "subtopic_index": result.get("subtopic_index"),
    }
    
    
    
    
    

