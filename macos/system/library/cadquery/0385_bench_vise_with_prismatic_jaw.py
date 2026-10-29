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
def _box_at(size: tuple[float, float, float], center: tuple[float, float, float]):
    return cq.Workplane("XY").box(*size).translate(center)
def _x_hole(y: float, z: float, radius: float, length: float = 0.60):
    return cq.Workplane("YZ").center(y, z).circle(radius).extrude(length, both=True)
def _moving_jaw_casting():
    """Single sliding casting with clear through-holes for the two bars and screw."""
    carriage = _box_at((0.165, 0.172, 0.078), (0.020, 0.0, 0.002))
    jaw_upright = _box_at((0.080, 0.188, 0.158), (-0.018, 0.0, 0.058))
    top_cap = _box_at((0.100, 0.176, 0.026), (-0.020, 0.0, 0.146))
    screw_nose = _box_at((0.060, 0.096, 0.032), (0.090, 0.0, -0.026))
    throat_rib = _box_at((0.115, 0.045, 0.052), (0.055, 0.0, 0.075))

    shape = carriage.union(jaw_upright).union(top_cap).union(screw_nose).union(throat_rib)
    for y in (-0.055, 0.055):
        shape = shape.cut(_x_hole(y, 0.0, 0.0175))
    shape = shape.cut(_x_hole(0.0, -0.030, 0.0120))
    return shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="quick_release_bench_vise")

    cast_iron = model.material("blue_cast_iron", rgba=(0.05, 0.12, 0.22, 1.0))
    dark_cast = model.material("dark_cast_iron", rgba=(0.025, 0.030, 0.035, 1.0))
    polished_steel = model.material("polished_steel", rgba=(0.72, 0.74, 0.72, 1.0))
    jaw_steel = model.material("flat_ground_jaw_steel", rgba=(0.84, 0.84, 0.78, 1.0))
    black_oxide = model.material("black_oxide", rgba=(0.01, 0.01, 0.012, 1.0))
    brass = model.material("oiled_bronze_half_nut", rgba=(0.72, 0.48, 0.18, 1.0))
    release_red = model.material("red_release_lever", rgba=(0.72, 0.055, 0.035, 1.0))

    body = model.part("body")
    body.visual(
        Box((0.54, 0.225, 0.035)),
        origin=Origin(xyz=(0.080, 0.0, 0.0175)),
        material=cast_iron,
        name="base_plate",
    )
    for xi, x in enumerate((-0.135, 0.295)):
        for yi, y in enumerate((-0.078, 0.078)):
            body.visual(
                Cylinder(radius=0.018, length=0.006),
                origin=Origin(xyz=(x, y, 0.038)),
                material=black_oxide,
                name=f"mount_bolt_{xi}_{yi}",
            )

    body.visual(
        Box((0.105, 0.190, 0.120)),
        origin=Origin(xyz=(-0.085, 0.0, 0.145)),
        material=cast_iron,
        name="fixed_jaw_upright",
    )
    for i, y in enumerate((-0.073, 0.073)):
        body.visual(
            Box((0.105, 0.040, 0.052)),
            origin=Origin(xyz=(-0.085, y, 0.061)),
            material=cast_iron,
            name=f"fixed_lower_cheek_{i}",
        )
    body.visual(
        Box((0.118, 0.150, 0.025)),
        origin=Origin(xyz=(-0.115, 0.0, 0.217)),
        material=dark_cast,
        name="small_anvil",
    )
    body.visual(
        Box((0.012, 0.165, 0.058)),
        origin=Origin(xyz=(-0.027, 0.0, 0.172)),
        material=jaw_steel,
        name="fixed_jaw_plate",
    )

    for i, y in enumerate((-0.075, 0.075)):
        body.visual(
            Box((0.165, 0.035, 0.072)),
            origin=Origin(xyz=(0.015, y, 0.066)),
            material=cast_iron,
            name=f"guide_side_web_{i}",
        )
    body.visual(
        Box((0.175, 0.160, 0.018)),
        origin=Origin(xyz=(0.035, 0.0, 0.108)),
        material=cast_iron,
        name="upper_guide_bridge",
    )
    for i, y in enumerate((-0.055, 0.055)):
        body.visual(
            Cylinder(radius=0.012, length=0.505),
            origin=Origin(xyz=(0.185, y, 0.080), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=polished_steel,
            name=f"guide_bar_{i}",
        )

    body.visual(
        Box((0.083, 0.080, 0.010)),
        origin=Origin(xyz=(0.034, 0.0, 0.0645)),
        material=brass,
        name="upper_half_nut",
    )
    body.visual(
        Box((0.083, 0.080, 0.010)),
        origin=Origin(xyz=(0.034, 0.0, 0.0355)),
        material=brass,
        name="lower_half_nut",
    )
    for i, y in enumerate((-0.040, 0.040)):
        body.visual(
            Box((0.083, 0.012, 0.050)),
            origin=Origin(xyz=(0.034, y, 0.050)),
            material=brass,
            name=f"half_nut_side_tie_{i}",
        )

    body.visual(
        Cylinder(radius=0.024, length=0.030),
        origin=Origin(xyz=(-0.025, -0.108, 0.105), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_cast,
        name="release_pivot_boss",
    )

    moving_jaw = model.part("moving_jaw")
    moving_jaw.visual(
        mesh_from_cadquery(_moving_jaw_casting(), "moving_jaw_casting", tolerance=0.0007),
        material=cast_iron,
        name="sliding_casting",
    )
    moving_jaw.visual(
        Box((0.012, 0.165, 0.058)),
        origin=Origin(xyz=(-0.059, 0.0, 0.105)),
        material=jaw_steel,
        name="jaw_plate",
    )
    moving_jaw.visual(
        Box((0.060, 0.065, 0.008)),
        origin=Origin(xyz=(0.092, 0.0, -0.010)),
        material=black_oxide,
        name="screw_bearing_upper",
    )
    moving_jaw.visual(
        Box((0.110, 0.052, 0.006)),
        origin=Origin(xyz=(0.055, 0.0, -0.042)),
        material=dark_cast,
        name="bed_slide_shoe",
    )
    screw_handle = model.part("lead_screw_handle")
    screw_handle.visual(
        Cylinder(radius=0.0075, length=0.580),
        origin=Origin(xyz=(-0.220, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished_steel,
        name="threaded_shaft",
    )
    for i in range(18):
        x = -0.425 + i * 0.025
        screw_handle.visual(
            Cylinder(radius=0.0092, length=0.0032),
            origin=Origin(xyz=(x, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=black_oxide,
            name=f"thread_crest_{i}",
        )
    screw_handle.visual(
        Cylinder(radius=0.006, length=0.145),
        origin=Origin(xyz=(0.067, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished_steel,
        name="tommy_bar",
    )
    for i, y in enumerate((-0.078, 0.078)):
        screw_handle.visual(
            Sphere(radius=0.015),
            origin=Origin(xyz=(0.067, y, 0.0)),
            material=black_oxide,
            name=f"handle_ball_{i}",
        )

    release_lever = model.part("release_lever")
    release_lever.visual(
        Cylinder(radius=0.017, length=0.008),
        origin=Origin(xyz=(0.0, -0.004, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black_oxide,
        name="pivot_washer",
    )
    release_lever.visual(
        Box((0.052, 0.008, 0.026)),
        origin=Origin(xyz=(0.018, -0.006, -0.012), rpy=(0.0, 0.18, 0.0)),
        material=release_red,
        name="lever_root",
    )
    release_lever.visual(
        Box((0.024, 0.008, 0.104)),
        origin=Origin(xyz=(0.025, -0.006, -0.046), rpy=(0.0, 0.35, 0.0)),
        material=release_red,
        name="lever_blade",
    )
    release_lever.visual(
        Box((0.040, 0.010, 0.026)),
        origin=Origin(xyz=(0.046, -0.006, -0.083), rpy=(0.0, 0.18, 0.0)),
        material=release_red,
        name="lever_end_pad",
    )
    release_lever.visual(
        Sphere(radius=0.020),
        origin=Origin(xyz=(0.050, -0.006, -0.094)),
        material=release_red,
        name="finger_knob",
    )

    model.articulation(
        "body_to_moving_jaw",
        ArticulationType.PRISMATIC,
        parent=body,
        child=moving_jaw,
        origin=Origin(xyz=(0.190, 0.0, 0.080)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=850.0, velocity=0.22, lower=0.0, upper=0.120),
    )
    model.articulation(
        "jaw_to_lead_screw_handle",
        ArticulationType.CONTINUOUS,
        parent=moving_jaw,
        child=screw_handle,
        origin=Origin(xyz=(0.090, 0.0, -0.030)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=22.0, velocity=9.0),
    )
    model.articulation(
        "body_to_release_lever",
        ArticulationType.REVOLUTE,
        parent=body,
        child=release_lever,
        origin=Origin(xyz=(-0.025, -0.123, 0.105)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=3.0, lower=-0.35, upper=0.75),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
