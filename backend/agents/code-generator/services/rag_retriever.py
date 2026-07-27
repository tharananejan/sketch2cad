"""
RAG Retriever Service
Handles ChromaDB vector storage, Ollama embeddings, auto-ingestion of knowledge files,
and similarity search for relevant FreeCAD Python macros.
"""

import os
import logging
from typing import Tuple, List

try:
    import chromadb
    from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB library not installed. RAG retrieval will be bypassed.")

from deps import Settings, get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "freecad_knowledge"
_client = None
_collection = None


def _get_embedding_function(settings: Settings):
    """Create Ollama embedding function."""
    if not CHROMADB_AVAILABLE:
        return None
    return OllamaEmbeddingFunction(
        model_name=settings.EMBED_MODEL,
        url=settings.OLLAMA_BASE_URL,
    )


def init_store(settings: Settings):
    """Initialize persistent ChromaDB client and get or create collection."""
    global _client, _collection
    if not CHROMADB_AVAILABLE:
        return None
    if _collection is not None:
        return _collection

    try:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_function(settings),
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB store: {e}")
        return None


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks suitable for SLM context."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for sep in [". ", ".\n", "\n\n", "\n"]:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1 and last_sep > start:
                    end = last_sep + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(start + 1, end - overlap)
    return chunks


def auto_ingest_knowledge_base(settings: Settings) -> None:
    """
    Scan knowledge base directory for .txt and .md files and upsert chunks into ChromaDB.
    Runs automatically prior to retrieval.
    """
    collection = init_store(settings)
    if collection is None:
        return

    if not os.path.isdir(settings.KNOWLEDGE_DIR):
        return

    documents = []
    for filename in sorted(os.listdir(settings.KNOWLEDGE_DIR)):
        if filename.endswith(".txt") or filename.endswith(".md"):
            filepath = os.path.join(settings.KNOWLEDGE_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    documents.append({"filename": filename, "content": content})
            except Exception as e:
                logger.error(f"Error reading knowledge file {filename}: {e}")

    if not documents:
        return

    ids = []
    docs = []
    metas = []
    for doc in documents:
        chunks = chunk_text(doc["content"], settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        for i, chunk_str in enumerate(chunks):
            ids.append(f"{doc['filename']}_{i}")
            docs.append(chunk_str)
            metas.append({"source": doc["filename"]})

    if ids:
        try:
            collection.upsert(ids=ids, documents=docs, metadatas=metas)
            logger.debug(f"Upserted {len(ids)} chunks into ChromaDB.")
        except Exception as e:
            logger.error(f"Error upserting chunks to ChromaDB: {e}")


def retrieve_context(query: str, settings: Settings = None) -> Tuple[str, List[str]]:
    """
    Retrieve relevant FreeCAD Python macros from knowledge base for the user query.
    Returns:
        tuple[str, list[str]]: (joined_context_text, list_of_unique_source_files)
    """
    if settings is None:
        settings = get_settings()

    # Automatically ingest/refresh knowledge base
    auto_ingest_knowledge_base(settings)

    collection = init_store(settings)
    if collection is None:
        return "", []

    try:
        results = collection.query(
            query_texts=[query],
            n_results=settings.TOP_K,
        )
        if not results or not results.get("documents") or not results["documents"][0]:
            return "", []

        context_parts = []
        sources = set()
        for i in range(len(results["documents"][0])):
            context_parts.append(results["documents"][0][i])
            sources.add(results["metadatas"][0][i]["source"])

        context_str = "\n---\n".join(context_parts)
        return context_str, sorted(list(sources))
    except Exception as e:
        logger.error(f"RAG retrieval query failed: {e}")
        return "", []
