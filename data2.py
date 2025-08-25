import os
import json
from googleapiclient.discovery import build
import re
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api.proxies import WebshareProxyConfig


# --- Configuration ---
# Directory to save the output JSON files
OUTPUT_DIR = "zoomcamp_transcripts"

# DataTalks.Club Zoomcamp Playlist URLs
ZOOMCAMP_PLAYLIST_URLS = [
"https://www.youtube.com/playlist?list=PL3MmuxUbc_hIoBpuc900htYF4uhEAbaT-"  # LLM Zoomcamp 2025
    # "https://www.youtube.com/playlist?list=PL3MmuxUbc_hLDZ8j0yyeX14N7fGfV4ovC"  # MLOps Zoomcamp 2025
]

# --- YouTube Data API Configuration ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyBo3P4fPTziAw_tpzEK8XFQzy_XmCQrnOM") # Replace with your actual key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

# --- Proxy Configuration for youtube-transcript-api ---
# IMPORTANT: Replace with your actual Webshare Proxy Username and Password
PROXY_USERNAME = "sazgwidb"
PROXY_PASSWORD = "vgz1dukft8x0"

# Initialize YouTubeTranscriptApi with proxy config once
ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=PROXY_USERNAME,
        proxy_password=PROXY_PASSWORD
    )
)

# --- Helper Functions ---

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
                    # This handles cases where fetch() might return internal objects directly
                    try:
                        final_segments.append({
                            'text': s.text,
                            'start': s.start,
                            'duration': s.duration
                        })
                    except AttributeError:
                        print(f"      - Warning: Object of type {type(s)} does not have expected attributes (text, start, duration). Skipping segment.")
                        continue
        transcript_segments = final_segments # Assign the cleaned list

        if not transcript_segments: # If still no segments after all attempts or conversion issues
            print(f"      - No usable transcript found for video ID: {video_id}.")
            return []

        print(f"      - Successfully fetched transcript for video ID: {video_id}.")
        return transcript_segments

    except NoTranscriptFound:
        print(f"      - No transcript found for video ID: {video_id}.")
    except TranscriptsDisabled:
        print(f"      - Transcripts are disabled for video ID: {video_id}.")
    except Exception as e:
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

            # MODIFIED: Create a separate entry for each transcript segment
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
                        "end": segment['start'] + segment['duration'] # NEW: Add the 'end' field
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
                    "end": None # NEW: Add 'end' as None if no transcript
                }
                all_zoomcamp_metadata.append(video_metadata_no_transcript)


    print("\n--- All Zoomcamp playlists processed. ---")
    # Note: Total unique videos collected will now reflect total segments + videos without transcripts
    print(f"Total entries (segments or video metadata) collected: {len(all_zoomcamp_metadata)}")

    # Save all collected metadata into one large JSON file
    output_file_path = os.path.join(OUTPUT_DIR, "all_zoomcamp_metadata_with_segmented_transcripts.json")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_zoomcamp_metadata, f, ensure_ascii=False, indent=2) # Indent=2 as requested
        print(f"All collected metadata combined and saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving combined JSON file: {e}")

if __name__ == "__main__":
    main()
