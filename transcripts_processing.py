import json
import os
from collections import defaultdict

# Load your transcript JSON
with open("zoomcamp_transcripts/all_zoomcamp_metadata_with_segmented_transcripts.json", "r") as f:
    transcript = json.load(f)

# Step 1: Group transcript into ~30s chunks
def group_transcript_by_time(transcript, window=30):
    chunks = []
    current_chunk = None
    current_end = None

    # Organize transcript entries by video_id
    grouped = defaultdict(list)
    for entry in transcript:
        grouped[entry["video_id"]].append(entry)

    for video_id, entries in grouped.items():
        entries.sort(key=lambda x: x["start"])  # Ensure entries are sorted
        print(f"Processing video_id: {video_id} with {len(entries)} transcript entries")

        for entry in entries:
            start = entry.get("start")
            end = entry.get("end")

            if start is None or end is None:
                continue

            if current_chunk is None:
                current_chunk = {
                    "video_id": video_id,
                    "video_url": entry["video_url"],
                    "start_time": start,
                    "text": [entry["text"]],
                }
                current_end = end
                continue

            if start - current_chunk["start_time"] < window:
                current_chunk["text"].append(entry["text"])
                current_end = end
            else:
                current_chunk["end_time"] = current_end
                current_chunk["text"] = " ".join(current_chunk["text"])
                chunks.append(current_chunk)

                current_chunk = {
                    "video_id": video_id,
                    "video_url": entry["video_url"],
                    "start_time": start,
                    "text": [entry["text"]],
                }
                current_end = end

        # Final chunk per video
        if current_chunk:
            current_chunk["end_time"] = current_end
            current_chunk["text"] = " ".join(current_chunk["text"])
            chunks.append(current_chunk)
            print(f"Created {len([c for c in chunks if c['video_id'] == video_id])} chunks for video_id: {video_id}")

        current_chunk = None
        current_end = None

    return chunks

chunks = group_transcript_by_time(transcript, window=30)

# Save the chunks to a new JSON file
output_path = "zoomcamp_transcripts/zoomcamp_chunks_30s.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(chunks, f, indent=2)

print(f"\n✅ Final chunks saved to {output_path} with total of {len(chunks)} entries (chunks).")
