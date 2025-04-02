import requests
import time

API_KEY = "AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9IlU"
KEYWORD = "Your_Search_Keyword"
CHECK_INTERVAL = 600  # 10 minutes in seconds

def fetch_new_videos():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": KEYWORD,
        "type": "video",
        "order": "date",  # Sort by upload date
        "maxResults": 10,
        "key": API_KEY
    }
    response = requests.get(url, params=params).json()
    return response.get("items", [])

def monitor():
    last_video_id = None
    while True:
        videos = fetch_new_videos()
        if videos:
            latest_video = videos[0]
            current_video_id = latest_video["id"]["videoId"]
            
            if current_video_id != last_video_id:
                print(f"New Video Found: {latest_video['snippet']['title']}")
                print(f"URL: https://youtube.com/watch?v={current_video_id}")
                last_video_id = current_video_id
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()
