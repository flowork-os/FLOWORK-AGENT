# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_sunroof_cassette, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_sunroof_cassette

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
ROOF_WIDTH = 1.20
ROOF_LENGTH = 2.00
ROOF_THICKNESS = 0.008
ROOF_CORNER_RADIUS = 0.16
OPENING_CENTER_Y = 0.32
ROOF_HOLE_WIDTH = 0.846
ROOF_HOLE_LENGTH = 0.860
ROOF_HOLE_CORNER_RADIUS = 0.060
FRAME_OUTER_WIDTH = 0.870
FRAME_OUTER_LENGTH = 0.884
FRAME_INNER_WIDTH = 0.804
FRAME_INNER_LENGTH = 0.818
FRAME_CORNER_RADIUS = 0.060
FRAME_THICKNESS = 0.0022
GASKET_THICKNESS = 0.0012
GLASS_WIDTH = 0.796
GLASS_LENGTH = 0.810
GLASS_THICKNESS = 0.005
GLASS_CORNER_RADIUS = 0.055
GLASS_CLOSED_BOTTOM_Z = ROOF_THICKNESS - GLASS_THICKNESS
RAIL_CENTER_X = 0.462
RAIL_CENTER_Y = -0.10
RAIL_LENGTH = 1.60
RAIL_OUTER_WIDTH = 0.050
RAIL_WALL_THICKNESS = 0.007
RAIL_HEIGHT = 0.046
SHOE_X_OFFSET = RAIL_CENTER_X
SHOE_FRONT_Y_OFFSET = 0.315
SHOE_REAR_Y_OFFSET = -0.315
SHOE_JOINT_Z = -0.015
SLIDER_SIZE = (0.028, 0.070, 0.012)
GLASS_RETRACT_DISTANCE = 0.835
GLASS_DROP_DISTANCE = 0.022
GLASS_SLIDE_STROKE = math.sqrt(GLASS_RETRACT_DISTANCE**2 + GLASS_DROP_DISTANCE**2)
GLASS_SLIDE_AXIS = (
    0.0,
    -GLASS_RETRACT_DISTANCE / GLASS_SLIDE_STROKE,
    -GLASS_DROP_DISTANCE / GLASS_SLIDE_STROKE,
)
def _mesh(name: str, geometry):
    return mesh_from_geometry(geometry, name)
def _shift_profile(
    profile: list[tuple[float, float]], *, dx: float = 0.0, dy: float = 0.0
) -> list[tuple[float, float]]:
    return [(x + dx, y + dy) for x, y in profile]
def _rounded_panel_mesh(
    name: str,
    *,
    width: float,
    length: float,
    thickness: float,
    radius: float,
):
    return _mesh(
        name,
        ExtrudeGeometry.from_z0(
            rounded_rect_profile(width, length, radius, corner_segments=10),
            thickness,
        ),
    )
def _rounded_ring_mesh(
    name: str,
    *,
    outer_width: float,
    outer_length: float,
    inner_width: float,
    inner_length: float,
    thickness: float,
    radius: float,
    center_y: float = 0.0,
):
    outer_profile = _shift_profile(
        rounded_rect_profile(outer_width, outer_length, radius, corner_segments=10),
        dy=center_y,
    )
    inner_profile = _shift_profile(
        rounded_rect_profile(
            inner_width,
            inner_length,
            max(0.001, radius - 0.004),
            corner_segments=10,
        ),
        dy=center_y,
    )
    return _mesh(
        name,
        ExtrudeWithHolesGeometry(
            outer_profile,
            [inner_profile],
            height=thickness,
            center=True,
        ),
    )
def _build_rail_part(model: ArticulatedObject, *, name: str, side_sign: float, rail_material, liner_material):
    rail = model.part(name)
    outer_wall_center_x = side_sign * (RAIL_OUTER_WIDTH * 0.5 - RAIL_WALL_THICKNESS * 0.5)
    inner_wall_center_x = -side_sign * (RAIL_OUTER_WIDTH * 0.5 - RAIL_WALL_THICKNESS * 0.5)
    guide_cheek_center_z = -0.012
    guide_cheek_height = 0.012
    guide_cheek_width = 0.005
    guide_cheek_center_x = 0.0185

    rail.visual(
        Box((RAIL_WALL_THICKNESS, RAIL_LENGTH, 0.042)),
        origin=Origin(xyz=(outer_wall_center_x, 0.0, -0.021)),
        material=rail_material,
        name="outer_wall",
    )
    rail.visual(
        Box((RAIL_WALL_THICKNESS, RAIL_LENGTH, 0.034)),
        origin=Origin(xyz=(inner_wall_center_x, 0.0, -0.025)),
        material=rail_material,
        name="inner_wall",
    )
    rail.visual(
        Box((0.032, RAIL_LENGTH, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, -0.021)),
        material=liner_material,
        name="runner_deck",
    )
    rail.visual(
        Box((guide_cheek_width, RAIL_LENGTH, guide_cheek_height)),
        origin=Origin(
            xyz=(
                guide_cheek_center_x,
                0.0,
                guide_cheek_center_z,
            )
        ),
        material=liner_material,
        name="outer_guide",
    )
    rail.visual(
        Box((guide_cheek_width, RAIL_LENGTH, guide_cheek_height)),
        origin=Origin(
            xyz=(
                -guide_cheek_center_x,
                0.0,
                guide_cheek_center_z,
            )
        ),
        material=liner_material,
        name="inner_guide",
    )
    rail.inertial = Inertial.from_geometry(
        Box((RAIL_OUTER_WIDTH + 0.020, RAIL_LENGTH, RAIL_HEIGHT)),
        mass=2.2,
        origin=Origin(xyz=(0.0, 0.0, -0.023)),
    )
    return rail
def _build_shoe_part(model: ArticulatedObject, *, name: str, side_sign: float, shoe_material, bracket_material):
    shoe = model.part(name)
    shoe.visual(
        Box(SLIDER_SIZE),
        origin=Origin(),
        material=shoe_material,
        name="slider_block",
    )
    shoe.visual(
        Box((0.012, 0.024, 0.016)),
        origin=Origin(
            xyz=(
                -side_sign * 0.006,
                0.0,
                0.002,
            )
        ),
        material=bracket_material,
        name="riser",
    )
    shoe.visual(
        Box((0.060, 0.026, 0.004)),
        origin=Origin(
            xyz=(
                -side_sign * 0.034,
                0.0,
                0.002,
            )
        ),
        material=bracket_material,
        name="yoke_arm",
    )
    shoe.visual(
        Box((0.010, 0.022, 0.008)),
        origin=Origin(
            xyz=(
                -side_sign * 0.062,
                0.0,
                0.007,
            )
        ),
        material=bracket_material,
        name="inner_riser",
    )
    shoe.visual(
        Box((0.032, 0.032, 0.004)),
        origin=Origin(
            xyz=(
                -side_sign * 0.068,
                0.0,
                0.013,
            )
        ),
        material=bracket_material,
        name="glass_pad",
    )
    shoe.inertial = Inertial.from_geometry(
        Box((0.110, 0.080, 0.030)),
        mass=0.32,
        origin=Origin(xyz=(-side_sign * 0.038, 0.0, 0.006)),
    )
    return shoe
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="frameless_glass_sunroof_cassette")

    body_paint = model.material("body_paint", rgba=(0.63, 0.65, 0.69, 1.0))
    cassette_black = model.material("cassette_black", rgba=(0.10, 0.10, 0.11, 1.0))
    rail_aluminium = model.material("rail_aluminium", rgba=(0.69, 0.71, 0.73, 1.0))
    brushed_aluminium = model.material("brushed_aluminium", rgba=(0.76, 0.78, 0.80, 1.0))
    shoe_polymer = model.material("shoe_polymer", rgba=(0.12, 0.12, 0.13, 1.0))
    bracket_steel = model.material("bracket_steel", rgba=(0.43, 0.45, 0.47, 1.0))
    glass_tint = model.material("glass_tint", rgba=(0.18, 0.27, 0.31, 0.42))
    glass_frit = model.material("glass_frit", rgba=(0.05, 0.05, 0.06, 1.0))
    seal_rubber = model.material("seal_rubber", rgba=(0.04, 0.04, 0.05, 1.0))

    cassette_body = model.part("cassette_body")
    cassette_body.visual(
        _mesh(
            "sunroof_roof_skin",
            ExtrudeWithHolesGeometry(
                rounded_rect_profile(
                    ROOF_WIDTH,
                    ROOF_LENGTH,
                    ROOF_CORNER_RADIUS,
                    corner_segments=12,
                ),
                [
                    _shift_profile(
                        rounded_rect_profile(
                            ROOF_HOLE_WIDTH,
                            ROOF_HOLE_LENGTH,
                            ROOF_HOLE_CORNER_RADIUS,
                            corner_segments=10,
                        ),
                        dy=OPENING_CENTER_Y,
                    )
                ],
                height=ROOF_THICKNESS,
                center=True,
            ),
        ),
        origin=Origin(xyz=(0.0, 0.0, ROOF_THICKNESS * 0.5)),
        material=body_paint,
        name="roof_skin",
    )
    cassette_body.visual(
        Box((0.090, 1.66, 0.040)),
        origin=Origin(xyz=(0.532, -0.12, -0.016)),
        material=cassette_black,
        name="left_trough",
    )
    cassette_body.visual(
        Box((0.090, 1.66, 0.040)),
        origin=Origin(xyz=(-0.532, -0.12, -0.016)),
        material=cassette_black,
        name="right_trough",
    )
    cassette_body.visual(
        Box((0.900, 0.090, 0.030)),
        origin=Origin(xyz=(0.0, 0.795, -0.011)),
        material=cassette_black,
        name="front_header",
    )
    cassette_body.visual(
        Box((0.300, 0.760, 0.040)),
        origin=Origin(xyz=(0.0, -0.57, -0.028)),
        material=cassette_black,
        name="rear_cartridge",
    )
    cassette_body.visual(
        Box((0.240, 0.080, 0.020)),
        origin=Origin(xyz=(0.0, -0.95, -0.012)),
        material=cassette_black,
        name="rear_crossmember",
    )
    cassette_body.inertial = Inertial.from_geometry(
        Box((ROOF_WIDTH, ROOF_LENGTH, 0.080)),
        mass=24.0,
        origin=Origin(xyz=(0.0, 0.0, -0.020)),
    )

    seal_frame = model.part("seal_frame")
    seal_frame.visual(
        _rounded_ring_mesh(
            "sunroof_frame_ring",
            outer_width=FRAME_OUTER_WIDTH,
            outer_length=FRAME_OUTER_LENGTH,
            inner_width=FRAME_INNER_WIDTH,
            inner_length=FRAME_INNER_LENGTH,
            thickness=FRAME_THICKNESS,
            radius=FRAME_CORNER_RADIUS,
            center_y=OPENING_CENTER_Y,
        ),
        origin=Origin(xyz=(0.0, 0.0, ROOF_THICKNESS + FRAME_THICKNESS * 0.5)),
        material=brushed_aluminium,
        name="frame_ring",
    )
    seal_frame.visual(
        _rounded_ring_mesh(
            "sunroof_gasket_ring",
            outer_width=FRAME_INNER_WIDTH + 0.010,
            outer_length=FRAME_INNER_LENGTH + 0.010,
            inner_width=FRAME_INNER_WIDTH - 0.006,
            inner_length=FRAME_INNER_LENGTH - 0.006,
            thickness=GASKET_THICKNESS,
            radius=FRAME_CORNER_RADIUS - 0.004,
            center_y=OPENING_CENTER_Y,
        ),
        origin=Origin(xyz=(0.0, 0.0, ROOF_THICKNESS + GASKET_THICKNESS * 0.5)),
        material=seal_rubber,
        name="gasket_ring",
    )
    seal_frame.inertial = Inertial.from_geometry(
        Box((FRAME_OUTER_WIDTH, FRAME_OUTER_LENGTH, FRAME_THICKNESS + GASKET_THICKNESS)),
        mass=1.3,
        origin=Origin(xyz=(0.0, OPENING_CENTER_Y, ROOF_THICKNESS + 0.0016)),
    )

    left_rail = _build_rail_part(
        model,
        name="left_rail",
        side_sign=1.0,
        rail_material=rail_aluminium,
        liner_material=cassette_black,
    )
    right_rail = _build_rail_part(
        model,
        name="right_rail",
        side_sign=-1.0,
        rail_material=rail_aluminium,
        liner_material=cassette_black,
    )

    glass_panel = model.part("glass_panel")
    glass_panel.visual(
        _rounded_panel_mesh(
            "sunroof_glass_panel",
            width=GLASS_WIDTH,
            length=GLASS_LENGTH,
            thickness=GLASS_THICKNESS,
            radius=GLASS_CORNER_RADIUS,
        ),
        material=glass_tint,
        name="glass_lite",
    )
    glass_panel.visual(
        _rounded_ring_mesh(
            "sunroof_glass_frit",
            outer_width=GLASS_WIDTH,
            outer_length=GLASS_LENGTH,
            inner_width=GLASS_WIDTH - 0.050,
            inner_length=GLASS_LENGTH - 0.050,
            thickness=0.0008,
            radius=GLASS_CORNER_RADIUS,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.0004)),
        material=glass_frit,
        name="glass_frit",
    )
    glass_panel.inertial = Inertial.from_geometry(
        Box((GLASS_WIDTH, GLASS_LENGTH, GLASS_THICKNESS)),
        mass=11.0,
        origin=Origin(xyz=(0.0, 0.0, GLASS_THICKNESS * 0.5)),
    )

    front_left_shoe = _build_shoe_part(
        model,
        name="front_left_shoe",
        side_sign=1.0,
        shoe_material=shoe_polymer,
        bracket_material=bracket_steel,
    )
    front_right_shoe = _build_shoe_part(
        model,
        name="front_right_shoe",
        side_sign=-1.0,
        shoe_material=shoe_polymer,
        bracket_material=bracket_steel,
    )
    rear_left_shoe = _build_shoe_part(
        model,
        name="rear_left_shoe",
        side_sign=1.0,
        shoe_material=shoe_polymer,
        bracket_material=bracket_steel,
    )
    rear_right_shoe = _build_shoe_part(
        model,
        name="rear_right_shoe",
        side_sign=-1.0,
        shoe_material=shoe_polymer,
        bracket_material=bracket_steel,
    )

    model.articulation(
        "cassette_to_seal_frame",
        ArticulationType.FIXED,
        parent=cassette_body,
        child=seal_frame,
        origin=Origin(),
    )
    model.articulation(
        "cassette_to_left_rail",
        ArticulationType.FIXED,
        parent=cassette_body,
        child=left_rail,
        origin=Origin(xyz=(RAIL_CENTER_X, RAIL_CENTER_Y, 0.0)),
    )
    model.articulation(
        "cassette_to_right_rail",
        ArticulationType.FIXED,
        parent=cassette_body,
        child=right_rail,
        origin=Origin(xyz=(-RAIL_CENTER_X, RAIL_CENTER_Y, 0.0)),
    )
    model.articulation(
        "glass_slide",
        ArticulationType.PRISMATIC,
        parent=cassette_body,
        child=glass_panel,
        origin=Origin(xyz=(0.0, OPENING_CENTER_Y, GLASS_CLOSED_BOTTOM_Z)),
        axis=GLASS_SLIDE_AXIS,
        motion_limits=MotionLimits(
            effort=180.0,
            velocity=0.35,
            lower=0.0,
            upper=GLASS_SLIDE_STROKE,
        ),
    )
    model.articulation(
        "glass_to_front_left_shoe",
        ArticulationType.FIXED,
        parent=glass_panel,
        child=front_left_shoe,
        origin=Origin(xyz=(SHOE_X_OFFSET, SHOE_FRONT_Y_OFFSET, SHOE_JOINT_Z)),
    )
    model.articulation(
        "glass_to_front_right_shoe",
        ArticulationType.FIXED,
        parent=glass_panel,
        child=front_right_shoe,
        origin=Origin(xyz=(-SHOE_X_OFFSET, SHOE_FRONT_Y_OFFSET, SHOE_JOINT_Z)),
    )
    model.articulation(
        "glass_to_rear_left_shoe",
        ArticulationType.FIXED,
        parent=glass_panel,
        child=rear_left_shoe,
        origin=Origin(xyz=(SHOE_X_OFFSET, SHOE_REAR_Y_OFFSET, SHOE_JOINT_Z)),
    )
    model.articulation(
        "glass_to_rear_right_shoe",
        ArticulationType.FIXED,
        parent=glass_panel,
        child=rear_right_shoe,
        origin=Origin(xyz=(-SHOE_X_OFFSET, SHOE_REAR_Y_OFFSET, SHOE_JOINT_Z)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
