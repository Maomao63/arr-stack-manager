import json
import os
import requests
from datetime import datetime
from urllib.parse import quote
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"))
CONFIG_DIR = os.environ.get("CONFIG_DIR", "/config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

def load_config():
    default = {
        "sonarr_a_url": "", "sonarr_a_api": "", "sonarr_b_url": "", "sonarr_b_api": "",
        "radarr_a_url": "", "radarr_a_api": "", "radarr_b_url": "", "radarr_b_api": ""
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                default.update(json.load(f))
        except: pass
    return default

def fetch_api(url, api_key, endpoint):
    if not url or not api_key: return []
    try:
        r = requests.get(f"{url.rstrip('/')}/api/v3/{endpoint}", headers={"X-Api-Key": api_key}, timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def delete_api(url, api_key, endpoint, item_id):
    try:
        r = requests.delete(f"{url.rstrip('/')}/api/v3/{endpoint}/{item_id}?deleteFiles=true", headers={"X-Api-Key": api_key}, timeout=10)
        return r.status_code == 200
    except: return False

def log_history(app_type, title):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except: pass
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    history.insert(0, {"time": timestamp, "app": app_type.capitalize(), "title": title})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:100], f) # Keep only the latest 100 entries

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=env.get_template("index.html").render())

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    return HTMLResponse(content=env.get_template("settings.html").render(load_config()))

@app.get("/history", response_class=HTMLResponse)
async def history_page():
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except: pass
    return HTMLResponse(content=env.get_template("history.html").render(history=history))

@app.get("/sonarr-data", response_class=HTMLResponse)
async def sonarr_data():
    c = load_config()
    series_a = fetch_api(c["sonarr_a_url"], c["sonarr_a_api"], "series")
    series_b = fetch_api(c["sonarr_b_url"], c["sonarr_b_api"], "series")
    if not series_a or not series_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Unable to connect to Sonarr. Check your settings.</div>")

    dict_b = {s.get("tvdbId"): s for s in series_b if s.get("tvdbId")}
    duplicates = []
    
    for s in series_a:
        tvdb = s.get("tvdbId")
        if tvdb in dict_b:
            stats_a = s.get("statistics", {})
            ep_file_a = stats_a.get("episodeFileCount", 0)
            
            # Hide series that do not have any downloaded episodes.
            if ep_file_a == 0:
                continue 
                
            ep_total_a = stats_a.get("totalEpisodeCount", 0)
            
            stats_b = dict_b[tvdb].get("statistics", {})
            ep_file_b = stats_b.get("episodeFileCount", 0)
            ep_total_b = stats_b.get("totalEpisodeCount", 0)
            
            status = f"Instance A: {ep_file_a}/{ep_total_a} episodes | Instance B: {ep_file_b}/{ep_total_b} episodes"
            safe_title = quote(s["title"])
            
            duplicates.append({"id": s["id"], "title": s["title"], "status": status, "complete": ep_file_a == ep_total_a, "safe_title": safe_title})
            
    return HTMLResponse(content=env.get_template("sonarr.html").render(duplicates=duplicates))

@app.get("/radarr-data", response_class=HTMLResponse)
async def radarr_data():
    c = load_config()
    movies_a = fetch_api(c["radarr_a_url"], c["radarr_a_api"], "movie")
    movies_b = fetch_api(c["radarr_b_url"], c["radarr_b_api"], "movie")
    if not movies_a or not movies_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Unable to connect to Radarr. Check your settings.</div>")

    dict_b = {m.get("tmdbId"): m for m in movies_b if m.get("tmdbId")}
    duplicates = []
    
    for m in movies_a:
        tmdb = m.get("tmdbId")
        if tmdb in dict_b:
            # Hide movies that do not have a file yet.
            if not m.get("hasFile"):
                continue
                
            has_file_b = dict_b[tmdb].get("hasFile")
            b_status = "Available" if has_file_b else "Missing"
            status = f"Instance A: Available | Instance B: {b_status}"
            safe_title = quote(m["title"])
            
            duplicates.append({"id": m["id"], "title": m["title"], "status": status, "complete": True, "safe_title": safe_title})
            
    return HTMLResponse(content=env.get_template("radarr.html").render(duplicates=duplicates))

@app.delete("/delete/{app_type}/{item_id}", response_class=HTMLResponse)
async def delete_item(app_type: str, item_id: int, title: str = "Unknown"):
    c = load_config()
    url, api, endpoint = (c["sonarr_a_url"], c["sonarr_a_api"], "series") if app_type == "sonarr" else (c["radarr_a_url"], c["radarr_a_api"], "movie")
    if delete_api(url, api, endpoint, item_id):
        log_history(app_type, title)
        return HTMLResponse(f"<div class='text-green-400 font-bold bg-green-500/10 px-4 py-2 rounded-xl border border-green-500/20'>Successfully deleted: {title}</div>")
    return HTMLResponse("<div class='text-red-400 font-bold bg-red-500/10 px-4 py-2 rounded-xl border border-red-500/20'>Failed to delete item</div>")

@app.post("/save-config")
async def save_config(sonarr_a_url: str=Form(""), sonarr_a_api: str=Form(""), sonarr_b_url: str=Form(""), sonarr_b_api: str=Form(""), radarr_a_url: str=Form(""), radarr_a_api: str=Form(""), radarr_b_url: str=Form(""), radarr_b_api: str=Form("")):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"sonarr_a_url": sonarr_a_url, "sonarr_a_api": sonarr_a_api, "sonarr_b_url": sonarr_b_url, "sonarr_b_api": sonarr_b_api, "radarr_a_url": radarr_a_url, "radarr_a_api": radarr_a_api, "radarr_b_url": radarr_b_url, "radarr_b_api": radarr_b_api}, f)
    return RedirectResponse(url="/", status_code=303)
