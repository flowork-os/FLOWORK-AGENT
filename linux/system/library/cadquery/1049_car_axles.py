# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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

def mesh_from_geometry(geometry, name=None, **kwargs):
    return _CQMesh(_to_shape(geometry), name=name if isinstance(name, str) else None)

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

def _solid_from_triangles(vertices, faces):
    """Fallback: wrap a raw triangle soup as a B-rep solid (for MeshGeometry
    instances that are authored vertex/face directly)."""
    tri_faces = []
    for (a, b, c) in faces:
        va, vb, vc = vertices[a], vertices[b], vertices[c]
        if va == vb or vb == vc or vc == va:
            continue
        w = cq.Wire.makePolygon([cq.Vector(*va), cq.Vector(*vb), cq.Vector(*vc)], close=True)
        try:
            tri_faces.append(cq.Face.makeFromWires(w))
        except Exception:
            continue
    if not tri_faces:
        raise ValidationError("MeshGeometry: no valid triangles to build a solid")
    shell = cq.Shell.makeShell(tri_faces)
    try:
        return cq.Solid.makeSolid(shell)
    except Exception:
        return cq.Compound.makeCompound(tri_faces)

class MeshGeometry:
    """Base for all geometry families. Subclasses build parametric CadQuery
    B-rep and call ``self._set(shape)``. Supports the mesh-style manipulation
    API (translate/rotate/scale/merge/copy) used by Articraft model scripts,
    applied to the underlying CadQuery shape."""

    def __init__(self, vertices=None, faces=None):
        self.vertices = list(vertices or [])
        self.faces = list(faces or [])
        self._shape = None

    # subclasses call this with their cadquery shape
    def _set(self, shape):
        self._shape = _to_shape(shape) if not isinstance(shape, cq.Shape) else shape
        return self

    def _cq(self):
        if self._shape is not None:
            return self._shape
        return _solid_from_triangles(self.vertices, self.faces)

    # ---- mesh-style authoring (raw triangle fallback path) ----
    def add_vertex(self, x, y, z):
        self.vertices.append((float(x), float(y), float(z)))
        return len(self.vertices) - 1

    def add_face(self, a, b, c):
        self.faces.append((int(a), int(b), int(c)))

    def copy(self):
        g = MeshGeometry(self.vertices, self.faces)
        g._shape = self._shape
        return g

    clone = copy

    # ---- rigid / affine transforms (operate on the cadquery shape) ----
    def translate(self, dx, dy=None, dz=None):
        if dy is None:
            dx, dy, dz = dx
        self._shape = self._cq().translate(cq.Vector(float(dx), float(dy), float(dz)))
        return self

    def rotate(self, axis, angle, *, origin=(0.0, 0.0, 0.0)):
        # Articraft angles are RADIANS; cadquery rotate takes degrees about a line.
        o = cq.Vector(float(origin[0]), float(origin[1]), float(origin[2]))
        a = cq.Vector(float(axis[0]), float(axis[1]), float(axis[2]))
        self._shape = self._cq().rotate(o, o + a, math.degrees(float(angle)))
        return self

    def scale(self, sx, sy=None, sz=None):
        if sy is None:
            sy = sz = sx
        if sz is None:
            sz = sx
        m = cq.Matrix([[float(sx), 0, 0, 0], [0, float(sy), 0, 0], [0, 0, float(sz), 0]])
        self._shape = self._cq().transformGeometry(m)
        return self

    def rotate_x(self, angle):
        return self.rotate((1.0, 0.0, 0.0), angle)

    def rotate_y(self, angle):
        return self.rotate((0.0, 1.0, 0.0), angle)

    def rotate_z(self, angle):
        return self.rotate((0.0, 0.0, 1.0), angle)

    def merge(self, other):
        o = _to_shape(other)
        if self._shape is None and not self.faces:
            self._shape = o          # empty accumulator: adopt other's shape
        else:
            self._shape = self._cq().fuse(o)
        return self

    union = merge

    def cut(self, other):
        self._shape = self._cq().cut(_to_shape(other))
        return self

    def difference(self, other):
        return self.cut(other)

    def intersect(self, other):
        self._shape = self._cq().intersect(_to_shape(other))
        return self

def superellipse_profile(width, height, exponent=2.6, *, segments=48):
    width = float(width); height = float(height); exponent = float(exponent)
    segments = max(12, int(segments))
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    if exponent <= 0:
        raise ValidationError("exponent must be positive")
    a = width * 0.5; b = height * 0.5; power = 2.0 / exponent
    pts = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        ct = math.cos(t); st = math.sin(t)
        x = a * (abs(ct) ** power); y = b * (abs(st) ** power)
        if ct < 0:
            x = -x
        if st < 0:
            y = -y
        pts.append((x, y))
    return pts

# ===== sweeps (2 syms) =====
def _loft_section_solid(rings, *, ruled=True):
    """Ruled-loft a list of section rings (each a closed loop of 3D points)
    into a single capped cq.Solid. Ruled stitching reproduces the sdk's
    straight quad strips between adjacent rings exactly."""
    if len(rings) < 2:
        raise ValueError("loft requires at least two section rings")
    wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in ring], close=True) for ring in rings]
    return cq.Solid.makeLoft(wires, ruled=bool(ruled))

def superellipse_side_loft(sections, *, exponents=2.8, segments: int = 56, cap: bool = True,
                           closed: bool = True, min_height: float = 1e-4, min_width: float = 1e-4):
    """Build an organic casing from side-profile rails ``(y, z_min, z_max, width)``.

    The loft axis is +Y and each cross-section is a superellipse in XZ. Profile
    construction is verbatim from the sdk; the rings are stitched into a ruled
    B-rep loft (matching LoftGeometry's quad strips) and rotated into the +Y
    world frame."""
    if len(sections) < 2:
        raise ValueError("superellipse_side_loft requires at least two sections")

    if isinstance(exponents, (int, float)):
        expo_list = [float(exponents)] * len(sections)
    else:
        expo_list = [float(v) for v in exponents]
        if len(expo_list) != len(sections):
            raise ValueError("exponents must match section count")

    profiles = []
    segs = max(12, int(segments))
    min_h = max(1e-9, float(min_height))
    min_w = max(1e-9, float(min_width))

    for i, sec in enumerate(sections):
        y, z_min, z_max, width = sec
        y = float(y)
        z0 = float(z_min)
        z1 = float(z_max)
        if z1 < z0:
            z0, z1 = z1, z0

        height = max(min_h, z1 - z0)
        width = max(min_w, float(width))
        z_center = 0.5 * (z0 + z1)
        exponent = max(0.2, float(expo_list[i]))

        prof_xy = superellipse_profile(width, height, exponent=exponent, segments=segs)
        # Map final (x, y_section, z) into the loft frame: (x, -(z_local + z_center), y).
        prof_xyz = [(x, -(z_local + z_center), y) for (x, z_local) in prof_xy]
        profiles.append(prof_xyz)

    solid = _loft_section_solid(profiles, ruled=True)
    # rotate_x(-pi/2) to bring the loft axis to world +Y (matches sdk geom.rotate_x).
    geom = MeshGeometry()._set(solid)
    geom.rotate((1.0, 0.0, 0.0), -pi / 2.0)
    return geom

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
import math
from pathlib import Path
ASSETS = AssetContext.from_script(__file__)
def _material(name: str, rgba: tuple[float, float, float, float]) -> Material:
    try:
        return Material(name=name, rgba=rgba)
    except TypeError:
        try:
            return Material(name=name, color=rgba)
        except TypeError:
            return Material(name, rgba)
def _origin_x(xyz: tuple[float, float, float]) -> Origin:
    return Origin(xyz=xyz, rpy=(0.0, math.pi / 2.0, 0.0))
def _origin_y(xyz: tuple[float, float, float]) -> Origin:
    return Origin(xyz=xyz, rpy=(math.pi / 2.0, 0.0, 0.0))
def _add_cover_bolts(part, hardware_material: Material) -> None:
    bolt_circle_radius = 0.104
    for idx in range(12):
        angle = (2.0 * math.pi * idx) / 12.0
        y = bolt_circle_radius * math.cos(angle)
        z = bolt_circle_radius * math.sin(angle)
        part.visual(
            Cylinder(radius=0.008, length=0.014),
            origin=_origin_x((-0.168, y, z)),
            material=hardware_material,
        )
def _build_hub(
    part, sign: float, steel: Material, hardware: Material, black_oxide: Material
) -> None:
    part.visual(
        Cylinder(radius=0.042, length=0.058),
        origin=_origin_y((0.0, sign * 0.029, 0.0)),
        material=steel,
    )
    part.visual(
        Cylinder(radius=0.055, length=0.018),
        origin=_origin_y((0.0, sign * 0.022, 0.0)),
        material=black_oxide,
    )
    part.visual(
        Cylinder(radius=0.152, length=0.012),
        origin=_origin_y((0.0, sign * 0.050, 0.0)),
        material=steel,
    )
    part.visual(
        Cylinder(radius=0.073, length=0.034),
        origin=_origin_y((0.0, sign * 0.050, 0.0)),
        material=steel,
    )
    part.visual(
        Cylinder(radius=0.095, length=0.024),
        origin=_origin_y((0.0, sign * 0.070, 0.0)),
        material=steel,
    )
    part.visual(
        Cylinder(radius=0.030, length=0.040),
        origin=_origin_y((0.0, sign * 0.100, 0.0)),
        material=black_oxide,
    )
    part.visual(
        Sphere(radius=0.024),
        origin=Origin(xyz=(0.0, sign * 0.114, 0.0)),
        material=black_oxide,
    )

    stud_radius = 0.062
    for idx in range(6):
        angle = (2.0 * math.pi * idx) / 6.0
        x = stud_radius * math.cos(angle)
        z = stud_radius * math.sin(angle)
        part.visual(
            Cylinder(radius=0.007, length=0.030),
            origin=_origin_y((x, sign * 0.095, z)),
            material=hardware,
        )

    part.inertial = Inertial.from_geometry(
        Box((0.32, 0.14, 0.32)),
        mass=14.5,
        origin=Origin(xyz=(0.0, sign * 0.072, 0.0)),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="car_axle_assembly", assets=ASSETS)

    cast_iron = _material("cast_iron", (0.20, 0.20, 0.22, 1.0))
    machined_steel = _material("machined_steel", (0.58, 0.60, 0.62, 1.0))
    zinc_hardware = _material("zinc_hardware", (0.73, 0.75, 0.78, 1.0))
    rubber_isolator = _material("rubber_isolator", (0.09, 0.09, 0.10, 1.0))
    black_oxide = _material("black_oxide", (0.14, 0.14, 0.15, 1.0))
    model.materials.extend([cast_iron, machined_steel, zinc_hardware, rubber_isolator, black_oxide])

    housing = model.part("axle_housing")
    pumpkin_sections = [
        (-0.220, -0.098, 0.086, 0.160),
        (-0.145, -0.136, 0.112, 0.248),
        (-0.060, -0.170, 0.144, 0.332),
        (0.060, -0.162, 0.152, 0.304),
        (0.155, -0.124, 0.112, 0.224),
        (0.220, -0.094, 0.086, 0.160),
    ]
    pumpkin_mesh = mesh_from_geometry(
        superellipse_side_loft(
            pumpkin_sections,
            exponents=2.7,
            segments=72,
            cap=True,
            closed=True,
        ),
        ASSETS.mesh_path("differential_housing.obj"),
    )
    housing.visual(pumpkin_mesh, material=cast_iron)

    for side in (-1.0, 1.0):
        housing.visual(
            Cylinder(radius=0.050, length=0.640),
            origin=_origin_y((0.0, side * 0.500, 0.0)),
            material=cast_iron,
        )
        housing.visual(
            Cylinder(radius=0.058, length=0.060),
            origin=_origin_y((0.0, side * 0.770, 0.0)),
            material=cast_iron,
        )
        housing.visual(
            Cylinder(radius=0.110, length=0.010),
            origin=_origin_y((0.0, side * 0.802, 0.0)),
            material=black_oxide,
        )
        housing.visual(
            Box((0.190, 0.120, 0.014)),
            origin=Origin(xyz=(0.0, side * 0.340, 0.057)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.160, 0.090, 0.008)),
            origin=Origin(xyz=(0.0, side * 0.340, 0.068)),
            material=rubber_isolator,
        )
        housing.visual(
            Box((0.050, 0.120, 0.025)),
            origin=Origin(xyz=(0.0, side * 0.340, 0.074)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.012, 0.050, 0.110)),
            origin=Origin(xyz=(-0.036, side * 0.520, 0.090)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.012, 0.050, 0.110)),
            origin=Origin(xyz=(0.036, side * 0.520, 0.090)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.012, 0.060, 0.100)),
            origin=Origin(xyz=(-0.040, side * 0.205, -0.070)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.012, 0.060, 0.100)),
            origin=Origin(xyz=(0.040, side * 0.205, -0.070)),
            material=cast_iron,
        )
        housing.visual(
            Box((0.092, 0.040, 0.014)),
            origin=Origin(xyz=(0.0, side * 0.205, -0.120)),
            material=cast_iron,
        )

    housing.visual(
        Cylinder(radius=0.132, length=0.046),
        origin=_origin_x((-0.145, 0.0, 0.0)),
        material=cast_iron,
    )
    housing.visual(
        Cylinder(radius=0.146, length=0.012),
        origin=_origin_x((-0.120, 0.0, 0.0)),
        material=cast_iron,
    )
    _add_cover_bolts(housing, zinc_hardware)

    housing.visual(
        Cylinder(radius=0.072, length=0.104),
        origin=_origin_x((0.170, 0.0, 0.0)),
        material=cast_iron,
    )
    housing.visual(
        Cylinder(radius=0.048, length=0.080),
        origin=_origin_x((0.245, 0.0, 0.0)),
        material=cast_iron,
    )
    housing.visual(
        Box((0.112, 0.030, 0.118)),
        origin=Origin(xyz=(0.012, -0.075, -0.010)),
        material=cast_iron,
    )
    housing.visual(
        Box((0.112, 0.030, 0.118)),
        origin=Origin(xyz=(0.012, 0.075, -0.010)),
        material=cast_iron,
    )
    housing.visual(
        Box((0.128, 0.080, 0.022)),
        origin=Origin(xyz=(0.020, 0.0, -0.112)),
        material=cast_iron,
    )
    housing.visual(
        Cylinder(radius=0.018, length=0.024),
        origin=Origin(xyz=(0.030, -0.015, 0.154)),
        material=black_oxide,
    )
    housing.visual(
        Cylinder(radius=0.010, length=0.016),
        origin=_origin_x((-0.172, 0.042, 0.072)),
        material=zinc_hardware,
    )
    housing.visual(
        Cylinder(radius=0.011, length=0.018),
        origin=_origin_x((-0.172, 0.000, -0.108)),
        material=zinc_hardware,
    )
    housing.inertial = Inertial.from_geometry(
        Box((0.56, 1.66, 0.38)),
        mass=92.0,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
    )

    left_hub = model.part("left_hub")
    _build_hub(left_hub, -1.0, machined_steel, zinc_hardware, black_oxide)

    right_hub = model.part("right_hub")
    _build_hub(right_hub, 1.0, machined_steel, zinc_hardware, black_oxide)

    pinion = model.part("pinion_flange")
    pinion.visual(
        Cylinder(radius=0.034, length=0.042),
        origin=_origin_x((0.021, 0.0, 0.0)),
        material=machined_steel,
    )
    pinion.visual(
        Cylinder(radius=0.062, length=0.016),
        origin=_origin_x((0.046, 0.0, 0.0)),
        material=machined_steel,
    )
    pinion.visual(
        Cylinder(radius=0.024, length=0.030),
        origin=_origin_x((0.066, 0.0, 0.0)),
        material=black_oxide,
    )
    pinion.visual(
        Cylinder(radius=0.018, length=0.018),
        origin=_origin_x((0.086, 0.0, 0.0)),
        material=black_oxide,
    )
    for dy, dz in ((0.034, 0.0), (-0.034, 0.0), (0.0, 0.034), (0.0, -0.034)):
        pinion.visual(
            Cylinder(radius=0.010, length=0.018),
            origin=_origin_x((0.052, dy, dz)),
            material=zinc_hardware,
        )
    pinion.inertial = Inertial.from_geometry(
        Box((0.11, 0.14, 0.14)),
        mass=3.4,
        origin=Origin(xyz=(0.050, 0.0, 0.0)),
    )

    model.articulation(
        "left_hub_spin",
        ArticulationType.CONTINUOUS,
        parent="axle_housing",
        child="left_hub",
        origin=Origin(xyz=(0.0, -0.828, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1800.0, velocity=40.0),
    )
    model.articulation(
        "right_hub_spin",
        ArticulationType.CONTINUOUS,
        parent="axle_housing",
        child="right_hub",
        origin=Origin(xyz=(0.0, 0.828, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1800.0, velocity=40.0),
    )
    model.articulation(
        "pinion_spin",
        ArticulationType.CONTINUOUS,
        parent="axle_housing",
        child="pinion_flange",
        origin=Origin(xyz=(0.292, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=650.0, velocity=90.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
