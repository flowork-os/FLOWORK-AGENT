# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
SHOULDER_Z = 0.92
FIRST_LINK_LENGTH = 1.02
SECOND_LINK_LENGTH = 0.78
WRIST_STANDOFF = 0.05
def _cyl_z(radius: float, length: float, center: tuple[float, float, float]):
    """CadQuery cylinder with its axis along +Z and centered at center."""
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((center[0], center[1], center[2] - length * 0.5))
    )
def _cyl_y(radius: float, length: float, center: tuple[float, float, float]):
    return _cyl_z(radius, length, (0.0, 0.0, 0.0)).rotate(
        (0, 0, 0), (1, 0, 0), -90
    ).translate(center)
def _cyl_x(radius: float, length: float, center: tuple[float, float, float]):
    return _cyl_z(radius, length, (0.0, 0.0, 0.0)).rotate(
        (0, 0, 0), (0, 1, 0), 90
    ).translate(center)
def _box(size: tuple[float, float, float], center: tuple[float, float, float]):
    return cq.Workplane("XY").box(*size).translate(center)
def _union(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.union(shape)
    return result
def _base_casting():
    """One connected casting for the fixed pedestal and shoulder fork."""
    shapes = [
        _cyl_z(0.34, 0.10, (0.0, 0.0, 0.05)),
        _cyl_z(0.25, 0.055, (0.0, 0.0, 0.125)),
        _cyl_z(0.16, 0.44, (0.0, 0.0, 0.36)),
        _box((0.40, 0.52, 0.14), (0.0, 0.0, 0.61)),
        _box((0.32, 0.075, 0.66), (0.0, 0.242, 0.91)),
        _box((0.32, 0.075, 0.66), (0.0, -0.242, 0.91)),
        # rear bridge and lower saddle make the fork unambiguously fixed
        _box((0.11, 0.43, 0.61), (-0.265, 0.0, 0.905)),
        _box((0.11, 0.43, 0.11), (-0.175, 0.0, 0.645)),
        _box((0.28, 0.45, 0.10), (0.0, 0.0, 0.64)),
        # raised bearing bosses and machined outer flanges on the cheeks
        _cyl_y(0.205, 0.036, (0.0, 0.292, SHOULDER_Z)),
        _cyl_y(0.205, 0.036, (0.0, -0.292, SHOULDER_Z)),
        _cyl_y(0.145, 0.050, (0.0, 0.315, SHOULDER_Z)),
        _cyl_y(0.145, 0.050, (0.0, -0.315, SHOULDER_Z)),
        # hard stops well outside the swept first-link envelope
        _box((0.050, 0.38, 0.13), (-0.240, 0.0, 1.145)),
        _box((0.050, 0.38, 0.13), (-0.240, 0.0, 0.685)),
    ]
    return _union(shapes)
def _first_link_casting():
    """Deep first moving link with shoulder trunnion and distal clevis."""
    shapes = [
        _cyl_y(0.162, 0.315, (0.0, 0.0, 0.0)),
        _box((0.72, 0.165, 0.285), (0.43, 0.0, 0.0)),
        _box((0.22, 0.19, 0.24), (0.14, 0.0, 0.0)),
        # distal clevis: two outboard cheeks plus a rear bridge, leaving a clear gap
        _box((0.285, 0.062, 0.275), (0.97, 0.142, 0.0)),
        _box((0.285, 0.062, 0.275), (0.97, -0.142, 0.0)),
        _box((0.105, 0.335, 0.205), (0.815, 0.0, 0.0)),
        _cyl_y(0.135, 0.065, (1.02, 0.178, 0.0)),
        _cyl_y(0.135, 0.065, (1.02, -0.178, 0.0)),
        # shallow raised inspection pads on both side faces
        _box((0.34, 0.014, 0.155), (0.48, 0.086, 0.0)),
        _box((0.34, 0.014, 0.155), (0.48, -0.086, 0.0)),
        # top rib and underside rib to make the section read as a deep casting
        _box((0.54, 0.075, 0.045), (0.48, 0.0, 0.162)),
        _box((0.48, 0.065, 0.035), (0.50, 0.0, -0.160)),
    ]
    return _union(shapes)
def _second_link_casting():
    """Slimmer second moving link nested between the first link's elbow cheeks."""
    shapes = [
        _cyl_y(0.112, 0.180, (0.0, 0.0, 0.0)),
        _box((0.545, 0.120, 0.175), (0.34, 0.0, 0.0)),
        _box((0.18, 0.145, 0.155), (0.12, 0.0, 0.0)),
        _box((0.135, 0.135, 0.205), (0.675, 0.0, 0.0)),
        _cyl_x(0.132, 0.100, (0.780, 0.0, 0.0)),
        _cyl_x(0.102, 0.070, (0.795, 0.0, 0.0)),
        # small flush inspection covers
        _box((0.255, 0.012, 0.103), (0.39, 0.063, 0.0)),
        _box((0.255, 0.012, 0.103), (0.39, -0.063, 0.0)),
        _box((0.38, 0.052, 0.030), (0.39, 0.0, 0.102)),
    ]
    return _union(shapes)
def _wrist_nose_casting():
    """Compact cylindrical wrist with a flange and an off-axis timing lug."""
    shapes = [
        _cyl_x(0.092, 0.245, (0.145, 0.0, 0.0)),
        _cyl_x(0.125, 0.042, (0.021, 0.0, 0.0)),
        _cyl_x(0.118, 0.045, (0.275, 0.0, 0.0)),
        _cyl_x(0.072, 0.042, (0.310, 0.0, 0.0)),
        _box((0.070, 0.036, 0.032), (0.165, 0.0, 0.096)),
        _box((0.060, 0.030, 0.026), (0.285, 0.0, 0.098)),
    ]
    # four proud bolt heads on the tool flange, embedded into the face
    for angle in (math.pi / 4.0, 3.0 * math.pi / 4.0, 5.0 * math.pi / 4.0, 7.0 * math.pi / 4.0):
        shapes.append(
            _cyl_x(
                0.013,
                0.014,
                (0.304, 0.070 * math.cos(angle), 0.070 * math.sin(angle)),
            )
        )
    return _union(shapes)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="machine_tending_arm")

    cast_steel = model.material("cast_steel", rgba=(0.30, 0.34, 0.37, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.10, 0.11, 0.12, 1.0))
    bare_steel = model.material("bare_steel", rgba=(0.63, 0.65, 0.66, 1.0))
    orange = model.material("safety_orange", rgba=(0.95, 0.36, 0.08, 1.0))
    link_gray = model.material("warm_link_gray", rgba=(0.70, 0.72, 0.70, 1.0))
    cover_black = model.material("cover_black", rgba=(0.04, 0.045, 0.05, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_casting(), "pedestal_fork_casting"),
        origin=Origin(),
        material=cast_steel,
        name="pedestal_fork_casting",
    )
    base.visual(
        Cylinder(radius=0.36, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.158)),
        material=bare_steel,
        name="pedestal_flange_ring",
    )
    # Four embedded anchor pads distinguish the fixed support from moving links.
    for index, (x, y) in enumerate(((0.23, 0.23), (-0.23, 0.23), (-0.23, -0.23), (0.23, -0.23))):
        base.visual(
            Cylinder(radius=0.027, length=0.014),
            origin=Origin(xyz=(x, y, 0.105)),
            material=dark_steel,
            name=f"anchor_bolt_{index}",
        )
    base.inertial = Inertial.from_geometry(
        Cylinder(radius=0.34, length=1.18),
        mass=185.0,
        origin=Origin(xyz=(0.0, 0.0, 0.60)),
    )

    first_link = model.part("first_link")
    first_link.visual(
        mesh_from_cadquery(_first_link_casting(), "deep_link_casting"),
        origin=Origin(),
        material=orange,
        name="deep_link_casting",
    )
    first_link.visual(
        Cylinder(radius=0.108, length=0.410),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=bare_steel,
        name="shoulder_trunnion_sleeve",
    )
    first_link.inertial = Inertial.from_geometry(
        Box((1.12, 0.34, 0.32)),
        mass=62.0,
        origin=Origin(xyz=(0.54, 0.0, 0.0)),
    )

    second_link = model.part("second_link")
    second_link.visual(
        mesh_from_cadquery(_second_link_casting(), "slim_link_casting"),
        origin=Origin(),
        material=link_gray,
        name="slim_link_casting",
    )
    second_link.visual(
        Cylinder(radius=0.080, length=0.222),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=bare_steel,
        name="elbow_trunnion_sleeve",
    )
    second_link.visual(
        Box((0.220, 0.010, 0.082)),
        origin=Origin(xyz=(0.39, 0.064, 0.0)),
        material=cover_black,
        name="side_cover_0",
    )
    second_link.visual(
        Box((0.220, 0.010, 0.082)),
        origin=Origin(xyz=(0.39, -0.064, 0.0)),
        material=cover_black,
        name="side_cover_1",
    )
    second_link.inertial = Inertial.from_geometry(
        Box((0.86, 0.18, 0.23)),
        mass=30.0,
        origin=Origin(xyz=(0.38, 0.0, 0.0)),
    )

    wrist_nose = model.part("wrist_nose")
    wrist_nose.visual(
        mesh_from_cadquery(_wrist_nose_casting(), "wrist_nose_casting"),
        origin=Origin(),
        material=dark_steel,
        name="wrist_nose_casting",
    )
    wrist_nose.visual(
        Cylinder(radius=0.062, length=0.052),
        origin=Origin(xyz=(0.327, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=bare_steel,
        name="tool_register",
    )
    wrist_nose.inertial = Inertial.from_geometry(
        Cylinder(radius=0.13, length=0.35),
        mass=12.0,
        origin=Origin(xyz=(0.16, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    model.articulation(
        "shoulder_pitch",
        ArticulationType.REVOLUTE,
        parent=base,
        child=first_link,
        origin=Origin(xyz=(0.0, 0.0, SHOULDER_Z)),
        # The link geometry extends along local +X; -Y makes positive q lift it.
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=1250.0, velocity=1.1, lower=-0.15, upper=1.10),
    )
    model.articulation(
        "elbow_pitch",
        ArticulationType.REVOLUTE,
        parent=first_link,
        child=second_link,
        origin=Origin(xyz=(FIRST_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=780.0, velocity=1.35, lower=-0.15, upper=1.45),
    )
    model.articulation(
        "wrist_roll",
        ArticulationType.REVOLUTE,
        parent=second_link,
        child=wrist_nose,
        origin=Origin(xyz=(SECOND_LINK_LENGTH + WRIST_STANDOFF, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=240.0,
            velocity=4.0,
            lower=-math.pi,
            upper=math.pi,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
