from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import io
import traceback

app = Flask(__name__)
CORS(app)

# Use a dictionary to store progress for multiple downloads if necessary
progress_store = {}

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")
    # A unique ID for the download request
    download_id = "download" 

    video_buffer = io.BytesIO()

    def progress_hook(d):
        if d['status'] == 'downloading':
            # Extract percentage and update the progress store
            percent_str = d.get('_percent_str', '0%')
            # Clean up the string
            percent_str = ''.join(filter(str.isdigit, percent_str))
            try:
                percent = float(percent_str)
                progress_store[download_id] = percent
            except ValueError:
                pass # Ignore if conversion fails
        elif d['status'] == 'finished':
            progress_store[download_id] = 100.0

    try:
        progress_store[download_id] = 0.0

        ydl_opts = {
            # Force IPv4 to avoid YouTube IP blocks on servers
            'source_address': '0.0.0.0',
            'format': 'best[ext=mp4]/best',
            'outtmpl': '-', # Output to stdout
            'logtostderr': True,
            'quiet': True,
            'progress_hooks': [progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get("title", "video")
            
            # Download to stdout and write to our buffer
            download_stream = ydl.extract_info(video_url, download=True)
            video_buffer.write(download_stream)
            video_buffer.seek(0)

        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=f"{video_title}.mp4",
            mimetype="video/mp4"
        )

    except yt_dlp.utils.DownloadError as e:
        progress_store.pop(download_id, None)
        error_message = "The requested video is unavailable. It may be private, deleted, or region-restricted."
        return jsonify({"success": False, "error": error_message}), 500
    except Exception as e:
        progress_store.pop(download_id, None)
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/progress")
def get_progress():
    download_id = "download"
    percent = progress_store.get(download_id, 0.0)
    return jsonify({"percent": percent})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)