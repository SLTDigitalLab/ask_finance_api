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

async def gemini_ocr(file_bytes: bytes) -> str:
    return "Extracted text from Gemini OCR"


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
    ocr_tasks = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get_content_disposition()

            # Body text
            if ctype == "text/plain" and disp != "attachment":
                body += part.get_content() + "\n"

            if ctype == "text/html" and disp != "attachment":
                soup = BeautifulSoup(part.get_content(), "html.parser")
                body += soup.get_text() + "\n"

            # Attachments
            if disp == "attachment":
                filename = part.get_filename() or ""
                data = part.get_content()

                if filename.lower().endswith(".pdf"):
                    attachment_texts.append(parse_pdf(data))
                elif filename.lower().endswith(".docx"):
                    attachment_texts.append(parse_docx(data))
                elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    ocr_tasks.append(gemini_ocr(data))

    if ocr_tasks:
        ocr_results = await asyncio.gather(*ocr_tasks)
        attachment_texts.extend(ocr_results)

    return build_email_document_structure(
        msg,
        body,
        "\n".join(attachment_texts)
    )

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
    """
    Document search with intelligent caching for ANY follow-up question.
    
    Caching Strategy:
    - Level 1: Cache retrieved document content (for questions about "that document")
    - Level 2: Cache last assistant answer (for questions about "explain above")
    """
    query = state["query"]
    original_query = state.get("original_query", query)
    chat_id = state.get("chat_id")
    domain = state.get("collection_id")
    
    logger.info(f"[DOC_AGENT] Query: '{original_query}'")

    is_vague = context_manager.is_followup_question(original_query or query)
    
    # Get cached data
    last_doc_content = context_manager.get_context("document_agent", "last_document_content", chat_id)
    last_answer = context_manager.get_last_answer_snippet(chat_id, max_length=1000)
    
    logger.info(f"[DOC_AGENT] Is vague: {is_vague}")
    logger.info(f"[DOC_AGENT] Has cached doc: {last_doc_content is not None}")
    logger.info(f"[DOC_AGENT] Has last answer: {last_answer is not None}")
    
    followup_type = None
    
    if is_vague:
        query_lower = original_query.lower()
        
        document_refs = [
            "that document", "this document", "the document",
            "what does it say", "what does it contain", "what's in it",
            "document content", "document policy"
        ]
        
        if any(ref in query_lower for ref in document_refs):
            followup_type = "DOCUMENT_SPECIFIC"
            logger.info(f"[DOC_AGENT] Follow-up type: DOCUMENT_SPECIFIC")
        
        elif any(word in query_lower for word in ['explain', 'elaborate', 'detail', 'more about']):
            answer_refs = [
                'explain all', 'explain those', 'explain these', 'explain them',
                'explain above', 'above thing', 'above mentioned',
                'tell me more', 'more details', 'elaborate',
                'break down', 'go deeper'
            ]
            
            if any(ref in query_lower for ref in answer_refs):
                followup_type = "ANSWER_ELABORATION"
                logger.info(f"[DOC_AGENT] Follow-up type: ANSWER_ELABORATION")
        
        elif len(original_query.split()) <= 5:
            if any(word in query_lower for word in ['it', 'them', 'those', 'these']):
                followup_type = "GENERIC_VAGUE"
                logger.info(f"[DOC_AGENT] Follow-up type: GENERIC_VAGUE")
    
    if followup_type == "DOCUMENT_SPECIFIC" and last_doc_content:
        logger.info(f"[DOC_AGENT] ✓ Strategy 1: Reusing cached document content")
        
        state["document_context"] = last_doc_content
        state["document_found"] = True
        state["sources"] = context_manager.get_context("document_agent", "last_document_ids", chat_id) or []
        state["reasoning_chain"].append("Document Search: Reused cached document (document-specific follow-up)")
        
        context_manager.update_entity_memory(chat_id, query, role="user")
        return state
    
    if followup_type == "ANSWER_ELABORATION" and last_doc_content:
        logger.info(f"[DOC_AGENT] ✓ Strategy 2: Reusing document for answer elaboration")
        
        # Add the previous answer as additional context
        combined_context = last_doc_content
        
        if last_answer:
            combined_context = f"Previous Answer:\n{last_answer}\n\n---\n\nOriginal Document Content:\n{last_doc_content}"
        
        state["document_context"] = combined_context
        state["document_found"] = True
        state["sources"] = context_manager.get_context("document_agent", "last_document_ids", chat_id) or []
        state["reasoning_chain"].append("Document Search: Reused document + previous answer (elaboration request)")
        
        context_manager.update_entity_memory(chat_id, query, role="user")
        return state
    
    if followup_type == "GENERIC_VAGUE" and last_doc_content:
        logger.info(f"[DOC_AGENT] ✓ Strategy 3: Attempting to reuse for generic vague query")
        
        state["document_context"] = last_doc_content
        state["document_found"] = True
        state["sources"] = context_manager.get_context("document_agent", "last_document_ids", chat_id) or []
        state["reasoning_chain"].append("Document Search: Reused cached document (generic follow-up)")
        
        context_manager.update_entity_memory(chat_id, query, role="user")
        return state
    
    logger.info(f"[DOC_AGENT] Strategy 4: Performing new document search")
    
    # Extract entities
    entities = context_manager.extract_entities(query)
    doc_codes = entities.get("CUSTOM", [])
    
    if not doc_codes and is_vague:
        recent_entities = context_manager.get_recent_entities(chat_id, limit=5)
        doc_codes = [e for e in recent_entities if any(char.isdigit() for char in e)]
        logger.info(f"[DOC_AGENT] Document codes from context: {doc_codes}")
    
    # Multi-strategy search
    all_docs = []
    
    if doc_codes:
        for doc_code in doc_codes[:2]:
            docs = search_similar(doc_code, domain=domain, limit=5)
            if docs:
                all_docs.extend(docs)
    
    if len(all_docs) == 0:
        docs = search_similar(original_query, domain=domain, limit=5)
        if docs:
            all_docs.extend(docs)
    
    if len(all_docs) == 0 and query != original_query:
        docs = search_similar(query, domain=domain, limit=5)
        if docs:
            all_docs.extend(docs)
    
    if not all_docs:
        state["document_found"] = False
        state["reasoning_chain"].append("Document Search: No documents found")
        return state
    
    # Deduplicate and sort
    seen = set()
    unique_docs = []
    for doc in all_docs:
        doc_id = doc.get('id')
        if doc_id not in seen:
            seen.add(doc_id)
            unique_docs.append(doc)
    
    unique_docs.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Log top results
    logger.info(f"[DOC_AGENT] Top 3 results:")
    for i, doc in enumerate(unique_docs[:3], 1):
        score = doc.get('score', 0)
        preview = doc.get('payload', {}).get('page_content', '')[:80]
        logger.info(f"  [{i}] Score: {score:.3f} | {preview}...")
    
    # Quality checks
    top_score = unique_docs[0].get('score', 0)
    
    # Document code verification
    if doc_codes:
        top_content = unique_docs[0].get('payload', {}).get('page_content', '').upper()
        if not any(code.upper() in top_content for code in doc_codes):
            filtered = [
                doc for doc in unique_docs
                if any(code.upper() in doc.get('payload', {}).get('page_content', '').upper() 
                       for code in doc_codes)
            ]
            
            if filtered:
                unique_docs = filtered
            else:
                state["document_found"] = False
                state["answer"] = f"I couldn't find document '{doc_codes[0]}' in the system."
                return state
    
    # Confidence check
    if is_vague and top_score < 0.6 and not doc_codes:
        state["document_found"] = False
        state["answer"] = f"I found documents but they don't seem very relevant. Please provide more details."
        return state
    
    # Build context with quality filtering
    top_docs = unique_docs[:5]
    raw_contexts = []
    
    for doc in top_docs:
        content = doc.get('payload', {}).get('page_content', '')
        if content:
            # Check readability
            readable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
            total_chars = len(content)
            
            if total_chars > 0 and (readable_chars / total_chars) > 0.7:
                raw_contexts.append(content)
            else:
                logger.warning(f"[DOC_AGENT] Skipping garbled content")
    
    if not raw_contexts:
        state["document_found"] = False
        state["answer"] = "I found documents but the content appears to be corrupted. Please check if documents were uploaded correctly."
        return state
    
    context = "\n\n".join(raw_contexts)
    
    # Cache for future follow-ups
    doc_ids = [doc.get('id') for doc in top_docs if any(
        doc.get('id') == d.get('id') 
        for d in [doc for doc in top_docs 
                 if (doc.get('payload', {}).get('page_content', '') in raw_contexts)]
    )]
    
    context_manager.update_context("document_agent", "last_document_ids", doc_ids, chat_id)
    context_manager.update_context("document_agent", "last_document_content", context, chat_id)
    context_manager.update_context("document_agent", "last_query", original_query, chat_id)
    
    logger.info(f"[DOC_AGENT] ✓ Cached {len(top_docs)} documents")
    
    # Update state
    state["document_context"] = context.strip()
    state["document_found"] = True
    state["sources"] = doc_ids
    state["reasoning_chain"].append(f"Document Search: Retrieved {len(top_docs)} new documents")
    
    # Update entity memory
    context_manager.update_entity_memory(chat_id, query, role="user")
    context_manager.update_entity_memory(chat_id, context[:500], role="assistant")
    
    if domain:
        context_manager.update_context("document_agent", "last_domain", domain, chat_id)
    
    return state
