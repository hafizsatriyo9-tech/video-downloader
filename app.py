from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===============================
# HOME
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

# ===============================
# DOWNLOAD ROUTE
# ===============================
@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    format_type = request.form["format"]

    filename = str(uuid.uuid4())

    if format_type == "mp3":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        final_file = f"{DOWNLOAD_DIR}/{filename}.mp3"
    else:
        ydl_opts = {
            'format': 'best[filesize<50M]',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'quiet': True 
            'noplaylist': True,
            'geo_bypass': True,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get("ext")
            final_file = f"{DOWNLOAD_DIR}/{filename}.{ext}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    # AUTO DELETE AFTER DOWNLOAD
    @after_this_request
    def remove_file(response):
        try:
            os.remove(final_file)
        except:
            pass
        return response

    return send_file(final_file, as_attachment=True)

# ===============================
# KEEP ALIVE (ANTI SLEEP)
# ===============================
@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
