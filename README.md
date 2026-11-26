# Render Batch

<img src="ui/icon.png" width="72" align="right">

Windows desktop app (PySide6) that batch renders the `Scs_N` / `Icon_N` collections of a prepared Blender file by running Blender in background mode (the Blender UI never opens).

Created by **Hari**.

## Install & run

1. Install **Python 3.10+** from https://www.python.org/downloads/ (tick *Add python.exe to PATH*).
2. Download the latest `Render_Batch_vX.Y.Z.zip` from [Releases](https://github.com/3DSixStudio/Render-Batch/releases/latest) and unzip it to a permanent folder.
3. Run **`run.bat`**. The first run installs PySide6 automatically.
4. Optional: run `Create_Desktop_Shortcut.bat` to create a Desktop shortcut (with the app icon).

## Features

- Dashboard UI: stat cards, live progress ring, scene item counts (Scs / Icon / Custom), recent renders.
- **Settings** popup: Blender executable (auto-detected from registry, Program Files, all Steam libraries, PATH...), GPU rendering, start frame, image size for Scs_N / Icon_N and resolution scale.
- **Info** popup: about the app and **Update** (checks GitHub Releases, optional check on start-up, previous files backed up to `_backup_update/`).
- Drag & drop a `.blend` onto the window to load and scan it.
- Scene items with check boxes, search and filter; render **all** or **checked only** (check state remembered per .blend).
- **Stop Now** kills Blender immediately. Full render log, saveable to a file.

## Asset Render

Point the app at a folder of **FBX** files and it renders one PNG per file, no scene setup needed:

- Each FBX is imported into an empty studio scene (cameras / lights inside the FBX are ignored).
- Camera: **3/4 view** or **Front view**, adjustable height; the camera is moved so the whole asset fits the frame with the chosen margin (never cropped).
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

1. Change the code, describe the changes in `release_notes.md`, bump `version.txt` (e.g. `1.1.1`).
2. Push to `main` → GitHub Actions (`.github/workflows/release.yml`) packages `Render_Batch_v1.1.1.zip` and publishes release `v1.1.1`.
3. Users click *Info → Check for updates*. Pushes without a version bump do not create a release.

To regenerate the icon: `python tools/make_icon.py` (needs Pillow).
