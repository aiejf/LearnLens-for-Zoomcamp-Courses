from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from dotenv import load_dotenv
import os
import pandas as pd
import json

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")

# ---------------------------
# Load Vectorstore + Retriever
# ---------------------------
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

persist_directory = "zoomcamp_transcripts/chroma_store"
vectorstore = Chroma(
    persist_directory=persist_directory,
    embedding_function=embedding_model,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# ---------------------------
# Initialize OpenAI LLM
# ---------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",  # can switch to gpt-4o, gpt-4-turbo, etc.
    temperature=0
)

# ---------------------------
# Custom Prompt for Concise Answers
# ---------------------------
prompt_template = """
You are a helpful assistant. 
Use the provided context to answer the question concisely in 2–3 sentences. 
If the context does not contain the answer, say "I don’t know."

Context:
{context}

Question:
{question}

Answer:
"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

# ---------------------------
# Step 1: Load ragas_dataset.json
# ---------------------------
with open("ragas_dataset.json", "r", encoding="utf-8") as f:
    ragas_data = json.load(f)

questions = [item["question"] for item in ragas_data]
ground_truths = [item["answer"] for item in ragas_data]
contexts_list = [item["contexts"] for item in ragas_data]

# ---------------------------
# Step 2: Run queries through your RAG system
# ---------------------------
answers = []
retrieved_contexts = []

for q in questions:
    result = qa_chain({"query": q})
    answers.append(result["result"])
    retrieved_contexts.append([doc.page_content for doc in result["source_documents"]])

# ---------------------------
# Step 3: Prepare dataset for Ragas
# ---------------------------
dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": retrieved_contexts,
    "ground_truth": ground_truths,
})

# ---------------------------
# Step 4: Run Ragas evaluation
# ---------------------------
result = evaluate(
    dataset=dataset,
    metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
)

print("📊 Evaluation Results:")
print(result)

# ---------------------------
# Step 5: Convert to Pandas + Export to Excel
# ---------------------------
df_metrics = result.to_pandas()

# Save original dataset alongside metrics
df_full = pd.concat([dataset.to_pandas(), df_metrics], axis=1)

# Export to Excel
output_file = "ragas_evaluation.xlsx"
df_full.to_excel(output_file, index=False)

print(f"✅ Results exported to {output_file}")
