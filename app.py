from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import uuid

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
# DOWNLOAD
# ===============================
@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url")
    format_type = request.form.get("format")

    filename = str(uuid.uuid4())

    if not url:
        return "URL kosong", 400

    if format_type == "mp3":

        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

        final_file = f"{DOWNLOAD_DIR}/{filename}.mp3"

    else:

        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if not info:
            return "Gagal mengambil video", 500

        if format_type != "mp3":
            ext = info.get("ext", "mp4")
            final_file = f"{DOWNLOAD_DIR}/{filename}.{ext}"

    except Exception as e:
        return f"Download error: {str(e)}", 500

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
# KEEP ALIVE
# ===============================
@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
