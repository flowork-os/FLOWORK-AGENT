# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, box_fan_with_control_knob, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: box_fan_with_control_knob

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

def _points_match_2d(a, b, tol=1e-9):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol

def _polygon_area(points):
    area = 0.0
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return area * 0.5

def _ensure_ccw(points):
    area = _polygon_area(points)
    if abs(area) <= 1e-9:
        raise ValidationError("Profile area must be non-zero")
    return list(reversed(points)) if area < 0 else points

def _profile_points_2d(profile):
    points = [(float(x), float(y)) for (x, y) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not _points_match_2d(cleaned[-1], pt):
            cleaned.append(pt)
    if len(cleaned) >= 2 and _points_match_2d(cleaned[0], cleaned[-1]):
        cleaned = cleaned[:-1]
    if len(cleaned) < 3:
        raise ValidationError("Profile must have at least 3 unique points")
    return cleaned

def rounded_rect_profile(width, height, radius, *, corner_segments=6):
    width = float(width); height = float(height); radius = float(radius)
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    corner_segments = max(1, int(corner_segments))
    max_r = 0.5 * min(width, height)
    if radius < 0 or radius > max_r:
        raise ValidationError("radius must be within [0, %s]" % max_r)
    hw = width * 0.5; hh = height * 0.5
    if radius <= 1e-12:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r = radius

    def arc(cx, cy, a0, a1):
        out = []
        for i in range(corner_segments + 1):
            t = i / corner_segments
            a = a0 + (a1 - a0) * t
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return out

    pts = []
    pts.extend(arc(hw - r, -hh + r, -math.pi / 2.0, 0.0))
    pts.extend(arc(hw - r, hh - r, 0.0, math.pi / 2.0)[1:])
    pts.extend(arc(-hw + r, hh - r, math.pi / 2.0, math.pi)[1:])
    pts.extend(arc(-hw + r, -hh + r, math.pi, 3.0 * math.pi / 2.0)[1:])
    return pts

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

# ===== lathe_extrude_loft (2 syms) =====
def _loft_side_faces(rings, closed):
    """Ruled side-wall faces between consecutive 3D rings (matched point counts).
    Each quad is split into two planar triangles, matching the sdk mesh exactly."""
    faces = []
    ring_count = len(rings[0])
    seg = ring_count if closed else ring_count - 1
    for i in range(len(rings) - 1):
        a_ring = rings[i]
        b_ring = rings[i + 1]
        for j in range(seg):
            j2 = (j + 1) % ring_count
            quad = (a_ring[j], a_ring[j2], b_ring[j2], b_ring[j])
            for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                if (tri[0] == tri[1] or tri[1] == tri[2] or tri[2] == tri[0]):
                    continue
                try:
                    w = cq.Wire.makePolygon([cq.Vector(*p) for p in tri], close=True)
                    faces.append(cq.Face.makeFromWires(w))
                except Exception:
                    continue
    return faces

class ExtrudeGeometry(MeshGeometry):
    """Extrude a 2D profile by `height` along +Z. center=True -> z in
    [-h/2, h/2]; center=False -> z in [0, h]."""

    @classmethod
    def centered(cls, profile, height, *, cap=True, closed=True):
        return cls(profile, height, cap=cap, center=True, closed=closed)

    @classmethod
    def from_z0(cls, profile, height, *, cap=True, closed=True):
        return cls(profile, height, cap=cap, center=False, closed=closed)

    def __init__(self, profile, height, *, cap=True, center=True, closed=True):
        super().__init__()
        height = float(height)
        if height <= 0:
            raise ValidationError("Extrude height must be positive")

        points = _ensure_ccw(_profile_points_2d(profile))
        if not closed:
            cap = False

        if cap:
            self._set(_extrude_profile(points, height, center=center))
            return

        z0 = -height / 2.0 if center else 0.0
        z1 = z0 + height
        rings = [[(x, y, z0) for (x, y) in points], [(x, y, z1) for (x, y) in points]]
        faces = _loft_side_faces(rings, closed)
        if not faces:
            raise ValidationError("Extrude produced no valid side faces")
        self._set(cq.Shell.makeShell(faces))

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
ASSETS = AssetContext.from_script(__file__)
BASE_W = 0.20
BASE_D = 0.12
BASE_H = 0.03
BODY_W = 0.11
BODY_D = 0.085
BODY_H = 0.72
WALL_T = 0.007
FRONT_LIP_D = 0.006
INNER_W = BODY_W - 2.0 * WALL_T
VENT_BOTTOM = BASE_H + 0.06
VENT_TOP = BASE_H + 0.64
VENT_H = VENT_TOP - VENT_BOTTOM
BODY_TOP = BASE_H + BODY_H
BODY_UNDERSIDE_TOP = BODY_TOP - WALL_T
ROTOR_Y = 0.006
ROTOR_CENTER_Z = 0.5 * (VENT_BOTTOM + VENT_TOP)
ROTOR_RADIUS = 0.025
ROTOR_CORE_RADIUS = 0.010
ROTOR_PACK_L = 0.56
ROTOR_BLADE_L = 0.54
ROTOR_ENDCAP_T = 0.01
ROTOR_SHAFT_L = 0.01
ROTOR_SHAFT_R = 0.004
SUPPORT_D = 0.012
SUPPORT_T = 0.008
KNOB_PAD_W = 0.054
KNOB_PAD_D = 0.022
KNOB_PAD_H = 0.004
KNOB_R = 0.016
KNOB_H = 0.012
KNOB_INDICATOR_W = 0.010
KNOB_INDICATOR_D = 0.004
KNOB_INDICATOR_H = 0.002
BASE_CORNER_R = 0.018
PAD_CORNER_R = 0.006
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_box_fan", assets=ASSETS)

    shell = model.material("shell", rgba=(0.87, 0.88, 0.90, 1.0))
    trim = model.material("trim", rgba=(0.16, 0.18, 0.20, 1.0))
    base_mat = model.material("base", rgba=(0.20, 0.22, 0.24, 1.0))
    rotor_mat = model.material("rotor", rgba=(0.34, 0.36, 0.39, 1.0))
    knob_mat = model.material("knob", rgba=(0.12, 0.13, 0.14, 1.0))

    pedestal_geom = ExtrudeGeometry.centered(
        rounded_rect_profile(BASE_W * 0.92, BASE_D * 0.88, BASE_CORNER_R),
        BASE_H,
        cap=True,
        closed=True,
    )
    pedestal_geom.translate(0.0, 0.0, BASE_H / 2.0)
    pedestal_mesh = mesh_from_geometry(
        pedestal_geom,
        "assets/meshes/tower_fan_pedestal.obj",
    )

    control_pad_geom = ExtrudeGeometry.centered(
        rounded_rect_profile(KNOB_PAD_W, KNOB_PAD_D, PAD_CORNER_R),
        KNOB_PAD_H,
        cap=True,
        closed=True,
    )
    control_pad_geom.translate(
        0.0,
        BODY_D / 2.0 - KNOB_PAD_D / 2.0,
        BODY_TOP + KNOB_PAD_H / 2.0,
    )
    control_pad_mesh = mesh_from_geometry(
        control_pad_geom,
        "assets/meshes/tower_fan_control_pad.obj",
    )

    body = model.part("body")
    body.visual(
        pedestal_mesh,
        material=base_mat,
        name="pedestal",
    )
    body.visual(
        Box((BODY_W, WALL_T, BODY_H - 2.0 * WALL_T)),
        origin=Origin(
            xyz=(0.0, -BODY_D / 2.0 + WALL_T / 2.0, BASE_H + BODY_H / 2.0)
        ),
        material=shell,
        name="rear_panel",
    )
    body.visual(
        Box((WALL_T, BODY_D, BODY_H - 2.0 * WALL_T)),
        origin=Origin(
            xyz=(-BODY_W / 2.0 + WALL_T / 2.0, 0.0, BASE_H + BODY_H / 2.0)
        ),
        material=shell,
        name="left_wall",
    )
    body.visual(
        Box((WALL_T, BODY_D, BODY_H - 2.0 * WALL_T)),
        origin=Origin(
            xyz=(BODY_W / 2.0 - WALL_T / 2.0, 0.0, BASE_H + BODY_H / 2.0)
        ),
        material=shell,
        name="right_wall",
    )
    body.visual(
        Box((BODY_W, BODY_D, WALL_T)),
        origin=Origin(xyz=(0.0, 0.0, BASE_H + WALL_T / 2.0)),
        material=shell,
        name="bottom_cap",
    )
    body.visual(
        Box((BODY_W, BODY_D, WALL_T)),
        origin=Origin(xyz=(0.0, 0.0, BODY_TOP - WALL_T / 2.0)),
        material=shell,
        name="top_cap",
    )

    lower_panel_h = VENT_BOTTOM - (BASE_H + WALL_T)
    control_panel_h = BODY_UNDERSIDE_TOP - VENT_TOP
    front_panel_y = BODY_D / 2.0 - FRONT_LIP_D / 2.0

    body.visual(
        Box((INNER_W, FRONT_LIP_D, lower_panel_h)),
        origin=Origin(
            xyz=(0.0, front_panel_y, (BASE_H + WALL_T + VENT_BOTTOM) / 2.0)
        ),
        material=shell,
        name="front_lower_panel",
    )
    body.visual(
        Box((INNER_W, FRONT_LIP_D, control_panel_h)),
        origin=Origin(xyz=(0.0, front_panel_y, (VENT_TOP + BODY_UNDERSIDE_TOP) / 2.0)),
        material=shell,
        name="front_control_panel",
    )

    slat_count = 5
    slat_w = 0.004
    slat_d = 0.005
    slat_span = INNER_W - 0.018
    for idx in range(slat_count):
        if slat_count == 1:
            x_pos = 0.0
        else:
            x_pos = -slat_span / 2.0 + idx * (slat_span / (slat_count - 1))
        body.visual(
            Box((slat_w, slat_d, VENT_H)),
            origin=Origin(xyz=(x_pos, BODY_D / 2.0 - slat_d / 2.0 - 0.001, ROTOR_CENTER_Z)),
            material=trim,
            name=f"slat_{idx}",
        )

    body.visual(
        Box((INNER_W, SUPPORT_D, SUPPORT_T)),
        origin=Origin(xyz=(0.0, ROTOR_Y, VENT_BOTTOM - SUPPORT_T / 2.0)),
        material=trim,
        name="bottom_support",
    )
    body.visual(
        Box((INNER_W, SUPPORT_D, SUPPORT_T)),
        origin=Origin(xyz=(0.0, ROTOR_Y, VENT_TOP + SUPPORT_T / 2.0)),
        material=trim,
        name="top_support",
    )
    body.visual(
        control_pad_mesh,
        material=trim,
        name="control_pad",
    )
    body.inertial = Inertial.from_geometry(
        Box((BASE_W, BASE_D, BODY_TOP)),
        mass=4.2,
        origin=Origin(xyz=(0.0, 0.0, BODY_TOP / 2.0)),
    )

    rotor = model.part("rotor")
    rotor.visual(
        Cylinder(radius=ROTOR_CORE_RADIUS, length=ROTOR_PACK_L),
        material=rotor_mat,
        name="hub_core",
    )
    rotor.visual(
        Cylinder(radius=ROTOR_RADIUS, length=ROTOR_ENDCAP_T),
        origin=Origin(xyz=(0.0, 0.0, ROTOR_PACK_L / 2.0 - ROTOR_ENDCAP_T / 2.0)),
        material=rotor_mat,
        name="top_endcap",
    )
    rotor.visual(
        Cylinder(radius=ROTOR_RADIUS, length=ROTOR_ENDCAP_T),
        origin=Origin(xyz=(0.0, 0.0, -ROTOR_PACK_L / 2.0 + ROTOR_ENDCAP_T / 2.0)),
        material=rotor_mat,
        name="bottom_endcap",
    )
    rotor.visual(
        Cylinder(radius=ROTOR_SHAFT_R, length=ROTOR_SHAFT_L),
        origin=Origin(xyz=(0.0, 0.0, ROTOR_PACK_L / 2.0 + ROTOR_SHAFT_L / 2.0)),
        material=trim,
        name="top_shaft",
    )
    rotor.visual(
        Cylinder(radius=ROTOR_SHAFT_R, length=ROTOR_SHAFT_L),
        origin=Origin(xyz=(0.0, 0.0, -ROTOR_PACK_L / 2.0 - ROTOR_SHAFT_L / 2.0)),
        material=trim,
        name="bottom_shaft",
    )

    blade_count = 7
    blade_radial_t = 0.004
    blade_tangent_d = 0.012
    blade_radius = ROTOR_RADIUS - blade_radial_t / 2.0
    for idx in range(blade_count):
        theta = pi / 2.0 + idx * (2.0 * pi / blade_count)
        rotor.visual(
            Box((blade_radial_t, blade_tangent_d, ROTOR_BLADE_L)),
            origin=Origin(
                xyz=(blade_radius * cos(theta), blade_radius * sin(theta), 0.0),
                rpy=(0.0, 0.0, theta),
            ),
            material=rotor_mat,
            name=f"blade_{idx}",
        )

    rotor.inertial = Inertial.from_geometry(
        Cylinder(radius=ROTOR_RADIUS, length=ROTOR_PACK_L + 2.0 * ROTOR_SHAFT_L),
        mass=0.9,
        origin=Origin(),
    )

    knob = model.part("knob")
    knob.visual(
        Cylinder(radius=KNOB_R, length=KNOB_H),
        material=knob_mat,
        name="dial",
    )
    knob.visual(
        Box((KNOB_INDICATOR_W, KNOB_INDICATOR_D, KNOB_INDICATOR_H)),
        origin=Origin(
            xyz=(
                0.0,
                KNOB_R * 0.45,
                KNOB_H / 2.0 + KNOB_INDICATOR_H / 2.0,
            )
        ),
        material=trim,
        name="indicator",
    )
    knob.inertial = Inertial.from_geometry(
        Cylinder(radius=KNOB_R, length=KNOB_H),
        mass=0.05,
        origin=Origin(),
    )

    model.articulation(
        "rotor_spin",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=rotor,
        origin=Origin(xyz=(0.0, ROTOR_Y, ROTOR_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=20.0,
        ),
    )
    model.articulation(
        "knob_turn",
        ArticulationType.REVOLUTE,
        parent=body,
        child=knob,
        origin=Origin(
            xyz=(
                0.0,
                BODY_D / 2.0 - KNOB_PAD_D / 2.0,
                BODY_TOP + KNOB_PAD_H + KNOB_H / 2.0,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.5,
            velocity=4.0,
            lower=0.0,
            upper=4.71,
        ),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
