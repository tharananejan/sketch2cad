from deps import get_settings
from services.rag_retriever import retrieve_context

print("Testing RAG retrieve_context...")
settings = get_settings()
context, sources = retrieve_context("Create a cylinder", settings)
print("Context:", context)
print("Sources:", sources)
