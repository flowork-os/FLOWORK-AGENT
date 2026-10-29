# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, adjustable_weight_bench_with_hinged_backrest, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: adjustable_weight_bench_with_hinged_backrest

from __future__ import annotations

import cadquery as cq
import math
from contextlib import suppress
from dataclasses import dataclass
from math import cos, pi, sin
from typing import Literal, Optional, Sequence
from typing import Optional, Sequence, Union

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

def rounded_rect_profile(width, height, radius, *, corner_segments=6):
    width = float(width); height = float(height); radius = float(radius)
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    corner_segments = max(1, int(corner_segments))
    max_r = 0.5 * min(width, height)
    if radius < 0 or radius > max_r:
        raise ValidationError("radius must be within [0, %s]" % max_r)
    hw = width * 0.5; hh = height * 0.5
    if radius <= 1e-12:
        return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    r = radius

    def arc(cx, cy, a0, a1):
        out = []
        for i in range(corner_segments + 1):
            t = i / corner_segments
            a = a0 + (a1 - a0) * t
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return out

    pts = []
    pts.extend(arc(hw - r, -hh + r, -math.pi / 2.0, 0.0))
    pts.extend(arc(hw - r, hh - r, 0.0, math.pi / 2.0)[1:])
    pts.extend(arc(-hw + r, hh - r, math.pi / 2.0, math.pi)[1:])
    pts.extend(arc(-hw + r, -hh + r, math.pi, 3.0 * math.pi / 2.0)[1:])
    return pts

def _extrude_profile(points, height, *, center=True, z0=None):
    """Extrude a closed 2D profile (XY) by height along +Z. Returns cq.Solid."""
    pts = _ensure_ccw(_profile_points_2d(points))
    face = cq.Face.makeFromWires(cq.Wire.makePolygon([cq.Vector(x, y, 0) for (x, y) in pts], close=True))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, float(height)))
    dz = (-height / 2.0 if center else 0.0) if z0 is None else z0
    if dz:
        solid = solid.translate(cq.Vector(0, 0, dz))
    return solid

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

# ===== panels_vents (1 syms) =====
@dataclass(frozen=True)
class BoltPattern:
    count: int
    circle_diameter: float
    hole_diameter: float
    countersink: float = 0.0

# ===== wheels_tires (22 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

def _wheels_tires_clamp(x, low, high):
    return max(low, min(high, x))

def _cq_annulus_x(outer_radius, inner_radius, width):
    return (
        cq.Workplane("YZ")
        .circle(float(outer_radius))
        .circle(max(float(inner_radius), 1.0e-4))
        .extrude(float(width) * 0.5, both=True)
    )

def _wheels_tires_centered_pattern_positions(count, spacing):
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    origin = -0.5 * float(spacing) * float(count - 1)
    return [origin + float(index) * float(spacing) for index in range(count)]

def _wheels_tires_rounded_slot_profile(length, width, *, segments=10):
    radius = width * 0.5
    straight = max(length - width, 0.0)
    half = straight * 0.5
    points = []
    for index in range(segments + 1):
        theta = -pi * 0.5 + pi * (index / float(segments))
        points.append((half + radius * cos(theta), radius * sin(theta)))
    for index in range(segments + 1):
        theta = pi * 0.5 + pi * (index / float(segments))
        points.append((-half + radius * cos(theta), radius * sin(theta)))
    return points

def _wheels_tires_loft_between_radii_z(radii_and_offsets):
    wp = None
    previous_offset = 0.0
    for radius, offset in radii_and_offsets:
        if wp is None:
            wp = cq.Workplane("XY").workplane(offset=offset).circle(radius)
        else:
            wp = wp.workplane(offset=offset - previous_offset).circle(radius)
        previous_offset = offset
    if wp is None:
        raise ValidationError("No loft sections were provided")
    return wp.loft(combine=True, ruled=False)

def _wheels_tires_cut_with_pattern(shape, cutters):
    for cutter in cutters:
        shape = shape.cut(cutter)
    return shape

def _shift_to_x0(shape):
    """Replicate sdk center=False: shift so the body's min X sits on x=0
    (inner mounting side on the origin plane)."""
    xmin = _to_shape(shape).BoundingBox().xmin
    return shape.translate((-xmin, 0.0, 0.0))

@dataclass(frozen=True)
class WheelRim:
    outer_radius: Optional[float] = None
    inner_radius: Optional[float] = None
    flange_height: float = 0.0
    flange_thickness: float = 0.0
    bead_seat_depth: float = 0.0

@dataclass(frozen=True)
class WheelHub:
    radius: float
    width: float
    cap_style: Literal["flat", "domed", "protruding", "recessed"] = "flat"
    bolt_pattern: Optional["BoltPattern"] = None

@dataclass(frozen=True)
class WheelFace:
    dish_depth: float = 0.0
    front_inset: float = 0.0
    rear_inset: float = 0.0
    window_depth: float = 0.0

@dataclass(frozen=True)
class WheelSpokes:
    style: Literal["none", "disc", "solid_slots", "straight", "split_y", "mesh"] = "none"
    count: Optional[int] = None
    thickness: float = 0.0
    window_radius: float = 0.0
    twist_deg: float = 0.0

@dataclass(frozen=True)
class WheelBore:
    style: Literal["round", "keyed", "hex"] = "round"
    diameter: float = 0.0
    key_width: Optional[float] = None

@dataclass(frozen=True)
class TireCarcass:
    crown_radius: Optional[float] = None
    belt_width_ratio: float = 0.34
    sidewall_bulge: float = 0.08

@dataclass(frozen=True)
class TireTread:
    style: Literal["none", "circumferential", "block", "rib", "chevron", "lug"] = "none"
    depth: float = 0.0
    pitch: Optional[float] = None
    count: Optional[int] = None
    angle_deg: float = 0.0
    land_ratio: float = 0.5

@dataclass(frozen=True)
class TireGroove:
    center_offset: float = 0.0
    width: float = 0.0
    depth: float = 0.0

@dataclass(frozen=True)
class TireSidewall:
    style: Literal["flat", "bulged", "square", "rounded"] = "rounded"
    bulge: float = 0.08
    inset_ratio: float = 0.18

@dataclass(frozen=True)
class TireShoulder:
    style: Literal["soft", "square"] = "soft"
    radius: float = 0.0
    width: float = 0.0

class WheelGeometry(MeshGeometry):
    """Build a wheel/rim/hub visual aligned to local X."""

    def __init__(
        self,
        radius: float,
        width: float,
        *,
        rim: Optional[WheelRim] = None,
        hub: Optional[WheelHub] = None,
        face: Optional[WheelFace] = None,
        spokes: Optional[WheelSpokes] = None,
        bore: Optional[WheelBore] = None,
        flange: Optional["WheelFlange"] = None,
        center: bool = True,
    ):
        super().__init__()
        radius = float(radius)
        width = float(width)
        if radius <= 0.0 or width <= 0.0:
            raise ValidationError("radius and width must be positive")

        rim = rim or WheelRim()
        hub = hub or WheelHub(radius=radius * 0.18, width=width * 0.55)
        face = face or WheelFace()
        spokes = spokes or WheelSpokes(style="disc")
        bore = bore or WheelBore(style="round", diameter=max(radius * 0.18, 0.004))

        rim_outer = float(rim.outer_radius) if rim.outer_radius is not None else radius
        rim_inner = float(rim.inner_radius) if rim.inner_radius is not None else radius * 0.68
        if rim_inner <= 0.0 or rim_inner >= rim_outer:
            raise ValidationError("WheelRim.inner_radius must be positive and less than outer_radius")
        if hub.radius <= 0.0 or hub.width <= 0.0 or hub.radius >= rim_inner:
            raise ValidationError("WheelHub dimensions must be positive and fit inside the rim")
        if bore.diameter <= 0.0 or bore.diameter >= hub.radius * 2.0:
            raise ValidationError("WheelBore.diameter must fit inside the hub")

        shape = _cq_annulus_x(rim_outer, rim_inner, width)
        if rim.flange_height > 1e-6 and rim.flange_thickness > 1e-6:
            flange_inner = max(rim_outer - rim.flange_height, rim_inner + 1.0e-4)
            lip = _cq_annulus_x(rim_outer, flange_inner, rim.flange_thickness)
            shape = shape.union(lip.translate((width * 0.5 - rim.flange_thickness * 0.5, 0.0, 0.0)))
            shape = shape.union(
                lip.translate((-(width * 0.5 - rim.flange_thickness * 0.5), 0.0, 0.0))
            )
        if rim.bead_seat_depth > 1e-6:
            seat = _cq_annulus_x(
                rim_outer,
                max(rim_outer - rim.bead_seat_depth, rim_inner + 1.0e-4),
                max(width * 0.22, 0.004),
            )
            shape = shape.cut(seat)

        hub_cyl = cq.Workplane("YZ").circle(hub.radius).extrude(hub.width * 0.5, both=True)
        shape = shape.union(hub_cyl)
        if hub.cap_style == "domed":
            front_cap = (
                _wheels_tires_loft_between_radii_z(
                    [
                        (hub.radius, 0.0),
                        (hub.radius * 0.82, hub.width * 0.12),
                        (hub.radius * 0.30, hub.width * 0.28),
                    ],
                )
                .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
                .translate((hub.width * 0.5, 0.0, 0.0))
            )
            shape = shape.union(front_cap)
        elif hub.cap_style == "protruding":
            cap = cq.Workplane("YZ").circle(hub.radius * 0.82).extrude(max(width * 0.12, 0.003))
            shape = shape.union(cap.translate((hub.width * 0.5, 0.0, 0.0)))
        elif hub.cap_style == "recessed":
            pocket = cq.Workplane("YZ").circle(hub.radius * 0.55).extrude(max(width * 0.10, 0.002))
            shape = shape.cut(
                pocket.translate((hub.width * 0.5 - max(width * 0.10, 0.002), 0.0, 0.0))
            )

        disc_thickness = max(spokes.thickness, width * 0.08, 0.002)
        face_outer_radius = min(
            rim_outer - max(rim.flange_height * 0.25, radius * 0.02),
            rim_inner + (rim_outer - rim_inner) * 0.28 + face.window_depth,
        )
        face_outer_radius = max(face_outer_radius, hub.radius * 1.6)
        front_inset = _wheels_tires_clamp(
            face.front_inset + max(face.dish_depth, 0.0), 0.0, width * 0.5 - disc_thickness * 0.5
        )
        rear_inset = _wheels_tires_clamp(face.rear_inset, 0.0, width * 0.5 - disc_thickness * 0.5)
        disc_inner_radius = max(hub.radius * 0.78, hub.radius - max(disc_thickness * 0.35, 0.0012))
        front_disc = _cq_annulus_x(
            face_outer_radius, disc_inner_radius, disc_thickness
        ).translate((width * 0.5 - front_inset - disc_thickness * 0.5, 0.0, 0.0))
        rear_disc = _cq_annulus_x(
            face_outer_radius, disc_inner_radius, disc_thickness
        ).translate((-(width * 0.5 - rear_inset - disc_thickness * 0.5), 0.0, 0.0))
        shape = shape.union(front_disc).union(rear_disc)

        spoke_style = spokes.style
        if spoke_style not in {"none", "disc"}:
            spoke_count = spokes.count or (6 if spoke_style in {"straight", "solid_slots"} else 5)
            if spoke_count < 2:
                raise ValidationError("WheelSpokes.count must be at least 2")
            window_width = max(
                spokes.window_radius
                if spokes.window_radius > 0.0
                else (rim_outer - hub.radius) * 0.09,
                0.003,
            )
            slot_length = max((face_outer_radius - hub.radius) * 0.75, 0.010)
            cut_width = width + 0.02
            cutters = []

            def radial_slot(angle_deg, center_radius, length, width_local):
                profile = _wheels_tires_rounded_slot_profile(length, width_local)
                slot = (
                    cq.Workplane("YZ")
                    .polyline([(point[1], point[0] + center_radius) for point in profile])
                    .close()
                    .extrude(cut_width * 0.5, both=True)
                    .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                )
                return slot

            if spoke_style in {"straight", "solid_slots"}:
                for index in range(spoke_count):
                    cutters.append(
                        radial_slot(
                            360.0 * index / float(spoke_count),
                            (hub.radius + face_outer_radius) * 0.5,
                            slot_length,
                            window_width * (1.5 if spoke_style == "solid_slots" else 1.0),
                        )
                    )
            elif spoke_style == "split_y":
                for index in range(spoke_count):
                    base = 360.0 * index / float(spoke_count)
                    cutters.append(
                        radial_slot(
                            base - 10.0,
                            hub.radius + (face_outer_radius - hub.radius) * 0.44,
                            slot_length * 0.55,
                            window_width * 0.85,
                        )
                    )
                    cutters.append(
                        radial_slot(
                            base + 10.0,
                            hub.radius + (face_outer_radius - hub.radius) * 0.64,
                            slot_length * 0.55,
                            window_width * 0.85,
                        )
                    )
            else:
                rows = (
                    hub.radius + (face_outer_radius - hub.radius) * 0.36,
                    hub.radius + (face_outer_radius - hub.radius) * 0.68,
                )
                for row_index, center_radius in enumerate(rows):
                    count = spoke_count * (2 if row_index == 1 else 1)
                    for index in range(count):
                        cutters.append(
                            radial_slot(
                                360.0 * index / float(count)
                                + (180.0 / float(count) if row_index == 1 else 0.0),
                                center_radius,
                                slot_length * (0.30 if row_index == 0 else 0.24),
                                window_width * 0.72,
                            )
                        )
            shape = _wheels_tires_cut_with_pattern(shape, cutters)

        if hub.bolt_pattern is not None:
            pattern = hub.bolt_pattern
            if pattern.count < 2 or pattern.circle_diameter <= 0.0 or pattern.hole_diameter <= 0.0:
                raise ValidationError(
                    "BoltPattern count, circle_diameter, and hole_diameter must be positive"
                )
            bolt_r = pattern.circle_diameter * 0.5
            if bolt_r + pattern.hole_diameter * 0.5 >= hub.radius:
                raise ValidationError("BoltPattern holes must fit inside the hub")
            for index in range(pattern.count):
                angle = 2.0 * pi * index / float(pattern.count)
                hole = (
                    cq.Workplane("YZ")
                    .circle(pattern.hole_diameter * 0.5)
                    .extrude(width + 0.04, both=True)
                    .translate((0.0, bolt_r * cos(angle), bolt_r * sin(angle)))
                )
                shape = shape.cut(hole)

        if bore.style == "round":
            bore_cut = (
                cq.Workplane("YZ").circle(bore.diameter * 0.5).extrude(width + 0.04, both=True)
            )
        elif bore.style == "hex":
            bore_cut = cq.Workplane("YZ").polygon(6, bore.diameter).extrude(width + 0.04, both=True)
        else:
            key_width = bore.key_width or bore.diameter * 0.32
            bore_cut = (
                cq.Workplane("YZ").circle(bore.diameter * 0.5).extrude(width + 0.04, both=True)
            )
            key = cq.Workplane("YZ").box(width + 0.04, key_width, bore.diameter * 0.5)
            bore_cut = bore_cut.union(key.translate((0.0, bore.diameter * 0.25, 0.0)))
        shape = shape.cut(bore_cut)

        if flange is not None:
            if flange.radius <= 0.0 or flange.thickness <= 0.0:
                raise ValidationError("WheelFlange radius and thickness must be positive")
            ring_inner = max(flange.radius - flange.thickness, hub.radius * 1.05)
            ring = _cq_annulus_x(flange.radius, ring_inner, flange.thickness * 0.6)
            bridge_len = max(flange.offset + flange.thickness * 0.6, flange.thickness * 0.8)
            bridge_radial = max(flange.radius - rim_outer + flange.thickness * 0.35, 0.006)
            bridge_thickness = max(flange.thickness * 0.55, 0.0015)
            strut = cq.Workplane("XY").box(bridge_len, bridge_radial, bridge_thickness)
            x_offsets = []
            if flange.side in {"front", "both"}:
                x_offsets.append(width * 0.5 + flange.offset)
            if flange.side in {"rear", "both"}:
                x_offsets.append(-(width * 0.5 + flange.offset))
            for x_offset in x_offsets:
                ring_shape = ring.translate((x_offset, 0.0, 0.0))
                shape = shape.union(ring_shape)
                axial_mid = (
                    (width * 0.5 + x_offset) * 0.5
                    if x_offset >= 0.0
                    else (-(width * 0.5) + x_offset) * 0.5
                )
                radial_mid = (rim_outer + ring_inner) * 0.5
                for angle_deg in (0.0, 90.0, 180.0, 270.0):
                    shape = shape.union(
                        strut.translate((axial_mid, radial_mid, 0.0)).rotate(
                            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg
                        )
                    )

        if not center:
            shape = _shift_to_x0(shape)
        self._set(_to_shape(shape))

class TireGeometry(MeshGeometry):
    """Build a tire aligned to local X."""

    def __init__(
        self,
        outer_radius: float,
        width: float,
        *,
        inner_radius: Optional[float] = None,
        carcass: Optional[TireCarcass] = None,
        tread: Optional[TireTread] = None,
        grooves: Sequence[TireGroove] = (),
        sidewall: Optional[TireSidewall] = None,
        shoulder: Optional[TireShoulder] = None,
        center: bool = True,
    ):
        super().__init__()
        outer_radius = float(outer_radius)
        width = float(width)
        inner_radius = float(inner_radius) if inner_radius is not None else outer_radius * 0.58
        carcass = carcass or TireCarcass()
        tread = tread or TireTread()
        sidewall = sidewall or TireSidewall()
        shoulder = shoulder or TireShoulder()

        if outer_radius <= 0.0 or width <= 0.0 or inner_radius <= 0.0:
            raise ValidationError("outer_radius, width, and inner_radius must be positive")
        if inner_radius >= outer_radius:
            raise ValidationError("inner_radius must be less than outer_radius")
        if tread.depth < 0.0:
            raise ValidationError("TireTread.depth must be non-negative")
        for groove in grooves:
            if groove.width < 0.0 or groove.depth < 0.0:
                raise ValidationError("TireGroove width/depth must be non-negative")

        half_w = width * 0.5
        belt_half = half_w * _wheels_tires_clamp(carcass.belt_width_ratio, 0.12, 0.96)
        shoulder_w = shoulder.width if shoulder.width > 1e-6 else width * 0.11
        side_bulge = max(sidewall.bulge, carcass.sidewall_bulge, 0.0)
        inner_crown = inner_radius * 0.82
        if sidewall.style == "square":
            outer_side = outer_radius
            shoulder_radius = max(
                outer_radius - max(shoulder.radius, tread.depth * 0.5, outer_radius * 0.01),
                inner_radius + 1.0e-4,
            )
        elif sidewall.style == "flat":
            outer_side = max(outer_radius - width * 0.08, inner_radius + 1.0e-4)
            shoulder_radius = outer_radius
        elif sidewall.style == "bulged":
            outer_side = min(outer_radius + side_bulge * width, outer_radius + width * 0.12)
            shoulder_radius = outer_radius
        else:
            outer_side = max(outer_radius - width * 0.04, inner_radius + 1.0e-4)
            shoulder_radius = outer_radius

        profile = [
            (-half_w, inner_radius),
            (-half_w * 0.92, inner_radius),
            (
                -half_w * 0.78,
                max(inner_radius + (outer_side - inner_radius) * 0.28, inner_radius + 1.0e-4),
            ),
            (-(belt_half + shoulder_w), outer_side),
            (-belt_half, shoulder_radius),
            (0.0, outer_radius),
            (belt_half, shoulder_radius),
            (belt_half + shoulder_w, outer_side),
            (
                half_w * 0.78,
                max(inner_radius + (outer_side - inner_radius) * 0.28, inner_radius + 1.0e-4),
            ),
            (half_w * 0.92, inner_radius),
            (half_w, inner_radius),
            (half_w * 0.55, inner_crown),
            (0.0, inner_crown),
            (-half_w * 0.55, inner_crown),
            (-half_w, inner_radius),
        ]
        shape = (
            cq.Workplane("XY")
            .polyline(profile)
            .close()
            .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
        )

        for groove in grooves:
            if groove.width <= 1e-6 or groove.depth <= 1e-6:
                continue
            cutter = (
                cq.Workplane("XY")
                .moveTo(groove.center_offset - groove.width * 0.5, outer_radius - groove.depth)
                .lineTo(groove.center_offset + groove.width * 0.5, outer_radius - groove.depth)
                .lineTo(
                    groove.center_offset + groove.width * 0.5, outer_radius + groove.depth * 1.6
                )
                .lineTo(
                    groove.center_offset - groove.width * 0.5, outer_radius + groove.depth * 1.6
                )
                .close()
                .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
            )
            shape = shape.cut(cutter)

        tread_style = tread.style
        tread_depth = tread.depth
        if tread_style == "circumferential" and tread_depth > 1e-6:
            groove_count = tread.count or 3
            band_positions = _wheels_tires_centered_pattern_positions(
                groove_count, max(tread.pitch or (width * 0.20), width * 0.14)
            )
            for pos in band_positions:
                cutter = (
                    cq.Workplane("XY")
                    .moveTo(pos - width * 0.03, outer_radius - tread_depth)
                    .lineTo(pos + width * 0.03, outer_radius - tread_depth)
                    .lineTo(pos + width * 0.03, outer_radius + tread_depth * 1.4)
                    .lineTo(pos - width * 0.03, outer_radius + tread_depth * 1.4)
                    .close()
                    .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                )
                shape = shape.cut(cutter)
        elif tread_style == "rib" and tread_depth > 1e-6:
            rib_count = tread.count or 3
            rib_positions = _wheels_tires_centered_pattern_positions(
                rib_count, max(tread.pitch or (width * 0.20), width * 0.14)
            )
            for pos in rib_positions:
                rib = (
                    cq.Workplane("XY")
                    .moveTo(pos - width * 0.04, outer_radius)
                    .lineTo(pos + width * 0.04, outer_radius)
                    .lineTo(pos + width * 0.04, outer_radius + tread_depth)
                    .lineTo(pos - width * 0.04, outer_radius + tread_depth)
                    .close()
                    .revolve(360.0, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
                )
                shape = shape.union(rib)
        elif tread_style in {"block", "lug", "chevron"} and tread_depth > 1e-6:
            circ_count = tread.count or (
                12
                if tread_style == "lug"
                else max(
                    14,
                    int(
                        (2.0 * pi * outer_radius) / max(tread.pitch or (width * 0.45), width * 0.24)
                    ),
                )
            )
            axial_rows = (
                [-width * 0.22, width * 0.22]
                if tread_style == "lug"
                else (
                    [-width * 0.22, 0.0, width * 0.22]
                    if tread_style == "block"
                    else [-width * 0.18, width * 0.18]
                )
            )
            tangential = (2.0 * pi * outer_radius / float(circ_count)) * _wheels_tires_clamp(
                tread.land_ratio, 0.18, 0.85
            )
            axial_width = width * (0.14 if tread_style == "lug" else 0.12)
            for row_index, row_x in enumerate(axial_rows):
                for index in range(circ_count):
                    angle_deg = 360.0 * index / float(circ_count) + (
                        180.0 / float(circ_count) if row_index % 2 == 1 else 0.0
                    )
                    if tread_style == "chevron":
                        for sign in (-1.0, 1.0):
                            lug = (
                                cq.Workplane("XY")
                                .box(axial_width, tread_depth * 1.35, tangential * 0.48)
                                .translate(
                                    (
                                        row_x + sign * axial_width * 0.38,
                                        outer_radius + tread_depth * 0.16,
                                        0.0,
                                    )
                                )
                                .rotate(
                                    (0.0, 0.0, 0.0),
                                    (0.0, 1.0, 0.0),
                                    tread.angle_deg * sign
                                    if abs(tread.angle_deg) > 1e-6
                                    else 24.0 * sign,
                                )
                                .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                            )
                            shape = shape.union(lug)
                    else:
                        lug = (
                            cq.Workplane("XY")
                            .box(
                                axial_width,
                                tread_depth * 1.35,
                                tangential * (0.55 if tread_style == "lug" else 0.42),
                            )
                            .translate((row_x, outer_radius + tread_depth * 0.16, 0.0))
                            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
                        )
                        shape = shape.union(lug)

        if not center:
            shape = _shift_to_x0(shape)
        self._set(_to_shape(shape))

# ===== model =====
import math
def _tube_pose(start: tuple[float, float, float], end: tuple[float, float, float]) -> tuple[Origin, float]:
    sx, sy, sz = start
    ex, ey, ez = end
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.0:
        raise ValueError("tube endpoints must be distinct")
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(math.sqrt(dx * dx + dy * dy), dz)
    return Origin(xyz=((sx + ex) * 0.5, (sy + ey) * 0.5, (sz + ez) * 0.5), rpy=(0.0, pitch, yaw)), length
def _add_tube(part, name: str, start, end, radius: float, material: Material) -> None:
    origin, length = _tube_pose(start, end)
    part.visual(Cylinder(radius=radius, length=length), origin=origin, material=material, name=name)
def _rounded_pad_mesh(name: str, length: float, width: float, thickness: float, radius: float):
    profile = rounded_rect_profile(length, width, radius, corner_segments=10)
    return mesh_from_geometry(ExtrudeGeometry(profile, thickness, center=True), name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="folding_adjustable_weight_bench")

    steel = Material("satin_black_steel", color=(0.03, 0.035, 0.035, 1.0))
    dark_steel = Material("dark_powdercoat", color=(0.01, 0.012, 0.012, 1.0))
    rubber = Material("matte_black_rubber", color=(0.005, 0.005, 0.004, 1.0))
    vinyl = Material("black_grained_vinyl", color=(0.02, 0.022, 0.024, 1.0))
    seam = Material("slightly_gloss_seam", color=(0.0, 0.0, 0.0, 1.0))
    metal = Material("brushed_pin_metal", color=(0.65, 0.66, 0.63, 1.0))
    red = Material("red_pop_pin_knob", color=(0.85, 0.04, 0.025, 1.0))

    # Root assembly: a compact low tubular home-gym frame with fixed brackets,
    # front transport axle, hinge axles, and the adjustment ladder under the back pad.
    frame = model.part("center_frame")
    rail_z = 0.075
    for y, suffix in ((-0.19, "0"), (0.19, "1")):
        _add_tube(frame, f"base_rail_{suffix}", (-0.68, y, rail_z), (0.61, y, rail_z), 0.022, steel)
    _add_tube(frame, "rear_cross_tube", (-0.65, -0.23, rail_z), (-0.65, 0.23, rail_z), 0.023, steel)
    _add_tube(frame, "front_cross_tube", (0.57, -0.23, rail_z), (0.57, 0.23, rail_z), 0.023, steel)
    _add_tube(frame, "center_spine", (-0.50, 0.0, 0.12), (0.43, 0.0, 0.255), 0.023, steel)
    _add_tube(frame, "rear_mast", (-0.44, 0.0, rail_z), (-0.125, 0.0, 0.365), 0.022, steel)
    _add_tube(frame, "front_mast", (0.40, 0.0, rail_z), (-0.035, 0.0, 0.395), 0.022, steel)
    _add_tube(frame, "rear_mast_crossbar", (-0.44, -0.19, rail_z), (-0.44, 0.19, rail_z), 0.018, steel)
    _add_tube(frame, "front_mast_crossbar", (0.40, -0.19, rail_z), (0.40, 0.19, rail_z), 0.018, steel)
    _add_tube(frame, "mid_cross_tube", (-0.18, -0.19, 0.315), (-0.18, 0.19, 0.315), 0.018, steel)
    frame.visual(
        Box((0.090, 0.430, 0.045)),
        origin=Origin(xyz=(-0.50, 0.0, 0.098)),
        material=dark_steel,
        name="spine_saddle_plate",
    )

    # Hinge and pivot hardware carried by the fixed frame.
    _add_tube(frame, "back_hinge_axle", (-0.09, -0.235, 0.43), (-0.09, 0.235, 0.43), 0.011, metal)
    _add_tube(frame, "seat_hinge_axle", (-0.035, -0.215, 0.43), (-0.035, 0.215, 0.43), 0.010, metal)
    _add_tube(frame, "support_pivot_axle", (-0.64, -0.13, 0.130), (-0.64, 0.13, 0.130), 0.010, metal)
    _add_tube(frame, "front_wheel_axle", (0.69, -0.325, 0.085), (0.69, 0.325, 0.085), 0.009, metal)
    for y, suffix in ((-0.238, "0"), (0.238, "1")):
        _add_tube(frame, f"back_hinge_side_support_{suffix}", (-0.18, y * 0.80, 0.315), (-0.09, y, 0.430), 0.012, steel)
    for y, suffix in ((-0.218, "0"), (0.218, "1")):
        _add_tube(frame, f"seat_hinge_side_support_{suffix}", (0.03, y * 0.88, 0.330), (-0.035, y, 0.430), 0.012, steel)
    _add_tube(frame, "wheel_axle_bracket", (0.57, 0.0, rail_z), (0.69, 0.0, 0.085), 0.011, steel)
    _add_tube(frame, "seat_support_crossbar", (0.03, -0.192, 0.330), (0.03, 0.192, 0.330), 0.014, steel)
    for y, suffix in ((-0.13, "0"), (0.13, "1")):
        frame.visual(
            Box((0.060, 0.018, 0.080)),
            origin=Origin(xyz=(-0.64, y, 0.098)),
            material=steel,
            name=f"support_pivot_lug_{suffix}",
        )

    # Rubber foot pads are small fixed caps on the cross tubes.
    for x, tag in ((-0.65, "rear"), (0.57, "front")):
        for y, side in ((-0.245, "0"), (0.245, "1")):
            frame.visual(
                Box((0.075, 0.035, 0.024)),
                origin=Origin(xyz=(x, y, 0.040)),
                material=rubber,
                name=f"{tag}_foot_{side}",
            )

    # The angle selector ladder is a slotted-looking fixed bar under the backrest.
    _add_tube(frame, "selector_ladder", (-0.50, -0.165, 0.215), (-0.18, -0.165, 0.36), 0.014, dark_steel)
    for i, (x, z) in enumerate(((-0.45, 0.238), (-0.37, 0.274), (-0.29, 0.310), (-0.21, 0.346))):
        frame.visual(
            Cylinder(radius=0.014, length=0.020),
            origin=Origin(xyz=(x, -0.165, z), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=metal,
            name=f"selector_hole_{i}",
        )
    frame.visual(
        Box((0.060, 0.045, 0.050)),
        origin=Origin(xyz=(-0.18, -0.168, 0.336)),
        material=dark_steel,
        name="selector_mount_tab",
    )

    # Backrest: independent pad, underside support bracket, hinge sleeve, and the
    # side pop-pin socket.  Its local frame is on the transverse hinge line.
    backrest = model.part("backrest")
    backrest.visual(
        _rounded_pad_mesh("backrest_pad_mesh", 0.78, 0.31, 0.075, 0.045),
        origin=Origin(xyz=(-0.405, 0.0, 0.060)),
        material=vinyl,
        name="back_pad",
    )
    backrest.visual(
        Box((0.70, 0.014, 0.008)),
        origin=Origin(xyz=(-0.405, 0.118, 0.0995)),
        material=seam,
        name="back_seam_0",
    )
    backrest.visual(
        Box((0.70, 0.014, 0.008)),
        origin=Origin(xyz=(-0.405, -0.118, 0.0995)),
        material=seam,
        name="back_seam_1",
    )
    for y, suffix in ((-0.105, "0"), (0.105, "1")):
        _add_tube(backrest, f"back_under_rail_{suffix}", (-0.745, y, 0.012), (-0.025, y, 0.012), 0.014, steel)
    _add_tube(backrest, "back_cross_bracket", (-0.52, -0.125, 0.012), (-0.52, 0.125, 0.012), 0.012, steel)
    _add_tube(backrest, "back_hinge_sleeve", (0.0, -0.205, 0.0), (0.0, 0.205, 0.0), 0.018, steel)
    for y, suffix in ((-0.105, "0"), (0.105, "1")):
        backrest.visual(
            Box((0.036, 0.034, 0.020)),
            origin=Origin(xyz=(-0.026, y, 0.025)),
            material=steel,
            name=f"back_hinge_tab_{suffix}",
        )
    backrest.visual(
        Box((0.28, 0.014, 0.055)),
        origin=Origin(xyz=(-0.28, -0.168, -0.020)),
        material=dark_steel,
        name="pop_pin_plate",
    )
    _add_tube(backrest, "pop_pin_standoff", (-0.28, -0.105, -0.010), (-0.28, -0.168, -0.010), 0.010, steel)
    backrest.visual(
        Cylinder(radius=0.019, length=0.018),
        origin=Origin(xyz=(-0.28, -0.178, -0.020), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="pop_pin_boss",
    )

    # Seat pad: a separate short pivoting pad on its own hinge and support bracket.
    seat = model.part("seat_pad")
    seat.visual(
        _rounded_pad_mesh("seat_pad_mesh", 0.46, 0.31, 0.075, 0.045),
        origin=Origin(xyz=(0.245, 0.0, 0.058)),
        material=vinyl,
        name="seat_cushion",
    )
    seat.visual(
        Box((0.37, 0.014, 0.008)),
        origin=Origin(xyz=(0.255, 0.118, 0.0995)),
        material=seam,
        name="seat_seam_0",
    )
    seat.visual(
        Box((0.37, 0.014, 0.008)),
        origin=Origin(xyz=(0.255, -0.118, 0.0995)),
        material=seam,
        name="seat_seam_1",
    )
    for y, suffix in ((-0.100, "0"), (0.100, "1")):
        _add_tube(seat, f"seat_under_rail_{suffix}", (0.025, y, 0.012), (0.435, y, 0.012), 0.014, steel)
    _add_tube(seat, "seat_cross_bracket", (0.25, -0.12, 0.012), (0.25, 0.12, 0.012), 0.012, steel)
    _add_tube(seat, "seat_hinge_sleeve", (0.0, -0.185, 0.0), (0.0, 0.185, 0.0), 0.017, steel)
    for y, suffix in ((-0.100, "0"), (0.100, "1")):
        seat.visual(
            Box((0.040, 0.032, 0.020)),
            origin=Origin(xyz=(0.020, y, 0.022)),
            material=steel,
            name=f"seat_hinge_tab_{suffix}",
        )

    # Rear support link: a pivoting pair of steel straps/tubes tied by pivot barrels.
    rear_support = model.part("rear_support")
    _add_tube(rear_support, "lower_bushing", (0.0, -0.115, 0.0), (0.0, 0.115, 0.0), 0.018, steel)
    for y, suffix in ((-0.075, "0"), (0.075, "1")):
        rear_support.visual(
            Box((0.032, 0.020, 0.018)),
            origin=Origin(xyz=(0.020, y, 0.020)),
            material=steel,
            name=f"lower_link_tab_{suffix}",
        )
        _add_tube(rear_support, f"side_link_{suffix}", (0.018, y, 0.018), (0.245, y, 0.245), 0.013, steel)
    _add_tube(rear_support, "upper_roller", (0.245, -0.105, 0.245), (0.245, 0.105, 0.245), 0.017, metal)

    # Transport wheels, each a spinning wheel-and-tire part on the fixed axle.
    tire_mesh = mesh_from_geometry(
        TireGeometry(
            0.066,
            0.044,
            inner_radius=0.043,
            carcass=TireCarcass(belt_width_ratio=0.70, sidewall_bulge=0.05),
            tread=TireTread(style="ribbed", depth=0.003, count=18, land_ratio=0.62),
            shoulder=TireShoulder(width=0.004, radius=0.002),
        ),
        "front_transport_tire",
    )
    wheel_mesh = mesh_from_geometry(
        WheelGeometry(
            0.043,
            0.042,
            rim=WheelRim(inner_radius=0.029, flange_height=0.004, flange_thickness=0.002),
            hub=WheelHub(
                radius=0.018,
                width=0.034,
                cap_style="domed",
                bolt_pattern=BoltPattern(count=4, circle_diameter=0.023, hole_diameter=0.003),
            ),
            spokes=WheelSpokes(style="straight", count=5, thickness=0.003, window_radius=0.006),
            bore=WheelBore(style="round", diameter=0.022),
        ),
        "front_transport_wheel",
    )
    for y, suffix in ((-0.285, "0"), (0.285, "1")):
        wheel = model.part(f"front_wheel_{suffix}")
        wheel.visual(tire_mesh, origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)), material=rubber, name="tire")
        wheel.visual(wheel_mesh, origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)), material=metal, name="rim")
        wheel.visual(
            Cylinder(radius=0.013, length=0.052),
            origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=metal,
            name="axle_bushing",
        )
        model.articulation(
            f"frame_to_wheel_{suffix}",
            ArticulationType.CONTINUOUS,
            parent=frame,
            child=wheel,
            origin=Origin(xyz=(0.69, y, 0.085)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=8.0, velocity=18.0),
        )

    # Separate pop-pin knob and shaft, translating outward along the local side axis.
    pop_pin = model.part("pop_pin")
    pop_pin.visual(
        Cylinder(radius=0.006, length=0.055),
        origin=Origin(xyz=(0.0, -0.026, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="pin_shaft",
    )
    pop_pin.visual(
        mesh_from_geometry(
            KnobGeometry(
                0.040,
                0.026,
                body_style="lobed",
                top_diameter=0.036,
                grip=KnobGrip(style="ribbed", count=8, depth=0.002),
            ),
            "pop_pin_knob_mesh",
        ),
        origin=Origin(xyz=(0.0, -0.066, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=red,
        name="knob_cap",
    )

    back_hinge = model.articulation(
        "frame_to_backrest",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=backrest,
        origin=Origin(xyz=(-0.09, 0.0, 0.43)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=90.0, velocity=1.4, lower=0.0, upper=1.20),
    )
    seat_hinge = model.articulation(
        "frame_to_seat",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=seat,
        origin=Origin(xyz=(-0.035, 0.0, 0.43)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=50.0, velocity=1.2, lower=0.0, upper=0.45),
    )
    support_pivot = model.articulation(
        "frame_to_rear_support",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=rear_support,
        origin=Origin(xyz=(-0.64, 0.0, 0.130)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=45.0, velocity=1.1, lower=-0.30, upper=0.85),
    )
    pin_slide = model.articulation(
        "backrest_to_pop_pin",
        ArticulationType.PRISMATIC,
        parent=backrest,
        child=pop_pin,
        origin=Origin(xyz=(-0.28, -0.182, -0.020)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=0.18, lower=0.0, upper=0.035),
    )

    # Keep handles for tests without changing the authored joint semantics.
    model.meta["primary_joints"] = (
        back_hinge.name,
        seat_hinge.name,
        support_pivot.name,
        pin_slide.name,
        "frame_to_wheel_0",
        "frame_to_wheel_1",
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
