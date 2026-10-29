# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bench_vise_with_prismatic_jaw, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bench_vise_with_prismatic_jaw

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

# ===== model =====
import math
import cadquery as cq
def _sliding_jaw_shape() -> cq.Workplane:
    """One-piece front jaw with guide-rod bores and raised grip serrations."""
    carriage = cq.Workplane("XY").box(0.088, 0.180, 0.075)
    upright = cq.Workplane("XY").box(0.034, 0.165, 0.120).translate((-0.035, 0.0, 0.055))
    jaw = carriage.union(upright)

    # Raised horizontal grip bars on the rear-facing jaw surface.
    for z in (0.020, 0.040, 0.060, 0.080, 0.100):
        tooth = cq.Workplane("XY").box(0.007, 0.142, 0.006).translate((-0.055, 0.0, z))
        jaw = jaw.union(tooth)

    # Two clearance bores let the static guide rods pass through the carriage.
    for y in (-0.055, 0.055):
        cutter = cq.Workplane("YZ").center(y, -0.025).circle(0.0145).extrude(0.160, both=True)
        jaw = jaw.cut(cutter)

    return jaw
def _threaded_boss_shape() -> cq.Workplane:
    """Annular lower screw boss with an actual center clearance hole."""
    return cq.Workplane("XY").circle(0.034).circle(0.015).extrude(0.026).translate((0.0, 0.0, -0.013))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="clamp_on_welding_vise")

    red = model.material("red_enamel", rgba=(0.64, 0.07, 0.035, 1.0))
    dark = model.material("dark_cast_iron", rgba=(0.08, 0.09, 0.10, 1.0))
    steel = model.material("brushed_steel", rgba=(0.68, 0.66, 0.60, 1.0))
    black = model.material("blackened_thread", rgba=(0.025, 0.024, 0.022, 1.0))
    wood = model.material("workbench_wood", rgba=(0.55, 0.34, 0.17, 1.0))

    body = model.part("body")

    # Contextual bench edge, visibly gripped by the clamp-on base.
    body.visual(
        Box((0.340, 0.300, 0.050)),
        origin=Origin(xyz=(0.060, 0.0, 0.035)),
        material=wood,
        name="bench_edge",
    )

    # Parallel C-clamp frame: upper shoe on top of the bench, lower arm below it,
    # and a rear spine around the bench edge.
    body.visual(
        Box((0.340, 0.170, 0.025)),
        origin=Origin(xyz=(0.020, 0.0, 0.0725)),
        material=red,
        name="upper_clamp_shoe",
    )
    body.visual(
        Box((0.060, 0.160, 0.040)),
        origin=Origin(xyz=(-0.060, 0.0, 0.105)),
        material=red,
        name="shoe_to_bed_rib",
    )
    body.visual(
        Box((0.430, 0.175, 0.035)),
        origin=Origin(xyz=(0.015, 0.0, 0.1275)),
        material=red,
        name="vise_bed",
    )
    body.visual(
        Box((0.048, 0.180, 0.210)),
        origin=Origin(xyz=(-0.170, 0.0, 0.035)),
        material=red,
        name="rear_spine",
    )
    body.visual(
        Box((0.245, 0.130, 0.030)),
        origin=Origin(xyz=(-0.055, 0.0, -0.055)),
        material=red,
        name="lower_clamp_arm",
    )
    for i, y in enumerate((-0.045, 0.045)):
        body.visual(
            Box((0.070, 0.025, 0.026)),
            origin=Origin(xyz=(0.085, y, -0.055)),
            material=red,
            name=f"boss_yoke_{i}",
        )
    body.visual(
        mesh_from_cadquery(_threaded_boss_shape(), "threaded_boss"),
        origin=Origin(xyz=(0.110, 0.0, -0.055)),
        material=dark,
        name="threaded_boss",
    )

    # Fixed rear jaw and hard serrated insert.
    body.visual(
        Box((0.070, 0.178, 0.125)),
        origin=Origin(xyz=(-0.145, 0.0, 0.2075)),
        material=red,
        name="rear_jaw_block",
    )
    body.visual(
        Box((0.010, 0.152, 0.092)),
        origin=Origin(xyz=(-0.105, 0.0, 0.232)),
        material=steel,
        name="rear_jaw_face",
    )
    for i, z in enumerate((0.198, 0.216, 0.234, 0.252, 0.270)):
        body.visual(
            Box((0.007, 0.135, 0.006)),
            origin=Origin(xyz=(-0.098, 0.0, z)),
            material=black,
            name=f"rear_tooth_{i}",
        )

    # Static parallel guide rods for the sliding front jaw.
    for i, y in enumerate((-0.055, 0.055)):
        body.visual(
            Cylinder(radius=0.0085, length=0.345),
            origin=Origin(xyz=(0.055, y, 0.160), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=steel,
            name=f"guide_rod_{i}",
        )
        body.visual(
            Cylinder(radius=0.012, length=0.010),
            origin=Origin(xyz=(0.232, y, 0.160), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark,
            name=f"rod_cap_{i}",
        )

    front_jaw = model.part("front_jaw")
    front_jaw.visual(
        mesh_from_cadquery(_sliding_jaw_shape(), "front_jaw_body", tolerance=0.0008),
        material=steel,
        name="jaw_body",
    )
    for i, y in enumerate((-0.055, 0.055)):
        front_jaw.visual(
            Box((0.072, 0.006, 0.007)),
            origin=Origin(xyz=(0.0, y, -0.013)),
            material=steel,
            name=f"bearing_pad_{i}",
        )

    clamp_screw = model.part("clamp_screw")
    clamp_screw.visual(
        Cylinder(radius=0.040, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=steel,
        name="pressure_pad",
    )
    clamp_screw.visual(
        Cylinder(radius=0.0105, length=0.090),
        origin=Origin(xyz=(0.0, 0.0, -0.041)),
        material=black,
        name="threaded_stem",
    )
    for i, z in enumerate((-0.074, -0.058, -0.042, -0.026, -0.010)):
        clamp_screw.visual(
            Cylinder(radius=0.0130, length=0.004),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=steel,
            name=f"thread_crest_{i}",
        )
    clamp_screw.visual(
        Cylinder(radius=0.0075, length=0.125),
        origin=Origin(xyz=(0.0, 0.0, -0.086), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="tommy_bar",
    )
    for i, y in enumerate((-0.058, 0.058)):
        clamp_screw.visual(
            Sphere(radius=0.012),
            origin=Origin(xyz=(0.0, y, -0.086)),
            material=steel,
            name=f"bar_end_{i}",
        )

    model.articulation(
        "body_to_front_jaw",
        ArticulationType.PRISMATIC,
        parent=body,
        child=front_jaw,
        origin=Origin(xyz=(0.025, 0.0, 0.185)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=250.0, velocity=0.18, lower=0.0, upper=0.110),
    )
    model.articulation(
        "body_to_clamp_screw",
        ArticulationType.REVOLUTE,
        parent=body,
        child=clamp_screw,
        origin=Origin(xyz=(0.110, 0.0, 0.004)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=80.0, velocity=4.0, lower=-math.pi, upper=math.pi),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
