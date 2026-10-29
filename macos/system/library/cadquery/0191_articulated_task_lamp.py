# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

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
import math
import cadquery as cq
BASE_LENGTH = 0.180
BASE_WIDTH = 0.110
BASE_HEIGHT = 0.020
PEDESTAL_LENGTH = 0.068
PEDESTAL_WIDTH = 0.060
PEDESTAL_HEIGHT = 0.022
BASE_PIVOT_X = -0.020
LOWER_LINK_LENGTH = 0.120
UPPER_LINK_LENGTH = 0.108
def _base_shape() -> cq.Workplane:
    foot = (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.008)
    )
    pedestal = (
        cq.Workplane("XY")
        .box(
            PEDESTAL_LENGTH,
            PEDESTAL_WIDTH,
            PEDESTAL_HEIGHT,
            centered=(True, True, False),
        )
        .translate((-0.034, 0.0, BASE_HEIGHT))
        .edges("|Z")
        .fillet(0.006)
    )
    cheek_size = (0.020, 0.010, 0.026)
    cheek_z = BASE_HEIGHT + PEDESTAL_HEIGHT - 0.002
    cheek_x = BASE_PIVOT_X - 0.002
    cheek_0 = (
        cq.Workplane("XY")
        .box(*cheek_size, centered=(True, True, False))
        .translate((cheek_x, -0.015, cheek_z))
        .edges("|Z")
        .fillet(0.002)
    )
    cheek_1 = (
        cq.Workplane("XY")
        .box(*cheek_size, centered=(True, True, False))
        .translate((cheek_x, 0.015, cheek_z))
        .edges("|Z")
        .fillet(0.002)
    )
    switch_bezel = (
        cq.Workplane("XY")
        .box(0.036, 0.003, 0.020, centered=(True, True, False))
        .translate((0.034, BASE_WIDTH / 2.0 + 0.0015, 0.002))
        .edges("|X")
        .fillet(0.0012)
    )
    switch_recess = (
        cq.Workplane("XY")
        .box(0.028, 0.010, 0.018, centered=(True, True, False))
        .translate((0.034, BASE_WIDTH / 2.0 - 0.004, 0.004))
    )
    return foot.union(pedestal).union(cheek_0).union(cheek_1).union(switch_bezel).cut(switch_recess)
def _lower_link_shape() -> cq.Workplane:
    pivot = (
        cq.Workplane("XY")
        .cylinder(0.014, 0.007, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
    )
    shoulder = (
        cq.Workplane("XY")
        .box(0.020, 0.020, 0.010, centered=(False, True, True))
        .translate((0.006, 0.0, 0.0))
        .edges("|X")
        .fillet(0.002)
    )
    rail_length = LOWER_LINK_LENGTH - 0.034
    rail_x = 0.018
    rail_0 = (
        cq.Workplane("XY")
        .box(rail_length, 0.008, 0.013, centered=(False, True, True))
        .translate((rail_x, -0.014, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    rail_1 = (
        cq.Workplane("XY")
        .box(rail_length, 0.008, 0.013, centered=(False, True, True))
        .translate((rail_x, 0.014, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    tip_bridge = (
        cq.Workplane("XY")
        .box(0.020, 0.028, 0.012, centered=(True, True, True))
        .translate((LOWER_LINK_LENGTH - 0.020, 0.0, 0.0))
        .edges("|Z")
        .fillet(0.002)
    )
    lug_x = LOWER_LINK_LENGTH - 0.010
    lug_0 = (
        cq.Workplane("XY")
        .box(0.020, 0.006, 0.026, centered=(True, True, True))
        .translate((lug_x, -0.013, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    lug_1 = (
        cq.Workplane("XY")
        .box(0.020, 0.006, 0.026, centered=(True, True, True))
        .translate((lug_x, 0.013, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    return pivot.union(shoulder).union(rail_0).union(rail_1).union(tip_bridge).union(lug_0).union(lug_1)
def _upper_link_shape() -> cq.Workplane:
    pivot = (
        cq.Workplane("XY")
        .cylinder(0.022, 0.007, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
    )
    spine = (
        cq.Workplane("XY")
        .box(0.086, 0.016, 0.012, centered=(False, True, True))
        .translate((0.006, 0.0, 0.0))
        .edges("|X")
        .fillet(0.002)
    )
    yoke_stem = (
        cq.Workplane("XY")
        .box(0.022, 0.066, 0.014, centered=(True, True, True))
        .translate((UPPER_LINK_LENGTH - 0.026, 0.0, 0.0))
        .edges("|Z")
        .fillet(0.002)
    )
    cheek_x = UPPER_LINK_LENGTH - 0.008
    cheek_0 = (
        cq.Workplane("XY")
        .box(0.016, 0.006, 0.036, centered=(True, True, True))
        .translate((cheek_x, -0.035, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    cheek_1 = (
        cq.Workplane("XY")
        .box(0.016, 0.006, 0.036, centered=(True, True, True))
        .translate((cheek_x, 0.035, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    return pivot.union(spine).union(yoke_stem).union(cheek_0).union(cheek_1)
def _head_shape() -> cq.Workplane:
    shell = (
        cq.Workplane("YZ")
        .circle(0.027)
        .extrude(0.078)
        .translate((0.010, 0.0, 0.0))
    )
    front_ring = (
        cq.Workplane("YZ")
        .circle(0.030)
        .circle(0.021)
        .extrude(0.006)
        .translate((0.081, 0.0, 0.0))
    )
    trunnion = (
        cq.Workplane("XY")
        .cylinder(0.068, 0.0055, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
    )
    neck = (
        cq.Workplane("XY")
        .box(0.012, 0.018, 0.012, centered=(False, True, True))
        .translate((-0.001, 0.0, 0.0))
        .edges("|X")
        .fillet(0.0015)
    )
    return shell.union(front_ring).union(trunnion).union(neck)
def _switch_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(0.028, 0.010, 0.016, centered=(True, True, True))
        .translate((0.0, 0.004, 0.0))
        .edges("|X")
        .fillet(0.0025)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bench_lamp")

    model.material("base_gray", rgba=(0.23, 0.24, 0.26, 1.0))
    model.material("arm_satin", rgba=(0.63, 0.65, 0.68, 1.0))
    model.material("head_black", rgba=(0.12, 0.12, 0.13, 1.0))
    model.material("switch_black", rgba=(0.09, 0.09, 0.10, 1.0))
    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_shape(), "base_shell"),
        material="base_gray",
        name="base_shell",
    )

    lower_link = model.part("lower_link")
    lower_link.visual(
        mesh_from_cadquery(_lower_link_shape(), "lower_link"),
        material="arm_satin",
        name="lower_frame",
    )

    upper_link = model.part("upper_link")
    upper_link.visual(
        mesh_from_cadquery(_upper_link_shape(), "upper_link"),
        material="arm_satin",
        name="upper_frame",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shape(), "head_shell"),
        material="head_black",
        name="head_shell",
    )

    switch = model.part("switch")
    switch.visual(
        mesh_from_cadquery(_switch_shape(), "rocker_switch"),
        material="switch_black",
        name="rocker_body",
    )

    model.articulation(
        "base_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=lower_link,
        origin=Origin(xyz=(BASE_PIVOT_X, 0.0, 0.052), rpy=(0.0, -0.85, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.8,
            lower=-0.55,
            upper=0.65,
        ),
    )
    model.articulation(
        "elbow_hinge",
        ArticulationType.REVOLUTE,
        parent=lower_link,
        child=upper_link,
        origin=Origin(xyz=(LOWER_LINK_LENGTH, 0.0, 0.0), rpy=(0.0, 0.45, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.0,
            lower=-0.90,
            upper=0.90,
        ),
    )
    model.articulation(
        "head_hinge",
        ArticulationType.REVOLUTE,
        parent=upper_link,
        child=head,
        origin=Origin(xyz=(UPPER_LINK_LENGTH, 0.0, 0.0), rpy=(0.0, 0.95, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=2.5,
            lower=-0.55,
            upper=0.80,
        ),
    )
    model.articulation(
        "switch_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=switch,
        origin=Origin(xyz=(0.034, 0.059, 0.013)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=4.0,
            lower=-0.30,
            upper=0.30,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
