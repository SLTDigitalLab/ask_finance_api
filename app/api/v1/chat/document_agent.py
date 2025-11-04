from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
import logging
import os
import aiohttp
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import trafilatura
from readability import Document
from db.psql_connector import DB, default_config
from api.v1.chat.vectorstore import *
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .app_types import AgentState
from .auth import verify_token, token_manager 
import pdfplumber
import docx
import io
import requests

GRAPH_URL = "https://graph.microsoft.com/v1.0"

logger = logging.getLogger(__name__)

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

REQUEST_TIMEOUT = 30

security = HTTPBearer()

class ChatRequest(BaseModel):
    query: str
    answer: str = ""
    domain: str = "default"
    chat_mode: str = "short"
    cache_mode: bool = False

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    pages: List[int] = []
    images: List[str] = []
    chat_id: str
    reasoning_chain: List[str] = []
    domain: str 

class DomainRequest(BaseModel):
    domain: str
    description: Optional[str] = None

class DomainResponse(BaseModel):
    domain: str
    collection_name: str
    status: str
    points_count: Optional[int] = None

class HRKBRequest(BaseModel):
    folder_id: str
    token: str
    domain: str = "hr"
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class LinkRequest(BaseModel):
    urls: List[HttpUrl]
    domain: str  # Added domain field
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class LinkResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    domain: str  # Added domain field
    title: str
    content_length: int
    chunks_created: int
    images: List[str] = []
    internal_links: List[str] = []
    metadata: Dict = {}

class BulkLinkRequest(BaseModel):
    urls: List[HttpUrl]
    domain: str  # Added domain field
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200
    extract_images: Optional[bool] = False
    extract_links: Optional[bool] = False

class BulkLinkResponse(BaseModel):
    success: bool
    processed: int
    failed: int
    results: List[LinkResponse]
    errors: List[str] = []
    domain: str  # Added domain field

chat_sessions: Dict[str, Dict] = {}
document_collections: Dict[str, Dict] = {}
collection_documents: Dict[str, List[Dict]] = {}

search_tool = TavilySearchResults()

logger = logging.getLogger(__name__)

def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def parse_text(file_bytes: bytes) -> str:
    """Default handler for txt/md/json/etc."""
    return file_bytes.decode("utf-8", errors="ignore")

def save_chat_to_db(chat_id: str, role: str, message: str, domain: str = "default"):
    """Save chat message to database with domain."""
    db = None
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()

        logger.info(f"Saving {role} message to DB: chat_id={chat_id}, domain={domain}")

        insert_query = """
        INSERT INTO virtual_kandy_chat_history_new (chat_id, role, message, domain, timestamp)
        VALUES (%s, %s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (chat_id, role, message, domain))
        db.conn.commit()
        
    except Exception as e:
        logger.error(f"Error saving message to database: {e}")
    finally:
        if db:
            try:
                db.close()
            except:
                pass

def get_chat_history(chat_id: str, domain: Optional[str] = None):
    """Get chat history from database, optionally filtered by domain."""
    db = None
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()
        
        if domain:
            query = """
            SELECT role, message FROM virtual_kandy_chat_history_new
            WHERE chat_id = %s AND domain = %s
            ORDER BY timestamp ASC
            """
            cursor.execute(query, (chat_id, domain))
        else:
            query = """
            SELECT role, message FROM virtual_kandy_chat_history_new
            WHERE chat_id = %s
            ORDER BY timestamp ASC
            """
            cursor.execute(query, (chat_id,))
        
        result = cursor.fetchall()
        
        history = []
        for row in result:
            history.append({
                "role": row[0],
                "content": row[1]
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")
        return []
    finally:
        if db:
            try:
                db.close()
            except:
                pass

async def fetch_page_content(session: aiohttp.ClientSession, url: str) -> tuple[str, Dict]:
    """Fetch and extract content from a web page."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with session.get(str(url), headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch URL: HTTP {response.status}")
            
            html_content = await response.text()

            content = ""
            title = ""
            metadata = {}
            
            try:
                extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True)
                if extracted:
                    content = extracted

                    metadata_extracted = trafilatura.extract_metadata(html_content)
                    if metadata_extracted:
                        title = metadata_extracted.title or ""
                        metadata.update({
                            'author': metadata_extracted.author,
                            'date': str(metadata_extracted.date) if metadata_extracted.date else None,
                            'description': metadata_extracted.description,
                            'categories': metadata_extracted.categories,
                            'tags': metadata_extracted.tags
                        })
            except Exception as e:
                logger.warning(f"Trafilatura extraction failed: {e}")
            
            if not content:
                try:
                    doc = Document(html_content)
                    content = doc.summary()
                    title = doc.title()
                except Exception as e:
                    logger.warning(f"Readability extraction failed: {e}")
            
            if not content:
                try:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    if not title:
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else ""
                    
                    content = soup.get_text()
                    
                    lines = (line.strip() for line in content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    
                except Exception as e:
                    logger.error(f"BeautifulSoup extraction failed: {e}")
                    content = html_content
            
            if not content:
                raise HTTPException(status_code=400, detail="Failed to extract content from the webpage")
            
            metadata.update({
                'url': str(url),
                'title': title,
                'content_length': len(content),
                'extraction_method': 'trafilatura' if 'trafilatura' in str(type(content)) else 'readability' if 'readability' in str(type(content)) else 'beautifulsoup'
            })
            
            return content, metadata
            
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

async def fetch_onedrive_folder_docs(folder_id: str, token: str):
    """Fetch all files in a OneDrive folder and extract their text."""
    url = f"{GRAPH_URL}/me/drive/items/{folder_id}/children"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    items = response.json().get("value", [])

    docs = []
    for item in items:
        if "@microsoft.graph.downloadUrl" in item:
            download_url = item["@microsoft.graph.downloadUrl"]
            file_resp = requests.get(download_url)
            file_resp.raise_for_status()
            file_bytes = file_resp.content
            name = item["name"].lower()

            if name.endswith(".docx"):
                file_text = parse_docx(file_bytes)
            elif name.endswith(".pdf"):
                file_text = parse_pdf(file_bytes)
            elif name.endswith((".txt", ".md", ".json")):
                file_text = parse_text(file_bytes)
            else:
                logger.warning(f"Skipping unsupported file type: {item['name']}")
                continue

            if file_text.strip():
                docs.append({
                    "id": item["id"],
                    "name": item["name"],
                    "content": file_text
                })
    return docs

def chunk_content(content: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split content into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(content)
    return chunks

@router.post("/domains/create", tags=["Domains"], response_model=DomainResponse)
async def create_domain(
    request: DomainRequest,
    token: str = Depends(token_manager.verify_admin_token)
):
    """Create a new domain collection."""
    try:
        status = create_collection(domain=request.domain)
        stats = get_domain_stats(request.domain)
        
        return DomainResponse(
            domain=request.domain,
            collection_name=stats.get("collection_name", ""),
            status=status,
            points_count=stats.get("points_count", 0)
        )
    except Exception as e:
        logger.error(f"Error creating domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains", tags=["Domains"])
async def list_domains(
    token: str = Depends(verify_token)
):
    """List all available domains."""
    try:
        collections = get_all_collections()
        
        domain_info = []
        for col in collections:
            stats = get_domain_stats(col["domain"])
            domain_info.append({
                "domain": col["domain"],
                "collection_name": col["collection_name"],
                "points_count": stats.get("points_count", 0),
                "status": stats.get("status", "unknown")
            })
        
        return {
            "domains": domain_info,
            "total_count": len(domain_info)
        }
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/domains/{domain}/stats", tags=["Domains"])
async def get_domain_statistics(
    domain: str,
    token: str = Depends(verify_token)
):
    """Get statistics for a specific domain."""
    try:
        stats = get_domain_stats(domain)
        if not stats.get("exists"):
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting domain stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/domains/{domain}", tags=["Domains"])
async def delete_domain(
    domain: str,
    token: str = Depends(token_manager.verify_admin_token)
):
    """Delete a domain and its collection."""
    try:
        delete_collection(domain=domain)
        return {
            "status": "success",
            "message": f"Domain '{domain}' deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add_data", tags=["Vectorstore"])
async def add_data_to_collection(
    request: LinkRequest,
):
    """Add web content to a specific domain."""
    result = {"status": "", "message": "", "domain": request.domain}

    try:
        async with aiohttp.ClientSession() as session:
            contents = ""
            for link in request.urls:
                content, metadata = await fetch_page_content(session, str(link))
                contents += content

            chunks = chunk_content(contents, request.chunk_size, request.chunk_overlap)

            logger.info(f"Successfully processed {len(request.urls)} links into {len(chunks)} chunks for domain '{request.domain}'")

            upsert_result = add_texts(chunks, domain=request.domain)

            result["status"] = "success"
            result["message"] = f"Added {len(chunks)} chunks to domain '{request.domain}'"

            return result

    except Exception as e:
        logger.error(f"Error processing links for domain '{request.domain}': {e}")
        result["status"] = "failed"
        result["message"] = str(e)
        return result

@router.post("/add_hr_kb", tags=["Vectorstore"])
async def add_hr_kb_to_collection(
    request: HRKBRequest,
):
    """Add OneDrive documents to a specific domain."""
    result = {"status": "", "message": "", "domain": request.domain}

    try:
        docs = await fetch_onedrive_folder_docs(request.folder_id, request.token)
        
        if not docs:
            return {"status": "failed", "message": "No documents found in OneDrive folder", "domain": request.domain}

        all_chunks = []
        for doc in docs:
            chunks = chunk_content(doc["content"], request.chunk_size, request.chunk_overlap)
            all_chunks.extend(chunks)
            logger.info(f"Processed OneDrive file {doc['name']} into {len(chunks)} chunks")

        upsert_result = add_texts(all_chunks, domain=request.domain)

        result["status"] = "success"
        result["message"] = f"Inserted {len(all_chunks)} chunks from {len(docs)} OneDrive docs to domain '{request.domain}'"
        return result

    except Exception as e:
        logger.error(f"Error processing OneDrive folder for domain '{request.domain}': {e}")
        result["status"] = "failed"
        result["message"] = str(e)
        return result

@router.get("/chunks/{domain}", tags=["Vectorstore"])
async def list_domain_chunks(
    domain: str,
    token: str = Depends(verify_token)
):
    """Get all chunks in a specific domain."""
    try:
        chunks = get_all_points(domain=domain)
        return {
            "domain": domain,
            "chunks": chunks,
            "total_count": len(chunks)
        }
    except Exception as e:
        logger.error(f"Error listing chunks for domain '{domain}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

def document_search_agent(state: AgentState) -> AgentState:
    """Enhanced document search agent with domain support."""
    query = state["query"]
    domain = state.get("collection_id")

    if domain is None:
        logger.error(f"[DOCUMENT_AGENT] collection_id is None! State keys: {state.keys()}")
        logger.error(f"[DOCUMENT_AGENT] Full state: {state}")
        domain = "default"
    
    chat_id = state.get("chat_id")

    logger.info(f"[DOCUMENT_AGENT] Searching in domain '{domain}' for query: {query}")
    logger.info(f"[DOCUMENT_AGENT] Full state collection_id: {state.get('collection_id')}")

    docs = search_similar(query, domain=domain)
    
    logger.info(f"[DOCUMENT_AGENT] Found {len(docs)} documents in domain '{domain}'")

    if not docs:
        state["document_found"] = False
        state["reasoning_chain"].append(f"Document Search Agent: No documents found in domain '{domain}'")
        logger.warning(f"[DOCUMENT_AGENT] No documents found in domain '{domain}'")
        return state

    # Build context
    context = "\n\n".join(
        [r["payload"]["page_content"] for r in docs if "page_content" in r.get("payload", {})]
    )

    if context.strip():
        state["document_context"] = context.strip()
        state["reasoning_chain"].append(f"Document Search Agent: Retrieved context from domain '{domain}' ({len(docs)} docs)")
        state["sources"] = [r["id"] for r in docs]
        state["document_found"] = True
        logger.info(f"[DOCUMENT_AGENT] Successfully retrieved context from domain '{domain}'")
    else:
        state["document_found"] = False
        state["reasoning_chain"].append(f"Document Search Agent: Retrieved docs from domain '{domain}' but no usable text")
        logger.warning(f"[DOCUMENT_AGENT] Documents found but no usable text in domain '{domain}'")

    return state
