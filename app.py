from flask import Flask, request, render_template, send_from_directory, jsonify
import os
from yt_dlp import YoutubeDL
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloaded_videos"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_video(url, output_dir=DOWNLOAD_FOLDER):
    """
    Downloads a video from the provided URL.
    """
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
    }
    try:
        print(f"Downloading video from: {url}")
        print(f"Download options: {ydl_opts}")
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            print(f"Downloaded video info: {info_dict}")
            return info_dict.get("title", "video"), output_dir
    except Exception as e:
        print(f"Error during download: {e}")
        return str(e), None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        video_url = request.form.get("media-url")
        if not video_url:
            return jsonify({"error": "No URL provided"}), 400

        video_title, folder = download_video(video_url)
        if folder:
            return jsonify({"message": f"Download successful. File saved as {video_title}."}), 200
        else:
            return jsonify({"error": "Download failed"}), 500
    return render_template("index.html")

@app.route("/downloaded/<path:filename>")
def serve_download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route("/test_url")
def test_url():
    url = request.args.get("url")
    try:
        response = requests.get(url)
        return jsonify({"status": response.status_code, "headers": dict(response.headers)})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/test_write")
def test_write():
    try:
        test_file = os.path.join(DOWNLOAD_FOLDER, "test.txt")
        with open(test_file, "w") as f:
            f.write("Write test successful!")
        return jsonify({"message": "Write successful"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
