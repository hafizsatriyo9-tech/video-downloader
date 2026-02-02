from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

progress_data = {}

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/progress/<task_id>")
def progress(task_id):
    return jsonify(progress_data.get(task_id, {"progress": 0}))


@app.route("/download", methods=["POST"])
def download():

    url = request.form["url"]
    format_type = request.form["format"]

    task_id = str(uuid.uuid4())
    filename = str(uuid.uuid4())

    progress_data[task_id] = {"progress": 0}

    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0').replace('%', '').strip()
            try:
                progress_data[task_id]["progress"] = float(percent)
            except:
                pass

        if d['status'] == 'finished':
            progress_data[task_id]["progress"] = 100

    if format_type == "mp3":

        ydl_opts = {
            'format': 'ba/best',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [hook],
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        final_file = f"{DOWNLOAD_DIR}/{filename}.mp3"

    else:

        ydl_opts = {
            'format': 'bv*+ba/best',
            'merge_output_format': 'mp4',
            'outtmpl': f'{DOWNLOAD_DIR}/{filename}.%(ext)s',
            'progress_hooks': [hook],
            'quiet': True,
            'noplaylist': True,
            'ignoreerrors': True,
            'geo_bypass': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        final_file = f"{DOWNLOAD_DIR}/{filename}.mp4"

    def run_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except:
            progress_data[task_id]["progress"] = -1

    thread = threading.Thread(target=run_download)
    thread.start()

    return jsonify({
        "task_id": task_id,
        "file": final_file
    })


@app.route("/getfile")
def get_file():
    path = request.args.get("path")

    def remove_file():
        time.sleep(5)
        try:
            os.remove(path)
        except:
            pass

    threading.Thread(target=remove_file).start()

    return send_file(path, as_attachment=True)


@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
