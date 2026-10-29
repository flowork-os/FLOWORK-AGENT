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

# ===== model =====
import math
import cadquery as cq
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """A centered, softly filleted rectangular casting."""
    return cq.Workplane("XY").box(*size).edges("|Z").fillet(radius)
def _stage_plate(size: tuple[float, float, float], aperture_radius: float) -> cq.Workplane:
    """A centered mechanical-stage plate with a real optical aperture."""
    sx, sy, sz = size
    return (
        cq.Workplane("XY")
        .box(sx, sy, sz)
        .edges("|Z")
        .fillet(0.004)
        .faces(">Z")
        .workplane()
        .hole(2.0 * aperture_radius)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="teaching_microscope")

    cream = model.material("warm_off_white_enamel", color=(0.82, 0.80, 0.72, 1.0))
    black = model.material("matte_black", color=(0.015, 0.015, 0.018, 1.0))
    dark = model.material("dark_oxide", color=(0.08, 0.085, 0.09, 1.0))
    metal = model.material("brushed_metal", color=(0.62, 0.64, 0.62, 1.0))
    glass = model.material("blue_green_glass", color=(0.35, 0.70, 0.85, 0.45))
    brass = model.material("aged_brass", color=(0.62, 0.45, 0.18, 1.0))

    # Root casting and support structure: broad bench base, rear focusing column,
    # and an offset side arm that reads as the microscope's carrying arm.
    stand = model.part("stand")
    stand.visual(
        mesh_from_cadquery(_rounded_box((0.260, 0.180, 0.028), 0.018), "rounded_base"),
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        material=cream,
        name="base_casting",
    )
    stand.visual(
        Cylinder(radius=0.018, length=0.086),
        origin=Origin(xyz=(-0.035, 0.0, 0.071)),
        material=cream,
        name="stage_pedestal",
    )
    stand.visual(
        Box((0.070, 0.095, 0.006)),
        origin=Origin(xyz=(-0.035, 0.0, 0.107)),
        material=cream,
        name="stage_yoke_web",
    )
    stand.visual(
        Box((0.055, 0.020, 0.008)),
        origin=Origin(xyz=(-0.035, 0.046, 0.110)),
        material=cream,
        name="stage_yoke_pad_0",
    )
    stand.visual(
        Box((0.055, 0.020, 0.008)),
        origin=Origin(xyz=(-0.035, -0.046, 0.110)),
        material=cream,
        name="stage_yoke_pad_1",
    )
    stand.visual(
        Box((0.030, 0.040, 0.246)),
        origin=Origin(xyz=(0.065, 0.0, 0.151)),
        material=cream,
        name="focus_column",
    )
    stand.visual(
        Box((0.006, 0.048, 0.170)),
        origin=Origin(xyz=(0.0475, 0.0, 0.190)),
        material=dark,
        name="focus_rail",
    )
    stand.visual(
        Box((0.230, 0.024, 0.026)),
        origin=Origin(xyz=(0.065, -0.066, 0.158), rpy=(0.0, -1.887, 0.0)),
        material=cream,
        name="side_arm",
    )
    stand.visual(
        Box((0.060, 0.026, 0.030)),
        origin=Origin(xyz=(0.102, -0.066, 0.043)),
        material=cream,
        name="arm_foot",
    )
    stand.visual(
        Box((0.036, 0.070, 0.034)),
        origin=Origin(xyz=(0.064, -0.036, 0.262)),
        material=cream,
        name="arm_boss",
    )

    # A separate fixed mechanical stage.  The plate has a real through aperture;
    # guide rails and a side bracket carry the moving side carriage and knobs.
    stage = model.part("stage")
    stage.visual(
        mesh_from_cadquery(_stage_plate((0.140, 0.100, 0.012), 0.035), "stage_plate"),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=black,
        name="stage_plate",
    )
    stage.visual(
        Box((0.120, 0.006, 0.006)),
        origin=Origin(xyz=(0.000, 0.032, 0.015)),
        material=metal,
        name="inner_guide_rail",
    )
    stage.visual(
        Box((0.120, 0.006, 0.006)),
        origin=Origin(xyz=(0.000, 0.045, 0.015)),
        material=metal,
        name="outer_guide_rail",
    )
    stage.visual(
        Box((0.090, 0.020, 0.026)),
        origin=Origin(xyz=(0.035, 0.064, 0.018)),
        material=dark,
        name="stage_bracket",
    )
    stage.visual(
        Box((0.086, 0.010, 0.010)),
        origin=Origin(xyz=(0.034, 0.052, 0.009)),
        material=dark,
        name="bracket_web",
    )
    stage.visual(
        Box((0.048, 0.012, 0.004)),
        origin=Origin(xyz=(-0.030, -0.035, 0.014)),
        material=metal,
        name="slide_clip",
    )

    model.articulation(
        "stand_to_stage",
        ArticulationType.FIXED,
        parent=stand,
        child=stage,
        origin=Origin(xyz=(-0.035, 0.0, 0.114)),
    )

    # Side carriage: the moving member of the mechanical stage guide.
    side_carriage = model.part("side_carriage")
    side_carriage.visual(
        Box((0.052, 0.030, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=metal,
        name="carriage_plate",
    )
    side_carriage.visual(
        Box((0.060, 0.006, 0.010)),
        origin=Origin(xyz=(0.0, -0.010, 0.010)),
        material=dark,
        name="carriage_grip",
    )
    model.articulation(
        "stage_to_side_carriage",
        ArticulationType.PRISMATIC,
        parent=stage,
        child=side_carriage,
        origin=Origin(xyz=(-0.010, 0.0385, 0.018)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=0.08, lower=-0.026, upper=0.026),
    )

    # Distinct coaxial stage-axis controls on the side bracket.
    inner_knob = model.part("inner_stage_knob")
    inner_knob.visual(
        Cylinder(radius=0.006, length=0.006),
        origin=Origin(xyz=(0.0, 0.003, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="inner_stem",
    )
    inner_knob.visual(
        Cylinder(radius=0.015, length=0.026),
        origin=Origin(xyz=(0.0, 0.019, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="inner_knob_cap",
    )
    inner_knob.visual(
        Cylinder(radius=0.016, length=0.004),
        origin=Origin(xyz=(0.0, 0.033, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark,
        name="inner_knurled_rim",
    )
    model.articulation(
        "stage_to_inner_knob",
        ArticulationType.CONTINUOUS,
        parent=stage,
        child=inner_knob,
        origin=Origin(xyz=(0.035, 0.074, 0.020)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=8.0),
    )

    outer_knob = model.part("outer_stage_knob")
    outer_knob.visual(
        Cylinder(radius=0.012, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="outer_knob_cap",
    )
    outer_knob.visual(
        Cylinder(radius=0.013, length=0.004),
        origin=Origin(xyz=(0.0, 0.011, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark,
        name="outer_knurled_rim",
    )
    model.articulation(
        "inner_to_outer_knob",
        ArticulationType.CONTINUOUS,
        parent=inner_knob,
        child=outer_knob,
        origin=Origin(xyz=(0.0, 0.044, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.3, velocity=10.0),
    )

    # Sliding optical body with monocular tube, eyepiece, and nosepiece collar.
    optical_body = model.part("optical_body")
    optical_body.visual(
        Box((0.018, 0.050, 0.085)),
        origin=Origin(xyz=(-0.009, 0.0, 0.000)),
        material=dark,
        name="slide_plate",
    )
    optical_body.visual(
        Box((0.048, 0.042, 0.036)),
        origin=Origin(xyz=(-0.034, 0.0, -0.010)),
        material=cream,
        name="body_bridge",
    )
    optical_body.visual(
        Box((0.078, 0.060, 0.042)),
        origin=Origin(xyz=(-0.080, 0.0, -0.026)),
        material=cream,
        name="head_block",
    )
    optical_body.visual(
        Cylinder(radius=0.018, length=0.020),
        origin=Origin(xyz=(-0.080, 0.0, -0.048)),
        material=cream,
        name="nosepiece_neck",
    )
    optical_body.visual(
        Cylinder(radius=0.022, length=0.018),
        origin=Origin(xyz=(-0.080, 0.0, -0.058)),
        material=dark,
        name="nosepiece_collar",
    )
    optical_body.visual(
        Cylinder(radius=0.018, length=0.022),
        origin=Origin(xyz=(-0.070, 0.0, 0.001), rpy=(0.0, 0.55, 0.0)),
        material=cream,
        name="tube_socket",
    )
    optical_body.visual(
        Cylinder(radius=0.014, length=0.110),
        origin=Origin(xyz=(-0.039, 0.0, 0.056), rpy=(0.0, 0.55, 0.0)),
        material=black,
        name="monocular_tube",
    )
    optical_body.visual(
        Cylinder(radius=0.019, length=0.034),
        origin=Origin(xyz=(-0.002, 0.0, 0.111), rpy=(0.0, 0.55, 0.0)),
        material=black,
        name="eyepiece",
    )
    optical_body.visual(
        Cylinder(radius=0.010, length=0.004),
        origin=Origin(xyz=(0.007, 0.0, 0.126), rpy=(0.0, 0.55, 0.0)),
        material=glass,
        name="ocular_lens",
    )
    model.articulation(
        "stand_to_optical_body",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=optical_body,
        origin=Origin(xyz=(0.0445, 0.0, 0.230)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=40.0, velocity=0.05, lower=0.0, upper=0.050),
    )

    # Rotating objective turret.  Its barrels are part of the turret so the full
    # objective cluster spins continuously about the nosepiece axis.
    turret = model.part("turret")
    turret.visual(
        Cylinder(radius=0.034, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, -0.006)),
        material=dark,
        name="turret_disk",
    )
    for i, (x, y, radius, length) in enumerate(
        (
            (0.020, 0.000, 0.0055, 0.034),
            (-0.010, 0.017, 0.0060, 0.038),
            (-0.010, -0.017, 0.0045, 0.030),
        )
    ):
        turret.visual(
            Cylinder(radius=radius, length=length),
            origin=Origin(xyz=(x, y, -0.012 - length / 2.0)),
            material=brass if i == 0 else metal,
            name=f"objective_{i}",
        )
        turret.visual(
            Cylinder(radius=radius * 1.35, length=0.005),
            origin=Origin(xyz=(x, y, -0.014)),
            material=dark,
            name=f"objective_collar_{i}",
        )
    model.articulation(
        "body_to_turret",
        ArticulationType.CONTINUOUS,
        parent=optical_body,
        child=turret,
        origin=Origin(xyz=(-0.080, 0.0, -0.067)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=4.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
