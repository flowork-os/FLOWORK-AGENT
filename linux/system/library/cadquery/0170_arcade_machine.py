# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

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

class Box:
    __slots__ = ("size",)

    def __init__(self, size):
        self.size = (float(size[0]), float(size[1]), float(size[2]))

    def _cq(self):
        sx, sy, sz = self.size
        return cq.Solid.makeBox(sx, sy, sz, cq.Vector(-sx / 2, -sy / 2, -sz / 2))

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
import math
import cadquery as cq
WIDTH = 0.78
HEIGHT = 1.74
SIDE_THK = 0.018
WALL = 0.018
BRIDGE_WIDTH = WIDTH - 2.0 * SIDE_THK + 0.004
LOWER_FRONT_Y = 0.06
BACK_Y = -0.46
FRONT_FACE_HEIGHT = 0.96
DOOR_W = 0.52
DOOR_H = 0.46
DOOR_T = 0.022
DOOR_BOTTOM_Z = 0.22
DOOR_CENTER_Z = DOOR_BOTTOM_Z + DOOR_H / 2.0
DOOR_HINGE_OFFSET = 0.003
TRAY_W = 0.18
TRAY_H = 0.055
TRAY_T = 0.016
TRAY_BOTTOM_Z = 0.082
TRAY_CENTER_Z = TRAY_BOTTOM_Z + TRAY_H / 2.0
DECK_ANGLE_DEG = -18.0
DECK_ANGLE_RAD = math.radians(DECK_ANGLE_DEG)
MONITOR_ANGLE_DEG = -16.0
MONITOR_ANGLE_RAD = math.radians(MONITOR_ANGLE_DEG)
def _box_shape(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _ring_panel(
    outer_size: tuple[float, float, float],
    inner_size: tuple[float, float],
) -> cq.Workplane:
    outer = cq.Workplane("XY").box(*outer_size)
    inner = cq.Workplane("XY").box(inner_size[0], outer_size[1] + 0.02, inner_size[1])
    return outer.cut(inner)
def _side_panel_shape() -> cq.Workplane:
    profile = [
        (LOWER_FRONT_Y, 0.0),
        (LOWER_FRONT_Y, 0.94),
        (0.18, 0.99),
        (0.03, 1.08),
        (0.11, 1.23),
        (0.03, 1.47),
        (0.03, HEIGHT),
        (-0.22, HEIGHT),
        (-0.33, 1.48),
        (BACK_Y, 0.90),
        (BACK_Y, 0.0),
    ]
    return cq.Workplane("YZ").polyline(profile).close().extrude(SIDE_THK)
def _coin_panel_shape() -> cq.Workplane:
    panel = _box_shape((0.31, 0.012, 0.18), (0.0, LOWER_FRONT_Y + 0.006, 0.81))
    left_slot = _box_shape((0.034, 0.03, 0.008), (-0.085, LOWER_FRONT_Y + 0.006, 0.85))
    right_slot = _box_shape((0.034, 0.03, 0.008), (0.085, LOWER_FRONT_Y + 0.006, 0.85))
    return panel.cut(left_slot).cut(right_slot)
def _tray_surround_shape() -> cq.Workplane:
    surround = _ring_panel((0.28, 0.012, 0.13), (TRAY_W + 0.018, TRAY_H + 0.012))
    return surround.translate((0.0, LOWER_FRONT_Y + 0.006, TRAY_CENTER_Z))
def _monitor_frame_shape() -> cq.Workplane:
    frame = _ring_panel((0.64, WALL, 0.60), (0.50, 0.38))
    return frame.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), MONITOR_ANGLE_DEG).translate(
        (0.0, -0.02, 1.33)
    )
def _service_door_shape() -> cq.Workplane:
    return _box_shape(
        (DOOR_W, DOOR_T, DOOR_H),
        (DOOR_HINGE_OFFSET + DOOR_W / 2.0, -DOOR_T / 2.0, DOOR_H / 2.0),
    )
def _tray_flap_shape() -> cq.Workplane:
    return _box_shape((TRAY_W, TRAY_T, TRAY_H), (0.0, -TRAY_T / 2.0, TRAY_H / 2.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="upright_arcade_cabinet")

    cabinet_black = model.material("cabinet_black", rgba=(0.12, 0.12, 0.13, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.34, 0.35, 0.37, 1.0))
    deck_blue = model.material("deck_blue", rgba=(0.16, 0.21, 0.29, 1.0))
    screen_dark = model.material("screen_dark", rgba=(0.03, 0.05, 0.07, 1.0))
    door_gray = model.material("door_gray", rgba=(0.26, 0.27, 0.29, 1.0))

    body = model.part("body")
    side_panel = _side_panel_shape()
    body.visual(
        mesh_from_cadquery(side_panel.translate((-WIDTH / 2.0, 0.0, 0.0)), "left_side"),
        material=cabinet_black,
        name="left_side",
    )
    body.visual(
        mesh_from_cadquery(side_panel.translate((WIDTH / 2.0 - SIDE_THK, 0.0, 0.0)), "right_side"),
        material=cabinet_black,
        name="right_side",
    )
    body.visual(
        mesh_from_cadquery(_coin_panel_shape(), "coin_panel"),
        material=trim_gray,
        name="coin_panel",
    )
    door_side_w = (BRIDGE_WIDTH - DOOR_W) / 2.0
    tray_side_w = (BRIDGE_WIDTH - TRAY_W) / 2.0
    center_y = LOWER_FRONT_Y - WALL / 2.0
    body.visual(
        Box((BRIDGE_WIDTH, WALL, TRAY_BOTTOM_Z)),
        origin=Origin(xyz=(0.0, center_y, TRAY_BOTTOM_Z / 2.0)),
        material=cabinet_black,
        name="front_base",
    )
    body.visual(
        Box((tray_side_w, WALL, TRAY_H)),
        origin=Origin(xyz=(-(TRAY_W + tray_side_w) / 2.0, center_y, TRAY_CENTER_Z)),
        material=cabinet_black,
        name="tray_side_0",
    )
    body.visual(
        Box((tray_side_w, WALL, TRAY_H)),
        origin=Origin(xyz=((TRAY_W + tray_side_w) / 2.0, center_y, TRAY_CENTER_Z)),
        material=cabinet_black,
        name="tray_side_1",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, DOOR_BOTTOM_Z - (TRAY_BOTTOM_Z + TRAY_H))),
        origin=Origin(xyz=(0.0, center_y, (DOOR_BOTTOM_Z + TRAY_BOTTOM_Z + TRAY_H) / 2.0)),
        material=cabinet_black,
        name="mid_rail",
    )
    body.visual(
        Box((door_side_w, WALL, DOOR_H)),
        origin=Origin(xyz=(-(DOOR_W + door_side_w) / 2.0, center_y, DOOR_CENTER_Z)),
        material=cabinet_black,
        name="door_stile_0",
    )
    body.visual(
        Box((door_side_w, WALL, DOOR_H)),
        origin=Origin(xyz=((DOOR_W + door_side_w) / 2.0, center_y, DOOR_CENTER_Z)),
        material=cabinet_black,
        name="door_stile_1",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, FRONT_FACE_HEIGHT - (DOOR_BOTTOM_Z + DOOR_H))),
        origin=Origin(xyz=(0.0, center_y, (FRONT_FACE_HEIGHT + DOOR_BOTTOM_Z + DOOR_H) / 2.0)),
        material=cabinet_black,
        name="front_top",
    )
    body.visual(
        mesh_from_cadquery(_tray_surround_shape(), "tray_surround"),
        material=trim_gray,
        name="tray_surround",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, 0.12)),
        origin=Origin(xyz=(0.0, 0.132, 0.94)),
        material=trim_gray,
        name="control_apron",
    )
    body.visual(
        Box((BRIDGE_WIDTH, 0.30, 0.024)),
        origin=Origin(xyz=(0.0, 0.04, 1.035), rpy=(DECK_ANGLE_RAD, 0.0, 0.0)),
        material=deck_blue,
        name="control_deck",
    )
    body.visual(
        mesh_from_cadquery(_monitor_frame_shape(), "monitor_frame"),
        material=trim_gray,
        name="monitor_frame",
    )
    body.visual(
        Box((0.58, 0.06, 0.48)),
        origin=Origin(xyz=(0.0, -0.055, 1.31), rpy=(MONITOR_ANGLE_RAD, 0.0, 0.0)),
        material=cabinet_black,
        name="monitor_mount",
    )
    body.visual(
        Box((0.50, 0.018, 0.38)),
        origin=Origin(xyz=(0.0, -0.012, 1.325), rpy=(MONITOR_ANGLE_RAD, 0.0, 0.0)),
        material=screen_dark,
        name="screen_glass",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, 0.22)),
        origin=Origin(xyz=(0.0, 0.01, 1.60)),
        material=trim_gray,
        name="marquee_face",
    )
    body.visual(
        Box((BRIDGE_WIDTH, 0.26, WALL)),
        origin=Origin(xyz=(0.0, -0.10, HEIGHT - WALL / 2.0)),
        material=cabinet_black,
        name="roof",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, 0.96)),
        origin=Origin(xyz=(0.0, BACK_Y + WALL / 2.0, 0.48)),
        material=cabinet_black,
        name="rear_lower",
    )
    body.visual(
        Box((BRIDGE_WIDTH, WALL, 0.72)),
        origin=Origin(xyz=(0.0, -0.31, 1.38)),
        material=cabinet_black,
        name="rear_upper",
    )
    body.visual(
        Box((BRIDGE_WIDTH, 0.49, WALL)),
        origin=Origin(xyz=(0.0, -0.20, WALL / 2.0)),
        material=cabinet_black,
        name="floor",
    )

    service_door = model.part("service_door")
    service_door.visual(
        mesh_from_cadquery(_service_door_shape(), "service_door"),
        material=door_gray,
        name="service_panel",
    )
    service_door.visual(
        Box((0.034, 0.028, 0.12)),
        origin=Origin(xyz=(DOOR_HINGE_OFFSET + DOOR_W * 0.78, 0.008, DOOR_H * 0.56)),
        material=trim_gray,
        name="service_handle",
    )

    tray_flap = model.part("tray_flap")
    tray_flap.visual(
        mesh_from_cadquery(_tray_flap_shape(), "tray_flap"),
        material=door_gray,
        name="tray_panel",
    )
    tray_flap.visual(
        Box((0.10, 0.018, 0.010)),
        origin=Origin(xyz=(0.0, 0.006, TRAY_H * 0.62)),
        material=trim_gray,
        name="tray_pull",
    )

    model.articulation(
        "body_to_service_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=service_door,
        origin=Origin(
            xyz=(
                -DOOR_W / 2.0 - DOOR_HINGE_OFFSET,
                LOWER_FRONT_Y + 0.004,
                DOOR_BOTTOM_Z,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.22, effort=20.0, velocity=1.2),
    )
    model.articulation(
        "body_to_tray_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=tray_flap,
        origin=Origin(xyz=(0.0, LOWER_FRONT_Y + 0.012, TRAY_BOTTOM_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.12, effort=4.0, velocity=1.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
