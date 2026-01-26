from dotenv import load_dotenv
import requests
from langchain_openai import ChatOpenAI
import os
from langchain.tools import tool
from tavily import TavilyClient
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import trim_messages
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda

import datetime
import os.path
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

model = ChatOpenAI(model="gpt-3.5-turbo")

tavily = TavilyClient()
api_weather = os.getenv("WEATHER_API_KEY")

@tool(description="Crie um evento no Google Calendar com os detalhes fornecidos.")
def create_event(ano: int, mes: int, dia: int, hora_inicio: int, minuto_inicio: int, hora_fim: int, minuto_fim: int, resumo: str, descricao: str) -> dict:
  '''
  Cria um evento no Google Calendar do usuário autenticado.
  
  A função conecta-se à API do Google Calendar usando credenciais armazenadas em 'token.json'
  e cria um novo evento no calendário primário do usuário com os parâmetros fornecidos.
  
  Parâmetros:
  -----------
  ano : int
      Ano do evento (ex: 2026)
  mes : int
      Mês do evento (1-12)
  dia : int
      Dia do evento (1-31)
  hora_inicio : int
      Hora de início do evento no formato 24h (0-23)
  minuto_inicio : int
      Minuto de início do evento (0-59)
  hora_fim : int
      Hora de término do evento no formato 24h (0-23)
  minuto_fim : int
      Minuto de término do evento (0-59)
  resumo : str
      Título/nome do evento que aparecerá no calendário
  descricao : str
      Descrição detalhada do evento (pode ser vazia)
  
  Retorna:
  --------
  dict ou str
      Se sucesso: dicionário com dados do evento criado, incluindo 'htmlLink' para acessá-lo
      Se falha: string 'Event not created'
  
  Exemplo:
  --------
  >>> event = create_event(2026, 1, 26, 14, 30, 15, 30, "Reunião", "Reunião com equipe")
  >>> print(f"Evento criado: {event.get('htmlLink')}")
  '''
  creds = ...
  SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.readonly"]

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

  service = build("calendar", "v3", credentials=creds)
  start_event = datetime.datetime(ano, mes, dia, hora_inicio, minuto_inicio, 00, tzinfo=ZoneInfo('America/Sao_Paulo')).isoformat()
  end_event = datetime.datetime(ano, mes, dia, hora_fim, minuto_fim, 00, tzinfo=ZoneInfo('America/Sao_Paulo')).isoformat()
  event = service.events().insert(
      calendarId="primary",
      body={
        "summary": resumo,
        "description": descricao,
        "start": {
          "dateTime": start_event,
          "timeZone": "America/Sao_Paulo"
        },
        "end": {
          "dateTime": end_event,
          "timeZone": "America/Sao_Paulo"
        }
      }
    ).execute()

  if event.get('status') == 'confirmed':
    return event
  else: 
    return ('Event not created')

@tool(description="Get Realtime weather of a city.")
def get_weather(city: str) -> str:
    url = f"https://api.tomorrow.io/v4/weather/realtime?location={city}&apikey={api_weather}"
    headers = {
        "accept": "application/json",
        "accept-encoding": "deflate, gzip, br"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:  
        return f"Erro: status code {response.status_code}"

tools = [create_event, get_weather] 

def get_session_history(session_id: str):
    # String de conexão PostgreSQL para Supabase
    connection_string = "sqlite:///message_store.db"
    
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=connection_string,
        table_name="message_store"
    )

def extract_last_message(agent_output): # Extrai apenas a última mensagem da saída do agent
    if isinstance(agent_output, dict) and "messages" in agent_output:
        return {"messages": [agent_output["messages"][-1]]}
    return agent_output

trimmer = trim_messages(
    max_tokens=20,  # cada mensagem conta como 1 token
    strategy="last",   # seleciona as últimas mensagens
    token_counter=lambda x: 1,  # Cada mensagem conta como 1 token
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Você é um assistente prestativo."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_input}")
])

agent = create_agent( 
    model=model,
    tools=tools
    # response_format=ToolStrategy(AgentResponse),
)

trim_chain = {
    "user_input": lambda x: x["user_input"],
    "history": lambda x: trimmer.invoke(x["history"]),
}

chain = trim_chain | prompt | agent | RunnableLambda(extract_last_message)

# adicionando histórico de conversação a chain
runnable_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="user_input", # a chave do dict de entrada contém a mensagem do usuário
    history_messages_key="history", # a chave será usada para injetar o histórico na chain
    output_messages_key="messages" # a chave do dict de saída contém as mensagens geradas
)

# user_input = "Crie um evento no meu calendário para uma reunião de equipe no dia 26 de janeiro de 2026, das 10h às 11h, com o título 'Reunião de Planejamento' e a descrição 'Discutir metas e estratégias para o próximo trimestre'."
user_input = "resuma nossas conversas anteriores." 

response = runnable_with_history.invoke(
    {"user_input": user_input}, 
    config={"configurable": {"session_id": "1"}} 
)

print(response['messages'][0].content)