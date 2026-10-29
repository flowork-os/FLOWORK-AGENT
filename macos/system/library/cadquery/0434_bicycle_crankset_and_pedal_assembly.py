# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_crankset_and_pedal_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_crankset_and_pedal_assembly

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

def _point_in_polygon(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-30) + xi):
            inside = not inside
        j = i
    return inside

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

# ===== brackets_hinges_bezels (1 syms) =====
def _polygon_centroid(points):
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    n = max(1, len(points))
    return (sx / float(n), sy / float(n))

# ===== lathe_extrude_loft (3 syms) =====
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

class ExtrudeWithHolesGeometry(MeshGeometry):
    """Extrude a 2D outer profile minus one or more through-holes."""

    def __init__(self, outer_profile, hole_profiles, height, *, cap=True,
                 center=True, closed=True):
        super().__init__()
        height = float(height)
        if height <= 0:
            raise ValidationError("Extrude height must be positive")

        outer = _ensure_ccw(_profile_points_2d(outer_profile))
        holes = [_ensure_ccw(_profile_points_2d(h)) for h in hole_profiles]
        if not closed:
            cap = False

        for hole in holes:
            c = _polygon_centroid(hole)
            if not _point_in_polygon(c, outer):
                raise ValidationError("Hole profile must lie inside outer profile")

        if not holes:
            self._set(_to_shape(ExtrudeGeometry(outer, height, cap=cap,
                                                center=center, closed=closed)))
            return

        z0 = -height / 2.0 if center else 0.0
        z1 = z0 + height

        if cap:
            outer_wire = cq.Wire.makePolygon(
                [cq.Vector(x, y, 0.0) for (x, y) in outer], close=True)
            hole_wires = [
                cq.Wire.makePolygon([cq.Vector(x, y, 0.0) for (x, y) in h], close=True)
                for h in holes
            ]
            solid = cq.Solid.extrudeLinear(outer_wire, hole_wires, cq.Vector(0, 0, height))
            if z0:
                solid = solid.translate(cq.Vector(0, 0, z0))
            self._set(solid)
            return

        # Open shell: outer side walls + interior (reversed) hole side walls.
        faces = _loft_side_faces(
            [[(x, y, z0) for (x, y) in outer], [(x, y, z1) for (x, y) in outer]], closed)
        for hole in holes:
            hole_cw = list(reversed(hole))
            faces += _loft_side_faces(
                [[(x, y, z0) for (x, y) in hole_cw], [(x, y, z1) for (x, y) in hole_cw]], closed)
        if not faces:
            raise ValidationError("ExtrudeWithHoles produced no valid side faces")
        self._set(cq.Shell.makeShell(faces))

# ===== model =====
import math
ASSETS = AssetContext.from_script(__file__)
def _save_mesh(name: str, geometry):
    return mesh_from_geometry(geometry, ASSETS.mesh_path(name))
def _circle_profile(radius: float, segments: int) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos((2.0 * math.pi * index) / segments),
            radius * math.sin((2.0 * math.pi * index) / segments),
        )
        for index in range(segments)
    ]
def _transform_profile(
    profile: list[tuple[float, float]],
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    angle: float = 0.0,
) -> list[tuple[float, float]]:
    c = math.cos(angle)
    s = math.sin(angle)
    return [(c * x - s * y + dx, s * x + c * y + dy) for x, y in profile]
def _build_ring_mesh(
    outer_radius: float,
    inner_radius: float,
    width: float,
    *,
    outer_segments: int = 56,
    inner_segments: int = 40,
):
    return ExtrudeWithHolesGeometry(
        _circle_profile(outer_radius, outer_segments),
        [_circle_profile(inner_radius, inner_segments)],
        height=width,
        center=True,
    ).rotate_x(math.pi / 2.0)
def _build_crank_arm_mesh():
    outer = [
        (0.018, -0.012),
        (0.024, -0.018),
        (0.055, -0.019),
        (0.106, -0.015),
        (0.146, -0.013),
        (0.164, -0.015),
        (0.172, -0.010),
        (0.176, 0.000),
        (0.172, 0.010),
        (0.164, 0.015),
        (0.146, 0.013),
        (0.106, 0.015),
        (0.055, 0.019),
        (0.024, 0.018),
        (0.018, 0.012),
        (0.014, 0.000),
    ]
    inner = [
        (0.036, -0.006),
        (0.044, -0.010),
        (0.084, -0.009),
        (0.125, -0.007),
        (0.146, -0.005),
        (0.150, 0.000),
        (0.146, 0.005),
        (0.125, 0.007),
        (0.084, 0.009),
        (0.044, 0.010),
        (0.036, 0.006),
        (0.032, 0.000),
    ]
    return ExtrudeWithHolesGeometry(
        outer,
        [inner],
        height=0.018,
        center=True,
    ).rotate_x(math.pi / 2.0)
def _build_chainring_mesh():
    window_profile = rounded_rect_profile(0.030, 0.056, radius=0.006, corner_segments=6)
    holes = [_circle_profile(0.024, 36)]
    for index in range(5):
        angle = (2.0 * math.pi * index / 5.0) + (math.pi / 10.0)
        holes.append(
            _transform_profile(
                window_profile,
                dx=math.cos(angle) * 0.057,
                dy=math.sin(angle) * 0.057,
                angle=angle,
            )
        )
    return ExtrudeWithHolesGeometry(
        _circle_profile(0.104, 84),
        holes,
        height=0.004,
        center=True,
    ).rotate_x(math.pi / 2.0)
def _add_platform_pedal(part, *, side_sign: float, alloy, dark_metal):
    pedal_y = side_sign * 0.046
    part.visual(
        Cylinder(radius=0.0060, length=0.020),
        origin=Origin(xyz=(0.0, side_sign * 0.010, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="spindle",
    )
    part.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(0.0, side_sign * 0.007, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="inner_hub",
    )
    part.visual(
        Box((0.094, 0.070, 0.004)),
        origin=Origin(xyz=(0.0, pedal_y, 0.012)),
        material=alloy,
        name="top_plate",
    )
    part.visual(
        Box((0.094, 0.070, 0.004)),
        origin=Origin(xyz=(0.0, pedal_y, -0.012)),
        material=alloy,
        name="bottom_plate",
    )
    part.visual(
        Box((0.006, 0.070, 0.024)),
        origin=Origin(xyz=(0.044, pedal_y, 0.0)),
        material=alloy,
        name="front_bar",
    )
    part.visual(
        Box((0.006, 0.070, 0.024)),
        origin=Origin(xyz=(-0.044, pedal_y, 0.0)),
        material=alloy,
        name="rear_bar",
    )
    part.visual(
        Box((0.094, 0.006, 0.020)),
        origin=Origin(xyz=(0.0, side_sign * 0.014, 0.0)),
        material=alloy,
        name="inboard_plate",
    )
    part.visual(
        Box((0.094, 0.006, 0.024)),
        origin=Origin(xyz=(0.0, side_sign * 0.078, 0.0)),
        material=alloy,
        name="outboard_plate",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="road_bike_crankset", assets=ASSETS)

    forged_alloy = model.material("forged_alloy", rgba=(0.70, 0.72, 0.75, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.22, 0.24, 0.27, 1.0))
    anodized_black = model.material("anodized_black", rgba=(0.08, 0.08, 0.09, 1.0))

    arm_mesh = _save_mesh("road_bike_crank_arm.obj", _build_crank_arm_mesh())
    chainring_mesh = _save_mesh("road_bike_chainring.obj", _build_chainring_mesh())
    cup_mesh = _save_mesh("road_bike_bottom_bracket_cup.obj", _build_ring_mesh(0.028, 0.018, 0.012))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(cup_mesh, origin=Origin(xyz=(0.0, -0.040, 0.0)), material=dark_metal, name="right_cup")
    bottom_bracket.visual(cup_mesh, origin=Origin(xyz=(0.0, 0.040, 0.0)), material=dark_metal, name="left_cup")
    bottom_bracket.visual(
        Box((0.008, 0.068, 0.008)),
        origin=Origin(xyz=(0.022, 0.0, 0.0)),
        material=anodized_black,
        name="connector_right",
    )
    bottom_bracket.visual(
        Box((0.008, 0.068, 0.008)),
        origin=Origin(xyz=(-0.022, 0.0, 0.0)),
        material=anodized_black,
        name="connector_left",
    )
    bottom_bracket.inertial = Inertial.from_geometry(Box((0.070, 0.100, 0.070)), mass=0.28)

    crankset = model.part("crankset")
    crankset.visual(
        Cylinder(radius=0.014, length=0.092),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="spindle_shaft",
    )
    crankset.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.0, -0.052, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="right_interface",
    )
    crankset.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.0, 0.052, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="left_interface",
    )
    crankset.visual(
        Cylinder(radius=0.024, length=0.014),
        origin=Origin(xyz=(0.0, -0.053, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="right_arm_root",
    )
    crankset.visual(
        arm_mesh,
        origin=Origin(xyz=(0.0, -0.069, 0.0)),
        material=forged_alloy,
        name="right_arm_panel",
    )
    crankset.visual(
        Cylinder(radius=0.013, length=0.010),
        origin=Origin(xyz=(0.172, -0.069, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="right_pedal_boss",
    )
    crankset.visual(
        chainring_mesh,
        origin=Origin(xyz=(0.0, -0.062, 0.0)),
        material=anodized_black,
        name="spider_chainring",
    )
    crankset.visual(
        Cylinder(radius=0.024, length=0.010),
        origin=Origin(xyz=(0.0, -0.060, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="chainring_hub",
    )
    for index in range(5):
        angle = (2.0 * math.pi * index / 5.0) + (math.pi / 10.0)
        crankset.visual(
            Cylinder(radius=0.0045, length=0.008),
            origin=Origin(
                xyz=(math.cos(angle) * 0.043, -0.062, math.sin(angle) * 0.043),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=forged_alloy,
            name=f"chainring_bolt_{index}",
        )
    crankset.visual(
        Cylinder(radius=0.024, length=0.014),
        origin=Origin(xyz=(0.0, 0.053, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="left_arm_root",
    )
    crankset.visual(
        arm_mesh,
        origin=Origin(xyz=(0.0, 0.069, 0.0), rpy=(0.0, math.pi, 0.0)),
        material=forged_alloy,
        name="left_arm_panel",
    )
    crankset.visual(
        Cylinder(radius=0.013, length=0.010),
        origin=Origin(xyz=(-0.172, 0.069, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="left_pedal_boss",
    )
    crankset.inertial = Inertial.from_geometry(
        Box((0.360, 0.180, 0.220)),
        mass=1.34,
        origin=Origin(),
    )

    right_pedal = model.part("right_pedal")
    _add_platform_pedal(right_pedal, side_sign=-1.0, alloy=forged_alloy, dark_metal=dark_metal)
    right_pedal.inertial = Inertial.from_geometry(
        Box((0.094, 0.096, 0.024)),
        mass=0.24,
        origin=Origin(xyz=(0.0, -0.046, 0.0)),
    )

    left_pedal = model.part("left_pedal")
    _add_platform_pedal(left_pedal, side_sign=1.0, alloy=forged_alloy, dark_metal=dark_metal)
    left_pedal.inertial = Inertial.from_geometry(
        Box((0.094, 0.096, 0.024)),
        mass=0.24,
        origin=Origin(xyz=(0.0, 0.046, 0.0)),
    )

    model.articulation(
        "bottom_bracket_spin",
        ArticulationType.CONTINUOUS,
        parent=bottom_bracket,
        child=crankset,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=12.0),
    )
    model.articulation(
        "right_pedal_spin",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=right_pedal,
        origin=Origin(xyz=(0.172, -0.074, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=20.0),
    )
    model.articulation(
        "left_pedal_spin",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=left_pedal,
        origin=Origin(xyz=(-0.172, 0.074, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=20.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
