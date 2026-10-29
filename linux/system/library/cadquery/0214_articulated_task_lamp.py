# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

from __future__ import annotations

import cadquery as cq
import math
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
from typing import Literal, Optional, Sequence

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

# ===== brackets_hinges_bezels (3 syms) =====
def _brackets_hinges_bezels_shift_to_z0(shape):
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(0.0, 0.0, -bb.zmin))

def _brackets_hinges_bezels_finish(target, model, center):
    shape = _to_shape(model)
    if not center:
        shape = _brackets_hinges_bezels_shift_to_z0(shape)
    target._set(shape)

class ClevisBracketGeometry(MeshGeometry):
    """Build a U-shaped clevis bracket with a bottom base and a transverse pin bore."""

    def __init__(
        self,
        overall_size: Sequence[float],
        *,
        gap_width: float,
        bore_diameter: float,
        bore_center_z: float,
        base_thickness: float,
        corner_radius: float = 0.0,
        center: bool = True,
    ):
        super().__init__()
        width = float(overall_size[0])
        depth = float(overall_size[1])
        height = float(overall_size[2])
        gap_width = float(gap_width)
        bore_diameter = float(bore_diameter)
        bore_center_z = float(bore_center_z)
        base_thickness = float(base_thickness)
        corner_radius = max(0.0, float(corner_radius))

        if width <= 0.0 or depth <= 0.0 or height <= 0.0:
            raise ValueError("overall_size values must be positive")
        if gap_width <= 0.0 or gap_width >= width:
            raise ValueError("gap_width must be positive and less than overall_size[0]")
        cheek_thickness = 0.5 * (width - gap_width)
        if cheek_thickness <= 1e-6:
            raise ValueError("gap_width leaves no side wall material")
        if bore_diameter <= 0.0 or bore_diameter >= min(cheek_thickness * 2.0, depth, height):
            raise ValueError("bore_diameter is too large for the clevis envelope")
        if base_thickness <= 0.0 or base_thickness >= height:
            raise ValueError("base_thickness must be positive and less than overall_size[2]")
        bore_radius = bore_diameter * 0.5
        if bore_center_z - bore_radius <= base_thickness or bore_center_z + bore_radius >= height:
            raise ValueError(
                "bore_center_z must leave material above the base and below the top edge"
            )

        shape = cq.Workplane("XY").box(width, depth, height)
        slot_cut = (
            cq.Workplane("XY")
            .box(gap_width, depth + 0.004, height - base_thickness)
            .translate((0.0, 0.0, base_thickness * 0.5))
        )
        shape = shape.cut(slot_cut)
        if corner_radius > 0.0:
            shape = shape.edges("|Z").fillet(
                min(corner_radius, cheek_thickness * 0.6, depth * 0.25, height * 0.25)
            )

        bore_z = -height * 0.5 + bore_center_z
        bore = (
            cq.Workplane("YZ")
            .circle(bore_radius)
            .extrude(width + 0.01, both=True)
            .translate((0.0, 0.0, bore_z))
        )
        shape = shape.cut(bore)

        _brackets_hinges_bezels_finish(self, shape, center)

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
BASE_RADIUS = 0.14
BASE_THICKNESS = 0.02
PEDESTAL_RADIUS = 0.022
PEDESTAL_HEIGHT = 0.055
LOWER_ARM_LENGTH = 0.70
LOWER_ARM_RADIUS = 0.0105
UPPER_ARM_LENGTH = 0.43
UPPER_ARM_RADIUS = 0.009
SHOULDER_BARREL_RADIUS = 0.008
SHOULDER_BARREL_LENGTH = 0.028
ELBOW_BARREL_RADIUS = 0.0075
ELBOW_BARREL_LENGTH = 0.024
SHOULDER_BORE_CENTER_Z = 0.022
ELBOW_BORE_CENTER_Z = 0.022
LOWER_REST_PITCH = 1.10
UPPER_REST_DROP = 0.65
SHADE_REST_DROP = 0.55
def _shade_body_shape() -> cq.Workplane:
    body_length = 0.19
    rear_overhang = 0.06
    rear_radius = 0.028
    front_radius = 0.057
    wall = 0.0028

    outer = (
        cq.Workplane("YZ")
        .circle(rear_radius)
        .workplane(offset=body_length)
        .circle(front_radius)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("YZ")
        .circle(rear_radius - wall)
        .workplane(offset=body_length)
        .circle(front_radius - wall)
        .loft(combine=True)
        .translate((wall * 1.8, 0.0, 0.0))
    )
    body = outer.cut(inner).translate((-rear_overhang, 0.0, 0.0))

    tail = (
        cq.Workplane("YZ")
        .circle(0.010)
        .extrude(0.020)
        .translate((-rear_overhang - 0.020, 0.0, 0.0))
    )
    return body.union(tail)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="floor_task_lamp")

    model.material("matte_black", rgba=(0.12, 0.12, 0.14, 1.0))
    model.material("graphite", rgba=(0.20, 0.21, 0.23, 1.0))
    model.material("steel", rgba=(0.67, 0.69, 0.72, 1.0))

    base = model.part("base")
    base.visual(
        Cylinder(radius=BASE_RADIUS, length=BASE_THICKNESS),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS / 2.0)),
        material="matte_black",
        name="base_plate",
    )
    base.visual(
        Cylinder(radius=PEDESTAL_RADIUS, length=PEDESTAL_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + PEDESTAL_HEIGHT / 2.0)),
        material="graphite",
        name="pedestal",
    )
    base.visual(
        mesh_from_geometry(
            ClevisBracketGeometry(
                (0.052, 0.046, 0.050),
                gap_width=0.030,
                bore_diameter=0.018,
                bore_center_z=SHOULDER_BORE_CENTER_Z,
                base_thickness=0.012,
                corner_radius=0.003,
                center=False,
            ),
            "shoulder_clevis",
        ),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + PEDESTAL_HEIGHT)),
        material="graphite",
        name="shoulder_clevis",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        Cylinder(radius=SHOULDER_BARREL_RADIUS, length=SHOULDER_BARREL_LENGTH),
        origin=Origin(rpy=(-pi / 2.0, 0.0, 0.0)),
        material="steel",
        name="shoulder_barrel",
    )
    lower_arm.visual(
        Box((0.080, 0.016, 0.016)),
        origin=Origin(xyz=(0.040, 0.0, 0.000)),
        material="graphite",
        name="shoulder_web",
    )
    lower_arm.visual(
        Cylinder(radius=LOWER_ARM_RADIUS, length=0.58),
        origin=Origin(xyz=(0.355, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="graphite",
        name="lower_tube",
    )
    lower_arm.visual(
        Box((0.090, 0.018, 0.024)),
        origin=Origin(xyz=(0.655, 0.0, -0.012)),
        material="graphite",
        name="elbow_web",
    )
    lower_arm.visual(
        mesh_from_geometry(
            ClevisBracketGeometry(
                (0.060, 0.042, 0.046),
                gap_width=0.028,
                bore_diameter=0.016,
                bore_center_z=ELBOW_BORE_CENTER_Z,
                base_thickness=0.012,
                corner_radius=0.003,
                center=False,
            ),
            "elbow_clevis",
        ),
        origin=Origin(xyz=(LOWER_ARM_LENGTH, 0.0, -ELBOW_BORE_CENTER_Z)),
        material="graphite",
        name="elbow_clevis",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        Cylinder(radius=ELBOW_BARREL_RADIUS, length=ELBOW_BARREL_LENGTH),
        origin=Origin(rpy=(-pi / 2.0, 0.0, 0.0)),
        material="steel",
        name="elbow_barrel",
    )
    upper_arm.visual(
        Box((0.075, 0.014, 0.014)),
        origin=Origin(xyz=(0.0375, 0.0, 0.000)),
        material="graphite",
        name="elbow_web",
    )
    upper_arm.visual(
        Cylinder(radius=UPPER_ARM_RADIUS, length=0.26),
        origin=Origin(xyz=(0.200, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="graphite",
        name="upper_tube",
    )
    upper_arm.visual(
        Box((0.056, 0.104, 0.012)),
        origin=Origin(xyz=(UPPER_ARM_LENGTH - 0.072, 0.0, -0.038)),
        material="graphite",
        name="yoke_bridge",
    )
    upper_arm.visual(
        Box((0.036, 0.016, 0.050)),
        origin=Origin(xyz=(0.318, 0.0, -0.024)),
        material="graphite",
        name="yoke_support",
    )
    upper_arm.visual(
        Box((0.060, 0.008, 0.070)),
        origin=Origin(xyz=(UPPER_ARM_LENGTH - 0.028, -0.045, -0.005)),
        material="graphite",
        name="yoke_arm_0",
    )
    upper_arm.visual(
        Box((0.060, 0.008, 0.070)),
        origin=Origin(xyz=(UPPER_ARM_LENGTH - 0.028, 0.045, -0.005)),
        material="graphite",
        name="yoke_arm_1",
    )

    shade = model.part("shade")
    shade.visual(
        mesh_from_cadquery(_shade_body_shape(), "shade_body"),
        material="matte_black",
        name="shade_body",
    )
    shade.visual(
        Sphere(radius=0.011),
        origin=Origin(xyz=(0.0, -0.029, 0.0)),
        material="graphite",
        name="left_hub",
    )
    shade.visual(
        Sphere(radius=0.011),
        origin=Origin(xyz=(0.0, 0.029, 0.0)),
        material="graphite",
        name="right_hub",
    )
    shade.visual(
        Cylinder(radius=0.0045, length=0.012),
        origin=Origin(xyz=(0.0, -0.035, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="steel",
        name="left_trunnion",
    )
    shade.visual(
        Cylinder(radius=0.0045, length=0.012),
        origin=Origin(xyz=(0.0, 0.035, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="steel",
        name="right_trunnion",
    )

    model.articulation(
        "base_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=base,
        child=lower_arm,
        origin=Origin(
            xyz=(0.0, 0.0, BASE_THICKNESS + PEDESTAL_HEIGHT + SHOULDER_BORE_CENTER_Z),
            rpy=(0.0, -LOWER_REST_PITCH, 0.0),
        ),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-1.10,
            upper=0.55,
            effort=30.0,
            velocity=1.2,
        ),
    )
    model.articulation(
        "lower_arm_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=(LOWER_ARM_LENGTH, 0.0, 0.0), rpy=(0.0, UPPER_REST_DROP, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-1.00,
            upper=1.00,
            effort=18.0,
            velocity=1.4,
        ),
    )
    model.articulation(
        "upper_arm_to_shade",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=shade,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0), rpy=(0.0, SHADE_REST_DROP, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-0.95,
            upper=0.80,
            effort=8.0,
            velocity=1.8,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
