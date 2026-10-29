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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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

# ===== model =====
import math
def _annular_tube_x(
    *,
    length: float,
    inner_radius: float,
    outer_radius: float,
    center_x: float = 0.0,
    segments: int = 72,
) -> MeshGeometry:
    """Watertight hollow cylinder aligned on the local X axis."""
    geom = MeshGeometry()
    x0 = center_x - length / 2.0
    x1 = center_x + length / 2.0
    outer0: list[int] = []
    outer1: list[int] = []
    inner0: list[int] = []
    inner1: list[int] = []

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        y = math.cos(theta)
        z = math.sin(theta)
        outer0.append(geom.add_vertex(x0, outer_radius * y, outer_radius * z))
        outer1.append(geom.add_vertex(x1, outer_radius * y, outer_radius * z))
        inner0.append(geom.add_vertex(x0, inner_radius * y, inner_radius * z))
        inner1.append(geom.add_vertex(x1, inner_radius * y, inner_radius * z))

    for i in range(segments):
        j = (i + 1) % segments
        # outer wall
        geom.add_face(outer0[i], outer0[j], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer1[i])
        # inner wall
        geom.add_face(inner0[j], inner0[i], inner1[i])
        geom.add_face(inner0[j], inner1[i], inner1[j])
        # end caps
        geom.add_face(outer1[i], outer1[j], inner1[j])
        geom.add_face(outer1[i], inner1[j], inner1[i])
        geom.add_face(outer0[j], outer0[i], inner0[i])
        geom.add_face(outer0[j], inner0[i], inner0[j])
    return geom
def _stepped_pressfit_shell() -> MeshGeometry:
    """Press-fit bottom bracket shell with larger bearing lips at each end."""
    stations = [
        (-0.060, 0.032),
        (-0.047, 0.032),
        (-0.047, 0.026),
        (0.047, 0.026),
        (0.047, 0.032),
        (0.060, 0.032),
    ]
    inner_radius = 0.0145
    segments = 72
    geom = MeshGeometry()
    outer: list[list[int]] = []
    inner: list[list[int]] = []

    for x, outer_radius in stations:
        outer_loop: list[int] = []
        inner_loop: list[int] = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            y = math.cos(theta)
            z = math.sin(theta)
            outer_loop.append(geom.add_vertex(x, outer_radius * y, outer_radius * z))
            inner_loop.append(geom.add_vertex(x, inner_radius * y, inner_radius * z))
        outer.append(outer_loop)
        inner.append(inner_loop)

    for s in range(len(stations) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            geom.add_face(outer[s][i], outer[s][j], outer[s + 1][j])
            geom.add_face(outer[s][i], outer[s + 1][j], outer[s + 1][i])
            geom.add_face(inner[s][j], inner[s][i], inner[s + 1][i])
            geom.add_face(inner[s][j], inner[s + 1][i], inner[s + 1][j])

    # Open tube end faces.
    for i in range(segments):
        j = (i + 1) % segments
        geom.add_face(outer[0][j], outer[0][i], inner[0][i])
        geom.add_face(outer[0][j], inner[0][i], inner[0][j])
        geom.add_face(outer[-1][i], outer[-1][j], inner[-1][j])
        geom.add_face(outer[-1][i], inner[-1][j], inner[-1][i])
    return geom
def _chainring_mesh(
    *,
    center_x: float,
    thickness: float,
    inner_radius: float = 0.124,
    root_radius: float = 0.156,
    tooth_tip_radius: float = 0.168,
    teeth: int = 48,
) -> MeshGeometry:
    """Thin track chainring: hollow annulus with repeated tooth tips."""
    segments = teeth * 4
    geom = MeshGeometry()
    x0 = center_x - thickness / 2.0
    x1 = center_x + thickness / 2.0
    outer0: list[int] = []
    outer1: list[int] = []
    inner0: list[int] = []
    inner1: list[int] = []

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        phase = (i % 4) / 4.0
        tooth_shape = 1.0 if phase in (0.25, 0.50) else 0.20
        radius = root_radius + (tooth_tip_radius - root_radius) * tooth_shape
        y = math.cos(theta)
        z = math.sin(theta)
        outer0.append(geom.add_vertex(x0, radius * y, radius * z))
        outer1.append(geom.add_vertex(x1, radius * y, radius * z))
        inner0.append(geom.add_vertex(x0, inner_radius * y, inner_radius * z))
        inner1.append(geom.add_vertex(x1, inner_radius * y, inner_radius * z))

    for i in range(segments):
        j = (i + 1) % segments
        # faces and side walls
        geom.add_face(outer1[i], outer1[j], inner1[j])
        geom.add_face(outer1[i], inner1[j], inner1[i])
        geom.add_face(outer0[j], outer0[i], inner0[i])
        geom.add_face(outer0[j], inner0[i], inner0[j])
        geom.add_face(outer0[i], outer0[j], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer1[i])
        geom.add_face(inner0[j], inner0[i], inner1[i])
        geom.add_face(inner0[j], inner1[i], inner1[j])
    return geom
def _extrude_polygon_x(
    profile_yz: list[tuple[float, float]],
    *,
    center_x: float,
    thickness: float,
) -> MeshGeometry:
    """Extrude a convex YZ profile into a thin solid along X."""
    geom = MeshGeometry()
    x0 = center_x - thickness / 2.0
    x1 = center_x + thickness / 2.0
    back: list[int] = []
    front: list[int] = []
    for y, z in profile_yz:
        back.append(geom.add_vertex(x0, y, z))
        front.append(geom.add_vertex(x1, y, z))

    cy = sum(p[0] for p in profile_yz) / len(profile_yz)
    cz = sum(p[1] for p in profile_yz) / len(profile_yz)
    c0 = geom.add_vertex(x0, cy, cz)
    c1 = geom.add_vertex(x1, cy, cz)
    n = len(profile_yz)
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(back[i], back[j], front[j])
        geom.add_face(back[i], front[j], front[i])
        geom.add_face(c1, front[i], front[j])
        geom.add_face(c0, back[j], back[i])
    return geom
def _crank_arm_profile(*, direction: int, length: float = 0.170) -> list[tuple[float, float]]:
    """Rounded, tapered forged arm outline in local YZ."""
    root_radius = 0.022
    end_radius = 0.0155
    root_half = 0.019
    end_half = 0.013
    side_samples = 12
    cap_samples = 10
    pts: list[tuple[float, float]] = []

    for i in range(side_samples + 1):
        t = i / side_samples
        v = length * t
        half = root_half + (end_half - root_half) * t
        pts.append((half, direction * v))
    for j in range(1, cap_samples + 1):
        theta = math.pi * j / cap_samples
        pts.append((end_radius * math.cos(theta), direction * (length + end_radius * math.sin(theta))))
    for i in range(side_samples - 1, -1, -1):
        t = i / side_samples
        v = length * t
        half = root_half + (end_half - root_half) * t
        pts.append((-half, direction * v))
    for j in range(1, cap_samples):
        theta = math.pi + math.pi * j / cap_samples
        pts.append((root_radius * math.cos(theta), direction * (root_radius * math.sin(theta))))
    return pts
def _spoke_profile(
    *, angle: float, inner_radius: float, outer_radius: float, width: float
) -> list[tuple[float, float]]:
    """Rounded radial spider spoke profile in YZ."""
    samples = 10
    cap_samples = 8
    radial = (math.cos(angle), math.sin(angle))
    tangent = (-math.sin(angle), math.cos(angle))
    half = width / 2.0
    pts: list[tuple[float, float]] = []

    # One long rounded slot-like bar from inner_radius to outer_radius.
    for i in range(samples + 1):
        t = i / samples
        r = inner_radius + (outer_radius - inner_radius) * t
        pts.append((r * radial[0] + half * tangent[0], r * radial[1] + half * tangent[1]))
    for j in range(1, cap_samples + 1):
        theta = angle + math.pi / 2.0 - math.pi * j / cap_samples
        pts.append((outer_radius * radial[0] + half * math.cos(theta), outer_radius * radial[1] + half * math.sin(theta)))
    for i in range(samples - 1, -1, -1):
        t = i / samples
        r = inner_radius + (outer_radius - inner_radius) * t
        pts.append((r * radial[0] - half * tangent[0], r * radial[1] - half * tangent[1]))
    for j in range(1, cap_samples):
        theta = angle - math.pi / 2.0 - math.pi * j / cap_samples
        pts.append((inner_radius * radial[0] + half * math.cos(theta), inner_radius * radial[1] + half * math.sin(theta)))
    return pts
def _add_pedal_visuals(part, *, side: int, metal: Material, rubber: Material) -> None:
    """Add a flat cage pedal that extends from the crank along +/-X."""
    sign = 1 if side >= 0 else -1
    # Threaded spindle and bearing barrel along the revolute axis.
    part.visual(
        Cylinder(radius=0.005, length=0.050),
        origin=Origin(xyz=(sign * 0.025, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="axle",
    )
    part.visual(
        Cylinder(radius=0.010, length=0.058),
        origin=Origin(xyz=(sign * 0.063, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="center_barrel",
    )

    center_x = sign * 0.073
    inner_x = sign * 0.034
    outer_x = sign * 0.112
    # Open rectangular cage: rails overlap at their mitred corners and the
    # central bridge ties the bearing barrel to the perimeter.
    part.visual(
        Box((0.090, 0.010, 0.012)),
        origin=Origin(xyz=(center_x, 0.050, 0.0)),
        material=metal,
        name="front_rail",
    )
    part.visual(
        Box((0.090, 0.010, 0.012)),
        origin=Origin(xyz=(center_x, -0.050, 0.0)),
        material=metal,
        name="rear_rail",
    )
    part.visual(
        Box((0.010, 0.108, 0.012)),
        origin=Origin(xyz=(outer_x, 0.0, 0.0)),
        material=metal,
        name="outer_side_rail",
    )
    part.visual(
        Box((0.010, 0.108, 0.012)),
        origin=Origin(xyz=(inner_x, 0.0, 0.0)),
        material=metal,
        name="inner_side_rail",
    )
    part.visual(
        Box((0.082, 0.008, 0.010)),
        origin=Origin(xyz=(center_x, 0.0, 0.0)),
        material=metal,
        name="center_bridge",
    )
    part.visual(
        Box((0.082, 0.006, 0.006)),
        origin=Origin(xyz=(center_x, 0.025, 0.0)),
        material=metal,
        name="front_bridge",
    )
    part.visual(
        Box((0.082, 0.006, 0.006)),
        origin=Origin(xyz=(center_x, -0.025, 0.0)),
        material=metal,
        name="rear_bridge",
    )

    # Low rubber grip pads and small cage teeth sit on the upper and lower edges.
    for yi, y in enumerate((-0.050, 0.050)):
        part.visual(
            Box((0.072, 0.006, 0.004)),
            origin=Origin(xyz=(center_x, y, 0.008)),
            material=rubber,
            name=f"grip_pad_{yi}",
        )
        for tx, x_offset in enumerate((-0.030, -0.010, 0.010, 0.030)):
            part.visual(
                Box((0.006, 0.006, 0.007)),
                origin=Origin(xyz=(center_x + sign * x_offset, y, 0.013)),
                material=metal,
                name=f"tooth_{yi}_{tx}",
            )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="single_speed_track_crankset")

    polished = model.material("polished_aluminum", rgba=(0.78, 0.76, 0.70, 1.0))
    dark = model.material("anodized_black", rgba=(0.02, 0.022, 0.024, 1.0))
    rubber = model.material("black_rubber", rgba=(0.01, 0.01, 0.012, 1.0))
    bearing = model.material("bearing_steel", rgba=(0.55, 0.58, 0.58, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_geometry(_stepped_pressfit_shell(), "pressfit_shell"),
        material=dark,
        name="pressfit_shell",
    )
    # Thin exposed bearing races inside the press-fit cups.
    bottom_bracket.visual(
        mesh_from_geometry(
            _annular_tube_x(
                length=0.010,
                inner_radius=0.0115,
                outer_radius=0.023,
                center_x=0.054,
                segments=64,
            ),
            "drive_bearing_race",
        ),
        material=bearing,
        name="drive_bearing_race",
    )
    bottom_bracket.visual(
        mesh_from_geometry(
            _annular_tube_x(
                length=0.010,
                inner_radius=0.0115,
                outer_radius=0.023,
                center_x=-0.054,
                segments=64,
            ),
            "opposite_bearing_race",
        ),
        material=bearing,
        name="opposite_bearing_race",
    )

    crank = model.part("crank")
    crank.visual(
        Cylinder(radius=0.0115, length=0.168),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="spindle",
    )
    crank.visual(
        Cylinder(radius=0.033, length=0.020),
        origin=Origin(xyz=(0.072, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="drive_boss",
    )
    crank.visual(
        Cylinder(radius=0.028, length=0.018),
        origin=Origin(xyz=(-0.072, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="opposite_boss",
    )
    crank.visual(
        mesh_from_geometry(
            _chainring_mesh(center_x=0.061, thickness=0.006),
            "large_toothed_chainring",
        ),
        material=dark,
        name="large_chainring",
    )
    for index in range(5):
        angle = -math.pi / 2.0 + 2.0 * math.pi * index / 5.0
        crank.visual(
            mesh_from_geometry(
                _extrude_polygon_x(
                    _spoke_profile(
                        angle=angle,
                        inner_radius=0.026,
                        outer_radius=0.132,
                        width=0.018,
                    ),
                    center_x=0.066,
                    thickness=0.006,
                ),
                f"spider_arm_{index}",
            ),
            material=polished,
            name=f"spider_arm_{index}",
        )
        bolt_y = 0.122 * math.cos(angle)
        bolt_z = 0.122 * math.sin(angle)
        crank.visual(
            Cylinder(radius=0.0055, length=0.005),
            origin=Origin(xyz=(0.068, bolt_y, bolt_z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=bearing,
            name=f"chainring_bolt_{index}",
        )

    crank.visual(
        mesh_from_geometry(
            _extrude_polygon_x(_crank_arm_profile(direction=-1), center_x=0.080, thickness=0.014),
            "drive_forged_arm",
        ),
        material=polished,
        name="drive_arm",
    )
    crank.visual(
        mesh_from_geometry(
            _extrude_polygon_x(_crank_arm_profile(direction=1), center_x=-0.080, thickness=0.014),
            "opposite_forged_arm",
        ),
        material=polished,
        name="opposite_arm",
    )
    crank.visual(
        Cylinder(radius=0.018, length=0.018),
        origin=Origin(xyz=(0.080, 0.0, -0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="drive_pedal_eye",
    )
    crank.visual(
        Cylinder(radius=0.018, length=0.018),
        origin=Origin(xyz=(-0.080, 0.0, 0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="opposite_pedal_eye",
    )

    drive_pedal = model.part("drive_pedal")
    _add_pedal_visuals(drive_pedal, side=1, metal=polished, rubber=rubber)
    opposite_pedal = model.part("opposite_pedal")
    _add_pedal_visuals(opposite_pedal, side=-1, metal=polished, rubber=rubber)

    model.articulation(
        "bottom_bracket_to_crank",
        ArticulationType.CONTINUOUS,
        parent=bottom_bracket,
        child=crank,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=18.0),
        motion_properties=MotionProperties(damping=0.02, friction=0.01),
    )
    model.articulation(
        "crank_to_drive_pedal",
        ArticulationType.CONTINUOUS,
        parent=crank,
        child=drive_pedal,
        origin=Origin(xyz=(0.089, 0.0, -0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.003),
    )
    model.articulation(
        "crank_to_opposite_pedal",
        ArticulationType.CONTINUOUS,
        parent=crank,
        child=opposite_pedal,
        origin=Origin(xyz=(-0.089, 0.0, 0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.003),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
