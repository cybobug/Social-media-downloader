import os
import uuid
import requests
from flask import Flask, request, render_template, send_file, jsonify
from yt_dlp import YoutubeDL
import logging
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Sophisticated headers to mimic browser requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

def validate_url(url):
    """
    Validate and sanitize the input URL
    """
    if not url:
        raise ValueError("No URL provided")
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError("Invalid URL format")
    
    return url

def download_video(url):
    """
    Download video with enhanced error handling and unique filename
    """
    # Ensure unique filename to prevent conflicts
    unique_id = str(uuid.uuid4())
    
    # Advanced yt-dlp options
    ydl_opts = {
        'outtmpl': f'/tmp/{unique_id}_%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'no_color': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'no_progress': True,
        'throttledbytes': 1024 * 1024,  # 1 MB throttling
        'retries': 3,
        'fragment_retries': 3,
        'http_headers': HEADERS,
        'progress_hooks': [lambda d: print_progress(d)],
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Extract video information
            info_dict = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            for filename in os.listdir('/tmp'):
                if unique_id in filename:
                    full_path = os.path.join('/tmp', filename)
                    
                    # Log successful download
                    logger.info(f"Successfully downloaded: {info_dict.get('title', 'Unknown')}")
                    
                    return {
                        'title': info_dict.get('title', 'Unknown'),
                        'filepath': full_path,
                        'duration': info_dict.get('duration', 0),
                        'ext': info_dict.get('ext', 'mp4')
                    }
        
        raise Exception("No file found after download")
    
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise

def print_progress(d):
    """
    Optional progress tracking
    """
    if d['status'] == 'finished':
        print('Video downloaded successfully.')

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route for video download
    """
    if request.method == "POST":
        try:
            # Get URL from request
            video_url = request.form.get("media-url")
            
            # Validate URL
            validated_url = validate_url(video_url)
            
            # Attempt download
            video_info = download_video(validated_url)
            
            # Prepare response
            return jsonify({
                "status": "success",
                "title": video_info['title'],
                "duration": video_info['duration'],
                "filepath": video_info['filepath']
            }), 200
        
        except ValueError as ve:
            # Handle URL validation errors
            logger.warning(f"URL Validation Error: {str(ve)}")
            return jsonify({"status": "error", "message": str(ve)}), 400
        
        except Exception as e:
            # Handle other download errors
            logger.error(f"Download Error: {str(e)}")
            return jsonify({"status": "error", "message": "Video download failed"}), 500
    
    # GET request renders the template
    return render_template("index.html")

@app.route("/download/<path:filename>")
def download_file(filename):
    """
    Serve the downloaded file
    """
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        return jsonify({"status": "error", "message": "File not found"}), 404

if __name__ == "__main__":
    # Ensure tmp directory exists
    os.makedirs('/tmp', exist_ok=True)
    
    # Run the app
    app.run(
        host='0.0.0.0', 
        port=int(os.environ.get('PORT', 5000)),
        debug=False
    )
