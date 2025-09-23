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
from typing import Optional, List, Dict
from api.v1.chat.vectorstore import *
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .app_types import AgentState
from .auth import verify_token, token_manager 
import pdfplumber
import docx
import io
import requests
from fastapi import Query

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

class HRKBRequest(BaseModel):
    folder_id: str
    token: str  # Graph API access token
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class LinkRequest(BaseModel):
    urls: List[HttpUrl]
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class LinkResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    collection_id: str
    title: str
    content_length: int
    chunks_created: int
    images: List[str] = []
    internal_links: List[str] = []
    metadata: Dict = {}

class BulkLinkRequest(BaseModel):
    urls: List[HttpUrl]
    collection_id: str
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

chat_sessions: Dict[str, Dict] = {}
document_collections: Dict[str, Dict] = {}
# vector_stores: Dict[str, FAISS] = {}
collection_documents: Dict[str, List[Dict]] = {}

# try:
#     embeddings = OpenAIEmbeddings()
# except Exception as e:
#     logger.error(f"Failed to initialize OpenAI embeddings: {e}")
#     embeddings = None

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

def save_chat_to_db(chat_id: str, role: str, message: str):
    """Save chat message to database."""
    db = None
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()

        logger.info(f"Saving {role} message to DB: chat_id={chat_id}")

        insert_query = """
        INSERT INTO virtual_kandy_chat_history_new (chat_id, role, message, timestamp)
        VALUES (%s, %s, %s, NOW())
        """
        cursor.execute(insert_query, (chat_id, role, message))
        db.conn.commit()
        
    except Exception as e:
        logger.error(f"Error saving message to database: {e}")
    finally:
        if db:
            try:
                db.close()
            except:
                pass

def get_chat_history(chat_id: str):
    """Get chat history from database."""
    db = None
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()
        
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

def test_database_connection():
    """Test database connection and methods."""
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        logger.info(f"Database connection test successful: {result}")
        
        # Test collection table
        cursor.execute("SELECT COUNT(*) FROM collection")
        count = cursor.fetchone()[0]
        logger.info(f"Collection table has {count} records")
        
        # Test documents table  
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        logger.info(f"Documents table has {doc_count} records")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


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
            
            # Additional metadata
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
        if "@microsoft.graph.downloadUrl" in item:  # Skip folders
            download_url = item["@microsoft.graph.downloadUrl"]
            file_resp = requests.get(download_url)
            file_resp.raise_for_status()
            file_bytes = file_resp.content
            name = item["name"].lower()

            # Detect file type
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


def extract_images_and_links(html_content: str, base_url: str) -> tuple[List[str], List[str]]:
    """Extract images and links from HTML content."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            img_url = urljoin(base_url, img['src'])
            if img_url not in images:
                images.append(img_url)
        
        # Extract internal links
        internal_links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            link_url = urljoin(base_url, link['href'])
            link_domain = urlparse(link_url).netloc
            
            # Only include internal links
            if link_domain == base_domain and link_url not in internal_links:
                internal_links.append(link_url)
        
        return images, internal_links
        
    except Exception as e:
        logger.error(f"Error extracting images and links: {e}")
        return [], []

def chunk_content(content: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split content into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_text(content)
    return chunks


@router.post("/add_data", tags=["Vectorstore"])
async def add_data_to_collection(
    request: LinkRequest,
    api_secret = os.getenv("ADMIN_TOKEN")
    ):
    result = {"status":"", "message":""}

    try:
        async with aiohttp.ClientSession() as session:
            contents = ""
            for link in request.urls:
                content, metadata = await fetch_page_content(session, str(link))
                contents += content

            chunks = chunk_content(contents, request.chunk_size, request.chunk_overlap)

            logger.info(f"Successfully processed link {request.urls} into {len(chunks)} chunks")

            upsert_result = add_texts(chunks)

            result["status"] = "success"
            result["message"] = str(upsert_result["status"])

            return result

    except Exception as e:
        logger.error(f"Error processing link {request.url}: {e}")
        result["status"] = "failed"
        result["message"] = str(e)
        return result

@router.post("/add_hr_kb", tags=["Vectorstore"])
async def add_hr_kb_to_collection(request: HRKBRequest):
    """
    Add documents from a OneDrive folder into the vector store.
    Works similar to /add_data, but sources from OneDrive.
    """
    result = {"status": "", "message": ""}

    try:
        # Fetch all docs in the OneDrive folder
        docs = await fetch_onedrive_folder_docs(request.folder_id, request.token)
        
        if not docs:
            return {"status": "failed", "message": "No documents found in OneDrive folder"}

        all_chunks = []
        for doc in docs:
            chunks = chunk_content(doc["content"], request.chunk_size, request.chunk_overlap)
            all_chunks.extend(chunks)
            logger.info(f"Processed OneDrive file {doc['name']} into {len(chunks)} chunks")

        # Upsert into vector store
        upsert_result = add_texts(all_chunks)

        result["status"] = "success"
        result["message"] = f"Inserted {len(all_chunks)} chunks from {len(docs)} OneDrive docs"
        return result

    except Exception as e:
        logger.error(f"Error processing OneDrive folder {request.folder_id}: {e}")
        result["status"] = "failed"
        result["message"] = str(e)
        return result

@router.get("/collections", tags=["Vectorstore"])
async def list_collections(
    api_secret = os.getenv("API_SECRET_TOKEN")
):
    """Get all available collections from the database."""
    collection = get_all_collections()
    return {
        "collections": collection,
        "total_count": len(collection)
    }



@router.get("/chunks", tags=["Vectorstore"])
async def list_collections(
    api_secret = os.getenv("API_SECRET_TOKEN")
):
    """Get all available chunks in the collection."""
    chunks = get_all_points()
    return {
        "chunks": chunks,
        "total_count": len(chunks)
    }



@router.delete("/delete", tags=["Vectorstore"])
async def drop_collection(
    api_secret = os.getenv("ADMIN_TOKEN")
):
    """Delete all available chunks in the collection."""
    try:
        delete_collection()
        return {
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "failed"
        }

def document_search_agent(state: AgentState) -> AgentState:
    """Enhanced document search agent with centralized destination memory."""
    query = state["query"]
    chat_id = state.get("chat_id")

    # Run similarity search
    docs = search_similar(query)

    if not docs:
        state["document_found"] = False
        state["reasoning_chain"].append("Document Search Agent: No documents found in vector store")
        return state

    # Build context
    context = "\n\n".join(
        [r["payload"]["page_content"] for r in docs if "page_content" in r.get("payload", {})]
    )

    if context.strip():
        state["document_context"] = context.strip()
        state["reasoning_chain"].append("Document Search Agent: Retrieved context from vector store")
        state["sources"] = [r["id"] for r in docs]  # or metadata if available
        state["document_found"] = True
    else:
        state["document_found"] = False
        state["reasoning_chain"].append("Document Search Agent: Retrieved docs but no usable text")

    return state
