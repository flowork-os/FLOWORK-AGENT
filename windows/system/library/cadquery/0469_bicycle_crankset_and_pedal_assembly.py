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
def _add_quad(mesh: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    mesh.add_face(a, b, c)
    mesh.add_face(a, c, d)
def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]
def _extrude_yz_profile(
    profile: list[tuple[float, float]], x_min: float, x_max: float
) -> MeshGeometry:
    """Extrude a simple YZ-plane profile between two X faces."""
    mesh = MeshGeometry()
    front = [mesh.add_vertex(x_max, y, z) for y, z in profile]
    back = [mesh.add_vertex(x_min, y, z) for y, z in profile]
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        _add_quad(mesh, front[i], front[j], back[j], back[i])

    cy = sum(y for y, _ in profile) / n
    cz = sum(z for _, z in profile) / n
    cf = mesh.add_vertex(x_max, cy, cz)
    cb = mesh.add_vertex(x_min, cy, cz)
    for i in range(n):
        j = (i + 1) % n
        mesh.add_face(cf, front[i], front[j])
        mesh.add_face(cb, back[j], back[i])
    return mesh
def _circle_profile(
    y: float, z: float, radius: float, *, segments: int = 36
) -> list[tuple[float, float]]:
    return [
        (
            y + radius * math.cos(2.0 * math.pi * i / segments),
            z + radius * math.sin(2.0 * math.pi * i / segments),
        )
        for i in range(segments)
    ]
def _capsule_profile(
    start_z: float,
    end_z: float,
    start_radius: float,
    end_radius: float,
    *,
    segments: int = 36,
) -> list[tuple[float, float]]:
    samples: list[tuple[float, float]] = []
    samples.extend(_circle_profile(0.0, start_z, start_radius, segments=segments))
    samples.extend(_circle_profile(0.0, end_z, end_radius, segments=segments))
    return _convex_hull(samples)
def _cylinder_x_mesh(
    radius: float,
    x_min: float,
    x_max: float,
    *,
    y: float = 0.0,
    z: float = 0.0,
    segments: int = 48,
) -> MeshGeometry:
    mesh = MeshGeometry()
    right = []
    left = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        yy = y + radius * math.cos(a)
        zz = z + radius * math.sin(a)
        right.append(mesh.add_vertex(x_max, yy, zz))
        left.append(mesh.add_vertex(x_min, yy, zz))

    cr = mesh.add_vertex(x_max, y, z)
    cl = mesh.add_vertex(x_min, y, z)
    for i in range(segments):
        j = (i + 1) % segments
        _add_quad(mesh, right[i], right[j], left[j], left[i])
        mesh.add_face(cr, right[i], right[j])
        mesh.add_face(cl, left[j], left[i])
    return mesh
def _tapered_spindle_mesh() -> MeshGeometry:
    """A road bottom-bracket spindle with visibly wider tapered ends."""
    stations = [
        (-0.086, 0.0165),
        (-0.055, 0.0128),
        (0.055, 0.0128),
        (0.086, 0.0165),
    ]
    segments = 64
    mesh = MeshGeometry()
    loops: list[list[int]] = []
    for x, radius in stations:
        loop = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            loop.append(
                mesh.add_vertex(x, radius * math.cos(a), radius * math.sin(a))
            )
        loops.append(loop)

    for k in range(len(loops) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            _add_quad(mesh, loops[k][i], loops[k][j], loops[k + 1][j], loops[k + 1][i])

    c0 = mesh.add_vertex(stations[0][0], 0.0, 0.0)
    c1 = mesh.add_vertex(stations[-1][0], 0.0, 0.0)
    for i in range(segments):
        j = (i + 1) % segments
        mesh.add_face(c0, loops[0][j], loops[0][i])
        mesh.add_face(c1, loops[-1][i], loops[-1][j])
    return mesh
def _annular_x_mesh(
    inner_radius: float,
    outer_radius: float,
    thickness: float,
    *,
    segments: int = 96,
    teeth: int = 0,
    tooth_depth: float = 0.0,
) -> MeshGeometry:
    """An annular plate in the YZ plane with optional chainring teeth."""
    steps = max(segments, teeth * 4 if teeth else 0)
    mesh = MeshGeometry()
    outer_r: list[float] = []
    for i in range(steps):
        if teeth:
            phase = i % 4
            outer_r.append(outer_radius + (tooth_depth if phase in (1, 2) else 0.0))
        else:
            outer_r.append(outer_radius)

    xf = thickness / 2.0
    xb = -thickness / 2.0
    outer_front: list[int] = []
    outer_back: list[int] = []
    inner_front: list[int] = []
    inner_back: list[int] = []
    for i in range(steps):
        a = 2.0 * math.pi * i / steps
        ca = math.cos(a)
        sa = math.sin(a)
        r = outer_r[i]
        outer_front.append(mesh.add_vertex(xf, r * ca, r * sa))
        outer_back.append(mesh.add_vertex(xb, r * ca, r * sa))
        inner_front.append(mesh.add_vertex(xf, inner_radius * ca, inner_radius * sa))
        inner_back.append(mesh.add_vertex(xb, inner_radius * ca, inner_radius * sa))

    for i in range(steps):
        j = (i + 1) % steps
        _add_quad(mesh, outer_front[i], outer_front[j], outer_back[j], outer_back[i])
        _add_quad(mesh, inner_front[j], inner_front[i], inner_back[i], inner_back[j])
        _add_quad(mesh, outer_front[i], outer_front[j], inner_front[j], inner_front[i])
        _add_quad(mesh, outer_back[j], outer_back[i], inner_back[i], inner_back[j])
    return mesh
def _spider_mesh() -> MeshGeometry:
    mesh = MeshGeometry()
    # Central web around the spindle.
    mesh.merge(_extrude_yz_profile(_circle_profile(0.0, 0.0, 0.030), 0.056, 0.086))

    # Five radial arms, with a broader lower arm blending into the right crank.
    bolt_radius = 0.069
    for k in range(5):
        angle = math.radians(90.0 + k * 72.0)
        y = bolt_radius * math.cos(angle)
        z = bolt_radius * math.sin(angle)
        width = 0.013 if k != 2 else 0.016
        samples: list[tuple[float, float]] = []
        samples.extend(_circle_profile(0.0, 0.0, 0.013, segments=24))
        samples.extend(_circle_profile(y, z, width, segments=24))
        radial_profile = _convex_hull(samples)
        mesh.merge(_extrude_yz_profile(radial_profile, 0.060, 0.084))
        mesh.merge(_extrude_yz_profile(_circle_profile(y, z, 0.014, segments=30), 0.054, 0.090))
    return mesh
def _crank_arm_mesh(x_min: float, x_max: float, end_z: float) -> MeshGeometry:
    profile = _capsule_profile(0.0, end_z, 0.024, 0.020, segments=40)
    return _extrude_yz_profile(profile, x_min, x_max)
def _pedal_body_mesh(sign: float) -> MeshGeometry:
    mesh = MeshGeometry()
    # Threaded axle from the crank face into the pedal body.
    mesh.merge(_cylinder_x_mesh(0.0042, min(0.0, 0.040 * sign), max(0.0, 0.040 * sign)))
    # Compact road-pedal platform, with shallow fore/aft bevels.
    x0 = 0.026 * sign
    x1 = 0.076 * sign
    mesh.merge(
        _extrude_yz_profile(
            [
                (-0.044, -0.006),
                (-0.034, -0.014),
                (0.034, -0.014),
                (0.044, -0.006),
                (0.040, 0.010),
                (0.022, 0.016),
                (-0.022, 0.016),
                (-0.040, 0.010),
            ],
            min(x0, x1),
            max(x0, x1),
        )
    )
    return mesh
def _tread_ridge_mesh(sign: float, y: float) -> MeshGeometry:
    x0 = min(0.035 * sign, 0.068 * sign)
    x1 = max(0.035 * sign, 0.068 * sign)
    return _extrude_yz_profile(
        [(y - 0.002, 0.010), (y + 0.002, 0.010), (y + 0.002, 0.020), (y - 0.002, 0.020)],
        x0,
        x1,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="road_double_crankset")

    matte_black = model.material("matte_black", rgba=(0.015, 0.014, 0.012, 1.0))
    satin_black = model.material("satin_black", rgba=(0.05, 0.05, 0.045, 1.0))
    graphite = model.material("graphite_chainring", rgba=(0.09, 0.095, 0.09, 1.0))
    aluminum = model.material("brushed_aluminum", rgba=(0.72, 0.70, 0.66, 1.0))
    steel = model.material("polished_steel", rgba=(0.82, 0.82, 0.78, 1.0))
    bearing_grey = model.material("bearing_grey", rgba=(0.30, 0.31, 0.32, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_geometry(
            _annular_x_mesh(0.0205, 0.030, 0.090, segments=96),
            "bearing_shell",
        ),
        material=bearing_grey,
        name="bearing_shell",
    )
    ball_radius = 0.00385
    ball_center_radius = 0.0128 + ball_radius
    for i, x in enumerate((-0.026, 0.026)):
        for j, angle in enumerate((math.pi / 2.0, 3.0 * math.pi / 2.0)):
            bottom_bracket.visual(
                Sphere(ball_radius),
                origin=Origin(
                    xyz=(
                        x,
                        ball_center_radius * math.cos(angle),
                        ball_center_radius * math.sin(angle),
                    )
                ),
                material=steel,
                name=f"bearing_ball_{i}_{j}",
            )

    crankset = model.part("crankset")
    crankset.visual(
        mesh_from_geometry(_tapered_spindle_mesh(), "tapered_spindle"),
        material=steel,
        name="tapered_spindle",
    )
    crankset.visual(
        mesh_from_geometry(_crank_arm_mesh(0.052, 0.068, -0.170), "right_crank_arm"),
        material=aluminum,
        name="right_crank_arm",
    )
    crankset.visual(
        mesh_from_geometry(_crank_arm_mesh(-0.068, -0.052, 0.170), "crank_arm"),
        material=aluminum,
        name="crank_arm",
    )
    crankset.visual(
        mesh_from_geometry(_spider_mesh(), "right_spider"),
        material=aluminum,
        name="right_spider",
    )
    crankset.visual(
        mesh_from_geometry(
            _annular_x_mesh(
                0.078,
                0.098,
                0.0032,
                segments=160,
                teeth=50,
                tooth_depth=0.005,
            ),
            "outer_chainring",
        ),
        origin=Origin(xyz=(0.086, 0.0, 0.0)),
        material=graphite,
        name="outer_chainring",
    )
    crankset.visual(
        mesh_from_geometry(
            _annular_x_mesh(
                0.050,
                0.069,
                0.0028,
                segments=128,
                teeth=34,
                tooth_depth=0.004,
            ),
            "inner_chainring",
        ),
        origin=Origin(xyz=(0.061, 0.0, 0.0)),
        material=graphite,
        name="inner_chainring",
    )
    crankset.visual(
        mesh_from_geometry(
            _cylinder_x_mesh(0.009, 0.068, 0.074, z=-0.170, segments=36),
            "pedal_boss_0",
        ),
        material=steel,
        name="pedal_boss_0",
    )
    crankset.visual(
        mesh_from_geometry(
            _cylinder_x_mesh(0.009, -0.074, -0.068, z=0.170, segments=36),
            "pedal_boss_1",
        ),
        material=steel,
        name="pedal_boss_1",
    )
    for k in range(5):
        angle = math.radians(90.0 + k * 72.0)
        y = 0.069 * math.cos(angle)
        z = 0.069 * math.sin(angle)
        crankset.visual(
            mesh_from_geometry(
                _cylinder_x_mesh(0.0045, 0.087, 0.092, y=y, z=z, segments=24),
                f"chainring_bolt_{k}",
            ),
            material=steel,
            name=f"chainring_bolt_{k}",
        )

    pedal_0 = model.part("pedal_0")
    pedal_0.visual(
        mesh_from_geometry(_pedal_body_mesh(1.0), "pedal_body_0"),
        material=satin_black,
        name="pedal_body",
    )
    for i, y in enumerate((-0.030, -0.015, 0.0, 0.015, 0.030)):
        pedal_0.visual(
            mesh_from_geometry(_tread_ridge_mesh(1.0, y), f"pedal_tread_0_{i}"),
            material=matte_black,
            name=f"tread_{i}",
        )

    pedal_1 = model.part("pedal_1")
    pedal_1.visual(
        mesh_from_geometry(_pedal_body_mesh(-1.0), "pedal_body_1"),
        material=satin_black,
        name="pedal_body",
    )
    for i, y in enumerate((-0.030, -0.015, 0.0, 0.015, 0.030)):
        pedal_1.visual(
            mesh_from_geometry(_tread_ridge_mesh(-1.0, y), f"pedal_tread_1_{i}"),
            material=matte_black,
            name=f"tread_{i}",
        )

    model.articulation(
        "bracket_to_crankset",
        ArticulationType.CONTINUOUS,
        parent=bottom_bracket,
        child=crankset,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=20.0),
    )
    model.articulation(
        "crankset_to_pedal_0",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=pedal_0,
        origin=Origin(xyz=(0.074, 0.0, -0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=30.0),
    )
    model.articulation(
        "crankset_to_pedal_1",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=pedal_1,
        origin=Origin(xyz=(-0.074, 0.0, 0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=30.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
