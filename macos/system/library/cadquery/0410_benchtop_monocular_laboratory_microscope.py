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
    """CadQuery box with gently rounded vertical edges, already centered at origin."""

    return cq.Workplane("XY").box(*size).edges("|Z").fillet(radius)
def _swept_arm() -> cq.Workplane:
    """A broad, swept microscope arm extruded through the width of the stand."""

    profile = [
        (-0.116, 0.030),
        (-0.074, 0.030),
        (-0.049, 0.105),
        (-0.047, 0.294),
        (-0.080, 0.320),
        (-0.112, 0.276),
        (-0.130, 0.120),
    ]
    return (
        cq.Workplane("XZ")
        .polyline(profile)
        .close()
        .extrude(0.055, both=True)
        .edges("|Y")
        .fillet(0.004)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_monocular_microscope")

    body_white = Material("warm_white_enamel", rgba=(0.86, 0.84, 0.78, 1.0))
    dark_metal = Material("charcoal_metal", rgba=(0.05, 0.055, 0.06, 1.0))
    brushed = Material("brushed_steel", rgba=(0.66, 0.68, 0.66, 1.0))
    black = Material("black_rubber", rgba=(0.006, 0.006, 0.007, 1.0))
    glass = Material("slide_glass", rgba=(0.72, 0.90, 1.0, 0.38))

    for material in (body_white, dark_metal, brushed, black, glass):
        model.material(material)

    frame = model.part("frame")

    base_mesh = _rounded_box((0.240, 0.160, 0.032), 0.007).translate((0.0, 0.0, 0.016))
    frame.visual(
        mesh_from_cadquery(base_mesh, "rounded_rectangular_base", tolerance=0.0008),
        material=dark_metal,
        name="base",
    )
    frame.visual(
        mesh_from_cadquery(_swept_arm(), "swept_arm", tolerance=0.0008),
        material=body_white,
        name="swept_arm",
    )

    # Fixed stage and its single pedestal.
    frame.visual(
        Box((0.050, 0.070, 0.116)),
        origin=Origin(xyz=(0.018, 0.0, 0.088)),
        material=body_white,
        name="stage_pedestal",
    )
    frame.visual(
        Box((0.145, 0.125, 0.014)),
        origin=Origin(xyz=(0.032, 0.0, 0.145)),
        material=dark_metal,
        name="stage_plate",
    )
    frame.visual(
        Box((0.132, 0.010, 0.003)),
        origin=Origin(xyz=(0.032, -0.055, 0.1505)),
        material=brushed,
        name="stage_rail_0",
    )
    frame.visual(
        Box((0.132, 0.010, 0.003)),
        origin=Origin(xyz=(0.032, 0.055, 0.1505)),
        material=brushed,
        name="stage_rail_1",
    )

    # Twin vertical guide rails on the front of the swept arm.
    frame.visual(
        Box((0.018, 0.014, 0.205)),
        origin=Origin(xyz=(-0.052, -0.034, 0.198)),
        material=brushed,
        name="guide_rail_0",
    )
    frame.visual(
        Box((0.018, 0.014, 0.205)),
        origin=Origin(xyz=(-0.052, 0.034, 0.198)),
        material=brushed,
        name="guide_rail_1",
    )

    # A split bearing yoke captures the focus shaft without filling the shaft space.
    frame.visual(
        Box((0.040, 0.048, 0.010)),
        origin=Origin(xyz=(-0.130, 0.0, 0.218)),
        material=body_white,
        name="focus_upper_lug",
    )
    frame.visual(
        Box((0.040, 0.048, 0.010)),
        origin=Origin(xyz=(-0.130, 0.0, 0.192)),
        material=body_white,
        name="focus_lower_lug",
    )

    slide_carriage = model.part("slide_carriage")
    slide_carriage.visual(
        Box((0.112, 0.045, 0.006)),
        origin=Origin(),
        material=brushed,
        name="carriage_plate",
    )
    slide_carriage.visual(
        Box((0.032, 0.080, 0.006)),
        origin=Origin(xyz=(-0.038, 0.050, 0.0)),
        material=brushed,
        name="projecting_tongue",
    )
    slide_carriage.visual(
        Box((0.078, 0.026, 0.0015)),
        origin=Origin(xyz=(0.006, -0.002, 0.00375)),
        material=glass,
        name="glass_slide",
    )

    model.articulation(
        "stage_to_carriage",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=slide_carriage,
        origin=Origin(xyz=(0.032, 0.0, 0.155)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=0.12, lower=-0.035, upper=0.035),
    )

    head_carriage = model.part("head_carriage")
    head_carriage.visual(
        Box((0.046, 0.088, 0.060)),
        origin=Origin(),
        material=body_white,
        name="slider_block",
    )
    head_carriage.visual(
        Box((0.056, 0.052, 0.026)),
        origin=Origin(xyz=(0.030, 0.0, -0.015)),
        material=body_white,
        name="head_neck",
    )
    head_carriage.visual(
        Cylinder(radius=0.022, length=0.014),
        origin=Origin(xyz=(0.052, 0.0, -0.029)),
        material=dark_metal,
        name="nosepiece",
    )
    head_carriage.visual(
        Cylinder(radius=0.012, length=0.060),
        origin=Origin(xyz=(0.062, 0.0, -0.032)),
        material=brushed,
        name="objective_barrel",
    )
    head_carriage.visual(
        Cylinder(radius=0.020, length=0.105),
        origin=Origin(xyz=(0.020, 0.0, 0.060), rpy=(0.0, 0.55, 0.0)),
        material=body_white,
        name="monocular_tube",
    )
    head_carriage.visual(
        Cylinder(radius=0.014, length=0.045),
        origin=Origin(xyz=(0.060, 0.0, 0.113), rpy=(0.0, 0.55, 0.0)),
        material=black,
        name="eyepiece",
    )

    model.articulation(
        "guide_to_head",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=head_carriage,
        origin=Origin(xyz=(-0.020, 0.0, 0.225)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=0.05, lower=-0.010, upper=0.055),
    )

    focus_knobs = model.part("focus_knobs")
    focus_knobs.visual(
        Cylinder(radius=0.008, length=0.206),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=brushed,
        name="shared_shaft",
    )
    focus_knobs.visual(
        Cylinder(radius=0.028, length=0.028),
        origin=Origin(xyz=(0.0, -0.110, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="knob_0",
    )
    focus_knobs.visual(
        Cylinder(radius=0.028, length=0.028),
        origin=Origin(xyz=(0.0, 0.110, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="knob_1",
    )
    focus_knobs.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.0, -0.127, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="knob_cap_0",
    )
    focus_knobs.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.0, 0.127, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="knob_cap_1",
    )

    model.articulation(
        "arm_to_focus",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=focus_knobs,
        origin=Origin(xyz=(-0.145, 0.0, 0.205)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=5.0, lower=-math.pi, upper=math.pi),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
