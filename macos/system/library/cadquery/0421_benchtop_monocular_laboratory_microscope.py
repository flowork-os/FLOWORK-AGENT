# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, benchtop_monocular_laboratory_microscope, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: benchtop_monocular_laboratory_microscope

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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
import cadquery as cq
def _box(size: tuple[float, float, float], center: tuple[float, float, float], fillet: float | None = None):
    shape = cq.Workplane("XY").box(*size)
    if fillet is not None:
        shape = shape.edges("|Z").fillet(fillet)
    return shape.translate(center)
def _cyl_z(radius: float, length: float, center: tuple[float, float, float]):
    return cq.Workplane("XY").cylinder(length, radius).translate(center)
def _cyl_y(radius: float, length: float, center: tuple[float, float, float]):
    return cq.Workplane("XY").cylinder(length, radius).rotate((0, 0, 0), (1, 0, 0), 90).translate(center)
def _cyl_x(radius: float, length: float, center: tuple[float, float, float]):
    return cq.Workplane("XY").cylinder(length, radius).rotate((0, 0, 0), (0, 1, 0), 90).translate(center)
def _frame_shape():
    base_lower = _box((0.240, 0.165, 0.018), (0.0, 0.0, 0.009), fillet=0.013)
    base_upper = _box((0.180, 0.118, 0.020), (-0.018, 0.0, 0.028), fillet=0.009)
    pedestal = _box((0.102, 0.084, 0.050), (-0.032, 0.0, 0.055), fillet=0.007)
    rear_column = _box((0.056, 0.048, 0.150), (-0.040, 0.0, 0.140), fillet=0.005)
    bridge = (
        cq.Workplane("XY")
        .box(0.072, 0.048, 0.034)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -22.0)
        .translate((-0.030, 0.0, 0.224))
    )

    return (
        base_lower.union(base_upper)
        .union(pedestal)
        .union(rear_column)
        .union(bridge)
    )
def _substage_shape():
    stage_arm = _box((0.105, 0.044, 0.018), (0.035, 0.0, 0.118), fillet=0.004)
    stage_pad = _box((0.090, 0.054, 0.004), (0.055, 0.0, 0.127))
    support_web = _box((0.040, 0.042, 0.070), (0.015, 0.0, 0.097))
    condenser_body = _cyl_z(0.022, 0.028, (0.055, 0.0, 0.110))
    condenser_ring = _cyl_z(0.030, 0.010, (0.055, 0.0, 0.094))
    pivot_mount = _box((0.018, 0.020, 0.018), (0.065, 0.021, 0.104))

    return (
        stage_arm.union(stage_pad)
        .union(support_web)
        .union(condenser_body)
        .union(condenser_ring)
        .union(pivot_mount)
    )
def _body_carriage_shape():
    sleeve = _box((0.072, 0.064, 0.082), (0.0, 0.0, 0.0), fillet=0.005)
    objective_tube = _cyl_z(0.020, 0.094, (0.0, 0.0, -0.001))
    lower_collar = _cyl_z(0.026, 0.012, (0.0, 0.0, -0.040))
    guide_block = _box((0.014, 0.046, 0.080), (-0.033, 0.0, 0.010), fillet=0.002)
    prism_block = (
        cq.Workplane("XY")
        .box(0.050, 0.048, 0.030)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 16.0)
        .translate((-0.010, 0.0, 0.057))
    )
    return sleeve.union(objective_tube).union(lower_collar).union(guide_block).union(prism_block)
def _body_knobs_shape():
    shaft = _cyl_y(0.0055, 0.072, (-0.010, 0.0, 0.004))
    knob_a = _cyl_y(0.018, 0.010, (-0.010, 0.041, 0.004))
    knob_b = _cyl_y(0.018, 0.010, (-0.010, -0.041, 0.004))
    return shaft.union(knob_a).union(knob_b)
def _eyepiece_shape():
    eyepiece_tube = (
        cq.Workplane("XY")
        .cylinder(0.082, 0.015)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -34.0)
        .translate((-0.012, 0.0, 0.108))
    )
    eye_cup = (
        cq.Workplane("XY")
        .cylinder(0.036, 0.012)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -34.0)
        .translate((-0.036, 0.0, 0.140))
    )
    lens_ring = (
        cq.Workplane("XY")
        .cylinder(0.008, 0.014)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -34.0)
        .translate((-0.048, 0.0, 0.151))
    )
    return eyepiece_tube.union(eye_cup).union(lens_ring)
def _nosepiece_shape():
    turret = _cyl_z(0.026, 0.012, (0.0, 0.0, -0.006))
    hub = _cyl_z(0.013, 0.010, (0.0, 0.0, 0.003))
    collar = _cyl_z(0.018, 0.006, (0.0, 0.0, -0.015))

    barrels = None
    for angle_deg, radius, length in (
        (0.0, 0.0085, 0.034),
        (120.0, 0.0070, 0.026),
        (240.0, 0.0070, 0.022),
    ):
        angle = angle_deg * pi / 180.0
        x_pos = 0.017 * cos(angle)
        y_pos = 0.017 * sin(angle)
        barrel = _cyl_z(radius, length, (x_pos, y_pos, -0.012 - length / 2.0))
        barrels = barrel if barrels is None else barrels.union(barrel)

    return turret.union(hub).union(collar).union(barrels)
def _stage_shape():
    plate = cq.Workplane("XY").box(0.120, 0.084, 0.008)
    plate = plate.faces(">Z").workplane().rect(0.028, 0.022).cutThruAll()
    stage = plate
    stage = stage.union(_box((0.090, 0.042, 0.010), (0.0, 0.0, -0.006)))
    stage = stage.union(_box((0.060, 0.004, 0.006), (0.0, -0.024, 0.005)))
    stage = stage.union(_box((0.034, 0.004, 0.009), (0.018, 0.024, 0.006)))
    stage = stage.union(_box((0.012, 0.018, 0.020), (0.008, 0.048, -0.004)))
    return stage
def _stage_knobs_shape():
    shaft = _cyl_y(0.004, 0.020, (0.012, 0.060, -0.004))
    knob_large = _cyl_y(0.013, 0.008, (0.012, 0.072, -0.004))
    knob_small = _cyl_y(0.009, 0.006, (0.012, 0.066, -0.004))
    return shaft.union(knob_large).union(knob_small)
def _lever_shape():
    pivot_barrel = _cyl_x(0.004, 0.008, (0.004, 0.0, 0.0))
    root_bridge = _box((0.010, 0.010, 0.004), (0.008, 0.007, -0.002))
    arm = (
        cq.Workplane("XY")
        .box(0.018, 0.032, 0.004)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -18.0)
        .translate((0.011, 0.020, -0.004))
    )
    connector = _box((0.007, 0.010, 0.004), (0.018, 0.029, -0.005))
    tip = _cyl_y(0.003, 0.012, (0.022, 0.034, -0.006))
    return pivot_barrel.union(root_bridge).union(arm).union(connector).union(tip)
def _add_mesh_visual(part, shape, name: str, material: str, visual_name: str):
    part.visual(mesh_from_cadquery(shape, name), material=material, name=visual_name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="monocular_microscope")

    model.material("cast_metal", rgba=(0.64, 0.66, 0.69, 1.0))
    model.material("dark_enamel", rgba=(0.12, 0.13, 0.14, 1.0))
    model.material("black_rubber", rgba=(0.05, 0.05, 0.06, 1.0))
    model.material("brass", rgba=(0.73, 0.61, 0.26, 1.0))

    frame = model.part("frame")
    _add_mesh_visual(frame, _frame_shape(), "frame_body", "cast_metal", "frame_body")

    focus_guide = model.part("focus_guide")
    focus_guide.visual(
        Box((0.026, 0.046, 0.120)),
        origin=Origin(xyz=(0.002, 0.0, 0.252)),
        material="dark_enamel",
        name="guide_rail",
    )

    substage = model.part("substage")
    _add_mesh_visual(substage, _substage_shape(), "substage_body", "cast_metal", "substage_body")

    body_carriage = model.part("body_carriage")
    _add_mesh_visual(body_carriage, _body_carriage_shape(), "body_carriage_shell", "cast_metal", "carriage_shell")
    _add_mesh_visual(body_carriage, _body_knobs_shape(), "body_focus_knobs", "dark_enamel", "focus_knobs")
    _add_mesh_visual(body_carriage, _eyepiece_shape(), "body_eyepiece", "black_rubber", "eyepiece")

    nosepiece = model.part("nosepiece")
    _add_mesh_visual(nosepiece, _nosepiece_shape(), "nosepiece_body", "brass", "nosepiece_body")

    stage_carriage = model.part("stage_carriage")
    stage_carriage.visual(
        mesh_from_cadquery(_stage_shape(), "stage_carriage_body"),
        material="dark_enamel",
        name="stage_body",
    )
    stage_carriage.visual(
        mesh_from_cadquery(_stage_knobs_shape(), "stage_controls"),
        material="dark_enamel",
        name="guide_controls",
    )

    diaphragm_lever = model.part("diaphragm_lever")
    _add_mesh_visual(diaphragm_lever, _lever_shape(), "diaphragm_lever", "dark_enamel", "lever_body")

    model.articulation(
        "frame_to_focus_guide",
        ArticulationType.FIXED,
        parent=frame,
        child=focus_guide,
        origin=Origin(),
    )
    model.articulation(
        "frame_to_substage",
        ArticulationType.FIXED,
        parent=frame,
        child=substage,
        origin=Origin(),
    )

    model.articulation(
        "focus_slide",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=body_carriage,
        origin=Origin(xyz=(0.055, 0.0, 0.265)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.055, effort=18.0, velocity=0.060),
    )
    model.articulation(
        "nosepiece_spin",
        ArticulationType.CONTINUOUS,
        parent=body_carriage,
        child=nosepiece,
        origin=Origin(xyz=(0.0, 0.0, -0.052)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=4.0),
    )
    model.articulation(
        "stage_slide",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=stage_carriage,
        origin=Origin(xyz=(0.055, 0.0, 0.143)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.020, upper=0.020, effort=10.0, velocity=0.030),
    )
    model.articulation(
        "diaphragm_pivot",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=diaphragm_lever,
        origin=Origin(xyz=(0.074, 0.030, 0.104)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=-0.45, upper=0.45, effort=1.0, velocity=1.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
