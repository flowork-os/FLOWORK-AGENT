# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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

# ===== model =====
import math
from pathlib import Path
ASSETS = AssetContext.from_script(__file__)
POLAR_TILT = math.radians(52.0)
POLAR_AXIS_DIR = (-math.sin(POLAR_TILT), 0.0, math.cos(POLAR_TILT))
POLAR_JOINT_XYZ = (0.0, 0.0, 0.985)
DECLINATION_JOINT_XYZ = (0.0, 0.0, 0.330)
TUBE_MOUNT_XYZ = (0.118, 0.0, 0.275)
def _offset(
    point: tuple[float, float, float],
    direction: tuple[float, float, float],
    distance: float,
) -> tuple[float, float, float]:
    return (
        point[0] + direction[0] * distance,
        point[1] + direction[1] * distance,
        point[2] + direction[2] * distance,
    )
def _midpoint(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
def _rpy_for_member(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    length_xy = math.hypot(dx, dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(length_xy, dz)
    return (0.0, pitch, yaw)
def _add_member(
    part,
    name: str,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    *,
    radius: float,
    material,
) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_member(a, b)),
        material=material,
        name=name,
    )
def _add_quad(geometry: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    geometry.add_face(a, b, c)
    geometry.add_face(a, c, d)
def _build_annular_cylinder_mesh(
    *,
    length: float,
    outer_radius: float,
    inner_radius: float,
    segments: int = 48,
) -> MeshGeometry:
    geometry = MeshGeometry()
    half_length = length * 0.5

    outer_back: list[int] = []
    outer_front: list[int] = []
    inner_back: list[int] = []
    inner_front: list[int] = []

    for index in range(segments):
        angle = (2.0 * math.pi * index) / segments
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        outer_back.append(geometry.add_vertex(-half_length, outer_radius * cos_a, outer_radius * sin_a))
        outer_front.append(geometry.add_vertex(half_length, outer_radius * cos_a, outer_radius * sin_a))
        inner_back.append(geometry.add_vertex(-half_length, inner_radius * cos_a, inner_radius * sin_a))
        inner_front.append(geometry.add_vertex(half_length, inner_radius * cos_a, inner_radius * sin_a))

    for index in range(segments):
        next_index = (index + 1) % segments
        _add_quad(
            geometry,
            outer_back[index],
            outer_back[next_index],
            outer_front[next_index],
            outer_front[index],
        )
        _add_quad(
            geometry,
            inner_back[index],
            inner_front[index],
            inner_front[next_index],
            inner_back[next_index],
        )
        _add_quad(
            geometry,
            outer_front[index],
            outer_front[next_index],
            inner_front[next_index],
            inner_front[index],
        )
        _add_quad(
            geometry,
            outer_back[index],
            inner_back[index],
            inner_back[next_index],
            outer_back[next_index],
        )

    return geometry
def _mesh(name: str, geometry: MeshGeometry):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(name))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="newtonian_reflector_equatorial_mount", assets=ASSETS)

    tripod_steel = model.material("tripod_steel", rgba=(0.34, 0.36, 0.39, 1.0))
    mount_paint = model.material("mount_paint", rgba=(0.77, 0.79, 0.82, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.18, 0.19, 0.21, 1.0))
    tube_paint = model.material("tube_paint", rgba=(0.95, 0.95, 0.96, 1.0))
    trim_black = model.material("trim_black", rgba=(0.08, 0.09, 0.10, 1.0))
    mirror_glass = model.material("mirror_glass", rgba=(0.66, 0.77, 0.86, 0.55))
    counterweight_metal = model.material("counterweight_metal", rgba=(0.54, 0.56, 0.60, 1.0))

    tube_shell_mesh = _mesh(
        "tube_shell.obj",
        _build_annular_cylinder_mesh(length=0.920, outer_radius=0.118, inner_radius=0.114, segments=56),
    )
    tube_ring_mesh = _mesh(
        "tube_ring.obj",
        _build_annular_cylinder_mesh(length=0.020, outer_radius=0.132, inner_radius=0.118, segments=48),
    )
    mirror_cell_mesh = _mesh(
        "mirror_cell.obj",
        _build_annular_cylinder_mesh(length=0.060, outer_radius=0.114, inner_radius=0.096, segments=48),
    )
    aperture_ring_mesh = _mesh(
        "aperture_ring.obj",
        _build_annular_cylinder_mesh(length=0.018, outer_radius=0.121, inner_radius=0.114, segments=48),
    )

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.090, length=0.060),
        origin=Origin(xyz=(0.0, 0.0, 0.840)),
        material=tripod_steel,
        name="tripod_crown",
    )
    tripod.visual(
        Cylinder(radius=0.055, length=0.080),
        origin=Origin(xyz=(0.0, 0.0, 0.895)),
        material=tripod_steel,
        name="tripod_head",
    )
    latitude_seat_center = _offset(POLAR_JOINT_XYZ, POLAR_AXIS_DIR, -0.016)
    tripod.visual(
        Cylinder(radius=0.042, length=0.032),
        origin=Origin(xyz=latitude_seat_center, rpy=(0.0, -POLAR_TILT, 0.0)),
        material=tripod_steel,
        name="latitude_seat",
    )
    tripod.visual(
        Cylinder(radius=0.024, length=0.100),
        origin=Origin(
            xyz=_offset(POLAR_JOINT_XYZ, POLAR_AXIS_DIR, -0.066),
            rpy=(0.0, -POLAR_TILT, 0.0),
        ),
        material=tripod_steel,
        name="latitude_riser",
    )
    tripod.visual(
        Box((0.080, 0.095, 0.060)),
        origin=Origin(xyz=(0.040, 0.0, 0.925), rpy=(0.0, -POLAR_TILT, 0.0)),
        material=tripod_steel,
        name="latitude_wedge",
    )
    tripod.visual(
        Cylinder(radius=0.040, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 0.420)),
        material=tripod_steel,
        name="spreader_hub",
    )
    tripod.visual(
        Cylinder(radius=0.115, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.396)),
        material=dark_metal,
        name="accessory_tray",
    )
    leg_top_radius = 0.080
    knee_radius = 0.250
    foot_radius = 0.560
    leg_top_z = 0.840
    knee_z = 0.490
    foot_z = 0.020
    brace_hub = (0.0, 0.0, 0.420)
    for index, angle in enumerate((math.radians(90.0), math.radians(210.0), math.radians(330.0))):
        top = (leg_top_radius * math.cos(angle), leg_top_radius * math.sin(angle), leg_top_z)
        knee = (knee_radius * math.cos(angle), knee_radius * math.sin(angle), knee_z)
        foot = (foot_radius * math.cos(angle), foot_radius * math.sin(angle), foot_z)
        _add_member(tripod, f"upper_leg_{index}", top, knee, radius=0.018, material=tripod_steel)
        _add_member(tripod, f"lower_leg_{index}", knee, foot, radius=0.014, material=tripod_steel)
        _add_member(tripod, f"tray_brace_{index}", brace_hub, knee, radius=0.008, material=tripod_steel)
        tripod.visual(
            Cylinder(radius=0.030, length=0.020),
            origin=Origin(xyz=(foot[0], foot[1], 0.010)),
            material=dark_metal,
            name=f"foot_pad_{index}",
        )
    tripod.inertial = Inertial.from_geometry(
        Box((1.20, 1.20, 1.02)),
        mass=8.6,
        origin=Origin(xyz=(0.0, 0.0, 0.51)),
    )

    polar = model.part("polar_assembly")
    polar.visual(
        Cylinder(radius=0.042, length=0.032),
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
        material=mount_paint,
        name="polar_base",
    )
    polar.visual(
        Cylinder(radius=0.029, length=0.180),
        origin=Origin(xyz=(0.0, 0.0, 0.122)),
        material=mount_paint,
        name="polar_housing",
    )
    polar.visual(
        Cylinder(radius=0.041, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.052)),
        material=trim_black,
        name="setting_circle",
    )
    polar.visual(
        Box((0.070, 0.046, 0.055)),
        origin=Origin(xyz=(0.055, 0.0, 0.112)),
        material=dark_metal,
        name="drive_motor",
    )
    polar.visual(
        Box((0.045, 0.110, 0.085)),
        origin=Origin(xyz=(0.006, 0.0, 0.243)),
        material=mount_paint,
        name="declination_carrier",
    )
    polar.visual(
        Box((0.042, 0.014, 0.150)),
        origin=Origin(xyz=(0.0, 0.060, 0.330)),
        material=mount_paint,
        name="left_cheek",
    )
    polar.visual(
        Box((0.042, 0.014, 0.150)),
        origin=Origin(xyz=(0.0, -0.060, 0.330)),
        material=mount_paint,
        name="right_cheek",
    )
    polar.inertial = Inertial.from_geometry(
        Box((0.18, 0.16, 0.42)),
        mass=5.6,
        origin=Origin(xyz=(0.01, 0.0, 0.21)),
    )

    declination = model.part("declination_head")
    declination.visual(
        Box((0.042, 0.106, 0.042)),
        material=dark_metal,
        name="declination_hub",
    )
    declination.visual(Box((0.055, 0.055, 0.045)), material=mount_paint, name="hub_block")
    declination.visual(
        Box((0.060, 0.045, 0.030)),
        origin=Origin(xyz=(0.045, 0.0, 0.015)),
        material=mount_paint,
        name="saddle_stem",
    )
    declination.visual(
        Box((0.050, 0.048, 0.100)),
        origin=Origin(xyz=(0.080, 0.0, 0.065)),
        material=mount_paint,
        name="saddle_tower",
    )
    declination.visual(
        Box((0.138, 0.055, 0.014)),
        origin=Origin(xyz=(0.090, 0.0, 0.122)),
        material=dark_metal,
        name="saddle_plate",
    )
    declination.visual(
        Box((0.160, 0.015, 0.030)),
        origin=Origin(xyz=(0.118, 0.0325, 0.140)),
        material=dark_metal,
        name="saddle_clamp_left",
    )
    declination.visual(
        Box((0.160, 0.015, 0.030)),
        origin=Origin(xyz=(0.118, -0.0325, 0.140)),
        material=dark_metal,
        name="saddle_clamp_right",
    )
    declination.visual(
        Box((0.250, 0.026, 0.028)),
        origin=Origin(xyz=(-0.125, 0.0, -0.005)),
        material=dark_metal,
        name="counterweight_arm",
    )
    declination.visual(
        Box((0.030, 0.026, 0.090)),
        origin=Origin(xyz=(-0.230, 0.0, -0.045)),
        material=dark_metal,
        name="counterweight_drop",
    )
    declination.visual(
        Box((0.040, 0.045, 0.040)),
        origin=Origin(xyz=(-0.240, 0.0, -0.085)),
        material=dark_metal,
        name="counterweight_clamp",
    )
    declination.visual(
        Cylinder(radius=0.012, length=0.240),
        origin=Origin(xyz=(-0.350, 0.0, -0.085), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="counterweight_shaft",
    )
    declination.visual(
        Cylinder(radius=0.022, length=0.028),
        origin=Origin(xyz=(-0.275, 0.0, -0.085), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="counterweight_collar",
    )
    declination.visual(
        Cylinder(radius=0.052, length=0.048),
        origin=Origin(xyz=(-0.335, 0.0, -0.085), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=counterweight_metal,
        name="weight_outer",
    )
    declination.visual(
        Cylinder(radius=0.046, length=0.048),
        origin=Origin(xyz=(-0.405, 0.0, -0.085), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=counterweight_metal,
        name="weight_inner",
    )
    declination.visual(
        Cylinder(radius=0.020, length=0.016),
        origin=Origin(xyz=(-0.462, 0.0, -0.085), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="shaft_stop",
    )
    declination.inertial = Inertial.from_geometry(
        Box((0.72, 0.11, 0.30)),
        mass=6.0,
        origin=Origin(xyz=(-0.14, 0.0, 0.0)),
    )

    optical_tube = model.part("optical_tube")
    optical_tube.visual(tube_shell_mesh, material=tube_paint, name="tube_shell")
    optical_tube.visual(
        aperture_ring_mesh,
        origin=Origin(xyz=(0.451, 0.0, 0.0)),
        material=trim_black,
        name="aperture_ring",
    )
    optical_tube.visual(
        mirror_cell_mesh,
        origin=Origin(xyz=(-0.420, 0.0, 0.0)),
        material=trim_black,
        name="mirror_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.098, length=0.012),
        origin=Origin(xyz=(-0.404, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=mirror_glass,
        name="primary_mirror",
    )
    optical_tube.visual(
        Box((0.003, 0.228, 0.010)),
        origin=Origin(xyz=(0.292, 0.0, 0.0)),
        material=trim_black,
        name="spider_vane_y",
    )
    optical_tube.visual(
        Box((0.003, 0.010, 0.228)),
        origin=Origin(xyz=(0.292, 0.0, 0.0)),
        material=trim_black,
        name="spider_vane_z",
    )
    optical_tube.visual(
        Box((0.020, 0.040, 0.030)),
        origin=Origin(xyz=(0.292, 0.0, 0.0), rpy=(0.0, math.pi / 4.0, 0.0)),
        material=trim_black,
        name="secondary_mirror",
    )
    optical_tube.visual(tube_ring_mesh, origin=Origin(xyz=(-0.170, 0.0, 0.0)), material=dark_metal, name="rear_ring")
    optical_tube.visual(tube_ring_mesh, origin=Origin(xyz=(0.160, 0.0, 0.0)), material=dark_metal, name="front_ring")
    optical_tube.visual(
        Box((0.028, 0.045, 0.090)),
        origin=Origin(xyz=(-0.170, 0.0, -0.104)),
        material=dark_metal,
        name="rear_ring_post",
    )
    optical_tube.visual(
        Box((0.028, 0.045, 0.090)),
        origin=Origin(xyz=(0.160, 0.0, -0.104)),
        material=dark_metal,
        name="front_ring_post",
    )
    optical_tube.visual(
        Box((0.220, 0.050, 0.016)),
        origin=Origin(xyz=(0.000, 0.0, -0.135)),
        material=dark_metal,
        name="dovetail_rail",
    )
    optical_tube.visual(
        Box((0.110, 0.045, 0.016)),
        origin=Origin(xyz=(0.080, 0.0, -0.119)),
        material=dark_metal,
        name="saddle_block",
    )
    optical_tube.visual(
        Box((0.060, 0.045, 0.008)),
        origin=Origin(xyz=(0.195, 0.0, 0.118)),
        material=trim_black,
        name="focuser_base",
    )
    optical_tube.visual(
        Cylinder(radius=0.021, length=0.058),
        origin=Origin(xyz=(0.195, 0.0, 0.143)),
        material=trim_black,
        name="focuser_housing",
    )
    optical_tube.visual(
        Cylinder(radius=0.015, length=0.086),
        origin=Origin(xyz=(0.195, 0.0, 0.211)),
        material=dark_metal,
        name="eyepiece",
    )
    optical_tube.visual(
        Box((0.085, 0.022, 0.012)),
        origin=Origin(xyz=(0.050, 0.0, 0.124)),
        material=dark_metal,
        name="finder_base",
    )
    optical_tube.visual(
        Box((0.016, 0.020, 0.030)),
        origin=Origin(xyz=(0.000, 0.0, 0.145)),
        material=dark_metal,
        name="finder_rear_post",
    )
    optical_tube.visual(
        Box((0.016, 0.020, 0.030)),
        origin=Origin(xyz=(0.100, 0.0, 0.145)),
        material=dark_metal,
        name="finder_front_post",
    )
    optical_tube.visual(
        Cylinder(radius=0.017, length=0.180),
        origin=Origin(xyz=(0.050, 0.0, 0.177), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_black,
        name="finder_scope",
    )
    optical_tube.inertial = Inertial.from_geometry(
        Box((0.94, 0.27, 0.38)),
        mass=7.2,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
    )

    model.articulation(
        "polar_axis",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=polar,
        origin=Origin(xyz=POLAR_JOINT_XYZ, rpy=(0.0, -POLAR_TILT, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=35.0, velocity=1.2),
    )
    model.articulation(
        "declination_axis",
        ArticulationType.REVOLUTE,
        parent=polar,
        child=declination,
        origin=Origin(xyz=DECLINATION_JOINT_XYZ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=26.0, velocity=0.9, lower=-0.10, upper=0.90),
    )
    model.articulation(
        "tube_mount",
        ArticulationType.FIXED,
        parent=declination,
        child=optical_tube,
        origin=Origin(xyz=TUBE_MOUNT_XYZ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
