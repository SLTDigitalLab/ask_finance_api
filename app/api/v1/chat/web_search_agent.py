from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import os
import requests
from dotenv import load_dotenv
import re
import spacy
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from .app_types import AgentState

logger = logging.getLogger(__name__)

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import APIRouter
router = APIRouter()

security = HTTPBearer()

class ChatRequest(BaseModel):
    query: str
    answer: str = ""
    collection_id: Optional[List[str]] = None
    chat_mode: str = "short"
    cache_mode: bool = False
    collection_mode: bool = False

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    pages: List[int] = []
    images: List[str] = []
    chat_id: str
    reasoning_chain: List[str] = []

class CollectionResponse(BaseModel):
    collection_id: str
    collection_name: str

chat_sessions: Dict[str, Dict] = {}
document_collections: Dict[str, Dict] = {}

collection_documents: Dict[str, List[Dict]] = {}

search_tool = TavilySearch()

def create_web_search_tool():
    """Create web search tool with proper error handling."""
    try:
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            logger.error("TAVILY_API_KEY not found in environment variables")
            return None
        
        logger.info("Initializing Tavily search tool...")
        return TavilySearch(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
    except Exception as e:
        logger.error(f"Failed to initialize Tavily search tool: {e}")
        return None

# Initialize search tool
search_tool = create_web_search_tool()

@tool
def web_search_enhanced(query: str) -> str:
    """Enhanced web search with better error handling and debugging."""
    try:
        if not search_tool:
            logger.error("Search tool not initialized")
            return "Web search tool not available. Please check TAVILY_API_KEY configuration."
        
        logger.info(f"Performing web search for query: '{query}'")
        results = search_tool.invoke(query)
        logger.info(f"Web search returned: {type(results)}")
        
        if isinstance(results, dict):
            if "results" in results:
                search_results = results["results"]
            else:
                search_results = [results]
        elif isinstance(results, list):
            search_results = results
        else:
            search_results = [results]
        
        if search_results:
            formatted_results = []
            for i, result in enumerate(search_results[:5]):
                if isinstance(result, dict):
                    title = result.get("title", f"Result {i+1}")
                    url = result.get("url", "No URL")
                    content = result.get("content", result.get("snippet", "No content"))
                    formatted_results.append(f"Title: {title}\nURL: {url}\nContent: {content[:300]}...\n")
                else:
                    formatted_results.append(f"Result {i+1}: {str(result)[:300]}...\n")
            
            result_text = "\n".join(formatted_results)
            logger.info(f"Web search successful - {len(result_text)} characters returned")
            return result_text
        else:
            logger.warning("No results returned from web search")
            return "No relevant web results found."
            
    except Exception as e:
        logger.error(f"Web search failed: {e}", exc_info=True)
        return f"Web search failed: {str(e)}"

def alternative_web_search(query: str) -> str:
    """Alternative web search using direct Tavily API calls."""
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Tavily API key not configured."
        
        url = "https://api.tavily.com/search"
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": True,
            "max_results": 5
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Making direct API call to Tavily for query: '{query}'")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Direct API response keys: {data.keys()}")
            
            if "results" in data:
                results = []
                for result in data["results"]:
                    title = result.get("title", "No title")
                    url = result.get("url", "No URL")
                    content = result.get("content", "No content")
                    results.append(f"Title: {title}\nURL: {url}\nContent: {content[:200]}...\n")
                
                return "\n\n".join(results)
            else:
                return f"Unexpected response format: {data}"
        else:
            logger.error(f"Direct API request failed: {response.status_code} - {response.text}")
            return f"API request failed with status {response.status_code}: {response.text}"
            
    except Exception as e:
        logger.error(f"Alternative web search failed: {e}")
        return f"Alternative web search failed: {str(e)}"

# Pronouns to help resolve ambiguous references
PRONOUNS = {"there": "they", "them": "they", "their": "their", "theirs": "theirs", "themselves": "themselves"}

# Load spaCy model globally (do once)
nlp = spacy.load("en_core_web_sm")

def extract_destination_from_query(query: str) -> Optional[str]:
    """
    Extract possible location/place from query using spaCy NER.
    Returns first detected GPE or LOC entity or None if not found.
    """
    doc = nlp(query)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            return ent.text
    return None

def web_search_agent(state: AgentState) -> AgentState:
    """Enhanced web search agent with centralized destination memory."""
    query = state.get("query", "")
    reasoning = state.get("reasoning_chain", [])
    chat_id = state.get("chat_id")
    
    words = query.lower().split()
    web_keywords = ["current", "recent", "latest", "news", "today", "2024", "2025", "weather", "stock", "price", "now"]
    needs_web_search = any(keyword in words for keyword in web_keywords)
    
    if not needs_web_search:
        reasoning.append("Web Search Agent: No web search keywords detected, skipping web search")
        state["search_results"] = ""
        state["reasoning_chain"] = reasoning
        return state
    
    enhanced_query = query
    
    try:
        logger.info(f"Web search agent processing query: '{enhanced_query}'")
        search_results = web_search_enhanced.invoke(enhanced_query)
        
        if not search_results or "failed" in search_results.lower():
            logger.info("Enhanced search failed, trying alternative search")
            search_results = alternative_web_search(enhanced_query)
        
        if search_results and "failed" not in search_results.lower() and len(search_results.strip()) > 0:
            state["search_results"] = search_results
            reasoning.append(f"Web Search Agent: Successfully retrieved {len(search_results)} characters of web results")
            logger.info(f"Web search successful for query: '{enhanced_query}'")
        else:
            state["search_results"] = ""
            reasoning.append(f"Web Search Agent: No useful results found")
            logger.warning(f"Web search failed for query: '{enhanced_query}'")
        
    except Exception as e:
        state["search_results"] = ""
        reasoning.append(f"Web Search Agent: Exception occurred - {str(e)}")
        logger.error(f"Web search agent error for query '{enhanced_query}': {e}", exc_info=True)
    
    state["reasoning_chain"] = reasoning
    return state