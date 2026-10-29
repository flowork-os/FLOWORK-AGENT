# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bell_tower_with_swinging_bell, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bell_tower_with_swinging_bell

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
def _bell_body_shape() -> cq.Workplane:
    """Lathe a hollow, flared alpine church bell in local metres."""
    wall_profile = [
        (0.225, -0.620),
        (0.214, -0.585),
        (0.165, -0.470),
        (0.112, -0.300),
        (0.081, -0.195),
        (0.045, -0.160),
        (0.000, -0.148),
        (0.000, -0.185),
        (0.050, -0.190),
        (0.075, -0.275),
        (0.128, -0.465),
        (0.183, -0.582),
        (0.194, -0.620),
    ]
    body = (
        cq.Workplane("XZ")
        .polyline(wall_profile)
        .close()
        .revolve(360.0, axisStart=(0.0, 0.0), axisEnd=(0.0, 1.0))
    )

    # Subtle raised bands are part of the cast bronze/brass body, not separate
    # floating decorations.
    shoulder_band = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.096, -0.248),
                (0.116, -0.248),
                (0.118, -0.268),
                (0.099, -0.270),
            ]
        )
        .close()
        .revolve(360.0, axisStart=(0.0, 0.0), axisEnd=(0.0, 1.0))
    )
    sound_bow_band = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.174, -0.505),
                (0.199, -0.505),
                (0.203, -0.535),
                (0.181, -0.538),
            ]
        )
        .close()
        .revolve(360.0, axisStart=(0.0, 0.0), axisEnd=(0.0, 1.0))
    )
    return body.union(shoulder_band).union(sound_bow_band)
def _bearing_plate_shape() -> cq.Workplane:
    """A fixed iron cheek plate with a real clearance hole for the trunnion."""
    return (
        cq.Workplane("XY")
        .box(0.040, 0.120, 0.110)
        .faces(">X")
        .workplane(centerOption="CenterOfMass")
        .circle(0.023)
        .cutThruAll()
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="alpine_wooden_bell_cote")

    wood = model.material("weathered_warm_timber", rgba=(0.50, 0.30, 0.15, 1.0))
    end_grain = model.material("darker_end_grain", rgba=(0.30, 0.17, 0.08, 1.0))
    roof_mat = model.material("dark_alpine_shingles", rgba=(0.16, 0.12, 0.09, 1.0))
    brass = model.material("aged_brass", rgba=(0.88, 0.62, 0.22, 1.0))
    iron = model.material("blackened_iron", rgba=(0.03, 0.03, 0.028, 1.0))

    frame = model.part("timber_frame")

    # Narrow rectangular open timber frame.
    for x, name in [(-0.350, "upright_0"), (0.350, "upright_1")]:
        frame.visual(
            Box((0.095, 0.200, 1.180)),
            origin=Origin(xyz=(x, 0.0, 0.690)),
            material=wood,
            name=name,
        )

    frame.visual(
        Box((0.800, 0.210, 0.115)),
        origin=Origin(xyz=(0.0, 0.0, 0.095)),
        material=end_grain,
        name="bottom_sill",
    )
    frame.visual(
        Box((0.800, 0.205, 0.095)),
        origin=Origin(xyz=(0.0, 0.0, 1.265)),
        material=wood,
        name="top_tie",
    )

    # Fixed pivot beam across the uprights; bearing cheeks are bolted to it.
    frame.visual(
        Box((0.700, 0.085, 0.085)),
        origin=Origin(xyz=(0.0, 0.100, 1.000)),
        material=wood,
        name="pivot_beam",
    )
    bearing_mesh = mesh_from_cadquery(
        _bearing_plate_shape(),
        "iron_bearing_plate",
        tolerance=0.0008,
        angular_tolerance=0.08,
    )
    for x, name in [(-0.245, "bearing_plate_0"), (0.245, "bearing_plate_1")]:
        frame.visual(
            bearing_mesh,
            origin=Origin(xyz=(x, 0.005, 1.000)),
            material=iron,
            name=name,
        )

    # Small diagonal knee braces behind the bell reinforce the Alpine timber
    # silhouette while staying clear of the swinging brass body.
    for x, yaw, name in [
        (-0.242, -0.61, "brace_0"),
        (0.242, 0.61, "brace_1"),
    ]:
        frame.visual(
            Box((0.360, 0.060, 0.060)),
            origin=Origin(xyz=(x, 0.085, 1.135), rpy=(0.0, yaw, 0.0)),
            material=wood,
            name=name,
        )

    # Pointed roof with overhanging shingled boards and a round ridge cap.
    roof_angle = math.atan2(0.240, 0.430)
    frame.visual(
        Box((0.540, 0.500, 0.060)),
        origin=Origin(xyz=(-0.215, 0.0, 1.430), rpy=(0.0, -roof_angle, 0.0)),
        material=roof_mat,
        name="roof_plane_0",
    )
    frame.visual(
        Box((0.540, 0.500, 0.060)),
        origin=Origin(xyz=(0.215, 0.0, 1.430), rpy=(0.0, roof_angle, 0.0)),
        material=roof_mat,
        name="roof_plane_1",
    )
    frame.visual(
        Cylinder(radius=0.035, length=0.540),
        origin=Origin(xyz=(0.0, 0.0, 1.555), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=roof_mat,
        name="ridge_cap",
    )

    bell = model.part("bell")
    bell.visual(
        mesh_from_cadquery(
            _bell_body_shape(),
            "hollow_brass_bell",
            tolerance=0.0008,
            angular_tolerance=0.06,
        ),
        origin=Origin(),
        material=brass,
        name="bell_body",
    )
    bell.visual(
        Box((0.405, 0.080, 0.070)),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=wood,
        name="headstock",
    )
    bell.visual(
        Cylinder(radius=0.016, length=0.490),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=iron,
        name="trunnion_pin",
    )
    for x, name in [(-0.070, "hanger_0"), (0.070, "hanger_1")]:
        bell.visual(
            Box((0.026, 0.024, 0.125)),
            origin=Origin(xyz=(x, 0.0, -0.120)),
            material=iron,
            name=name,
        )
    bell.visual(
        Cylinder(radius=0.007, length=0.345),
        origin=Origin(xyz=(0.0, 0.0, -0.365)),
        material=iron,
        name="clapper_stem",
    )
    bell.visual(
        Sphere(radius=0.035),
        origin=Origin(xyz=(0.0, 0.0, -0.555)),
        material=iron,
        name="clapper_ball",
    )

    model.articulation(
        "headstock_hinge",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=bell,
        origin=Origin(xyz=(0.0, -0.050, 1.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=2.5, lower=-0.62, upper=0.62),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
