import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from graph import app as graph_app, CHAPTER_1_SUBTOPICS

api = FastAPI()

class RespondRequest(BaseModel):
    answer:str
    thread_id:str

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
    
    return {"thread_id": thread_id, "response": result["response"], "stage": result["stage"]}


@api.post("/respond")
def respond(req: RespondRequest):
    config = {"configurable":{"thread_id": req.thread_id}}
    result = graph_app.invoke({"query":req.answer}, config = config)
    
    return {
        "response":result["response"],
        "stage":result["stage"],
        "understanding":result["understanding"]
    }
    
    
    
    
    

