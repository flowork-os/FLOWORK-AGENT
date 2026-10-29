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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
import cadquery as cq
def _rounded_box_shape(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """CadQuery rounded box with its bottom face on local z=0."""
    sx, sy, sz = size
    fillet = min(radius, sx * 0.20, sy * 0.20, sz * 0.20)
    return (
        cq.Workplane("XY")
        .box(sx, sy, sz)
        .edges()
        .fillet(fillet)
        .translate((0.0, 0.0, sz / 2.0))
    )
def _curved_arm_shape() -> cq.Workplane:
    """Low, swept side plate that forms the microscope's short curved arm."""
    # Coordinates are (front/back Y, vertical Z) in the YZ workplane.
    pts = [
        (0.070, 0.040),
        (0.090, 0.040),
        (0.093, 0.080),
        (0.091, 0.130),
        (0.086, 0.190),
        (0.069, 0.252),
        (0.034, 0.296),
        (-0.012, 0.309),
        (-0.054, 0.306),
        (-0.066, 0.282),
        (-0.051, 0.244),
        (-0.009, 0.235),
        (0.028, 0.202),
        (0.037, 0.144),
        (0.032, 0.079),
        (0.052, 0.048),
    ]
    wp = cq.Workplane("YZ").moveTo(*pts[0])
    for p in pts[1:]:
        wp = wp.lineTo(*p)
    return wp.close().extrude(0.065).translate((-0.0325, 0.0, 0.0))
def _stage_plate_shape() -> cq.Workplane:
    """Compact square stage plate with a central optical aperture."""
    return (
        cq.Workplane("XY")
        .box(0.105, 0.095, 0.010)
        .edges("|Z")
        .fillet(0.004)
        .faces(">Z")
        .workplane()
        .hole(0.026)
        .translate((0.0, 0.0, 0.005))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="low_profile_monocular_microscope")

    model.material("black_enamel", rgba=(0.035, 0.040, 0.045, 1.0))
    model.material("charcoal", rgba=(0.13, 0.14, 0.15, 1.0))
    model.material("warm_gray", rgba=(0.42, 0.43, 0.42, 1.0))
    model.material("stage_metal", rgba=(0.72, 0.73, 0.70, 1.0))
    model.material("polished_steel", rgba=(0.82, 0.84, 0.86, 1.0))
    model.material("rubber", rgba=(0.015, 0.016, 0.017, 1.0))
    model.material("glass", rgba=(0.45, 0.72, 0.92, 0.55))

    stand = model.part("stand")
    stand.visual(
        mesh_from_cadquery(_rounded_box_shape((0.240, 0.220, 0.040), 0.012), "thick_base"),
        material="black_enamel",
        name="thick_base",
    )
    stand.visual(
        mesh_from_cadquery(_curved_arm_shape(), "curved_arm"),
        material="warm_gray",
        name="curved_arm",
    )
    stand.visual(
        Box((0.065, 0.065, 0.052)),
        origin=Origin(xyz=(0.0, -0.085, 0.066)),
        material="charcoal",
        name="stage_pedestal",
    )
    for y_pos, name in ((-0.105, "stage_rail_0"), (-0.065, "stage_rail_1")):
        stand.visual(
            Cylinder(radius=0.0035, length=0.165),
            origin=Origin(xyz=(0.0, y_pos, 0.0955), rpy=(0.0, pi / 2.0, 0.0)),
            material="polished_steel",
            name=name,
        )
    for x_pos, name in ((-0.045, "guide_rod_0"), (0.045, "guide_rod_1")):
        stand.visual(
            Cylinder(radius=0.0045, length=0.150),
            origin=Origin(xyz=(x_pos, -0.0675, 0.220)),
            material="polished_steel",
            name=name,
        )
    stand.visual(
        Box((0.024, 0.019, 0.018)),
        origin=Origin(xyz=(-0.045, -0.0675, 0.145)),
        material="charcoal",
        name="lower_guide_block_0",
    )
    stand.visual(
        Box((0.024, 0.019, 0.018)),
        origin=Origin(xyz=(0.045, -0.0675, 0.145)),
        material="charcoal",
        name="lower_guide_block_1",
    )
    stand.visual(
        Box((0.120, 0.019, 0.018)),
        origin=Origin(xyz=(0.0, -0.0675, 0.294)),
        material="charcoal",
        name="upper_guide_block",
    )

    stage_carrier = model.part("stage_carrier")
    stage_carrier.visual(
        Box((0.130, 0.052, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material="charcoal",
        name="slide_saddle",
    )
    stage_carrier.visual(
        mesh_from_cadquery(_stage_plate_shape(), "stage_plate"),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material="stage_metal",
        name="stage_plate",
    )
    stage_carrier.visual(
        Cylinder(radius=0.016, length=0.0015),
        origin=Origin(xyz=(0.0, 0.0, 0.01775)),
        material="rubber",
        name="black_aperture",
    )
    for x_pos, name in ((-0.026, "slide_clip_0"), (0.026, "slide_clip_1")):
        stage_carrier.visual(
            Box((0.034, 0.006, 0.003)),
            origin=Origin(xyz=(x_pos, 0.032, 0.0185)),
            material="polished_steel",
            name=name,
        )

    head_carriage = model.part("head_carriage")
    head_carriage.visual(
        Box((0.110, 0.026, 0.055)),
        origin=Origin(xyz=(0.0, 0.0, 0.032)),
        material="charcoal",
        name="slide_block",
    )
    head_carriage.visual(
        mesh_from_cadquery(_rounded_box_shape((0.075, 0.078, 0.056), 0.008), "head_shell"),
        origin=Origin(xyz=(0.0, -0.028, 0.002)),
        material="black_enamel",
        name="head_shell",
    )
    # The socket face terminates at the turret joint plane; the rotating disk
    # contacts it from below without using a broad inter-part overlap.
    head_carriage.visual(
        Cylinder(radius=0.016, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, -0.003)),
        material="black_enamel",
        name="turret_socket",
    )
    eyepiece_roll = 0.70
    tube_axis_y = -sin(eyepiece_roll)
    tube_axis_z = cos(eyepiece_roll)
    tube_start = (0.0, -0.030, 0.054)
    tube_len = 0.086
    tube_center = (
        0.0,
        tube_start[1] + tube_axis_y * tube_len / 2.0,
        tube_start[2] + tube_axis_z * tube_len / 2.0,
    )
    head_carriage.visual(
        Cylinder(radius=0.016, length=tube_len),
        origin=Origin(xyz=tube_center, rpy=(eyepiece_roll, 0.0, 0.0)),
        material="black_enamel",
        name="eyepiece_tube",
    )
    cap_len = 0.026
    cap_center = (
        0.0,
        tube_start[1] + tube_axis_y * (tube_len + cap_len / 2.0),
        tube_start[2] + tube_axis_z * (tube_len + cap_len / 2.0),
    )
    head_carriage.visual(
        Cylinder(radius=0.020, length=cap_len),
        origin=Origin(xyz=cap_center, rpy=(eyepiece_roll, 0.0, 0.0)),
        material="rubber",
        name="eyepiece_cup",
    )
    lens_center = (
        0.0,
        tube_start[1] + tube_axis_y * (tube_len + cap_len + 0.001),
        tube_start[2] + tube_axis_z * (tube_len + cap_len + 0.001),
    )
    head_carriage.visual(
        Cylinder(radius=0.014, length=0.003),
        origin=Origin(xyz=lens_center, rpy=(eyepiece_roll, 0.0, 0.0)),
        material="glass",
        name="eyepiece_glass",
    )

    nosepiece = model.part("nosepiece")
    nosepiece.visual(
        Cylinder(radius=0.028, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -0.007)),
        material="charcoal",
        name="turret_disk",
    )
    for i, angle in enumerate((0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0)):
        x_pos = 0.018 * sin(angle)
        y_pos = -0.018 * cos(angle)
        nosepiece.visual(
            Cylinder(radius=0.0065, length=0.040),
            origin=Origin(xyz=(x_pos, y_pos, -0.031)),
            material="polished_steel",
            name=f"objective_{i}",
        )
        nosepiece.visual(
            Cylinder(radius=0.0075, length=0.010),
            origin=Origin(xyz=(x_pos, y_pos, -0.041)),
            material="black_enamel",
            name=f"objective_band_{i}",
        )
        nosepiece.visual(
            Cylinder(radius=0.0045, length=0.0025),
            origin=Origin(xyz=(x_pos, y_pos, -0.05225)),
            material="glass",
            name=f"objective_lens_{i}",
        )

    model.articulation(
        "stage_slide",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=stage_carrier,
        origin=Origin(xyz=(0.0, -0.085, 0.106)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=-0.030, upper=0.030, effort=24.0, velocity=0.12),
    )
    model.articulation(
        "focus_slide",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=head_carriage,
        origin=Origin(xyz=(0.0, -0.085, 0.198)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.055, effort=18.0, velocity=0.08),
    )
    model.articulation(
        "turret",
        ArticulationType.REVOLUTE,
        parent=head_carriage,
        child=nosepiece,
        origin=Origin(xyz=(0.0, 0.0, -0.009)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-2.20, upper=2.20, effort=1.2, velocity=2.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
