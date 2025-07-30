from flask import Flask, request, jsonify
from yt_dlp import YoutubeDL

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        ydl_opts = {
            'quiet': True,               # No console output
            'no_warnings': True,         # Suppress warnings
            'outtmpl': 'downloads/%(title)s.%(ext)s',  # Output path
            'format': 'best',
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        return jsonify({
            "message": "Video downloaded successfully",
            "title": info.get("title"),
            "filename": ydl.prepare_filename(info)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
