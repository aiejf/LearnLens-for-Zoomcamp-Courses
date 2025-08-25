
import streamlit as st
from RAG import ask_question  # import your function from the RAG script

st.set_page_config(page_title="LearnLens - Zoomcamp Assistant", page_icon="🎓", layout="wide")

st.title("🎓 LearnLens: Your Zoomcamp Assistant")
st.markdown("Ask questions and get answers directly from **DataTalks.Club Zoomcamp transcripts**.")

# Input box for question
query = st.text_input("🔎 Enter your question:")

if query:
    with st.spinner("Thinking... 🤔"):
        answer, sources = ask_question(query)

        st.subheader("🧠 Answer")
        st.write(answer)

        st.subheader("📚 Sources")
        if sources:
            for s in sources:
                start = int(s["start_time"]) if s["start_time"] else 0
                link = f"{s['video_url']}&t={start}s"
                st.markdown(f"- **{s['video_title']}** — [Watch from {start}s]({link})")
        else:
            st.write("No relevant sources found.")
