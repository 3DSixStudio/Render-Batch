# -*- coding: utf-8 -*-
"""
SCS Batch Render - Core (chay BEN TRONG Blender, che do background)
====================================================================
File nay duoc app "SCS Batch Render" goi tu dong. Cung co the chay tay:

    blender --background "D:/scene.blend" --python scs_render_core.py --python-exit-code 1 -- --output "D:/renders"

Tham so (sau dau "--"):
    --output DIR        thu muc luu anh (bat buoc khi render)
    --start-frame N     frame bat dau (mac dinh 2) -> frame cua collection so N = start + (N-1)
    --gpu               ep Cycles dung GPU (OPTIX/CUDA/HIP/METAL/ONEAPI)
    --only A,B          chi render cac collection nay (vd: Scs_3,Icon_2)
    --select FILE.json  chi render cac item co key nam trong file (list string)
    --scan-json FILE    KHONG render, chi quet scene va ghi danh sach item ra JSON
    --scs-res WxH       size anh Scs (mac dinh 2796x2048)
    --icon-res WxH      size anh Icon (mac dinh 2048x2048)
    --percent N         % do phan giai (100 = full)

Quy tac:
  - Collection "Scs_<so>"  -> 2796 x 2048 | "Icon_<so>" -> 2048 x 2048
  - Moi object goc (empty/mesh top-level) trong collection = 1 anh rieng,
    object con tu hien theo.
  - Collection "Setup" luon hien.
  - Collection "Map": render rieng (1 anh, hoac 1 anh / Event_ duoc tick
    scs_event_active). Map luon bi AN trong anh object.
  - Object tick scs_render_separate=True -> render rieng o cuoi (frame goc cua scene).

App doc cac dong bat dau bang "@@SCS " (JSON) de cap nhat tien do.
"""

import bpy
import os
import re
import sys
import json
import argparse
import time
import datetime
import functools
import traceback

# Tranh UnicodeEncodeError khi ten object co dau (stdout bi pipe tren Windows = cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

print = functools.partial(print, flush=True)

DEFAULT_START_FRAME = 2
RESOLUTIONS = {
    "Scs": (2796, 2048),
    "Icon": (2048, 2048),
}
PREFIX_ORDER = {"Scs": 0, "Icon": 1}   # Scs truoc, Icon sau
FILE_FORMAT = "PNG"
FILE_EXT = ".png"


def mark(event, **data):
    """Dong tien do may doc duoc cho app UI."""
    data["ev"] = event
    print("@@SCS " + json.dumps(data, ensure_ascii=True))


_BAD_CHARS = re.compile(r'[<>:"/\\|?*#\s]+')


def safe_name(text):
    # '#' bi Blender thay bang so frame; cac ky tu con lai khong hop le tren Windows
    return _BAD_CHARS.sub("_", text).strip("_.") or "unnamed"


# ---------------------------------------------------------------------------
# ARGS
# ---------------------------------------------------------------------------
def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []

    p = argparse.ArgumentParser(description="SCS Batch Render Core")
    p.add_argument("--output", "-o", default=None)
    p.add_argument("--start-frame", type=int, default=DEFAULT_START_FRAME)
    p.add_argument("--only", default=None)
    p.add_argument("--select", default=None)
    p.add_argument("--scan-json", default=None)
    p.add_argument("--gpu", action="store_true")
    p.add_argument("--scs-res", default=None, help="Size anh Scs, vd 2796x2048")
    p.add_argument("--icon-res", default=None, help="Size anh Icon, vd 2048x2048")
    p.add_argument("--percent", type=int, default=100,
                   help="% do phan giai (100 = full; 25-50 de render thu nhanh)")
    return p.parse_args(argv)


def enable_gpu_rendering(scene):
    if scene.render.engine != 'CYCLES':
        print(f"!!! Render engine is '{scene.render.engine}', not CYCLES -> GPU option skipped.")
        return
    addon = bpy.context.preferences.addons.get("cycles")
    if not addon:
        print("!!! Cycles add-on preferences not found -> GPU option skipped.")
        return
    cprefs = addon.preferences
    chosen = None
    for backend in ["OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"]:
        try:
            cprefs.compute_device_type = backend
            cprefs.get_devices()
            if any(d.type == backend for d in cprefs.devices):
                chosen = backend
                for d in cprefs.devices:
                    d.use = (d.type == backend)
                break
        except Exception:
            continue
    if chosen:
        scene.cycles.device = 'GPU'
        print(f"=== GPU rendering: ON ({chosen}) ===")
        for d in cprefs.devices:
            if d.use:
                print(f"   -> Using: {d.name} ({d.type})")
    else:
        print("!!! No usable GPU found -> rendering on CPU.")


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def force_enable_collection(col_name):
    col = bpy.data.collections.get(col_name)
    if col:
        col.hide_viewport = False
        col.hide_render = False

    def walk(layer_col):
        if layer_col.name == col_name:
            layer_col.exclude = False
            layer_col.hide_viewport = False
        for child in layer_col.children:
            walk(child)

    walk(bpy.context.view_layer.layer_collection)


def set_hide_render_recursive_by_name(obj_name, hide_state, _visited=None):
    if _visited is None:
        _visited = set()
    if obj_name in _visited:
        return
    _visited.add(obj_name)
    obj = bpy.data.objects.get(obj_name)
    if obj:
        obj.hide_render = hide_state
        for child in obj.children:
            set_hide_render_recursive_by_name(child.name, hide_state, _visited)


# Cache ten object cua collection: goi .all_objects lap lai sau khi render
# co the lam Blender crash (EXCEPTION_ACCESS_VIOLATION) -> chi goi 1 lan.
_ALL_OBJECTS_CACHE = {}


def get_cached_all_object_names(col_name):
    if col_name not in _ALL_OBJECTS_CACHE:
        col = bpy.data.collections.get(col_name)
        _ALL_OBJECTS_CACHE[col_name] = [o.name for o in col.all_objects] if col else []
    return _ALL_OBJECTS_CACHE[col_name]


def set_collection_objects_hidden(col_name, hidden):
    for name in get_cached_all_object_names(col_name):
        obj = bpy.data.objects.get(name)
        if obj:
            obj.hide_render = hidden


def _flag(obj, prop):
    try:
        return bool(obj.get(prop, False)) or bool(getattr(obj, prop, False))
    except Exception:
        return False


def get_scs_event_active(obj):
    return _flag(obj, "scs_event_active")


def get_scs_render_separate(obj):
    return _flag(obj, "scs_render_separate")


RES_PERCENT = 100


def set_resolution(scene, width, height):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = RES_PERCENT


def render_still(scene, filepath):
    scene.render.filepath = filepath
    scene.render.image_settings.file_format = FILE_FORMAT
    start = time.time()
    print(f"  -> [START {datetime.datetime.now():%H:%M:%S}] Rendering: {filepath}")
    bpy.ops.render.render(write_still=True)
    elapsed = time.time() - start
    print(f"  -> [DONE {datetime.datetime.now():%H:%M:%S}] took {elapsed:.1f}s -> {filepath}")
    return elapsed


# ---------------------------------------------------------------------------
# QUEUE
# ---------------------------------------------------------------------------
def custom_separate_names():
    return {o.name for o in bpy.data.objects
            if o.type in {'EMPTY', 'MESH'} and get_scs_render_separate(o)}


def find_root_objects(target_col, exclude_names):
    col_names = {o.name for o in target_col.objects}
    roots = []
    for obj in target_col.objects:
        parent = obj.parent
        if obj.type == 'EMPTY':
            # Goc neu: khong co parent, hoac parent khong phai empty VA khong nam
            # trong cung collection (tranh render trung khi empty con cua 1 mesh goc)
            is_root = parent is None or (parent.type != 'EMPTY' and parent.name not in col_names)
        elif obj.type == 'MESH':
            is_root = parent is None or parent.name not in col_names
        else:
            is_root = False
        if is_root and obj.name not in exclude_names:
            roots.append(obj.name)
    return roots


def build_queue_for_collection(prefix, number, target_col, output_dir, exclude_names):
    col_name = target_col.name
    queue = []
    map_col = bpy.data.collections.get("Map")
    if map_col:
        events = [o for o in map_col.objects
                  if o.type == 'EMPTY' and o.name.startswith("Event_") and get_scs_event_active(o)]
        if events:
            for ev in events:
                queue.append({
                    "key": f"{col_name}::map_event::{ev.name}",
                    "type": "map_event",
                    "label": f"Map - {ev.name}",
                    "filepath": os.path.join(output_dir, safe_name(f"{prefix}_{number}_Map_{ev.name}") + FILE_EXT),
                    "event_name": ev.name,
                })
        else:
            queue.append({
                "key": f"{col_name}::map",
                "type": "map",
                "label": "Map",
                "filepath": os.path.join(output_dir, safe_name(f"{prefix}_{number}_Map") + FILE_EXT),
            })

    for obj_name in find_root_objects(target_col, exclude_names):
        queue.append({
            "key": f"{col_name}::object::{obj_name}",
            "type": "object",
            "label": obj_name,
            "filepath": os.path.join(output_dir, safe_name(f"{prefix}_{number}_{obj_name}") + FILE_EXT),
            "target_obj": obj_name,
        })
    return queue


def build_plan(args, output_dir):
    pattern = re.compile(r'^(Scs|Icon)_(\d+)$')
    found = []
    for col in bpy.data.collections:
        m = pattern.match(col.name)
        if m:
            found.append((m.group(1), int(m.group(2)), col))

    if args.only:
        only = {s.strip() for s in args.only.split(",") if s.strip()}
        found = [t for t in found if t[2].name in only]

    found.sort(key=lambda t: (PREFIX_ORDER.get(t[0], 9), t[1]))

    excl = custom_separate_names()
    plan = []
    for prefix, number, col in found:
        w, h = RESOLUTIONS[prefix]
        plan.append({
            "name": col.name, "prefix": prefix, "number": number, "col": col,
            "resolution": (w, h),
            "frame": args.start_frame + (number - 1),
            "items": build_queue_for_collection(prefix, number, col, output_dir, excl),
        })

    custom = []
    for o in bpy.data.objects:
        if o.type in {'EMPTY', 'MESH'} and get_scs_render_separate(o):
            col_name = o.users_collection[0].name if o.users_collection else "Setup"
            custom.append({
                "key": f"custom::{o.name}",
                "type": "custom",
                "label": o.name,
                "collection": col_name,
                "filepath": os.path.join(output_dir, safe_name(f"Custom_{o.name}") + FILE_EXT),
                "target_obj": o.name,
            })
    return plan, custom


# ---------------------------------------------------------------------------
# SCAN MODE
# ---------------------------------------------------------------------------
def do_scan(args):
    scene = bpy.context.scene
    plan, custom = build_plan(args, args.output or "")
    data = {
        "blend": bpy.data.filepath,
        "scene": scene.name,
        "engine": scene.render.engine,
        "frame_current": scene.frame_current,
        "has_setup": bpy.data.collections.get("Setup") is not None,
        "has_map": bpy.data.collections.get("Map") is not None,
        "collections": [{
            "name": c["name"], "prefix": c["prefix"], "number": c["number"],
            "resolution": list(c["resolution"]), "frame": c["frame"],
            "items": [{"key": i["key"], "type": i["type"], "label": i["label"]} for i in c["items"]],
        } for c in plan],
        "custom": [{"key": c["key"], "type": "custom", "label": c["label"], "collection": c["collection"]}
                   for c in custom],
    }
    with open(args.scan_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n_items = sum(len(c["items"]) for c in plan) + len(custom)
    print(f"=== SCAN COMPLETE: {len(plan)} collection(s), {n_items} image(s) ===")
    mark("scan_done", path=args.scan_json)


# ---------------------------------------------------------------------------
# RENDER
# ---------------------------------------------------------------------------
class Counter:
    def __init__(self, total):
        self.total = total
        self.index = 0
        self.ok = 0
        self.fail = 0


def run_item(scene, item, col_info, counter, action):
    counter.index += 1
    mark("item", i=counter.index, total=counter.total, key=item["key"], label=item["label"],
         collection=col_info["name"],
         res=[int(r * RES_PERCENT / 100) for r in col_info["resolution"]], frame=scene.frame_current,
         path=item["filepath"])
    try:
        action()
        elapsed = render_still(scene, item["filepath"])
        counter.ok += 1
        mark("done", i=counter.index, key=item["key"], path=item["filepath"], sec=round(elapsed, 1))
    except Exception as e:
        counter.fail += 1
        print(f"!!! ERROR while rendering {item['key']}: {e}")
        traceback.print_exc()
        mark("error", i=counter.index, key=item["key"], msg=str(e))


def process_collection(info, counter):
    scene = bpy.context.scene
    frame = info["frame"]
    scene.frame_set(frame)
    scene.frame_start = frame
    scene.frame_end = frame
    set_resolution(scene, *info["resolution"])

    for obj in bpy.data.objects:
        obj.hide_render = True

    force_enable_collection("Setup")
    set_collection_objects_hidden("Setup", False)

    map_col = bpy.data.collections.get("Map")
    if map_col:
        force_enable_collection("Map")
        set_collection_objects_hidden("Map", True)

    force_enable_collection(info["name"])

    for item in info["items"]:
        t = item["type"]
        if t in ("map", "map_event"):
            def show_map(item=item):
                set_collection_objects_hidden("Map", False)
                for obj in map_col.objects:
                    if obj.type == 'EMPTY' and obj.name.startswith("Event_"):
                        hide = True if item["type"] == "map" else (obj.name != item["event_name"])
                        set_hide_render_recursive_by_name(obj.name, hide)
            run_item(scene, item, info, counter, show_map)
            set_collection_objects_hidden("Map", True)
        elif t == "object":
            run_item(scene, item, info, counter,
                     lambda item=item: set_hide_render_recursive_by_name(item["target_obj"], False))
            set_hide_render_recursive_by_name(item["target_obj"], True)


def process_custom_objects(custom, counter, orig_frame, orig_res):
    if not custom:
        return
    scene = bpy.context.scene
    # FIX: dung frame GOC cua scene (truoc day frame_current da bi doi sang collection cuoi)
    scene.frame_set(orig_frame)
    scene.frame_start = orig_frame
    scene.frame_end = orig_frame
    print(f"\n=== Rendering {len(custom)} Custom Object(s) | Frame {orig_frame} ===")

    for obj in bpy.data.objects:
        obj.hide_render = True
    force_enable_collection("Setup")
    set_collection_objects_hidden("Setup", False)

    pattern = re.compile(r'^(Scs|Icon)_(\d+)$')
    for item in custom:
        col_name = item["collection"]
        m = pattern.match(col_name)
        # FIX: resolution theo collection chua object (truoc day lay resolution cua collection cuoi)
        res = RESOLUTIONS[m.group(1)] if m else orig_res
        set_resolution(scene, *res)
        force_enable_collection(col_name)
        info = {"name": col_name, "resolution": res}
        run_item(scene, item, info, counter,
                 lambda item=item: set_hide_render_recursive_by_name(item["target_obj"], False))
        set_hide_render_recursive_by_name(item["target_obj"], True)


def load_selection(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data if isinstance(data, list) else data.get("keys", []))


def do_render(args):
    global RES_PERCENT
    RES_PERCENT = max(1, min(100, args.percent))
    if not args.output:
        print("!!! Missing --output")
        sys.exit(1)
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    scene = bpy.context.scene
    orig_frame = scene.frame_current
    orig_res = (scene.render.resolution_x, scene.render.resolution_y)

    if args.gpu:
        enable_gpu_rendering(scene)

    plan, custom = build_plan(args, output_dir)

    if args.select:
        sel = load_selection(args.select)
        for c in plan:
            c["items"] = [i for i in c["items"] if i["key"] in sel]
        custom = [c for c in custom if c["key"] in sel]
    plan = [c for c in plan if c["items"]]

    total = sum(len(c["items"]) for c in plan) + len(custom)
    if total == 0:
        print("!!! Nothing to render (no Scs_N/Icon_N collections found, or nothing selected).")
        mark("finish", ok=0, fail=0, total=0, sec=0)
        return

    print(f"=== Rendering {total} image(s) in {len(plan)} collection(s) ===")
    for c in plan:
        print(f"   - {c['name']}: {len(c['items'])} image(s) | {c['resolution'][0]}x{c['resolution'][1]} | frame {c['frame']}")
    if custom:
        print(f"   - Custom: {len(custom)} image(s)")
    mark("total", total=total)

    get_cached_all_object_names("Setup")
    get_cached_all_object_names("Map")

    print("\n*** The FIRST image can take a few minutes (shader compile / loading the scene to the GPU).\n")

    counter = Counter(total)
    t0 = time.time()
    for info in plan:
        print(f"\n=== Render {info['name']} | {info['resolution'][0]}x{info['resolution'][1]} | Frame {info['frame']} ===")
        process_collection(info, counter)
    process_custom_objects(custom, counter, orig_frame, orig_res)

    sec = time.time() - t0
    m, s = divmod(sec, 60)
    print(f"\n=== FINISHED | {counter.ok} OK, {counter.fail} failed | Total: {int(m)} min {s:.1f} s ===")
    mark("finish", ok=counter.ok, fail=counter.fail, total=total, sec=round(sec, 1))
    if counter.fail:
        sys.exit(2)


def _parse_res(text):
    m = re.match(r"^\s*(\d+)\s*[xX*×]\s*(\d+)\s*$", text or "")
    if not m:
        return None
    w, h = int(m.group(1)), int(m.group(2))
    return (w, h) if w > 0 and h > 0 else None


def apply_custom_resolutions(args):
    for key, prefix in (("scs_res", "Scs"), ("icon_res", "Icon")):
        val = getattr(args, key, None)
        if val:
            res = _parse_res(val)
            if res:
                RESOLUTIONS[prefix] = res
            else:
                print(f"!!! Ignoring --{key.replace('_', '-')} '{val}' (invalid, expected e.g. 2796x2048)")
    print(f"=== Image size: Scs {RESOLUTIONS['Scs'][0]}x{RESOLUTIONS['Scs'][1]} | "
          f"Icon {RESOLUTIONS['Icon'][0]}x{RESOLUTIONS['Icon'][1]} ===")


def main():
    args = parse_args()
    apply_custom_resolutions(args)
    if args.scan_json:
        do_scan(args)
    else:
        do_render(args)


if __name__ == "__main__":
    main()
