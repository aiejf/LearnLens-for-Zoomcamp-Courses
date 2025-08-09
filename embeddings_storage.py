# from langchain.vectorstores import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain.schema import Document

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
# Convert chunks into LangChain Documents
documents = []
for chunk in chunks:
    text = chunk["text"]
    metadata = {
        "video_id": chunk["video_id"],
        "video_url": chunk["video_url"],
        "start_time": chunk["start_time"],
        "end_time": chunk["end_time"],
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

