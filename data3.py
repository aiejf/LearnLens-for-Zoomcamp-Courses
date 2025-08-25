from langchain_community.vectorstores import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI  # ✅ correct import
from langchain.chains import RetrievalQA

import json
import os

# Set your Google API key
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"

# Load transcripts
with open("zoomcamp_transcripts/zoomcamp_chunks_30s.json", "r") as f:
    chunks = json.load(f)

# Initialize embeddings
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Convert chunks to Documents
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

# Setup Chroma vectorstore
persist_directory = "zoomcamp_transcripts/chroma_store"
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedding_model,
    persist_directory=persist_directory
)

vectorstore.persist()

# Create retriever + RAG chain
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Example query
query = "How do I set up a virtual environment in Python?"
result = qa_chain({"query": query})

print("Answer:", result["result"])
print("Sources:", [doc.metadata for doc in result["source_documents"]])

