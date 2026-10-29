# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

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

# ===== model =====
import math
def _rolled_point(
    x: float,
    center_y: float,
    center_z: float,
    local_y: float,
    local_z: float,
    roll: float,
) -> tuple[float, float, float]:
    return (
        x,
        center_y + (local_y * math.cos(roll)) - (local_z * math.sin(roll)),
        center_z + (local_y * math.sin(roll)) + (local_z * math.cos(roll)),
    )
def _circle_profile(
    radius: float,
    *,
    center: tuple[float, float] = (0.0, 0.0),
    segments: int = 32,
) -> list[tuple[float, float]]:
    cx, cy = center
    return [
        (
            cx + (radius * math.cos((2.0 * math.pi * index) / segments)),
            cy + (radius * math.sin((2.0 * math.pi * index) / segments)),
        )
        for index in range(segments)
    ]
def _control_deck_mesh() -> object:
    deck = ExtrudeWithHolesGeometry(
        [
            (-0.39, -0.17),
            (0.39, -0.17),
            (0.39, 0.17),
            (-0.39, 0.17),
        ],
        [
            _circle_profile(0.0225, center=(-0.070, 0.022)),
            _circle_profile(0.0225, center=(0.070, 0.022)),
        ],
        0.026,
        cap=True,
        center=True,
        closed=True,
    )
    return mesh_from_geometry(deck, "control_deck_shell")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="two_player_arcade_machine")

    cabinet_black = model.material("cabinet_black", rgba=(0.11, 0.11, 0.13, 1.0))
    cabinet_trim = model.material("cabinet_trim", rgba=(0.18, 0.18, 0.20, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.08, 0.12, 0.14, 0.55))
    marquee_glow = model.material("marquee_glow", rgba=(0.88, 0.92, 0.98, 0.82))
    slot_black = model.material("slot_black", rgba=(0.03, 0.03, 0.04, 1.0))
    coin_metal = model.material("coin_metal", rgba=(0.58, 0.60, 0.62, 1.0))
    hatch_metal = model.material("hatch_metal", rgba=(0.28, 0.29, 0.31, 1.0))
    sleeve_black = model.material("sleeve_black", rgba=(0.07, 0.07, 0.08, 1.0))
    joystick_red = model.material("joystick_red", rgba=(0.70, 0.14, 0.13, 1.0))
    action_orange = model.material("action_orange", rgba=(0.91, 0.39, 0.12, 1.0))
    action_yellow = model.material("action_yellow", rgba=(0.96, 0.72, 0.12, 1.0))
    action_green = model.material("action_green", rgba=(0.18, 0.74, 0.30, 1.0))
    button_blue = model.material("button_blue", rgba=(0.40, 0.77, 1.0, 0.88))
    button_red = model.material("button_red", rgba=(1.0, 0.34, 0.30, 0.88))

    deck_center_y = -0.118
    deck_center_z = 0.944
    deck_roll = 0.26
    deck_thickness = 0.026
    deck_top_local_z = deck_thickness * 0.5
    screen_center_y = -0.142
    screen_center_z = 1.285
    screen_roll = -0.17
    joystick_specs: list[tuple[str, tuple[float, float, float]]] = []
    action_button_specs: list[tuple[str, tuple[float, float, float], object, str]] = []

    cabinet = model.part("cabinet")
    cabinet.visual(
        Box((0.82, 0.78, 0.92)),
        origin=Origin(xyz=(0.0, 0.04, 0.46)),
        material=cabinet_black,
        name="lower_shell",
    )
    cabinet.visual(
        Box((0.82, 0.48, 0.72)),
        origin=Origin(xyz=(0.0, 0.17, 1.26)),
        material=cabinet_black,
        name="rear_tower",
    )
    cabinet.visual(
        Box((0.82, 0.20, 0.12)),
        origin=Origin(xyz=(0.0, -0.095, 1.68)),
        material=cabinet_black,
        name="marquee_top",
    )
    cabinet.visual(
        Box((0.70, 0.012, 0.082)),
        origin=Origin(xyz=(0.0, -0.195, 1.68)),
        material=marquee_glow,
        name="marquee_face",
    )
    cabinet.visual(
        _control_deck_mesh(),
        origin=Origin(xyz=(0.0, deck_center_y, deck_center_z), rpy=(deck_roll, 0.0, 0.0)),
        material=cabinet_trim,
        name="control_deck",
    )
    cabinet.visual(
        Box((0.78, 0.06, 0.11)),
        origin=Origin(xyz=(0.0, -0.205, 0.875), rpy=(deck_roll, 0.0, 0.0)),
        material=cabinet_black,
        name="deck_skirt",
    )
    cabinet.visual(
        Box((0.060, 0.045, 0.490)),
        origin=Origin(
            xyz=_rolled_point(-0.293, screen_center_y, screen_center_z, 0.0, 0.0, screen_roll),
            rpy=(screen_roll, 0.0, 0.0),
        ),
        material=slot_black,
        name="monitor_left_bezel",
    )
    cabinet.visual(
        Box((0.060, 0.045, 0.490)),
        origin=Origin(
            xyz=_rolled_point(0.293, screen_center_y, screen_center_z, 0.0, 0.0, screen_roll),
            rpy=(screen_roll, 0.0, 0.0),
        ),
        material=slot_black,
        name="monitor_right_bezel",
    )
    cabinet.visual(
        Box((0.646, 0.045, 0.058)),
        origin=Origin(
            xyz=_rolled_point(0.0, screen_center_y, screen_center_z, 0.0, 0.218, screen_roll),
            rpy=(screen_roll, 0.0, 0.0),
        ),
        material=slot_black,
        name="monitor_top_bezel",
    )
    cabinet.visual(
        Box((0.646, 0.045, 0.058)),
        origin=Origin(
            xyz=_rolled_point(0.0, screen_center_y, screen_center_z, 0.0, -0.218, screen_roll),
            rpy=(screen_roll, 0.0, 0.0),
        ),
        material=slot_black,
        name="monitor_bottom_bezel",
    )
    cabinet.visual(
        Box((0.520, 0.016, 0.366)),
        origin=Origin(
            xyz=_rolled_point(0.0, screen_center_y, screen_center_z, 0.030, 0.0, screen_roll),
            rpy=(screen_roll, 0.0, 0.0),
        ),
        material=screen_glass,
        name="monitor_screen",
    )
    cabinet.visual(
        Box((0.690, 0.180, 0.540)),
        origin=Origin(xyz=(0.0, -0.030, 1.285)),
        material=cabinet_trim,
        name="monitor_backer",
    )
    cabinet.visual(
        Box((0.42, 0.018, 0.16)),
        origin=Origin(xyz=(0.0, -0.359, 0.585)),
        material=cabinet_trim,
        name="coin_panel",
    )
    cabinet.visual(
        Box((0.112, 0.008, 0.018)),
        origin=Origin(xyz=(-0.120, -0.372, 0.614)),
        material=slot_black,
        name="left_coin_slot",
    )
    cabinet.visual(
        Box((0.112, 0.008, 0.018)),
        origin=Origin(xyz=(0.120, -0.372, 0.614)),
        material=slot_black,
        name="right_coin_slot",
    )
    cabinet.visual(
        Box((0.030, 0.010, 0.030)),
        origin=Origin(xyz=(-0.120, -0.371, 0.552)),
        material=coin_metal,
        name="left_coin_return",
    )
    cabinet.visual(
        Box((0.030, 0.010, 0.030)),
        origin=Origin(xyz=(0.120, -0.371, 0.552)),
        material=coin_metal,
        name="right_coin_return",
    )
    cabinet.visual(
        Box((0.48, 0.012, 0.022)),
        origin=Origin(xyz=(0.0, -0.356, 0.401)),
        material=coin_metal,
        name="service_frame_top",
    )
    cabinet.visual(
        Box((0.020, 0.012, 0.262)),
        origin=Origin(xyz=(-0.240, -0.356, 0.265)),
        material=coin_metal,
        name="service_frame_left",
    )
    cabinet.visual(
        Box((0.020, 0.012, 0.262)),
        origin=Origin(xyz=(0.240, -0.356, 0.265)),
        material=coin_metal,
        name="service_frame_right",
    )

    for side_index, x_sign in enumerate((-1.0, 1.0)):
        joy_x = 0.230 * x_sign
        joy_joint_xyz = _rolled_point(
            joy_x,
            deck_center_y,
            deck_center_z,
            -0.030,
            deck_top_local_z,
            deck_roll,
        )
        joy_collar_xyz = _rolled_point(
            joy_x,
            deck_center_y,
            deck_center_z,
            -0.030,
            deck_top_local_z + 0.003,
            deck_roll,
        )
        cabinet.visual(
            Cylinder(radius=0.018, length=0.006),
            origin=Origin(xyz=joy_collar_xyz, rpy=(deck_roll, 0.0, 0.0)),
            material=slot_black,
            name=f"joystick_collar_{side_index}",
        )
        joystick_specs.append((f"player_{side_index}_joystick", joy_joint_xyz))
        action_materials = (action_orange, action_yellow, action_green)
        action_offsets_x = (0.135 * x_sign, 0.180 * x_sign, 0.225 * x_sign)
        action_offsets_y = (0.018, 0.043, 0.008)
        for button_index, (button_x, button_y, button_material) in enumerate(
            zip(action_offsets_x, action_offsets_y, action_materials, strict=True)
        ):
            action_joint_xyz = _rolled_point(
                button_x,
                deck_center_y,
                deck_center_z,
                button_y,
                deck_top_local_z,
                deck_roll,
            )
            action_guide_xyz = _rolled_point(
                button_x,
                deck_center_y,
                deck_center_z,
                button_y,
                deck_top_local_z + 0.002,
                deck_roll,
            )
            cabinet.visual(
                Cylinder(radius=0.020, length=0.004),
                origin=Origin(xyz=action_guide_xyz, rpy=(deck_roll, 0.0, 0.0)),
                material=sleeve_black,
                name=f"action_button_guide_{side_index}_{button_index}",
            )
            action_button_specs.append(
                (
                    f"action_button_{side_index}_{button_index}",
                    action_joint_xyz,
                    button_material,
                    f"action_button_guide_{side_index}_{button_index}",
                )
            )

    left_button_joint_xyz = _rolled_point(
        -0.070,
        deck_center_y,
        deck_center_z,
        0.022,
        deck_top_local_z,
        deck_roll,
    )
    right_button_joint_xyz = _rolled_point(
        0.070,
        deck_center_y,
        deck_center_z,
        0.022,
        deck_top_local_z,
        deck_roll,
    )
    left_sleeve_xyz = _rolled_point(
        -0.070,
        deck_center_y,
        deck_center_z,
        0.022,
        deck_top_local_z - 0.020,
        deck_roll,
    )
    right_sleeve_xyz = _rolled_point(
        0.070,
        deck_center_y,
        deck_center_z,
        0.022,
        deck_top_local_z - 0.020,
        deck_roll,
    )
    cabinet.visual(
        Box((0.056, 0.056, 0.028)),
        origin=Origin(xyz=left_sleeve_xyz, rpy=(deck_roll, 0.0, 0.0)),
        material=sleeve_black,
        name="left_button_sleeve",
    )
    cabinet.visual(
        Box((0.056, 0.056, 0.028)),
        origin=Origin(xyz=right_sleeve_xyz, rpy=(deck_roll, 0.0, 0.0)),
        material=sleeve_black,
        name="right_button_sleeve",
    )
    cabinet.inertial = Inertial.from_geometry(
        Box((0.82, 0.78, 1.82)),
        mass=88.0,
        origin=Origin(xyz=(0.0, 0.03, 0.91)),
    )

    service_hatch = model.part("service_hatch")
    service_hatch.visual(
        Box((0.46, 0.018, 0.25)),
        origin=Origin(xyz=(0.0, 0.009, 0.125)),
        material=hatch_metal,
        name="hatch_panel",
    )
    service_hatch.visual(
        Box((0.16, 0.008, 0.032)),
        origin=Origin(xyz=(0.0, -0.004, 0.205)),
        material=coin_metal,
        name="hatch_pull",
    )
    service_hatch.inertial = Inertial.from_geometry(
        Box((0.46, 0.018, 0.25)),
        mass=4.2,
        origin=Origin(xyz=(0.0, 0.009, 0.125)),
    )

    for part_name, origin_xyz in joystick_specs:
        joystick = model.part(part_name)
        joystick.visual(
            Cylinder(radius=0.010, length=0.050),
            origin=Origin(xyz=(0.0, 0.0, 0.031)),
            material=slot_black,
            name="joystick_shaft",
        )
        joystick.visual(
            Cylinder(radius=0.024, length=0.018),
            origin=Origin(xyz=(0.0, 0.0, 0.066)),
            material=joystick_red,
            name="joystick_ball",
        )
        joystick.inertial = Inertial.from_geometry(
            Box((0.050, 0.050, 0.090)),
            mass=0.10,
            origin=Origin(xyz=(0.0, 0.0, 0.045)),
        )
        model.articulation(
            f"cabinet_to_{part_name}",
            ArticulationType.REVOLUTE,
            parent=cabinet,
            child=joystick,
            origin=Origin(xyz=origin_xyz, rpy=(deck_roll, 0.0, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(
                effort=0.8,
                velocity=2.5,
                lower=-0.35,
                upper=0.35,
            ),
        )

    for part_name, origin_xyz, button_material, _guide_name in action_button_specs:
        action_button = model.part(part_name)
        action_button.visual(
            Cylinder(radius=0.018, length=0.010),
            origin=Origin(xyz=(0.0, 0.0, 0.007)),
            material=button_material,
            name="button_cap",
        )
        action_button.inertial = Inertial.from_geometry(
            Cylinder(radius=0.018, length=0.010),
            mass=0.04,
            origin=Origin(xyz=(0.0, 0.0, 0.007)),
        )
        model.articulation(
            f"cabinet_to_{part_name}",
            ArticulationType.PRISMATIC,
            parent=cabinet,
            child=action_button,
            origin=Origin(xyz=origin_xyz, rpy=(deck_roll, 0.0, 0.0)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=0.8,
                velocity=0.12,
                lower=0.0,
                upper=0.003,
            ),
        )

    left_start_button = model.part("left_start_button")
    left_start_button.visual(
        Cylinder(radius=0.019, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=slot_black,
        name="button_plunger",
    )
    left_start_button.visual(
        Cylinder(radius=0.036, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=button_blue,
        name="button_cap",
    )
    left_start_button.inertial = Inertial.from_geometry(
        Cylinder(radius=0.036, length=0.034),
        mass=0.10,
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
    )

    right_start_button = model.part("right_start_button")
    right_start_button.visual(
        Cylinder(radius=0.019, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=slot_black,
        name="button_plunger",
    )
    right_start_button.visual(
        Cylinder(radius=0.036, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=button_red,
        name="button_cap",
    )
    right_start_button.inertial = Inertial.from_geometry(
        Cylinder(radius=0.036, length=0.034),
        mass=0.10,
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
    )

    model.articulation(
        "cabinet_to_service_hatch",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=service_hatch,
        origin=Origin(xyz=(0.0, -0.368, 0.140)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.2,
            lower=0.0,
            upper=1.28,
        ),
    )
    model.articulation(
        "cabinet_to_left_start_button",
        ArticulationType.PRISMATIC,
        parent=cabinet,
        child=left_start_button,
        origin=Origin(xyz=left_button_joint_xyz, rpy=(deck_roll, 0.0, 0.0)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=0.08,
            lower=0.0,
            upper=0.004,
        ),
    )
    model.articulation(
        "cabinet_to_right_start_button",
        ArticulationType.PRISMATIC,
        parent=cabinet,
        child=right_start_button,
        origin=Origin(xyz=right_button_joint_xyz, rpy=(deck_roll, 0.0, 0.0)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=0.08,
            lower=0.0,
            upper=0.004,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
