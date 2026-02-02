from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url")
    format_type = request.form.get("format")

    filename = str(uuid.uuid4())

    try:

        # ================= MP3 =================
        if format_type == "mp3":

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
                'ffmpeg_location': '/usr/bin/ffmpeg',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'noplaylist': True,
                'geo_bypass': True,
            }

            final_file = f"{DOWNLOAD_DIR}/{filename}.mp3"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)


        # ================= MP4 =================
        else:

            ydl_opts = {
                'format': 'best[filesize<50M]/best',
                'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
                'quiet': True,
                'noplaylist': True,
                'geo_bypass': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    return "Download failed: video not available or blocked"

                ext = info.get("ext", "mp4")
                final_file = f"{DOWNLOAD_DIR}/{filename}.{ext}"


    except Exception as e:
        return f"Download error: {str(e)}"


    @after_this_request
    def remove_file(response):
        try:
            os.remove(final_file)
        except:
            pass
        return response


    return send_file(final_file, as_attachment=True)


@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
