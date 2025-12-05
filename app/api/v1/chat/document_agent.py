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
from .context_manager import context_manager
from fastapi import Query
import email
from email import policy
from email.parser import BytesParser
from PIL import Image
import asyncio
import tempfile
import base64
import zipfile
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from google import genai
from google.genai import types



GRAPH_URL = "https://graph.microsoft.com/v1.0"

GEMINI_OCR_URL = "https://api.gemini.ai/v1/vision/ocr"  

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
    domain: str 
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200

class LinkResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    domain: str  
    title: str
    content_length: int
    chunks_created: int
    images: List[str] = []
    internal_links: List[str] = []
    metadata: Dict = {}

class BulkLinkRequest(BaseModel):
    urls: List[HttpUrl]
    domain: str  
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
    domain: str  

chat_sessions: Dict[str, Dict] = {}
document_collections: Dict[str, Dict] = {}
collection_documents: Dict[str, List[Dict]] = {}

search_tool = TavilySearchResults()

logger = logging.getLogger(__name__)


# Gemini OCR function
os.environ["GENAI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

async def gemini_ocr(file_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Extract text from an image using Gemini API asynchronously.
    If mime_type is not provided, defaults to 'image/jpeg'.
    """
    try:
        client = genai.Client()

        # Run synchronous Gemini client in thread executor
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    "Extract all text accurately from this flyer/image."
                ]
            )
        )

        return response.text or ""

    except Exception as e:
        print(f"[gemini_ocr] OCR failed: {e}")
        return ""


# EML parser (email)
def build_email_document_structure(msg, body_text: str, attachment_text: str) -> str:
    from_addr = msg.get("From", "")
    to_addr = msg.get("To", "")
    subject = msg.get("Subject", "")
    sent_on = msg.get("Date", "")

    final_text = f"""
From: {from_addr}
Sent on: {sent_on}
To: {to_addr}
Subject: {subject}

Body:
{body_text}

Flyer Text:
{attachment_text}
""".strip()

    return final_text

async def parse_eml(file_bytes: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(file_bytes)

    body = ""
    attachment_texts = []
    ocr_tasks = []  # list of tuples: (key, task)
    cid_map = {}  # cid -> OCR text

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()
            cid = part.get("Content-ID", "").strip("<>")

            # ------------------------
            # BODY TEXT
            # ------------------------
            if ctype == "text/plain" and disp != "attachment":
                body += part.get_content() + "\n"
            elif ctype == "text/html" and disp != "attachment":
                soup = BeautifulSoup(part.get_content(), "html.parser")
                body += soup.get_text() + "\n"

            # ------------------------
            # INLINE IMAGES (cid)
            # ------------------------
            if ctype.startswith("image/") and cid:
                data = part.get_content()
                mime_type = ctype
                task = asyncio.create_task(gemini_ocr(data, mime_type))
                ocr_tasks.append((cid, task))

            # ------------------------
            # ATTACHMENTS
            # ------------------------
            if disp == "attachment":
                filename = (part.get_filename() or "").lower()
                data = part.get_content()

                if filename.endswith(".pdf"):
                    attachment_texts.append(parse_pdf(data))
                elif filename.endswith(".docx"):
                    attachment_texts.append(parse_docx(data))
                elif filename.endswith((".png", ".jpg", ".jpeg")):
                    task = asyncio.create_task(gemini_ocr(data, part.get_content_type()))
                    ocr_tasks.append((filename, task))

    # Run OCR asynchronously
    for key, task in ocr_tasks:
        text = await task
        cid_map[key] = text

    # Replace cids in body with OCR text
    for cid, text in cid_map.items():
        body = body.replace(f"[cid:{cid}]", text)

    # Combine any remaining OCRed attachments that weren’t inline
    attachment_texts.extend([v for k, v in cid_map.items() if k not in body])

    return build_email_document_structure(
        msg,
        body,
        "\n".join(attachment_texts)
    )


# DOCX parser
def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

# PDF parser
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

# Image parser (OCR)
async def parse_image(file_bytes: bytes) -> str:
    try:
        Image.open(io.BytesIO(file_bytes))  # Validate image
        ocr_text = await gemini_ocr(file_bytes)
        return f"[IMAGE OCR] {ocr_text.strip()}" if ocr_text else ""
    except Exception as e:
        print(f"Image parsing failed: {e}")
        return ""

# PPTX parser with OCR for images
async def parse_pptx_smart(file_bytes: bytes) -> str:
    """
    Fully enhanced PPTX extractor:
    - Slide text
    - SmartArt text
    - Grouped shape text
    - Table text
    - Speaker notes
    - Images (ppt/media, embeddings, charts) → OCR via Gemini
    """

    prs = Presentation(io.BytesIO(file_bytes))
    extracted_text = []

    # ------------------------------------------
    # Helper: recursively extract text from shapes
    # ------------------------------------------
    def extract_shape_text(shape):
        try:
            # Basic text
            if hasattr(shape, "text") and shape.text.strip():
                extracted_text.append(shape.text.strip())

            # Text frame
            if hasattr(shape, "text_frame") and shape.text_frame:
                for p in shape.text_frame.paragraphs:
                    t = p.text.strip()
                    if t:
                        extracted_text.append(t)

            # Table text
            if shape.has_table:
                for row in shape.table.rows:
                    for cell in row.cells:
                        t = cell.text.strip()
                        if t:
                            extracted_text.append(t)

            # Grouped shapes / SmartArt
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                for sub in shape.shapes:
                    extract_shape_text(sub)

        except Exception:
            pass

    # ------------------------------------------
    # Extract text from slides + notes
    # ------------------------------------------
    for slide in prs.slides:
        for shape in slide.shapes:
            extract_shape_text(shape)

        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                extracted_text.append(f"[SPEAKER NOTES] {notes}")

    # ------------------------------------------
    # Extract images from PPTX ZIP
    # ------------------------------------------
    pptx_zip = zipfile.ZipFile(io.BytesIO(file_bytes))
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff")

    image_files = [
        fn for fn in pptx_zip.namelist()
        if fn.lower().endswith(image_extensions)
    ]

    # Also check ppt/media, ppt/embeddings
    for fn in pptx_zip.namelist():
        lower_fn = fn.lower()
        if (
            lower_fn.startswith("ppt/media/")
            or lower_fn.startswith("ppt/embeddings/")
        ):
            if lower_fn.endswith(image_extensions):
                if fn not in image_files:
                    image_files.append(fn)

    # ------------------------------------------
    # OCR each image
    # ------------------------------------------
    for img_name in image_files:
        try:
            img_bytes = pptx_zip.read(img_name)

            # Validate correct image type
            try:
                Image.open(io.BytesIO(img_bytes))
            except:
                continue  # skip broken or non-image files

            # OCR using Gemini
            ocr_text = await gemini_ocr(img_bytes)

            if ocr_text and ocr_text.strip():
                extracted_text.append(f"[IMAGE OCR] {ocr_text.strip()}")

        except Exception as e:
            print(f"Failed OCR for image {img_name}: {e}")

    # ------------------------------------------
    # Clean + dedupe
    # ------------------------------------------
    cleaned = []
    seen = set()

    for line in extracted_text:
        line = line.strip()
        if line and line not in seen:
            cleaned.append(line)
            seen.add(line)

    return "\n".join(cleaned)


def get_chat_history(chat_id: str, domain: Optional[str] = None):
    """Get chat history from database, optionally filtered by domain."""
    db = None
    try:
        db = DB(default_config())
        cursor = db.conn.cursor()
        
        if domain:
            query = """
            SELECT role, message FROM ask_hr_history
            WHERE chat_id = %s AND domain = %s
            ORDER BY timestamp ASC
            """
            cursor.execute(query, (chat_id, domain))
        else:
            query = """
            SELECT role, message FROM ask_hr_history
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
            elif name.endswith(".eml"):
                file_text = await parse_eml(file_bytes)  # New support for emails
            elif name.endswith(".pptx"):
                file_text = await parse_pptx_smart(file_bytes)
            elif name.endswith((".jpg", ".jpeg", ".png")):
                file_text = await gemini_ocr(file_bytes)
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

def document_search_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Document search with context-aware query (already enriched by coordinator)."""
    query = state["query"]
    original_query = state.get("original_query", query)
    chat_id = state.get("chat_id")
    domain = state.get("collection_id")
    
    logger.info(f"[DOC_AGENT] Searching with query: '{query}'")
    logger.info(f"[DOC_AGENT] Domain: '{domain}'")

    is_vague = context_manager.is_followup_question(original_query or query)
    was_enriched = "[Context:" in query or original_query != query
    
    if is_vague and not was_enriched:
        recent_entities = context_manager.get_recent_entities(chat_id, limit=3)
        if not recent_entities:
            state["document_found"] = False
            state["answer"] = "Your question refers to something from our conversation, but I couldn't find that context. Please provide more details or rephrase your question."
            state["reasoning_chain"].append("Document Search: Vague query without context - rejected")
            logger.warning(f"[DOC_AGENT] Rejected vague query without context: '{query}'")
            return state
    
    # Update entity memory from user query
    context_manager.update_entity_memory(chat_id, query, role="user")
    
    # Store domain for continuity
    if domain:
        context_manager.update_context("document_agent", "last_domain", domain, chat_id)
    
    # Search with the query
    from api.v1.chat.vectorstore import search_similar
    docs = search_similar(query, domain=domain)
    
    if not docs:
        state["document_found"] = False
        state["reasoning_chain"].append(f"Document Search: No docs in '{domain}'")
        return state
    
    if is_vague:
        avg_score = sum(doc.get("score", 0) for doc in docs) / len(docs)
        
        if avg_score < 0.7:
            state["document_found"] = False
            state["answer"] = "I found some documents, but they don't seem relevant to what you're asking about. Could you rephrase or provide more context?"
            state["reasoning_chain"].append(f"Document Search: Low confidence score ({avg_score:.2f}) - rejected")
            logger.warning(f"[DOC_AGENT] Low confidence on vague query: score={avg_score:.2f}")
            return state
    
    # Build context from retrieved documents
    context = "\n\n".join(
        [r["payload"]["page_content"] for r in docs if "page_content" in r.get("payload", {})]
    )
    
    if context.strip():
        state["document_context"] = context.strip()
        state["reasoning_chain"].append(f"Document Search: Found {len(docs)} docs in '{domain}'")
        state["sources"] = [r["id"] for r in docs]
        state["document_found"] = True
        
        # Extract entities from documents for future reference
        context_manager.update_entity_memory(chat_id, context[:500], role="assistant")
    else:
        state["document_found"] = False
        state["reasoning_chain"].append(f"Document Search: No usable text in '{domain}'")
    
    return state
