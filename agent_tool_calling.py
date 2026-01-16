from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from langchain_core.messages import HumanMessage
from rich.pretty import pprint
from tavily import TavilyClient
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
import os
load_dotenv()

model = ChatOpenAI(model="gpt-3.5-turbo")
tavily = TavilyClient()
api_weather = os.getenv("WEATHER_API_KEY")

class Source(BaseModel):
    """Squema para a fonte de informação."""
    name_source: str = Field(description="Nome da fonte")
    url: str = Field(description="URL da fonte")

class Weather(BaseModel):
    """Squema para o clima."""
    temperature: float = Field(description="Temperatura")

class AgentResponse(BaseModel):
    """Squema para a resposta do agente."""
    answer: str = Field(description="Resultado")
    sources: Optional[List[Source]] = Field(default=None, description="Fontes (Se aplicável)")
    weather: Optional[Weather] = Field(default=None, description="Temperatura em C° (Se aplicável)")

@tool
def get_capital(country: str) -> str:
    """Get the capital of a country."""
    capital = tavily.search(
        query=f"What is the capital of {country}?",
        search_depth="ultra-fast", # ultra-fast, fast, medium, advanced 
        max_results=1,
    )
    return capital

@tool
def get_weather(city: str) -> str:
    """Get Realtime weather of a city."""
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

# model_with_tools = llm.bind_tools(tools, tool_choice="required") # força o uso da tool (required, none)
tool = [get_capital, get_weather]
agent = create_agent(model=model, tools=tool, response_format=ToolStrategy(AgentResponse)) # ToolStrategy(AgentResponse) força o uso do schema

def main():
    result = agent.invoke({"messages": [HumanMessage(content="Capital of Brazil? And what is the weather of Toronto?")]})
    pprint(result, expand_all=True) # melhora a visualização de dict/list no terminal

if __name__ == "__main__":
    main()
