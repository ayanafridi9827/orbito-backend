from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
from pytube import YouTube
import uuid
import re
import io
import traceback

app = Flask(__name__)
CORS(app)

PROGRESS_FILE = "progress.json"

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")

    video_buffer = io.BytesIO()  # Memory buffer for video

    def progress_function(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percent = (bytes_downloaded / total_size) * 100
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(percent))

    try:
        with open(PROGRESS_FILE, "w") as f:
            f.write("0.0")

        yt = YouTube(video_url, on_progress_callback=progress_function)
        stream = yt.streams.get_highest_resolution()
        video_title = yt.title

        # Download to memory buffer
        stream.stream_to_buffer(video_buffer)
        video_buffer.seek(0)
        
        with open(PROGRESS_FILE, "w") as f:
            f.write("100.0")

        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype="video/mp4"
        )

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
