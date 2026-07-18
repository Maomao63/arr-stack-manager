import json
import os
import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"))
CONFIG_FILE = "/config/config.json"

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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=env.get_template("index.html").render())

@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    return HTMLResponse(content=env.get_template("settings.html").render(load_config()))

@app.get("/sonarr-data", response_class=HTMLResponse)
async def sonarr_data():
    c = load_config()
    series_a = fetch_api(c["sonarr_a_url"], c["sonarr_a_api"], "series")
    series_b = fetch_api(c["sonarr_b_url"], c["sonarr_b_api"], "series")
    if not series_a or not series_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Keine Verbindung zu Sonarr. Einstellungen prüfen.</div>")

    tvdb_b = {s.get("tvdbId") for s in series_b}
    duplicates = []
    for s in series_a:
        if s.get("tvdbId") in tvdb_b:
            stats = s.get("statistics", {})
            seasons, ep_total, ep_file = stats.get("seasonCount", 0), stats.get("totalEpisodeCount", 0), stats.get("episodeFileCount", 0)
            status = "Keine Episoden" if ep_total == 0 else f"{seasons} Staffeln | Komplett ({ep_file}/{ep_total})" if ep_file == ep_total else f"{seasons} Staffeln | Unvollständig ({ep_total - ep_file} fehlen)"
            duplicates.append({"id": s["id"], "title": s["title"], "status": status, "complete": ep_file == ep_total and ep_total > 0})
            
    return HTMLResponse(content=env.get_template("sonarr.html").render(duplicates=duplicates))

@app.get("/radarr-data", response_class=HTMLResponse)
async def radarr_data():
    c = load_config()
    movies_a = fetch_api(c["radarr_a_url"], c["radarr_a_api"], "movie")
    movies_b = fetch_api(c["radarr_b_url"], c["radarr_b_api"], "movie")
    if not movies_a or not movies_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Keine Verbindung zu Radarr. Einstellungen prüfen.</div>")

    tmdb_b = {m.get("tmdbId") for m in movies_b}
    duplicates = []
    for m in movies_a:
        if m.get("tmdbId") in tmdb_b:
            status = "Film vorhanden" if m.get("hasFile") else "Keine Datei vorhanden"
            duplicates.append({"id": m["id"], "title": m["title"], "status": status, "complete": m.get("hasFile")})
            
    return HTMLResponse(content=env.get_template("radarr.html").render(duplicates=duplicates))

@app.delete("/delete/{app_type}/{item_id}", response_class=HTMLResponse)
async def delete_item(app_type: str, item_id: int):
    c = load_config()
    url, api, endpoint = (c["sonarr_a_url"], c["sonarr_a_api"], "series") if app_type == "sonarr" else (c["radarr_a_url"], c["radarr_a_api"], "movie")
    if delete_api(url, api, endpoint, item_id):
        return HTMLResponse("<div class='text-green-400 font-bold bg-green-500/10 px-4 py-2 rounded-xl border border-green-500/20'>Erfolgreich von Instanz A gelöscht!</div>")
    return HTMLResponse("<div class='text-red-400 font-bold bg-red-500/10 px-4 py-2 rounded-xl border border-red-500/20'>Fehler beim Löschen</div>")

@app.post("/save-config")
async def save_config(sonarr_a_url: str=Form(""), sonarr_a_api: str=Form(""), sonarr_b_url: str=Form(""), sonarr_b_api: str=Form(""), radarr_a_url: str=Form(""), radarr_a_api: str=Form(""), radarr_b_url: str=Form(""), radarr_b_api: str=Form("")):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"sonarr_a_url": sonarr_a_url, "sonarr_a_api": sonarr_a_api, "sonarr_b_url": sonarr_b_url, "sonarr_b_api": sonarr_b_api, "radarr_a_url": radarr_a_url, "radarr_a_api": radarr_a_api, "radarr_b_url": radarr_b_url, "radarr_b_api": radarr_b_api}, f)
    return RedirectResponse(url="/", status_code=303)
