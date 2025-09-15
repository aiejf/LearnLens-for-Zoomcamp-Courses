from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please set it in your .env file.")

# -----------------------------
# Embedding Model & Vectorstore
# -----------------------------
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

persist_directory = "zoomcamp_transcripts/chroma_store"
vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# -----------------------------
# LLM Setup (Gemini)
# -----------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2  # more focused answers
)

# -----------------------------
# Custom Prompt Template
# -----------------------------


prompt_template = """
You're a strict teaching assistant. 
Use ONLY the CONTEXT provided to answer the QUESTION. 
- If the answer is not in the CONTEXT, say: "I don’t know based on the course materials."
- Keep answers concise (2–3 sentences).
- Cite video timestamps when available.

Context:
{context}

Question:
{question}

Answer:
"""
prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["question", "context"]
)

# -----------------------------
# RetrievalQA Chain
# -----------------------------
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True,
)

# -----------------------------
# Query Function
# -----------------------------
def ask_question(query: str):
    """Query the RAG system and return structured answer + sources."""
    result = qa_chain({"query": query})

    answer = result["result"]
    sources = [
        {
            "video_title": doc.metadata.get("video_title"),
            "video_url": doc.metadata.get("video_url"),
            "start_time": doc.metadata.get("start_time"),
            "end_time": doc.metadata.get("end_time"),
        }
        for doc in result["source_documents"]
    ]
    return answer, sources

# -----------------------------
# Example Run
# -----------------------------
# if __name__ == "__main__":
#     query = "How do I set up a virtual environment in Python?"
#     answer, sources = ask_question(query)

#     print("\n🧠 Answer:\n")
#     print(answer)

#     print("\n📚 Sources:\n")
#     for s in sources:
#         print(f"- {s['video_title']} ({s['video_url']} at {s['start_time']}s–{s['end_time']}s)")
