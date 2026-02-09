from flask import Flask, render_template, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import re
import shutil

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIE_FILE = os.path.abspath("cookies.txt")

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

def has_cookies():
    return os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0

# ===============================
# BASE YT-DLP CONFIG (CLOUD SAFE)
# ===============================

BASE_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,

    # ✅ COOKIES (BENAR)
    "cookiefile": COOKIE_FILE if has_cookies() else None,

    # 🧠 Browser-like headers
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),

    "http_headers": {
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "DNT": "1"
    },

    # 🐢 Anti rate-limit
    "sleep_interval": 2,
    "max_sleep_interval": 5,

    "retries": 5,
    "fragment_retries": 5,
    "extractor_retries": 3,

    "concurrent_fragment_downloads": 1,
    "socket_timeout": 30,

    "nocheckcertificate": True,
}

# ===============================
# ROUTES
# ===============================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ping")
def ping():
    return jsonify({
        "status": "alive",
        "ffmpeg": has_ffmpeg(),
        "cookies": has_cookies()
    })

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    format_type = request.form.get("format", "mp4")

    if not url:
        return "URL kosong"

    try:
        # =====================
        # GET INFO
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
        # MP4 (DEFAULT 720p – PALING STABIL)
        # =====================
        else:
            if has_ffmpeg():
                ydl_opts = {
                    **BASE_YDL_OPTS,
                    "format": "bv*[height<=720]+ba/b[height<=720]/best",
                    "merge_output_format": "mp4",
                    "outtmpl": base_path + ".%(ext)s",
                }
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
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception:
            # 🔁 FALLBACK
            ydl_opts["format"] = "best"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        if not os.path.exists(final_file):
            return "File gagal dibuat"

        # =====================
        # AUTO DELETE
        # =====================
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_file):
                    os.remove(final_file)
            except:
                pass
            return response

        return send_file(final_file, as_attachment=True)

    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        if "login" in msg.lower():
            return "Platform meminta login. Pastikan cookies.txt valid."
        return f"Download error: {msg}"

    except Exception as e:
        return f"Download error: {str(e)}"
