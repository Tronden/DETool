import threading
import webbrowser
import sys
import os
import time
import json
from flask import Flask, send_from_directory, request
import pystray
from PIL import Image, ImageDraw

app = Flask(__name__, static_folder='static', template_folder='static')

# Serve the UI
@app.route('/')
def root():
    # Launch profile selection page.
    return send_from_directory('static', 'profile.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server = request.environ.get('werkzeug.server.shutdown')
    if shutdown_server is None:
        return 'Not running with the Werkzeug Server', 500
    shutdown_server()
    return 'Server shutting down...'

# REST endpoints for Tag Options (shared across profiles)
def get_appdata_dir():
    return os.path.join(os.environ.get("APPDATA", "."), "DETool")

def get_tag_settings_path():
    appdata_dir = get_appdata_dir()
    os.makedirs(appdata_dir, exist_ok=True)
    return os.path.join(appdata_dir, "TagSettings.json")

@app.route('/api/tagsettings', methods=['GET', 'POST'])
def tagsettings():
    path = get_tag_settings_path()
    if request.method == 'GET':
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return data, 200
        else:
            return {}, 200
    else:
        data = request.get_json()
        with open(path, "w") as f:
            json.dump(data, f)
        return {"status": "ok"}, 200

# --- Server threading functions ---
server_thread = None

def run_flask():
    # Run on port 80 so that the user sees "http://DETool.APP" (after mapping DETool.APP to 127.0.0.1)
    app.run(port=80, threaded=True)

def start_server():
    global server_thread
    server_thread = threading.Thread(target=run_flask, daemon=True)
    server_thread.start()

def restart_server():
    try:
        import requests
        requests.post("http://localhost/shutdown")
    except Exception as e:
        print("Error shutting down server:", e)
    time.sleep(1)
    start_server()

# --- System Tray Icon ---
def create_image():
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        return Image.open(icon_path)
    image = Image.new('RGB', (64, 64), (0, 0, 0))
    d = ImageDraw.Draw(image)
    d.ellipse((0, 0, 64, 64), fill=(0, 123, 255))
    return image

def on_open(icon, item):
    # Open custom URL. Ensure your hosts file maps DETool.APP to 127.0.0.1.
    webbrowser.open("http://DETool.APP")

def on_restart(icon, item):
    restart_server()

def on_exit(icon, item):
    try:
        import requests
        requests.post("http://localhost/shutdown")
    except Exception as e:
        print("Error shutting down server:", e)
    icon.stop()
    sys.exit()

def setup_tray():
    image = create_image()
    menu = pystray.Menu(
        pystray.MenuItem("Open DETool.APP", on_open),
        pystray.MenuItem("Restart Server", on_restart),
        pystray.MenuItem("Close Server", on_exit)
    )
    tray_icon = pystray.Icon("DETool", image, "DETool.APP", menu)
    tray_icon.run()

if __name__ == '__main__':
    start_server()
    tray_thread = threading.Thread(target=setup_tray, daemon=True)
    tray_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit()