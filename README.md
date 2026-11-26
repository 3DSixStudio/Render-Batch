# Render Batch

<img src="ui/icon.png" width="72" align="right">

Windows desktop app (PySide6) that batch renders the `Scs_N` / `Icon_N` collections of a prepared Blender file by running Blender in background mode (the Blender UI never opens).

Created by **Hari**.

## Install

1. Download **`Render_Batch_Setup_vX.Y.Z.exe`** from [Releases](https://github.com/3DSixStudio/Render-Batch/releases/latest).
2. Run it and click through the installer (no admin rights needed; installs to `%LOCALAPPDATA%\Programs\Render Batch`, adds Start Menu and optional Desktop shortcuts, and an uninstaller in Windows Settings › Apps).
3. Updates: open **Info & Update → Check for updates**. The app downloads the new setup, installs it silently and reopens by itself.

No Python needed for the installed version.

### Run from source (developers)

Install Python 3.10+, download the source zip (or `git clone`), run **`run.bat`** (installs PySide6 on first run). In this mode updates replace the source files.

## Layout

The sidebar has two **workspaces** and a **general** section:

| Section | What it does |
|---|---|
| **Icon & SCS** | Batch renders the `Scs_N` / `Icon_N` collections of a prepared .blend. Options: image size for Scs / Icon, resolution scale, start frame. |
| **Asset Render** | Renders a folder of FBX files with automatic camera, lights and framing. |
| **Settings** | Shared by both workspaces: Blender executable (auto-detected) and GPU rendering. |
| **Info & Update** | About the app (created by Hari) and updates from GitHub Releases. |

Both workspaces share the same layout: header with **Start Render / Stop Now**, four stat cards (found, will render, rendered, elapsed / ETA), **Source** + **Render Options** cards, then the list of items to tick and a **Progress** card (current image, last finished image, log).

## Asset Render

Point the app at a folder of **FBX** files and it renders one PNG per file, no scene setup needed:

- Each FBX is imported into an empty studio scene (cameras / lights inside the FBX are ignored).
- Camera: **3/4 view** or **Front view**; the camera is moved so the whole asset fits the frame with the chosen margin (never cropped).
- **Asset type** (Auto by default): files with a rig (armature) or `-Loop` in the name are **skins** - camera at eye level (front 4°, 3/4 turned 22° at 6°), soft frontal light, smooth textures. Everything else is an **object** - camera a bit from above (front 8°, 3/4 turned 35° at 20°), sharp pixel textures. Camera height can be overridden.
- Lights: automatic key / fill / rim sun lights + soft ambient, "Standard" colour so colours stay vivid. Light strength is adjustable.
- Parents are rendered together with all their children (everything in the FBX). Animated FBX files are posed at their first frame.
- Image name = FBX name, with everything from `-Loop` removed: `Boy-Loop-Idle.fbx` → `Boy.png`. Duplicate names get `_2`, `_3`…
- Transparent background and sharp pixel textures by default. Cycles or EEVEE.

## Render rules

| Collection | Default size | Frame |
|---|---|---|
| `Scs_N` | 2796 × 2048 | Start + (N − 1) |
| `Icon_N` | 2048 × 2048 | Start + (N − 1) |

- Every root object (top-level empty/mesh) in a collection → one image; its children are shown with it.
- `Setup` is always visible. `Map` is rendered as its own image (or one image per `Event_` with `scs_event_active`) and is always hidden in object images.
- Objects with `scs_render_separate = True` are rendered last, at the scene's original frame.
- Order: Scs first, then Icon, each ascending by number.

## Command line (no UI)

`Render_Batch_CLI.bat`, or:

```
blender --background scene.blend --python scs_render_core.py --python-exit-code 1 -- --output D:\renders [--gpu] [--only Scs_1,Icon_2] [--scs-res 2796x2048] [--icon-res 2048x2048] [--percent 25]
```

## Releasing (automatic)

1. Change the code, describe the changes in `release_notes.md`, bump `version.txt` (e.g. `1.4.1`).
2. Push to `main` → GitHub Actions (`.github/workflows/release.yml`, Windows runner) builds `RenderBatch.exe` with PyInstaller (`installer/RenderBatch.spec`), self-tests it, builds the installer with Inno Setup (`installer/RenderBatch.iss`) and publishes release `v1.4.1` with `Render_Batch_Setup_v1.4.1.exe` and the source zip.
3. Users click *Info & Update → Check for updates*. Pushes without a version bump do not create a release.

To regenerate the icon: `python tools/make_icon.py` (needs Pillow).
