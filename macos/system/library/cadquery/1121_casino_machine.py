# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

from __future__ import annotations

import cadquery as cq
import math
from contextlib import suppress
from dataclasses import dataclass
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

def superellipse_profile(width, height, exponent=2.6, *, segments=48):
    width = float(width); height = float(height); exponent = float(exponent)
    segments = max(12, int(segments))
    if width <= 0 or height <= 0:
        raise ValidationError("width/height must be positive")
    if exponent <= 0:
        raise ValidationError("exponent must be positive")
    a = width * 0.5; b = height * 0.5; power = 2.0 / exponent
    pts = []
    for i in range(segments):
        t = 2.0 * math.pi * i / segments
        ct = math.cos(t); st = math.sin(t)
        x = a * (abs(ct) ** power); y = b * (abs(st) ** power)
        if ct < 0:
            x = -x
        if st < 0:
            y = -y
        pts.append((x, y))
    return pts

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

# ===== brackets_hinges_bezels (17 syms) =====
def _brackets_hinges_bezels_shift_to_z0(shape):
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(0.0, 0.0, -bb.zmin))

def _brackets_hinges_bezels_finish(target, model, center):
    shape = _to_shape(model)
    if not center:
        shape = _brackets_hinges_bezels_shift_to_z0(shape)
    target._set(shape)

@dataclass(frozen=True)
class BezelFace:
    style: Literal["flat", "rounded", "chamfered", "radiused_step"] = "flat"
    front_lip: float = 0.0
    chamfer: float = 0.0
    fillet: float = 0.0

@dataclass(frozen=True)
class BezelRecess:
    depth: float
    inset: float
    floor_radius: float = 0.0
    wall_draft_deg: float = 0.0

@dataclass(frozen=True)
class BezelVisor:
    top_extension: float = 0.0
    side_extension: float = 0.0
    thickness: float = 0.0
    draft_deg: float = 0.0

@dataclass(frozen=True)
class BezelFlange:
    width: float = 0.0
    thickness: float = 0.0
    offset: float = 0.0

@dataclass(frozen=True)
class BezelMounts:
    style: Literal["none", "bosses", "tabs", "rear_flange"] = "none"
    hole_count: int = 0
    hole_diameter: Optional[float] = None
    boss_diameter: Optional[float] = None
    setback: float = 0.0

@dataclass(frozen=True)
class BezelCutout:
    edge: Literal["top", "bottom", "left", "right"]
    width: float
    depth: float
    offset: float = 0.0

@dataclass(frozen=True)
class BezelEdgeFeature:
    style: Literal["bead", "step", "notch"] = "bead"
    edge: Literal["top", "bottom", "left", "right"] = "top"
    size: float = 0.0
    offset: float = 0.0
    extent: float = 0.0

def _sample_ellipse_profile(width: float, height: float, *, segments: int = 64):
    rx = float(width) * 0.5
    ry = float(height) * 0.5
    return [
        (rx * math.cos(2.0 * math.pi * index / float(segments)),
         ry * math.sin(2.0 * math.pi * index / float(segments)))
        for index in range(segments)
    ]

def _sample_rect_profile(width: float, height: float):
    hw = float(width) * 0.5
    hh = float(height) * 0.5
    return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]

def _shape_profile_points_2d(shape, size, *, corner_radius: float = 0.0, segments: int = 64):
    width = float(size[0])
    height = float(size[1])
    if width <= 0.0 or height <= 0.0:
        raise ValueError("shape size values must be positive")
    if shape == "rect":
        return _sample_rect_profile(width, height)
    if shape == "rounded_rect":
        return rounded_rect_profile(
            width, height, max(0.0, corner_radius), corner_segments=max(4, segments // 16)
        )
    if shape == "circle":
        diameter = min(width, height)
        return _sample_ellipse_profile(diameter, diameter, segments=segments)
    if shape == "ellipse":
        return _sample_ellipse_profile(width, height, segments=segments)
    if shape == "superellipse":
        return superellipse_profile(width, height, exponent=2.8, segments=segments)
    raise ValueError(f"Unsupported shape {shape!r}")

def _shape_size_from_wall(inner_size, wall):
    inner_w = float(inner_size[0])
    inner_h = float(inner_size[1])
    if isinstance(wall, (int, float)):
        wall_left = wall_right = wall_bottom = wall_top = float(wall)
    else:
        if len(wall) != 4:
            raise ValueError("wall must be a float or a 4-sequence")
        wall_left, wall_right, wall_bottom, wall_top = (float(value) for value in wall)
    if min(wall_left, wall_right, wall_bottom, wall_top) < 0.0:
        raise ValueError("wall values must be non-negative")
    return (inner_w + wall_left + wall_right, inner_h + wall_bottom + wall_top)

def _cq_polyline_wire(cq_module, points, plane: str = "XY"):
    return cq_module.Workplane(plane).polyline(points).close()

def _cq_ring_solid(cq_module, outer_points, inner_points, depth: float, *, center: bool = True):
    shape = _cq_polyline_wire(cq_module, outer_points).extrude(float(depth) * 0.5, both=center)
    inner_cut = _cq_polyline_wire(cq_module, inner_points).extrude(
        float(depth) + max(0.002, float(depth) * 0.5),
        both=center,
    )
    return shape.cut(inner_cut)

def _brackets_hinges_bezels_centered_pattern_positions(count: int, spacing: float):
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    origin = -0.5 * float(spacing) * float(count - 1)
    return [origin + float(index) * float(spacing) for index in range(count)]

class BezelGeometry(MeshGeometry):
    """Build a framed opening with optional recess, visor, flange, and rear mounts."""

    def __init__(
        self,
        opening_size: Sequence[float],
        outer_size: Sequence[float],
        depth: float,
        *,
        opening_shape: Literal[
            "rect", "rounded_rect", "circle", "ellipse", "superellipse"
        ] = "rounded_rect",
        outer_shape: Literal[
            "rect", "rounded_rect", "circle", "ellipse", "superellipse"
        ] = "rounded_rect",
        opening_corner_radius: float = 0.0,
        outer_corner_radius: float = 0.0,
        wall: Union[float, tuple[float, float, float, float], None] = None,
        face: Optional[BezelFace] = None,
        recess: Optional[BezelRecess] = None,
        visor: Optional[BezelVisor] = None,
        flange: Optional[BezelFlange] = None,
        mounts: Optional[BezelMounts] = None,
        cutouts: Sequence[BezelCutout] = (),
        edge_features: Sequence[BezelEdgeFeature] = (),
        center: bool = True,
    ):
        super().__init__()
        opening_w = float(opening_size[0])
        opening_h = float(opening_size[1])
        outer_w = float(outer_size[0])
        outer_h = float(outer_size[1])
        depth = float(depth)
        opening_corner_radius = max(0.0, float(opening_corner_radius))
        outer_corner_radius = max(0.0, float(outer_corner_radius))
        face = face or BezelFace()
        visor = visor or BezelVisor()
        flange = flange or BezelFlange()
        mounts = mounts or BezelMounts()

        if min(opening_w, opening_h, outer_w, outer_h, depth) <= 0.0:
            raise ValueError("opening_size, outer_size, and depth must be positive")
        if opening_w >= outer_w or opening_h >= outer_h:
            raise ValueError("opening_size must be smaller than outer_size on both axes")
        if recess is not None and (recess.depth <= 0.0 or recess.inset < 0.0):
            raise ValueError("BezelRecess depth must be positive and inset must be non-negative")

        outer_points = _shape_profile_points_2d(
            outer_shape, (outer_w, outer_h), corner_radius=outer_corner_radius
        )
        opening_points = _shape_profile_points_2d(
            opening_shape, (opening_w, opening_h), corner_radius=opening_corner_radius
        )
        shape = _cq_ring_solid(cq, outer_points, opening_points, depth, center=True)

        if face.style in {"rounded", "radiused_step"} and face.fillet > 1e-6:
            with suppress(Exception):
                shape = shape.edges("|Z").fillet(
                    min(face.fillet, depth * 0.25, min(outer_w, outer_h) * 0.1)
                )
        if face.style == "chamfered" and face.chamfer > 1e-6:
            with suppress(Exception):
                shape = shape.edges("|Z").chamfer(
                    min(face.chamfer, depth * 0.25, min(outer_w, outer_h) * 0.1)
                )

        derived_wall = (
            (outer_w - opening_w) * 0.5,
            (outer_w - opening_w) * 0.5,
            (outer_h - opening_h) * 0.5,
            (outer_h - opening_h) * 0.5,
        )
        if face.front_lip > 1e-6 or face.style == "radiused_step":
            lip_thickness = max(face.front_lip, depth * 0.08, 0.0015)
            if wall is not None:
                lip_size = _shape_size_from_wall(opening_size, wall)
            else:
                lip_size = (
                    min(
                        opening_w + max(face.front_lip * 2.0, derived_wall[0] * 1.05),
                        outer_w - 0.001,
                    ),
                    min(
                        opening_h + max(face.front_lip * 2.0, derived_wall[2] * 1.05),
                        outer_h - 0.001,
                    ),
                )
            if lip_size[0] < outer_w and lip_size[1] < outer_h:
                lip_outer = _shape_profile_points_2d(
                    opening_shape if outer_shape != "circle" else outer_shape,
                    lip_size,
                    corner_radius=min(
                        opening_corner_radius + face.front_lip,
                        lip_size[0] * 0.25,
                        lip_size[1] * 0.25,
                    ),
                )
                lip = _cq_ring_solid(
                    cq, lip_outer, opening_points, lip_thickness, center=True
                ).translate((0.0, 0.0, depth * 0.5))
                shape = shape.union(lip)

        if recess is not None:
            requested_recess_size = (opening_w + recess.inset * 2.0, opening_h + recess.inset * 2.0)
            if wall is None and (
                requested_recess_size[0] >= outer_w or requested_recess_size[1] >= outer_h
            ):
                raise ValueError("recess wall leaves no outer frame material")
            recess_size = (
                _shape_size_from_wall(opening_size, wall)
                if wall is not None
                else (
                    min(requested_recess_size[0], outer_w - 0.001),
                    min(requested_recess_size[1], outer_h - 0.001),
                )
            )
            if recess_size[0] >= outer_w or recess_size[1] >= outer_h:
                raise ValueError("recess wall leaves no outer frame material")
            recess_points = _shape_profile_points_2d(
                opening_shape if outer_shape != "circle" else outer_shape,
                recess_size,
                corner_radius=min(
                    opening_corner_radius + recess.inset,
                    recess_size[0] * 0.25,
                    recess_size[1] * 0.25,
                ),
            )
            recess_cut = _cq_ring_solid(
                cq, recess_points, opening_points, recess.depth, center=True
            ).translate((0.0, 0.0, depth * 0.5 - recess.depth * 0.5))
            shape = shape.cut(recess_cut)

        if visor.thickness > 1e-6 and (visor.top_extension > 1e-6 or visor.side_extension > 1e-6):
            top_visor = (
                cq.Workplane("XY")
                .box(
                    outer_w + visor.side_extension * 2.0,
                    max(visor.top_extension, visor.thickness),
                    visor.thickness,
                )
                .translate((0.0, outer_h * 0.5 + visor.top_extension * 0.5, depth * 0.5))
            )
            shape = shape.union(top_visor)
            if visor.side_extension > 1e-6:
                cheek_y = max(visor.top_extension, outer_h * 0.5) * 0.5
                cheek = cq.Workplane("XY").box(
                    visor.side_extension,
                    max(visor.top_extension, outer_h * 0.45),
                    visor.thickness,
                )
                shape = shape.union(
                    cheek.translate(
                        (outer_w * 0.5 + visor.side_extension * 0.5, cheek_y, depth * 0.5)
                    )
                )
                shape = shape.union(
                    cheek.translate(
                        (-(outer_w * 0.5 + visor.side_extension * 0.5), cheek_y, depth * 0.5)
                    )
                )

        if flange.width > 1e-6 and flange.thickness > 1e-6:
            flange_outer = _shape_profile_points_2d(
                outer_shape,
                (outer_w + flange.width * 2.0, outer_h + flange.width * 2.0),
                corner_radius=outer_corner_radius + flange.width,
            )
            flange_shape = _cq_ring_solid(
                cq, flange_outer, outer_points, flange.thickness, center=True
            ).translate((0.0, 0.0, -depth * 0.5 - flange.offset))
            shape = shape.union(flange_shape)

        if mounts.style == "bosses" and mounts.hole_count > 0:
            boss_radius = (
                max(float(mounts.boss_diameter) * 0.5, 0.0015)
                if mounts.boss_diameter is not None
                else max(min(outer_w, outer_h) * 0.05, 0.003)
            )
            hole_radius = (
                max(float(mounts.hole_diameter) * 0.5, 0.0008)
                if mounts.hole_diameter is not None
                else boss_radius * 0.38
            )
            boss_thickness = max(depth * 0.18, boss_radius * 0.8)
            margin_x = outer_w * 0.5 - boss_radius - max(mounts.setback, 0.001)
            margin_y = outer_h * 0.5 - boss_radius - max(mounts.setback, 0.001)
            boss_points = [
                (-margin_x, -margin_y),
                (margin_x, -margin_y),
                (margin_x, margin_y),
                (-margin_x, margin_y),
            ][: mounts.hole_count]
            for bx, by in boss_points:
                boss = (
                    cq.Workplane("XY")
                    .circle(boss_radius)
                    .extrude(boss_thickness)
                    .translate((bx, by, -depth * 0.5 - boss_thickness))
                )
                hole = (
                    cq.Workplane("XY")
                    .circle(hole_radius)
                    .extrude(boss_thickness + depth + 0.01)
                    .translate((bx, by, -depth * 0.5 - boss_thickness))
                )
                shape = shape.union(boss).cut(hole)
        elif mounts.style == "tabs" and mounts.hole_count > 0:
            tab_width = max(outer_w * 0.16, 0.008)
            tab_depth = max(depth * 0.14, 0.002)
            hole_radius = (
                max(float(mounts.hole_diameter) * 0.5, 0.0008)
                if mounts.hole_diameter is not None
                else tab_width * 0.14
            )
            tab_positions = _brackets_hinges_bezels_centered_pattern_positions(
                mounts.hole_count, outer_w / max(mounts.hole_count, 1)
            )
            for px in tab_positions:
                tab = (
                    cq.Workplane("XY")
                    .box(tab_width, tab_width * 0.6, tab_depth)
                    .translate(
                        (px, -(outer_h * 0.5 + tab_width * 0.3), -depth * 0.5 - tab_depth * 0.5)
                    )
                )
                hole = (
                    cq.Workplane("XY")
                    .circle(hole_radius)
                    .extrude(tab_depth + depth + 0.01)
                    .translate((px, -(outer_h * 0.5 + tab_width * 0.3), -depth * 0.5 - tab_depth))
                )
                shape = shape.union(tab).cut(hole)
        elif (
            mounts.style == "rear_flange"
            and mounts.hole_count > 0
            and mounts.hole_diameter is not None
        ):
            flange_width = max(max(mounts.setback, 0.003), min(outer_w, outer_h) * 0.06)
            rear_flange_outer = _shape_profile_points_2d(
                outer_shape,
                (outer_w + flange_width * 2.0, outer_h + flange_width * 2.0),
                corner_radius=outer_corner_radius + flange_width,
            )
            rear_flange = _cq_ring_solid(
                cq, rear_flange_outer, outer_points, max(depth * 0.12, 0.002), center=True
            ).translate((0.0, 0.0, -depth * 0.5 - max(depth * 0.12, 0.002)))
            shape = shape.union(rear_flange)

        for cutout in cutouts:
            if cutout.width <= 0.0 or cutout.depth <= 0.0:
                raise ValueError("BezelCutout width and depth must be positive")
            cut_height = cutout.width
            cut_depth = cutout.depth
            if cutout.edge in {"top", "bottom"}:
                cutter = cq.Workplane("XY").box(
                    cutout.width, cut_depth, depth + visor.thickness + 0.02
                )
                y = (
                    outer_h * 0.5 - cut_depth * 0.5
                    if cutout.edge == "top"
                    else -outer_h * 0.5 + cut_depth * 0.5
                )
                cutter = cutter.translate((cutout.offset, y, 0.0))
            else:
                cutter = cq.Workplane("XY").box(
                    cut_depth, cut_height, depth + visor.thickness + 0.02
                )
                x = (
                    outer_w * 0.5 - cut_depth * 0.5
                    if cutout.edge == "right"
                    else -outer_w * 0.5 + cut_depth * 0.5
                )
                cutter = cutter.translate((x, cutout.offset, 0.0))
            shape = shape.cut(cutter)

        for feature in edge_features:
            if feature.size <= 0.0:
                continue
            extent = (
                feature.extent
                if feature.extent > 0.0
                else (outer_w if feature.edge in {"top", "bottom"} else outer_h)
            )
            if feature.style == "notch":
                if feature.edge in {"top", "bottom"}:
                    cutter = cq.Workplane("XY").box(
                        extent, feature.size, depth + visor.thickness + 0.02
                    )
                    y = (
                        outer_h * 0.5 - feature.size * 0.5
                        if feature.edge == "top"
                        else -outer_h * 0.5 + feature.size * 0.5
                    )
                    cutter = cutter.translate((feature.offset, y, 0.0))
                else:
                    cutter = cq.Workplane("XY").box(
                        feature.size, extent, depth + visor.thickness + 0.02
                    )
                    x = (
                        outer_w * 0.5 - feature.size * 0.5
                        if feature.edge == "right"
                        else -outer_w * 0.5 + feature.size * 0.5
                    )
                    cutter = cutter.translate((x, feature.offset, 0.0))
                shape = shape.cut(cutter)
                continue
            if feature.edge in {"top", "bottom"}:
                solid = cq.Workplane("XY").box(extent, feature.size, max(depth * 0.10, 0.0015))
                y = (
                    outer_h * 0.5 + feature.size * 0.5
                    if feature.edge == "top"
                    else -(outer_h * 0.5 + feature.size * 0.5)
                )
                solid = solid.translate((feature.offset, y, depth * 0.5))
            else:
                solid = cq.Workplane("XY").box(feature.size, extent, max(depth * 0.10, 0.0015))
                x = (
                    outer_w * 0.5 + feature.size * 0.5
                    if feature.edge == "right"
                    else -(outer_w * 0.5 + feature.size * 0.5)
                )
                solid = solid.translate((x, feature.offset, depth * 0.5))
            shape = (
                shape.union(solid)
                if feature.style == "bead"
                else shape.cut(solid.translate((0.0, 0.0, -max(depth * 0.04, 0.0008))))
            )

        _brackets_hinges_bezels_finish(self, shape, center)

# ===== primitives (1 syms) =====
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="high_top_slot_machine")

    black = model.material("black_enamel", rgba=(0.015, 0.012, 0.010, 1.0))
    deep_red = model.material("deep_red_lacquer", rgba=(0.45, 0.025, 0.018, 1.0))
    gold = model.material("brushed_gold", rgba=(0.92, 0.66, 0.20, 1.0))
    chrome = model.material("polished_chrome", rgba=(0.78, 0.80, 0.82, 1.0))
    dark_glass = model.material("smoked_glass", rgba=(0.08, 0.11, 0.14, 0.38))
    cream = model.material("warm_reel_ivory", rgba=(0.96, 0.90, 0.72, 1.0))
    red = model.material("reel_red", rgba=(0.86, 0.04, 0.03, 1.0))
    blue = model.material("reel_blue", rgba=(0.05, 0.22, 0.78, 1.0))
    green = model.material("reel_green", rgba=(0.05, 0.55, 0.18, 1.0))

    cabinet = model.part("cabinet")

    # Coordinate frame: +Z is up, -Y is the front face, +X is the lever flank.
    lower_w = 0.58
    lower_d = 0.50
    lower_h = 1.30
    wall = 0.04
    front_y = -lower_d / 2.0
    back_y = lower_d / 2.0
    front_panel_y = front_y + wall / 2.0

    # Narrow lower cabinet shell.  It is built from real panels so the reel
    # window and service-door opening are not hidden by a solid block.
    cabinet.visual(
        Box((wall, lower_d, lower_h)),
        origin=Origin(xyz=(-lower_w / 2.0 + wall / 2.0, 0.0, lower_h / 2.0)),
        material=black,
        name="lower_side_0",
    )
    cabinet.visual(
        Box((wall, lower_d, lower_h)),
        origin=Origin(xyz=(lower_w / 2.0 - wall / 2.0, 0.0, lower_h / 2.0)),
        material=black,
        name="lower_side_1",
    )
    cabinet.visual(
        Box((lower_w, wall, lower_h)),
        origin=Origin(xyz=(0.0, back_y - wall / 2.0, lower_h / 2.0)),
        material=black,
        name="lower_back",
    )
    cabinet.visual(
        Box((lower_w, lower_d, 0.08)),
        origin=Origin(xyz=(0.0, 0.0, 0.04)),
        material=black,
        name="plinth",
    )
    cabinet.visual(
        Box((lower_w, lower_d, 0.055)),
        origin=Origin(xyz=(0.0, 0.0, lower_h - 0.0275)),
        material=black,
        name="lower_top_deck",
    )

    # Lower front strips around the service door.
    door_w = 0.34
    door_h = 0.52
    door_bottom = 0.18
    door_left = -door_w / 2.0
    door_right = door_w / 2.0
    door_top = door_bottom + door_h
    side_strip_w = (lower_w - door_w) / 2.0 + 0.012
    cabinet.visual(
        Box((side_strip_w, wall, 0.66)),
        origin=Origin(xyz=(-lower_w / 2.0 + side_strip_w / 2.0, front_panel_y, 0.43)),
        material=deep_red,
        name="front_lower_side_0",
    )
    cabinet.visual(
        Box((side_strip_w, wall, 0.66)),
        origin=Origin(xyz=(lower_w / 2.0 - side_strip_w / 2.0, front_panel_y, 0.43)),
        material=deep_red,
        name="front_lower_side_1",
    )
    cabinet.visual(
        Box((lower_w, wall, 0.12)),
        origin=Origin(xyz=(0.0, front_panel_y, 0.10)),
        material=deep_red,
        name="front_bottom_rail",
    )
    cabinet.visual(
        Box((lower_w, wall, 0.12)),
        origin=Origin(xyz=(0.0, front_panel_y, door_top + 0.06)),
        material=deep_red,
        name="front_mid_rail",
    )

    # Reel-window frame and glass in the lower cabinet.
    window_w = 0.50
    window_h = 0.28
    window_z = 1.00
    window_bottom = window_z - window_h / 2.0
    window_top = window_z + window_h / 2.0
    cabinet.visual(
        Box(((lower_w - window_w) / 2.0 + 0.012, wall, window_h + 0.08)),
        origin=Origin(
            xyz=(
                -lower_w / 2.0 + ((lower_w - window_w) / 2.0 + 0.012) / 2.0,
                front_panel_y,
                window_z,
            )
        ),
        material=deep_red,
        name="window_side_0",
    )
    cabinet.visual(
        Box(((lower_w - window_w) / 2.0 + 0.012, wall, window_h + 0.08)),
        origin=Origin(
            xyz=(
                lower_w / 2.0 - ((lower_w - window_w) / 2.0 + 0.012) / 2.0,
                front_panel_y,
                window_z,
            )
        ),
        material=deep_red,
        name="window_side_1",
    )
    cabinet.visual(
        Box((lower_w, wall, 0.085)),
        origin=Origin(xyz=(0.0, front_panel_y, window_bottom - 0.042)),
        material=deep_red,
        name="window_bottom_rail",
    )
    cabinet.visual(
        Box((lower_w, wall, 0.075)),
        origin=Origin(xyz=(0.0, front_panel_y, window_top + 0.038)),
        material=deep_red,
        name="window_top_rail",
    )
    reel_bezel = BezelGeometry(
        (window_w, window_h),
        (window_w + 0.065, window_h + 0.065),
        0.025,
        opening_shape="rounded_rect",
        outer_shape="rounded_rect",
        opening_corner_radius=0.025,
        outer_corner_radius=0.045,
        face=BezelFace(style="radiused_step", front_lip=0.004, fillet=0.003),
    )
    cabinet.visual(
        mesh_from_geometry(reel_bezel, "reel_window_bezel"),
        origin=Origin(xyz=(0.0, front_y - 0.010, window_z), rpy=(pi / 2.0, 0.0, 0.0)),
        material=gold,
        name="reel_window_bezel",
    )
    cabinet.visual(
        Box((window_w + 0.020, 0.006, window_h + 0.020)),
        origin=Origin(xyz=(0.0, front_y - 0.014, window_z)),
        material=dark_glass,
        name="reel_window_glass",
    )

    # Back-lit high-top housing, wider than the narrow lower body.
    topper_w = 0.74
    topper_d = 0.54
    topper_h = 0.82
    topper_bottom = lower_h - 0.005
    cabinet.visual(
        Box((topper_w, topper_d, topper_h)),
        origin=Origin(xyz=(0.0, 0.0, topper_bottom + topper_h / 2.0)),
        material=black,
        name="topper_housing",
    )
    cabinet.visual(
        Box((topper_w - 0.10, 0.018, 0.47)),
        origin=Origin(xyz=(0.0, -topper_d / 2.0 - 0.008, topper_bottom + 0.51)),
        material=gold,
        name="topper_marquee",
    )
    cabinet.visual(
        Box((topper_w - 0.17, 0.020, 0.31)),
        origin=Origin(xyz=(0.0, -topper_d / 2.0 - 0.020, topper_bottom + 0.51)),
        material=deep_red,
        name="topper_lit_panel",
    )
    # Stylized "777" sign made from raised bars, not texture.
    for i, x in enumerate((-0.21, 0.0, 0.21)):
        cabinet.visual(
            Box((0.115, 0.014, 0.030)),
            origin=Origin(xyz=(x, -topper_d / 2.0 - 0.034, topper_bottom + 0.61)),
            material=gold,
            name=f"seven_top_{i}",
        )
        cabinet.visual(
            Box((0.032, 0.014, 0.205)),
            origin=Origin(
                xyz=(x + 0.025, -topper_d / 2.0 - 0.034, topper_bottom + 0.515),
                rpy=(0.0, 0.0, -0.35),
            ),
            material=gold,
            name=f"seven_stem_{i}",
        )

    # Player details on the lower front.
    cabinet.visual(
        Box((0.15, 0.012, 0.045)),
        origin=Origin(xyz=(-0.14, front_y - 0.018, 0.81)),
        material=chrome,
        name="coin_slot_plate",
    )
    cabinet.visual(
        Box((0.075, 0.010, 0.012)),
        origin=Origin(xyz=(-0.14, front_y - 0.026, 0.815)),
        material=black,
        name="coin_slot",
    )
    for i, x in enumerate((0.065, 0.135, 0.205)):
        cabinet.visual(
            Cylinder(radius=0.022, length=0.018),
            origin=Origin(xyz=(x, front_y - 0.018, 0.81), rpy=(pi / 2.0, 0.0, 0.0)),
            material=(red, blue, green)[i],
            name=f"play_button_{i}",
        )

    # A visible axle ties the rotating reel set back into the cabinet sidewalls.
    # It intentionally passes through the reel hubs and is allowed in tests.
    axle_y = -0.090
    axle_z = window_z
    cabinet.visual(
        Cylinder(radius=0.018, length=0.54),
        origin=Origin(xyz=(0.0, axle_y, axle_z), rpy=(0.0, pi / 2.0, 0.0)),
        material=chrome,
        name="reel_axle",
    )
    cabinet.visual(
        Box((0.05, 0.045, 0.24)),
        origin=Origin(xyz=(-0.265, axle_y, axle_z)),
        material=chrome,
        name="reel_side_bracket_0",
    )
    cabinet.visual(
        Box((0.05, 0.045, 0.24)),
        origin=Origin(xyz=(0.265, axle_y, axle_z)),
        material=chrome,
        name="reel_side_bracket_1",
    )

    # Cabinet hinge leaves for the lower service door.
    for i, z in enumerate((door_bottom + 0.09, door_bottom + 0.26, door_bottom + 0.43)):
        cabinet.visual(
            Box((0.038, 0.012, 0.095)),
            origin=Origin(xyz=(door_left - 0.017, front_y - 0.005, z)),
            material=chrome,
            name=f"service_hinge_leaf_{i}",
        )

    # Rotating reel set: three independent reels, each on a horizontal X axis.
    reel_centers = (-0.17, 0.0, 0.17)
    decal_mats = (red, blue, green)
    for i, x in enumerate(reel_centers):
        reel = model.part(f"reel_{i}")
        reel.visual(
            Cylinder(radius=0.130, length=0.110),
            origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
            material=cream,
            name="reel_core",
        )
        reel.visual(
            mesh_from_geometry(TorusGeometry(0.128, 0.006), f"reel_{i}_rim_0_mesh"),
            origin=Origin(xyz=(-0.055, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
            material=gold,
            name="reel_rim_0",
        )
        reel.visual(
            mesh_from_geometry(TorusGeometry(0.128, 0.006), f"reel_{i}_rim_1_mesh"),
            origin=Origin(xyz=(0.055, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
            material=gold,
            name="reel_rim_1",
        )
        # Raised symbol cards are embedded slightly into the reel surface so
        # they rotate with the cylinder instead of reading as separate labels.
        reel.visual(
            Box((0.080, 0.008, 0.055)),
            origin=Origin(xyz=(0.0, -0.128, 0.000)),
            material=decal_mats[i],
            name="front_symbol",
        )
        reel.visual(
            Box((0.080, 0.008, 0.045)),
            origin=Origin(xyz=(0.0, -0.106, 0.080)),
            material=gold,
            name="upper_symbol",
        )
        reel.visual(
            Box((0.080, 0.008, 0.045)),
            origin=Origin(xyz=(0.0, -0.106, -0.080)),
            material=black,
            name="lower_symbol",
        )
        model.articulation(
            f"cabinet_to_reel_{i}",
            ArticulationType.CONTINUOUS,
            parent=cabinet,
            child=reel,
            origin=Origin(xyz=(x, axle_y, axle_z)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=18.0),
        )

    # Side pull lever, mounted to the cabinet's right flank.
    lever = model.part("pull_lever")
    lever.visual(
        Cylinder(radius=0.058, length=0.060),
        origin=Origin(xyz=(0.030, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=chrome,
        name="pivot_hub",
    )
    lever.visual(
        Box((0.034, 0.035, 0.390)),
        origin=Origin(xyz=(0.066, 0.0, -0.230)),
        material=chrome,
        name="lever_arm",
    )
    lever.visual(
        Sphere(radius=0.052),
        origin=Origin(xyz=(0.066, 0.0, -0.460)),
        material=deep_red,
        name="lever_knob",
    )
    model.articulation(
        "cabinet_to_pull_lever",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=lever,
        origin=Origin(xyz=(lower_w / 2.0, -0.055, 1.16)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=3.0, lower=-0.75, upper=0.90),
    )

    # Hinged service door on the lower front.  Its part frame is the bottom of
    # the vertical hinge line, so positive motion swings the free edge outward.
    service_door = model.part("service_door")
    service_door.visual(
        Box((door_w, 0.022, door_h)),
        origin=Origin(xyz=(door_w / 2.0, 0.0, door_h / 2.0)),
        material=deep_red,
        name="door_panel",
    )
    service_door.visual(
        Box((door_w - 0.055, 0.010, 0.040)),
        origin=Origin(xyz=(door_w / 2.0 + 0.010, -0.016, door_h - 0.075)),
        material=chrome,
        name="door_pull",
    )
    service_door.visual(
        Cylinder(radius=0.014, length=door_h + 0.025),
        origin=Origin(xyz=(0.0, 0.0, door_h / 2.0)),
        material=chrome,
        name="hinge_barrel",
    )
    model.articulation(
        "cabinet_to_service_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=service_door,
        origin=Origin(xyz=(door_left, front_y - 0.016, door_bottom)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=10.0, velocity=2.0, lower=0.0, upper=1.65),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
