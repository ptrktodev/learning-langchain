from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from rich.pretty import pprint
from tavily import TavilyClient
load_dotenv()

model = ChatOpenAI(model="gpt-3.5-turbo")
tavily = TavilyClient()

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
def get_news(topic: str) -> str:
    """Get the most recent news about this topic."""
    news_recent = tavily.search(
        query=f"What is the news most recent about {topic}?",
        search_depth="fast", # ultra-fast, fast, medium, advanced 
        max_results=3,
        topic='news',
        start_date='2026-01-09',
    )
    return news_recent

@tool
def get_weather(city: str) -> str:
    """Get current weather and temperature in Celsius."""
    weather = tavily.search(
        query=(
            f"What is the current weather in {city} "
            f"including the temperature in degrees Celsius?"
        ),
        search_depth="ultra-fast",
        max_results=1,
    )
    return weather

# model_with_tools = llm.bind_tools(tools, tool_choice="required") # força o uso da tool (required, none)
tool = [get_capital, get_news, get_weather]
agent = create_agent(model, tool)

def main():
    result = agent.invoke({"messages": [HumanMessage(content="Weather and temperature now in New York.")]})
    pprint(result['messages'], expand_all=True) # melhora a visualização de dict/list no terminal

if __name__ == "__main__":
    main()
