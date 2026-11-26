# -*- coding: utf-8 -*-
"""Update online qua GitHub Releases: https://github.com/3DSixStudio/Render-Batch/releases

Chi lay ban trong Release MOI NHAT (khong lay code dang nam tren nhanh main).
Uu tien file .zip dinh kem trong release; neu khong co thi dung source zip cua tag.
"""

import io
import os
import json
import shutil
import zipfile
import datetime
import urllib.request
import urllib.error

OWNER = "3DSixStudio"
REPO = "Render-Batch"
REPO_URL = f"https://github.com/{OWNER}/{REPO}"
RELEASES_URL = f"{REPO_URL}/releases"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_DIR, ".installed_version.json")

# File/thu muc KHONG bao gio bi ghi de khi update
PROTECTED = {".git", ".installed_version.json", "_backup_update", "__pycache__"}

UA = {"User-Agent": "SCS-Batch-Render-Updater", "Accept": "application/vnd.github+json"}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def local_version():
    try:
        with open(os.path.join(APP_DIR, "version.txt"), "r", encoding="utf-8") as f:
            return f.read().strip() or "0"
    except Exception:
        return "0"


def version_tuple(v):
    parts = []
    for x in str(v or "").strip().lstrip("vV").split("."):
        num = "".join(ch for ch in x if ch.isdigit())
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def check_remote():
    """Doc Release moi nhat. Tra ve dict {tag, version, name, notes, date, url, download_url}."""
    try:
        rel = json.loads(_get(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("The repository has no releases yet (or it is private).")
        if e.code == 403:
            raise RuntimeError("GitHub rate limit reached. Please try again in a few minutes.")
        raise
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not connect to GitHub: {e.reason}")

    download = None
    for a in rel.get("assets", []):
        if a.get("name", "").lower().endswith(".zip"):
            download = a.get("browser_download_url")
            break
    if not download:
        download = rel.get("zipball_url")

    tag = rel.get("tag_name", "")
    return {
        "tag": tag,
        "version": tag.lstrip("vV"),
        "name": rel.get("name") or tag,
        "notes": (rel.get("body") or "").strip(),
        "date": (rel.get("published_at") or "")[:10],
        "url": rel.get("html_url") or RELEASES_URL,
        "download_url": download,
    }


def is_newer(remote, local_ver):
    return version_tuple(remote.get("version")) > version_tuple(local_ver)


def download_and_install(remote, log=print):
    url = remote["download_url"]
    log(f"Downloading {remote.get('tag')}: {url}")
    data = _get(url, timeout=180)
    log(f"Downloaded {len(data) / 1024:.0f} KB, extracting...")

    zf = zipfile.ZipFile(io.BytesIO(data))
    files = [n for n in zf.namelist() if not n.endswith("/")]
    if not files:
        raise RuntimeError("The downloaded zip is empty.")
    # Neu moi file nam chung 1 thu muc goc (vd: Render-Batch/...) thi bo thu muc do
    tops = {n.split("/")[0] for n in files}
    strip = (tops.pop() + "/") if len(tops) == 1 and all("/" in n for n in files) else ""
    if not any(n[len(strip):] == "scs_batch_render_app.py" for n in files):
        raise RuntimeError("Unexpected package layout (scs_batch_render_app.py not found).")

    backup = os.path.join(APP_DIR, "_backup_update", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    count = 0
    for n in files:
        rel = n[len(strip):]
        if not rel or rel.split("/")[0] in PROTECTED:
            continue
        dst = os.path.join(APP_DIR, *rel.split("/"))
        if os.path.isfile(dst):
            bdst = os.path.join(backup, *rel.split("/"))
            os.makedirs(os.path.dirname(bdst), exist_ok=True)
            shutil.copy2(dst, bdst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with zf.open(n) as src, open(dst, "wb") as out:
            out.write(src.read())
        count += 1

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"tag": remote.get("tag"),
                   "installed_at": datetime.datetime.now().isoformat(timespec="seconds")}, f, indent=1)
    log(f"Updated {count} file(s) to {remote.get('tag')}. Previous files backed up to: {backup}")
    return count
