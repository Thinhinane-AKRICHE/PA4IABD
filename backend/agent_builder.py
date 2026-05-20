from langgraph.prebuilt import create_react_agent
from backend.llm_factory import get_llm

from agent import (
    search_destination_info,
    get_weather_info,
    get_hotels_info,
    create_travel_plan,
    get_user_profile,
    memory,
    SYSTEM_PROMPT,
)

tools = [
    search_destination_info,
    get_weather_info,
    get_hotels_info,
    create_travel_plan,
    get_user_profile,
]


def build_agent(provider: str, model: str, temperature: float = 0):
    llm = get_llm(provider, model, temperature)

    return create_react_agent(
        llm,
        tools,
        checkpointer=memory,
        prompt=SYSTEM_PROMPT,
    )