from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
import yt_dlp
import uuid
import re
import io
import traceback
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PROGRESS_FILE = "progress.json"
ANSI_ESCAPE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%')
            clean_percent_str = ANSI_ESCAPE.sub('', percent_str).strip().replace('%', '')
            try:
                percent = float(clean_percent_str)
            except ValueError:
                percent = 0.0
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(percent))
        elif d['status'] == 'finished':
            with open(PROGRESS_FILE, "w") as f:
                f.write("100.0")

    try:
        with open(PROGRESS_FILE, "w") as f:
            f.write("0.0")

        # Temporary file name
        temp_filename = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            'outtmpl': temp_filename,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'noplaylist': True,
            'ignoreerrors': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
                info = ydl.extract_info(video_url, download=False)
                video_title = info.get("title", "video")
            except yt_dlp.utils.DownloadError as de:
                return jsonify({
                    "success": False,
                    "error": "This video is unavailable or restricted.",
                    "details": str(de)
                }), 400

        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_filename)
            except Exception as e:
                print(f"File delete failed: {e}")
            return response

        return send_file(
            temp_filename,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        with open(PROGRESS_FILE, "w") as f:
            f.write("0.0")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Unexpected error occurred.",
            "details": str(e)
        }), 500


@app.route("/progress")
def get_progress():
    try:
        with open(PROGRESS_FILE, "r") as f:
            percent = float(f.read())
        return jsonify({"percent": percent})
    except:
        return jsonify({"percent": 0.0})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
