# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, benchtop_monocular_laboratory_microscope, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: benchtop_monocular_laboratory_microscope

from __future__ import annotations

import cadquery as cq
import math
from math import acos, atan2, cos, isfinite, pi, sin, sqrt, tan

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

# ===== sweeps (2 syms) =====
def _v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def _v_scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)

# ===== model =====
import math
import cadquery as cq
TILT_DEG = 30.0
TILT_RAD = math.radians(TILT_DEG)
OPTICAL_AXIS = (0.0, -math.sin(TILT_RAD), math.cos(TILT_RAD))
NOSE_JOINT = (0.0, 0.135, 0.054)
STAGE_Y = 0.095
PIVOT_Y = 0.113
def _v_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _v_scale(v: tuple[float, float, float], s: float) -> tuple[float, float, float]:
    return (v[0] * s, v[1] * s, v[2] * s)
def _box(size: tuple[float, float, float], center: tuple[float, float, float], fillet: float | None = None):
    shape = cq.Workplane("XY").box(*size).translate(center)
    if fillet is not None and fillet > 0.0:
        shape = shape.edges("|Z").fillet(fillet)
    return shape
def _cyl_z(radius: float, length: float, center: tuple[float, float, float] = (0.0, 0.0, 0.0)):
    return cq.Workplane("XY").circle(radius).extrude(length / 2.0, both=True).translate(center)
def _ring_z(
    outer_radius: float,
    inner_radius: float,
    length: float,
    center: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length / 2.0, both=True)
        .translate(center)
    )
def _tilt_about_x(shape, angle_deg: float = TILT_DEG):
    return shape.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
def _add_mesh_visual(part, shape, name: str, material: str) -> None:
    part.visual(mesh_from_cadquery(shape, name), material=material, name=name)
def _base_cast_shape():
    rear_pad = _box((0.115, 0.120, 0.020), (0.0, -0.032, 0.010), fillet=0.010)
    left_foot = _box((0.052, 0.092, 0.016), (-0.046, 0.064, 0.008), fillet=0.009)
    right_foot = _box((0.052, 0.092, 0.016), (0.046, 0.064, 0.008), fillet=0.009)
    bridge = _box((0.040, 0.040, 0.014), (0.0, 0.020, 0.007), fillet=0.005)
    column_boss = _cyl_z(0.030, 0.010, (0.0, -0.055, 0.025))
    return rear_pad.union(left_foot).union(right_foot).union(bridge).union(column_boss)
def _nosepiece_collar_shape():
    return _tilt_about_x(_ring_z(0.020, 0.0105, 0.014)).translate(NOSE_JOINT)
def _stage_bridge_shape():
    return _box((0.042, 0.090, 0.014), (0.0, 0.062, -0.005), fillet=0.003)
def _stage_guide_shape():
    base_plate = _box((0.040, 0.110, 0.004), (0.0, STAGE_Y, 0.002))
    left_rail = _box((0.008, 0.110, 0.008), (-0.016, STAGE_Y, 0.006))
    right_rail = _box((0.008, 0.110, 0.008), (0.016, STAGE_Y, 0.006))
    return base_plate.union(left_rail).union(right_rail)
def _condenser_housing_shape():
    stem = _box((0.012, 0.018, 0.028), (0.0, STAGE_Y, -0.014), fillet=0.002)
    housing = _cyl_z(0.018, 0.030, (0.0, STAGE_Y, -0.043))
    lower_ring = _cyl_z(0.011, 0.012, (0.0, STAGE_Y, -0.064))
    support_tab = _box((0.024, 0.012, 0.004), (0.012, PIVOT_Y, -0.047))
    return stem.union(housing).union(lower_ring).union(support_tab)
def _stage_plate_shape():
    plate = cq.Workplane("XY").box(0.095, 0.090, 0.004)
    opening = cq.Workplane("XY").box(0.040, 0.040, 0.012)
    return plate.cut(opening).translate((0.0, 0.0, 0.014))
def _stage_saddle_shape():
    return _box((0.018, 0.105, 0.012), (0.0, 0.0, 0.006), fillet=0.0015)
def _turret_hub_shape():
    disk = _cyl_z(0.021, 0.006, (0.0, 0.0, -0.008))
    spindle = _cyl_z(0.0105, 0.016, (0.0, 0.0, 0.001))
    return disk.union(spindle)
def _objective_shape(length: float, angle_deg: float):
    angle_rad = math.radians(angle_deg)
    radius = 0.012
    center = (radius * math.cos(angle_rad), radius * math.sin(angle_rad), -0.011 - length / 2.0)
    return _cyl_z(0.0055, length, center)
def _lever_shape():
    hub = _ring_z(0.0055, 0.0032, 0.004)
    arm = _box((0.004, 0.026, 0.004), (0.0, 0.016, 0.0))
    tip = _cyl_z(0.0035, 0.004, (0.0, 0.030, 0.0))
    return hub.union(arm).union(tip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="clinical_monocular_microscope")

    model.material("cast_gray", rgba=(0.62, 0.64, 0.67, 1.0))
    model.material("enamel_gray", rgba=(0.78, 0.79, 0.80, 1.0))
    model.material("stage_black", rgba=(0.10, 0.10, 0.11, 1.0))
    model.material("optic_black", rgba=(0.15, 0.16, 0.18, 1.0))
    model.material("steel_dark", rgba=(0.32, 0.34, 0.37, 1.0))

    stand = model.part("stand")
    _add_mesh_visual(stand, _base_cast_shape(), "base_cast", "cast_gray")
    stand.visual(
        Cylinder(radius=0.014, length=0.220),
        origin=Origin(xyz=(0.0, -0.055, 0.130)),
        material="steel_dark",
        name="column",
    )
    _add_mesh_visual(
        stand,
        _box((0.038, 0.032, 0.060), (0.0, -0.074, 0.050), fillet=0.003),
        "rear_brace",
        "cast_gray",
    )

    carriage = model.part("carriage")
    _add_mesh_visual(carriage, _ring_z(0.027, 0.016, 0.082), "column_sleeve", "enamel_gray")
    carriage.visual(
        Box((0.002, 0.010, 0.060)),
        origin=Origin(xyz=(0.015, 0.0, 0.0)),
        material="steel_dark",
        name="guide_pad",
    )
    carriage.visual(
        Box((0.030, 0.034, 0.082)),
        origin=Origin(xyz=(0.0, 0.0425, 0.062)),
        material="enamel_gray",
        name="rear_body",
    )
    carriage.visual(
        Box((0.034, 0.054, 0.040)),
        origin=Origin(xyz=(0.0, 0.050, 0.094)),
        material="enamel_gray",
        name="upper_body",
    )
    carriage.visual(
        Box((0.022, 0.032, 0.072)),
        origin=Origin(xyz=(0.0, 0.085, 0.068)),
        material="enamel_gray",
        name="head_support",
    )
    carriage.visual(
        Box((0.014, 0.022, 0.014)),
        origin=Origin(xyz=(0.0, 0.106, 0.050)),
        material="enamel_gray",
        name="collar_support",
    )
    carriage.visual(
        Box((0.018, 0.018, 0.020)),
        origin=Origin(xyz=(0.0, 0.030, 0.012)),
        material="enamel_gray",
        name="stage_pillar",
    )
    carriage.visual(
        Cylinder(radius=0.018, length=0.110),
        origin=Origin(xyz=_v_add(NOSE_JOINT, _v_scale(OPTICAL_AXIS, 0.090)), rpy=(TILT_RAD, 0.0, 0.0)),
        material="enamel_gray",
        name="main_tube",
    )
    carriage.visual(
        Cylinder(radius=0.013, length=0.090),
        origin=Origin(xyz=_v_add(NOSE_JOINT, _v_scale(OPTICAL_AXIS, 0.165)), rpy=(TILT_RAD, 0.0, 0.0)),
        material="optic_black",
        name="eyepiece_tube",
    )
    carriage.visual(
        Cylinder(radius=0.0145, length=0.020),
        origin=Origin(xyz=_v_add(NOSE_JOINT, _v_scale(OPTICAL_AXIS, 0.210)), rpy=(TILT_RAD, 0.0, 0.0)),
        material="optic_black",
        name="ocular_cap",
    )
    carriage.visual(
        Cylinder(radius=0.013, length=0.020),
        origin=Origin(xyz=(-0.025, 0.044, 0.026), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="optic_black",
        name="coarse_knob_0",
    )
    carriage.visual(
        Cylinder(radius=0.013, length=0.020),
        origin=Origin(xyz=(0.025, 0.044, 0.026), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="optic_black",
        name="coarse_knob_1",
    )
    carriage.visual(
        Cylinder(radius=0.0065, length=0.012),
        origin=Origin(xyz=(-0.034, 0.044, 0.026), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="steel_dark",
        name="fine_knob_0",
    )
    carriage.visual(
        Cylinder(radius=0.0065, length=0.012),
        origin=Origin(xyz=(0.034, 0.044, 0.026), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="steel_dark",
        name="fine_knob_1",
    )
    _add_mesh_visual(carriage, _nosepiece_collar_shape(), "nosepiece_collar", "optic_black")
    _add_mesh_visual(carriage, _stage_bridge_shape(), "stage_bridge", "enamel_gray")
    _add_mesh_visual(carriage, _stage_guide_shape(), "stage_guide", "steel_dark")
    _add_mesh_visual(carriage, _condenser_housing_shape(), "condenser_housing", "optic_black")
    carriage.visual(
        Cylinder(radius=0.0032, length=0.008),
        origin=Origin(xyz=(0.020, PIVOT_Y, -0.043)),
        material="steel_dark",
        name="pivot_pin",
    )

    stage = model.part("stage")
    _add_mesh_visual(stage, _stage_plate_shape(), "stage_plate", "stage_black")
    _add_mesh_visual(stage, _stage_saddle_shape(), "stage_saddle", "steel_dark")

    turret = model.part("turret")
    _add_mesh_visual(turret, _turret_hub_shape(), "turret_hub", "optic_black")
    _add_mesh_visual(turret, _objective_shape(0.024, 0.0), "objective_0", "optic_black")
    _add_mesh_visual(turret, _objective_shape(0.030, 120.0), "objective_1", "optic_black")
    _add_mesh_visual(turret, _objective_shape(0.020, 240.0), "objective_2", "optic_black")

    diaphragm_lever = model.part("diaphragm_lever")
    _add_mesh_visual(diaphragm_lever, _lever_shape(), "lever", "steel_dark")

    focus_slide = model.articulation(
        "stand_to_carriage",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=carriage,
        origin=Origin(xyz=(0.0, -0.055, 0.145)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-0.020, upper=0.040, effort=140.0, velocity=0.060),
    )
    stage_slide = model.articulation(
        "carriage_to_stage",
        ArticulationType.PRISMATIC,
        parent=carriage,
        child=stage,
        origin=Origin(xyz=(0.0, STAGE_Y, 0.004)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.022, upper=0.022, effort=40.0, velocity=0.040),
    )
    turret_spin = model.articulation(
        "carriage_to_turret",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=turret,
        origin=Origin(xyz=NOSE_JOINT, rpy=(TILT_RAD, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=10.0, velocity=4.0),
    )
    iris_lever = model.articulation(
        "carriage_to_diaphragm_lever",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=diaphragm_lever,
        origin=Origin(xyz=(0.020, PIVOT_Y, -0.043)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-0.55, upper=0.55, effort=2.0, velocity=2.0),
    )

    focus_slide.meta["qc_samples"] = [-0.020, 0.0, 0.040]
    stage_slide.meta["qc_samples"] = [-0.022, 0.0, 0.022]
    turret_spin.meta["qc_samples"] = [0.0, 1.7, 3.4]
    iris_lever.meta["qc_samples"] = [-0.55, 0.0, 0.55]

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
