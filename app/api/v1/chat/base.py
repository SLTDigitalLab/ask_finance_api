from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
import asyncio
import uuid
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from db.psql_connector import DB, default_config
import re
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from api.v1.chat.vectorstore import *
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch
from .document_agent import document_search_agent
from .app_types import AgentState
import spacy
from langsmith import trace
from .intent_detector import detect_intent, detect_intent_with_context
from .auth import verify_token, token_manager

nlp = spacy.load("en_core_web_sm")

logger = logging.getLogger(__name__)

load_dotenv()

LANGCHAIN_TRACING_V2 = "true"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

REQUEST_TIMEOUT = 30

db = DB(default_config())

class ChatRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    chat_id: str
    reasoning_chain: List[str] = []

class CollectionResponse(BaseModel):
    collection_id: str
    collection_name: str

# Global state management
chat_sessions: Dict[str, Dict] = {}
document_collections: Dict[str, Dict] = {}

# Collection-based storage
collection_documents: Dict[str, List[Dict]] = {}

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    logger.info("Successfully initialized Gemini embeddings")
except Exception as e:
    logger.error(f"Failed to initialize Gemini embeddings: {e}")
    embeddings = None

# Initialize search
search_tool = TavilySearch()

def get_default_collection_id() -> Optional[str]:
    """Get the most recently created collection ID as default."""
    db = None
    try:
        db = DB(default_config())
        
        query = "SELECT collection_id FROM collection ORDER BY created_at DESC LIMIT 1"
        cursor = db.exec(query)
        result = cursor.fetchone()
        
        if result and result[0]:
            collection_id = str(result[0]).strip()
            if collection_id:
                logger.info(f"Using most recent collection as default: {collection_id}")
                return collection_id
        
        logger.warning("No collections found in database")
        return None
        
    except Exception as e:
        logger.error(f"Error getting default collection: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return None
        
    finally:
        if db:
            try:
                db.close()
            except:
                pass

def create_initial_state(query: str, collection_ids: Optional[List[str]] = None) -> dict:
    """Create initial state with proper collection handling."""
    if not collection_ids:
        default_collection = get_default_collection_id()
        collection_ids = [default_collection] if default_collection else []

    return {
        "query": query,
        "answer": "",
        "sources": [],
        "pages": [],
        "images": [],
        "chat_id": str(uuid.uuid4()),
        "collection_id": collection_ids[0] if collection_ids else None,
        "chat_mode": "short",
        "cache_mode": False,
        "collection_mode": False,
        "search_results": None,
        "document_context": None,
        "reasoning_chain": [],
        "messages": [],
        "previous_context": None,
    }

def initialize_available_collections():
    """Initialize with any available collections from database."""
    try:
        create_collection()
        
        logger.info(f"Initialized collection")
        
    except Exception as e:
        logger.error(f"Error initializing collections: {e}")

initialize_available_collections()

user_sessions: Dict[str, Dict[str, Union[str, int]]] = {}

def convert_history_to_messages(history: List[Dict[str, str]]) -> List:
    """Convert DB chat history to LangChain messages."""
    messages = []
    for msg in history:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    return messages

def route_to_specific_agent(state: AgentState) -> str:
    """
    Enhanced routing function that uses destination context for intent detection.
    IMPORTANT: This function should NOT modify state, only return the next node name.
    """
    query = state.get("query", "")
    collection_id = state.get("collection_id")
    
    logger.info(f"[ROUTER] Routing query: {query}")
    logger.info(f"[ROUTER] Collection ID in state: {collection_id}")
    
    # Use enhanced intent detector with destination context
    detected_intent = detect_intent_with_context(query)

    # For greetings, still route to document_search_agent but synthesis_agent will handle it naturally
    if detected_intent == "GREETING":
        logger.info(f"[ROUTER] Detected greeting, routing to document_search_agent (will be handled in synthesis)")
        return "document_search_agent"
    elif detected_intent == "DOCUMENT":
        logger.info(f"[ROUTER] Routing to document_search_agent for domain: {collection_id}")
        return "document_search_agent"
    else:
        logger.info(f"[ROUTER] Defaulting to document_search_agent for domain: {collection_id}")
        return "document_search_agent"
    
def save_chat_to_db(chat_id: str, role: str, message: str):
    try:
        db = DB(default_config())

        logger.info(f"Saving {role} message to DB: chat_id={chat_id}")

        insert_query = """
        INSERT INTO ask_hr_history (chat_id, role, message, timestamp)
        VALUES (%s, %s, %s, NOW())
        """
        db.exec(insert_query, (chat_id, role, message))
        db.commit()
    except Exception as e:
        logger.error(f"Error saving message to database: {e}")
    finally:
        db.close()

def extract_subject_from_messages(messages: List[BaseMessage]) -> str:
    """Try to extract a subject entity from previous human/assistant messages."""
    for msg in reversed(messages):
        if isinstance(msg, (HumanMessage, AIMessage)):
            content = msg.content.lower()
            for word in content.split():
                if word.istitle() and word.lower() not in ['i', 'we', 'you', 'it', 'he', 'she', 'they']:
                    return word
    return ""

def enrich_query_with_context(query: str, messages: List[BaseMessage]) -> str:
    """Append previous subject to vague queries if found in chat history."""
    vague_keywords = [
        "its", "their", "there", "that city", "that place", "it",
        "what's its", "whats its", "what is its", "what's their",
        "whats their", "what is their", "this", "those", "they"
    ]
    lower_query = query.lower()

    if any(kw in lower_query for kw in vague_keywords):
        subject = extract_subject_from_messages(messages)
        if subject:
            enriched = f"{query} (referring to {subject})"
            logger.info(f"Enriched query: {enriched}")
            return enriched
        else:
            logger.info("No subject found to enrich the query.")
    else:
        logger.info("Query not considered vague.")

    return query

def coordinator_agent(state: AgentState) -> AgentState:
    """Enhanced coordinator with centralized destination memory."""
    query = state.get("query", "")
    chat_id = state.get("chat_id")
    collection_id = state.get("collection_id") 
    
    logger.info(f"[COORDINATOR] Processing query: {query}")
    logger.info(f"[COORDINATOR] Collection ID: {collection_id}")
    
    reasoning_chain = ["Coordinator: Analyzing query and routing to appropriate agents"]

    detected_intent = detect_intent(query)

    lower_query = query.lower()
    needs_document = detected_intent == "DOCUMENT" 

    state["needs_doc_search"] = needs_document
    state["reasoning_chain"] = reasoning_chain
    if collection_id:
        state["collection_id"] = collection_id

    active_agents = []
    
    if needs_document:
        active_agents.append("document")
        reasoning_chain.append("Enhanced Coordinator: Will route to document agent")
    
    if not active_agents:
        reasoning_chain.append("Enhanced Coordinator: No specific intent detected, defaulting to document search")
        active_agents.append("document (default)")

    logger.info(f"[COORDINATOR] Query: '{query}' -> Active agents: {active_agents} -> Domain: {collection_id}")
    return state

def synthesis_agent(state: AgentState) -> AgentState:
    with trace("synthesis_agent"):
        """Agent that synthesizes information and generates final response using only the document context."""

        query = state["query"]
        chat_id = state.get("chat_id")
        document_context = state.get("document_context", "")
        chat_mode = state.get("chat_mode", "short")

        # Check if this is a greeting or a conversational phrase before processing document context
        detected_intent = detect_intent(query)
        
        if detected_intent == "GREETING":
            # Handle various conversation phrases naturally without document search
            query_lower = query.lower().strip()
            
            # Conversation starters
            if any(word in query_lower for word in ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
                greeting_responses = [
                    "Hello! How can I help you today?",
                    "Hi there! What can I assist you with?", 
                    "Hello! Feel free to ask me any questions.",
                    "Hi! I'm here to help. What would you like to know?"
                ]
            
            # Thanks/acknowledgments
            elif any(word in query_lower for word in ["thanks", "thank you", "thank", "thx", "appreciate"]):
                greeting_responses = [
                    "You're welcome!",
                    "My pleasure!",
                    "Happy to help!",
                    "Glad I could assist!",
                    "Anytime!"
                ]
            
            # Conversation endings
            elif any(word in query_lower for word in ["bye", "goodbye", "see you", "farewell"]):
                greeting_responses = [
                    "Goodbye! Feel free to ask if you have more questions.",
                    "See you! Have a great day!",
                    "Bye! Come back anytime you need help.",
                    "Take care!"
                ]
            
            # Simple acknowledgments
            elif any(word in query_lower for word in ["ok", "okay", "alright", "sure", "got it", "cool", "nice"]):
                greeting_responses = [
                    "Great!",
                    "Alright!",
                    "Okay!",
                    "Sure thing!",
                    "Got it!"
                ]
            
            # Default greeting response
            else:
                greeting_responses = [
                    "Hello! How can I help you?",
                    "Hi there! What can I do for you?",
                    "Hello! I'm here to assist."
                ]
                
            import random
            state["answer"] = random.choice(greeting_responses)
            state["reasoning_chain"].append("Synthesis Agent: Responded naturally to greeting")
            state["sources"] = []
            return state

        context_parts = []
        if document_context and document_context != "No relevant documents found.":
            context_parts.append(f"Document Context:\n{document_context}")

        context = "\n\n".join(context_parts) if context_parts else ""

        system_prompt = """You are a helpful AI assistant that provides clear and concise responses.
Use ONLY the provided document context to answer clearly and accurately.
Focus on the most important information.

IMPORTANT INSTRUCTIONS:
- Use ONLY the provided document context.
- If no document context is provided or it doesn't contain the answer, respond with:
  "I couldn’t find relevant information in the knowledge base."
- Never use general or world knowledge.
"""

        if not document_context or document_context == "No relevant documents found.":
            state["answer"] = "I couldn’t find relevant information in the knowledge base."
            state["reasoning_chain"].append(
                "Synthesis Agent: Blocked general knowledge, no relevant documents found."
            )
            return state

        try:
            if not os.getenv("GOOGLE_API_KEY"):
                response_parts = [
                    f"Based on the available information:\n\n{context[:1000]}..."
                ]
                state["answer"] = "\n".join(response_parts)
                state["reasoning_chain"].append(
                    "Synthesis Agent: Used fallback response (no Gemini API key)."
                )
                return state

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.7,
                convert_system_message_to_human=True,
            )

            prompt_content = f"""
{system_prompt}

Current User Question: "{query}"

Document Context:
{context}

Answer ONLY using the document context. If not found, say:
"I couldn’t find relevant information in the knowledge base."
"""

            response = llm.invoke([HumanMessage(content=prompt_content)])
            answer = response.content

            state["answer"] = answer
            state["reasoning_chain"].append("Synthesis Agent: Used document-only reasoning.")
            return state

        except Exception as e:
            response_parts = [
                f"Error: {str(e)}",
                f"Based on available context:\n\n{context[:1000]}..."
            ]
            state["answer"] = "\n".join(response_parts)
            state["reasoning_chain"].append(f"Synthesis Agent: Error occurred - {str(e)}")
            logger.error(f"Synthesis failed: {e}")
            return state


def should_continue(state: AgentState) -> str:
    with trace("should_continue"):
        """Determine if we should continue processing or end."""
        if state.get("answer"):
            return END
        return "synthesis_agent"
    
def debug_state_node(state: AgentState) -> AgentState:
    """Debug node to inspect state between coordinator and document agent."""
    logger.info(f"[DEBUG_NODE] === State Inspection ===")
    logger.info(f"[DEBUG_NODE] collection_id: {state.get('collection_id')}")
    logger.info(f"[DEBUG_NODE] query: {state.get('query')}")
    logger.info(f"[DEBUG_NODE] All keys: {list(state.keys())}")
    logger.info(f"[DEBUG_NODE] === End State Inspection ===")
    return state

def create_chat_graph():
    with trace("create_chat_graph"):
        """Create the LangGraph workflow with proper routing."""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("coordinator", coordinator_agent)
        workflow.add_node("debug_state", debug_state_node) 
        workflow.add_node("document_search_agent", document_search_agent)
        
        workflow.add_node("synthesis_agent", synthesis_agent)
        
        workflow.set_entry_point("coordinator")

        workflow.add_edge("coordinator", "debug_state") 

        workflow.add_conditional_edges(
            "debug_state", 
            route_to_specific_agent,
            { 
                "document_search_agent": "document_search_agent"
            }
        )
        
        workflow.add_edge("document_search_agent","synthesis_agent" )

        workflow.add_edge("synthesis_agent", END)
    
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        
        return app
    
chat_graph = create_chat_graph()

def get_or_create_chat_session(chat_id: str = None) -> str:
    """Return the provided chat_id if it exists, otherwise create a new one."""
    if chat_id and chat_id in chat_sessions:
        return chat_id

    new_chat_id = str(uuid.uuid4())
    chat_sessions[new_chat_id] = {
        "messages": [],
        "created_at": datetime.now()
    }
    return new_chat_id


@router.post("/{domain}/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    request: ChatRequest,
    domain: str,
    token: str = Depends(token_manager.verify_frontend_token)
):
    with trace("chat_endpoint"):
        """Main chat endpoint."""
        try:
            logger.info(f"[CHAT_ENDPOINT] Received request for domain: '{domain}'")
            logger.info(f"[CHAT_ENDPOINT] Query: {request.query}")
            
            chat_id = request.chat_id or str(uuid.uuid4())

            db = DB(default_config())
            try:
                cursor = db.exec(
                    """
                    SELECT role, message FROM ask_hr_history
                    WHERE chat_id = %s
                    ORDER BY timestamp ASC
                    """,
                    (chat_id,)
                )
                history_rows = cursor.fetchall() if cursor else []
            except Exception as db_error:
                logger.error(f"DB error when loading chat history: {db_error}")
                history_rows = []
            finally:
                db.close()

            history_messages = []
            for row in history_rows:
                role = row["role"]
                content = row["message"]
                if role == "user":
                    history_messages.append({"role": "user", "content": content})
                elif role == "assistant":
                    history_messages.append({"role": "assistant", "content": content})

            # Get the last 5 user-assistant pairs (10 messages)
            limited_history = history_messages[-10:] if len(history_messages) > 10 else history_messages
            messages = convert_history_to_messages(limited_history)

            # Append the current message
            messages.append(HumanMessage(content=request.query))

            # Create text-based previous context
            previous_context = "\n".join([
                f"User: {m['content']}" if m["role"] == "user" else f"Assistant: {m['content']}"
                for m in limited_history
            ])

            # Append the current message
            messages.append(HumanMessage(content=request.query))

            initial_state = AgentState(
                messages=[HumanMessage(content=request.query)],
                query=request.query,
                answer="",
                sources=[],
                pages=[],
                chat_id=chat_id,
                search_results=None,
                document_context=None,
                reasoning_chain=[],
                previous_context=previous_context,
                collection_id=domain, 
            )
            
            logger.info(f"[CHAT_ENDPOINT] Initial state collection_id: {initial_state.get('collection_id')}")

            config = {"configurable": {"thread_id": chat_id}}
            final_state = await asyncio.to_thread(
                chat_graph.invoke, 
                initial_state, 
                config
            )

            logger.info(f"[CHAT_ENDPOINT] Final state used domain: {final_state.get('collection_id')}")
            logger.info(f"[CHAT_ENDPOINT] Document found: {final_state.get('document_found')}")
            logger.info(f"[CHAT_ENDPOINT] Reasoning chain: {final_state.get('reasoning_chain')}")

            if chat_id not in chat_sessions:
                chat_sessions[chat_id] = {"messages": []}
            chat_sessions[chat_id]["messages"].extend([
                {"role": "user", "content": request.query},
                {"role": "assistant", "content": final_state["answer"]}
            ])
            
            save_chat_to_db(chat_id=chat_id, role="user", message=request.query)
            save_chat_to_db(chat_id=chat_id, role="assistant", message=final_state["answer"])
            
            return ChatResponse(
                answer=final_state["answer"],
                sources=final_state.get("sources", []),
                chat_id=chat_id,
                reasoning_chain=final_state.get("reasoning_chain", []),
            )
            
        except Exception as e:
            logger.error(f"[CHAT_ENDPOINT] Chat endpoint error: {e}")
            import traceback
            logger.error(f"[CHAT_ENDPOINT] Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
        

@router.get("/health", tags=["Chat"])
async def health_check(
    token: str = Depends(verify_token)
):
    """Health check endpoint."""
    return {"status": "healthy. Lets start", "timestamp": datetime.now()}

@router.get("/debug/check-data", tags=["Database"])
async def debug_check_data(
    token: str = Depends(verify_token)
):
    """Simple check to see what's in the database."""
    try:
        db = DB(default_config())
        
        db.exec("SELECT COUNT(*) as count FROM ask_hr_history")
        total_result = db.fetchone()
        total_count = total_result["count"] if total_result else 0
        
        db.exec("SELECT chat_id, role, message, timestamp FROM ask_hr_history ORDER BY timestamp DESC LIMIT 10")
        sample_records = db.fetchall()
        
        db.exec("SELECT DISTINCT chat_id FROM ask_hr_history")
        distinct_ids = db.fetchall()
        
        return {
            "total_records": total_count,
            "distinct_chat_ids": [row["chat_id"] for row in distinct_ids] if distinct_ids else [],
            "sample_records": sample_records if sample_records else []
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@router.get("/sessions", tags=["Database"])
async def get_all_chat_sessions(
    token: str = Depends(verify_token)
):
    """Get all unique chat session IDs from the database."""
    try:
        db = DB(default_config())
        db.exec(
            """
            CREATE TABLE IF NOT EXISTS ask_hr_history (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()
        db.exec(
            """
            SELECT DISTINCT chat_id, 
                   MIN(timestamp) as first_message_time,
                   MAX(timestamp) as last_message_time,
                   COUNT(*) as message_count
            FROM ask_hr_history 
            WHERE chat_id IS NOT NULL
            GROUP BY chat_id 
            ORDER BY last_message_time DESC
            """
        )
        sessions = db.fetchall()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "chat_id": session["chat_id"],
                "first_message_time": session["first_message_time"],
                "last_message_time": session["last_message_time"],
                "message_count": session["message_count"]
            })
        
        return {
            "status": "success",
            "total_sessions": len(session_list),
            "sessions": session_list
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat sessions: {str(e)}")
    finally:
        db.close()


@router.get("/session/{session_id}/history", tags=["Database"])
async def get_session_history(
    session_id: str,
    token: str = Depends(verify_token)
    ):
    """Get chat history for a specific session ID."""
    try:
        db = DB(default_config())
        db.exec(
            """
            SELECT role, message, timestamp
            FROM ask_hr_history
            WHERE chat_id = %s
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )
        history = db.fetchall()
        
        return {
            "session_id": session_id,
            "message_count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Error fetching session history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session history: {str(e)}")
    finally:
        db.close()


@router.delete("/session/{session_id}", tags=["Database"])
async def delete_session(
    session_id: str,
    token: str = Depends(token_manager.verify_admin_token)
    ):
    """Delete all messages for a specific session ID."""
    try:
        db = DB(default_config())
        db.exec(
            """
            DELETE FROM ask_hr_history
            WHERE chat_id = %s
            """,
            (session_id,)
        )
        db.commit()
        
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        
        return {
            "status": "success",
            "message": f"Deleted messages for session {session_id}"
        }
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
    finally:
        db.close()

async def get_chats():
    try:
        db = DB(default_config())
        db.exec("SELECT * FROM ask_hr_history ORDER BY timestamp DESC LIMIT 10")
        rows = db.fetchall()
        return {"chats": rows}
    except Exception as e:
        logger.error(f"Failed to fetch chats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chats")
    finally:
        db.close()