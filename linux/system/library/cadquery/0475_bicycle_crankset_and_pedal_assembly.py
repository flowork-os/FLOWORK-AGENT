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
    sections: list[tuple[float, float]],
    inner_radius: float,
    *,
    segments: int = 80,
) -> MeshGeometry:
    """Stepped hollow tube whose axis is local X."""
    geom = MeshGeometry()
    outer: list[list[int]] = []
    inner: list[list[int]] = []
    for x, outer_radius in sections:
        outer_row: list[int] = []
        inner_row: list[int] = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ca, sa = math.cos(a), math.sin(a)
            outer_row.append(geom.add_vertex(x, outer_radius * ca, outer_radius * sa))
            inner_row.append(geom.add_vertex(x, inner_radius * ca, inner_radius * sa))
        outer.append(outer_row)
        inner.append(inner_row)

    for row in range(len(sections) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            # Outer skin.
            geom.add_face(outer[row][i], outer[row + 1][i], outer[row + 1][j])
            geom.add_face(outer[row][i], outer[row + 1][j], outer[row][j])
            # Inner bore, wound inward.
            geom.add_face(inner[row][i], inner[row + 1][j], inner[row + 1][i])
            geom.add_face(inner[row][i], inner[row][j], inner[row + 1][j])

    # Annular end caps.
    for rings in ((outer[0], inner[0]), (outer[-1], inner[-1])):
        outer_ring, inner_ring = rings
        for i in range(segments):
            j = (i + 1) % segments
            geom.add_face(outer_ring[i], outer_ring[j], inner_ring[j])
            geom.add_face(outer_ring[i], inner_ring[j], inner_ring[i])
    return geom
def _loop_with_hole_x(
    outer_loop: list[tuple[float, float]],
    inner_loop: list[tuple[float, float]],
    thickness: float,
    *,
    x_center: float = 0.0,
) -> MeshGeometry:
    """Extrude matching 2-D YZ loops into a thin plate with one through hole."""
    if len(outer_loop) != len(inner_loop):
        raise ValueError("outer_loop and inner_loop need the same sample count")
    n = len(outer_loop)
    geom = MeshGeometry()
    x0 = x_center - thickness / 2.0
    x1 = x_center + thickness / 2.0

    outer0: list[int] = []
    outer1: list[int] = []
    inner0: list[int] = []
    inner1: list[int] = []
    for y, z in outer_loop:
        outer0.append(geom.add_vertex(x0, y, z))
        outer1.append(geom.add_vertex(x1, y, z))
    for y, z in inner_loop:
        inner0.append(geom.add_vertex(x0, y, z))
        inner1.append(geom.add_vertex(x1, y, z))

    for i in range(n):
        j = (i + 1) % n
        # Front/back annular faces.
        geom.add_face(outer0[i], outer0[j], inner0[j])
        geom.add_face(outer0[i], inner0[j], inner0[i])
        geom.add_face(outer1[i], inner1[j], outer1[j])
        geom.add_face(outer1[i], inner1[i], inner1[j])
        # Outer and inner side walls.
        geom.add_face(outer0[i], outer1[i], outer1[j])
        geom.add_face(outer0[i], outer1[j], outer0[j])
        geom.add_face(inner0[i], inner1[j], inner1[i])
        geom.add_face(inner0[i], inner0[j], inner1[j])
    return geom
def _solid_loop_x(
    loop: list[tuple[float, float]],
    thickness: float,
    *,
    x_center: float = 0.0,
) -> MeshGeometry:
    """Extrude a convex YZ loop into a thin solid plate."""
    n = len(loop)
    geom = MeshGeometry()
    x0 = x_center - thickness / 2.0
    x1 = x_center + thickness / 2.0
    back: list[int] = []
    front: list[int] = []
    for y, z in loop:
        back.append(geom.add_vertex(x0, y, z))
        front.append(geom.add_vertex(x1, y, z))
    c0 = geom.add_vertex(x0, sum(p[0] for p in loop) / n, sum(p[1] for p in loop) / n)
    c1 = geom.add_vertex(x1, sum(p[0] for p in loop) / n, sum(p[1] for p in loop) / n)
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(back[i], front[i], front[j])
        geom.add_face(back[i], front[j], back[j])
        geom.add_face(c0, back[j], back[i])
        geom.add_face(c1, front[i], front[j])
    return geom
def _vertical_capsule_loop(
    *,
    center_z: float,
    length: float,
    width: float,
    samples_per_end: int = 32,
) -> list[tuple[float, float]]:
    """Rounded long slot/profile in the YZ plane."""
    r = width / 2.0
    straight = max(0.0, length - width)
    top_z = center_z + straight / 2.0
    bottom_z = center_z - straight / 2.0
    pts: list[tuple[float, float]] = []
    # Right side bottom-to-top through the top cap, then left side downward.
    for k in range(samples_per_end + 1):
        a = -math.pi / 2.0 + math.pi * k / samples_per_end
        pts.append((r * math.cos(a), top_z + r * math.sin(a)))
    for k in range(samples_per_end + 1):
        a = math.pi / 2.0 + math.pi * k / samples_per_end
        pts.append((r * math.cos(a), bottom_z + r * math.sin(a)))
    return pts
def _oval_tooth_loops(
    *,
    outer_y: float,
    outer_z: float,
    inner_y: float,
    inner_z: float,
    teeth: int = 40,
    samples: int = 160,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    outer: list[tuple[float, float]] = []
    inner: list[tuple[float, float]] = []
    for i in range(samples):
        a = 2.0 * math.pi * i / samples
        tooth_phase = (a * teeth / (2.0 * math.pi)) % 1.0
        # Pointed but small narrow-wide tooth scallop.
        tooth = 1.0 + 0.045 * (1.0 - abs(2.0 * tooth_phase - 1.0))
        outer.append((outer_y * tooth * math.cos(a), outer_z * tooth * math.sin(a)))
        inner.append((inner_y * math.cos(a), inner_z * math.sin(a)))
    return outer, inner
def _spoke_origin(angle: float, radius: float, x: float) -> Origin:
    # Local box Z length is rotated into the YZ radial direction.
    return Origin(xyz=(x, radius * math.sin(angle), radius * math.cos(angle)), rpy=(-angle, 0.0, 0.0))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="gravel_one_by_crankset")

    forged_black = model.material("forged_black", rgba=(0.015, 0.018, 0.020, 1.0))
    satin_graphite = model.material("satin_graphite", rgba=(0.23, 0.24, 0.24, 1.0))
    dark_recess = model.material("dark_recess", rgba=(0.005, 0.006, 0.007, 1.0))
    hard_anodized = model.material("hard_anodized", rgba=(0.04, 0.045, 0.048, 1.0))
    bearing_steel = model.material("bearing_steel", rgba=(0.72, 0.70, 0.66, 1.0))
    spindle_steel = model.material("spindle_steel", rgba=(0.18, 0.19, 0.20, 1.0))
    composite_black = model.material("composite_black", rgba=(0.025, 0.027, 0.030, 1.0))
    spring_steel = model.material("spring_steel", rgba=(0.55, 0.58, 0.58, 1.0))

    shell = model.part("bottom_bracket_shell")
    shell_body = _annular_tube_x(
        [
            (-0.058, 0.046),
            (-0.049, 0.046),
            (-0.049, 0.038),
            (0.049, 0.038),
            (0.049, 0.046),
            (0.058, 0.046),
        ],
        inner_radius=0.021,
        segments=96,
    )
    shell.visual(
        mesh_from_geometry(shell_body, "wide_hollow_bottom_bracket_shell"),
        material=satin_graphite,
        name="shell_body",
    )
    shell.visual(
        mesh_from_geometry(_annular_tube_x([(-0.057, 0.0216), (-0.050, 0.0216)], 0.0135, segments=64), "left_bearing_race"),
        material=bearing_steel,
        name="bearing_race_0",
    )
    shell.visual(
        mesh_from_geometry(_annular_tube_x([(0.050, 0.0216), (0.057, 0.0216)], 0.0135, segments=64), "right_bearing_race"),
        material=bearing_steel,
        name="bearing_race_1",
    )

    crankset = model.part("crankset")
    crankset.visual(
        Cylinder(radius=0.011, length=0.170),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=spindle_steel,
        name="common_spindle",
    )

    # Matching hollow-forged arms: true through-slots in thin forged plates.
    arm_outer_down = _vertical_capsule_loop(center_z=-0.085, length=0.174, width=0.032, samples_per_end=36)
    arm_inner_down = _vertical_capsule_loop(center_z=-0.087, length=0.105, width=0.012, samples_per_end=36)
    arm_outer_up = [(y, -z) for y, z in arm_outer_down]
    arm_inner_up = [(y, -z) for y, z in arm_inner_down]
    crankset.visual(
        mesh_from_geometry(_loop_with_hole_x(arm_outer_down, arm_inner_down, 0.015, x_center=0.067), "right_hollow_crank_arm"),
        material=forged_black,
        name="right_arm",
    )
    crankset.visual(
        mesh_from_geometry(_loop_with_hole_x(arm_outer_up, arm_inner_up, 0.015, x_center=-0.067), "left_hollow_crank_arm"),
        material=forged_black,
        name="left_arm",
    )
    crankset.visual(
        mesh_from_geometry(_solid_loop_x(_vertical_capsule_loop(center_z=-0.090, length=0.100, width=0.014, samples_per_end=18), 0.016, x_center=0.075), "right_recess_shadow"),
        material=dark_recess,
        name="right_arm_recess",
    )
    crankset.visual(
        mesh_from_geometry(_solid_loop_x(_vertical_capsule_loop(center_z=0.090, length=0.100, width=0.014, samples_per_end=18), 0.016, x_center=-0.075), "left_recess_shadow"),
        material=dark_recess,
        name="left_arm_recess",
    )

    # Axle and pedal bosses overlap their own arm plates, as a forged assembly would.
    for x, z, name in (
        (0.067, 0.0, "right_hub_boss"),
        (-0.067, 0.0, "left_hub_boss"),
        (0.067, -0.170, "right_pedal_boss"),
        (-0.067, 0.170, "left_pedal_boss"),
    ):
        crankset.visual(
            Cylinder(radius=0.028 if z == 0.0 else 0.020, length=0.018),
            origin=Origin(xyz=(x, 0.0, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=forged_black,
            name=name,
        )

    # Stub axles for the pedal bodies.  They run inside the hollow pedal bushings.
    crankset.visual(
        Cylinder(radius=0.0055, length=0.060),
        origin=Origin(xyz=(0.101, 0.0, -0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=spindle_steel,
        name="right_pedal_axle",
    )
    crankset.visual(
        Cylinder(radius=0.0055, length=0.060),
        origin=Origin(xyz=(-0.101, 0.0, 0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=spindle_steel,
        name="left_pedal_axle",
    )
    crankset.visual(
        Cylinder(radius=0.010, length=0.002),
        origin=Origin(xyz=(0.077, 0.0, -0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=spindle_steel,
        name="right_axle_collar",
    )
    crankset.visual(
        Cylinder(radius=0.010, length=0.002),
        origin=Origin(xyz=(-0.077, 0.0, 0.170), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=spindle_steel,
        name="left_axle_collar",
    )

    # Right-side direct-mount spider and the wide 40T oval 1x ring.
    for idx, angle in enumerate([0.0, 2.0 * math.pi / 5.0, 4.0 * math.pi / 5.0, 6.0 * math.pi / 5.0, 8.0 * math.pi / 5.0]):
        crankset.visual(
            Box((0.007, 0.013, 0.078)),
            origin=_spoke_origin(angle, 0.050, 0.080),
            material=hard_anodized,
            name=f"spider_spoke_{idx}",
        )
    outer_ring, inner_ring = _oval_tooth_loops(outer_y=0.081, outer_z=0.089, inner_y=0.056, inner_z=0.063)
    crankset.visual(
        mesh_from_geometry(_loop_with_hole_x(outer_ring, inner_ring, 0.0055, x_center=0.086), "forty_tooth_oval_chainring"),
        material=hard_anodized,
        name="oval_chainring",
    )
    crankset.visual(
        Cylinder(radius=0.020, length=0.006),
        origin=Origin(xyz=(0.086, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=hard_anodized,
        name="direct_mount_lockring",
    )

    right_pedal = model.part("right_pedal")
    left_pedal = model.part("left_pedal")
    for part, side in ((right_pedal, 1.0), (left_pedal, -1.0)):
        side_name = "right" if side > 0 else "left"
        part.visual(
            mesh_from_geometry(_annular_tube_x([(-0.030, 0.013), (0.030, 0.013)], 0.0065, segments=48), f"{side_name}_pedal_hollow_bushing"),
            material=spring_steel,
            name="axle_bushing",
        )
        part.visual(
            Box((0.066, 0.010, 0.014)),
            origin=Origin(xyz=(0.0, 0.038, 0.0)),
            material=composite_black,
            name="front_rail",
        )
        part.visual(
            Box((0.066, 0.010, 0.014)),
            origin=Origin(xyz=(0.0, -0.038, 0.0)),
            material=composite_black,
            name="rear_rail",
        )
        part.visual(
            Box((0.052, 0.050, 0.005)),
            origin=Origin(xyz=(0.0, 0.0, 0.018)),
            material=spring_steel,
            name="upper_clip",
        )
        part.visual(
            Box((0.052, 0.050, 0.005)),
            origin=Origin(xyz=(0.0, 0.0, -0.018)),
            material=spring_steel,
            name="lower_clip",
        )
        part.visual(
            Box((0.012, 0.010, 0.032)),
            origin=Origin(xyz=(0.0, 0.028, 0.0)),
            material=spring_steel,
            name="front_clip_post",
        )
        part.visual(
            Box((0.012, 0.010, 0.032)),
            origin=Origin(xyz=(0.0, -0.028, 0.0)),
            material=spring_steel,
            name="rear_clip_post",
        )
        part.visual(
            Box((0.012, 0.070, 0.010)),
            origin=Origin(xyz=(side * 0.033, 0.0, 0.0)),
            material=composite_black,
            name="outer_bridge",
        )

    model.articulation(
        "bottom_bracket_axle",
        ArticulationType.CONTINUOUS,
        parent=shell,
        child=crankset,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=20.0),
        motion_properties=MotionProperties(damping=0.02, friction=0.01),
    )
    model.articulation(
        "right_pedal_axle",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=right_pedal,
        origin=Origin(xyz=(0.108, 0.0, -0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=25.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.004),
    )
    model.articulation(
        "left_pedal_axle",
        ArticulationType.CONTINUOUS,
        parent=crankset,
        child=left_pedal,
        origin=Origin(xyz=(-0.108, 0.0, 0.170)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=25.0),
        motion_properties=MotionProperties(damping=0.01, friction=0.004),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
