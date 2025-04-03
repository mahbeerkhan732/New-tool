import requests
import time

API_KEY = "AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9IlU"  # Replace with regenerated key
KEYWORD = "tech news"  # Replace with your keyword
CHECK_INTERVAL = 600

def fetch_new_videos():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": KEYWORD,
        "type": "video",
        "order": "date",
        "maxResults": 50,  # Increased to catch more videos
        "key": API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()
        if "error" in data:
            print(f"API Error: {data['error']['message']}")
            return []
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []

def monitor():
    seen_video_ids = set()  # Track all known videos
    while True:
        videos = fetch_new_videos()
        if not videos:
            time.sleep(CHECK_INTERVAL)
            continue
        
        # Process oldest first to avoid missing videos between checks
        for video in reversed(videos):
            video_id = video["id"]["videoId"]
            if video_id not in seen_video_ids:
                title = video["snippet"]["title"]
                print(f"\nNew Video Found: {title}")
                print(f"URL: https://youtube.com/watch?v={video_id}")
                seen_video_ids.add(video_id)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
