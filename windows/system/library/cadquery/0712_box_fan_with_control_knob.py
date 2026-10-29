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

def _profile_points_3d(profile):
    points = [(float(x), float(y), float(z)) for (x, y, z) in profile]
    cleaned = []
    for pt in points:
        if not cleaned or not (abs(cleaned[-1][0] - pt[0]) <= 1e-9 and abs(cleaned[-1][1] - pt[1]) <= 1e-9 and abs(cleaned[-1][2] - pt[2]) <= 1e-9):
            cleaned.append(pt)
    if len(cleaned) >= 2 and abs(cleaned[0][0] - cleaned[-1][0]) <= 1e-9 and abs(cleaned[0][1] - cleaned[-1][1]) <= 1e-9 and abs(cleaned[0][2] - cleaned[-1][2]) <= 1e-9:
        cleaned = cleaned[:-1]
    if len(cleaned) < 2:
        raise ValidationError("Profile must have at least 2 unique points")
    return cleaned

# ===== lathe_extrude_loft (4 syms) =====
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

def _xy_area(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        a += x1 * y2 - x2 * y1
    return a * 0.5

def _loft_solid(rings, *, cap, closed, ruled=True):
    """Loft through a list of 3D rings. cap+closed -> solid via makeLoft;
    otherwise an open side-wall shell. Rings are oriented consistently first."""
    rings = [list(r) for r in rings]
    if len(rings) < 2:
        raise ValidationError("Loft requires at least two profiles")
    base = _xy_area(rings[0])
    if abs(base) > 1e-9:
        if base < 0:
            rings = [list(reversed(r)) for r in rings]
            base = -base
        for idx in range(len(rings)):
            if _xy_area(rings[idx]) * base < 0:
                rings[idx] = list(reversed(rings[idx]))
    if cap and closed:
        wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in r], close=True) for r in rings]
        return cq.Solid.makeLoft(wires, ruled)
    faces = _loft_side_faces(rings, closed)
    if not faces:
        raise ValidationError("Loft produced no valid side faces")
    return cq.Shell.makeShell(faces)

class LoftGeometry(MeshGeometry):
    """Loft through a sequence of closed 3D profiles (each a list of (x,y,z))."""

    def __init__(self, profiles, *, cap=True, closed=True):
        super().__init__()
        profile_list = [_profile_points_3d(p) for p in profiles]
        if len(profile_list) < 2:
            raise ValidationError("Loft requires at least two profiles")

        ring_count = len(profile_list[0])
        if closed and ring_count < 3:
            raise ValidationError("Closed loft profiles must have at least 3 points")
        for profile in profile_list:
            if len(profile) != ring_count:
                raise ValidationError("Loft profiles must have the same point count")

        self._set(_loft_solid(profile_list, cap=cap, closed=closed))

# ===== model =====
import math
ASSETS = AssetContext.from_script(__file__)
IVORY_PLASTIC = Material("ivory_plastic", (0.90, 0.88, 0.83, 1.0))
GRAPHITE_PLASTIC = Material("graphite_plastic", (0.12, 0.13, 0.14, 1.0))
STEEL_WIRE = Material("steel_wire", (0.33, 0.35, 0.38, 1.0))
SMOKE_BLADE = Material("smoke_blade", (0.28, 0.32, 0.35, 0.58))
RUBBER = Material("rubber", (0.08, 0.08, 0.09, 1.0))
SILVER = Material("silver_trim", (0.72, 0.73, 0.75, 1.0))
POINTER_WHITE = Material("pointer_white", (0.96, 0.96, 0.94, 1.0))
def _blade_section(chord: float, thickness: float, sweep: float, radius: float, twist: float):
    profile_2d = [
        (-0.48 * chord, -0.18 * thickness),
        (-0.20 * chord, -0.56 * thickness),
        (0.16 * chord, -0.44 * thickness),
        (0.50 * chord, 0.0),
        (0.18 * chord, 0.56 * thickness),
        (-0.42 * chord, 0.22 * thickness),
    ]
    c = math.cos(twist)
    s = math.sin(twist)
    section = []
    for x, y in profile_2d:
        x += sweep
        xr = c * x - s * y
        yr = s * x + c * y
        section.append((xr, yr, radius))
    return section
def _build_blade_mesh():
    blade_geom = LoftGeometry(
        [
            _blade_section(chord=0.088, thickness=0.011, sweep=0.006, radius=0.045, twist=0.32),
            _blade_section(chord=0.070, thickness=0.0085, sweep=0.014, radius=0.108, twist=0.14),
            _blade_section(chord=0.048, thickness=0.0060, sweep=0.025, radius=0.172, twist=-0.08),
        ],
        cap=True,
        closed=True,
    )
    return mesh_from_geometry(blade_geom, ASSETS.mesh_path("box_fan_blade.obj"))
def _add_grille(part, y: float, grille_w: float, grille_h: float, material: Material) -> None:
    frame_radius = 0.0035
    wire_radius = 0.0023

    part.visual(
        Cylinder(radius=frame_radius, length=grille_h),
        origin=Origin(xyz=(-grille_w / 2, y, 0.0)),
        material=material,
        name=f"grille_side_left_{y:+.3f}",
    )
    part.visual(
        Cylinder(radius=frame_radius, length=grille_h),
        origin=Origin(xyz=(grille_w / 2, y, 0.0)),
        material=material,
        name=f"grille_side_right_{y:+.3f}",
    )
    part.visual(
        Cylinder(radius=frame_radius, length=grille_w),
        origin=Origin(xyz=(0.0, y, grille_h / 2), rpy=(0.0, math.pi / 2, 0.0)),
        material=material,
        name=f"grille_top_{y:+.3f}",
    )
    part.visual(
        Cylinder(radius=frame_radius, length=grille_w),
        origin=Origin(xyz=(0.0, y, -grille_h / 2), rpy=(0.0, math.pi / 2, 0.0)),
        material=material,
        name=f"grille_bottom_{y:+.3f}",
    )

    vertical_count = 11
    horizontal_count = 11
    for i in range(vertical_count):
        x = -0.17 + i * (0.34 / (vertical_count - 1))
        part.visual(
            Cylinder(radius=wire_radius, length=grille_h - 0.014),
            origin=Origin(xyz=(x, y, 0.0)),
            material=material,
            name=f"grille_v_{i}_{y:+.3f}",
        )
    for i in range(horizontal_count):
        z = -0.17 + i * (0.34 / (horizontal_count - 1))
        part.visual(
            Cylinder(radius=wire_radius, length=grille_w - 0.014),
            origin=Origin(xyz=(0.0, y, z), rpy=(0.0, math.pi / 2, 0.0)),
            material=material,
            name=f"grille_h_{i}_{y:+.3f}",
        )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="box_fan", assets=ASSETS)

    blade_mesh = _build_blade_mesh()

    outer_w = 0.52
    outer_h = 0.54
    depth = 0.16
    frame_t = 0.05
    corner_r = frame_t / 2
    front_y = depth / 2 - 0.012
    rear_y = -depth / 2 + 0.012

    housing = model.part("housing")
    housing.inertial = Inertial.from_geometry(
        Box((outer_w, depth, outer_h)),
        mass=3.8,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
    )

    side_h = outer_h - 2 * corner_r
    top_w = outer_w - 2 * corner_r
    for x in (-outer_w / 2 + frame_t / 2, outer_w / 2 - frame_t / 2):
        housing.visual(
            Box((frame_t, depth, side_h)),
            origin=Origin(xyz=(x, 0.0, 0.0)),
            material=IVORY_PLASTIC,
            name=f"side_column_{x:+.3f}",
        )
    for z in (-outer_h / 2 + frame_t / 2, outer_h / 2 - frame_t / 2):
        housing.visual(
            Box((top_w, depth, frame_t)),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=IVORY_PLASTIC,
            name=f"cross_rail_{z:+.3f}",
        )
    for x in (-outer_w / 2 + corner_r, outer_w / 2 - corner_r):
        for z in (-outer_h / 2 + corner_r, outer_h / 2 - corner_r):
            housing.visual(
                Cylinder(radius=corner_r, length=depth),
                origin=Origin(xyz=(x, 0.0, z), rpy=(math.pi / 2, 0.0, 0.0)),
                material=IVORY_PLASTIC,
                name=f"corner_{x:+.3f}_{z:+.3f}",
            )

    for x in (-0.11, 0.11):
        housing.visual(
            Box((0.11, depth + 0.03, 0.018)),
            origin=Origin(xyz=(x, 0.0, -outer_h / 2 - 0.009)),
            material=IVORY_PLASTIC,
            name=f"foot_{x:+.3f}",
        )
        housing.visual(
            Box((0.09, depth + 0.02, 0.004)),
            origin=Origin(xyz=(x, 0.0, -outer_h / 2 - 0.020)),
            material=RUBBER,
            name=f"foot_pad_{x:+.3f}",
        )

    for x in (-0.105, 0.105):
        housing.visual(
            Box((0.028, depth * 0.80, 0.055)),
            origin=Origin(xyz=(x, 0.0, outer_h / 2 + 0.028)),
            material=IVORY_PLASTIC,
            name=f"handle_post_{x:+.3f}",
        )
    housing.visual(
        Box((0.235, depth * 0.64, 0.028)),
        origin=Origin(xyz=(0.0, 0.0, outer_h / 2 + 0.068)),
        material=IVORY_PLASTIC,
        name="handle_bridge",
    )
    housing.visual(
        Cylinder(radius=0.014, length=depth * 0.64),
        origin=Origin(xyz=(-0.1175, 0.0, outer_h / 2 + 0.068), rpy=(math.pi / 2, 0.0, 0.0)),
        material=IVORY_PLASTIC,
        name="handle_round_left",
    )
    housing.visual(
        Cylinder(radius=0.014, length=depth * 0.64),
        origin=Origin(xyz=(0.1175, 0.0, outer_h / 2 + 0.068), rpy=(math.pi / 2, 0.0, 0.0)),
        material=IVORY_PLASTIC,
        name="handle_round_right",
    )

    _add_grille(housing, front_y, grille_w=0.424, grille_h=0.424, material=STEEL_WIRE)
    _add_grille(housing, rear_y, grille_w=0.424, grille_h=0.424, material=STEEL_WIRE)

    housing.visual(
        Cylinder(radius=0.058, length=0.060),
        origin=Origin(xyz=(0.0, -0.030, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=GRAPHITE_PLASTIC,
        name="rear_motor_cap",
    )
    housing.visual(
        Box((0.300, 0.008, 0.008)),
        origin=Origin(xyz=(0.0, -0.064, 0.0)),
        material=STEEL_WIRE,
        name="rear_support_horizontal",
    )
    housing.visual(
        Box((0.008, 0.008, 0.300)),
        origin=Origin(xyz=(0.0, -0.064, 0.0)),
        material=STEEL_WIRE,
        name="rear_support_vertical",
    )
    housing.visual(
        Box((0.060, 0.014, 0.004)),
        origin=Origin(xyz=(0.0, front_y, -0.205)),
        material=GRAPHITE_PLASTIC,
        name="front_badge",
    )

    control_pod = model.part("control_pod")
    control_pod.inertial = Inertial.from_geometry(
        Box((0.074, 0.090, 0.022)),
        mass=0.18,
        origin=Origin(xyz=(0.0, 0.0, 0.011)),
    )
    control_pod.visual(
        Box((0.074, 0.090, 0.022)),
        origin=Origin(xyz=(0.0, 0.0, 0.011)),
        material=IVORY_PLASTIC,
        name="pod_body",
    )
    control_pod.visual(
        Cylinder(radius=0.024, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.027)),
        material=SILVER,
        name="pod_knob_bezel",
    )
    control_pod.visual(
        Box((0.048, 0.008, 0.003)),
        origin=Origin(xyz=(0.0, -0.031, 0.005)),
        material=GRAPHITE_PLASTIC,
        name="pod_label_strip",
    )

    rotor = model.part("rotor")
    rotor.inertial = Inertial.from_geometry(
        Cylinder(radius=0.034, length=0.028),
        mass=0.45,
        origin=Origin(xyz=(0.0, 0.022, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
    )
    rotor.visual(
        Cylinder(radius=0.034, length=0.028),
        origin=Origin(xyz=(0.0, 0.022, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=GRAPHITE_PLASTIC,
        name="hub_body",
    )
    rotor.visual(
        Cylinder(radius=0.020, length=0.014),
        origin=Origin(xyz=(0.0, 0.010, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=SILVER,
        name="hub_collar",
    )
    rotor.visual(
        Cylinder(radius=0.022, length=0.018),
        origin=Origin(xyz=(0.0, 0.042, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=SILVER,
        name="spinner_cap",
    )
    for i in range(5):
        angle = i * (2.0 * math.pi / 5.0)
        rotor.visual(
            blade_mesh,
            origin=Origin(xyz=(0.0, 0.020, 0.0), rpy=(0.0, angle, 0.0)),
            material=SMOKE_BLADE,
            name=f"blade_{i}",
        )

    knob = model.part("knob")
    knob.inertial = Inertial.from_geometry(
        Cylinder(radius=0.019, length=0.012),
        mass=0.05,
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
    )
    knob.visual(
        Cylinder(radius=0.019, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=GRAPHITE_PLASTIC,
        name="knob_base",
    )
    knob.visual(
        Cylinder(radius=0.016, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.019)),
        material=GRAPHITE_PLASTIC,
        name="knob_cap",
    )
    knob.visual(
        Box((0.013, 0.003, 0.004)),
        origin=Origin(xyz=(0.0105, 0.0, 0.030)),
        material=POINTER_WHITE,
        name="knob_pointer",
    )

    model.articulation(
        "control_pod_mount",
        ArticulationType.FIXED,
        parent="housing",
        child="control_pod",
        origin=Origin(xyz=(0.155, 0.0, outer_h / 2)),
    )
    model.articulation(
        "blade_spin",
        ArticulationType.CONTINUOUS,
        parent="housing",
        child="rotor",
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.8,
            velocity=28.0,
        ),
    )
    model.articulation(
        "speed_knob",
        ArticulationType.REVOLUTE,
        parent="control_pod",
        child="knob",
        origin=Origin(xyz=(0.0, 0.0, 0.032)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.3,
            velocity=2.5,
            lower=0.0,
            upper=4.2,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
