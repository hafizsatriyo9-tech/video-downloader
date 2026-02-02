from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import re
import shutil

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIE_FILE = "cookies.txt"

# ===============================
# UTIL SAFE FILENAME
# ===============================

def clean_filename(name):
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:120]


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


# ===============================
# ROUTES
# ===============================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})


@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url")
    format_type = request.form.get("format")

    if not url:
        return "URL kosong"

    try:

        # =====================
        # GET VIDEO INFO FIRST
        # =====================

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            return "Video tidak tersedia"

        title = info.get("title", "video")
        safe_title = clean_filename(title)

        base_path = os.path.join(DOWNLOAD_DIR, safe_title)

        final_file = None

        # =====================
        # MP3 MODE
        # =====================

        if format_type == "mp3":

            if not has_ffmpeg():
                return "Server tidak punya ffmpeg. MP3 tidak tersedia."

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': base_path + '.%(ext)s',
                'cookies': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
                'quiet': True,
                'geo_bypass': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

            final_file = base_path + ".mp3"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # =====================
        # MP4 MODE 1080P
        # =====================

        else:

            # Kalau ffmpeg ada → bisa merge 1080p
            if has_ffmpeg():

                format_string = "(bestvideo[height<=1080]/bestvideo)+bestaudio/best"

                ydl_opts = {
                    'format': format_string,
                    'merge_output_format': 'mp4',
                    'outtmpl': base_path + '.%(ext)s',
                    'cookies': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                    'noplaylist': True,
                    'quiet': True,
                    'geo_bypass': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0'
                    }
                }

                final_file = base_path + ".mp4"

            # Kalau ffmpeg TIDAK ada → pakai single file
            else:

                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'outtmpl': base_path + '.%(ext)s',
                    'cookies': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
                    'noplaylist': True,
                    'quiet': True,
                    'geo_bypass': True,
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0'
                    }
                }

                final_file = base_path + ".mp4"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # =====================
        # AUTO DELETE AFTER SEND
        # =====================

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_file):
                    os.remove(final_file)
            except:
                pass
            return response

        if not os.path.exists(final_file):
            return "File gagal dibuat"

        return send_file(final_file, as_attachment=True)

    except Exception as e:
        return f"Download error: {str(e)}"


# ===============================
# RUN LOCAL
# ===============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
