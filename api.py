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

class ChatRequest(BaseModel):
    messages:list
    context:str
    
@api.post("/ask")
def ask_doubt(req: AskRequest):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": (
                "You are a CBSE Class 10 Social Science teacher. A student selected a "
                "phrase from their lesson because they didn't understand it. Explain it "
                "clearly and briefly (2-4 sentences), using ONLY the lesson context below."
            )},
            {"role": "user", "content": f"Selected text: {req.selected_text}\n\nLesson context: {req.context}"}
        ]
    )
    
    return {"answer": completion.choices[0].message.content}
    

@api.post("/start")
def start_session():
    thread_id = str(uuid.uuid4())
    config = {"configurable":{"thread_id": thread_id}}
    
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
    
    
    
    
    

