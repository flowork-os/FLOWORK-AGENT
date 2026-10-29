# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_W = 0.24
BODY_D = 0.19
BODY_H = 0.92
BODY_CORNER_R = 0.026
WALL = 0.014
FRONT_WALL = 0.018
BOTTOM_BASE = 0.075
TOP_SECTION = 0.145
CAVITY_W = BODY_W - 2.0 * WALL
CAVITY_D = BODY_D - FRONT_WALL
CAVITY_H = BODY_H - BOTTOM_BASE - TOP_SECTION
CAVITY_CENTER_Z = BOTTOM_BASE + CAVITY_H / 2.0
HINGE_R = 0.006
HINGE_X = CAVITY_W / 2.0 - 0.014
BODY_KNUCKLE_LEN = 0.17
DOOR_KNUCKLE_LEN = 0.28
DOOR_T = 0.008
DOOR_W = CAVITY_W + 0.016
DOOR_H = CAVITY_H + 0.030
DOOR_LEAF_W = DOOR_W - 0.014
FILTER_W = CAVITY_W - 0.022
FILTER_D = 0.165
FILTER_H = CAVITY_H - 0.040
FILTER_TRAVEL = 0.11
SHOULDER_OUTER_R = 0.080
SHOULDER_INNER_R = 0.060
SHOULDER_H = 0.012
SHOULDER_CENTER_Z = BODY_H + 0.004
RING_OUTER_R = 0.094
RING_INNER_R = 0.080
RING_H = 0.018
RING_CENTER_Z = BODY_H + 0.019
SLOT_CENTER_Z = 0.66
SLOT_CUT_X = 0.030
SLOT_CUT_Y = 0.012
SLOT_CUT_Z = 0.078
SLIDER_TRAVEL = 0.022
def centered_annulus(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((0.0, 0.0, -height / 2.0))
    )
def build_body_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(BODY_W, BODY_D, BODY_H)
        .translate((0.0, 0.0, BODY_H / 2.0))
        .edges("|Z")
        .fillet(BODY_CORNER_R)
    )

    rear_cavity = (
        cq.Workplane("XY")
        .box(CAVITY_W, CAVITY_D, CAVITY_H)
        .translate((0.0, -FRONT_WALL / 2.0, CAVITY_CENTER_Z))
    )

    top_outlet = (
        cq.Workplane("XY")
        .circle(SHOULDER_INNER_R)
        .extrude(TOP_SECTION + 0.040)
        .translate((0.0, 0.0, BODY_H - TOP_SECTION - 0.010))
    )

    timer_slot = (
        cq.Workplane("XY")
        .box(SLOT_CUT_X, SLOT_CUT_Y, SLOT_CUT_Z)
        .translate((BODY_W / 2.0 - WALL / 2.0, 0.0, SLOT_CENTER_Z))
    )

    return outer.cut(rear_cavity).cut(top_outlet).cut(timer_slot)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_purifier")

    shell_white = model.material("shell_white", rgba=(0.92, 0.93, 0.94, 1.0))
    graphite = model.material("graphite", rgba=(0.18, 0.19, 0.21, 1.0))
    charcoal = model.material("charcoal", rgba=(0.24, 0.25, 0.26, 1.0))
    satin = model.material("satin", rgba=(0.70, 0.73, 0.76, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(build_body_shell(), "body_shell"),
        material=shell_white,
        name="body_shell",
    )
    body.visual(
        mesh_from_cadquery(
            centered_annulus(SHOULDER_OUTER_R, SHOULDER_INNER_R, SHOULDER_H),
            "top_shoulder",
        ),
        origin=Origin(xyz=(0.0, 0.0, SHOULDER_CENTER_Z)),
        material=graphite,
        name="top_shoulder",
    )
    body.visual(
        Box((0.120, 0.004, 0.430)),
        origin=Origin(xyz=(0.0, BODY_D / 2.0 - 0.001, 0.41)),
        material=graphite,
        name="front_grille",
    )
    body.visual(
        Box((0.012, 0.010, BODY_KNUCKLE_LEN)),
        origin=Origin(
            xyz=(HINGE_X - 0.006, -BODY_D / 2.0 - 0.002, CAVITY_CENTER_Z - 0.275),
        ),
        material=graphite,
        name="body_mount_0",
    )
    body.visual(
        Cylinder(radius=HINGE_R, length=BODY_KNUCKLE_LEN),
        origin=Origin(
            xyz=(HINGE_X, -BODY_D / 2.0 - 0.002, CAVITY_CENTER_Z - 0.275),
        ),
        material=graphite,
        name="body_knuckle_0",
    )
    body.visual(
        Box((0.012, 0.010, BODY_KNUCKLE_LEN)),
        origin=Origin(
            xyz=(HINGE_X - 0.006, -BODY_D / 2.0 - 0.002, CAVITY_CENTER_Z + 0.275),
        ),
        material=graphite,
        name="body_mount_1",
    )
    body.visual(
        Cylinder(radius=HINGE_R, length=BODY_KNUCKLE_LEN),
        origin=Origin(
            xyz=(HINGE_X, -BODY_D / 2.0 - 0.002, CAVITY_CENTER_Z + 0.275),
        ),
        material=graphite,
        name="body_knuckle_1",
    )

    filter_door = model.part("filter_door")
    filter_door.visual(
        Box((DOOR_LEAF_W, DOOR_T, DOOR_H)),
        origin=Origin(xyz=(-DOOR_LEAF_W / 2.0 - 0.010, -DOOR_T / 2.0, 0.0)),
        material=shell_white,
        name="door_leaf",
    )
    filter_door.visual(
        Box((0.024, 0.010, 0.120)),
        origin=Origin(xyz=(-DOOR_W + 0.016, -0.009, 0.0)),
        material=graphite,
        name="door_pull",
    )
    filter_door.visual(
        Box((0.010, 0.010, DOOR_KNUCKLE_LEN)),
        origin=Origin(xyz=(-0.007, -0.004, 0.0)),
        material=graphite,
        name="door_mount",
    )
    filter_door.visual(
        Cylinder(radius=HINGE_R, length=DOOR_KNUCKLE_LEN),
        origin=Origin(xyz=(0.0, -0.004, 0.0)),
        material=graphite,
        name="door_knuckle",
    )

    filter_pack = model.part("filter_pack")
    filter_pack.visual(
        Box((FILTER_W, FILTER_D, FILTER_H)),
        origin=Origin(xyz=(0.0, FILTER_D / 2.0, 0.0)),
        material=satin,
        name="filter_frame",
    )
    filter_pack.visual(
        Box((FILTER_W - 0.022, FILTER_D - 0.014, FILTER_H - 0.050)),
        origin=Origin(xyz=(0.0, FILTER_D / 2.0 + 0.004, 0.0)),
        material=charcoal,
        name="filter_media",
    )

    control_ring = model.part("control_ring")
    control_ring.visual(
        mesh_from_cadquery(
            centered_annulus(RING_OUTER_R, RING_INNER_R, RING_H),
            "control_ring",
        ),
        material=satin,
        name="ring_shell",
    )

    timer_slider = model.part("timer_slider")
    timer_slider.visual(
        Box((WALL + 0.012, 0.010, 0.010)),
        origin=Origin(),
        material=graphite,
        name="slider_runner",
    )
    timer_slider.visual(
        Box((0.018, 0.016, 0.026)),
        origin=Origin(xyz=(0.012, 0.0, 0.0)),
        material=graphite,
        name="slider_thumb",
    )

    model.articulation(
        "body_to_filter_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=filter_door,
        origin=Origin(xyz=(HINGE_X, -BODY_D / 2.0, CAVITY_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.5,
            lower=0.0,
            upper=2.1,
        ),
    )

    model.articulation(
        "body_to_filter_pack",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_pack,
        origin=Origin(xyz=(0.0, -BODY_D / 2.0, CAVITY_CENTER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=20.0,
            velocity=0.12,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    model.articulation(
        "body_to_control_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=control_ring,
        origin=Origin(xyz=(0.0, 0.0, RING_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=6.0),
    )

    model.articulation(
        "body_to_timer_slider",
        ArticulationType.PRISMATIC,
        parent=body,
        child=timer_slider,
        origin=Origin(xyz=(BODY_W / 2.0 - WALL / 2.0, 0.0, SLOT_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=0.08,
            lower=-SLIDER_TRAVEL,
            upper=SLIDER_TRAVEL,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
