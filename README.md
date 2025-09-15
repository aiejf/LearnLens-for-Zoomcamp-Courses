# LearnLens-for-Zoomcamp-Courses
earnLens is an AI-powered learning assistant built for the full suite of Zoomcamp courses by DataTalks.Club. Whether you're learning Machine Learning, Data Engineering, or MLOps, LearnLens helps you find exactly where your question is answered — without watching entire videos.

## Project Overview 💻
This project builds a Retrieval-Augmented Generation (RAG) system designed to answer questions using a comprehensive knowledge base of DataTalks.Club Zoomcamp transcripts. It processes YouTube video transcripts, chunks them into manageable segments, creates vector embeddings, and stores them in a ChromaDB vector store. A Streamlit application serves as the user interface, where a user's question is retrieved and answered by a Google Gemini model based on the relevant transcript chunks. The project also includes scripts for generating evaluation datasets and running RAGAS-based evaluations to measure the system's performance.

## Installation Instructions ⚙️
To get started, you'll need to set up your environment and install the required dependencies.

Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

## Set up a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies
Install all necessary Python libraries from the requirements.txt file.

```bash
pip install -r requirements.txt
```
## Configure API Keys
Create a .env file in the project's root directory to store your API keys. You'll need keys for the YouTube Data API, OpenAI, and Google Gemini.
```bash
YOUTUBE_API_KEY="your_youtube_api_key"
OPENAI_KEY="your_openai_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```
YouTube Data API: Used to fetch video and playlist metadata.

OpenAI: Used in the evaluation script to generate Q&A pairs.

Google Gemini: The Large Language Model (LLM) used for generating answers in the RAG system.

## Usage Guide 🚀
### Step 1: Fetch and Process Transcripts
First, you need to download and process the transcripts from the DataTalks.Club YouTube playlists.

```bash
python 1-get_zoomcamp_transcripts.py
```
This script saves the raw, segmented transcripts to zoomcamp_transcripts/all_zoomcamp_metadata_with_segmented_transcripts.json.

### Step 2: Create Transcript Chunks
Next, chunk the transcripts into ~30-second segments for better retrieval granularity.
```bash
python 2-chunks_processing.py
```
This script outputs the processed chunks to zoomcamp_transcripts/zoomcamp_chunks_30s.json.

### Step 3: Generate Embeddings and Build Vector Store
This step creates vector embeddings for each chunk using the HuggingFaceEmbeddings model all-MiniLM-L6-v2 and stores them in a persistent ChromaDB instance.
```bash
python 3-embeddings_storage.py
```
This will create a chroma_store directory within the zoomcamp_transcripts folder.

### Step 4: Run the RAG Application
Launch the Streamlit application to interact with the RAG system.
```bash
streamlit run app.py
```
A web browser window will open, allowing you to ask questions and get answers from the Zoomcamp transcripts.

## Development Setup Guide 🧑‍💻
The project's codebase is modular, allowing for easy development and modification of individual components.

RAG System Core (RAG.py)
ask_question(query: str): This function is the core of the RAG system. It takes a user's question, uses a RetrievalQA chain to find relevant documents from the ChromaDB retriever, and then generates an answer using the ChatGoogleGenerativeAI model.

Prompt Customization: The prompt_template is used to guide the Gemini model's response, ensuring it sticks to the provided context, remains concise, and cites video timestamps when available.

Evaluation (5-RAG_Data_Eval_Gen.py and 6-RAGAs_eval.py)
Dataset Generation: The 5-RAG_Data_Eval_Gen.py script uses the OpenAI API to automatically generate a ground truth Q&A dataset (ragas_dataset.json) from the processed transcript chunks.

Evaluation Metrics: The 6-RAGAs_eval.py script runs the generated dataset through the RAG system and evaluates the performance using RAGAS metrics such as context_precision, context_recall, faithfulness, and answer_relevancy. The results are then saved to an Excel file (ragas_evaluation.xlsx).
