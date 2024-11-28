import os
import uuid
import logging
from flask import Flask, request, render_template, jsonify, send_file
from yt_dlp import YoutubeDL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Directory to store downloaded videos
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_video(url):
    """
    Download video from any supported platform using yt_dlp without requiring login or cookies.
    """
    try:
        # Generate a unique filename for the downloaded video
        unique_id = str(uuid.uuid4())
        filename_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

        # Configure yt_dlp options
        ydl_opts = {
            "outtmpl": filename_template,
            "format": "bestvideo+bestaudio/best",  # Best video and audio quality
            "merge_output_format": "mp4",  # Ensure output is in MP4 format
            "quiet": False,  # Enables verbose output in logs
            "nocheckcertificate": True,  # Bypass SSL certificate checks
            "ignoreerrors": True,  # Skip errors and continue processing
            "geo_bypass": True,  # Attempt to bypass geographic restrictions
            "geo_bypass_country": "US",  # Force region to the US
        }

        # Use yt_dlp to download the video
        with YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading video from URL: {url}")
            info = ydl.extract_info(url, download=True)  # Download and extract video info
            downloaded_file = ydl.prepare_filename(info)  # Get downloaded filename

        return {
            "title": info.get("title", "Unknown Title"),
            "filepath": downloaded_file,
            "duration": info.get("duration", "Unknown Duration"),
            "thumbnail": info.get("thumbnail", ""),
        }

    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise ValueError("Video download failed. Please check the URL or try again later.")

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route for video download
    """
    if request.method == "POST":
        try:
            # Get the video URL from the request
            video_url = request.form.get("media-url")

            # Validate the URL (basic check)
            if not video_url:
                raise ValueError("No URL provided")

            # Attempt to download the video
            video_info = download_video(video_url)

            # Prepare a JSON response
            return jsonify({
                "status": "success",
                "title": video_info["title"],
                "filepath": os.path.basename(video_info["filepath"]),
            }), 200

        except ValueError as ve:
            # Handle validation errors
            logger.warning(f"Validation Error: {ve}")
            return jsonify({"status": "error", "message": str(ve)}), 400

        except Exception as e:
            # Handle other download errors
            logger.error(f"Unexpected Error: {e}")
            return jsonify({"status": "error", "message": "Video download failed"}), 500

    # For GET requests, render the HTML form
    return render_template("index.html")

@app.route("/download/<path:filename>")
def download_file(filename):
    """
    Serve the downloaded file
    """
    try:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        logger.error(f"File download error: {e}")
        return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == "__main__":
    # Run the Flask app
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
