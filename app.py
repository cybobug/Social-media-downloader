import os
import logging
import requests
from flask import Flask, request, Response, render_template, abort
from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Path to cookies.txt file (if needed for authentication)
COOKIES_FILE = os.path.join(os.getcwd(), "cookies.txt")


def fetch_video_info(url):
    """
    Fetches video metadata and the direct streaming URL using yt_dlp.
    """
    try:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            "quiet": True,
            "noplaylist": True,  # Only process a single video
        }

        with YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Fetching video info for URL: {url}")
            info = ydl.extract_info(url, download=False)
            return {
                "url": info["url"],
                "title": info.get("title", "video"),
                "ext": info.get("ext", "mp4"),
            }
    except Exception as e:
        logger.error(f"Failed to fetch video info: {e}")
        raise ValueError("Failed to fetch video details. Ensure the URL is correct.")


def stream_video_content(video_url):
    """
    Streams video content from the direct URL to the client.
    """
    try:
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk
    except Exception as e:
        logger.error(f"Error streaming video content: {e}")
        raise ValueError("Failed to stream video content.")


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route for handling video streaming requests.
    """
    if request.method == "POST":
        try:
            # Retrieve the video URL from the form
            video_url = request.form.get("media-url")
            if not video_url:
                abort(400, description="No URL provided.")

            # Fetch video info
            video_info = fetch_video_info(video_url)

            # Stream the video
            return Response(
                stream_video_content(video_info["url"]),
                content_type=f"video/{video_info['ext']}",
                headers={
                    "Content-Disposition": f'attachment; filename="{video_info["title"]}.{video_info["ext"]}"'
                },
            )
        except ValueError as ve:
            logger.warning(f"Validation error: {ve}")
            abort(400, description=str(ve))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            abort(500, description="Internal server error.")
    return render_template("index.html")


@app.errorhandler(400)
def bad_request_error(error):
    return render_template("index.html", error=str(error)), 400


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("index.html", error="Internal server error. Please try again later."), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
