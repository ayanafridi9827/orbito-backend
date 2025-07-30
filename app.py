import os
import subprocess
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import traceback

app = Flask(__name__)
CORS(app)

# A simple in-memory store for progress tracking
progress_store = {}

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")
    download_id = "download"  # Using a fixed ID for simplicity

    if not video_url:
        return jsonify({"success": False, "error": "URL is required"}), 400

    try:
        progress_store[download_id] = {"status": "starting", "percent": 0}

        import sys

        # Command to get video info as JSON
        info_command = [
            sys.executable,  # Use the current python interpreter
            '-m', 'yt_dlp',
            '--quiet',
            '--no-warnings',
            '--dump-json',
            '--source-address', '0.0.0.0', # Force IPv4
            video_url
        ]

        # Get video metadata
        info_process = subprocess.run(info_command, capture_output=True, text=True)
        if info_process.returncode != 0:
            raise subprocess.CalledProcessError(info_process.returncode, info_command, stderr=info_process.stderr)
        
        video_info = json.loads(info_process.stdout)
        video_title = video_info.get("title", "video")

        # Command to download the video to stdout
        download_command = [
            sys.executable, # Use the current python interpreter
            '-m', 'yt_dlp',
            '--quiet',
            '--no-warnings',
            '--format', 'best[ext=mp4]/best',
            '--source-address', '0.0.0.0', # Force IPv4
            '-o', '-',  # Output to stdout
            video_url
        ]

        progress_store[download_id] = {"status": "downloading", "percent": 50} # Placeholder progress

        # Download the video
        download_process = subprocess.run(download_command, capture_output=True)
        if download_process.returncode != 0:
            raise subprocess.CalledProcessError(download_process.returncode, download_command, stderr=download_process.stderr)

        video_buffer = io.BytesIO(download_process.stdout)
        video_buffer.seek(0)

        progress_store[download_id] = {"status": "finished", "percent": 100}

        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype="video/mp4"
        )

    except subprocess.CalledProcessError as e:
        progress_store.pop(download_id, None)
        error_message = "The requested video is unavailable. It may be private, deleted, or region-restricted."
        # Log the actual error from yt-dlp for debugging
        print(f"yt-dlp error: {e.stderr}")
        return jsonify({"success": False, "error": error_message}), 500
    except Exception as e:
        progress_store.pop(download_id, None)
        traceback.print_exc()
        return jsonify({"success": False, "error": "An internal server error occurred."}), 500

@app.route("/progress")
def get_progress():
    download_id = "download"
    progress = progress_store.get(download_id, {"status": "idle", "percent": 0})
    return jsonify(progress)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
