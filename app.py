from flask import Flask, request, render_template, jsonify
import os
from yt_dlp import YoutubeDL

app = Flask(__name__)

def download_video(url):
    """
    Downloads a video from the provided URL to a temporary directory.
    """
    ydl_opts = {
        'outtmpl': '/tmp/%(title)s.%(ext)s',  # Save files to /tmp directory
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
    }
    try:
        print(f"Downloading video from: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return info_dict.get("title", "video"), None
    except Exception as e:
        print(f"Error during download: {e}")
        return None, str(e)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("media-url")
        if not video_url:
            return jsonify({"error": "No URL provided"}), 400

        video_title, error = download_video(video_url)
        if error:
            return jsonify({"error": f"Download failed: {error}"}), 500

        return jsonify({"message": f"Download successful: {video_title}"}), 200
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
