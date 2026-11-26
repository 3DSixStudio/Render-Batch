# -*- coding: utf-8 -*-
"""
Render Batch - Asset Render core (runs INSIDE Blender, background mode)
=======================================================================
For every FBX file: import into an empty studio scene, set up camera + lights,
fit the camera so the whole asset is inside the frame, render a PNG.

    blender --background --python asset_render_core.py --python-exit-code 1 -- \
        --jobs jobs.json --output D:/renders [--view three_quarter|front] [--gpu] ...

jobs.json = [{"key": "...", "path": "D:/assets/Boy-Loop-Idle.fbx", "name": "Boy"}, ...]
Progress lines start with "@@SCS " (JSON), same protocol as scs_render_core.py.
"""

import bpy
import os
import sys
import json
import math
import time
import argparse
import functools
import traceback
from mathutils import Vector

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

print = functools.partial(print, flush=True)

STUDIO_PREFIX = "RB_"
RENDERABLE = {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'CURVES', 'POINTCLOUD', 'VOLUME'}

VIEWS = {
    # azimuth: degrees around Z, 0 = looking from the front (-Y) ; negative = camera on the left
    "three_quarter": {"azimuth": -35.0, "elevation": 20.0},
    "front": {"azimuth": 0.0, "elevation": 8.0},
}


def mark(event, **data):
    data["ev"] = event
    print("@@SCS " + json.dumps(data, ensure_ascii=True))


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(description="Render Batch - Asset Render")
    p.add_argument("--jobs", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--view", default="three_quarter", choices=list(VIEWS.keys()))
    p.add_argument("--elevation", type=float, default=None, help="override camera elevation (deg)")
    p.add_argument("--margin", type=float, default=6.0, help="empty border around the asset, % of frame")
    p.add_argument("--width", type=int, default=2048)
    p.add_argument("--height", type=int, default=2048)
    p.add_argument("--focal", type=float, default=50.0)
    p.add_argument("--engine", default="cycles", choices=["cycles", "eevee"])
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--light", type=float, default=1.0, help="overall light multiplier")
    p.add_argument("--opaque", action="store_true", help="white background instead of transparent")
    p.add_argument("--smooth-textures", action="store_true", help="keep linear texture filtering")
    p.add_argument("--gpu", action="store_true")
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Scene / studio
# ---------------------------------------------------------------------------
def engine_id(name):
    items = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()
    if name == "cycles":
        return "CYCLES"
    for cand in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if cand in items:
            return cand
    return "CYCLES"


def enable_gpu(scene):
    if scene.render.engine != 'CYCLES':
        return
    addon = bpy.context.preferences.addons.get("cycles")
    if not addon:
        print("!!! Cycles add-on preferences not found -> GPU option skipped.")
        return
    cp = addon.preferences
    for backend in ["OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"]:
        try:
            cp.compute_device_type = backend
            cp.get_devices()
            if any(d.type == backend for d in cp.devices):
                for d in cp.devices:
                    d.use = (d.type == backend)
                scene.cycles.device = 'GPU'
                print(f"=== GPU rendering: ON ({backend}) ===")
                return
        except Exception:
            continue
    print("!!! No usable GPU found -> rendering on CPU.")


def setup_scene(args):
    scene = bpy.context.scene
    r = scene.render
    r.engine = engine_id(args.engine)
    r.resolution_x = args.width
    r.resolution_y = args.height
    r.resolution_percentage = 100
    r.film_transparent = not args.opaque
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGBA' if not args.opaque else 'RGB'
    r.image_settings.color_depth = '8'
    r.image_settings.compression = 15

    # Bright, saturated colours like the reference icons
    try:
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.look = 'None'
    except Exception:
        pass
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    if r.engine == 'CYCLES':
        c = scene.cycles
        c.samples = max(1, args.samples)
        try:
            c.use_adaptive_sampling = True
            c.adaptive_threshold = 0.03
            c.use_denoising = True
        except Exception:
            pass
        c.max_bounces = 6
        c.diffuse_bounces = 3
        c.glossy_bounces = 2
        c.transmission_bounces = 4
        c.transparent_max_bounces = 8
        c.caustics_reflective = False
        c.caustics_refractive = False
        try:
            r.use_persistent_data = True
        except Exception:
            pass
        if args.gpu:
            enable_gpu(scene)
    else:
        e = scene.eevee
        try:
            e.taa_render_samples = max(1, args.samples)
        except Exception:
            pass
        for attr, val in (("use_shadows", True), ("use_raytracing", True), ("use_gtao", True)):
            try:
                setattr(e, attr, val)
            except Exception:
                pass

    # World = soft ambient fill (invisible with transparent film)
    world = bpy.data.worlds.get(STUDIO_PREFIX + "World") or bpy.data.worlds.new(STUDIO_PREFIX + "World")
    if not world.node_tree:
        world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
        bg.inputs[1].default_value = 0.45 * args.light
    scene.world = world

    # Camera
    cam_data = bpy.data.cameras.get(STUDIO_PREFIX + "Camera") or bpy.data.cameras.new(STUDIO_PREFIX + "Camera")
    cam_data.lens = args.focal
    cam_data.sensor_fit = 'AUTO'
    cam = bpy.data.objects.get(STUDIO_PREFIX + "Camera") or bpy.data.objects.new(STUDIO_PREFIX + "Camera", cam_data)
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    scene.camera = cam

    # Lights: key (top front-right of the camera), fill (left), rim (back top)
    lights = {}
    for name, energy, angle in (("Key", 2.6, 12.0), ("Fill", 0.55, 30.0), ("Rim", 1.4, 10.0)):
        ld = bpy.data.lights.get(STUDIO_PREFIX + name) or bpy.data.lights.new(STUDIO_PREFIX + name, 'SUN')
        ld.energy = energy * args.light
        ld.angle = math.radians(angle)
        ob = bpy.data.objects.get(STUDIO_PREFIX + name) or bpy.data.objects.new(STUDIO_PREFIX + name, ld)
        if ob.name not in scene.collection.objects:
            scene.collection.objects.link(ob)
        lights[name] = ob
    return cam, lights


def direction(azimuth_deg, elevation_deg):
    """Unit vector from the target TOWARDS the camera/light position."""
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    # azimuth 0 -> -Y (front); positive azimuth -> +X side
    return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))).normalized()


def aim_sun(obj, from_dir):
    # A sun shines along its local -Z. from_dir points from the target to the light.
    obj.rotation_euler = from_dir.to_track_quat('Z', 'Y').to_euler()


def place_lights(lights, cam_az, cam_el):
    aim_sun(lights["Key"], direction(cam_az + 40.0, max(cam_el + 35.0, 45.0)))
    aim_sun(lights["Fill"], direction(cam_az - 70.0, 15.0))
    aim_sun(lights["Rim"], direction(cam_az + 160.0, 50.0))


# ---------------------------------------------------------------------------
# Asset handling
# ---------------------------------------------------------------------------
def clean_scene():
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        if not ob.name.startswith(STUDIO_PREFIX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.actions, bpy.data.armatures,
                 bpy.data.textures, bpy.data.curves, bpy.data.node_groups, bpy.data.cameras, bpy.data.lights):
        for block in list(coll):
            if block.users == 0 and not block.name.startswith(STUDIO_PREFIX):
                try:
                    coll.remove(block)
                except Exception:
                    pass
    try:
        bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    except Exception:
        pass
    scene.frame_set(1)


def import_fbx(path):
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.fbx(filepath=path, use_anim=True)
    except AttributeError:
        bpy.ops.wm.fbx_import(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    # Remove cameras / lights that came with the file: the studio provides them
    for o in list(new):
        if o.type in {'CAMERA', 'LIGHT', 'LIGHT_PROBE'}:
            new.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    return new


def pose_frame(objects):
    """First frame of the imported animation (e.g. *-Loop-Idle), else 1."""
    starts = []
    for o in objects:
        ad = o.animation_data
        if ad and ad.action:
            try:
                starts.append(int(ad.action.frame_range[0]))
            except Exception:
                pass
    return min(starts) if starts else 1


def pixel_textures(objects, smooth):
    if smooth:
        return
    seen = set()
    for o in objects:
        for slot in getattr(o, "material_slots", []):
            m = slot.material
            if not m or m.name in seen or not m.node_tree:
                continue
            seen.add(m.name)
            for n in m.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'


def world_points(objects):
    """World-space vertices of everything that renders (with modifiers / armature pose)."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objects:
        if o.type not in RENDERABLE or o.hide_render:
            continue
        ev = o.evaluated_get(depsgraph)
        mw = ev.matrix_world
        try:
            me = ev.to_mesh()
        except Exception:
            me = None
        if me is not None and len(me.vertices):
            verts = me.vertices
            step = max(1, len(verts) // 20000)
            for i in range(0, len(verts), step):
                pts.append(mw @ verts[i].co)
            ev.to_mesh_clear()
        else:
            for c in ev.bound_box:
                pts.append(mw @ Vector(c))
    return pts


def fit_camera(cam, pts, view, margin_pct, aspect):
    """Place the camera along the view direction so every point is inside the frame."""
    d_dir = direction(view["azimuth"], view["elevation"])     # target -> camera
    fwd = -d_dir                                               # camera looks along fwd
    right = fwd.cross(Vector((0, 0, 1)))
    if right.length < 1e-6:
        right = Vector((1, 0, 0))
    right.normalize()
    up = right.cross(fwd).normalized()

    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    center = (lo + hi) / 2
    size = max((hi - lo).length, 1e-4)

    data = cam.data
    sensor = data.sensor_width
    # with sensor_fit AUTO the sensor covers the larger image side
    fov_big = 2 * math.atan(sensor / (2 * data.lens))
    if aspect >= 1:
        tan_h = math.tan(fov_big / 2)
        tan_v = tan_h / aspect
    else:
        tan_v = math.tan(fov_big / 2)
        tan_h = tan_v * aspect
    k = max(0.05, 1.0 - 2 * margin_pct / 100.0)
    tan_h *= k
    tan_v *= k

    target = center.copy()
    dist = size
    for _ in range(4):
        rel = [p - target for p in pts]
        need = 0.0
        for v in rel:
            x, y, z = v.dot(right), v.dot(up), v.dot(fwd)
            need = max(need, abs(x) / tan_h - z, abs(y) / tan_v - z)
        dist = max(need, size * 0.05)
        # re-centre the projected bounds
        xs, ys = [], []
        for v in rel:
            depth = dist + v.dot(fwd)
            if depth <= 1e-6:
                continue
            xs.append(v.dot(right) / depth)
            ys.append(v.dot(up) / depth)
        if not xs:
            break
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        if abs(cx) < 1e-4 and abs(cy) < 1e-4:
            break
        target = target + right * (cx * dist) + up * (cy * dist)

    cam.location = target + d_dir * dist
    cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
    data.clip_start = max(dist * 0.001, 1e-4)
    data.clip_end = dist + size * 4
    return dist


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()
    with open(args.jobs, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)

    view = dict(VIEWS[args.view])
    if args.elevation is not None:
        view["elevation"] = args.elevation

    clean_scene()
    cam, lights = setup_scene(args)
    place_lights(lights, view["azimuth"], view["elevation"])
    scene = bpy.context.scene
    aspect = args.width / float(args.height)

    total = len(jobs)
    print(f"=== Asset Render: {total} file(s) | view {args.view} | {args.width}x{args.height} | "
          f"engine {scene.render.engine} ===")
    mark("total", total=total)

    ok = fail = 0
    t0 = time.time()
    for i, job in enumerate(jobs, 1):
        out_path = os.path.join(out_dir, job["name"] + ".png")
        mark("item", i=i, total=total, key=job["key"], label=job["name"],
             collection=os.path.basename(job["path"]), res=[args.width, args.height], frame=1, path=out_path)
        start = time.time()
        try:
            clean_scene()
            print(f"\n--- [{i}/{total}] {os.path.basename(job['path'])} -> {job['name']}.png")
            objs = import_fbx(job["path"])
            if not objs:
                raise RuntimeError("Nothing was imported from this FBX.")
            frame = pose_frame(objs)
            scene.frame_set(frame)
            pixel_textures(objs, args.smooth_textures)
            pts = world_points(objs)
            if not pts:
                raise RuntimeError("The FBX has no renderable geometry.")
            dist = fit_camera(cam, pts, view, args.margin, aspect)
            n_mesh = sum(1 for o in objs if o.type in RENDERABLE)
            print(f"    {len(objs)} object(s), {n_mesh} renderable, frame {frame}, camera distance {dist:.3f}")
            scene.render.filepath = out_path
            bpy.ops.render.render(write_still=True)
            sec = time.time() - start
            ok += 1
            print(f"    [DONE] {sec:.1f}s -> {out_path}")
            mark("done", i=i, key=job["key"], path=out_path, sec=round(sec, 1))
        except Exception as e:
            fail += 1
            print(f"!!! ERROR on {job['path']}: {e}")
            traceback.print_exc()
            mark("error", i=i, key=job["key"], msg=str(e))

    sec = time.time() - t0
    m, s = divmod(sec, 60)
    print(f"\n=== FINISHED | {ok} OK, {fail} failed | Total: {int(m)} min {s:.1f} s ===")
    mark("finish", ok=ok, fail=fail, total=total, sec=round(sec, 1))
    if fail:
        sys.exit(2)


if __name__ == "__main__":
    main()
