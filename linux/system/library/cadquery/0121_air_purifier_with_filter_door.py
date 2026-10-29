# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
BODY_WIDTH = 0.72
BODY_DEPTH = 0.56
BODY_HEIGHT = 1.40
CASTER_HEIGHT = 0.12
BODY_BOTTOM_Z = CASTER_HEIGHT
BODY_TOP_Z = BODY_BOTTOM_Z + BODY_HEIGHT
PANEL_THICKNESS = 0.028
def _rect_profile(
    width: float,
    height: float,
    *,
    cx: float = 0.0,
    cy: float = 0.0,
) -> list[tuple[float, float]]:
    half_w = width * 0.5
    half_h = height * 0.5
    return [
        (cx - half_w, cy - half_h),
        (cx + half_w, cy - half_h),
        (cx + half_w, cy + half_h),
        (cx - half_w, cy + half_h),
    ]
def _mesh(name: str, geometry):
    return mesh_from_geometry(geometry, name)
def _grille_mesh(
    name: str,
    *,
    width: float,
    height: float,
    thickness: float,
    cols: int,
    rows: int,
    border_x: float,
    border_z: float,
    web: float,
):
    outer = _rect_profile(width, height)
    usable_w = width - 2.0 * border_x
    usable_h = height - 2.0 * border_z
    hole_w = (usable_w - (cols - 1) * web) / cols
    hole_h = (usable_h - (rows - 1) * web) / rows
    holes: list[list[tuple[float, float]]] = []
    start_x = -width * 0.5 + border_x + hole_w * 0.5
    start_z = -height * 0.5 + border_z + hole_h * 0.5
    for row in range(rows):
        hole_z = start_z + row * (hole_h + web)
        for col in range(cols):
            hole_x = start_x + col * (hole_w + web)
            holes.append(_rect_profile(hole_w, hole_h, cx=hole_x, cy=hole_z))
    return _mesh(
        name,
        ExtrudeWithHolesGeometry(
            outer,
            holes,
            height=thickness,
            center=True,
        ).rotate_x(pi / 2.0),
    )
def _add_caster(part, *, steel, dark_steel, rubber) -> None:
    part.visual(
        Box((0.10, 0.08, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, -0.004)),
        material=steel,
        name="mount_plate",
    )
    part.visual(
        Cylinder(radius=0.020, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, -0.015)),
        material=dark_steel,
        name="swivel_head",
    )
    part.visual(
        Cylinder(radius=0.014, length=0.032),
        origin=Origin(xyz=(0.0, 0.0, -0.038)),
        material=dark_steel,
        name="swivel_stem",
    )
    part.visual(
        Box((0.070, 0.020, 0.016)),
        origin=Origin(xyz=(0.0, 0.0, -0.052)),
        material=steel,
        name="yoke_bridge",
    )
    for side_sign in (-1.0, 1.0):
        part.visual(
            Box((0.012, 0.020, 0.050)),
            origin=Origin(xyz=(side_sign * 0.024, 0.0, -0.056)),
            material=steel,
            name=f"yoke_cheek_{'left' if side_sign < 0.0 else 'right'}",
        )
    part.visual(
        Cylinder(radius=0.006, length=0.058),
        origin=Origin(xyz=(0.0, 0.0, -0.070), rpy=(0.0, pi / 2.0, 0.0)),
        material=dark_steel,
        name="axle",
    )
    part.visual(
        Cylinder(radius=0.050, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, -0.070), rpy=(0.0, pi / 2.0, 0.0)),
        material=rubber,
        name="wheel_tire",
    )
    part.visual(
        Cylinder(radius=0.020, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, -0.070), rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="wheel_hub",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="industrial_air_scrubber")

    cabinet_paint = model.material("cabinet_paint", rgba=(0.80, 0.81, 0.82, 1.0))
    trim_dark = model.material("trim_dark", rgba=(0.17, 0.18, 0.20, 1.0))
    blower_dark = model.material("blower_dark", rgba=(0.10, 0.11, 0.12, 1.0))
    steel = model.material("steel", rgba=(0.62, 0.64, 0.67, 1.0))
    hinge_steel = model.material("hinge_steel", rgba=(0.55, 0.57, 0.60, 1.0))
    rubber = model.material("rubber", rgba=(0.05, 0.05, 0.05, 1.0))

    cabinet = model.part("cabinet")
    cabinet.inertial = Inertial.from_geometry(
        Box((BODY_WIDTH, BODY_DEPTH, BODY_TOP_Z)),
        mass=92.0,
        origin=Origin(xyz=(0.0, 0.0, BODY_TOP_Z * 0.5)),
    )

    body_center_z = BODY_BOTTOM_Z + BODY_HEIGHT * 0.5
    cabinet.visual(
        Box((PANEL_THICKNESS, BODY_DEPTH, BODY_HEIGHT)),
        origin=Origin(xyz=(-BODY_WIDTH * 0.5 + PANEL_THICKNESS * 0.5, 0.0, body_center_z)),
        material=cabinet_paint,
        name="left_wall",
    )
    cabinet.visual(
        Box((PANEL_THICKNESS, BODY_DEPTH, BODY_HEIGHT)),
        origin=Origin(xyz=(BODY_WIDTH * 0.5 - PANEL_THICKNESS * 0.5, 0.0, body_center_z)),
        material=cabinet_paint,
        name="right_wall",
    )
    cabinet.visual(
        Box((BODY_WIDTH - 2.0 * PANEL_THICKNESS + 0.012, PANEL_THICKNESS, BODY_HEIGHT)),
        origin=Origin(xyz=(0.0, -BODY_DEPTH * 0.5 + PANEL_THICKNESS * 0.5, body_center_z)),
        material=cabinet_paint,
        name="back_wall",
    )
    cabinet.visual(
        Box((BODY_WIDTH - 0.020, BODY_DEPTH - 0.020, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.0, 0.0, BODY_BOTTOM_Z + PANEL_THICKNESS * 0.5)),
        material=trim_dark,
        name="base_pan",
    )
    cabinet.visual(
        Box((0.058, PANEL_THICKNESS, 1.18)),
        origin=Origin(xyz=(-0.332, BODY_DEPTH * 0.5 - PANEL_THICKNESS * 0.5, 0.770)),
        material=cabinet_paint,
        name="front_left_jamb",
    )
    cabinet.visual(
        Box((0.058, PANEL_THICKNESS, 1.18)),
        origin=Origin(xyz=(0.332, BODY_DEPTH * 0.5 - PANEL_THICKNESS * 0.5, 0.770)),
        material=cabinet_paint,
        name="front_right_jamb",
    )
    cabinet.visual(
        Box((0.672, PANEL_THICKNESS, 0.084)),
        origin=Origin(xyz=(0.0, BODY_DEPTH * 0.5 - PANEL_THICKNESS * 0.5, 0.162)),
        material=cabinet_paint,
        name="front_bottom_rail",
    )
    cabinet.visual(
        Box((0.672, PANEL_THICKNESS, 0.180)),
        origin=Origin(xyz=(0.0, BODY_DEPTH * 0.5 - PANEL_THICKNESS * 0.5, 1.430)),
        material=cabinet_paint,
        name="front_top_rail",
    )
    cabinet.visual(
        Box((BODY_WIDTH - 2.0 * PANEL_THICKNESS + 0.010, 0.160, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.0, 0.200, BODY_TOP_Z - PANEL_THICKNESS * 0.5)),
        material=cabinet_paint,
        name="top_front_rail",
    )
    cabinet.visual(
        Box((BODY_WIDTH - 2.0 * PANEL_THICKNESS + 0.010, 0.080, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.0, -0.240, BODY_TOP_Z - PANEL_THICKNESS * 0.5)),
        material=cabinet_paint,
        name="top_rear_rail",
    )
    cabinet.visual(
        Box((0.120, 0.320, PANEL_THICKNESS)),
        origin=Origin(xyz=(-0.300, -0.040, BODY_TOP_Z - PANEL_THICKNESS * 0.5)),
        material=cabinet_paint,
        name="top_left_rail",
    )
    cabinet.visual(
        Box((0.120, 0.320, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.300, -0.040, BODY_TOP_Z - PANEL_THICKNESS * 0.5)),
        material=cabinet_paint,
        name="top_right_rail",
    )
    cabinet.visual(
        Box((0.400, 0.220, 0.320)),
        origin=Origin(xyz=(0.0, -0.170, 1.360)),
        material=blower_dark,
        name="blower_plenum",
    )
    for z_pos, name in ((0.380, "lower_hinge_backer"), (1.160, "upper_hinge_backer")):
        cabinet.visual(
            Box((0.018, PANEL_THICKNESS, 0.220)),
            origin=Origin(xyz=(-0.348, BODY_DEPTH * 0.5 - PANEL_THICKNESS * 0.5, z_pos)),
            material=hinge_steel,
            name=name,
        )
    cabinet.visual(
        Box((0.026, 0.030, 0.590)),
        origin=Origin(xyz=(-0.362, 0.267, 0.770)),
        material=hinge_steel,
        name="door_hinge_bridge",
    )
    cabinet.visual(
        Cylinder(radius=0.012, length=0.590),
        origin=Origin(xyz=(-0.375, 0.294, 0.770)),
        material=hinge_steel,
        name="door_center_knuckle",
    )
    cabinet.visual(
        Box((0.220, 0.024, 0.020)),
        origin=Origin(xyz=(0.0, -0.267, BODY_TOP_Z + 0.004)),
        material=hinge_steel,
        name="baffle_hinge_bridge",
    )
    cabinet.visual(
        Cylinder(radius=0.010, length=0.220),
        origin=Origin(xyz=(0.0, -0.255, BODY_TOP_Z + 0.024), rpy=(0.0, pi / 2.0, 0.0)),
        material=hinge_steel,
        name="baffle_center_knuckle",
    )

    access_door = model.part("access_door")
    access_door.inertial = Inertial.from_geometry(
        Box((0.622, 0.030, 1.120)),
        mass=18.0,
        origin=Origin(xyz=(0.316, 0.020, 0.0)),
    )

    access_door.visual(
        Box((0.066, 0.028, 1.120)),
        origin=Origin(xyz=(0.093, 0.008, 0.0)),
        material=cabinet_paint,
        name="left_stile",
    )
    access_door.visual(
        Box((0.066, 0.028, 1.120)),
        origin=Origin(xyz=(0.639, 0.008, 0.0)),
        material=cabinet_paint,
        name="right_stile",
    )
    access_door.visual(
        Box((0.622, 0.028, 0.120)),
        origin=Origin(xyz=(0.366, 0.008, 0.500)),
        material=cabinet_paint,
        name="top_rail",
    )
    access_door.visual(
        Box((0.622, 0.028, 0.140)),
        origin=Origin(xyz=(0.366, 0.008, -0.490)),
        material=cabinet_paint,
        name="bottom_rail",
    )
    access_door.visual(
        Box((0.480, 0.020, 0.200)),
        origin=Origin(xyz=(0.366, 0.006, 0.300)),
        material=cabinet_paint,
        name="upper_panel",
    )
    access_door.visual(
        _grille_mesh(
            "access_door_grille",
            width=0.480,
            height=0.720,
            thickness=0.0035,
            cols=5,
            rows=7,
            border_x=0.032,
            border_z=0.042,
            web=0.012,
        ),
        origin=Origin(xyz=(0.366, 0.022, -0.060)),
        material=trim_dark,
        name="door_grille",
    )
    for z_pos, name in ((0.390, "upper_knuckle"), (-0.390, "lower_knuckle")):
        access_door.visual(
            Cylinder(radius=0.012, length=0.190),
            origin=Origin(xyz=(0.0, 0.0, z_pos)),
            material=hinge_steel,
            name=name,
        )
        access_door.visual(
            Box((0.056, 0.012, 0.200)),
            origin=Origin(xyz=(0.035, 0.010, z_pos)),
            material=hinge_steel,
            name=f"{name}_leaf",
        )
    access_door.visual(
        Box((0.014, 0.024, 0.036)),
        origin=Origin(xyz=(0.610, 0.031, 0.090)),
        material=hinge_steel,
        name="handle_upper_post",
    )
    access_door.visual(
        Box((0.014, 0.024, 0.036)),
        origin=Origin(xyz=(0.610, 0.031, -0.090)),
        material=hinge_steel,
        name="handle_lower_post",
    )
    access_door.visual(
        Cylinder(radius=0.012, length=0.240),
        origin=Origin(xyz=(0.610, 0.039, 0.0)),
        material=hinge_steel,
        name="handle_grip",
    )

    exhaust_baffle = model.part("exhaust_baffle")
    exhaust_baffle.inertial = Inertial.from_geometry(
        Box((0.480, 0.240, 0.070)),
        mass=5.0,
        origin=Origin(xyz=(0.0, 0.120, 0.030)),
    )
    exhaust_baffle.visual(
        Box((0.480, 0.240, 0.016)),
        origin=Origin(xyz=(0.0, 0.138, -0.012)),
        material=cabinet_paint,
        name="baffle_panel",
    )
    exhaust_baffle.visual(
        Box((0.016, 0.240, 0.060)),
        origin=Origin(xyz=(-0.232, 0.138, 0.006)),
        material=cabinet_paint,
        name="left_flange",
    )
    exhaust_baffle.visual(
        Box((0.016, 0.240, 0.060)),
        origin=Origin(xyz=(0.232, 0.138, 0.006)),
        material=cabinet_paint,
        name="right_flange",
    )
    exhaust_baffle.visual(
        Box((0.440, 0.016, 0.050)),
        origin=Origin(xyz=(0.0, 0.250, 0.003)),
        material=cabinet_paint,
        name="front_lip",
    )
    exhaust_baffle.visual(
        Box((0.180, 0.012, 0.024)),
        origin=Origin(xyz=(0.0, 0.256, 0.028)),
        material=hinge_steel,
        name="lift_tab",
    )
    exhaust_baffle.visual(
        Cylinder(radius=0.010, length=0.100),
        origin=Origin(xyz=(-0.160, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=hinge_steel,
        name="left_baffle_knuckle",
    )
    exhaust_baffle.visual(
        Box((0.100, 0.012, 0.020)),
        origin=Origin(xyz=(-0.160, 0.016, 0.0)),
        material=hinge_steel,
        name="left_baffle_leaf",
    )
    exhaust_baffle.visual(
        Cylinder(radius=0.010, length=0.100),
        origin=Origin(xyz=(0.160, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=hinge_steel,
        name="right_baffle_knuckle",
    )
    exhaust_baffle.visual(
        Box((0.100, 0.012, 0.020)),
        origin=Origin(xyz=(0.160, 0.016, 0.0)),
        material=hinge_steel,
        name="right_baffle_leaf",
    )

    caster_positions = {
        "front_left_caster": (-0.230, 0.180, BODY_BOTTOM_Z),
        "front_right_caster": (0.230, 0.180, BODY_BOTTOM_Z),
        "rear_left_caster": (-0.230, -0.180, BODY_BOTTOM_Z),
        "rear_right_caster": (0.230, -0.180, BODY_BOTTOM_Z),
    }
    for caster_name in caster_positions:
        caster = model.part(caster_name)
        caster.inertial = Inertial.from_geometry(
            Box((0.10, 0.08, 0.12)),
            mass=2.2,
            origin=Origin(xyz=(0.0, 0.0, -0.060)),
        )
        _add_caster(caster, steel=steel, dark_steel=trim_dark, rubber=rubber)

    model.articulation(
        "access_door_hinge",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=access_door,
        origin=Origin(xyz=(-0.375, 0.294, 0.770)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=45.0, velocity=1.6, lower=0.0, upper=1.55),
    )
    model.articulation(
        "exhaust_baffle_hinge",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=exhaust_baffle,
        origin=Origin(xyz=(0.0, -0.255, BODY_TOP_Z + 0.024)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.4, lower=0.0, upper=1.10),
    )
    for caster_name, xyz in caster_positions.items():
        model.articulation(
            f"{caster_name}_mount",
            ArticulationType.FIXED,
            parent=cabinet,
            child=caster_name,
            origin=Origin(xyz=xyz),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
