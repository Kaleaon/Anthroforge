"""A14 render-only pass: opens the saved comparison blend, shoots in
judging order (cheap close-ups first, shell-heavy shots last)."""
import bpy, os, sys, time
ROOT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur"
bpy.ops.wm.open_mainfile(filepath=ROOT + "/shortfur_compare.blend")
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 32
scene.render.image_settings.file_format = 'PNG'

def shoot(cam_name, out, w, h, samples):
    t0 = time.time()
    scene.camera = bpy.data.objects[cam_name]
    scene.render.resolution_x = w; scene.render.resolution_y = h
    scene.cycles.samples = samples
    scene.render.filepath = ROOT + "/renders/" + out
    bpy.ops.render.render(write_still=True)
    print(f"A14 SHOT {out} {time.time()-t0:.0f}s", flush=True)

shoot("CamClose_ctrl", "render_close_ctrl", 880, 880, 64)
shoot("CamClose_t1", "render_close_t1", 880, 880, 64)
shoot("CamClose_t3", "render_close_t3", 880, 880, 64)
shoot("CamClose_t2", "render_close_t2", 880, 880, 64)
shoot("CamGrazeT2", "render_grazing_t2", 1200, 820, 64)
shoot("CamLineup", "render_lineup", 1680, 880, 56)
print("A14 RENDERS DONE", flush=True)
