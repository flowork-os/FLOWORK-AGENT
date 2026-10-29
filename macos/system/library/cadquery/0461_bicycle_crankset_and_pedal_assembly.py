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
def _extruded_yz_polygon(points: list[tuple[float, float]], x0: float, x1: float) -> MeshGeometry:
    """Extrude a simple CCW polygon in the YZ plane between two X planes."""
    geom = MeshGeometry()
    n = len(points)
    left = [geom.add_vertex(x0, y, z) for y, z in points]
    right = [geom.add_vertex(x1, y, z) for y, z in points]

    for i in range(1, n - 1):
        geom.add_face(left[0], left[i], left[i + 1])
        geom.add_face(right[0], right[i + 1], right[i])

    for i in range(n):
        j = (i + 1) % n
        geom.add_face(left[i], right[i], right[j])
        geom.add_face(left[i], right[j], left[j])
    return geom
def _annular_plate_x(
    *,
    x_center: float,
    thickness: float,
    inner_radius: float,
    root_radius: float,
    tip_radius: float,
    teeth: int,
) -> MeshGeometry:
    """A thin chainring-like annular plate in the YZ plane, with alternating tooth tips."""
    geom = MeshGeometry()
    count = teeth * 2
    x_back = x_center - thickness / 2.0
    x_front = x_center + thickness / 2.0
    outer_back: list[int] = []
    inner_back: list[int] = []
    outer_front: list[int] = []
    inner_front: list[int] = []

    for i in range(count):
        a = 2.0 * math.pi * i / count
        # Tooth tips are a little swept forward so the ring reads like a real chainring.
        radius = tip_radius if i % 2 == 0 else root_radius
        y = radius * math.cos(a)
        z = radius * math.sin(a)
        yi = inner_radius * math.cos(a)
        zi = inner_radius * math.sin(a)
        outer_back.append(geom.add_vertex(x_back, y, z))
        inner_back.append(geom.add_vertex(x_back, yi, zi))
        outer_front.append(geom.add_vertex(x_front, y, z))
        inner_front.append(geom.add_vertex(x_front, yi, zi))

    for i in range(count):
        j = (i + 1) % count
        # Back and front annular faces.
        geom.add_face(outer_back[i], outer_back[j], inner_back[j])
        geom.add_face(outer_back[i], inner_back[j], inner_back[i])
        geom.add_face(outer_front[i], inner_front[j], outer_front[j])
        geom.add_face(outer_front[i], inner_front[i], inner_front[j])
        # Tooth outer wall and inner bore wall.
        geom.add_face(outer_back[i], outer_front[i], outer_front[j])
        geom.add_face(outer_back[i], outer_front[j], outer_back[j])
        geom.add_face(inner_back[i], inner_back[j], inner_front[j])
        geom.add_face(inner_back[i], inner_front[j], inner_front[i])
    return geom
def _stepped_tube_x(
    sections: list[tuple[float, float, float]],
    *,
    segments: int = 72,
) -> MeshGeometry:
    """Connected stepped tube mesh along X. Each section is (x, inner_r, outer_r)."""
    geom = MeshGeometry()
    outer: list[list[int]] = []
    inner: list[list[int]] = []
    for x, inner_r, outer_r in sections:
        outer_ring: list[int] = []
        inner_ring: list[int] = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ca = math.cos(a)
            sa = math.sin(a)
            outer_ring.append(geom.add_vertex(x, outer_r * ca, outer_r * sa))
            inner_ring.append(geom.add_vertex(x, inner_r * ca, inner_r * sa))
        outer.append(outer_ring)
        inner.append(inner_ring)

    for s in range(len(sections) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            geom.add_face(outer[s][i], outer[s + 1][i], outer[s + 1][j])
            geom.add_face(outer[s][i], outer[s + 1][j], outer[s][j])
            geom.add_face(inner[s][i], inner[s][j], inner[s + 1][j])
            geom.add_face(inner[s][i], inner[s + 1][j], inner[s + 1][i])

    # End caps connect outer and inner walls while leaving the bore open.
    for ring_index in (0, len(sections) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            if ring_index == 0:
                geom.add_face(outer[ring_index][i], inner[ring_index][j], inner[ring_index][i])
                geom.add_face(outer[ring_index][i], outer[ring_index][j], inner[ring_index][j])
            else:
                geom.add_face(outer[ring_index][i], inner[ring_index][i], inner[ring_index][j])
                geom.add_face(outer[ring_index][i], inner[ring_index][j], outer[ring_index][j])
    return geom
def _spider_plate_x(
    *,
    x_center: float,
    thickness: float,
    arms: int = 4,
    valley_radius: float = 0.035,
    peak_radius: float = 0.081,
    samples: int = 160,
    phase: float = math.radians(45.0),
) -> MeshGeometry:
    points: list[tuple[float, float]] = []
    for i in range(samples):
        a = 2.0 * math.pi * i / samples
        lobe = max(0.0, math.cos(arms * (a - phase)))
        radius = valley_radius + (peak_radius - valley_radius) * (lobe**3.0)
        points.append((radius * math.cos(a), radius * math.sin(a)))
    return _extruded_yz_polygon(points, x_center - thickness / 2.0, x_center + thickness / 2.0)
def _crank_arm_plate_x(
    *,
    x_center: float,
    thickness: float,
    length: float,
    direction: float,
    root_width: float = 0.038,
    tip_width: float = 0.027,
) -> MeshGeometry:
    """Tapered rounded-ended arm extending along +/-Z in the YZ plane."""
    root_z = direction * 0.026
    tip_z = direction * length
    pts: list[tuple[float, float]] = []

    # One side of the tapered blade.
    pts.append((-root_width / 2.0, root_z))
    pts.append((-tip_width / 2.0, tip_z - direction * tip_width / 2.0))

    # Rounded pedal end.
    center_z = tip_z
    if direction < 0.0:
        angles = [math.pi + t * math.pi / 10.0 for t in range(11)]
    else:
        angles = [0.0 + t * math.pi / 10.0 for t in range(11)]
    for a in angles:
        pts.append((math.cos(a) * tip_width / 2.0, center_z + direction * math.sin(a) * tip_width / 2.0))

    pts.append((tip_width / 2.0, tip_z - direction * tip_width / 2.0))
    pts.append((root_width / 2.0, root_z))
    # Broad scalloped root so the blade visibly grows into the spindle boss.
    pts.append((root_width * 0.45, direction * 0.005))
    pts.append((0.0, direction * 0.000))
    pts.append((-root_width * 0.45, direction * 0.005))
    return _extruded_yz_polygon(pts, x_center - thickness / 2.0, x_center + thickness / 2.0)
def _bolt_positions(radius: float, count: int = 4, phase: float = math.radians(45.0)) -> list[tuple[float, float]]:
    return [
        (radius * math.cos(phase + 2.0 * math.pi * i / count), radius * math.sin(phase + 2.0 * math.pi * i / count))
        for i in range(count)
    ]
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mountain_bike_crankset")

    alloy = model.material("brushed_alloy", rgba=(0.70, 0.72, 0.70, 1.0))
    dark_alloy = model.material("black_anodized_alloy", rgba=(0.015, 0.017, 0.018, 1.0))
    satin_black = model.material("satin_black", rgba=(0.02, 0.022, 0.025, 1.0))
    steel = model.material("polished_steel", rgba=(0.82, 0.82, 0.78, 1.0))
    bearing = model.material("dark_bearing_rubber", rgba=(0.005, 0.005, 0.006, 1.0))

    bottom_bracket = model.part("bottom_bracket")
    bottom_bracket.visual(
        mesh_from_geometry(
            _stepped_tube_x(
                [
                    (-0.052, 0.0140, 0.035),
                    (-0.044, 0.0140, 0.030),
                    (0.044, 0.0140, 0.030),
                    (0.052, 0.0140, 0.035),
                ]
            ),
            "hollow_bottom_bracket_shell",
        ),
        material=dark_alloy,
        name="hollow_shell",
    )
    bottom_bracket.visual(
        mesh_from_geometry(
            _stepped_tube_x(
                [
                    (-0.053, 0.0118, 0.026),
                    (-0.049, 0.0118, 0.026),
                    (0.049, 0.0118, 0.026),
                    (0.053, 0.0118, 0.026),
                ],
                segments=64,
            ),
            "bearing_seal_lips",
        ),
        material=bearing,
        name="bearing_seals",
    )

    crankset = model.part("crankset")
    crankset.visual(
        Cylinder(radius=0.0110, length=0.182),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="spindle",
    )
    crankset.visual(
        Cylinder(radius=0.033, length=0.056),
        origin=Origin(xyz=(0.080, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=alloy,
        name="drive_hub",
    )
    crankset.visual(
        Cylinder(radius=0.032, length=0.056),
        origin=Origin(xyz=(-0.080, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=alloy,
        name="offside_hub",
    )
    crankset.visual(
        mesh_from_geometry(_spider_plate_x(x_center=0.070, thickness=0.018), "four_arm_spider"),
        material=alloy,
        name="spider",
    )
    crankset.visual(
        mesh_from_geometry(
            _annular_plate_x(
                x_center=0.080,
                thickness=0.004,
                inner_radius=0.071,
                root_radius=0.091,
                tip_radius=0.097,
                teeth=36,
            ),
            "outer_chainring_36t",
        ),
        material=dark_alloy,
        name="outer_chainring",
    )
    crankset.visual(
        mesh_from_geometry(
            _annular_plate_x(
                x_center=0.060,
                thickness=0.004,
                inner_radius=0.050,
                root_radius=0.068,
                tip_radius=0.074,
                teeth=24,
            ),
            "inner_chainring_24t",
        ),
        material=dark_alloy,
        name="inner_chainring",
    )
    crankset.visual(
        mesh_from_geometry(
            _crank_arm_plate_x(x_center=0.099, thickness=0.020, length=0.175, direction=-1.0),
            "wide_drive_crank_arm",
        ),
        material=alloy,
        name="drive_arm",
    )
    crankset.visual(
        mesh_from_geometry(
            _crank_arm_plate_x(x_center=-0.099, thickness=0.020, length=0.175, direction=1.0),
            "wide_offside_crank_arm",
        ),
        material=alloy,
        name="offside_arm",
    )
    crankset.visual(
        Cylinder(radius=0.020, length=0.040),
        origin=Origin(xyz=(0.094, 0.0, -0.175), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=alloy,
        name="drive_pedal_boss",
    )
    crankset.visual(
        Cylinder(radius=0.020, length=0.040),
        origin=Origin(xyz=(-0.094, 0.0, 0.175), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=alloy,
        name="offside_pedal_boss",
    )
    for i, (y, z) in enumerate(_bolt_positions(0.073)):
        crankset.visual(
            Cylinder(radius=0.0048, length=0.026),
            origin=Origin(xyz=(0.070, y, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=steel,
            name=f"chainring_bolt_{i}",
        )

    def add_pedal(part_name: str, direction: float, material: Material) -> None:
        pedal = model.part(part_name)
        pedal.visual(
            Cylinder(radius=0.0048, length=0.066),
            origin=Origin(xyz=(direction * 0.033, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=steel,
            name="stub_axle",
        )
        pedal.visual(
            Box((0.058, 0.090, 0.024)),
            origin=Origin(xyz=(direction * 0.092, 0.0, 0.0)),
            material=material,
            name="clipless_body",
        )
        pedal.visual(
            Box((0.044, 0.010, 0.010)),
            origin=Origin(xyz=(direction * 0.092, -0.024, 0.017)),
            material=steel,
            name="front_cleat_jaw",
        )
        pedal.visual(
            Box((0.044, 0.010, 0.010)),
            origin=Origin(xyz=(direction * 0.092, 0.024, 0.017)),
            material=steel,
            name="rear_cleat_jaw",
        )
        pedal.visual(
            Box((0.040, 0.050, 0.006)),
            origin=Origin(xyz=(direction * 0.092, 0.0, -0.015)),
            material=steel,
            name="lower_retention_plate",
        )
        return None

    add_pedal("drive_pedal", 1.0, satin_black)
    add_pedal("offside_pedal", -1.0, satin_black)

    model.articulation(
        "bottom_bracket_to_crankset",
        ArticulationType.REVOLUTE,
        parent=bottom_bracket,
        child=crankset,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=130.0, velocity=14.0, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "drive_pedal_axle",
        ArticulationType.REVOLUTE,
        parent=crankset,
        child="drive_pedal",
        origin=Origin(xyz=(0.114, 0.0, -0.175)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "offside_pedal_axle",
        ArticulationType.REVOLUTE,
        parent=crankset,
        child="offside_pedal",
        origin=Origin(xyz=(-0.114, 0.0, 0.175)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0, lower=-math.pi, upper=math.pi),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
