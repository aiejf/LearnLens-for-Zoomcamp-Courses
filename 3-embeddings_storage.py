from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

import json
import os

# Load your 30s transcript chunks
with open("zoomcamp_transcripts/zoomcamp_chunks_30s.json", "r") as f:
    chunks = json.load(f)

# Initialize embedding model
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Convert chunks into LangChain Documents with extended metadata
documents = []
for chunk in chunks:
    text = chunk["text"]
    metadata = {
        "video_id": chunk.get("video_id"),
        "video_url": chunk.get("video_url"),
        "video_title": chunk.get("video_title"),
        "playlist_id": chunk.get("playlist_id"),
        "playlist_title": chunk.get("playlist_title"),
        "start_time": chunk.get("start_time"),
        "end_time": chunk.get("end_time"),
    }
    documents.append(Document(page_content=text, metadata=metadata))

# Setup Chroma vector store
persist_directory = "zoomcamp_transcripts/chroma_store"
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedding_model,
    persist_directory=persist_directory
)

# Save to disk
vectorstore.persist()

print(f"✅ Successfully embedded and stored {len(documents)} chunks in ChromaDB.")
