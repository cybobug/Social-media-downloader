from flask import Flask, request, render_template, send_from_directory, jsonify
import os
from yt_dlp import YoutubeDL

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
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return info_dict.get("title", "video"), output_dir
    except Exception as e:
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

if __name__ == "__main__":
    app.run(debug=True)
