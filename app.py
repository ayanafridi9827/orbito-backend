from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import uuid
import os
import subprocess

app = Flask(__name__)
CORS(app)

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")

    try:
        filename = f"{uuid.uuid4()}.mp4"
        filepath = f"/tmp/{filename}"  # Render uses /tmp for temp files

        # yt-dlp download command
        cmd = ["yt-dlp", "-f", "best", "-o", filepath, video_url]

        subprocess.run(cmd, check=True)

        return send_file(
            filepath,
            as_attachment=True,
            download_name="video.mp4",
            mimetype="video/mp4"
        )

    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": "Video download failed."}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/")
def home():
    return "YouTube/Instagram Downloader API"

if __name__ == "__main__":
    app.run(debug=True)
