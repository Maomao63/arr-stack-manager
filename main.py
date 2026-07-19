import asyncio
import html
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from urllib.parse import quote, urlparse

import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape


logger = logging.getLogger("arr-stack-manager")

CONFIG_DIR = os.environ.get("CONFIG_DIR", "/config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")
NOTIFICATION_STATE_FILE = os.path.join(CONFIG_DIR, "notification_state.json")

DEFAULT_CONFIG = {
    "sonarr_enabled": True,
    "sonarr_a_url": "",
    "sonarr_a_api": "",
    "sonarr_b_url": "",
    "sonarr_b_api": "",
    "radarr_enabled": True,
    "radarr_a_url": "",
    "radarr_a_api": "",
    "radarr_b_url": "",
    "radarr_b_api": "",
    "discord_enabled": False,
    "discord_webhook": "",
    "discord_frequency": "daily",
    "discord_time": "09:00",
    "discord_weekday": "0",
    "discord_monthday": "1",
}

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def load_json(path, default):
    if not os.path.exists(path):
        return default.copy() if isinstance(default, dict) else default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        logger.warning("Unable to read %s: %s", path, error)
        return default.copy() if isinstance(default, dict) else default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary_path = f"{path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    os.replace(temporary_path, path)


def load_config():
    config = DEFAULT_CONFIG.copy()
    stored_config = load_json(CONFIG_FILE, {})
    if isinstance(stored_config, dict):
        config.update(stored_config)
    return config


def build_config_from_form(form):
    frequency = str(form.get("discord_frequency", "daily"))
    if frequency not in {"daily", "weekly", "monthly"}:
        frequency = "daily"

    schedule_time = str(form.get("discord_time", "09:00"))
    try:
        datetime.strptime(schedule_time, "%H:%M")
    except ValueError:
        schedule_time = "09:00"

    try:
        weekday = str(min(6, max(0, int(form.get("discord_weekday", 0)))))
    except (TypeError, ValueError):
        weekday = "0"

    try:
        monthday = str(min(28, max(1, int(form.get("discord_monthday", 1)))))
    except (TypeError, ValueError):
        monthday = "1"

    return {
        "sonarr_enabled": form.get("sonarr_enabled") == "true",
        "sonarr_a_url": str(form.get("sonarr_a_url", "")).strip(),
        "sonarr_a_api": str(form.get("sonarr_a_api", "")).strip(),
        "sonarr_b_url": str(form.get("sonarr_b_url", "")).strip(),
        "sonarr_b_api": str(form.get("sonarr_b_api", "")).strip(),
        "radarr_enabled": form.get("radarr_enabled") == "true",
        "radarr_a_url": str(form.get("radarr_a_url", "")).strip(),
        "radarr_a_api": str(form.get("radarr_a_api", "")).strip(),
        "radarr_b_url": str(form.get("radarr_b_url", "")).strip(),
        "radarr_b_api": str(form.get("radarr_b_api", "")).strip(),
        "discord_enabled": form.get("discord_enabled") == "true",
        "discord_webhook": str(form.get("discord_webhook", "")).strip(),
        "discord_frequency": frequency,
        "discord_time": schedule_time,
        "discord_weekday": weekday,
        "discord_monthday": monthday,
    }


def fetch_api(url, api_key, endpoint):
    if not url or not api_key:
        return []
    try:
        response = requests.get(
            f"{url.rstrip('/')}/api/v3/{endpoint}",
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        return response.json() if response.status_code == 200 else []
    except requests.RequestException:
        return []


def fetch_api_for_report(url, api_key, endpoint):
    if not url or not api_key:
        raise ValueError("not configured")
    response = requests.get(
        f"{url.rstrip('/')}/api/v3/{endpoint}",
        headers={"X-Api-Key": api_key},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("unexpected API response")
    return data


def test_arr_connection(url, api_key):
    if not url or not api_key:
        return False
    try:
        response = requests.get(
            f"{url.rstrip('/')}/api/v3/system/status",
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def delete_api(url, api_key, endpoint, item_id):
    try:
        response = requests.delete(
            f"{url.rstrip('/')}/api/v3/{endpoint}/{item_id}?deleteFiles=true",
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def log_history(app_type, title):
    history = load_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    history.insert(0, {"time": timestamp, "app": app_type.capitalize(), "title": title})
    save_json(HISTORY_FILE, history[:100])


def is_valid_discord_webhook(webhook_url):
    try:
        parsed = urlparse(webhook_url)
    except ValueError:
        return False
    hostname = (parsed.hostname or "").lower()
    valid_host = (
        hostname in {"discord.com", "discordapp.com"}
        or hostname.endswith(".discord.com")
        or hostname.endswith(".discordapp.com")
    )
    return parsed.scheme == "https" and valid_host and parsed.path.startswith("/api/webhooks/")


def get_sonarr_duplicate_titles(config):
    if not config.get("sonarr_enabled", True):
        return None
    required = (
        config["sonarr_a_url"],
        config["sonarr_a_api"],
        config["sonarr_b_url"],
        config["sonarr_b_api"],
    )
    if not all(required):
        return None
    series_a = fetch_api_for_report(config["sonarr_a_url"], config["sonarr_a_api"], "series")
    series_b = fetch_api_for_report(config["sonarr_b_url"], config["sonarr_b_api"], "series")
    ids_b = {series.get("tvdbId") for series in series_b if series.get("tvdbId")}
    titles = [
        series.get("title", "Unknown series")
        for series in series_a
        if series.get("tvdbId") in ids_b
        and series.get("statistics", {}).get("episodeFileCount", 0) > 0
    ]
    return sorted(titles, key=str.casefold)


def get_radarr_duplicate_titles(config):
    if not config.get("radarr_enabled", True):
        return None
    required = (
        config["radarr_a_url"],
        config["radarr_a_api"],
        config["radarr_b_url"],
        config["radarr_b_api"],
    )
    if not all(required):
        return None
    movies_a = fetch_api_for_report(config["radarr_a_url"], config["radarr_a_api"], "movie")
    movies_b = fetch_api_for_report(config["radarr_b_url"], config["radarr_b_api"], "movie")
    ids_b = {movie.get("tmdbId") for movie in movies_b if movie.get("tmdbId")}
    titles = [
        movie.get("title", "Unknown movie")
        for movie in movies_a
        if movie.get("tmdbId") in ids_b and movie.get("hasFile")
    ]
    return sorted(titles, key=str.casefold)


def format_report_section(label, titles):
    if titles is None:
        return [f"**{label}:** Not configured"]
    if not titles:
        return [f"**{label}:** No duplicates found ✅"]
    return [f"**{label}:** {len(titles)} duplicate(s) found ⚠️"] + [
        f"- {title}" for title in titles
    ]


def create_duplicate_report(config):
    lines = [
        "**Arr Stack Manager duplicate report**",
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        "",
    ]
    if config.get("sonarr_enabled", True):
        try:
            lines.extend(format_report_section("Sonarr", get_sonarr_duplicate_titles(config)))
        except (requests.RequestException, ValueError) as error:
            lines.append(f"**Sonarr:** Check failed ({error})")
    if config.get("sonarr_enabled", True) and config.get("radarr_enabled", True):
        lines.append("")
    if config.get("radarr_enabled", True):
        try:
            lines.extend(format_report_section("Radarr", get_radarr_duplicate_titles(config)))
        except (requests.RequestException, ValueError) as error:
            lines.append(f"**Radarr:** Check failed ({error})")
    if not config.get("sonarr_enabled", True) and not config.get("radarr_enabled", True):
        lines.append("No applications are enabled.")
    return "\n".join(lines)


def split_discord_message(message, limit=1900):
    chunks = []
    current_lines = []
    current_length = 0
    for original_line in message.splitlines():
        line = original_line[:limit]
        additional_length = len(line) + (1 if current_lines else 0)
        if current_lines and current_length + additional_length > limit:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_length = 0
        current_lines.append(line)
        current_length += len(line) + (1 if current_length else 0)
    if current_lines:
        chunks.append("\n".join(current_lines))
    return chunks


def send_duplicate_report(config):
    webhook_url = config.get("discord_webhook", "")
    if not is_valid_discord_webhook(webhook_url):
        raise ValueError("Enter a valid Discord webhook URL")
    report = create_duplicate_report(config)
    for chunk in split_discord_message(report):
        try:
            response = requests.post(
                webhook_url,
                json={"content": chunk, "allowed_mentions": {"parse": []}},
                timeout=10,
            )
        except requests.RequestException as error:
            raise ValueError("Unable to reach the Discord webhook") from error
        if not 200 <= response.status_code < 300:
            raise ValueError(f"Discord rejected the webhook (HTTP {response.status_code})")


def current_schedule_key(config, now):
    if not config.get("discord_enabled") or not config.get("discord_webhook"):
        return None
    schedule_time = config.get("discord_time", "09:00")
    try:
        datetime.strptime(schedule_time, "%H:%M")
    except ValueError:
        return None
    if now.strftime("%H:%M") < schedule_time:
        return None

    frequency = config.get("discord_frequency", "daily")
    if frequency == "daily":
        return f"daily:{schedule_time}:{now.date().isoformat()}"
    if frequency == "weekly":
        weekday = int(config.get("discord_weekday", 0))
        if now.weekday() != weekday:
            return None
        iso_year, iso_week, _ = now.isocalendar()
        return f"weekly:{weekday}:{schedule_time}:{iso_year}-{iso_week}"
    if frequency == "monthly":
        monthday = int(config.get("discord_monthday", 1))
        if now.day != monthday:
            return None
        return f"monthly:{monthday}:{schedule_time}:{now:%Y-%m}"
    return None


async def notification_scheduler():
    while True:
        try:
            config = load_config()
            schedule_key = current_schedule_key(config, datetime.now())
            state = load_json(NOTIFICATION_STATE_FILE, {})
            if schedule_key and state.get("last_schedule_key") != schedule_key:
                result = "sent"
                try:
                    await asyncio.to_thread(send_duplicate_report, config)
                    logger.info("Scheduled Discord duplicate report sent")
                except (requests.RequestException, ValueError) as error:
                    result = str(error)
                    logger.error("Scheduled Discord report failed: %s", error)
                save_json(
                    NOTIFICATION_STATE_FILE,
                    {
                        "last_schedule_key": schedule_key,
                        "last_attempt": datetime.now().isoformat(timespec="seconds"),
                        "last_result": result,
                    },
                )
        except (OSError, TypeError, ValueError) as error:
            logger.error("Discord scheduler error: %s", error)
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(_app):
    scheduler_task = asyncio.create_task(notification_scheduler())
    try:
        yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=env.get_template("index.html").render(load_config()))


@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    return HTMLResponse(content=env.get_template("settings.html").render(load_config()))


@app.get("/history", response_class=HTMLResponse)
async def history_page():
    history = load_json(HISTORY_FILE, [])
    return HTMLResponse(content=env.get_template("history.html").render(history=history))


@app.get("/sonarr-data", response_class=HTMLResponse)
async def sonarr_data():
    config = load_config()
    if not config.get("sonarr_enabled", True):
        return HTMLResponse("<div class='text-slate-400'>Sonarr is disabled in Settings.</div>")
    series_a = fetch_api(config["sonarr_a_url"], config["sonarr_a_api"], "series")
    series_b = fetch_api(config["sonarr_b_url"], config["sonarr_b_api"], "series")
    if not series_a or not series_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Unable to connect to Sonarr. Check your settings.</div>")

    dict_b = {series.get("tvdbId"): series for series in series_b if series.get("tvdbId")}
    duplicates = []
    for series in series_a:
        tvdb_id = series.get("tvdbId")
        if tvdb_id not in dict_b:
            continue
        stats_a = series.get("statistics", {})
        episode_files_a = stats_a.get("episodeFileCount", 0)
        if episode_files_a == 0:
            continue
        total_episodes_a = stats_a.get("totalEpisodeCount", 0)
        stats_b = dict_b[tvdb_id].get("statistics", {})
        episode_files_b = stats_b.get("episodeFileCount", 0)
        total_episodes_b = stats_b.get("totalEpisodeCount", 0)
        status = (
            f"Instance A: {episode_files_a}/{total_episodes_a} episodes | "
            f"Instance B: {episode_files_b}/{total_episodes_b} episodes"
        )
        duplicates.append(
            {
                "id": series["id"],
                "title": series["title"],
                "status": status,
                "complete": episode_files_a == total_episodes_a,
                "safe_title": quote(series["title"]),
            }
        )
    return HTMLResponse(content=env.get_template("sonarr.html").render(duplicates=duplicates))


@app.get("/radarr-data", response_class=HTMLResponse)
async def radarr_data():
    config = load_config()
    if not config.get("radarr_enabled", True):
        return HTMLResponse("<div class='text-slate-400'>Radarr is disabled in Settings.</div>")
    movies_a = fetch_api(config["radarr_a_url"], config["radarr_a_api"], "movie")
    movies_b = fetch_api(config["radarr_b_url"], config["radarr_b_api"], "movie")
    if not movies_a or not movies_b:
        return HTMLResponse("<div class='text-red-400 bg-red-500/10 p-6 rounded-2xl border border-red-500/20'>Unable to connect to Radarr. Check your settings.</div>")

    dict_b = {movie.get("tmdbId"): movie for movie in movies_b if movie.get("tmdbId")}
    duplicates = []
    for movie in movies_a:
        tmdb_id = movie.get("tmdbId")
        if tmdb_id not in dict_b or not movie.get("hasFile"):
            continue
        status_b = "Available" if dict_b[tmdb_id].get("hasFile") else "Missing"
        duplicates.append(
            {
                "id": movie["id"],
                "title": movie["title"],
                "status": f"Instance A: Available | Instance B: {status_b}",
                "complete": True,
                "safe_title": quote(movie["title"]),
            }
        )
    return HTMLResponse(content=env.get_template("radarr.html").render(duplicates=duplicates))


@app.delete("/delete/{app_type}/{item_id}", response_class=HTMLResponse)
async def delete_item(app_type: str, item_id: int, title: str = "Unknown"):
    config = load_config()
    if app_type == "sonarr":
        if not config.get("sonarr_enabled", True):
            return HTMLResponse("<div class='text-red-400'>Sonarr is disabled in Settings.</div>", status_code=400)
        url, api_key, endpoint = config["sonarr_a_url"], config["sonarr_a_api"], "series"
    elif app_type == "radarr":
        if not config.get("radarr_enabled", True):
            return HTMLResponse("<div class='text-red-400'>Radarr is disabled in Settings.</div>", status_code=400)
        url, api_key, endpoint = config["radarr_a_url"], config["radarr_a_api"], "movie"
    else:
        return HTMLResponse("<div class='text-red-400'>Unsupported application</div>", status_code=400)
    if delete_api(url, api_key, endpoint, item_id):
        log_history(app_type, title)
        safe_title = html.escape(title)
        return HTMLResponse(f"<div class='text-green-400 font-bold bg-green-500/10 px-4 py-2 rounded-xl border border-green-500/20'>Successfully deleted: {safe_title}</div>")
    return HTMLResponse("<div class='text-red-400 font-bold bg-red-500/10 px-4 py-2 rounded-xl border border-red-500/20'>Failed to delete item</div>")


@app.post("/save-config")
async def save_config(request: Request):
    form = await request.form()
    save_json(CONFIG_FILE, build_config_from_form(form))
    return RedirectResponse(url="/", status_code=303)


@app.post("/test-discord", response_class=HTMLResponse)
async def test_discord(request: Request):
    form = await request.form()
    config = build_config_from_form(form)
    try:
        await asyncio.to_thread(send_duplicate_report, config)
    except (requests.RequestException, ValueError) as error:
        return HTMLResponse(
            f"<div class='text-red-400 font-semibold'>Discord test failed: {html.escape(str(error))}</div>"
        )
    return HTMLResponse(
        "<div class='text-emerald-400 font-semibold'>Discord test report sent successfully.</div>"
    )


@app.post("/test-arr-connection/{app_type}/{instance}", response_class=HTMLResponse)
async def test_connection(app_type: str, instance: str, request: Request):
    if app_type not in {"sonarr", "radarr"} or instance not in {"a", "b"}:
        return HTMLResponse("<span class='text-red-400 font-semibold'>Connection failed</span>")
    form = await request.form()
    url = str(form.get(f"{app_type}_{instance}_url", "")).strip()
    api_key = str(form.get(f"{app_type}_{instance}_api", "")).strip()
    connected = await asyncio.to_thread(test_arr_connection, url, api_key)
    if connected:
        return HTMLResponse("<span class='text-emerald-400 font-semibold'>Connected</span>")
    return HTMLResponse("<span class='text-red-400 font-semibold'>Connection failed</span>")
