"""Shared studio setup for fur prototype renders."""
import bpy
from mathutils import Vector


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def build_studio(scene):
    # world
    world = bpy.data.worlds.get("FurWorld") or bpy.data.worlds.new("FurWorld")
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.015, 0.015, 0.02, 1.0)
    bg.inputs[1].default_value = 0.7
    scene.world = world

    # ground
    if "Ground" not in bpy.data.objects:
        bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.002))
        g = bpy.context.active_object
        g.name = "Ground"
        gm = bpy.data.materials.new("GroundMat")
        gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
        gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
        g.data.materials.append(gm)

    def area(name, pos, energy, size, target=(0, 0, 1.0)):
        if name in bpy.data.objects:
            return bpy.data.objects[name]
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.shape = 'DISK'
        ld.size = size
        o = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(o)
        o.location = pos
        aim(o, target)
        return o

    area("KeyLight", (-2.3, -2.5, 3.1), 520, 2.2)
    area("FillLight", (2.5, -1.4, 1.5), 170, 2.6)
    area("RimLight", (0.7, 2.7, 2.7), 430, 1.8)

    if "Cam" not in bpy.data.objects:
        cd = bpy.data.cameras.new("Cam")
        cam = bpy.data.objects.new("Cam", cd)
        scene.collection.objects.link(cam)
    cam = bpy.data.objects["Cam"]
    scene.camera = cam
    return cam


def set_camera(cam, pos, target, lens=50):
    cam.location = pos
    cam.data.lens = lens
    aim(cam, target)


def psys_modifiers(ob):
    """Yield (psys_name, modifier) for particle system modifiers."""
    for m in ob.modifiers:
        if m.type == 'PARTICLE_SYSTEM':
            yield m.particle_system.name, m


def set_system_visibility(ob, visible_names):
    for name, m in psys_modifiers(ob):
        m.show_render = name in visible_names
        m.show_viewport = name in visible_names
