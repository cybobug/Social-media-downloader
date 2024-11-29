import os
import uuid
import logging
from flask import Flask, request, jsonify, send_file, abort, render_template
from yt_dlp import YoutubeDL
import validators

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Directory to store temporary downloads
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Path to cookies.txt file (optional for authenticated downloads)
COOKIES_FILE = os.path.join(os.getcwd(), "cookies.txt")

def download_video(url):
    """
    Downloads a video from the given URL using yt_dlp and saves it locally.
    """
    try:
        # Validate the URL
        if not validators.url(url):
            raise ValueError("Invalid URL provided.")

        # Generate a unique filename
        unique_id = str(uuid.uuid4())
        filename_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

        # yt_dlp options
        ydl_opts = {
            "outtmpl": filename_template,
            "format": "bestvideo+bestaudio/best",  # Best quality video and audio
            "merge_output_format": "mp4",
            "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
            "quiet": True,
        }

        # Download the video
        with YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading video from URL: {url}")
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info).replace(".webm", ".mp4")

        # Ensure the file exists
        if not os.path.exists(downloaded_file):
            raise FileNotFoundError("The video file was not downloaded successfully.")

        return {
            "title": info.get("title", "Unknown Title"),
            "filepath": downloaded_file,
        }
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise ValueError("Video download failed. Please check the URL or try again later.")

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route for handling video download requests.
    """
    if request.method == "POST":
        try:
            # Retrieve the video URL from the form
            video_url = request.form.get("media-url")
            if not video_url:
                abort(400, description="No URL provided.")

            # Download the video
            video_info = download_video(video_url)

            # Return the file as a response
            filepath = video_info["filepath"]

            # Ensure the file is removed after the response
            from flask import after_this_request
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(filepath)
                    logger.info(f"Deleted temporary file: {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {filepath}: {e}")
                return response

            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True, download_name=os.path.basename(filepath))
            else:
                abort(404, description="Downloaded file not found.")
        except ValueError as ve:
            logger.warning(f"Validation error: {ve}")
            abort(400, description=str(ve))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            abort(500, description="Internal server error.")
    return render_template("index.html")

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="An unexpected error occurred. Please try again later."), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
