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
VECTORSTORE_NAME = os.getenv("VECTORSTORE_NAME")
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_EMBEDDING_MODEL")

if server:
    QDRANT_URL = os.getenv("VECTORSTORE_PROD_URL")
else:
    QDRANT_URL = os.getenv("VECTORSTORE_DEV_URL")

def create_collection(name: str = VECTORSTORE_NAME, size: int = DEFAULT_DIM) -> str:
    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(name):
        logger.info("The collection already exists")
        return client.get_collection(name).status

    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=size,
            distance=models.Distance.COSINE,
        ),
    )
    return client.get_collection(name).status

def delete_collection(name: str = VECTORSTORE_NAME) -> None:
    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(name):
        client.delete_collection(name)
        logger.info("Collection Deleted")
    else:
        logger.info("The collection already exists")


def get_collection(name: str = VECTORSTORE_NAME) -> Dict[str, Any]:
    if client.collection_exists(name):
        """Return full collection info as a dict."""
        client = QdrantClient(url=QDRANT_URL)
        info = client.get_collection(name)
        return info.dict() if hasattr(info, "dict") else info
    else:
        return None


def get_all_collections() -> list[str]:
    client = QdrantClient(url=QDRANT_URL)
    response = client.get_collections()
    return [c.name for c in response.collections]

def get_all_points(
    collection: str = VECTORSTORE_NAME,
    limit: int = 100,
    with_payload: bool = True,
    with_vectors: bool = False,
) -> List[Dict[str, Any]]:

    client = QdrantClient(url=QDRANT_URL)

    all_points: List[Dict[str, Any]] = []
    offset: Optional[str] = None

    if client.collection_exists(collection):
        while True:
            scroll_result = client.scroll(
                collection_name=collection,
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
    collection: str = VECTORSTORE_NAME
) -> Dict[str, Any]:
    
    client = QdrantClient(url=QDRANT_URL)
    
    if not client.collection_exists(collection):
        create_collection()

    metadatas = [{"page_content":text} for text in texts]

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
    result = client.upsert(collection_name=collection, points=points)
    return result.dict() if hasattr(result, "dict") else result


def search_similar(
    query_text: str,
    limit: int = 5,
    *,
    collection: str = VECTORSTORE_NAME,
    model: str = DEFAULT_GEMINI_MODEL,
    output_dimensionality: Optional[int] = None,
    with_payload: bool = True,
) -> List[Dict[str, Any]]:
    
    client = QdrantClient(url=QDRANT_URL)
    
    if not client.collection_exists(collection):
        return []

    [qvec] = _embed_texts(
        [query_text], model=model, output_dimensionality=output_dimensionality
    )

    hits = client.search(
        collection_name=collection,
        query_vector=qvec,
        limit=limit,
        with_payload=with_payload,
    )

    out = []
    for h in hits:
        d = h.dict() if hasattr(h, "dict") else h
        out.append(d)
    return out




if __name__ == "__main__":

    # docs = [
    #     "Temple of the Tooth Relic is a sacred Buddhist site in Kandy.",
    #     "Udawatta Kele Sanctuary has beautiful walking trails and wildlife.",
    #     "The Kandy Lake is a popular spot for evening walks."
    # ]

    # upsert_result = add_texts(docs)
    # print(upsert_result)

    # delete_collection()

    results = search_similar("Top places to see in Kandy", limit=4)
    print(results)