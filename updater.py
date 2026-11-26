# -*- coding: utf-8 -*-
"""Update online tu GitHub: https://github.com/3DSixStudio/Render-Batch"""

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
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(APP_DIR, ".installed_version.json")

# File/thu muc KHONG bao gio bi ghi de khi update
PROTECTED = {".git", ".installed_version.json", "_backup_update", "__pycache__"}

UA = {"User-Agent": "SCS-Batch-Render-Updater"}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def local_version():
    ver = "?"
    try:
        with open(os.path.join(APP_DIR, "version.txt"), "r", encoding="utf-8") as f:
            ver = f.read().strip() or "?"
    except Exception:
        pass
    sha = None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            sha = json.load(f).get("sha")
    except Exception:
        pass
    return ver, sha


def check_remote():
    """Tra ve dict {branch, sha, message, date, version}. Raise neu loi mang."""
    info = {"branch": "main", "sha": None, "message": "", "date": "", "version": None}
    try:
        repo = json.loads(_get(f"https://api.github.com/repos/{OWNER}/{REPO}"))
        info["branch"] = repo.get("default_branch") or "main"
        c = json.loads(_get(f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{info['branch']}"))
        info["sha"] = c.get("sha")
        msg = (c.get("commit", {}).get("message") or "").strip()
        info["message"] = msg.splitlines()[0] if msg else ""
        info["date"] = c.get("commit", {}).get("committer", {}).get("date", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("Khong tim thay repo (repo private, sai ten, hoac chua co commit nao).")
        if e.code == 403:
            info["sha"] = None  # bi gioi han API -> van cho phep tai ban moi nhat
        else:
            raise
    for br in (info["branch"], "main", "master"):
        try:
            info["version"] = _get(f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{br}/version.txt").decode("utf-8").strip()
            info["branch"] = br
            break
        except Exception:
            continue
    return info


def _version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).strip().lstrip("vV").split("."))
    except Exception:
        return None


def is_newer(remote, local_ver, local_sha):
    """True neu ban tren GitHub moi hon ban dang cai."""
    rv, lv = _version_tuple(remote.get("version")), _version_tuple(local_ver)
    if rv and lv and rv != lv:
        return rv > lv
    if remote.get("sha") and local_sha:
        return remote["sha"] != local_sha
    if remote.get("sha") and not local_sha:
        return True   # chua tung update -> khong biet, cho phep update
    return False


def download_and_install(branch, sha=None, log=print):
    url = f"https://codeload.github.com/{OWNER}/{REPO}/zip/refs/heads/{branch}"
    log(f"Dang tai: {url}")
    data = _get(url, timeout=120)
    log(f"Da tai {len(data) / 1024:.0f} KB, dang giai nen...")

    zf = zipfile.ZipFile(io.BytesIO(data))
    names = zf.namelist()
    if not names:
        raise RuntimeError("File zip rong.")
    top = names[0].split("/")[0] + "/"

    backup = os.path.join(APP_DIR, "_backup_update", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    count = 0
    for n in names:
        if not n.startswith(top) or n.endswith("/"):
            continue
        rel = n[len(top):]
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
        json.dump({"sha": sha, "branch": branch,
                   "installed_at": datetime.datetime.now().isoformat(timespec="seconds")}, f, indent=1)
    log(f"Da cap nhat {count} file. Ban cu luu tai: {backup}")
    return count
