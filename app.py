from flask import Flask, request, render_template, Response, abort
from yt_dlp import YoutubeDL
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_video_info(url):
    """
    Extracts video metadata and streaming URL using yt_dlp with cookies.
    """
    try:
        # Check if cookies file exists
        cookies_path = "cookies.txt"
        if not os.path.exists(cookies_path):
            logger.warning("cookies.txt not found. Restricted videos may fail.")

        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "format": "bestvideo+bestaudio/best",
            "cookies": cookies_path if os.path.exists(cookies_path) else None,  # Use cookies if available
        }
        if "youtube.com/shorts/" in url:
            url = url.replace("youtube.com/shorts/", "youtube.com/watch?v=")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video info fetched: {info}")

            # Extract the video URL
            video_url = info.get("url") or (
                info.get("formats")[-1]["url"] if "formats" in info else None
            )
            if not video_url:
                raise ValueError("Unable to retrieve video URL from yt_dlp response.")

            return {
                "url": video_url,
                "title": info.get("title", "video").replace(" ", "_"),
                "ext": info.get("ext", "mp4"),
                "filesize": info.get("filesize", 0),
            }
    except Exception as e:
        logger.error(f"Failed to fetch video info: {e}")
        raise ValueError("Invalid URL or unsupported platform.")

def stream_video_content(video_url):
    """
    Streams video content from the direct URL to the client.
    Implements retries for robust downloading.
    """
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        with session.get(video_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=128 * 1024):  # 128 KB chunks
                yield chunk
    except Exception as e:
        logger.error(f"Error streaming video: {e}")
        raise ValueError("Failed to stream video content.")

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route to handle video download requests.
    """
    if request.method == "POST":
        video_url = request.form.get("media-url")
        if not video_url:
            abort(400, "No URL provided.")
        try:
            video_info = fetch_video_info(video_url)
            logger.info(f"Resolved video URL: {video_info['url']}")

            # Prepare headers for the response
            headers = {
                "Content-Disposition": f'attachment; filename="{video_info["title"]}.{video_info["ext"]}"',
            }
            if video_info["filesize"]:
                headers["Content-Length"] = str(video_info["filesize"])

            # Stream video content directly to user
            return Response(
                stream_video_content(video_info["url"]),
                content_type=f"video/{video_info["ext"]}",
                headers=headers,
            )
        except ValueError as ve:
            return render_template("index.html", error=str(ve)), 400
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return render_template("index.html", error="An internal error occurred."), 500

    return render_template("index.html", error=None)

@app.errorhandler(400)
def bad_request_error(error):
    return render_template("index.html", error=str(error)), 400

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("index.html", error="Internal server error. Please try again later."), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
