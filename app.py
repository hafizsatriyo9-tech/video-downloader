from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os

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

    if not url:
        return "URL kosong!"

    try:

        # ================= MP3 =================
        if format_type == "mp3":

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',

                'ffmpeg_location': '/usr/bin/ffmpeg',

                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],

                'quiet': True,
                'noplaylist': True,
                'geo_bypass': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=True)

                if info is None:
                    return "Download gagal"

                final_file = ydl.prepare_filename(info)
                final_file = final_file.rsplit(".", 1)[0] + ".mp3"


        # ================= MP4 (1080p) =================
        else:

            ydl_opts = {
                'format': '(bestvideo[height<=1080]/bestvideo)+bestaudio/best',

                'merge_output_format': 'mp4',

                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',

                'ffmpeg_location': '/usr/bin/ffmpeg',

                'quiet': True,
                'noplaylist': True,
                'geo_bypass': True,

                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=True)

                if info is None:
                    return "Download gagal"

                final_file = ydl.prepare_filename(info)
                final_file = final_file.rsplit(".", 1)[0] + ".mp4"


    except Exception as e:
        return f"Download error: {str(e)}"


    # ===============================
    # AUTO DELETE FILE
    # ===============================
    @after_this_request
    def remove_file(response):
        try:
            os.remove(final_file)
        except:
            pass
        return response


    return send_file(final_file, as_attachment=True)


# ===============================
# KEEP ALIVE (RAILWAY)
# ===============================
@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})


# ===============================
# LOCAL RUN
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
