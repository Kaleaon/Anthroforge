# Neutral Base Head v2 — LAYERED construction (skull -> muscles -> tissue)
# Headless Blender 5.2.3. Frame: L=1.0 along Y (nose +0.50, occiput -0.50), +Z up, +X = head's left.
# Tissue surface = skull form + muscle masses + tissue padding, per region (see TISSUE TABLE in notes).
import bpy, math, json, os, sys
from mathutils import Vector, Matrix

OUT = os.path.expanduser('~/workspace/anthroforge-v2/base-head-v2')
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
FINAL = '--final' in argv

# ---------------------------------------------------------------- helpers
def clean_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def make_mesh(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return ob

def material(name, color, rough=0.6, subsurface=0.0, spec=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Subsurface Weight'].default_value = subsurface
    bsdf.inputs['Subsurface Scale'].default_value = 0.012
    bsdf.inputs['Specular IOR Level'].default_value = spec
    return m

def assign_mat(ob, mat):
    ob.data.materials.append(mat)

def sstep(a, b, x):
    t = max(0.0, min(1.0, (x-a)/(b-a)))
    return t*t*(3-2*t)

def gauss(d, s):
    return math.exp(-(d*d)/(2*s*s))

def catmull(keys, t):
    # keys: list of (x, v) in ANY order; interpolate v at t
    keys = sorted(keys)
    if t <= keys[0][0]: return keys[0][1]
    if t >= keys[-1][0]: return keys[-1][1]
    for i in range(len(keys)-1):
        x0, v0 = keys[i]; x1, v1 = keys[i+1]
        if x0 <= t <= x1:
            u = (t-x0)/(x1-x0)
            # smoothstep interpolation (C1-ish, monotone)
            return v0 + (v1-v0)*(u*u*(3-2*u))
    return keys[-1][1]

# ---------------------------------------------------------------- loft builder
# stations: list of dicts along Y. Ring: NR points, superellipse cross-section.
def loft(name, keys, n_stations, n_ring, cap_front=True, cap_back=True, arch_z=-0.010):
    chans = list(keys[0].keys())
    ys = [k['y'] for k in keys]
    stations = []
    for i in range(n_stations):
        y = ys[0] + (ys[-1]-ys[0]) * i/(n_stations-1)
        st = {c: catmull([(k['y'], k[c]) for k in keys], y) for c in chans}
        st['y'] = y
        stations.append(st)
    verts, faces = [], []
    for st in stations:
        hw, top, bot, p = st['hw'], st['top'], st['bot'], st['p']
        arch = st.get('arch', 0.0)
        for j in range(n_ring):
            a = 2*math.pi*j/n_ring
            c, s = math.cos(a), math.sin(a)
            ex = 2.0/p
            x = hw * math.copysign(abs(c)**ex, c)
            f = math.copysign(abs(s)**ex, s)
            z = top*f if s >= 0 else bot*(-f)  # bot is negative; -f = |shape| on the lower half
            # zygomatic arch bulge: lateral, band-limited in z
            if arch:
                x += math.copysign(arch*gauss(z-arch_z, st.get('archsig', 0.062)), x if x != 0 else 1)
            # dorsal flattening (frontal / nasal plane): compress top toward plane
            fl = st.get('flat', 0.0)
            if fl and z > 0:
                plane = top*0.52
                if z > plane:
                    z = plane + (z-plane)*(1-0.55*fl)
            verts.append((x, st['y'], z))
    for i in range(n_stations-1):
        for j in range(n_ring):
            j1 = (j+1) % n_ring
            a = i*n_ring+j; b = i*n_ring+j1; c2 = (i+1)*n_ring+j1; d = (i+1)*n_ring+j
            faces.append((a, b, c2, d))
    if cap_front:
        st = stations[0]
        ci = len(verts); verts.append((0, st['y']+0.018, (st['top']+st['bot'])/2))
        for j in range(n_ring):
            faces.append((ci, (j+1) % n_ring, j))
    if cap_back:
        st = stations[-1]
        base = (n_stations-1)*n_ring
        ci = len(verts); verts.append((0, st['y']-0.018, (st['top']+st['bot'])/2))
        for j in range(n_ring):
            faces.append((ci, base+j, base+(j+1) % n_ring))
    return verts, faces, stations

# ---------------------------------------------------------------- station tables
# TISSUE head (final surface). Widths = spec neutral anchors incl. tissue.
TISSUE_KEYS = [
    # y,     hw,    top,    bot,    p,   arch,  flat
    dict(y= 0.500, hw=0.047, top= 0.052, bot=-0.052, p=2.6, arch=0.00, flat=0.0),
    dict(y= 0.470, hw=0.055, top= 0.058, bot=-0.066, p=3.0, arch=0.00, flat=0.25),
    dict(y= 0.430, hw=0.064, top= 0.066, bot=-0.082, p=3.2, arch=0.00, flat=0.35),
    dict(y= 0.380, hw=0.072, top= 0.074, bot=-0.094, p=3.2, arch=0.00, flat=0.40),
    dict(y= 0.320, hw=0.084, top= 0.086, bot=-0.106, p=3.0, arch=0.00, flat=0.45),
    dict(y= 0.260, hw=0.092, top= 0.090, bot=-0.110, p=2.9, arch=0.01, flat=0.50),
    dict(y= 0.200, hw=0.099, top= 0.096, bot=-0.108, p=2.8, arch=0.03, flat=0.55),
    dict(y= 0.165, hw=0.105, top= 0.087, bot=-0.110, p=2.8, arch=0.05, flat=0.30),  # STOP dip
    dict(y= 0.120, hw=0.117, top= 0.106, bot=-0.112, p=2.7, arch=0.075, flat=0.55),
    dict(y= 0.060, hw=0.136, top= 0.130, bot=-0.112, p=2.6, arch=0.108, flat=0.65),
    dict(y= 0.020, hw=0.151, top= 0.144, bot=-0.110, p=2.5, arch=0.130, flat=0.70),  # arch peak ~t=0.48 (puma)
    dict(y=-0.040, hw=0.155, top= 0.156, bot=-0.104, p=2.5, arch=0.128, flat=0.70),
    dict(y=-0.120, hw=0.160, top= 0.164, bot=-0.096, p=2.5, arch=0.095, flat=0.65),
    dict(y=-0.200, hw=0.176, top= 0.168, bot=-0.088, p=2.4, arch=0.030, flat=0.60),  # braincase 0.352
    dict(y=-0.300, hw=0.170, top= 0.158, bot=-0.080, p=2.4, arch=0.00, flat=0.50),
    dict(y=-0.400, hw=0.148, top= 0.134, bot=-0.070, p=2.3, arch=0.00, flat=0.35),
    dict(y=-0.470, hw=0.112, top= 0.098, bot=-0.054, p=2.2, arch=0.00, flat=0.15),
    dict(y=-0.500, hw=0.070, top= 0.062, bot=-0.038, p=2.2, arch=0.00, flat=0.0),
]
# SKULL = tissue reduced by per-region soft-tissue thickness (documented in notes)
SKULL_KEYS = []
for k in TISSUE_KEYS:
    s = dict(k)
    s['hw'] = k['hw'] - (0.016 if k['y'] > 0.15 else 0.011)
    s['top'] = k['top'] - 0.009
    s['bot'] = k['bot'] + 0.010
    s['arch'] = k['arch']*0.82
    SKULL_KEYS.append(s)
# post-brow frontal dip in the BONE only (felid frontal depression — the
# "shelf and shadow" brow read, brow-study.md SS2): tissue fills most of it
for _k in SKULL_KEYS:
    if 0.09 < _k['y'] < 0.20: _k['top'] -= 0.003

EYE = (0.106, 0.085, 0.040)   # eye centre (x one side), seated INSIDE the surface; orbit dia spec 0.15
EYE_R = 0.050

def displacement_passes(verts, stations):
    # returns displaced verts for tissue head: sockets, rims, brow, temporalis, cheek pads, mouth crease
    out = []
    zc = {round(st['y'],4): (st['top']+st['bot'])/2 for st in stations}
    ys_sorted = sorted(zc.keys())
    def centre_z(y):
        # nearest station centre
        best = min(ys_sorted, key=lambda yy: abs(yy-y))
        return zc[best]
    for (x, y, z) in verts:
        px, py, pz = x, y, z
        radial = Vector((x, 0, z-centre_z(y)))
        rl = radial.length
        rn = radial/rl if rl > 1e-6 else Vector((0,0,1))
        disp = 0.0
        for sgn in (1,-1):
            E = Vector((sgn*EYE[0], EYE[1], EYE[2]))
            d = (Vector((px,py,pz)) - E).length
            if d < 0.088:  # socket bowl (deepened: the ball centre sits inside the surface)
                disp -= 0.020 * (1 - (d/0.088)**2)
            elif d < 0.118:  # orbital rim
                disp += 0.005 * gauss(d-0.098, 0.010)
            # brow pad (tissue over the supraorbital shelf; BrowPadding +6 on
            # the brow-study scale ~ a 6mm-class increment, NOT a lump — the
            # animal brow read is shelf + shadow, projection is NEGATIVE)
            B = Vector((sgn*0.104, 0.140, 0.098))
            disp += 0.006 * gauss((Vector((px,py,pz))-B).length, 0.052)
            # temporalis pad
            T = Vector((sgn*0.148, -0.150, 0.058))
            disp += 0.011 * gauss((Vector((px,py,pz))-T).length, 0.078)
            # cheek fat pad over arch (broad and low — a fin here reads "manta")
            C = Vector((sgn*0.205, -0.005, -0.018))
            disp += 0.011 * gauss((Vector((px,py,pz))-C).length, 0.085)
        px += rn.x*disp; pz += rn.z*disp
        # mouth crease: subtle lift+pinch along mouth line
        mz = -0.060 - 0.012*sstep(0.45, 0.0, y)
        if 0.0 < y < 0.45 and abs(z-mz) < 0.013 and abs(x) < 0.10:
            w = (1-abs(z-mz)/0.013) * sstep(0.0, 0.06, y) * sstep(0.45, 0.38, y)
            pz += 0.004*w; px *= (1-0.05*w)
        out.append((px, py, pz))
    return out

# ---------------------------------------------------------------- jaw (U-trough loft)
JAW_KEYS = [
    # y,     hw,    rim,    floor,  bot
    dict(y= 0.440, hw=0.060, top=-0.050, bot=-0.106, p=2.2, arch=0, flat=0),
    dict(y= 0.380, hw=0.070, top=-0.052, bot=-0.112, p=2.2, arch=0, flat=0),
    dict(y= 0.300, hw=0.078, top=-0.054, bot=-0.114, p=2.2, arch=0, flat=0),
    dict(y= 0.200, hw=0.084, top=-0.056, bot=-0.118, p=2.2, arch=0, flat=0),
    dict(y= 0.100, hw=0.090, top=-0.056, bot=-0.120, p=2.2, arch=0, flat=0),
    dict(y= 0.000, hw=0.098, top=-0.054, bot=-0.122, p=2.2, arch=0, flat=0),
    dict(y=-0.100, hw=0.118, top=-0.048, bot=-0.132, p=2.2, arch=0, flat=0),
    dict(y=-0.180, hw=0.140, top= 0.005, bot=-0.150, p=2.2, arch=0, flat=0),
    dict(y=-0.240, hw=0.172, top= 0.082, bot=-0.132, p=2.2, arch=0, flat=0),
    dict(y=-0.285, hw=0.192, top= 0.108, bot=-0.118, p=2.2, arch=0, flat=0),  # condyle flare
]
def jaw_profile(hw, rim, bot, wall=0.017, floor_drop=0.020):
    # closed loop: outer surface (left rim -> bottom -> right rim), rim step in, inner wall down to floor, floor across, up.
    pts = []
    # outer: parametrize by angle from rim-left around bottom to rim-right (through bottom)
    NO = 13
    for i in range(NO):
        u = i/(NO-1)  # 0..1
        ang = math.pi*u  # 0 at left rim going under
        x = -hw*math.cos(ang)
        z = rim - (rim-bot)*math.sin(ang)**0.8
        pts.append((x, z))
    # inner right wall
    iw = hw-wall
    floor = rim - floor_drop - (rim-bot)*0.55  # floor sits above bottom inner
    floor = max(floor, bot+wall)
    pts.append((iw, rim))
    pts.append((iw, floor+0.012))
    NI = 7
    for i in range(NI):
        u = i/(NI-1)
        pts.append((iw - 2*iw*u, floor))
    pts.append((-iw, floor+0.012))
    pts.append((-iw, rim))
    return pts

def build_jaw():
    chans = ['hw','top','bot']
    ys = [k['y'] for k in JAW_KEYS]
    n_st = 40
    stations = []
    for i in range(n_st):
        y = ys[0] + (ys[-1]-ys[0])*i/(n_st-1)
        st = {c: catmull([(k['y'], k[c]) for k in JAW_KEYS], y) for c in chans}
        st['y'] = y
        stations.append(st)
    verts, faces = [], []
    prof0 = jaw_profile(stations[0]['hw'], stations[0]['top'], stations[0]['bot'])
    NP = len(prof0)
    for st in stations:
        prof = jaw_profile(st['hw'], st['top'], st['bot'])
        # masseter bulge on outer wall points near angle
        for (x, z) in prof:
            bx = x
            if abs(x) > st['hw']*0.8:
                bx += math.copysign(0.016*gauss(st['y']+0.13, 0.07)*gauss(z+0.085, 0.05), x)
            verts.append((bx, st['y'], z))
    for i in range(n_st-1):
        for j in range(NP):
            j1 = (j+1) % NP
            faces.append((i*NP+j, i*NP+j1, (i+1)*NP+j1, (i+1)*NP+j))
    # caps: fan across profile centroid (front/back)
    for idx, st in ((0, stations[0]), (n_st-1, stations[-1])):
        prof = jaw_profile(st['hw'], st['top'], st['bot'])
        cx = sum(p[0] for p in prof)/NP; cz = sum(p[1] for p in prof)/NP
        ci = len(verts); verts.append((cx, st['y'] + (0.012 if idx==0 else -0.012), cz))
        base = idx*NP
        for j in range(NP):
            j1 = (j+1) % NP
            faces.append((ci, base+j1, base+j) if idx == 0 else (ci, base+j, base+j1))
    return verts, faces

# ---------------------------------------------------------------- ears (lens cross-section loft)
def build_ear(sign):
    # local frame: t along ear length (0 base -> 1 tip), lofted then transformed
    keys = [  # t, halfW, frontD, backD, xoff (tip drift out), zoff
        (0.00, 0.065, 0.026, 0.016, 0.00),
        (0.15, 0.088, 0.034, 0.020, 0.00),
        (0.35, 0.098, 0.036, 0.021, 0.01),
        (0.55, 0.086, 0.033, 0.019, 0.02),
        (0.75, 0.062, 0.027, 0.016, 0.03),
        (0.90, 0.034, 0.019, 0.012, 0.04),
        (1.00, 0.004, 0.004, 0.003, 0.05),
    ]
    NP = 20
    LEN = 0.40
    n_st = 14
    verts, faces = [], []
    for i in range(n_st):
        t = i/(n_st-1)
        hw = catmull([(k[0], k[1]) for k in keys], t)
        fd = catmull([(k[0], k[2]) for k in keys], t)
        bd = catmull([(k[0], k[3]) for k in keys], t)
        xo = catmull([(k[0], k[4]) for k in keys], t)
        for j in range(NP):
            a = 2*math.pi*j/NP
            ca, sa = math.cos(a), math.sin(a)
            lx = hw*math.copysign(abs(sa)**0.85, sa)
            ly = (fd if ca >= 0 else bd)*math.copysign(abs(ca)**0.9, ca)
            # inner-ear dish: push front-centre verts back
            if ly > 0:
                dish = 0.013 * gauss(lx, hw*0.55) * sstep(0.10, 0.30, t) * sstep(1.0, 0.8, t)
                ly -= dish
            verts.append((lx, ly, t*LEN, xo))
    # transform: base at (sign*0.100, -0.155, 0.128); dir up, cant out 14deg, tilt back 7deg
    import mathutils
    R = Matrix.Rotation(math.radians(-7), 4, 'X') @ Matrix.Rotation(math.radians(sign*14), 4, 'Y')
    base = Vector((sign*0.100, -0.155, 0.128))
    out = []
    for (lx, ly, lz, xo) in verts:
        v = Vector((sign*(lx+xo), ly, lz))
        v = R @ v + base
        out.append(tuple(v))
    for i in range(n_st-1):
        for j in range(NP):
            j1 = (j+1) % NP
            quad = (i*NP+j, i*NP+j1, (i+1)*NP+j1, (i+1)*NP+j)
            faces.append(quad if sign > 0 else (quad[0], quad[3], quad[2], quad[1]))
    # tip cap
    ci = len(out); out.append(tuple(R @ Vector((sign*0.05, 0, LEN+0.004)) + base))
    base_i = (n_st-1)*NP
    for j in range(NP):
        j1 = (j+1) % NP
        faces.append((ci, base_i+j, base_i+j1) if sign > 0 else (ci, base_i+j1, base_i+j))
    return out, faces

print("script part 1 loaded")

# ---------------------------------------------------------------- primitive helpers
def ellipsoid(name, centre, scale, rot_euler=(0,0,0), subdiv=3):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0, location=centre)
    ob = bpy.context.object; ob.name = name
    ob.scale = scale; ob.rotation_euler = rot_euler
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return ob

def torus(name, centre, major, minor, rot_euler=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=28, minor_segments=10, location=centre)
    ob = bpy.context.object; ob.name = name; ob.rotation_euler = rot_euler
    return ob

def cone(name, centre, r1, r2, depth, rot_euler=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=r1, radius2=r2, depth=depth, location=centre)
    ob = bpy.context.object; ob.name = name; ob.rotation_euler = rot_euler
    return ob

def box(name, centre, scale, rot_euler=(0,0,0), subdiv=0):
    bpy.ops.mesh.primitive_cube_add(location=centre)
    ob = bpy.context.object; ob.name = name
    ob.scale = (scale[0]/2, scale[1]/2, scale[2]/2); ob.rotation_euler = rot_euler
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if subdiv:
        mod = ob.modifiers.new('s', 'SUBSURF'); mod.levels = subdiv
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob

def tube(name, points, radius, mat=None):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = 3
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co; bp.handle_left_type = 'AUTO'; bp.handle_right_type = 'AUTO'
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob.select_set(False)
    return ob

def join_objects(name, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    return ob

def smooth_obj(ob, iterations=2, factor=0.5):
    me = ob.data
    # simple laplacian via neighbour averaging on vertex coords
    adj = {}
    for e in me.edges:
        a, b = e.vertices
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    for _ in range(iterations):
        newc = []
        for i, v in enumerate(me.vertices):
            ns = adj.get(i, [])
            if not ns: newc.append(v.co); continue
            avg = Vector((0,0,0))
            for j in ns: avg += me.vertices[j].co
            avg /= len(ns)
            newc.append(v.co.lerp(avg, factor))
        for i, co in enumerate(newc): me.vertices[i].co = co
    me.update()

# ---------------------------------------------------------------- build
clean_scene()
MAT_TISSUE = material('TissueClay', (0.60, 0.53, 0.485), rough=0.62, subsurface=0.28)
MAT_TISSUE_D = material('TissueClayDark', (0.52, 0.45, 0.41), rough=0.6, subsurface=0.25)
MAT_BONE = material('Bone', (0.86, 0.82, 0.74), rough=0.55, subsurface=0.05)
MAT_MUSCLE = material('Muscle', (0.44, 0.13, 0.11), rough=0.48, subsurface=0.2)
MAT_NOSE = material('NoseLeather', (0.15, 0.115, 0.11), rough=0.32, spec=0.7)
MAT_TEETH = material('Teeth', (0.92, 0.89, 0.82), rough=0.32, spec=0.6)
MAT_TONGUE = material('Tongue', (0.54, 0.29, 0.31), rough=0.42, subsurface=0.3)
MAT_DARK = material('MouthDark', (0.07, 0.045, 0.045), rough=0.9)
MAT_EYE = material('Eyeball', (0.88, 0.86, 0.82), rough=0.14, spec=0.9)
MAT_IRIS = material('Iris', (0.16, 0.09, 0.045), rough=0.12, spec=0.9)

# ---- SKULL layer
sv, sf, sstations = loft('Skull', SKULL_KEYS, 48, 64)
skull = make_mesh('Skull', sv, sf); assign_mat(skull, MAT_BONE)
arch_parts = []
for sgn in (1,-1):
    pts = [(sgn*0.108, 0.115, -0.012), (sgn*0.205, 0.03, -0.006), (sgn*0.232, -0.05, -0.002), (sgn*0.185, -0.16, 0.004), (sgn*0.138, -0.235, 0.01)]
    arch_parts.append(tube('ZygArch', pts, 0.0155))
nasal = box('NasalBone', (0, 0.335, 0.0835), (0.062, 0.26, 0.012), rot_euler=(math.radians(-4), 0, 0), subdiv=1)
# SUPRAORBITAL SHELF (brow, BONE layer — brow-study.md SS6.1): canids/felids
# have NO supraorbital torus; every species BrowProjection vector is NEGATIVE
# (-20..-45, neutral midpoint ~-31 vs modern human 0, Neanderthal +56..+100,
# gorilla +150). The bone brow here is only a modest shelf — a frontal-sinus
# eminence bar sitting mostly INSIDE the frontal, ledging a few mm proud on
# the brow slope; the visible brow read = shelf shadow + muscle + padding.
# The torus range belongs to humanoid bases' bone layers, not this neutral.
shelf = ellipsoid('SupraorbitalShelf', (0, 0.140, 0.070), (0.118, 0.034, 0.012), subdiv=2)
glabella = ellipsoid('Glabella', (0, 0.140, 0.074), (0.026, 0.022, 0.010), subdiv=2)
skull_all = join_objects('Skull', [skull] + arch_parts + [nasal, shelf, glabella]); assign_mat(skull_all, MAT_BONE)
# skull mandible (bone reference, closed pose)
jv, jf = build_jaw()
skull_mand = make_mesh('SkullMandible', [(x*0.94, y, z+0.012) for (x,y,z) in jv], jf)
assign_mat(skull_mand, MAT_BONE)

# ---- MUSCLE layer
mus = []
for sgn in (1,-1):
    mus.append(ellipsoid('Temporalis', (sgn*0.140, -0.140, 0.052), (0.050, 0.100, 0.085), rot_euler=(0, 0, sgn*math.radians(-8))))
    mus.append(ellipsoid('Masseter', (sgn*0.138, -0.148, -0.080), (0.040, 0.072, 0.060), rot_euler=(math.radians(12), 0, sgn*math.radians(10))))
    mus.append(ellipsoid('Buccinator', (sgn*0.128, 0.015, -0.042), (0.018, 0.082, 0.052)))
    # zygomaticus: strap from arch to mouth corner
    a = Vector((sgn*0.205, -0.02, -0.008)); b = Vector((sgn*0.072, 0.155, -0.052))
    mid = (a+b)/2; d = (b-a); length = d.length
    ob = ellipsoid('Zygomaticus', tuple(mid), (0.014, 0.014, length/2))
    ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = d.to_track_quat('Z', 'Y'); mus.append(ob)
    mus.append(torus('OrbOculi', (sgn*EYE[0], EYE[1], EYE[2]), 0.054, 0.011, rot_euler=(math.radians(75), sgn*math.radians(-18), 0)))
    # corrugator supercilii: measured 29.2mm long x 12.6mm wide x 1.62mm thick
    # (brow-study SS4) — expression, not mass; a thin diagonal slip
    mus.append(ellipsoid('Corrugator', (sgn*0.045, 0.148, 0.090), (0.030, 0.070, 0.005), rot_euler=(0, sgn*math.radians(28), sgn*math.radians(-20))))
mus.append(ellipsoid('Frontalis', (0, 0.110, 0.096), (0.095, 0.065, 0.010)))  # thin sheet over the frontal
mus.append(torus('OrbOris', (0, 0.432, -0.026), 0.050, 0.015, rot_euler=(math.radians(90), 0, 0)))
muscles = join_objects('Muscles', mus); assign_mat(muscles, MAT_MUSCLE)
for p in muscles.data.polygons: p.use_smooth = True

# ---- TISSUE head (deliverable)
tv, tf, tstations = loft('TissueHead', TISSUE_KEYS, 60, 80)
tv = displacement_passes(tv, tstations)
head = make_mesh('TissueHead', tv, tf); assign_mat(head, MAT_TISSUE)
HINGE = Vector((0, -0.245, -0.026))

# ---- JAW (tissue, U-trough)
jv2, jf2 = build_jaw()
jaw = make_mesh('Jaw', jv2, jf2); assign_mat(jaw, MAT_TISSUE)
jaw.rotation_mode = 'AXIS_ANGLE'
# note: jaw posed at render time via matrix around HINGE (object origin stays world origin; posing done in render fn)

# ---- EARS
ear_objs = []
for sgn, nm in ((1, 'Ear_L'), (-1, 'Ear_R')):
    ev, ef = build_ear(sgn)
    eo = make_mesh(nm, ev, ef); assign_mat(eo, MAT_TISSUE); ear_objs.append(eo)

# ---- EYES + LIDS
eye_objs, lid_objs = [], []
for sgn, nm in ((1, 'L'), (-1, 'R')):
    C = Vector((sgn*EYE[0], EYE[1], EYE[2]))
    ball = ellipsoid('Eyeball_'+nm, tuple(C), (EYE_R, EYE_R, EYE_R), subdiv=3)
    assign_mat(ball, MAT_EYE); eye_objs.append(ball)
    axis = Vector((sgn*0.35, 0.55, 0.25)).normalized()  # outward-forward-up gaze axis of the orbit
    # iris cap: sits PROUD of the ball surface so it actually reads
    iris = ellipsoid('Iris_'+nm, tuple(C + axis*(EYE_R*0.96)), (0.023, 0.023, 0.010))
    iris.rotation_mode = 'QUATERNION'; iris.rotation_quaternion = axis.to_track_quat('Z', 'Y')
    assign_mat(iris, MAT_IRIS); eye_objs.append(iris)
    pupil = ellipsoid('Pupil_'+nm, tuple(C + axis*(EYE_R*1.00)), (0.0105, 0.0105, 0.006))
    pupil.rotation_mode = 'QUATERNION'; pupil.rotation_quaternion = axis.to_track_quat('Z', 'Y')
    assign_mat(pupil, MAT_DARK); eye_objs.append(pupil)
    # lid shell: sphere r*1.07 with front cap (within 52deg of axis) removed
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=18, radius=EYE_R*1.07, location=tuple(C))
    lid = bpy.context.object; lid.name = 'Eyelid_'+nm
    me = lid.data
    keep = []
    for p in me.polygons:
        d = (p.center - C)
        if d.length > 1e-6 and d.normalized().dot(axis) > math.cos(math.radians(52)):
            continue
        keep.append(p.index)
    bpy.ops.object.select_all(action='DESELECT'); lid.select_set(True)
    bpy.context.view_layer.objects.active = lid
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons:
        p.select = p.index not in keep
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.delete(type='FACE'); bpy.ops.object.mode_set(mode='OBJECT')
    for p in me.polygons: p.use_smooth = True
    assign_mat(lid, MAT_TISSUE_D); lid_objs.append(lid)
    # lid margin torus at opening
    marg = torus('LidMargin_'+nm, tuple(C + axis*(EYE_R*1.07*math.cos(math.radians(52)))), EYE_R*1.07*math.sin(math.radians(52)), 0.0062)
    marg.rotation_mode = 'QUATERNION'; marg.rotation_quaternion = axis.to_track_quat('Z', 'Y')
    assign_mat(marg, MAT_TISSUE_D); lid_objs.append(marg)

# ---- NOSE LEATHER: defined form on the muzzle tip
nose = ellipsoid('NoseLeather', (0, 0.487, 0.012), (0.042, 0.026, 0.034), subdiv=3)
# nostril bumps + philtrum: pinch centre bottom via vertex tweak
for v in nose.data.vertices:
    if v.co.z < -0.012 and abs(v.co.x) < 0.012 and v.co.y > 0.008:
        v.co.z += 0.010  # philtrum groove lift
    if abs(abs(v.co.x) - 0.030) < 0.010 and v.co.y > 0.006 and v.co.z < 0.0:
        v.co.y += 0.004  # nostril wing swell
assign_mat(nose, MAT_NOSE)

# ---- TEETH + TONGUE + THROAT
up = []
for sgn in (1,-1):
    up.append(cone('CanineU', (sgn*0.053, 0.330, -0.090), 0.0115, 0.002, 0.040, rot_euler=(math.pi, 0, sgn*math.radians(5))))
    for i, yy in enumerate((0.245, 0.180, 0.118)):
        up.append(box('CheekU', (sgn*0.060, yy, -0.088), (0.020, 0.026, 0.020), subdiv=1))
for i, xx in enumerate((-0.027, -0.009, 0.009, 0.027)):
    up.append(box('IncisorU', (xx, 0.418, -0.086), (0.015, 0.014, 0.020), subdiv=1))
teeth_up = join_objects('TeethUpper', up); assign_mat(teeth_up, MAT_TEETH)
lo = []
for sgn in (1,-1):
    lo.append(cone('CanineL', (sgn*0.049, 0.312, -0.052), 0.010, 0.002, 0.046))
    for i, yy in enumerate((0.235, 0.175)):
        lo.append(box('CheekL', (sgn*0.056, yy, -0.066), (0.018, 0.024, 0.016), subdiv=1))
for i, xx in enumerate((-0.024, -0.008, 0.008, 0.024)):
    lo.append(box('IncisorL', (xx, 0.408, -0.062), (0.013, 0.012, 0.016), subdiv=1))
teeth_lo = join_objects('TeethLower', lo); assign_mat(teeth_lo, MAT_TEETH)
tongue = box('Tongue', (0, 0.265, -0.052), (0.068, 0.235, 0.020), subdiv=3)
# round the tongue: pull edges down slightly
for v in tongue.data.vertices:
    v.co.z -= 0.010*(abs(v.co.x)/0.034)**2
    v.co.z += 0.006*gauss(v.co.y-0.265, 0.07)
assign_mat(tongue, MAT_TONGUE)
throat = ellipsoid('Throat', (0, 0.015, -0.045), (0.082, 0.030, 0.075), subdiv=2)
assign_mat(throat, MAT_DARK)
neck = torus('NeckSocket', (0, -0.440, -0.030), 0.088, 0.015, rot_euler=(math.radians(115), 0, 0))
assign_mat(neck, MAT_TISSUE_D)
socket_disc = ellipsoid('NeckSocketDisc', (0, -0.452, -0.038), (0.086, 0.026, 0.086), subdiv=2)
assign_mat(socket_disc, MAT_DARK)

print("build part 2 done")

# ---------------------------------------------------------------- vertex groups (spec's 20)
def add_group(ob, name, weights):
    vg = ob.vertex_groups.new(name=name)
    for i, w in enumerate(weights):
        if w > 0.001:
            vg.add([i], min(1.0, w), 'REPLACE')
    return vg

groups_export = {}
def collect_groups(ob):
    d = {}
    for vg in ob.vertex_groups:
        idx = []
        for v in ob.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.001:
                    idx.append(v.index)
        d[vg.name] = idx
    groups_export[ob.name] = d

hw_list = []
for v in head.data.vertices:
    x, y, z = v.co
    hw_list.append((x, y, z))
W = {}
W['Muzzle'] = [sstep(0.02, 0.165, y) for (x,y,z) in hw_list]
W['MuzzleTip'] = [sstep(0.36, 0.46, y) for (x,y,z) in hw_list]
W['NoseLeather'] = [sstep(0.44, 0.495, y)*sstep(-0.035, 0.005, z) for (x,y,z) in hw_list]
W['MuzzleBridge'] = [sstep(0.15, 0.22, y)*(1-sstep(0.42, 0.50, y))*sstep(0.015, 0.05, z) for (x,y,z) in hw_list]
W['Cranium'] = [1-sstep(0.02, 0.12, y) for (x,y,z) in hw_list]
W['CraniumDome'] = [(1-sstep(-0.02, 0.08, y))*sstep(0.06, 0.105, z) for (x,y,z) in hw_list]
for nm, sgn, C in (('CheekL', 1, (0.235,-0.01,-0.01)), ('CheekR', -1, (-0.235,-0.01,-0.01))):
    W[nm] = [max(gauss((Vector((x,y,z))-Vector(C)).length, 0.105),
                 0.8*gauss((Vector((x,y,z))-Vector((C[0]*0.82, -0.145, -0.05))).length, 0.09)) for (x,y,z) in hw_list]
for nm, sgn in (('BrowL', 1), ('BrowR', -1)):
    W[nm] = [gauss((Vector((x,y,z))-Vector((sgn*0.112, 0.150, 0.112))).length, 0.060) for (x,y,z) in hw_list]
for nm, sgn in (('EyeSocketL', 1), ('EyeSocketR', -1)):
    W[nm] = [gauss((Vector((x,y,z))-Vector((sgn*EYE[0], EYE[1], EYE[2]))).length - 0.098, 0.030) for (x,y,z) in hw_list]
for nm, ws in W.items(): add_group(head, nm, ws)
collect_groups(head)

for eo, sgn in zip(ear_objs, (1,-1)):
    base = Vector((sgn*0.100, -0.155, 0.128))
    ds = [(v.co - base).length for v in eo.data.vertices]
    add_group(eo, 'Ear' + ('_L' if sgn > 0 else '_R'), [1.0]*len(ds))
    add_group(eo, 'EarBase' + ('_L' if sgn > 0 else '_R'), [1-sstep(0.03, 0.15, d) for d in ds])
    add_group(eo, 'EarTip' + ('_L' if sgn > 0 else '_R'), [sstep(0.23, 0.35, d) for d in ds])
    collect_groups(eo)

add_group(jaw, 'Jaw', [1.0]*len(jaw.data.vertices))
add_group(jaw, 'Chin', [sstep(0.33, 0.42, v.co.y) for v in jaw.data.vertices])
collect_groups(jaw)
json.dump(groups_export, open(os.path.join(OUT, 'neutral_base_head_v2.groups.json'), 'w'), indent=0)

# ---------------------------------------------------------------- proportions
def sl_width(ob, y0, y1, zmin=None):
    xs = [v.co.x for v in ob.data.vertices if y0 <= v.co.y <= y1 and (zmin is None or v.co.z >= zmin)]
    return (max(xs)-min(xs)) if xs else 0.0

hv = [v.co for v in head.data.vertices]
L_meas = max(v.y for v in hv) - min(v.y for v in hv)
props = {}
def ratio(name, val, target):
    props[name] = {'measured': round(val, 3), 'target': target, 'dev_pct': round(100*(val-target)/target, 1)}
ratio('Length_L', L_meas, 1.0)
ratio('CheekWidth_ZB', sl_width(head, -0.10, 0.08)/L_meas, 0.58)
ratio('CraniumWidth', sl_width(head, -0.26, -0.15, zmin=0.045)/L_meas, 0.36)
ratio('MuzzleWidth_rostrum', sl_width(head, 0.31, 0.33)/L_meas, 0.17)
zs32 = [v.z for v in hv if 0.31 <= v.y <= 0.33]
ratio('MuzzleDepth', (max(zs32)-min(zs32))/L_meas, 0.20)
ratio('SkullHeight_head_plus_jaw', (max(v.z for v in hv) - min(v.co.z for v in jaw.data.vertices))/L_meas, 0.31)
jv_all = [v.co for v in jaw.data.vertices]
ratio('JawLength', (max(v.y for v in jv_all)-min(v.y for v in jv_all))/L_meas, 0.74)
ratio('JawWidth', (max(v.x for v in jv_all)-min(v.x for v in jv_all))/L_meas, 0.40)
ratio('JawDepth_ramus', (max(v.z for v in jv_all)-min(v.z for v in jv_all))/L_meas, 0.28)
earL = ear_objs[0]
base_e = Vector((0.100, -0.155, 0.128))
ear_len = max((v.co-base_e).length for v in earL.data.vertices)
ratio('EarHeight', ear_len/L_meas, 0.40)
ear_w = sl_width(earL, -10, 10)
ratio('EarWidth_over_EarLength', ear_w/ear_len, 0.55)
# NB: the spec's 0.15 is the ORBIT diameter. Orbit opening estimated from the
# tissue rim ring (r 0.098 about the eye centre); eyeball reported raw.
ratio('OrbitOpening_est', 2*0.098/L_meas, 0.15)
props['EyeballDiameter'] = {'measured': round(2*EYE_R/L_meas, 3), 'target': None, 'dev_pct': None}
ratio('EyeCentreSpacing', 2*EYE[0]/L_meas, 0.34)
nose_w = max(v.co.x for v in nose.data.vertices) - min(v.co.x for v in nose.data.vertices)
ratio('NoseWidth_over_MuzzleWidth', nose_w/(sl_width(head, 0.31, 0.33)), 0.55)
json.dump(props, open(os.path.join(OUT, 'proportions.json'), 'w'), indent=1)
print('PROPORTIONS:', json.dumps(props))

# ---------------------------------------------------------------- renders
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.resolution_x = 950; scene.render.resolution_y = 950
world = bpy.data.worlds.new('W'); scene.world = world
env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(os.path.expanduser('~/workspace/bodies-3d/parts-library/polyhaven/photo-studio-01-hdri/photo_studio_01_2k.hdr'))
bg = world.node_tree.nodes['Background']
world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.85
# camera rays see a plain studio grey; the HDRI only lights the subject
bg2 = world.node_tree.nodes.new('ShaderNodeBackground')
bg2.inputs['Color'].default_value = (0.145, 0.145, 0.15, 1.0)
bg2.inputs['Strength'].default_value = 1.0
lp = world.node_tree.nodes.new('ShaderNodeLightPath')
mix = world.node_tree.nodes.new('ShaderNodeMixShader')
wo = world.node_tree.nodes['World Output']
world.node_tree.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
world.node_tree.links.new(bg.outputs['Background'], mix.inputs[1])
world.node_tree.links.new(bg2.outputs['Background'], mix.inputs[2])
world.node_tree.links.new(mix.outputs['Shader'], wo.inputs['Surface'])

cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 82
cam = bpy.data.objects.new('Cam', cam_data); scene.collection.objects.link(cam)
scene.camera = cam
def look_at(obj, target):
    d = target - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
def shoot(name, pos, target=Vector((0, -0.01, 0.0))):
    cam.location = pos; look_at(cam, target)
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

FINAL_SET = [head, jaw, teeth_lo, tongue] + ear_objs + eye_objs + lid_objs + [nose, teeth_up, throat, neck, socket_disc]
REF_SET = [skull_all, skull_mand, muscles]
def set_render(objs, show):
    for o in objs: o.hide_render = not show
def pose_jaw(angle):
    M = Matrix.Translation(HINGE) @ Matrix.Rotation(angle, 4, 'X') @ Matrix.Translation(-HINGE)
    for o in (jaw, teeth_lo, tongue):
        o.matrix_world = M
def unpose():
    for o in (jaw, teeth_lo, tongue):
        o.matrix_world = Matrix.Identity(4)

set_render(REF_SET, False); set_render(FINAL_SET, True)
unpose()
shoot('render_front.png', Vector((0, 2.1, 0.10)), Vector((0, -0.01, 0.05)))
shoot('render_side.png', Vector((2.1, 0.0, 0.06)), Vector((0, -0.01, 0.02)))
pose_jaw(math.radians(-21))
shoot('render_threequarter.png', Vector((1.35, 1.45, 0.62)), Vector((0, -0.01, 0.03)))
unpose()
# layers view: skull + muscles visible, tissue hidden
set_render(FINAL_SET, False); set_render(REF_SET, True)
shoot('render_layers.png', Vector((1.35, 1.45, 0.62)))
set_render(REF_SET, False); set_render(FINAL_SET, True)

if FINAL:
    bpy.ops.object.select_all(action='DESELECT')
    for o in FINAL_SET: o.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'neutral_base_head_v2.glb'), export_format='GLB', use_selection=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'neutral_base_head_v2.blend'))
print('DONE')
