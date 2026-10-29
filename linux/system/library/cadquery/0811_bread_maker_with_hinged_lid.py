# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bread_maker_with_hinged_lid, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bread_maker_with_hinged_lid

from __future__ import annotations

import cadquery as cq
import math
from contextlib import suppress
from dataclasses import dataclass
from math import cos, pi, sin
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

# ===== knobs (9 syms) =====
@dataclass(frozen=True)
class KnobSkirt:
    diameter: float
    height: float
    flare: float = 0.0
    chamfer: float = 0.0

@dataclass(frozen=True)
class KnobGrip:
    style: Literal[
        "none",
        "fluted",
        "scalloped",
        "knurled",
        "ribbed",
        "diamond_knurl",
    ] = "none"
    count: Optional[int] = None
    depth: float = 0.0
    width: Optional[float] = None
    helix_angle_deg: float = 0.0

@dataclass(frozen=True)
class KnobIndicator:
    style: Literal["none", "line", "notch", "wedge", "dot"] = "none"
    length: Optional[float] = None
    width: Optional[float] = None
    depth: float = 0.0
    angle_deg: float = 0.0
    mode: Literal["engraved", "raised"] = "engraved"

@dataclass(frozen=True)
class KnobTopFeature:
    style: Literal["none", "flush_disk", "recessed_disk", "top_insert"] = "none"
    diameter: Optional[float] = None
    depth: float = 0.0
    height: float = 0.0

@dataclass(frozen=True)
class KnobBore:
    style: Literal["none", "round", "d_shaft", "double_d", "splined", "hex"] = "round"
    diameter: Optional[float] = None
    flat_depth: Optional[float] = None
    spline_count: Optional[int] = None
    spline_depth: float = 0.0
    through: bool = True

@dataclass(frozen=True)
class KnobRelief:
    style: Literal["side_window", "top_recess", "coin_slot"]
    angle_deg: float = 0.0
    width: Optional[float] = None
    height: Optional[float] = None
    depth: float = 0.0

def _knobs_loft_between_radii_z(cq_module, radii_and_offsets):
    """Loft a stack of circular sections at given (radius, z-offset) pairs."""
    wp = None
    previous_offset = 0.0
    for radius, offset in radii_and_offsets:
        if wp is None:
            wp = cq_module.Workplane("XY").workplane(offset=offset).circle(radius)
        else:
            wp = wp.workplane(offset=offset - previous_offset).circle(radius)
        previous_offset = offset
    if wp is None:
        raise ValidationError("No loft sections were provided")
    return wp.loft(combine=True, ruled=False)

def _knobs_cut_with_pattern(shape, cutters):
    for cutter in cutters:
        shape = shape.cut(cutter)
    return shape

class KnobGeometry(MeshGeometry):
    """
    Build a flexible rotary knob aligned to local Z with multiple silhouette families.
    """

    def __init__(
        self,
        diameter: float,
        height: float,
        *,
        body_style: Literal[
            "cylindrical",
            "tapered",
            "domed",
            "mushroom",
            "skirted",
            "hourglass",
            "faceted",
            "lobed",
        ] = "cylindrical",
        top_diameter: Optional[float] = None,
        base_diameter: Optional[float] = None,
        crown_radius: float = 0.0,
        edge_radius: float = 0.0,
        side_draft_deg: float = 0.0,
        skirt: Optional[KnobSkirt] = None,
        grip: Optional[KnobGrip] = None,
        indicator: Optional[KnobIndicator] = None,
        top_feature: Optional[KnobTopFeature] = None,
        bore: Optional[KnobBore] = None,
        body_reliefs: Sequence[KnobRelief] = (),
        center: bool = True,
    ):
        super().__init__()
        diameter = float(diameter)
        height = float(height)
        crown_radius = max(0.0, float(crown_radius))
        edge_radius = max(0.0, float(edge_radius))
        side_draft_deg = float(side_draft_deg)
        if diameter <= 0.0 or height <= 0.0:
            raise ValidationError("diameter and height must be positive")
        if abs(side_draft_deg) >= 45.0:
            raise ValidationError("abs(side_draft_deg) must be < 45")

        base_diameter = float(base_diameter) if base_diameter is not None else diameter
        if base_diameter <= 0.0:
            raise ValidationError("base_diameter must be positive")
        top_diameter = float(top_diameter) if top_diameter is not None else diameter
        if top_diameter <= 0.0:
            raise ValidationError("top_diameter must be positive")

        grip = grip or KnobGrip()
        indicator = indicator or KnobIndicator()
        top_feature = top_feature or KnobTopFeature()
        bore = bore or KnobBore(style="none")
        if skirt is not None and (skirt.diameter <= 0.0 or skirt.height <= 0.0):
            raise ValidationError("KnobSkirt diameter and height must be positive")
        if grip.depth < 0.0:
            raise ValidationError("KnobGrip.depth must be non-negative")
        if indicator.depth < 0.0:
            raise ValidationError("KnobIndicator.depth must be non-negative")
        if top_feature.depth < 0.0 or top_feature.height < 0.0:
            raise ValidationError("KnobTopFeature depth/height must be non-negative")
        if bore.diameter is not None and bore.diameter <= 0.0:
            raise ValidationError("KnobBore.diameter must be positive when provided")
        for relief in body_reliefs:
            if relief.depth < 0.0:
                raise ValidationError("KnobRelief.depth must be non-negative")

        body_height = height
        body_bottom = -height * 0.5
        max_radius = max(base_diameter, top_diameter) * 0.5
        if skirt is not None:
            max_radius = max(max_radius, skirt.diameter * 0.5)

        def body_radius_at(t: float) -> float:
            if body_style == "cylindrical":
                return max(base_diameter, top_diameter) * 0.5
            if body_style == "tapered":
                return (base_diameter * (1.0 - t) + top_diameter * t) * 0.5
            if body_style == "domed":
                if t < 0.72:
                    return (base_diameter * 0.5) * (
                        1.0 - min(max(side_draft_deg / 50.0, -0.2), 0.2) * t
                    )
                u = (t - 0.72) / 0.28
                return max(
                    0.001,
                    top_diameter * 0.5 + (base_diameter * 0.5 - top_diameter * 0.5) * (1.0 - u * u),
                )
            if body_style == "mushroom":
                stem_radius = min(base_diameter, top_diameter, diameter) * 0.28
                cap_radius = max(base_diameter, top_diameter, diameter) * 0.5
                if t < 0.42:
                    return stem_radius
                if t < 0.62:
                    u = (t - 0.42) / 0.20
                    return stem_radius + (cap_radius - stem_radius) * u
                if t < 0.85:
                    return cap_radius
                u = (t - 0.85) / 0.15
                return max(cap_radius * (1.0 - 0.20 * u * u), stem_radius)
            if body_style == "skirted":
                skirt_radius = max(base_diameter * 0.55, diameter * 0.52)
                crown_radius_local = top_diameter * 0.5
                if t < 0.40:
                    return skirt_radius
                if t < 0.56:
                    u = (t - 0.40) / 0.16
                    return skirt_radius + (crown_radius_local - skirt_radius) * u
                return crown_radius_local
            if body_style == "hourglass":
                waist_radius = min(base_diameter, top_diameter, diameter) * 0.32
                if t < 0.5:
                    u = t / 0.5
                    return base_diameter * 0.5 + (waist_radius - base_diameter * 0.5) * u
                u = (t - 0.5) / 0.5
                return waist_radius + (top_diameter * 0.5 - waist_radius) * u
            if body_style == "faceted":
                return (base_diameter * (1.0 - t) + top_diameter * t) * 0.5
            if body_style == "lobed":
                lower_radius = base_diameter * 0.5
                upper_radius = max(top_diameter, diameter * 1.02) * 0.5
                if t < 0.24:
                    u = t / 0.24
                    return lower_radius + (upper_radius * 0.92 - lower_radius) * u
                if t < 0.80:
                    u = (t - 0.24) / 0.56
                    return upper_radius * (0.92 + 0.08 * sin(u * pi))
                u = (t - 0.80) / 0.20
                return upper_radius + (top_diameter * 0.5 - upper_radius) * u
            raise ValidationError(f"Unsupported body_style {body_style!r}")

        def section_outline(radius: float, t: float):
            if body_style == "faceted":
                facet_count = 6
                phase = pi / float(facet_count)
                return [
                    (
                        radius * cos(phase + 2.0 * pi * index / float(facet_count)),
                        radius * sin(phase + 2.0 * pi * index / float(facet_count)),
                    )
                    for index in range(facet_count)
                ]
            if body_style == "lobed":
                lobe_count = 5
                point_count = 72
                blend = min(max((t - 0.10) / 0.30, 0.0), 1.0)
                amplitude = radius * (0.04 + 0.14 * blend)
                valley_floor = radius * 0.62
                points = []
                for index in range(point_count):
                    theta = 2.0 * pi * index / float(point_count)
                    local_radius = radius - amplitude * (0.5 - 0.5 * cos(lobe_count * theta))
                    local_radius = max(local_radius, valley_floor)
                    points.append((local_radius * cos(theta), local_radius * sin(theta)))
                return points
            return None

        section_offsets = [
            0.0,
            body_height * 0.18,
            body_height * 0.42,
            body_height * 0.72,
            body_height,
        ]
        radii_and_offsets = [
            (max(0.001, body_radius_at(offset / body_height)), body_bottom + offset)
            for offset in section_offsets
        ]
        wp = None
        previous_offset = 0.0
        for radius, offset in radii_and_offsets:
            t = (offset - body_bottom) / body_height if body_height > 1e-9 else 0.0
            profile_points = section_outline(radius, t)
            if wp is None:
                wp = cq.Workplane("XY").workplane(offset=offset)
            else:
                wp = wp.workplane(offset=offset - previous_offset)
            if profile_points is None:
                wp = wp.circle(radius)
            else:
                wp = wp.polyline(profile_points).close()
            previous_offset = offset
        if wp is None:
            raise ValidationError("KnobGeometry requires at least one loft section")
        shape = wp.loft(combine=True, ruled=False)

        if skirt is not None:
            skirt_radius = skirt.diameter * 0.5
            skirt_bottom = body_bottom - skirt.height
            skirt_shape = _knobs_loft_between_radii_z(
                cq,
                [
                    (max(0.001, skirt_radius * (1.0 + skirt.flare)), skirt_bottom),
                    (max(0.001, skirt_radius), body_bottom),
                ],
            )
            shape = shape.union(skirt_shape)
            if skirt.chamfer > 1e-6:
                with suppress(Exception):
                    shape = (
                        shape.faces("<Z")
                        .edges()
                        .chamfer(min(skirt.chamfer, skirt.height * 0.7, skirt_radius * 0.25))
                    )

        if edge_radius > 0.0:
            with suppress(Exception):
                shape = shape.edges("|Z").fillet(min(edge_radius, max_radius * 0.35, height * 0.18))
        if crown_radius > 0.0:
            with suppress(Exception):
                shape = (
                    shape.faces(">Z")
                    .edges()
                    .fillet(min(crown_radius, max_radius * 0.25, height * 0.16))
                )

        if grip.style != "none" and grip.depth > 1e-6:
            grip_count = grip.count or (28 if grip.style in {"knurled", "diamond_knurl"} else 18)
            if grip_count < 2:
                raise ValidationError("KnobGrip.count must be at least 2")
            grip_width = (
                float(grip.width)
                if grip.width is not None
                else (
                    max_radius * 0.18
                    if grip.style in {"fluted", "scalloped"}
                    else max_radius * 0.10
                )
            )
            if grip_width <= 0.0:
                raise ValidationError("KnobGrip.width must be positive when provided")

            cutters = []
            if grip.style in {"fluted", "scalloped", "ribbed"}:
                cutter_radius = grip_width * (0.55 if grip.style != "ribbed" else 0.38)
                radial_center = max_radius + cutter_radius - grip.depth
                for index in range(grip_count):
                    cutter = (
                        cq.Workplane("XY")
                        .circle(cutter_radius)
                        .extrude(
                            height + (skirt.height if skirt is not None else 0.0) + 0.01, both=True
                        )
                        .translate((radial_center, 0.0, body_bottom + height * 0.5))
                        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 360.0 * index / float(grip_count))
                    )
                    cutters.append(cutter)
            else:
                tangential = max(grip_width, max_radius * 0.06)
                radial = max(grip.depth * 1.8, max_radius * 0.06)
                box_height = height * 1.25
                helix_angle = grip.helix_angle_deg if abs(grip.helix_angle_deg) > 1e-6 else 24.0
                for index in range(grip_count):
                    base_angle = 360.0 * index / float(grip_count)
                    for tilt_sign in (-1.0, 1.0) if grip.style == "diamond_knurl" else (1.0,):
                        cutter = (
                            cq.Workplane("XY")
                            .box(radial, tangential, box_height)
                            .translate(
                                (max_radius - grip.depth * 0.5, 0.0, body_bottom + height * 0.5)
                            )
                            .rotate(
                                (0.0, 0.0, 0.0), (0.0, 1.0, 0.0), helix_angle * float(tilt_sign)
                            )
                            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), base_angle)
                        )
                        cutters.append(cutter)
            shape = _knobs_cut_with_pattern(shape, cutters)

        if indicator.style != "none":
            indicator_length = indicator.length or max(diameter * 0.34, 0.003)
            indicator_width = indicator.width or max(diameter * 0.06, 0.0015)
            indicator_depth = max(indicator.depth, max(height * 0.03, 0.0008))
            top_z = body_bottom + height
            if indicator.style in {"line", "notch"}:
                feature = (
                    cq.Workplane("XY")
                    .box(indicator_length, indicator_width, indicator_depth)
                    .translate((indicator_length * 0.18, 0.0, top_z + indicator_depth * 0.5))
                )
            elif indicator.style == "wedge":
                profile = [
                    (-indicator_width * 0.5, 0.0),
                    (indicator_width * 0.5, 0.0),
                    (0.0, indicator_length),
                ]
                feature = (
                    cq.Workplane("XY")
                    .polyline(profile)
                    .close()
                    .extrude(indicator_depth)
                    .translate((0.0, 0.0, top_z))
                )
            else:
                dot_radius = indicator_width * 0.5
                feature = (
                    cq.Workplane("XY")
                    .circle(dot_radius)
                    .extrude(indicator_depth)
                    .translate((indicator_length * 0.22, 0.0, top_z))
                )
            feature = feature.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), indicator.angle_deg)
            if indicator.mode == "raised" and indicator.style != "notch":
                shape = shape.union(feature)
            else:
                shape = shape.cut(feature.translate((0.0, 0.0, -indicator_depth * 0.5)))

        if top_feature.style != "none":
            feature_diameter = top_feature.diameter or diameter * 0.55
            feature_radius = feature_diameter * 0.5
            top_z = body_bottom + height
            if feature_radius <= 0.0:
                raise ValidationError("KnobTopFeature.diameter must be positive when provided")
            if top_feature.style == "flush_disk":
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.height, height * 0.06))
                    .translate((0.0, 0.0, top_z))
                )
                shape = shape.union(feature)
            elif top_feature.style == "top_insert":
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.height, height * 0.04))
                    .translate((0.0, 0.0, top_z + height * 0.01))
                )
                shape = shape.union(feature)
            else:
                feature = (
                    cq.Workplane("XY")
                    .circle(feature_radius)
                    .extrude(max(top_feature.depth, height * 0.08))
                    .translate((0.0, 0.0, top_z - max(top_feature.depth, height * 0.08)))
                )
                shape = shape.cut(feature)

        if bore.style != "none":
            bore_diameter = bore.diameter or diameter * 0.34
            if bore_diameter <= 0.0 or bore_diameter >= max_radius * 2.0:
                raise ValidationError("KnobBore diameter must fit inside the knob body")
            bore_depth = (
                height + (skirt.height if skirt is not None else 0.0) + 0.01
                if bore.through
                else max(height * 0.7, diameter * 0.22)
            )
            if bore.style == "round":
                bore_cut = cq.Workplane("XY").circle(bore_diameter * 0.5).extrude(bore_depth)
            elif bore.style == "hex":
                bore_cut = cq.Workplane("XY").polygon(6, bore_diameter).extrude(bore_depth)
            elif bore.style in {"d_shaft", "double_d"}:
                flat_depth = (
                    float(bore.flat_depth) if bore.flat_depth is not None else bore_diameter * 0.16
                )
                cut_r = bore_diameter * 0.5
                flat_x = cut_r - flat_depth
                circle_points = [
                    (cut_r * cos(theta), cut_r * sin(theta))
                    for theta in (2.0 * pi * index / 48.0 for index in range(48))
                ]
                if bore.style == "d_shaft":
                    profile_points = [(min(point[0], flat_x), point[1]) for point in circle_points]
                else:
                    profile_points = [
                        (max(min(point[0], flat_x), -flat_x), point[1]) for point in circle_points
                    ]
                bore_cut = cq.Workplane("XY").polyline(profile_points).close().extrude(bore_depth)
            else:
                spline_count = bore.spline_count or 8
                if spline_count < 3:
                    raise ValidationError("KnobBore.spline_count must be at least 3")
                spline_depth = max(bore.spline_depth, bore_diameter * 0.06)
                outer_r = bore_diameter * 0.5
                inner_r = max(outer_r - spline_depth, outer_r * 0.72)
                points = []
                for index in range(spline_count * 2):
                    theta = pi * index / float(spline_count)
                    radius = outer_r if index % 2 == 0 else inner_r
                    points.append((radius * cos(theta), radius * sin(theta)))
                bore_cut = cq.Workplane("XY").polyline(points).close().extrude(bore_depth)
            bore_cut = bore_cut.translate(
                (0.0, 0.0, body_bottom - (skirt.height if skirt is not None else 0.0))
            )
            shape = shape.cut(bore_cut)

        for relief in body_reliefs:
            relief_depth = max(relief.depth, diameter * 0.04)
            relief_width = relief.width or diameter * 0.22
            relief_height = relief.height or height * 0.18
            if relief.style == "side_window":
                cutter = (
                    cq.Workplane("XY")
                    .box(relief_depth * 2.2, relief_width, relief_height)
                    .translate((max_radius - relief_depth * 0.55, 0.0, body_bottom + height * 0.55))
                    .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), relief.angle_deg)
                )
                shape = shape.cut(cutter)
            elif relief.style == "top_recess":
                cutter = (
                    cq.Workplane("XY")
                    .circle(relief_width * 0.5)
                    .extrude(relief_depth)
                    .translate((0.0, 0.0, body_bottom + height - relief_depth))
                )
                shape = shape.cut(cutter)
            else:
                cutter = (
                    cq.Workplane("XY")
                    .box(relief_width, relief_width * 0.24, relief_depth)
                    .translate((0.0, 0.0, body_bottom + height - relief_depth * 0.5))
                    .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), relief.angle_deg)
                )
                shape = shape.cut(cutter)

        solid = _to_shape(shape)
        if not center:
            bb = solid.BoundingBox()
            solid = solid.translate(cq.Vector(0.0, 0.0, -bb.zmin))
        self._set(solid)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
import cadquery as cq
BODY_D = 0.290
BODY_W = 0.220
BODY_H = 0.320
BODY_RADIUS = 0.018
FLOOR = 0.008
CHAMBER_D = 0.172
CHAMBER_W = 0.112
CHAMBER_X = 0.004
CHAMBER_Y = -0.028
LINER_THICKNESS = 0.0012
LID_D = 0.196
LID_W = 0.154
LID_H = 0.032
PANEL_X = 0.052
PANEL_Z = 0.202
PANEL_FLOOR_Y = BODY_W / 2.0
KNOB_X = PANEL_X - 0.022
KNOB_Z = PANEL_Z + 0.017
BUTTON_X = PANEL_X + 0.030
BUTTON_ZS = (PANEL_Z + 0.024, PANEL_Z - 0.022)
PADDLE_X = 0.010
PADDLE_Y = CHAMBER_Y
SPINDLE_Z = FLOOR + 0.002
PLUNGER_Z = BODY_H - 0.052
def _build_body_shape() -> cq.Workplane:
    body = cq.Workplane("XY").box(BODY_D, BODY_W, BODY_H, centered=(True, True, False))
    body = body.edges("|Z").fillet(BODY_RADIUS)
    body = body.edges(">Z").fillet(0.007)

    chamber = (
        cq.Workplane("XY")
        .box(CHAMBER_D, CHAMBER_W, BODY_H, centered=(True, True, False))
        .translate((CHAMBER_X, CHAMBER_Y, FLOOR))
    )
    body = body.cut(chamber)

    knob_hole = (
        cq.Workplane("XY")
        .box(0.016, 0.042, 0.016, centered=(True, True, True))
        .translate((KNOB_X, PANEL_FLOOR_Y - 0.011, KNOB_Z))
    )
    body = body.cut(knob_hole)

    for button_z in BUTTON_ZS:
        button_hole = (
            cq.Workplane("XY")
            .box(0.018, 0.040, 0.018, centered=(True, True, True))
            .translate((BUTTON_X, PANEL_FLOOR_Y - 0.010, button_z))
        )
        body = body.cut(button_hole)

    front_slot = (
        cq.Workplane("XY")
        .box(0.032, 0.020, 0.020, centered=(True, True, True))
        .translate((BODY_D / 2.0 - 0.007, CHAMBER_Y, PLUNGER_Z))
    )
    body = body.cut(front_slot)

    return cq.Workplane(obj=body.val())
def _build_lid_shape() -> cq.Workplane:
    shell = cq.Workplane("XY").box(LID_D, LID_W, LID_H, centered=(False, True, False))
    shell = shell.edges("|Z").fillet(0.010)
    shell = shell.edges(">Z").fillet(0.005)

    inner = (
        cq.Workplane("XY")
        .box(LID_D - 0.016, LID_W - 0.016, LID_H - 0.003, centered=(False, True, False))
        .translate((0.008, 0.0, 0.0))
    )
    shell = shell.cut(inner)

    grip = (
        cq.Workplane("XY")
        .box(0.034, 0.074, 0.010, centered=(False, True, False))
        .translate((LID_D - 0.052, 0.0, LID_H - 0.007))
    )
    return shell.union(grip)
def _build_paddle_shape() -> cq.Workplane:
    hub = (
        cq.Workplane("XY")
        .circle(0.009)
        .extrude(0.016)
        .translate((0.0, 0.0, 0.001))
    )
    blade = (
        cq.Workplane("XY")
        .box(0.046, 0.016, 0.006, centered=(True, True, False))
        .translate((0.002, 0.0, 0.004))
    )
    fin = (
        cq.Workplane("XY")
        .box(0.022, 0.010, 0.010, centered=(True, True, False))
        .translate((0.010, 0.0, 0.010))
    )
    paddle = hub.union(blade).union(fin)
    bore = cq.Workplane("XY").circle(0.0065).extrude(0.024)
    return paddle.cut(bore)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bread_maker")

    shell_white = model.material("shell_white", rgba=(0.92, 0.92, 0.90, 1.0))
    trim_grey = model.material("trim_grey", rgba=(0.70, 0.72, 0.73, 1.0))
    liner_metal = model.material("liner_metal", rgba=(0.83, 0.84, 0.86, 1.0))
    dark_grey = model.material("dark_grey", rgba=(0.18, 0.19, 0.20, 1.0))
    button_grey = model.material("button_grey", rgba=(0.82, 0.84, 0.85, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shape(), "bread_maker_body"),
        material=shell_white,
        name="shell",
    )
    body.visual(
        Box((CHAMBER_D - 0.012, CHAMBER_W - 0.012, 0.002)),
        origin=Origin(xyz=(CHAMBER_X, CHAMBER_Y, FLOOR + 0.001)),
        material=liner_metal,
        name="liner_floor",
    )
    liner_height = BODY_H - FLOOR - 0.015
    liner_z = FLOOR + liner_height / 2.0 - 0.0005
    body.visual(
        Box((CHAMBER_D - 0.008, LINER_THICKNESS, liner_height)),
        origin=Origin(
            xyz=(
                CHAMBER_X,
                CHAMBER_Y - (CHAMBER_W - LINER_THICKNESS) / 2.0,
                liner_z,
            )
        ),
        material=liner_metal,
        name="liner_left",
    )
    body.visual(
        Box((CHAMBER_D - 0.008, LINER_THICKNESS, liner_height)),
        origin=Origin(
            xyz=(
                CHAMBER_X,
                CHAMBER_Y + (CHAMBER_W - LINER_THICKNESS) / 2.0,
                liner_z,
            )
        ),
        material=liner_metal,
        name="liner_right",
    )
    body.visual(
        Box((LINER_THICKNESS, CHAMBER_W - 0.008, liner_height)),
        origin=Origin(
            xyz=(
                CHAMBER_X - (CHAMBER_D - LINER_THICKNESS) / 2.0,
                CHAMBER_Y,
                liner_z,
            )
        ),
        material=liner_metal,
        name="liner_rear",
    )
    body.visual(
        Box((LINER_THICKNESS, CHAMBER_W - 0.008, liner_height)),
        origin=Origin(
            xyz=(
                CHAMBER_X + (CHAMBER_D - LINER_THICKNESS) / 2.0,
                CHAMBER_Y,
                liner_z,
            )
        ),
        material=liner_metal,
        name="liner_front",
    )
    body.visual(
        Cylinder(radius=0.0082, length=0.002),
        origin=Origin(xyz=(PADDLE_X, PADDLE_Y, SPINDLE_Z + 0.001)),
        material=trim_grey,
        name="spindle_seat",
    )
    body.visual(
        Cylinder(radius=0.0058, length=0.018),
        origin=Origin(xyz=(PADDLE_X, PADDLE_Y, SPINDLE_Z + 0.010)),
        material=dark_grey,
        name="spindle",
    )
    body.inertial = Inertial.from_geometry(
        Box((BODY_D, BODY_W, BODY_H)),
        mass=4.8,
        origin=Origin(xyz=(0.0, 0.0, BODY_H / 2.0)),
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_build_lid_shape(), "bread_maker_lid"),
        origin=Origin(xyz=(0.0, 0.0, 0.0004)),
        material=shell_white,
        name="lid_shell",
    )
    lid.inertial = Inertial.from_geometry(
        Box((LID_D, LID_W, LID_H)),
        mass=0.65,
        origin=Origin(xyz=(LID_D / 2.0, 0.0, LID_H / 2.0)),
    )

    paddle = model.part("paddle")
    paddle.visual(
        mesh_from_cadquery(_build_paddle_shape(), "kneading_paddle"),
        material=dark_grey,
        name="paddle_body",
    )
    paddle.visual(
        Box((0.010, 0.006, 0.008)),
        origin=Origin(xyz=(0.020, 0.0, 0.015)),
        material=trim_grey,
        name="paddle_fin",
    )
    paddle.inertial = Inertial.from_geometry(
        Box((0.050, 0.018, 0.020)),
        mass=0.10,
        origin=Origin(xyz=(0.005, 0.0, 0.010)),
    )

    timer_knob = model.part("timer_knob")
    timer_knob.visual(
        mesh_from_geometry(
            KnobGeometry(
                0.040,
                0.018,
                body_style="skirted",
                top_diameter=0.031,
                skirt=KnobSkirt(0.046, 0.004, flare=0.06),
                grip=KnobGrip(style="fluted", count=14, depth=0.0011),
                indicator=KnobIndicator(style="line", mode="raised", angle_deg=0.0),
                center=False,
            ),
            "bread_maker_timer_knob",
        ),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_grey,
        name="knob_shell",
    )
    timer_knob.visual(
        Cylinder(radius=0.0042, length=0.016),
        origin=Origin(xyz=(0.0, -0.008, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=trim_grey,
        name="shaft",
    )
    timer_knob.visual(
        Box((0.006, 0.002, 0.004)),
        origin=Origin(xyz=(0.0, 0.017, 0.014)),
        material=button_grey,
        name="pointer",
    )
    timer_knob.inertial = Inertial.from_geometry(
        Box((0.046, 0.020, 0.040)),
        mass=0.05,
        origin=Origin(xyz=(0.0, 0.004, 0.0)),
    )

    for index, button_z in enumerate(BUTTON_ZS):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.022, 0.006, 0.022)),
            origin=Origin(xyz=(0.0, 0.003, 0.0)),
            material=button_grey,
            name="cap",
        )
        button.visual(
            Box((0.015, 0.018, 0.015)),
            origin=Origin(xyz=(0.0, -0.009, 0.0)),
            material=dark_grey,
            name="stem",
        )
        button.inertial = Inertial.from_geometry(Box((0.022, 0.022, 0.022)), mass=0.02)
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(BUTTON_X, PANEL_FLOOR_Y, button_z)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.08,
                lower=0.0,
                upper=0.005,
            ),
        )

    release_plunger = model.part("release_plunger")
    release_plunger.visual(
        Box((0.006, 0.022, 0.022)),
        origin=Origin(xyz=(0.003, 0.0, 0.0)),
        material=button_grey,
        name="cap",
    )
    release_plunger.visual(
        Box((0.020, 0.010, 0.010)),
        origin=Origin(xyz=(-0.010, 0.0, 0.0)),
        material=dark_grey,
        name="stem",
    )
    release_plunger.inertial = Inertial.from_geometry(Box((0.026, 0.022, 0.022)), mass=0.03)

    model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(
            xyz=(
                CHAMBER_X - LID_D / 2.0,
                CHAMBER_Y,
                BODY_H - 0.0005,
            )
        ),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.2,
            lower=0.0,
            upper=math.radians(112.0),
        ),
    )
    model.articulation(
        "body_to_paddle",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=paddle,
        origin=Origin(xyz=(PADDLE_X, PADDLE_Y, SPINDLE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=18.0),
    )
    model.articulation(
        "body_to_timer_knob",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=timer_knob,
        origin=Origin(xyz=(KNOB_X, PANEL_FLOOR_Y, KNOB_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=8.0),
    )
    model.articulation(
        "body_to_release_plunger",
        ArticulationType.PRISMATIC,
        parent=body,
        child=release_plunger,
        origin=Origin(xyz=(BODY_D / 2.0 - 0.001, CHAMBER_Y, PLUNGER_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=0.08,
            lower=0.0,
            upper=0.010,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
