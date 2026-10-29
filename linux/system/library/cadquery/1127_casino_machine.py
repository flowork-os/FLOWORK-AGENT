# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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

class Cylinder:
    __slots__ = ("radius", "length")

    def __init__(self, radius, length=None, *, height=None):
        self.radius = float(radius)
        self.length = float(height if length is None else length)

    @property
    def height(self):
        return self.length

    def _cq(self):
        return cq.Solid.makeCylinder(
            self.radius, self.length, cq.Vector(0, 0, -self.length / 2), cq.Vector(0, 0, 1)
        )

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
CABINET_WIDTH = 0.76
CABINET_DEPTH = 0.66
CABINET_HEIGHT = 1.86
WALL_THICKNESS = 0.028
FRONT_Y = CABINET_DEPTH / 2.0
WINDOW_OUTER_WIDTH = 0.50
WINDOW_OUTER_HEIGHT = 0.44
WINDOW_INNER_WIDTH = 0.39
WINDOW_INNER_HEIGHT = 0.31
WINDOW_DEPTH = 0.040
WINDOW_CENTER_Z = 1.06
DOOR_OPENING_WIDTH = 0.56
DOOR_OPENING_HEIGHT = 0.74
DOOR_WIDTH = 0.53
DOOR_HEIGHT = 0.70
DOOR_THICKNESS = 0.020
DOOR_CENTER_Z = 0.47
HANDLE_PIVOT_X = CABINET_WIDTH / 2.0 + 0.040
HANDLE_PIVOT_Y = 0.10
HANDLE_PIVOT_Z = 1.14
def _cabinet_shell_mesh():
    back_y = -CABINET_DEPTH / 2.0
    front_y = CABINET_DEPTH / 2.0

    outer_profile = (
        cq.Workplane("YZ")
        .moveTo(back_y, 0.0)
        .lineTo(front_y - 0.065, 0.0)
        .lineTo(front_y, 0.12)
        .lineTo(front_y, 1.43)
        .threePointArc((0.22, 1.79), (0.01, CABINET_HEIGHT))
        .lineTo(back_y + 0.02, CABINET_HEIGHT)
        .lineTo(back_y, 1.68)
        .close()
    )

    shell = outer_profile.extrude(CABINET_WIDTH / 2.0, both=True).faces("<Z").shell(-WALL_THICKNESS)

    window_cut = cq.Workplane("XY").box(
        WINDOW_INNER_WIDTH + 0.05,
        0.14,
        WINDOW_INNER_HEIGHT + 0.05,
    ).translate((0.0, FRONT_Y - 0.055, WINDOW_CENTER_Z))

    door_cut = cq.Workplane("XY").box(
        DOOR_OPENING_WIDTH,
        0.14,
        DOOR_OPENING_HEIGHT,
    ).translate((0.0, FRONT_Y - 0.055, DOOR_CENTER_Z))

    side_plate = cq.Workplane("XY").box(0.010, 0.18, 0.22).translate(
        (CABINET_WIDTH / 2.0 + 0.005, HANDLE_PIVOT_Y, HANDLE_PIVOT_Z)
    )

    front_trim = cq.Workplane("XY").box(0.62, 0.018, 0.12).translate((0.0, FRONT_Y + 0.009, 1.58))

    return shell.cut(window_cut).cut(door_cut).union(side_plate).union(front_trim)
def _window_frame_mesh():
    frame = cq.Workplane("XY").box(
        WINDOW_OUTER_WIDTH,
        WINDOW_DEPTH,
        WINDOW_OUTER_HEIGHT,
    ).translate((0.0, WINDOW_DEPTH / 2.0, 0.0))

    opening = cq.Workplane("XY").box(
        WINDOW_INNER_WIDTH,
        WINDOW_DEPTH + 0.01,
        WINDOW_INNER_HEIGHT,
    ).translate((0.0, WINDOW_DEPTH / 2.0, 0.0))

    mullion_offset = WINDOW_INNER_WIDTH / 3.0
    mullion = lambda x: cq.Workplane("XY").box(0.016, WINDOW_DEPTH, WINDOW_INNER_HEIGHT + 0.02).translate(
        (x, WINDOW_DEPTH / 2.0, 0.0)
    )

    return frame.cut(opening).union(mullion(-mullion_offset / 2.0)).union(mullion(mullion_offset / 2.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="reel_slot_machine")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.54, 0.05, 0.08, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.80, 0.67, 0.21, 1.0))
    dark_glass = model.material("dark_glass", rgba=(0.08, 0.08, 0.10, 0.82))
    reel_finish = model.material("reel_finish", rgba=(0.94, 0.92, 0.85, 1.0))
    metal_finish = model.material("metal_finish", rgba=(0.73, 0.75, 0.79, 1.0))
    black_finish = model.material("black_finish", rgba=(0.10, 0.10, 0.12, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_cabinet_shell_mesh(), "cabinet_shell"),
        material=cabinet_finish,
        name="shell",
    )
    cabinet.visual(
        Box((0.56, 0.018, 0.10)),
        origin=Origin(xyz=(0.0, FRONT_Y + 0.009, 0.74)),
        material=trim_finish,
        name="panel_band",
    )
    for index, x_pos in enumerate((-0.24, 0.24)):
        cabinet.visual(
            Box((0.020, 0.030, 0.46)),
            origin=Origin(xyz=(x_pos, FRONT_Y + 0.015, WINDOW_CENTER_Z)),
            material=trim_finish,
            name=f"window_mount_{index}",
        )

    reel_window = model.part("reel_window")
    reel_window.visual(
        mesh_from_cadquery(_window_frame_mesh(), "reel_window_frame"),
        material=trim_finish,
        name="frame",
    )
    reel_window.visual(
        Box((WINDOW_INNER_WIDTH * 0.98, 0.008, WINDOW_INNER_HEIGHT * 0.92)),
        origin=Origin(xyz=(0.0, -0.004, 0.0)),
        material=dark_glass,
        name="glass",
    )
    for index, x_pos in enumerate((-0.12, 0.0, 0.12)):
        reel_window.visual(
            Box((0.090, 0.004, 0.23)),
            origin=Origin(xyz=(x_pos, -0.002, 0.0)),
            material=reel_finish,
            name=f"reel_{index}",
        )

    service_door = model.part("service_door")
    service_door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, -DOOR_THICKNESS / 2.0, 0.0)),
        material=cabinet_finish,
        name="panel",
    )
    service_door.visual(
        Box((DOOR_WIDTH - 0.08, 0.004, DOOR_HEIGHT - 0.10)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, 0.002, 0.0)),
        material=trim_finish,
        name="bead",
    )
    service_door.visual(
        Cylinder(radius=0.016, length=0.008),
        origin=Origin(xyz=(DOOR_WIDTH - 0.055, 0.004, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material=metal_finish,
        name="lock",
    )

    side_handle = model.part("side_handle")
    side_handle.visual(
        Cylinder(radius=0.028, length=0.060),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=metal_finish,
        name="hub",
    )
    side_handle.visual(
        Cylinder(radius=0.018, length=0.34),
        origin=Origin(xyz=(0.024, 0.0, -0.17)),
        material=black_finish,
        name="arm",
    )
    side_handle.visual(
        Sphere(radius=0.050),
        origin=Origin(xyz=(0.024, 0.0, -0.39)),
        material=black_finish,
        name="knob",
    )

    model.articulation(
        "cabinet_to_reel_window",
        ArticulationType.FIXED,
        parent=cabinet,
        child=reel_window,
        origin=Origin(xyz=(0.0, FRONT_Y + 0.030, WINDOW_CENTER_Z)),
    )
    model.articulation(
        "cabinet_to_service_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=service_door,
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, FRONT_Y, DOOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.45, effort=30.0, velocity=1.2),
    )
    model.articulation(
        "cabinet_to_side_handle",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=side_handle,
        origin=Origin(xyz=(HANDLE_PIVOT_X, HANDLE_PIVOT_Y, HANDLE_PIVOT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.0, effort=18.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
