from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


# =========================
# CLEAN FILENAME (SnapTik Style Safe)
# =========================

def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)   # remove windows illegal chars
    name = re.sub(r'[^\w\s.-]', '', name)      # remove emoji & symbols
    name = name.replace(" ", "_")
    return name.strip()


# =========================
# GET FINAL FILE AUTO
# =========================

def get_latest_file(folder):
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    files = [f for f in files if os.path.isfile(f)]
    return max(files, key=os.path.getctime)


# =========================
# HOME
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# DOWNLOAD ROUTE
# =========================

@app.route("/download", methods=["POST"])
def download():

    url = request.form.get("url")
    filetype = request.form.get("type", "mp4")  # mp4 or mp3

    if not url:
        return jsonify({"error": "URL kosong"}), 400

    uid = str(uuid.uuid4())

    base_path = f"{DOWNLOAD_DIR}/{uid}"

    try:

        # =========================
        # MP4 VIDEO
        # =========================

        if filetype == "mp4":

            ydl_opts = {
                'format': '(bestvideo[height<=1080]/bestvideo)+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': base_path + '.%(ext)s',
                'noplaylist': True,
                'quiet': True,
                'geo_bypass': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0'
                }
            }

        # =========================
        # MP3 AUDIO
        # =========================

        else:

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': base_path + '.%(ext)s',
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

        # =========================
        # DOWNLOAD PROCESS
        # =========================

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get("title", "video")
        safe_title = clean_filename(title)

        final_file = get_latest_file(DOWNLOAD_DIR)

        new_path = f"{DOWNLOAD_DIR}/{safe_title}.{final_file.split('.')[-1]}"

        os.rename(final_file, new_path)

        return send_file(new_path, as_attachment=True)


    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# RUN LOCAL
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
