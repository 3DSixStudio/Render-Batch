# -*- coding: utf-8 -*-
"""Tu dong tim blender.exe tren may Windows."""

import os
import re
import glob
import shutil
import subprocess
import sys


def _norm(p):
    try:
        return os.path.normcase(os.path.abspath(p))
    except Exception:
        return p


def _version_from_path(path):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", os.path.basename(os.path.dirname(path)))
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    return None


def get_blender_version(exe, timeout=15):
    """Chay 'blender --version' de lay version that (vd: 'Blender 4.2.3')."""
    try:
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        out = subprocess.run([exe, "--version"], capture_output=True, text=True,
                             timeout=timeout, creationflags=flags, errors="replace").stdout
        m = re.search(r"Blender\s+(\d+)\.(\d+)(?:\.(\d+))?", out)
        if m:
            return tuple(int(x) if x else 0 for x in m.groups())
    except Exception:
        pass
    return None


def _registry_candidates():
    found = []
    if sys.platform != "win32":
        return found
    try:
        import winreg
    except ImportError:
        return found

    keys = [
        (winreg.HKEY_CLASSES_ROOT, r"blendfile\shell\open\command", ""),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Classes\blendfile\shell\open\command", ""),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Classes\blendfile\shell\open\command", ""),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\blender.exe", ""),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\blender.exe", ""),
    ]
    for root, sub, val in keys:
        try:
            with winreg.OpenKey(root, sub) as k:
                v, _ = winreg.QueryValueEx(k, val)
                m = re.search(r'"?([^"]*?blender(?:-launcher)?\.exe)"?', v, re.I)
                if m:
                    p = m.group(1).replace("blender-launcher.exe", "blender.exe")
                    found.append(p)
        except OSError:
            pass

    # Danh sach chuong trinh da cai (Uninstall)
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for base in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
            try:
                with winreg.OpenKey(root, base) as k:
                    for i in range(winreg.QueryInfoKey(k)[0]):
                        try:
                            name = winreg.EnumKey(k, i)
                            with winreg.OpenKey(k, name) as sk:
                                disp = winreg.QueryValueEx(sk, "DisplayName")[0]
                                if "blender" not in str(disp).lower():
                                    continue
                                for field in ("InstallLocation", "DisplayIcon"):
                                    try:
                                        v = winreg.QueryValueEx(sk, field)[0]
                                    except OSError:
                                        continue
                                    v = str(v).strip('"').split(",")[0]
                                    if v.lower().endswith(".exe"):
                                        v = os.path.dirname(v)
                                    if v:
                                        found.append(os.path.join(v, "blender.exe"))
                        except OSError:
                            continue
            except OSError:
                pass
    return found


def _steam_libraries():
    libs = []
    roots = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
        os.path.expandvars(r"%ProgramFiles%\Steam"),
    ]
    if sys.platform == "win32":
        try:
            import winreg
            for root, sub in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                              (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(root, sub) as k:
                        for val in ("SteamPath", "InstallPath"):
                            try:
                                roots.append(winreg.QueryValueEx(k, val)[0])
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass

    for r in roots:
        if not r or not os.path.isdir(r):
            continue
        libs.append(r)
        vdf = os.path.join(r, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            try:
                with open(vdf, "r", encoding="utf-8", errors="replace") as f:
                    for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                        libs.append(m.group(1).replace("\\\\", "\\"))
            except Exception:
                pass
    return libs


def find_blenders():
    """Tra ve list dict {path, version(tuple|None), label} - moi nhat truoc."""
    cands = []

    cands += _registry_candidates()

    for lib in _steam_libraries():
        cands.append(os.path.join(lib, "steamapps", "common", "Blender", "blender.exe"))

    pf_dirs = {os.environ.get(v) for v in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")}
    for pf in filter(None, pf_dirs):
        cands += glob.glob(os.path.join(pf, "Blender Foundation", "*", "blender.exe"))
        cands += glob.glob(os.path.join(pf, "Blender*", "blender.exe"))

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        cands += glob.glob(os.path.join(local, "Programs", "Blender*", "*", "blender.exe"))
        cands += glob.glob(os.path.join(local, "Programs", "Blender*", "blender.exe"))
    home = os.path.expanduser("~")
    cands += glob.glob(os.path.join(home, "scoop", "apps", "blender", "*", "blender.exe"))

    # Microsoft Store: WindowsApps\BlenderFoundation.Blender* (thuong khong doc duoc,
    # nhung co alias trong %LOCALAPPDATA%\Microsoft\WindowsApps\blender.exe)
    if local:
        cands.append(os.path.join(local, "Microsoft", "WindowsApps", "blender.exe"))

    # O dia khac: X:\Blender*\blender.exe, X:\Program Files\Blender Foundation\*
    for d in "CDEFGH":
        root = f"{d}:\\"
        if not os.path.isdir(root):
            continue
        cands += glob.glob(os.path.join(root, "Blender*", "blender.exe"))
        cands += glob.glob(os.path.join(root, "Blender*", "*", "blender.exe"))
        if d != "C":
            cands += glob.glob(os.path.join(root, "Program Files", "Blender Foundation", "*", "blender.exe"))
            cands.append(os.path.join(root, "SteamLibrary", "steamapps", "common", "Blender", "blender.exe"))

    w = shutil.which("blender")
    if w:
        cands.append(w)

    seen = set()
    result = []
    for p in cands:
        if not p or not os.path.isfile(p):
            continue
        key = _norm(p)
        if key in seen:
            continue
        seen.add(key)
        result.append({"path": os.path.abspath(p), "version": None})

    # Lay version that bang --version (nhanh, ~1s/ban)
    for r in result:
        r["version"] = get_blender_version(r["path"]) or _version_from_path(r["path"])
        v = ".".join(str(x) for x in r["version"]) if r["version"] else "?"
        src = "Steam" if "steamapps" in r["path"].lower() else ""
        r["label"] = f"Blender {v}" + (f" ({src})" if src else "") + f"  -  {r['path']}"

    result.sort(key=lambda r: r["version"] or (0,), reverse=True)
    return result


if __name__ == "__main__":
    for b in find_blenders():
        print(b["label"])
