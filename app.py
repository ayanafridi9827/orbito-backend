from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
import yt_dlp
import uuid
import re
import io
import traceback

app = Flask(__name__)
CORS(app)

PROGRESS_FILE = "progress.json"
ANSI_ESCAPE = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")

    video_buffer = io.BytesIO()  # Memory buffer for video

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
            'source_address': '0.0.0.0'  # Force IPv4 to potentially avoid IP blocks
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get("title", "video")

        # Read video into memory
        with open(temp_filename, "rb") as f:
            video_buffer.write(f.read())
        video_buffer.seek(0)

        @after_this_request
        def remove_file(response):
            import os
            try:
                os.remove(temp_filename)
            except Exception as e:
                print(f"File delete failed: {e}")
            return response

        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype="video/mp4"
        )

    except yt_dlp.utils.DownloadError:
        with open(PROGRESS_FILE, "w") as f:
            f.write("0.0")
        error_message = "The requested video is unavailable. It may be private, deleted, or region-restricted."
        return jsonify({"success": False, "error": error_message}), 500
    except Exception as e:
        with open(PROGRESS_FILE, "w") as f:
            f.write("0.0")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


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
