import requests
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    filename='youtube_monitor.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

API_KEY = "AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9IlU"  # Replace with your valid API key
KEYWORD = "tech news"  # Replace with your desired keyword
CHECK_INTERVAL = 600  # 10 minutes

def fetch_new_videos():
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": KEYWORD,
        "type": "video",
        "order": "date",
        "maxResults": 50,
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Check for HTTP errors
        data = response.json()

        if "error" in data:
            error_message = data["error"]["message"]
            logging.error(f"API Error: {error_message}")
            return []
        return data.get("items", [])

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return []

def monitor():
    seen_video_ids = set()

    while True:
        try:
            videos = fetch_new_videos()
            if not videos:
                logging.info(f"No new videos found for keyword: {KEYWORD}")
                time.sleep(CHECK_INTERVAL)
                continue

            for video in reversed(videos):
                video_id = video["id"]["videoId"]
                if video_id not in seen_video_ids:
                    title = video["snippet"]["title"]
                    published_at = video["snippet"]["publishedAt"]
                    url = f"https://youtube.com/watch?v={video_id}"
                    logging.info(f"New Video Found: {title}")
                    logging.info(f"Published: {published_at}")
                    logging.info(f"URL: {url}")
                    seen_video_ids.add(video_id)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logging.info("YouTube Video Monitor started.")
    monitor()
```
