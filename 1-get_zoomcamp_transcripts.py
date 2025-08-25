import os
import json
import re
import csv # New import for CSV logging
from datetime import datetime # New import for timestamp in error log
from dotenv import load_dotenv 

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.proxies import WebshareProxyConfig

# --- Configuration ---
# Directory to save the transcript JSON files
OUTPUT_DIR = "zoomcamp_transcripts"
# Path for the error log CSV file
ERROR_LOG_FILE = os.path.join(OUTPUT_DIR, "error_log.csv")

# DataTalks.Club Zoomcamp Playlist URLs
ZOOMCAMP_PLAYLIST_URLS = [
#test
# "https://www.youtube.com/watch?v=-zpVha7bw5A","https://www.youtube.com/watch?v=INVALID_VIDEO_ID",
# "https://www.youtube.com/playlist?list=PL3MmuxUbc_hLDZ8j0yyeX14N7fGfV4ovC"
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hIoBpuc900htYF4uhEAbaT-",  # LLM Zoomcamp 2025
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hKiIVNf7DeEt_tGjypOYtKV", # LLM Zoomcamp 2024
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R", #LLM zoomcamp
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hLDZ8j0yyeX14N7fGfV4ovC",  # MLOps Zoomcamp 2025
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hJD0AVR2Un_GSVGMpotGM2t", # MLOPS zoomcamp 2024
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hKqamJqQ7Ew8HxptJYnXqQM", # MLOps Zoomcamp 2023
    "http://www.youtube.com/playlist?list=PL3MmuxUbc_hLG1MoGNxJ9DmQSSM2bEdQT",  # MLOps Zoomcamp 2022
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hIUISrluw_A7wDSmfOhErJK", # MLOps Zoomcamp  
    "http://www.youtube.com/playlist?list=PL3MmuxUbc_hJZdpLpRHp7dg6EOx828q6y",  # Data Engineering Zoomcamp 2025
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hKihpnNQ9qtTmWYy26bPrSb", # Data Engineering Zoomcamp 2024
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hJjEePXIdE-LVUx_1ZZjYGW", # Data Engineering Zoomcamp 2023
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hKVX8VnwWCPaWlIHf1qmg8s", # Data Engineering Zoomcamp 2022
    "http://www.youtube.com/playlist?list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb" , # Data Engineering Zoomcamp 
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hJoui-E7wf2r5wWgET3MMZt",  # Machine Learning Zoomcamp 2024
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hJo_PzMibLDcEGyazxYAtV0", # Machine Learning Zoomcamp 2023
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hL5QBBEyKUXKuTNx-3cTpKs", # Machine Learning Zoomcamp 2022
    "https://www.youtube.com/playlist?list=PL3MmuxUbc_hL4Gx-wzOJMT4q1K-cArKqu", # Machine Learning Zoomcamp 2021
    "http://www.youtube.com/playlist?list=PL3MmuxUbc_hIhxl5Ji8t4O6lPAOpHaCLR"  # Machine Learning Zoomcamp
]

# --- YouTube Data API Configuration ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") # Replace with your actual key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

# --- Proxy Configuration for youtube-transcript-api ---
# IMPORTANT: Replace with your actual Webshare Proxy Username and Password
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

# Initialize YouTubeTranscriptApi with proxy config
# This instance will be reused for all transcript fetches
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=PROXY_USERNAME,
        proxy_password=PROXY_PASSWORD
    )
)

# --- Helper Functions ---

def log_error(video_id, error_type, error_message):
    """Logs errors to a CSV file."""
    # Ensure output directory exists before writing log
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    file_exists = os.path.isfile(ERROR_LOG_FILE)
    with open(ERROR_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['video_id', 'error_type', 'error_message', 'timestamp'])
        writer.writerow([video_id, error_type, error_message, datetime.now().isoformat()])
    print(f"      - Error logged for video ID {video_id}: {error_type} - {error_message}")


def get_playlist_id_from_url(url):
    """Extracts playlist ID from a YouTube playlist URL."""
    match = re.search(r'list=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None

def get_video_id_from_url(url):
    """Extracts video ID from a YouTube video URL."""
    match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(1)
    return None

def get_playlist_title_from_id(playlist_id):
    """Retrieves playlist title using YouTube Data API."""
    try:
        playlist_request = youtube.playlists().list(
            part="snippet",
            id=playlist_id
        )
        playlist_response = playlist_request.execute()
        if playlist_response.get("items"):
            return playlist_response["items"][0]["snippet"]["title"]
    except Exception as e:
        error_message = f"Error getting playlist title for ID {playlist_id}: {e}"
        log_error(playlist_id, "Playlist_API_Error", error_message)
        print(f"Error getting playlist title for ID {playlist_id}: {e}. Using default title.")
    return "Unknown Playlist"

def get_video_details(video_id):
    """Retrieves video title and URL using YouTube Data API."""
    video_title = "Unknown Video"
    video_url = f"https://www.youtube.com/watch?v={video_id}" # Construct URL from ID

    try:
        video_request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        video_response = video_request.execute()
        if video_response.get("items"):
            video_title = video_response["items"][0]["snippet"]["title"]
    except Exception as e:
        error_message = f"Error getting video title for ID {video_id}: {e}"
        log_error(video_id, "Video_API_Error", error_message)
        print(f"    - Error getting video title for ID {video_id}: {e}. Using default title.")
    
    return video_title, video_url

def get_video_transcript_segments(video_id):
    """
    Fetches transcript segments for a given video ID using the proxied YouTubeTranscriptApi.
    Ensures the output is a list of dictionaries.
    Returns a list of dictionaries with 'text', 'start', and 'duration'.
    Returns an empty list if no transcript is found or an error occurs.
    """
    transcript_segments_raw = [] # Temporarily store raw fetched data
    try:
        # Prioritize English, then try any available transcript
        transcript_segments_raw = ytt_api.fetch(video_id, languages=['en', 'en-US'])
        
        if not transcript_segments_raw:
            available_transcripts = ytt_api.list_transcripts(video_id)
            if available_transcripts:
                try:
                    # Try to find an auto-generated English transcript first
                    transcript_segments_raw = available_transcripts.find_transcript(['a.en', 'a.en-US', 'en', 'en-US']).fetch()
                except Exception:
                    # If specific English not found, try to fetch the first available one
                    if available_transcripts:
                        transcript_segments_raw = available_transcripts[0].fetch() 
            
        # Ensure transcript_segments is always a list of dictionaries
        # This is the crucial part to prevent 'FetchedTranscriptSnippet' object is not subscriptable
        final_segments = []
        if transcript_segments_raw:
            for s in transcript_segments_raw:
                if isinstance(s, dict):
                    final_segments.append(s)
                else:
                    # If it's not a dict, assume it's a FetchedTranscriptSnippet and extract attributes
                    try:
                        final_segments.append({
                            'text': s.text,
                            'start': s.start,
                            'duration': s.duration
                        })
                    except AttributeError:
                        error_message = f"Object of type {type(s)} does not have expected attributes (text, start, duration)."
                        log_error(video_id, "Transcript_Parsing_Error", error_message)
                        print(f"      - Warning: {error_message} Skipping segment.")
                        continue
        transcript_segments = final_segments # Assign the cleaned list

        if not transcript_segments: # If still no segments after all attempts or conversion issues
            log_error(video_id, "Transcript_Not_Found", "No usable transcript found for video ID.")
            print(f"      - No usable transcript found for video ID: {video_id}.")
            return []

        print(f"      - Successfully fetched transcript for video ID: {video_id}.")
        return transcript_segments

    except NoTranscriptFound:
        log_error(video_id, "Transcript_Not_Found", "No transcript found.")
        print(f"      - No transcript found for video ID: {video_id}.")
    except TranscriptsDisabled:
        log_error(video_id, "Transcripts_Disabled", "Transcripts are disabled.")
        print(f"      - Transcripts are disabled for video ID: {video_id}.")
    except Exception as e:
        error_message = f"An unexpected error occurred while fetching transcript: {e}"
        log_error(video_id, "Transcript_Fetch_Error", error_message)
        print(f"      - An unexpected error occurred while fetching transcript for ID {video_id}: {e}.")
    
    return [] # Return empty list on any error

# --- Main Execution ---

def main():
    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory '{OUTPUT_DIR}' ensured.")

    all_zoomcamp_metadata = [] # This will store all video metadata (or segment metadata)
    processed_video_ids = set() # Set to store IDs of videos that have been processed

    # Process each identified Zoomcamp playlist
    for playlist_url in ZOOMCAMP_PLAYLIST_URLS:
        playlist_id = get_playlist_id_from_url(playlist_url)
        if not playlist_id:
            log_error("N/A", "Playlist_ID_Extraction_Error", f"Could not extract playlist ID from URL: {playlist_url}")
            print(f"Skipping playlist {playlist_url} as its ID could not be extracted.")
            continue

        playlist_title = get_playlist_title_from_id(playlist_id)
        print(f"\n--- Starting processing for playlist: '{playlist_title}' (ID: {playlist_id}) ---")
        
        # Fetch video IDs from the playlist using YouTube Data API
        playlist_video_ids = []
        next_page_token = None
        try:
            while True:
                playlist_items_request = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50, # Max results per page
                    pageToken=next_page_token
                )
                playlist_items_response = playlist_items_request.execute()

                for item in playlist_items_response.get("items", []):
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    playlist_video_ids.append(video_id)
                
                next_page_token = playlist_items_response.get("nextPageToken")
                if not next_page_token:
                    break # No more pages

            print(f"  Successfully fetched {len(playlist_video_ids)} video IDs from playlist.")

        except Exception as e:
            error_message = f"Error fetching video IDs for playlist {playlist_url} with YouTube Data API: {e}"
            log_error(playlist_id, "Playlist_Video_ID_Fetch_Error", error_message)
            print(f"  Error fetching video IDs for playlist {playlist_url} with YouTube Data API: {e}")
            print("  Please ensure your YOUTUBE_API_KEY is correct and YouTube Data API v3 is enabled for your project.")
            continue # Skip to next playlist if there's an error

        if not playlist_video_ids:
            print(f"  No videos found or error retrieving videos for playlist '{playlist_title}'.")
            continue

        for i, current_video_id in enumerate(playlist_video_ids):
            if current_video_id in processed_video_ids:
                print(f"  Skipping video {i+1}/{len(playlist_video_ids)}: {current_video_id} (Already processed in another playlist)")
                continue
            else:
                processed_video_ids.add(current_video_id) # Mark as processed

            print(f"  Processing video {i+1}/{len(playlist_video_ids)}: {current_video_id}")
            
            video_title, video_url = get_video_details(current_video_id)
            
            # Fetch transcript segments for the current video
            transcript_segments = get_video_transcript_segments(current_video_id)

            # Create a separate entry for each transcript segment
            if transcript_segments:
                for segment_index, segment in enumerate(transcript_segments):
                    segment_metadata = {
                        "video_id": current_video_id,
                        "video_title": video_title,
                        "video_url": video_url,
                        "playlist_id": playlist_id,
                        "playlist_title": playlist_title,
                        "text": segment['text'],
                        "start": segment['start'],
                        "duration": segment['duration'],
                        "end": segment['start'] + segment['duration']
                        # You can add a unique ID for each segment if needed, e.g.:
                        # "segment_id": f"{current_video_id}_segment_{segment_index + 1:03d}"
                    }
                    all_zoomcamp_metadata.append(segment_metadata)
            else:
                # If no transcript, still add video metadata but with transcript fields as None
                video_metadata_no_transcript = {
                    "video_id": current_video_id,
                    "video_title": video_title,
                    "video_url": video_url,
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title,
                    "text": None,
                    "start": None,
                    "duration": None,
                    "end": None
                }
                all_zoomcamp_metadata.append(video_metadata_no_transcript)


    print("\n--- All Zoomcamp playlists processed. ---")
    print(f"Total entries (segments or video metadata) collected: {len(all_zoomcamp_metadata)}")

    # Save all collected metadata into one large JSON file
    output_file_path = os.path.join(OUTPUT_DIR, "all_zoomcamp_metadata_with_segmented_transcripts.json")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_zoomcamp_metadata, f, ensure_ascii=False, indent=2)
        print(f"All collected metadata combined and saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving combined JSON file: {e}")
        log_error("N/A", "JSON_Save_Error", f"Error saving combined JSON file: {e}")

if __name__ == "__main__":
    main()
