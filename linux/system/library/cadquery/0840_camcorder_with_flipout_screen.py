# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

from __future__ import annotations

import cadquery as cq
import math

# ===== shim core =====
def _rpy_R(r, p, y):
    """Rotation matrix Rz(yaw)@Ry(pitch)@Rx(roll) as rows (URDF convention)."""
    cr, sr = math.cos(r), math.sin(r)
    cp, sp = math.cos(p), math.sin(p)
    cy, sy = math.cos(y), math.sin(y)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp,     cp * sr,                cp * cr),
    )

def _mat_mul(A, B):
    return tuple(
        tuple(sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )

def _mat_vec(A, v):
    return tuple(sum(A[i][k] * v[k] for k in range(3)) for i in range(3))

class _Tf:
    """Rigid transform: rotation matrix R (rows) + translation t."""
    __slots__ = ("R", "t")
    _I = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def __init__(self, R=None, t=(0.0, 0.0, 0.0)):
        self.R = R if R is not None else _Tf._I
        self.t = (float(t[0]), float(t[1]), float(t[2]))

    @staticmethod
    def from_origin(origin):
        if origin is None:
            return _Tf()
        xyz = getattr(origin, "xyz", (0.0, 0.0, 0.0))
        rpy = getattr(origin, "rpy", (0.0, 0.0, 0.0))
        return _Tf(_rpy_R(rpy[0], rpy[1], rpy[2]), xyz)

    def __matmul__(self, o):
        return _Tf(_mat_mul(self.R, o.R),
                   tuple(a + b for a, b in zip(_mat_vec(self.R, o.t), self.t)))

    def location(self):
        R, t = self.R, self.t
        xdir = cq.Vector(R[0][0], R[1][0], R[2][0])
        zdir = cq.Vector(R[0][2], R[1][2], R[2][2])
        return cq.Location(cq.Plane(origin=cq.Vector(*t), xDir=xdir, normal=zdir))

class ValidationError(ValueError):
    pass

class ArticulationType:
    REVOLUTE = "revolute"
    CONTINUOUS = "continuous"
    PRISMATIC = "prismatic"
    FIXED = "fixed"
    FLOATING = "floating"

class Origin:
    __slots__ = ("xyz", "rpy")

    def __init__(self, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)):
        self.xyz = (float(xyz[0]), float(xyz[1]), float(xyz[2]))
        self.rpy = (float(rpy[0]), float(rpy[1]), float(rpy[2]))

class Material:
    def __init__(self, name, rgba=None, texture=None, *, color=None):
        self.name = str(name)
        c = rgba if rgba is not None else color
        if c is not None:
            c = tuple(float(v) for v in c)
            if len(c) == 3:
                c = c + (1.0,)
        self.rgba = c
        self.texture = texture

class MotionLimits:
    def __init__(self, effort=1.0, velocity=1.0, lower=None, upper=None):
        self.effort = float(effort)
        self.velocity = float(velocity)
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)

def _to_shape(model):
    """Coerce a cadquery object (Workplane/Shape/Assembly) or a shim geometry
    wrapper into a single cq.Shape."""
    if isinstance(model, _CQMesh):
        return model.shape
    if hasattr(model, "_cq"):
        return model._cq()
    if isinstance(model, cq.Assembly):
        return model.toCompound()
    if isinstance(model, cq.Workplane):
        vals = [v for v in model.vals() if isinstance(v, cq.Shape)]
        if not vals:
            raise ValidationError("cadquery Workplane has no shape values")
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    if isinstance(model, cq.Shape):
        return model
    raise ValidationError("unsupported cadquery model type: %r" % type(model))

class _CQMesh:
    """Mesh stand-in that simply carries an exact cadquery B-rep shape."""
    __slots__ = ("shape", "name")

    def __init__(self, shape, name=None):
        self.shape = shape
        self.name = name

    def _cq(self):
        return self.shape

def mesh_from_cadquery(model, name=None, **kwargs):
    return _CQMesh(_to_shape(model), name=name if isinstance(name, str) else None)

class Visual:
    __slots__ = ("geometry", "origin", "material", "name")

    def __init__(self, geometry, origin=None, material=None, name=None):
        self.geometry = geometry
        self.origin = origin or Origin()
        self.material = material
        self.name = name

class Part:
    def __init__(self, name, visuals=None, inertial=None, meta=None):
        self.name = name
        self.visuals = list(visuals or [])
        self.collisions = []
        self.inertial = inertial
        self.meta = dict(meta or {})

    def visual(self, geometry, *, origin=None, material=None, color=None, name=None):
        if color is not None and material is None:
            material = color if isinstance(color, (str, Material)) else Material("inline", rgba=color)
        v = Visual(geometry, origin=origin, material=material, name=name)
        self.visuals.append(v)
        return v

    def get_visual(self, name):
        for v in self.visuals:
            if v.name == name:
                return v
        raise ValidationError("unknown visual %r" % name)

class Articulation:
    def __init__(self, name, articulation_type, parent, child, origin=None,
                 axis=(0.0, 0.0, 1.0), motion_limits=None, motion_properties=None,
                 mimic=None, meta=None):
        self.name = name
        self.articulation_type = articulation_type
        self.parent = parent if isinstance(parent, str) else parent.name
        self.child = child if isinstance(child, str) else child.name
        self.origin = origin or Origin()
        self.axis = tuple(float(a) for a in axis)
        self.motion_limits = motion_limits
        self.motion_properties = motion_properties
        self.mimic = mimic
        self.meta = dict(meta or {})

    # aliases used by some scripts
    @property
    def joint_type(self):
        return self.articulation_type

    @property
    def limit(self):
        return self.motion_limits

class ArticulatedObject:
    def __init__(self, name, parts=None, articulations=None, materials=None, meta=None, assets=None):
        self.name = name
        self.parts = list(parts or [])
        self.articulations = list(articulations or [])
        self.materials = list(materials or [])
        self.meta = dict(meta or {})
        self.assets = assets

    # ---- builders ----
    def part(self, name, *, visuals=None, inertial=None, meta=None):
        p = Part(name, visuals=visuals, inertial=inertial, meta=meta)
        self.parts.append(p)
        return p

    link = part

    def articulation(self, name, articulation_type, parent, child, *, origin=None,
                     axis=None, motion_limits=None, motion_properties=None, mimic=None, meta=None):
        a = Articulation(name, articulation_type, parent, child, origin=origin,
                         axis=axis or (0.0, 0.0, 1.0), motion_limits=motion_limits,
                         motion_properties=motion_properties, mimic=mimic, meta=meta)
        self.articulations.append(a)
        return a

    def joint(self, name, joint_type, parent, child, *, origin=None, axis=None,
              limit=None, dynamics=None, mimic=None, meta=None):
        return self.articulation(name, joint_type, parent, child, origin=origin, axis=axis,
                                 motion_limits=limit, motion_properties=dynamics, mimic=mimic, meta=meta)

    def material(self, name, *, rgba=None, color=None, texture=None):
        m = Material(name, rgba=rgba, color=color, texture=texture)
        self.materials.append(m)
        return m

    def set_assets(self, assets):
        self.assets = assets
        return assets

    # ---- queries ----
    def get_part(self, name):
        key = name if isinstance(name, str) else name.name
        for p in self.parts:
            if p.name == key:
                return p
        raise ValidationError("unknown part %r" % name)

    get_link = get_part

    def get_articulation(self, name):
        key = name if isinstance(name, str) else getattr(name, "name", name)
        for a in self.articulations:
            if a.name == key:
                return a
        raise ValidationError("unknown articulation %r" % name)

    get_joint = get_articulation

    def root_parts(self):
        children = {a.child for a in self.articulations}
        return [p for p in self.parts if p.name not in children]

    root_links = root_parts

    def validate(self, *a, **k):
        return None

    def to_urdf(self, *a, **k):
        raise ValidationError("URDF export is not available in self-contained CadQuery mode")

    # ---- rest-pose world transform per part (URDF forward kinematics, q=0) ----
    def _world_transforms(self):
        parent_of, joint_tf = {}, {}
        for a in self.articulations:
            parent_of[a.child] = a.parent
            joint_tf[a.child] = _Tf.from_origin(a.origin)
        cache = {}

        def world(name):
            if name in cache:
                return cache[name]
            if name in parent_of:
                tf = world(parent_of[name]) @ joint_tf[name]
            else:
                tf = _Tf()
            cache[name] = tf
            return tf

        return {p.name: world(p.name) for p in self.parts}

    # ---- assemble to a CadQuery Assembly in rest pose ----
    def to_cq(self):
        worlds = self._world_transforms()
        asm = cq.Assembly(name=self.name or "model")
        idx = 0
        for part in self.parts:
            wt = worlds.get(part.name, _Tf())
            for vis in part.visuals:
                try:
                    shape = _to_shape(vis.geometry)
                except Exception as exc:
                    raise ValidationError(
                        "part %r visual %r: %s" % (part.name, vis.name, exc)
                    )
                loc = (wt @ _Tf.from_origin(vis.origin)).location()
                rgba = None
                mat = vis.material
                if isinstance(mat, str):
                    mat = next((m for m in self.materials if m.name == mat), None)
                if isinstance(mat, Material) and mat.rgba:
                    rgba = mat.rgba
                kw = {"name": "%s_%d" % (part.name, idx)}
                if rgba:
                    kw["color"] = cq.Color(*rgba)
                asm.add(shape, loc=loc, **kw)
                idx += 1
        return asm

    # convenience aliases a few scripts might call
    def to_assembly(self):
        return self.to_cq()

    def compound(self):
        return self.to_cq().toCompound()

# ===== model =====
import cadquery as cq
BODY_L = 0.190
BODY_W = 0.086
BODY_H = 0.110
CORNER_R = 0.011
BULGE_L = 0.046
BULGE_W = 0.074
BULGE_H = 0.074
BULGE_X = -0.106
BULGE_Z = 0.006
LENS_Z = 0.006
LENS_MOUNT_R = 0.029
LENS_MOUNT_LEN = 0.014
LENS_R = 0.024
LENS_LEN = 0.050
HOOD_R = 0.031
HOOD_LEN = 0.018
LENS_BORE_R = 0.017
LENS_BORE_LEN = 0.056
HANDLE_Y = 0.013
HANDLE_POST_H = 0.030
HANDLE_POST_SIZE = (0.013, 0.018, HANDLE_POST_H)
HANDLE_FRONT_X = 0.034
HANDLE_REAR_X = -0.008
HANDLE_BEAM_SIZE = (0.082, 0.019, 0.010)
HANDLE_BEAM_Z = BODY_H / 2.0 + HANDLE_POST_H + HANDLE_BEAM_SIZE[2] / 2.0 - 0.004
LCD_W = 0.074
LCD_H = 0.050
LCD_T = 0.0045
LCD_RECESS_W = 0.078
LCD_RECESS_H = 0.054
LCD_RECESS_D = 0.0085
LCD_X = -0.006
LCD_Z = 0.016
DOOR_W = 0.082
DOOR_H = 0.038
DOOR_T = 0.006
DOOR_RECESS_W = 0.086
DOOR_RECESS_H = 0.042
DOOR_RECESS_D = 0.0085
DOOR_X = -0.001
DOOR_Z = -0.028
DIAL_R = 0.015
DIAL_TOP_R = 0.012
DIAL_H = 0.010
DIAL_X = -0.062
DIAL_Y = 0.014
DIAL_Z = BODY_H / 2.0
LCD_OPEN = 1.55
DOOR_OPEN = 1.35
def _make_body_mesh():
    body = (
        cq.Workplane("XY")
        .box(BODY_L, BODY_W, BODY_H)
        .edges("|Z")
        .fillet(CORNER_R)
        .edges(">Z")
        .fillet(0.004)
    )

    bulge = (
        cq.Workplane("XY")
        .transformed(offset=(BULGE_X, 0.0, BULGE_Z))
        .box(BULGE_L, BULGE_W, BULGE_H)
        .edges("|Y")
        .fillet(0.016)
        .edges("|Z")
        .fillet(0.010)
    )

    front_post = (
        cq.Workplane("XY")
        .transformed(
            offset=(
                HANDLE_FRONT_X,
                HANDLE_Y,
                BODY_H / 2.0 + HANDLE_POST_H / 2.0 - 0.002,
            )
        )
        .box(*HANDLE_POST_SIZE)
    )
    rear_post = (
        cq.Workplane("XY")
        .transformed(
            offset=(
                HANDLE_REAR_X,
                HANDLE_Y,
                BODY_H / 2.0 + HANDLE_POST_H / 2.0 - 0.002,
            )
        )
        .box(*HANDLE_POST_SIZE)
    )
    handle_beam = (
        cq.Workplane("XY")
        .transformed(offset=(0.013, HANDLE_Y, HANDLE_BEAM_Z))
        .box(*HANDLE_BEAM_SIZE)
        .edges("|Y")
        .fillet(0.004)
    )

    body = body.union(bulge)
    body = body.union(front_post).union(rear_post).union(handle_beam).combine()

    lcd_recess = (
        cq.Workplane("XY")
        .box(LCD_RECESS_W, LCD_RECESS_D + 0.002, LCD_RECESS_H)
        .translate((LCD_X, -BODY_W / 2.0 + LCD_RECESS_D / 2.0, LCD_Z))
    )
    door_recess = (
        cq.Workplane("XY")
        .box(DOOR_RECESS_W, DOOR_RECESS_D + 0.002, DOOR_RECESS_H)
        .translate((DOOR_X, -BODY_W / 2.0 + DOOR_RECESS_D / 2.0, DOOR_Z))
    )
    body = body.cut(lcd_recess).cut(door_recess).combine()

    return mesh_from_cadquery(body, "camcorder_body")
def _make_lens_mesh():
    lens = (
        cq.Workplane("YZ")
        .circle(LENS_MOUNT_R)
        .extrude(LENS_MOUNT_LEN)
    )
    barrel = (
        cq.Workplane("YZ")
        .circle(LENS_R)
        .extrude(LENS_LEN)
        .translate((LENS_MOUNT_LEN - 0.002, 0.0, 0.0))
    )
    hood = (
        cq.Workplane("YZ")
        .circle(HOOD_R)
        .extrude(HOOD_LEN)
        .translate((LENS_MOUNT_LEN + LENS_LEN - HOOD_LEN - 0.002, 0.0, 0.0))
    )
    bore = (
        cq.Workplane("YZ")
        .circle(LENS_BORE_R)
        .extrude(LENS_BORE_LEN)
        .translate((0.006, 0.0, 0.0))
    )
    ring = (
        cq.Workplane("YZ")
        .circle(LENS_R + 0.003)
        .extrude(0.007)
        .translate((LENS_MOUNT_LEN + 0.015, 0.0, 0.0))
    )
    lens = lens.union(barrel).union(hood).union(ring).cut(bore)
    return mesh_from_cadquery(lens, "camcorder_lens")
def _make_lcd_panel_mesh():
    panel = (
        cq.Workplane("XY")
        .box(LCD_W, LCD_T, LCD_H)
        .translate((LCD_W / 2.0, -LCD_T / 2.0, 0.0))
    )
    bezel_cut = (
        cq.Workplane("XY")
        .box(LCD_W - 0.010, LCD_T * 0.55, LCD_H - 0.010)
        .translate((LCD_W / 2.0 + 0.001, LCD_T * 0.18, 0.0))
    )
    hinge_barrel = (
        cq.Workplane("XY")
        .circle(0.0024)
        .extrude(LCD_H - 0.010)
        .translate((0.0, -0.0024, -(LCD_H - 0.010) / 2.0))
    )
    hinge_leaf = (
        cq.Workplane("XY")
        .box(0.003, 0.001, LCD_H - 0.016)
        .translate((0.0015, -0.0005, 0.0))
    )
    panel = panel.cut(bezel_cut).union(hinge_barrel).union(hinge_leaf)
    return mesh_from_cadquery(panel, "lcd_panel")
def _make_tape_door_mesh():
    door = (
        cq.Workplane("XY")
        .box(DOOR_W, DOOR_T, DOOR_H)
        .translate((0.0, DOOR_T / 2.0, -DOOR_H / 2.0))
        .edges("|X")
        .fillet(0.0025)
    )
    hinge_lip = (
        cq.Workplane("XY")
        .box(DOOR_W - 0.008, 0.001, 0.003)
        .translate((0.0, -0.0005, -0.0015))
    )
    finger_notch = (
        cq.Workplane("YZ")
        .circle(0.0065)
        .extrude(DOOR_W * 0.40)
        .translate((-DOOR_W * 0.20, 0.0005, -DOOR_H + 0.005))
    )
    door = door.union(hinge_lip).cut(finger_notch)
    return mesh_from_cadquery(door, "tape_door")
def _make_dial_mesh():
    spindle = cq.Workplane("XY").circle(0.0045).extrude(0.0015)
    dial = spindle.union(
        cq.Workplane("XY").circle(DIAL_R).extrude(DIAL_H * 0.42).translate((0.0, 0.0, 0.0015))
    )
    dial = dial.union(
        cq.Workplane("XY")
        .circle(DIAL_TOP_R)
        .extrude(DIAL_H)
        .translate((0.0, 0.0, DIAL_H * 0.10 + 0.0015))
    )
    dial = dial.union(
        cq.Workplane("XY")
        .box(0.005, 0.003, 0.0018)
        .translate((DIAL_R - 0.003, 0.0, DIAL_H + 0.0024))
    )
    return mesh_from_cadquery(dial, "selector_dial")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="shoulder_mini_camcorder")

    body_finish = model.material("body_finish", rgba=(0.16, 0.17, 0.18, 1.0))
    panel_finish = model.material("panel_finish", rgba=(0.07, 0.08, 0.09, 1.0))
    lens_finish = model.material("lens_finish", rgba=(0.04, 0.04, 0.05, 1.0))
    dial_finish = model.material("dial_finish", rgba=(0.47, 0.49, 0.52, 1.0))

    body = model.part("body")
    body.visual(_make_body_mesh(), material=body_finish, name="body_shell")

    lens_tube = model.part("lens_tube")
    lens_tube.visual(_make_lens_mesh(), material=lens_finish, name="lens_shell")

    lcd_panel = model.part("lcd_panel")
    lcd_panel.visual(_make_lcd_panel_mesh(), material=panel_finish, name="panel_shell")

    tape_door = model.part("tape_door")
    tape_door.visual(_make_tape_door_mesh(), material=panel_finish, name="door_shell")

    selector_dial = model.part("selector_dial")
    selector_dial.visual(_make_dial_mesh(), material=dial_finish, name="dial_shell")

    model.articulation(
        "body_to_lens_tube",
        ArticulationType.FIXED,
        parent=body,
        child=lens_tube,
        origin=Origin(xyz=(BODY_L / 2.0, 0.0, LENS_Z)),
    )

    model.articulation(
        "body_to_lcd_panel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lcd_panel,
        origin=Origin(xyz=(LCD_X - LCD_W / 2.0 - 0.0014, -BODY_W / 2.0, LCD_Z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(lower=0.0, upper=LCD_OPEN, effort=3.0, velocity=2.0),
    )

    model.articulation(
        "body_to_tape_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=tape_door,
        origin=Origin(xyz=(DOOR_X, -BODY_W / 2.0, DOOR_Z + DOOR_H / 2.0 + 0.0015)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=DOOR_OPEN, effort=3.0, velocity=2.0),
    )

    model.articulation(
        "body_to_selector_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=selector_dial,
        origin=Origin(xyz=(DIAL_X, DIAL_Y, DIAL_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.5, velocity=8.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
