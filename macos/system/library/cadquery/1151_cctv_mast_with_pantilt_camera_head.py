# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cctv_mast_with_pantilt_camera_head, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cctv_mast_with_pantilt_camera_head

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

# ===== primitives (3 syms) =====
def _coerce_positive_radii3(value, *, name):
    """Verbatim port of the sdk helper: accept a positive scalar or a positive
    3-sequence and return an (rx, ry, rz) tuple."""
    if isinstance(value, (int, float)):
        radius = float(value)
        if radius <= 0.0:
            raise ValidationError("%s must be positive" % name)
        return (radius, radius, radius)
    if len(value) != 3:
        raise ValidationError("%s must be a positive float or a 3-sequence" % name)
    rx = float(value[0])
    ry = float(value[1])
    rz = float(value[2])
    if rx <= 0.0 or ry <= 0.0 or rz <= 0.0:
        raise ValidationError("%s values must be positive" % name)
    return (rx, ry, rz)

class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

class DomeGeometry(MeshGeometry):
    def __init__(self, radius, *, radial_segments=24, height_segments=12, closed=True):
        super().__init__()
        rx, ry, rz = _coerce_positive_radii3(radius, name="radius")
        # upper hemisphere (z>=0) of a unit sphere, scaled to the half-ellipsoid
        hemi = cq.Solid.makeSphere(
            1.0, angleDegrees1=0, angleDegrees2=90, angleDegrees3=360
        )
        m = cq.Matrix([[rx, 0, 0, 0], [0, ry, 0, 0], [0, 0, rz, 0]])
        solid = hemi.transformGeometry(m)
        self._set(solid)

# ===== model =====
import math
PAN_X = 0.54
ARM_Z = 0.45
PAN_Z = 0.405
TILT_Z = -0.125
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="corner_mount_cctv_arm")

    galvanized = model.material("galvanized_steel", rgba=(0.63, 0.66, 0.64, 1.0))
    dark_galv = model.material("dark_galvanized_edges", rgba=(0.37, 0.39, 0.38, 1.0))
    screw_black = model.material("blackened_screws", rgba=(0.06, 0.065, 0.07, 1.0))
    camera_white = model.material("powder_coated_white", rgba=(0.92, 0.93, 0.90, 1.0))
    camera_black = model.material("smoked_black_dome", rgba=(0.015, 0.020, 0.025, 0.70))

    mount = model.part("mount_arm")

    # A broad tapered sheet is the distinctive diagonal galvanized corner plate:
    # its base is high on the corner, while the top and bottom edges slope into
    # a short flat tip where the arm tube is welded.
    diagonal_profile = [
        (-0.025, -0.170),
        (-0.025, 0.170),
        (0.230, 0.030),
        (0.230, -0.030),
    ]
    diagonal_plate = ExtrudeGeometry(diagonal_profile, 0.012, center=True).rotate_x(math.pi / 2)
    diagonal_plate.translate(0.0, 0.0, ARM_Z)
    mount.visual(
        mesh_from_geometry(diagonal_plate, "diagonal_plate"),
        material=galvanized,
        name="diagonal_plate",
    )

    # The two short leaves behind the diagonal sheet suggest a real corner
    # bracket bolted to perpendicular walls.
    for index, (yaw, y) in enumerate(((math.radians(42.0), 0.052), (-math.radians(42.0), -0.052))):
        mount.visual(
            Box((0.012, 0.105, 0.380)),
            origin=Origin(xyz=(-0.028, y, ARM_Z), rpy=(0.0, 0.0, yaw)),
            material=galvanized,
            name=f"corner_leaf_{index}",
        )
    mount.visual(
        Box((0.030, 0.120, 0.380)),
        origin=Origin(xyz=(-0.032, 0.0, ARM_Z)),
        material=dark_galv,
        name="corner_spine",
    )

    # Bolt heads are seated into the diagonal plate rather than floating on it.
    bolt_points = [
        (0.020, 0.0, ARM_Z - 0.105),
        (0.020, 0.0, ARM_Z + 0.105),
        (0.130, 0.0, ARM_Z - 0.045),
        (0.130, 0.0, ARM_Z + 0.045),
    ]
    for index, xyz in enumerate(bolt_points):
        mount.visual(
            Cylinder(radius=0.011, length=0.006),
            origin=Origin(xyz=(xyz[0], -0.0085, xyz[2]), rpy=(-math.pi / 2, 0.0, 0.0)),
            material=screw_black,
            name=f"plate_bolt_{index}",
        )

    # The short horizontal galvanized arm projects from the tip of the plate.
    mount.visual(
        Cylinder(radius=0.022, length=0.315),
        origin=Origin(xyz=(0.382, 0.0, ARM_Z), rpy=(0.0, math.pi / 2, 0.0)),
        material=galvanized,
        name="arm_tube",
    )
    mount.visual(
        Cylinder(radius=0.035, length=0.034),
        origin=Origin(xyz=(0.235, 0.0, ARM_Z), rpy=(0.0, math.pi / 2, 0.0)),
        material=dark_galv,
        name="weld_collar",
    )
    mount.visual(
        Box((0.170, 0.008, 0.050)),
        origin=Origin(xyz=(0.315, 0.0, ARM_Z - 0.032), rpy=(0.0, 0.0, 0.0)),
        material=dark_galv,
        name="under_gusset",
    )

    # A static lower bearing at the arm end carries the pan axis.  The rotating
    # yoke sits directly below this face.
    mount.visual(
        Cylinder(radius=0.040, length=0.060),
        origin=Origin(xyz=(PAN_X, 0.0, PAN_Z + 0.030)),
        material=galvanized,
        name="pan_bearing",
    )
    mount.visual(
        mesh_from_geometry(
            TorusGeometry(radius=0.033, tube=0.004, radial_segments=16, tubular_segments=48),
            "bearing_lip",
        ),
        origin=Origin(xyz=(PAN_X, 0.0, PAN_Z + 0.061)),
        material=dark_galv,
        name="bearing_lip",
    )

    yoke = model.part("pan_yoke")
    yoke.visual(
        Cylinder(radius=0.016, length=0.095),
        origin=Origin(xyz=(0.0, 0.0, -0.0475)),
        material=camera_white,
        name="pan_stem",
    )
    yoke.visual(
        Cylinder(radius=0.035, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -0.007)),
        material=camera_white,
        name="turntable",
    )
    yoke.visual(
        Box((0.080, 0.145, 0.020)),
        origin=Origin(xyz=(0.0, 0.0, -0.058)),
        material=camera_white,
        name="yoke_crown",
    )
    yoke.visual(
        Box((0.030, 0.012, 0.135)),
        origin=Origin(xyz=(0.0, -0.066, -0.125)),
        material=camera_white,
        name="side_cheek_0",
    )
    yoke.visual(
        Cylinder(radius=0.017, length=0.006),
        origin=Origin(xyz=(0.0, -0.075, TILT_Z), rpy=(math.pi / 2, 0.0, 0.0)),
        material=screw_black,
        name="pivot_cap_0",
    )
    yoke.visual(
        Box((0.030, 0.012, 0.135)),
        origin=Origin(xyz=(0.0, 0.066, -0.125)),
        material=camera_white,
        name="side_cheek_1",
    )
    yoke.visual(
        Cylinder(radius=0.017, length=0.006),
        origin=Origin(xyz=(0.0, 0.075, TILT_Z), rpy=(-math.pi / 2, 0.0, 0.0)),
        material=screw_black,
        name="pivot_cap_1",
    )

    camera = model.part("dome_camera")
    camera.visual(
        Cylinder(radius=0.0088, length=0.120),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-math.pi / 2, 0.0, 0.0)),
        material=dark_galv,
        name="tilt_pin",
    )
    camera.visual(
        Cylinder(radius=0.030, length=0.092),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-math.pi / 2, 0.0, 0.0)),
        material=camera_white,
        name="tilt_barrel",
    )
    camera.visual(
        Cylinder(radius=0.052, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=camera_white,
        name="housing_band",
    )
    camera.visual(
        mesh_from_geometry(DomeGeometry(0.045, radial_segments=48, height_segments=14), "tinted_dome"),
        origin=Origin(xyz=(0.0, 0.0, -0.0525), rpy=(math.pi, 0.0, 0.0)),
        material=camera_black,
        name="tinted_dome",
    )
    camera.visual(
        Cylinder(radius=0.019, length=0.003),
        origin=Origin(xyz=(0.020, 0.0, -0.090), rpy=(0.0, math.pi / 2, 0.0)),
        material=screw_black,
        name="lens_window",
    )

    model.articulation(
        "arm_to_yoke",
        ArticulationType.REVOLUTE,
        parent=mount,
        child=yoke,
        origin=Origin(xyz=(PAN_X, 0.0, PAN_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=1.6, lower=-2.7, upper=2.7),
    )
    model.articulation(
        "yoke_to_camera",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=camera,
        origin=Origin(xyz=(0.0, 0.0, TILT_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=1.4, lower=-0.75, upper=0.75),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
