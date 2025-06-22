from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar a API Key da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Modelo de dados para entrada de mensagens
class UserMessage(BaseModel):
    session_id: str
    message: str

# Histórico de conversas (Multi-turn chat)
conversation_history = {}

# Prompt base para o Chatbot
SYSTEM_PROMPT = """
Você é um agente virtual de atendimento da oficina mecânica [NOME DA OFICINA].

Regras:
- Seja educado, breve e objetivo.
- Atenda clientes sobre:
    1. Orçamento de serviços.
    2. Agendamento de manutenção.
    3. Status de veículos (peça a placa ou CPF).
    4. Dúvidas técnicas simples.
    5. Encaminhamento para um atendente humano.

Se o cliente digitar um número de opção, siga conforme o fluxo.
"""

@app.post("/chat/")
async def chat(user_message: UserMessage):
    try:
        history = conversation_history.get(user_message.session_id, [])

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        messages.append({"role": "user", "content": user_message.message})

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )

        bot_reply = response.choices[0].message.content

        history.append({"role": "user", "content": user_message.message})
        history.append({"role": "assistant", "content": bot_reply})
        conversation_history[user_message.session_id] = history

        return {"response": bot_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/whatsapp-webhook/")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    incoming_msg = form_data.get('Body')
    sender_id = form_data.get('From')

    user_message = UserMessage(session_id=sender_id, message=incoming_msg)
    reply = await chat(user_message)

    response_text = reply["response"]

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>"""
