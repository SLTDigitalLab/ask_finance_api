from __future__ import annotations
import os
from typing import List, Optional, Sequence, Union, Dict, Any
from qdrant_client import QdrantClient, models
import google.generativeai as genai
import uuid
from dotenv import load_dotenv
from mode import server
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEFAULT_DIM = os.getenv("VECTORSTORE_DIM")
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_EMBEDDING_MODEL")

if server:
    QDRANT_URL = os.getenv("VECTORSTORE_PROD_URL")
else:
    QDRANT_URL = os.getenv("VECTORSTORE_DEV_URL")

def get_collection_name(domain: str) -> str:
    """Generate collection name based on domain."""
    return f"{domain.lower().replace(' ', '_')}"

def create_collection(domain: str, size: int = DEFAULT_DIM) -> str:
    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(collection_name):
        logger.info("The collection already exists")
        return client.get_collection(collection_name).status

    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=size,
            distance=models.Distance.COSINE,
        ),
    )
    return client.get_collection(collection_name).status

def delete_collection(domain: str) -> None:
    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        logger.info("Collection Deleted")
    else:
        logger.info("The collection already exists")


def get_collection(domain: str) -> Dict[str, Any]:
    if client.collection_exists(domain):
        """Return full collection info as a dict."""
        collection_name = get_collection_name(domain)
        client = QdrantClient(url=QDRANT_URL)
        info = client.get_collection(collection_name)
        return info.dict() if hasattr(info, "dict") else info
    else:
        return None


def get_all_collections() -> List[Dict[str, Any]]:
    """
    Return list of collections with domain info.

    FIXED: Properly handle the Qdrant response structure.
    """
    try:
        client = QdrantClient(url=QDRANT_URL)
        response = client.get_collections()

        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response: {response}")

        if hasattr(response, 'collections'):
            collections_list = response.collections
        else:
            collections_list = response if isinstance(response, list) else []

        result = []
        for collection in collections_list:
            if hasattr(collection, 'name'):
                name = collection.name
            elif isinstance(collection, dict):
                name = collection.get('name', '')
            else:
                name = str(collection)

            result.append({
                "domain": name,
                "collection_name": name
            })

        logger.info(f"Found {len(result)} collections: {[c['domain'] for c in result]}")
        return result

    except Exception as e:
        logger.error(f"Error in get_all_collections: {str(e)}", exc_info=True)
        return []

def get_all_points(
    domain: str,
    limit: int = 100,
    with_payload: bool = True,
    with_vectors: bool = False,
) -> List[Dict[str, Any]]:

    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)

    all_points: List[Dict[str, Any]] = []
    offset: Optional[str] = None

    if client.collection_exists(collection_name):
        while True:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors,
            )

            points, offset = scroll_result
            for p in points:
                d = p.dict() if hasattr(p, "dict") else p
                all_points.append(d)

            if offset is None:  # no more points
                break

    return all_points

def _embed_texts(
    texts: Sequence[str],
    model: str = DEFAULT_GEMINI_MODEL,
    output_dimensionality: Optional[int] = None,
) -> List[List[float]]:

    if not GOOGLE_API_KEY:
        raise RuntimeError("GOOGLE_API_KEY is not set in the environment.")

    genai.configure(api_key=GOOGLE_API_KEY)

    kwargs = {}
    if output_dimensionality is not None:
        kwargs["output_dimensionality"] = int(output_dimensionality)

    resp = genai.embed_content(
        model=model,
        content=list(texts),
        task_type="retrieval_document",
        **kwargs,
    )

    if "embedding" in resp:
        return resp["embedding"]
    else:
        raise RuntimeError(f"Unexpected Gemini embedding response: {resp}")



def add_texts(
    texts: Sequence[str],
    metadatas: Optional[Sequence[Dict[str, Any]]] = None,
    ids: Optional[Sequence[Union[int, str]]] = None,
    *,
    domain: str,
) -> Dict[str, Any]:
    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)
    
    if not client.collection_exists(collection_name):
        create_collection(domain=domain)

    metadatas = [{"page_content":text, "domain":domain} for text in texts]

    if ids is None:
        ids = [str(uuid.uuid4()) for _ in texts]

    if not (len(texts) == len(metadatas) == len(ids)):
        raise ValueError("texts, metadatas, and ids must have the same length")

    vectors = _embed_texts(
        texts=texts
    )

    points = [
        models.PointStruct(
            id=pid,
            vector=vec,
            payload=meta,
        )
        for pid, vec, meta in zip(ids, vectors, metadatas)
    ]
    result = client.upsert(collection_name=collection_name, points=points)
    return result.dict() if hasattr(result, "dict") else result


def search_similar(
    query_text: str,
    limit: int = 5,
    *,
    domain: str,
    model: str = DEFAULT_GEMINI_MODEL,
    output_dimensionality: Optional[int] = None,
    with_payload: bool = True,
) -> List[Dict[str, Any]]:
    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)
    
    if not client.collection_exists(collection_name):
        return []

    [qvec] = _embed_texts(
        [query_text], model=model, output_dimensionality=output_dimensionality
    )

    hits = client.search(
        collection_name=collection_name,
        query_vector=qvec,
        limit=limit,
        with_payload=with_payload,
    )

    out = []
    for h in hits:
        d = h.dict() if hasattr(h, "dict") else h
        out.append(d)
    return out

def search_across_domains(
    query_text: str,
    domains: List[str],
    limit_per_domain: int = 5,
    score_threshold: Optional[float] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Search across multiple domains and return results grouped by domain."""
    results = {}
    
    for domain in domains:
        domain_results = search_similar(
            query_text=query_text,
            domain=domain,
            limit=limit_per_domain,
            score_threshold=score_threshold
        )
        if domain_results:
            results[domain] = domain_results
    
    return results

def get_domain_stats(domain: str) -> Dict[str, Any]:
    """Get statistics for a specific domain's collection."""
    collection_name = get_collection_name(domain)
    client = QdrantClient(url=QDRANT_URL)
    
    if not client.collection_exists(collection_name):
        return {"exists": False, "domain": domain}
    
    info = client.get_collection(collection_name)
    
    return {
        "exists": True,
        "domain": domain,
        "collection_name": collection_name,
        "points_count": info.points_count,
        "vectors_count": info.vectors_count,
        "status": info.status,
    }


if __name__ == "__main__":

    create_collection("hr")
    create_collection("sales")
    create_collection("support")
    
    hr_docs = [
        "Our company offers 15 days of paid vacation per year.",
        "Health insurance enrollment opens in January.",
        "Performance reviews are conducted quarterly."
    ]
    add_texts(hr_docs, domain="hr")
    
    sales_docs = [
        "Q1 sales targets increased by 20%.",
        "New CRM system training is mandatory for all sales staff.",
        "Product launch scheduled for next month."
    ]
    add_texts(sales_docs, domain="sales")
    
    results = search_similar("vacation policy", domain="hr", limit=3)
    print(f"HR results: {results}")
    
    multi_results = search_across_domains(
        "training requirements",
        domains=["hr", "sales"],
        limit_per_domain=2
    )
    print(f"Multi-domain results: {multi_results}")
    
    hr_stats = get_domain_stats("hr")
    print(f"HR domain stats: {hr_stats}")