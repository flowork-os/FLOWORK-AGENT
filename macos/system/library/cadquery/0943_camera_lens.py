# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
def _x_cylinder(radius: float, x_min: float, x_max: float):
    """CadQuery cylinder whose axis is the lens X axis."""

    return (
        cq.Workplane("YZ")
        .circle(radius)
        .extrude(x_max - x_min)
        .translate((x_min, 0.0, 0.0))
    )
def _build_barrel_mesh():
    """One connected, hollow, stepped telephoto barrel shell."""

    segments = [
        (-0.455, -0.365, 0.052),
        (-0.370, -0.315, 0.061),
        (-0.325, -0.160, 0.060),
        (-0.165, -0.105, 0.071),
        (-0.110, 0.125, 0.074),
        (0.120, 0.225, 0.083),
        (0.220, 0.425, 0.103),
        (0.398, 0.466, 0.111),
    ]
    body = _x_cylinder(segments[0][2], segments[0][0], segments[0][1])
    for x_min, x_max, radius in segments[1:]:
        body = body.union(_x_cylinder(radius, x_min, x_max))

    # The long central optical bore and the wider front glass recess keep the
    # lens from reading as a solid rod.
    body = body.cut(_x_cylinder(0.032, -0.470, 0.475))
    body = body.cut(_x_cylinder(0.086, 0.300, 0.480))
    body = body.cut(_x_cylinder(0.040, -0.475, -0.410))
    return body
def _build_grip_ring_mesh(
    *,
    length: float,
    inner_radius: float,
    core_radius: float,
    rib_height: float,
    rib_count: int,
):
    """Rubber control ring with raised axial ribs and hollow clearance."""

    x_min = -length * 0.5
    x_max = length * 0.5
    ring = _x_cylinder(core_radius, x_min, x_max)
    ring = ring.union(_x_cylinder(core_radius + 0.003, x_min, x_min + 0.009))
    ring = ring.union(_x_cylinder(core_radius + 0.003, x_max - 0.009, x_max))

    for index in range(rib_count):
        angle_deg = index * 360.0 / rib_count
        rib = (
            cq.Workplane("XY")
            .box(length * 0.83, 0.0036, rib_height)
            .translate((0.0, 0.0, core_radius + rib_height * 0.5 - 0.0007))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
        )
        ring = ring.union(rib)

    return ring.cut(_x_cylinder(inner_radius, x_min - 0.010, x_max + 0.010))
def _build_tripod_collar_mesh():
    """Rotating tripod collar with an integrated downward foot."""

    length = 0.074
    x_min = -length * 0.5
    x_max = length * 0.5
    collar = _x_cylinder(0.091, x_min, x_max)
    collar = collar.union(_x_cylinder(0.097, x_min, x_min + 0.010))
    collar = collar.union(_x_cylinder(0.097, x_max - 0.010, x_max))

    # Clamp ears at camera-right and an Arca-style foot below the barrel.
    ears = (
        cq.Workplane("XY")
        .box(0.050, 0.030, 0.034)
        .translate((0.0, 0.090, 0.000))
    )
    collar = collar.union(ears)
    neck = (
        cq.Workplane("XY")
        .box(0.046, 0.052, 0.072)
        .translate((0.0, 0.0, -0.125))
    )
    foot_plate = (
        cq.Workplane("XY")
        .box(0.180, 0.064, 0.018)
        .translate((0.0, 0.0, -0.166))
    )
    collar = collar.union(neck).union(foot_plate)

    # Keep the collar a true clearance ring around the barrel.
    return collar.cut(_x_cylinder(0.074, x_min - 0.010, x_max + 0.010))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="telephoto_zoom_lens")

    satin_black = model.material("satin_black", rgba=(0.015, 0.016, 0.018, 1.0))
    rubber = model.material("ribbed_rubber", rgba=(0.035, 0.036, 0.038, 1.0))
    graphite = model.material("graphite_metal", rgba=(0.12, 0.125, 0.13, 1.0))
    glass = model.material("coated_glass", rgba=(0.18, 0.32, 0.40, 0.48))
    deep_glass = model.material("rear_glass", rgba=(0.03, 0.04, 0.05, 0.70))
    white = model.material("engraving_white", rgba=(0.86, 0.88, 0.84, 1.0))
    red = model.material("mount_red", rgba=(0.70, 0.04, 0.03, 1.0))

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_build_barrel_mesh(), "stepped_lens_barrel"),
        material=satin_black,
        name="barrel_shell",
    )
    barrel.visual(
        Cylinder(radius=0.087, length=0.008),
        origin=Origin(xyz=(0.302, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_element",
    )
    barrel.visual(
        Cylinder(radius=0.041, length=0.006),
        origin=Origin(xyz=(-0.444, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=deep_glass,
        name="rear_element",
    )
    barrel.visual(
        Box((0.006, 0.022, 0.0024)),
        origin=Origin(xyz=(-0.145, 0.0, 0.0718)),
        material=white,
        name="zoom_index",
    )
    barrel.visual(
        Box((0.006, 0.026, 0.0024)),
        origin=Origin(xyz=(0.070, 0.0, 0.0748)),
        material=white,
        name="focus_index",
    )
    barrel.visual(
        Sphere(radius=0.0045),
        origin=Origin(xyz=(-0.392, -0.039, 0.039)),
        material=red,
        name="mount_dot",
    )

    zoom_ring = model.part("zoom_ring")
    zoom_ring.visual(
        mesh_from_cadquery(
            _build_grip_ring_mesh(
                length=0.145,
                inner_radius=0.0600,
                core_radius=0.078,
                rib_height=0.006,
                rib_count=36,
            ),
            "zoom_ring_ribbed",
        ),
        material=rubber,
        name="zoom_grip",
    )
    for mark_x, mark_y, mark_z, mark_len in (
        (-0.042, 0.0, 0.084, 0.018),
        (-0.006, 0.0, 0.084, 0.012),
        (0.030, 0.0, 0.084, 0.016),
    ):
        zoom_ring.visual(
            Box((0.003, mark_len, 0.002)),
            origin=Origin(xyz=(mark_x, mark_y, mark_z)),
            material=white,
            name=f"zoom_mark_{mark_x:.3f}".replace("-", "m").replace(".", "_"),
        )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(
            _build_grip_ring_mesh(
                length=0.112,
                inner_radius=0.0830,
                core_radius=0.096,
                rib_height=0.005,
                rib_count=44,
            ),
            "focus_ring_ribbed",
        ),
        material=rubber,
        name="focus_grip",
    )
    for index, mark_x in enumerate((-0.032, 0.000, 0.032)):
        focus_ring.visual(
            Box((0.003, 0.020 - index * 0.004, 0.002)),
            origin=Origin(xyz=(mark_x, 0.0, 0.101)),
            material=white,
            name=f"focus_mark_{index}",
        )

    collar = model.part("tripod_collar")
    collar.visual(
        mesh_from_cadquery(_build_tripod_collar_mesh(), "tripod_collar_foot"),
        material=graphite,
        name="collar_foot",
    )
    collar.visual(
        Cylinder(radius=0.009, length=0.006),
        origin=Origin(xyz=(0.0, 0.107, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=white,
        name="clamp_screw",
    )
    collar.visual(
        Cylinder(radius=0.012, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, -0.1765)),
        material=satin_black,
        name="tripod_socket",
    )

    model.articulation(
        "barrel_to_zoom_ring",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=zoom_ring,
        origin=Origin(xyz=(-0.245, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.7,
            velocity=3.5,
            lower=math.radians(-38.0),
            upper=math.radians(92.0),
        ),
    )
    model.articulation(
        "barrel_to_focus_ring",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.155, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.45,
            velocity=4.0,
            lower=math.radians(-105.0),
            upper=math.radians(105.0),
        ),
    )
    model.articulation(
        "barrel_to_tripod_collar",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=collar,
        origin=Origin(xyz=(-0.010, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=2.5),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
