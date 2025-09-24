from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rhea_python_chatbot import RHEAHealthBot

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = RHEAHealthBot()
bot.get_health_data()

class Query(BaseModel):
    message: str

@app.post("/chat")
def chat(query: Query):
    response = bot.process_message(query.message)
    return {"response": response}
