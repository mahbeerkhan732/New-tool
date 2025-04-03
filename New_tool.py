import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
import configparser
import plotly.express as px

# Handle streamlit-tags dependency
try:
    from streamlit_tags import st_tags
except ImportError:
    st.error("Required package missing! Install with: pip install streamlit-tags")
    st.stop()

# Configuration
config = configparser.ConfigParser()
config.read('config.ini')

# YouTube API Configuration
API_KEY = config.get('YOUTUBE', 'API_KEY', fallback='AIzaSyBA-WdCo1FfkfQ1G5k5M3AFTV0x-kq9IlU')
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# App Configuration
st.set_page_config(
    page_title="AI YouTube Trend Analyzer Pro",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    .st-bb {background-color: #ffffff;}
    .st-at {background-color: #eef2f7;}
    h1 {color: #2b5876;}
    h2 {color: #4e4376;}
    .stProgress > div > div > div > div {background-color: #2b5876;}
</style>
""", unsafe_allow_html=True)

# App Header
st.title("🔍 AI-Powered YouTube Trend Analyzer Pro")
st.markdown("### Discover Viral Content Opportunities with Advanced AI Insights")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    # API Check
    if API_KEY == 'ENTER_YOUR_API_KEY_HERE':
        st.error("YouTube API Key Required!")
        st.markdown("Get API Key: [Google Cloud Console](https://console.cloud.google.com/)")
        st.stop()

    # Date Configuration
    st.subheader("📅 Date Range")
    days = st.slider("Analysis Period (Days)", 1, 3650, 365, 
                    help="Select time range for content analysis")

    # Channel Filters
    st.subheader("👥 Channel Filters")
    min_subs, max_subs = st.slider(
        "Subscriber Range",
        0, 1000000, (0, 10000),
        help="Filter channels by subscriber count"
    )

    # Content Settings
    st.subheader("🎯 Content Parameters")
    col1, col2 = st.columns(2)
    with col1:
        min_results = st.number_input("Min Results/Keyword", 1, 50, 3)
    with col2:
        max_results = st.number_input("Max Results/Keyword", 1, 50, 10)

    # AI Configuration
    st.subheader("🧠 AI Settings")
    analysis_depth = st.selectbox(
        "Analysis Depth",
        ["Basic", "Advanced", "Expert"],
        index=1
    )

    # Keyword Management
    st.header("🔑 Keyword Configuration")
    keyword_presets = {
        "Relationships": ["Dating Advice", "Marriage Tips", "Breakup Stories"],
        "True Stories": ["Crime Documentaries", "Survival Stories"],
        "Viral Content": ["Reddit Recap", "TikTok Compilations"]
    }
    
    selected_categories = st.multiselect(
        "Content Categories",
        list(keyword_presets.keys()),
        default=["Relationships"]
    )
    
    custom_keywords = st_tags(
        label="Custom Keywords:",
        text="Press enter to add",
        value=["Viral Stories"],
        suggestions=["Scary Stories", "Family Drama"]
    )

    # Export Options
    st.header("📤 Export Options")
    export_format = st.selectbox(
        "Report Format",
        ["CSV", "Excel", "JSON"],
        index=0
    )

# Initialize Keywords
keywords = []
for category in selected_categories:
    keywords.extend(keyword_presets[category])
keywords.extend(custom_keywords)
keywords = list(set(keywords))

# API Functions
@st.cache_data(ttl=3600)
def fetch_youtube_data(url, params):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Video Processing
def process_video(video_data, channel_data):
    try:
        stats = video_data["statistics"]
        snippet = video_data["snippet"]
        channel_info = next(
            (c for c in channel_data["items"] 
             if c["id"] == snippet["channelId"]), None
        )
        
        if not channel_info:
            return None
            
        subs = int(channel_info["statistics"].get("subscriberCount", 0))
        if not (min_subs <= subs <= max_subs):
            return None

        return {
            "Title": snippet.get("title", "Untitled"),
            "Views": int(stats.get("viewCount", 0)),
            "Likes": int(stats.get("likeCount", 0)),
            "Comments": int(stats.get("commentCount", 0)),
            "Subscribers": subs,
            "Channel": snippet.get("channelTitle", "Unknown"),
            "Published": snippet.get("publishedAt", ""),
            "URL": f"https://youtu.be/{video_data['id']}",
            "Tags": ", ".join(snippet.get("tags", [])[:5]),
            "Description": snippet.get("description", "")[:500]
        }
    except Exception as e:
        return None

# Main Analysis Function
def analyze_keyword(keyword):
    try:
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
            "maxResults": max_results,
            "key": API_KEY
        }
        
        search_data = fetch_youtube_data(YOUTUBE_SEARCH_URL, search_params)
        if not search_data or "items" not in search_data:
            return []
            
        video_ids = [item["id"]["videoId"] for item in search_data["items"]]
        channel_ids = list({item["snippet"]["channelId"] for item in search_data["items"]})

        # Get detailed data
        videos_data = fetch_youtube_data(YOUTUBE_VIDEO_URL, {
            "part": "statistics,snippet",
            "id": ",".join(video_ids),
            "key": API_KEY
        })
        
        channels_data = fetch_youtube_data(YOUTUBE_CHANNEL_URL, {
            "part": "statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY
        })

        return [process_video(v, channels_data) for v in videos_data.get("items", []) if v]

    except Exception as e:
        st.error(f"Error processing {keyword}: {str(e)}")
        return []

# Main Application Logic
if st.button("🚀 Start Analysis", type="primary"):
    with st.spinner("🔍 Analyzing YouTube Trends..."):
        try:
            # Process all keywords
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = []
                for keyword_results in executor.map(analyze_keyword, keywords):
                    results.extend([r for r in keyword_results if r])
            
            if not results:
                st.warning("No results found matching criteria")
                st.stop()

            df = pd.DataFrame(results)
            df = df.sort_values("Views", ascending=False).head(min(len(results), max_results*len(keywords)))

            # Display Results
            st.success(f"✅ Analysis Complete: Found {len(df)} Qualified Videos")
            
            # Metrics Dashboard
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Videos", len(df))
            col2.metric("Avg Views", f"{df['Views'].mean():,.0f}")
            col3.metric("Top Channel", df.iloc[0]['Channel'])

            # Detailed Analysis
            st.header("📊 Video Performance Analysis")
            tab1, tab2 = st.tabs(["Trend Visualization", "Raw Data"])
            
            with tab1:
                fig = px.scatter(df, x='Subscribers', y='Views', 
                               hover_data=['Title', 'Channel'],
                               log_x=True, log_y=True)
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                st.dataframe(df[['Title', 'Channel', 'Views', 'Subscribers', 'Published']], 
                           height=500)

            # Video Details Section
            st.header("🎥 Top Performing Content")
            for idx, row in df.iterrows():
                with st.expander(f"{row['Title']} ({row['Views']:,} views)"):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.image(f"https://img.youtube.com/vi/{row['URL'].split('/')[-1]}/mqdefault.jpg", 
                               width=300)
                    with col2:
                        st.markdown(f"""
                        **Channel:** {row['Channel']}  
                        **Subscribers:** {row['Subscribers']:,}  
                        **Published:** {row['Published'][:10]}  
                        **Tags:** {row['Tags']}  
                        """)
                        st.progress(min(row['Views']/1000000, 1.0))
                        st.caption(row['Description'])

            # Export Functionality
            st.header("💾 Export Results")
            if export_format == "CSV":
                st.download_button("Download CSV", df.to_csv(), "youtube_analysis.csv")
            elif export_format == "Excel":
                df.to_excel("youtube_analysis.xlsx")
                with open("youtube_analysis.xlsx", "rb") as f:
                    st.download_button("Download Excel", f, "youtube_analysis.xlsx")
            elif export_format == "JSON":
                st.download_button("Download JSON", df.to_json(), "youtube_analysis.json")

        except Exception as e:
            st.error(f"Analysis Failed: {str(e)}")
            st.stop()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>© 2024 YouTube Trend Analyzer Pro • v2.1</p>
    <p>Data Source: YouTube API • Analytics Powered by AI</p>
</div>
""", unsafe_allow_html=True)
