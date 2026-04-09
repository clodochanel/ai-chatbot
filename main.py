import os
import json
import csv
import smtplib # For email notifications
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from email.message import EmailMessage

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = Groq(api_key="GROQ_API_KEY")

# --- MEMORY STORAGE ---
# In a big app, we'd use a database. For an MVP, we use a simple Python dictionary.
chat_histories = {}

def get_knowledge():
    with open("knowledge.json", "r", encoding="utf-8") as f:
        return json.dumps(json.load(f))

def send_lead_email(lead_info):
    """Sends an email to the business owner when a lead is captured."""
    # Note: For this to work, you'll need a Gmail 'App Password' or a service like Resend.
    # For now, we will just print to console to show the logic.
    print(f"ALERTA DE LEAD: Enviando email a la inmobiliaria con: {lead_info}")

@app.get("/chat")
async def chat(user_query: str, session_id: str = "default"):
    # 1. Load context
    knowledge = get_knowledge()
    
    # 2. Get or create history for this user
    if session_id not in chat_histories:
        chat_histories[session_id] = [
            {"role": "system", "content": f"Eres SolBot, asistente de Sol Real Estate. Usa este JSON: {knowledge}. Habla en el idioma del usuario (Español/Inglés). Si captas un lead, di [LEAD: info]."}
        ]
    
    # 3. Add user query to history
    chat_histories[session_id].append({"role": "user", "content": user_query})

    # 4. Get response from Groq (sending the WHOLE history for memory)
    completion = client.chat.completions.create(
        messages=chat_histories[session_id],
        model="llama-3.1-8b-instant",
    )
    
    response_text = completion.choices[0].message.content
    
    # 5. Add bot response to history
    chat_histories[session_id].append({"role": "assistant", "content": response_text})

    # 6. Lead Logic
    if "[LEAD:" in response_text:
        lead_info = response_text.split("[LEAD:")[1].split("]")[0]
        send_lead_email(lead_info)
        response_text = response_text.split("[LEAD:")[0]

    return {"response": response_text}