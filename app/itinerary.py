import os
from dotenv import load_dotenv
from google import genai
from typing import TypedDict, List, Any, Generator


from api_wrappers import (
    get_weather, search_places, get_exchange_rate,
    search_flights, search_hotels,
    search_google_places,
    get_country_info, get_destination_photo
)
from rag import query_documents


from langgraph.graph import StateGraph, END

# LangSmith tracing
from langsmith import traceable

# LangChain 
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# CSV usage logger
from utils_usage import log_usage


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

# Google GenAI 
client = genai.Client(api_key=GEMINI_API_KEY)

# LLM
lc_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7,
)

chat_prompt = ChatPromptTemplate.from_template(
    """You are a professional travel planner.

User Request:
{user_prompt}

Generate a helpful, friendly itinerary with:
-Trvaelling Options(flights,Trains,bus)
- Day-wise plan (morning/afternoon/evening)
- Food & attraction suggestions
- Weather/travel details
- Rough budget cavets 

Return plain text (not JSON)."""
)

free_chat_chain = chat_prompt | lc_llm


class TravelState(TypedDict, total=False):
    origin: str
    destination: str
    destination_code: str
    country: str
    days: int
    date: str
    budget_currency: str
    target_currency: str
    interests: List[str]
    user_prompt: str
    research: Any
    weather: Any
    budget: Any
    transport: Any
    accommodation: Any
    activities: Any
    country_info: Any
    media: Any
    structured_data: Any
    itinerary: Any



def research_agent(state: TravelState):
    dest = state.get("destination")
    if not dest:
        state["research"] = {"error": "No destination provided"}
        return state
    query = f"Top attractions and travel info for {dest}"
    results = search_places("attractions", dest, num_results=5)
    rag_results = query_documents(query)
    state["research"] = {"attractions": results, "cultural_notes": rag_results}
    return state


def weather_agent(state: TravelState):
    dest = state.get("destination")
    days = state.get("days", 3)
    if not dest:
        state["weather"] = {"error": "No destination provided"}
        return state
    state["weather"] = get_weather(dest, days)
    return state


def budget_agent(state: TravelState):
    base = state.get("budget_currency", "USD")
    target = state.get("target_currency", "USD")
    try:
        exchange = get_exchange_rate(base, target)
    except Exception as e:
        exchange = {"error": f"exchange API failed: {e}"}
    state["budget"] = {
        "exchange_rate": exchange,
        "categories": {
            "flights": "from transport agent",
            "stay": "from accommodation agent",
            "food": "avg $20/day",
            "activities": "variable",
        },
    }
    return state


def transport_agent(state: TravelState):
    DESTINATION_AIRPORTS = {
        "Manali": "IXC",
        "Shimla": "SLV",
        "Ooty": "CJB",
        "Darjeeling": "IXB",
    }
    origin = state.get("origin")
    dest = state.get("destination")
    date = state.get("date", "")
    if not origin or not dest:
        state["transport"] = {"error": "origin/destination missing"}
        return state

    dest_code = state.get("destination_code") or DESTINATION_AIRPORTS.get(dest, dest)
    flights = {}
    try:
        flights = search_flights(origin, dest_code, date, adults=1)
    except Exception as e:
        flights = {"error": f"flight search failed: {e}"}

    if not flights or not flights.get("data"):
        state["transport"] = {
            "flights": None,
            "note": f"No direct flights to {dest}. Suggest road/train from {origin}.",
        }
    else:
        state["transport"] = {
            "flights": flights,
            "local_transport": ["cab", "bus", "rental bike"],
        }
    return state


def accommodation_agent(state: TravelState):
    city_code = state.get("destination_code") or state.get("destination")
    if not city_code:
        state["accommodation"] = {"error": "No destination code or city provided"}
        return state
    try:
        hotels = search_hotels(city_code)
    except Exception as e:
        hotels = {"error": f"hotel search failed: {e}"}
    state["accommodation"] = hotels
    return state


def activity_agent(state: TravelState):
    dest = state.get("destination", "")
    interests = state.get("interests", [])
    query = f"{' and '.join(interests) if interests else 'popular'} activities in {dest}"
    try:
        activities = search_google_places(query, "0,0")
    except Exception as e:
        activities = {"error": f"places search failed: {e}"}
    state["activities"] = activities
    return state


def country_agent(state: TravelState):
    country = state.get("country")
    if not country:
        state["country_info"] = {"error": "No country provided"}
        return state
    try:
        info = get_country_info(country)
    except Exception as e:
        info = {"error": f"country info failed: {e}"}
    state["country_info"] = info
    return state


def media_agent(state: TravelState):
    dest = state.get("destination", "")
    try:
        photos = get_destination_photo(dest, count=3)
    except Exception as e:
        photos = {"error": f"photo fetch failed: {e}"}
    state["media"] = photos
    return state


def coordinator_agent(state: TravelState):
    structured = {
        "research": state.get("research"),
        "weather": state.get("weather"),
        "budget": state.get("budget"),
        "transport": state.get("transport"),
        "accommodation": state.get("accommodation"),
        "activities": state.get("activities"),
        "country_info": state.get("country_info"),
        "media": state.get("media"),
    }
    state["structured_data"] = structured
    return state



def build_prep_graph():
    """
    Graph that runs all agents up to the 'coordinator' and ENDS there.
    We'll then stream the itinerary text with Gemini manually.
    """
    g = StateGraph(TravelState)
    g.add_node("research", research_agent)
    g.add_node("weather", weather_agent)
    g.add_node("budget", budget_agent)
    g.add_node("transport", transport_agent)
    g.add_node("accommodation", accommodation_agent)
    g.add_node("activities", activity_agent)
    g.add_node("country", country_agent)
    g.add_node("media", media_agent)
    g.add_node("coordinator", coordinator_agent)

    g.add_edge("research", "weather")
    g.add_edge("weather", "budget")
    g.add_edge("budget", "transport")
    g.add_edge("transport", "accommodation")
    g.add_edge("accommodation", "activities")
    g.add_edge("activities", "country")
    g.add_edge("country", "media")
    g.add_edge("media", "coordinator")
    g.add_edge("coordinator", END)

    g.set_entry_point("research")
    return g.compile()


def build_full_graph_with_llm():
    """
    Original full graph (non-stream fallback), where LLM agent is inside the graph.
    """
    g = StateGraph(TravelState)

    g.add_node("research", research_agent)
    g.add_node("weather", weather_agent)
    g.add_node("budget", budget_agent)
    g.add_node("transport", transport_agent)
    g.add_node("accommodation", accommodation_agent)
    g.add_node("activities", activity_agent)
    g.add_node("country", country_agent)
    g.add_node("media", media_agent)
    g.add_node("coordinator", coordinator_agent)
    g.add_node("llm", llm_agent)  # non-stream inside node

    g.add_edge("research", "weather")
    g.add_edge("weather", "budget")
    g.add_edge("budget", "transport")
    g.add_edge("transport", "accommodation")
    g.add_edge("accommodation", "activities")
    g.add_edge("activities", "country")
    g.add_edge("country", "media")
    g.add_edge("media", "coordinator")
    g.add_edge("coordinator", "llm")
    g.add_edge("llm", END)

    g.set_entry_point("research")
    return g.compile()



@traceable
def llm_agent(state: TravelState):
    structured = state["structured_data"]
    days = state.get("days", 3)
    dest = state.get("destination", "")
    user_prompt = state.get("user_prompt", "")
    target_currency = state.get("target_currency", "USD")

    prompt = f"""
You are an intelligent travel planner. Using the structured data below, generate a complete {days}-day itinerary for {dest}, formatted as JSON.

Structured Data:
{structured}

Additional user request: {user_prompt}

Rules:
- If flight data is empty, suggest nearest airport & road/train options.
- If hotel data missing, suggest budget, mid-range, luxury options.
- Consider user interests: {state.get("interests", [])}.
- Ensure costs are in {target_currency}.
- Provide practical weather notes.

Output format:
{{
  "day_wise_plan": [
    {{
      "day": 1,
      "morning": "...",
      "afternoon": "...",
      "evening": "...",
      "meals": "...",
      "est_cost": "..."
    }}
  ],
  "weather_summary": "...",
  "top_attractions": ["...", "..."],
  "recommendations": ["...", "..."]
}}
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    state["itinerary"] = response.text
    return state



def _stream_structured_itinerary(structured: Any, days: int, dest: str, user_prompt: str, target_currency: str) -> Generator[str, None, str]:
    """Stream only the itinerary generation text (after graph prepared the data)."""
    prompt = f"""
You are an intelligent travel planner. Using the structured data below, generate a complete {days}-day itinerary for {dest}.

Structured Data:
{structured}

Additional user request: {user_prompt}

Guidelines:
- Day-wise detailed plan (morning/afternoon/evening), food spots, transport notes
- A short weather summary and practical tips
- Rough budget remarks in {target_currency}

Return clear Markdown (NOT JSON).
"""
    collected = ""
    stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=prompt
    )
    for chunk in stream:
        if hasattr(chunk, "text") and chunk.text:
            collected += chunk.text
            yield chunk.text
    return collected



@traceable
def generate_itinerary(user_request: dict) -> str:
    """
    Non-stream fallback for places where you want a single string result.
    """
    
    if "user_prompt" in user_request and len(user_request.keys()) <= 2:
        result = free_chat_chain.invoke({"user_prompt": user_request["user_prompt"]})
        try:
            log_usage("free_chat")
        except Exception:
            pass
        return result.content

    
    workflow = build_full_graph_with_llm()
    final_state = workflow.invoke({**user_request})
    text = final_state.get("itinerary", "")
    try:
        log_usage("structured")
    except Exception:
        pass
    return text


def generate_itinerary_stream(user_request: dict) -> Generator[str, None, str]:
    """
    Streaming version for BOTH modes.
    Yields chunks of text; returns full string at the end.
    """
    
    if "user_prompt" in user_request and len(user_request.keys()) <= 2:
        collected = ""
        for chunk in free_chat_chain.stream({"user_prompt": user_request["user_prompt"]}):
            text = getattr(chunk, "content", None) or ""
            if text:
                collected += text
                yield text
        
        try:
            log_usage("free_chat")
        except Exception:
            pass
        return collected

    
    prep_graph = build_prep_graph()
    state_pre = prep_graph.invoke({**user_request})
    structured = state_pre.get("structured_data", {})
    days = user_request.get("days", 3)
    dest = user_request.get("destination", "")
    user_prompt = user_request.get("user_prompt", "")
    target_currency = user_request.get("target_currency", "USD")

    collected_s = ""
    for part in _stream_structured_itinerary(structured, days, dest, user_prompt, target_currency):
        collected_s += part
        yield part

    try:
        log_usage("structured")
    except Exception:
        pass

    return collected_s
