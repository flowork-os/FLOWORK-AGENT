# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
def _add_quad(geom: MeshGeometry, a: int, b: int, c: int, d: int) -> None:
    geom.add_face(a, b, c)
    geom.add_face(a, c, d)
def _open_frustum_shell(
    *,
    rear_radius: float,
    front_radius: float,
    length: float,
    wall: float,
    segments: int = 40,
) -> MeshGeometry:
    geom = MeshGeometry()

    outer_rear: list[int] = []
    outer_front: list[int] = []
    inner_front: list[int] = []
    inner_rear: list[int] = []

    inner_rear_radius = max(rear_radius - wall, wall * 0.6)
    inner_front_radius = max(front_radius - wall, wall * 0.6)

    for index in range(segments):
        angle = 2.0 * pi * index / segments
        c = cos(angle)
        s = sin(angle)
        outer_rear.append(geom.add_vertex(0.0, rear_radius * c, rear_radius * s))
        outer_front.append(geom.add_vertex(length, front_radius * c, front_radius * s))
        inner_front.append(geom.add_vertex(length, inner_front_radius * c, inner_front_radius * s))
        inner_rear.append(geom.add_vertex(0.0, inner_rear_radius * c, inner_rear_radius * s))

    for index in range(segments):
        nxt = (index + 1) % segments
        _add_quad(geom, outer_rear[index], outer_rear[nxt], outer_front[nxt], outer_front[index])
        _add_quad(geom, inner_front[index], inner_front[nxt], inner_rear[nxt], inner_rear[index])
        _add_quad(geom, outer_rear[index], inner_rear[index], inner_rear[nxt], outer_rear[nxt])

    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="industrial_machine_lamp")

    painted_steel = model.material("painted_steel", rgba=(0.43, 0.46, 0.48, 1.0))
    dark_cast = model.material("dark_cast", rgba=(0.20, 0.21, 0.23, 1.0))
    shade_green = model.material("shade_green", rgba=(0.19, 0.31, 0.22, 1.0))
    black_trim = model.material("black_trim", rgba=(0.08, 0.08, 0.09, 1.0))
    brushed_aluminum = model.material("brushed_aluminum", rgba=(0.76, 0.77, 0.79, 1.0))

    clamp_base = model.part("clamp_base")
    clamp_base.inertial = Inertial.from_geometry(
        Box((0.18, 0.12, 0.35)),
        mass=4.2,
        origin=Origin(xyz=(0.02, 0.0, -0.17)),
    )
    clamp_base.visual(
        Cylinder(radius=0.024, length=0.22),
        origin=Origin(xyz=(-0.050, 0.0, -0.110)),
        material=dark_cast,
        name="support_post",
    )
    clamp_base.visual(
        Box((0.072, 0.104, 0.088)),
        origin=Origin(xyz=(-0.012, 0.0, -0.205)),
        material=dark_cast,
        name="clamp_body",
    )
    clamp_base.visual(
        Box((0.120, 0.050, 0.018)),
        origin=Origin(xyz=(0.046, 0.0, -0.162)),
        material=painted_steel,
        name="top_jaw",
    )
    clamp_base.visual(
        Cylinder(radius=0.007, length=0.132),
        origin=Origin(xyz=(0.020, 0.0, -0.274), rpy=(0.0, pi / 2.0, 0.0)),
        material=brushed_aluminum,
        name="clamp_screw",
    )
    clamp_base.visual(
        Box((0.050, 0.060, 0.044)),
        origin=Origin(xyz=(-0.005, 0.0, -0.269)),
        material=dark_cast,
        name="screw_block",
    )
    clamp_base.visual(
        Cylinder(radius=0.0045, length=0.086),
        origin=Origin(xyz=(-0.046, 0.0, -0.274), rpy=(pi / 2.0, 0.0, 0.0)),
        material=black_trim,
        name="clamp_handle",
    )
    clamp_base.visual(
        Cylinder(radius=0.007, length=0.058),
        origin=Origin(xyz=(0.086, 0.0, -0.304)),
        material=brushed_aluminum,
        name="pad_stem",
    )
    clamp_base.visual(
        Cylinder(radius=0.024, length=0.010),
        origin=Origin(xyz=(0.086, 0.0, -0.338)),
        material=black_trim,
        name="pressure_pad",
    )
    clamp_base.visual(
        Box((0.036, 0.014, 0.050)),
        origin=Origin(xyz=(0.000, 0.027, 0.000)),
        material=dark_cast,
        name="left_shoulder_ear",
    )
    clamp_base.visual(
        Box((0.036, 0.014, 0.050)),
        origin=Origin(xyz=(0.000, -0.027, 0.000)),
        material=dark_cast,
        name="right_shoulder_ear",
    )
    clamp_base.visual(
        Box((0.032, 0.068, 0.016)),
        origin=Origin(xyz=(-0.010, 0.0, -0.031)),
        material=dark_cast,
        name="shoulder_bridge",
    )
    clamp_base.visual(
        Box((0.050, 0.084, 0.034)),
        origin=Origin(xyz=(-0.028, 0.0, -0.060)),
        material=dark_cast,
        name="pivot_carrier",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.inertial = Inertial.from_geometry(
        Box((0.44, 0.07, 0.06)),
        mass=1.5,
        origin=Origin(xyz=(0.215, 0.0, 0.0)),
    )
    lower_arm.visual(
        Cylinder(radius=0.018, length=0.040),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=painted_steel,
        name="rear_hub",
    )
    lower_arm.visual(
        Box((0.076, 0.036, 0.032)),
        origin=Origin(xyz=(0.038, 0.0, 0.0)),
        material=painted_steel,
        name="rear_transition",
    )
    lower_arm.visual(
        Box((0.300, 0.036, 0.026)),
        origin=Origin(xyz=(0.200, 0.0, 0.0)),
        material=painted_steel,
        name="main_beam",
    )
    lower_arm.visual(
        Box((0.056, 0.014, 0.048)),
        origin=Origin(xyz=(0.392, 0.027, 0.0)),
        material=painted_steel,
        name="left_elbow_ear",
    )
    lower_arm.visual(
        Box((0.056, 0.014, 0.048)),
        origin=Origin(xyz=(0.392, -0.027, 0.0)),
        material=painted_steel,
        name="right_elbow_ear",
    )
    lower_arm.visual(
        Box((0.048, 0.068, 0.012)),
        origin=Origin(xyz=(0.384, 0.0, -0.028)),
        material=painted_steel,
        name="elbow_bridge",
    )
    lower_arm.visual(
        Box((0.044, 0.068, 0.020)),
        origin=Origin(xyz=(0.348, 0.0, -0.018)),
        material=painted_steel,
        name="elbow_web",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.inertial = Inertial.from_geometry(
        Box((0.39, 0.07, 0.06)),
        mass=1.2,
        origin=Origin(xyz=(0.185, 0.0, 0.0)),
    )
    upper_arm.visual(
        Cylinder(radius=0.018, length=0.040),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=painted_steel,
        name="rear_hub",
    )
    upper_arm.visual(
        Box((0.072, 0.036, 0.032)),
        origin=Origin(xyz=(0.036, 0.0, 0.0)),
        material=painted_steel,
        name="rear_transition",
    )
    upper_arm.visual(
        Box((0.260, 0.036, 0.024)),
        origin=Origin(xyz=(0.170, 0.0, 0.0)),
        material=painted_steel,
        name="main_beam",
    )
    upper_arm.visual(
        Box((0.054, 0.014, 0.046)),
        origin=Origin(xyz=(0.342, 0.027, 0.0)),
        material=painted_steel,
        name="left_tip_ear",
    )
    upper_arm.visual(
        Box((0.054, 0.014, 0.046)),
        origin=Origin(xyz=(0.342, -0.027, 0.0)),
        material=painted_steel,
        name="right_tip_ear",
    )
    upper_arm.visual(
        Box((0.044, 0.068, 0.012)),
        origin=Origin(xyz=(0.336, 0.0, -0.028)),
        material=painted_steel,
        name="tip_bridge",
    )
    upper_arm.visual(
        Box((0.040, 0.068, 0.020)),
        origin=Origin(xyz=(0.306, 0.0, -0.018)),
        material=painted_steel,
        name="tip_web",
    )

    lamp_shade = model.part("lamp_shade")
    lamp_shade.inertial = Inertial.from_geometry(
        Box((0.24, 0.20, 0.20)),
        mass=0.9,
        origin=Origin(xyz=(0.120, 0.0, 0.0)),
    )
    lamp_shade.visual(
        Cylinder(radius=0.017, length=0.040),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=black_trim,
        name="hinge_barrel",
    )
    lamp_shade.visual(
        Cylinder(radius=0.018, length=0.090),
        origin=Origin(xyz=(0.055, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=black_trim,
        name="neck_tube",
    )
    lamp_shade.visual(
        Cylinder(radius=0.050, length=0.044),
        origin=Origin(xyz=(0.074, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=black_trim,
        name="socket_housing",
    )
    shade_shell_mesh = mesh_from_geometry(
        _open_frustum_shell(
            rear_radius=0.054,
            front_radius=0.100,
            length=0.160,
            wall=0.006,
            segments=44,
        ),
        "shade_shell",
    )
    lamp_shade.visual(
        shade_shell_mesh,
        origin=Origin(xyz=(0.062, 0.0, 0.0)),
        material=shade_green,
        name="shade_shell",
    )
    model.articulation(
        "shoulder_joint",
        ArticulationType.REVOLUTE,
        parent=clamp_base,
        child=lower_arm,
        origin=Origin(),
        # The lower arm extends along +X from the shoulder, so -Y raises it.
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=20.0,
            velocity=1.2,
            lower=-0.75,
            upper=1.20,
        ),
    )
    model.articulation(
        "elbow_joint",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=(0.400, 0.0, 0.0)),
        # The upper arm also extends along +X from the elbow, so -Y lifts it.
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=16.0,
            velocity=1.5,
            lower=-0.15,
            upper=1.70,
        ),
    )
    model.articulation(
        "shade_tilt",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=lamp_shade,
        origin=Origin(xyz=(0.350, 0.0, 0.0)),
        # The shade extends along +X from the hinge, so +Y tips it downward.
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=1.6,
            lower=-0.90,
            upper=0.75,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
