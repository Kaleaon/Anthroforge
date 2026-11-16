import bpy, os
exec(open("render_clumps.py").read().split("HEAD_PARTS")[0])
HEAD_PARTS = {'fur_cheek_tufts', 'fur_ear_tufts', 'fur_chest_ruff'}
TAIL_OBJS = {'fur_tail_clumps', 'tail_core_proxy'}
for ob in bpy.data.objects:
    if ob.name in TAIL_OBJS:
        ob.hide_render = True
shot("head_threequarter.png", (0.82, 0.86, 0.34), (0, -0.02, -0.03))
shot("head_side.png", (1.45, -0.05, -0.02), (0, -0.02, -0.04))
shot("head_front.png", (0, 1.45, -0.02), (0, 0, -0.04))
print("DONE")
