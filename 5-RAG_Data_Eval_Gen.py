import json
import random
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

# Load transcript JSON
with open("zoomcamp_transcripts/zoomcamp_chunks_30s.json", "r", encoding="utf-8") as f:
    transcripts = json.load(f)


qa_pairs = []
target_pairs = 100
batch_size = 5  # number of chunks to process at once
max_words_per_chunk = 500

for i in range(0, len(transcripts), batch_size):
    batch = transcripts[i:i+batch_size]
    
    for chunk in batch:
        context_text = chunk["text"]
        video_title = chunk["video_title"]
        
        # Trim long transcripts
        words = context_text.split()
        if len(words) > max_words_per_chunk:
            context_text = " ".join(words[:max_words_per_chunk])
        
        prompt = f"""
You are given a transcript from a YouTube video titled "{video_title}".
Transcript: {context_text}

Generate 2-3 concise question-answer pairs strictly based on this transcript.
- Questions must be 1 sentence max.
- Answers must be concise, factual, and grounded only in this transcript.
- Return output as valid JSON ONLY.
- Use this format EXACTLY:
[
  {{"question": "...", "answer": "..."}},
  {{"question": "...", "answer": "..."}}
]
Do not include explanations or extra text.
"""
        success = False
        retries = 0
        while not success and retries < 3:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                raw = response.choices[0].message.content.strip()
                
                # Try to parse JSON
                pairs = json.loads(raw)
                for p in pairs:
                    qa_pairs.append({
                        "question": p["question"],
                        "answer": p["answer"],
                        "contexts": [context_text],
                        "video_url": chunk.get("video_url", ""),
                        "start_time": chunk.get("start_time", 0)
                    })
                success = True
                
            except json.JSONDecodeError:
                print("JSON decode error, raw output:", raw)
                retries += 1
                time.sleep(1)
            except Exception as e:
                print("Error:", e)
                retries += 1
                time.sleep(1)
        
        if len(qa_pairs) >= target_pairs:
            break
    if len(qa_pairs) >= target_pairs:
        break

# Shuffle and keep exactly target_pairs
random.shuffle(qa_pairs)
qa_pairs = qa_pairs[:target_pairs]

# Save to JSON for RAGAS
with open("ragas_dataset.json", "w", encoding="utf-8") as f:
    json.dump(qa_pairs, f, indent=2, ensure_ascii=False)

print(f"✅ Generated {len(qa_pairs)} Q&A pairs saved to ragas_dataset.json")