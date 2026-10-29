# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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

# ===== brackets_hinges_bezels (1 syms) =====
def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

# ===== primitives (1 syms) =====
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== model =====
import math
def _normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if length <= 1e-9:
        return (0.0, 1.0, 0.0)
    return (v[0] / length, v[1] / length, v[2] / length)
def _cross(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
def _de_dion_centerline(samples: int = 53) -> list[tuple[float, float, float]]:
    """Smooth, shallowly bowed transverse axle tube centerline."""
    half_span = 0.88
    pts: list[tuple[float, float, float]] = []
    for i in range(samples):
        u = -1.0 + 2.0 * i / (samples - 1)
        y = u * half_span
        bow = 1.0 - u * u
        x = -0.040 * bow
        z = 0.420 + 0.035 * (1.0 - abs(u) ** 1.5)
        pts.append((x, y, z))
    return pts
def _slotted_hollow_tube_geometry(
    centerline: list[tuple[float, float, float]],
    *,
    outer_radius: float,
    inner_radius: float,
    radial_segments: int = 34,
    slot_center_angle: float = math.pi / 2.0,
    slot_width: float = 1.05,
) -> MeshGeometry:
    """A C-section hollow tube, with a front cutaway slot to reveal the shafts."""
    geom = MeshGeometry()
    start_angle = slot_center_angle + slot_width / 2.0
    end_angle = slot_center_angle + 2.0 * math.pi - slot_width / 2.0
    angles = [
        start_angle + (end_angle - start_angle) * j / (radial_segments - 1)
        for j in range(radial_segments)
    ]

    outer: list[list[int]] = []
    inner: list[list[int]] = []
    up = (0.0, 0.0, 1.0)
    for i, p in enumerate(centerline):
        if i == 0:
            tangent = (
                centerline[1][0] - p[0],
                centerline[1][1] - p[1],
                centerline[1][2] - p[2],
            )
        elif i == len(centerline) - 1:
            tangent = (
                p[0] - centerline[i - 1][0],
                p[1] - centerline[i - 1][1],
                p[2] - centerline[i - 1][2],
            )
        else:
            tangent = (
                centerline[i + 1][0] - centerline[i - 1][0],
                centerline[i + 1][1] - centerline[i - 1][1],
                centerline[i + 1][2] - centerline[i - 1][2],
            )
        t = _normalize(tangent)
        side = _normalize(_cross(t, up))
        vertical = _normalize(_cross(side, t))

        outer_row: list[int] = []
        inner_row: list[int] = []
        for a in angles:
            # a=0 is visually "up"; a=pi/2 is the forward/+X cutaway side.
            direction = (
                math.cos(a) * vertical[0] + math.sin(a) * side[0],
                math.cos(a) * vertical[1] + math.sin(a) * side[1],
                math.cos(a) * vertical[2] + math.sin(a) * side[2],
            )
            outer_row.append(
                geom.add_vertex(
                    p[0] + outer_radius * direction[0],
                    p[1] + outer_radius * direction[1],
                    p[2] + outer_radius * direction[2],
                )
            )
            inner_row.append(
                geom.add_vertex(
                    p[0] + inner_radius * direction[0],
                    p[1] + inner_radius * direction[1],
                    p[2] + inner_radius * direction[2],
                )
            )
        outer.append(outer_row)
        inner.append(inner_row)

    rows = len(centerline)
    cols = len(angles)
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Outer skin.
            geom.add_face(outer[i][j], outer[i + 1][j], outer[i + 1][j + 1])
            geom.add_face(outer[i][j], outer[i + 1][j + 1], outer[i][j + 1])
            # Inner bore skin.
            geom.add_face(inner[i][j + 1], inner[i + 1][j + 1], inner[i + 1][j])
            geom.add_face(inner[i][j + 1], inner[i + 1][j], inner[i][j])

    # Longitudinal lips along the cutaway edges.
    for i in range(rows - 1):
        for j in (0, cols - 1):
            geom.add_face(outer[i][j], inner[i][j], inner[i + 1][j])
            geom.add_face(outer[i][j], inner[i + 1][j], outer[i + 1][j])

    # Annular end faces, leaving the bore open.
    for j in range(cols - 1):
        geom.add_face(outer[0][j], outer[0][j + 1], inner[0][j + 1])
        geom.add_face(outer[0][j], inner[0][j + 1], inner[0][j])
        geom.add_face(outer[-1][j + 1], outer[-1][j], inner[-1][j])
        geom.add_face(outer[-1][j + 1], inner[-1][j], inner[-1][j + 1])

    return geom
def _origin_y(y: float = 0.0) -> Origin:
    return Origin(xyz=(0.0, y, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="rear_de_dion_tube_axle")

    satin_black = model.material("satin_black", rgba=(0.025, 0.027, 0.030, 1.0))
    tube_steel = model.material("tube_steel", rgba=(0.12, 0.13, 0.14, 1.0))
    cut_edge = model.material("cut_edge", rgba=(0.55, 0.56, 0.57, 1.0))
    bright_steel = model.material("bright_steel", rgba=(0.68, 0.70, 0.72, 1.0))
    cv_boot = model.material("cv_boot", rgba=(0.015, 0.014, 0.013, 1.0))
    hub_metal = model.material("hub_metal", rgba=(0.42, 0.44, 0.47, 1.0))
    bearing_dark = model.material("bearing_dark", rgba=(0.05, 0.055, 0.06, 1.0))
    bolt_yellow = model.material("bolt_yellow", rgba=(0.86, 0.63, 0.18, 1.0))

    chassis = model.part("chassis_mount")
    chassis.visual(
        Box((0.40, 0.62, 0.070)),
        origin=Origin(xyz=(-0.060, 0.0, 0.820)),
        material=satin_black,
        name="crossmember",
    )
    chassis.visual(
        Box((0.095, 0.028, 0.225)),
        origin=Origin(xyz=(-0.060, -0.1565, 0.680)),
        material=satin_black,
        name="bracket_0",
    )
    chassis.visual(
        Box((0.095, 0.028, 0.225)),
        origin=Origin(xyz=(-0.060, 0.1565, 0.680)),
        material=satin_black,
        name="bracket_1",
    )
    chassis.visual(
        Cylinder(radius=0.018, length=0.345),
        origin=Origin(xyz=(-0.060, 0.0, 0.620), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=bolt_yellow,
        name="lateral_mount_bolt",
    )

    tube = model.part("de_dion_tube")
    tube_shell = _slotted_hollow_tube_geometry(
        _de_dion_centerline(),
        outer_radius=0.080,
        inner_radius=0.060,
        radial_segments=36,
    )
    tube.visual(
        mesh_from_geometry(tube_shell, "curved_slotted_de_dion_tube"),
        material=tube_steel,
        name="tube_shell",
    )
    tube.visual(
        Box((0.180, 0.245, 0.090)),
        origin=Origin(xyz=(-0.040, 0.0, 0.525)),
        material=tube_steel,
        name="lateral_clamp_block",
    )
    tube.visual(
        Box((0.120, 0.285, 0.018)),
        origin=Origin(xyz=(-0.040, 0.0, 0.575)),
        material=cut_edge,
        name="clamp_top_plate",
    )
    bearing_mesh = mesh_from_geometry(
        TorusGeometry(radius=0.054, tube=0.029, radial_segments=18, tubular_segments=52),
        "bearing_ring",
    )
    for side, y in (("side_0", -0.890), ("side_1", 0.890)):
        tube.visual(
            bearing_mesh,
            origin=Origin(xyz=(0.0, y, 0.420), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=bearing_dark,
            name=f"end_bearing_{side}",
        )
        tube.visual(
            Box((0.075, 0.050, 0.110)),
            origin=Origin(xyz=(-0.006, y, 0.520)),
            material=tube_steel,
            name=f"caliper_lug_{side}",
        )
    support_mesh = mesh_from_geometry(
        TorusGeometry(radius=0.0215, tube=0.0060, radial_segments=14, tubular_segments=36),
        "shaft_support_bushing",
    )
    for idx, y in enumerate((-0.560, -0.320, 0.320, 0.560)):
        tube.visual(
            support_mesh,
            origin=Origin(xyz=(-0.020, y, 0.435), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=bearing_dark,
            name=f"shaft_bushing_{idx}",
        )
        tube.visual(
            Box((0.018, 0.020, 0.060)),
            origin=Origin(xyz=(-0.020, y, 0.386)),
            material=cut_edge,
            name=f"bushing_web_{idx}",
        )

    def add_halfshaft(name: str, y_center: float, inner_sign: float) -> None:
        shaft = model.part(name)
        shaft.visual(
            Cylinder(radius=0.016, length=0.650),
            origin=_origin_y(),
            material=bright_steel,
            name="shaft_core",
        )
        for idx, local_y in enumerate((-0.315, 0.315)):
            shaft.visual(
                Sphere(radius=0.031),
                origin=Origin(xyz=(0.0, local_y, 0.0)),
                material=bright_steel,
                name=f"cv_ball_{idx}",
            )
            for rib in range(4):
                offset = local_y - inner_sign * (0.030 + rib * 0.018)
                shaft.visual(
                    Cylinder(radius=0.027 - rib * 0.0025, length=0.022),
                    origin=_origin_y(offset),
                    material=cv_boot,
                    name=f"boot_rib_{idx}_{rib}",
                )
        model.articulation(
            f"tube_to_{name}",
            ArticulationType.CONTINUOUS,
            parent=tube,
            child=shaft,
            origin=Origin(xyz=(-0.020, y_center, 0.435)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=180.0, velocity=95.0),
        )

    add_halfshaft("half_shaft_0", -0.455, -1.0)
    add_halfshaft("half_shaft_1", 0.455, 1.0)

    def add_hub(name: str, side_sign: float) -> None:
        hub = model.part(name)
        hub.visual(
            Cylinder(radius=0.026, length=0.150),
            origin=_origin_y(side_sign * 0.035),
            material=bright_steel,
            name="stub_axle",
        )
        hub.visual(
            Cylinder(radius=0.118, length=0.026),
            origin=_origin_y(side_sign * 0.090),
            material=hub_metal,
            name="wheel_flange",
        )
        hub.visual(
            Cylinder(radius=0.150, length=0.014),
            origin=_origin_y(side_sign * 0.052),
            material=bright_steel,
            name="brake_rotor",
        )
        hub.visual(
            Cylinder(radius=0.042, length=0.040),
            origin=_origin_y(side_sign * 0.126),
            material=bearing_dark,
            name="center_cap",
        )
        for stud in range(5):
            angle = 2.0 * math.pi * stud / 5.0
            hub.visual(
                Cylinder(radius=0.0065, length=0.030),
                origin=Origin(
                    xyz=(
                        0.072 * math.cos(angle),
                        side_sign * 0.115,
                        0.072 * math.sin(angle),
                    ),
                    rpy=(-math.pi / 2.0, 0.0, 0.0),
                ),
                material=bolt_yellow,
                name=f"wheel_stud_{stud}",
            )
        model.articulation(
            f"tube_to_{name}",
            ArticulationType.CONTINUOUS,
            parent=tube,
            child=hub,
            origin=Origin(xyz=(0.0, side_sign * 0.890, 0.420)),
            axis=(0.0, side_sign, 0.0),
            motion_limits=MotionLimits(effort=260.0, velocity=80.0),
        )

    add_hub("wheel_hub_0", -1.0)
    add_hub("wheel_hub_1", 1.0)

    model.articulation(
        "chassis_to_tube",
        ArticulationType.FIXED,
        parent=chassis,
        child=tube,
        origin=Origin(),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
