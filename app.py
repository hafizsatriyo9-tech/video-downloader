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
# UTIL
# ===============================

def clean_filename(name):
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name[:120]


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


# ===============================
# BASE YT-DLP CONFIG (FIXED)
# ===============================

BASE_YDL_OPTS = {
    "quiet": True,
    "noplaylist": True,
    "geo_bypass": True,
    "cookies": COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    },
    "js_runtimes": {
        "node": {}   # ✅ FORMAT BENAR (DICT)
    }
}

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
        # GET VIDEO INFO
        # =====================
        with yt_dlp.YoutubeDL(BASE_YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return "Video tidak tersedia"

        title = info.get("title", "video")
        safe_title = clean_filename(title)
        base_path = os.path.join(DOWNLOAD_DIR, safe_title)

        final_file = None

        # =====================
        # MP3
        # =====================
        if format_type == "mp3":

            if not has_ffmpeg():
                return "Server tidak memiliki ffmpeg"

            ydl_opts = {
                **BASE_YDL_OPTS,
                "format": "bestaudio/best",
                "outtmpl": base_path + ".%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }

            final_file = base_path + ".mp3"

        # =====================
        # MP4 HD 1080p
        # =====================
        else:

            if has_ffmpeg():
                ydl_opts = {
                    **BASE_YDL_OPTS,
                    "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best",
                    "merge_output_format": "mp4",
                    "outtmpl": base_path + ".%(ext)s",
                }
                final_file = base_path + ".mp4"
            else:
                ydl_opts = {
                    **BASE_YDL_OPTS,
                    "format": "best[ext=mp4]/best",
                    "outtmpl": base_path + ".%(ext)s",
                }
                final_file = base_path + ".mp4"

        # =====================
        # DOWNLOAD
        # =====================
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
