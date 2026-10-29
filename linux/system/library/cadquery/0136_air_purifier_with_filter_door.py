# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

from __future__ import annotations

import cadquery as cq
import math
from contextlib import suppress
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union
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

# ===== panels_vents (7 syms) =====
def _centered_axis_positions(limit, pitch):
    """Symmetric positions in [-limit, +limit] spaced by `pitch`, centered on 0."""
    if limit < -1e-9:
        return []
    if limit <= 1e-9:
        return [0.0]
    count = int((2.0 * limit) / pitch) + 1
    if count <= 0:
        return []
    return [((index - (count - 1) * 0.5) * pitch) for index in range(count)]

def _panels_vents_finish(self, shape, center):
    """Coerce the (Workplane/Shape) result to a solid, optionally drop its
    rear-most face to z=0 (center=False), and store it on the geometry."""
    solid = _to_shape(shape)
    if not center:
        bb = solid.BoundingBox()
        if abs(bb.zmin) > 1e-12:
            solid = solid.translate(cq.Vector(0.0, 0.0, -bb.zmin))
    self._set(solid)

@dataclass(frozen=True)
class VentGrilleSlats:
    profile: str = "flat"
    direction: str = "down"
    inset: float = 0.0
    divider_count: int = 0
    divider_width: float = 0.004

@dataclass(frozen=True)
class VentGrilleFrame:
    style: str = "flush"
    depth: float = 0.0

@dataclass(frozen=True)
class VentGrilleMounts:
    style: str = "none"
    inset: float = 0.008
    hole_diameter: Optional[float] = None

@dataclass(frozen=True)
class VentGrilleSleeve:
    style: str = "full"
    depth: Optional[float] = None
    wall: Optional[float] = None

class VentGrilleGeometry(MeshGeometry):
    """Framed vent/register face (XY, extruded along Z) with real slats and an
    optional shallow rear sleeve. The front flange is centered on local z=0 and
    the sleeve extends toward -Z."""

    def __init__(
        self,
        panel_size,
        *,
        frame=0.012,
        face_thickness=0.004,
        duct_depth=0.026,
        duct_wall=0.003,
        slat_pitch=0.018,
        slat_width=0.009,
        slat_angle_deg=35.0,
        slat_thickness=None,
        corner_radius=0.0,
        slats=None,
        frame_profile=None,
        mounts=None,
        sleeve=None,
        center=True,
    ):
        super().__init__()
        panel_w = float(panel_size[0])
        panel_h = float(panel_size[1])
        frame = float(frame)
        face_t = float(face_thickness)
        duct_depth = float(duct_depth)
        duct_wall = float(duct_wall)
        slat_pitch = float(slat_pitch)
        slat_w = float(slat_width)
        slat_t = float(slat_thickness) if slat_thickness is not None else max(0.001, face_t * 0.35)
        corner_radius = max(0.0, float(corner_radius))
        slats = slats or VentGrilleSlats()
        frame_profile = frame_profile or VentGrilleFrame()
        mounts = mounts or VentGrilleMounts()
        sleeve = sleeve or VentGrilleSleeve()

        if panel_w <= 0 or panel_h <= 0:
            raise ValidationError("panel_size must be positive")
        if face_t <= 0 or duct_depth <= 0 or duct_wall <= 0:
            raise ValidationError("face_thickness, duct_depth, and duct_wall must be positive")
        if frame <= 0 or frame >= min(panel_w, panel_h) * 0.5:
            raise ValidationError("frame must be > 0 and less than half of min(panel_size)")
        if slat_pitch <= 0 or slat_w <= 0 or slat_t <= 0:
            raise ValidationError("slat_pitch, slat_width, and slat_thickness must be positive")
        if slat_pitch <= slat_w:
            raise ValidationError("slat_pitch must be greater than slat_width")

        slat_profile = str(slats.profile)
        if slat_profile not in {"flat", "airfoil", "boxed"}:
            raise ValidationError("slats.profile must be one of flat, airfoil, or boxed")
        slat_direction = str(slats.direction)
        if slat_direction not in {"down", "up"}:
            raise ValidationError("slats.direction must be one of down or up")
        slat_inset = float(slats.inset)
        divider_count = int(slats.divider_count)
        divider_width = float(slats.divider_width)
        if slat_inset < 0.0:
            raise ValidationError("slats.inset must be non-negative")
        if divider_count < 0:
            raise ValidationError("slats.divider_count must be non-negative")
        if divider_count > 0 and divider_width <= 0.0:
            raise ValidationError("slats.divider_width must be positive when dividers are requested")

        frame_style = str(frame_profile.style)
        if frame_style not in {"flush", "beveled", "radiused"}:
            raise ValidationError("frame_profile.style must be one of flush, beveled, or radiused")
        frame_depth = float(frame_profile.depth)
        if frame_depth < 0.0:
            raise ValidationError("frame_profile.depth must be non-negative")

        mount_style = str(mounts.style)
        if mount_style not in {"none", "holes"}:
            raise ValidationError("mounts.style must be one of none or holes")
        mount_inset = float(mounts.inset)
        if mount_inset < 0.0:
            raise ValidationError("mounts.inset must be non-negative")
        mount_hole_diameter = (
            float(mounts.hole_diameter)
            if mounts.hole_diameter is not None
            else max(frame * 0.36, 0.0032)
        )
        if mount_style != "none" and mount_hole_diameter <= 0.0:
            raise ValidationError("mounts.hole_diameter must be positive when mounts are enabled")

        sleeve_style = str(sleeve.style)
        if sleeve_style not in {"none", "short", "full"}:
            raise ValidationError("sleeve.style must be one of none, short, or full")
        sleeve_depth = float(sleeve.depth) if sleeve.depth is not None else duct_depth
        sleeve_wall = float(sleeve.wall) if sleeve.wall is not None else duct_wall
        if sleeve_style == "short" and sleeve.depth is None:
            sleeve_depth = max(face_t * 1.8, duct_depth * 0.45)
        if sleeve_style == "none":
            sleeve_depth = 0.0
        if sleeve_style != "none" and sleeve_depth <= 0.0:
            raise ValidationError("sleeve.depth must be positive when sleeve.style is not none")
        if sleeve_style != "none" and sleeve_wall <= 0.0:
            raise ValidationError("sleeve.wall must be positive when sleeve.style is not none")

        opening_w = panel_w - 2.0 * frame
        opening_h = panel_h - 2.0 * frame
        if sleeve_style != "none" and (
            opening_w <= 2.0 * sleeve_wall or opening_h <= 2.0 * sleeve_wall
        ):
            raise ValidationError("frame/duct_wall leave no open sleeve area")
        y = -opening_h * 0.5 + slat_pitch * 0.5
        limit = opening_h * 0.5 - slat_pitch * 0.5
        slat_rows = []
        while y <= limit + 1e-9:
            slat_rows.append(y)
            y += slat_pitch
        if not slat_rows:
            raise ValidationError("No slat rows fit panel; increase panel height or reduce slat_pitch")

        if divider_count > 0:
            usable_divider_span = opening_w - divider_width
            if usable_divider_span <= 0.0:
                raise ValidationError("slats.divider_width leaves no grille opening")
            divider_pitch = usable_divider_span / float(divider_count + 1)
            if divider_pitch <= divider_width:
                raise ValidationError("slats.divider_count/divider_width leave no usable openings")

        mount_positions = [
            (panel_w * 0.5 - mount_inset, panel_h * 0.5 - mount_inset),
            (-panel_w * 0.5 + mount_inset, panel_h * 0.5 - mount_inset),
            (panel_w * 0.5 - mount_inset, -panel_h * 0.5 + mount_inset),
            (-panel_w * 0.5 + mount_inset, -panel_h * 0.5 + mount_inset),
        ]
        if mount_style != "none":
            hole_radius = mount_hole_diameter * 0.5
            if hole_radius >= frame * 0.80:
                raise ValidationError("mounts.hole_diameter is too large for the frame width")
            for hole_x, hole_y in mount_positions:
                if (
                    abs(hole_x) + hole_radius > panel_w * 0.5
                    or abs(hole_y) + hole_radius > panel_h * 0.5
                ):
                    raise ValidationError("mounts.inset places holes outside the face")

        shape = cq.Workplane("XY").box(panel_w, panel_h, face_t)
        if corner_radius > 0.0:
            shape = shape.edges("|Z").fillet(
                min(corner_radius, panel_w * 0.5 - frame, panel_h * 0.5 - frame)
            )
        if frame_style == "beveled" and frame_depth > 1.0e-9:
            shape = shape.edges(">Z").chamfer(min(frame_depth, frame * 0.7, face_t * 0.7))
        elif frame_style == "radiused" and frame_depth > 1.0e-9:
            shape = shape.edges(">Z").fillet(min(frame_depth, frame * 0.7, face_t * 0.48))

        shape = shape.cut(
            cq.Workplane("XY").box(
                opening_w,
                opening_h,
                face_t + max(0.002, face_t * 0.5),
            )
        )

        if sleeve_style != "none":
            duct_outer = cq.Workplane("XY").box(opening_w, opening_h, sleeve_depth)
            duct_inner = cq.Workplane("XY").box(
                opening_w - 2.0 * sleeve_wall,
                opening_h - 2.0 * sleeve_wall,
                sleeve_depth + face_t + 0.004,
            )
            duct_shell = duct_outer.cut(duct_inner).translate(
                (0.0, 0.0, -face_t * 0.5 - sleeve_depth * 0.5 + min(face_t * 0.25, 0.001))
            )
            shape = shape.union(duct_shell)

        slat_embed = min(frame * 0.5, 0.002)
        slat_clear_w = opening_w - max(0.0, divider_count * divider_width)
        slat_chord = max(1.0e-4, slat_clear_w + 2.0 * slat_embed)
        slat_z = -face_t * 0.25 - slat_inset
        slat_angle = abs(float(slat_angle_deg)) * (-1.0 if slat_direction == "down" else 1.0)

        def _make_slat():
            if slat_profile == "flat":
                return cq.Workplane("XY").box(slat_chord, slat_w, slat_t)
            if slat_profile == "boxed":
                box_t = max(slat_t * 1.35, slat_w * 0.42)
                return cq.Workplane("XY").box(slat_chord, slat_w, box_t)

            section_points = [
                (-0.50 * slat_w, 0.00),
                (-0.22 * slat_w, 0.56 * slat_t),
                (0.08 * slat_w, 0.64 * slat_t),
                (0.44 * slat_w, 0.10 * slat_t),
                (0.34 * slat_w, -0.22 * slat_t),
                (-0.10 * slat_w, -0.38 * slat_t),
                (-0.44 * slat_w, -0.14 * slat_t),
            ]
            return (
                cq.Workplane("YZ")
                .workplane(offset=-slat_chord * 0.5)
                .polyline(section_points)
                .close()
                .extrude(slat_chord)
            )

        for row_y in slat_rows:
            slat = _make_slat()
            slat = slat.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), slat_angle)
            slat = slat.translate((0.0, row_y, slat_z))
            shape = shape.union(slat)

        if divider_count > 0:
            divider_positions = _centered_axis_positions(
                opening_w * 0.5 - divider_width * 0.5,
                (opening_w - divider_width) / float(divider_count + 1),
            )
            divider_positions = (
                divider_positions[1:-1]
                if len(divider_positions) > divider_count
                else divider_positions
            )
            divider_depth = max(face_t * 0.90, slat_t * 1.10)
            divider_span_y = opening_h + min(frame * 0.35, 0.003)
            for x_pos in divider_positions[:divider_count]:
                divider = cq.Workplane("XY").box(divider_width, divider_span_y, divider_depth)
                divider = divider.translate((x_pos, 0.0, -face_t * 0.18))
                shape = shape.union(divider)

        if mount_style != "none":
            hole_depth = face_t + max(sleeve_depth, 0.0) + 0.01
            for hole_x, hole_y in mount_positions:
                hole = (
                    cq.Workplane("XY")
                    .circle(mount_hole_diameter * 0.5)
                    .extrude(hole_depth * 0.5, both=True)
                    .translate((hole_x, hole_y, -max(sleeve_depth, 0.0) * 0.5))
                )
                shape = shape.cut(hole)

        _panels_vents_finish(self, shape, center)

# ===== model =====
import math
import cadquery as cq
HOUSING_W = 0.54
HOUSING_D = 0.18
HOUSING_H = 0.82
DOOR_W = 0.46
DOOR_T = 0.026
DOOR_H = 0.57
HINGE_Y = 0.205
HINGE_Z = 0.125
def _safe_front_fillet(model: cq.Workplane, radius: float) -> cq.Workplane:
    """Add a soft medical-appliance edge treatment without making construction brittle."""
    try:
        return model.faces(">Y").edges().fillet(radius)
    except Exception:
        return model
def _housing_shell() -> cq.Workplane:
    """Single connected, flat-backed purifier shell with a real recessed filter opening."""
    body = cq.Workplane("XY").box(HOUSING_W, HOUSING_D, HOUSING_H).translate(
        (0.0, HOUSING_D / 2.0, HOUSING_H / 2.0)
    )
    body = _safe_front_fillet(body, 0.014)

    # Cut only from the front toward the back so the rear wall stays flat and closed.
    cutter = cq.Workplane("XY").box(0.430, 0.300, 0.565).translate((0.0, 0.180, 0.410))
    body = body.cut(cutter)

    # A small lower service-lip relief makes the hinge area read as a service door sill.
    lip_cutter = cq.Workplane("XY").box(0.500, 0.090, 0.026).translate((0.0, 0.190, 0.112))
    body = body.cut(lip_cutter)
    return body
def _door_panel() -> cq.Workplane:
    """Rounded but flat rectangular access door, authored in the child hinge frame."""
    # The lower edge clears the hinge pin; the hinge leaf below visibly carries the load.
    panel = cq.Workplane("XY").box(DOOR_W, DOOR_T, DOOR_H).translate((0.0, 0.0, DOOR_H / 2.0 + 0.014))
    panel = _safe_front_fillet(panel, 0.010)
    return panel
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_mounted_medical_air_purifier")

    shell_mat = model.material("antimicrobial_warm_white", rgba=(0.86, 0.88, 0.88, 1.0))
    door_mat = model.material("powder_coated_white", rgba=(0.93, 0.94, 0.93, 1.0))
    trim_mat = model.material("soft_gray_trim", rgba=(0.62, 0.66, 0.68, 1.0))
    shadow_mat = model.material("cavity_shadow", rgba=(0.025, 0.030, 0.034, 1.0))
    filter_mat = model.material("hepa_filter_media", rgba=(0.72, 0.78, 0.80, 1.0))
    gasket_mat = model.material("blue_medical_gasket", rgba=(0.18, 0.46, 0.78, 1.0))
    metal_mat = model.material("brushed_stainless", rgba=(0.65, 0.67, 0.66, 1.0))
    latch_mat = model.material("satin_latch_gray", rgba=(0.40, 0.43, 0.44, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_housing_shell(), "housing_shell", tolerance=0.0008),
        material=shell_mat,
        name="housing_shell",
    )

    # Recessed filter cavity with visible pleated HEPA media behind the access panel.
    housing.visual(
        Box((0.402, 0.012, 0.498)),
        origin=Origin(xyz=(0.0, 0.034, 0.410)),
        material=shadow_mat,
        name="cavity_shadow",
    )
    housing.visual(
        Box((0.382, 0.010, 0.476)),
        origin=Origin(xyz=(0.0, 0.042, 0.410)),
        material=filter_mat,
        name="filter_media",
    )
    for i, x in enumerate([-0.165, -0.132, -0.099, -0.066, -0.033, 0.0, 0.033, 0.066, 0.099, 0.132, 0.165]):
        housing.visual(
            Box((0.010, 0.012, 0.462)),
            origin=Origin(xyz=(x, 0.050, 0.410)),
            material=model.material(f"pleat_shade_{i}", rgba=(0.62, 0.70, 0.73, 1.0))
            if i % 2
            else filter_mat,
            name=f"filter_pleat_{i}",
        )

    cavity_bezel = BezelGeometry(
        (0.410, 0.535),
        (0.468, 0.592),
        0.007,
        opening_shape="rounded_rect",
        outer_shape="rounded_rect",
        opening_corner_radius=0.010,
        outer_corner_radius=0.018,
    )
    housing.visual(
        mesh_from_geometry(cavity_bezel, "cavity_bezel"),
        origin=Origin(xyz=(0.0, 0.183, 0.410), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=gasket_mat,
        name="cavity_bezel",
    )

    # Fixed half of a continuous knuckle hinge and its load path back into the housing.
    housing.visual(
        Box((0.500, 0.020, 0.070)),
        origin=Origin(xyz=(0.0, 0.188, 0.077)),
        material=shell_mat,
        name="hinge_support",
    )
    housing.visual(
        Box((0.500, 0.012, 0.030)),
        origin=Origin(xyz=(0.0, 0.195, 0.105)),
        material=metal_mat,
        name="hinge_leaf",
    )

    hinge_centers = [-0.216, -0.162, -0.108, -0.054, 0.0, 0.054, 0.108, 0.162, 0.216]
    for i, x in enumerate(hinge_centers):
        if i % 2 == 0:
            housing.visual(
                Cylinder(radius=0.008, length=0.040),
                origin=Origin(xyz=(x, HINGE_Y, HINGE_Z), rpy=(0.0, math.pi / 2.0, 0.0)),
                material=metal_mat,
                name=f"fixed_knuckle_{i}",
            )

    # Upper corner detent keepers attached to the upper housing frame.
    for i, x in enumerate((-0.188, 0.188)):
        keeper_arm_name = ("keeper_arm_0", "keeper_arm_1")[i]
        keeper_name = ("keeper_0", "keeper_1")[i]
        housing.visual(
            Box((0.040, 0.044, 0.010)),
            origin=Origin(xyz=(x, 0.202, 0.720)),
            material=metal_mat,
            name=keeper_arm_name,
        )
        housing.visual(
            Box((0.044, 0.008, 0.024)),
            origin=Origin(xyz=(x, 0.224, 0.729)),
            material=metal_mat,
            name=keeper_name,
        )

    door = model.part("filter_door")
    door.visual(
        mesh_from_cadquery(_door_panel(), "door_panel", tolerance=0.0008),
        material=door_mat,
        name="door_panel",
    )
    # A raised perimeter lip on the front panel reads as a gasketed medical service door.
    door.visual(
        Box((0.430, 0.008, 0.030)),
        origin=Origin(xyz=(0.0, 0.017, 0.548)),
        material=trim_mat,
        name="top_lip",
    )
    door.visual(
        Box((0.430, 0.008, 0.028)),
        origin=Origin(xyz=(0.0, 0.017, 0.030)),
        material=trim_mat,
        name="bottom_lip",
    )
    for i, x in enumerate((-0.219, 0.219)):
        door.visual(
            Box((0.020, 0.008, 0.520)),
            origin=Origin(xyz=(x, 0.017, 0.286)),
            material=trim_mat,
            name=f"side_lip_{i}",
        )

    grille = VentGrilleGeometry(
        (0.358, 0.086),
        frame=0.010,
        face_thickness=0.004,
        duct_depth=0.012,
        duct_wall=0.0025,
        slat_pitch=0.013,
        slat_width=0.006,
        slat_angle_deg=32.0,
        corner_radius=0.006,
        slats=VentGrilleSlats(profile="airfoil", direction="down", inset=0.002, divider_count=2),
        frame_profile=VentGrilleFrame(style="beveled", depth=0.001),
        sleeve=VentGrilleSleeve(style="short", depth=0.010, wall=0.0025),
    )
    door.visual(
        mesh_from_geometry(grille, "front_grille"),
        origin=Origin(xyz=(0.0, 0.015, 0.392), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_mat,
        name="front_grille",
    )

    # Moving half of the piano hinge: alternating knuckles plus a leaf tied to the door.
    door.visual(
        Box((0.460, 0.008, 0.032)),
        origin=Origin(xyz=(0.0, 0.012, 0.016)),
        material=metal_mat,
        name="door_hinge_leaf",
    )
    for i, x in enumerate(hinge_centers):
        if i % 2 == 1:
            door.visual(
                Cylinder(radius=0.008, length=0.040),
                origin=Origin(xyz=(x, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
                material=metal_mat,
                name=f"door_knuckle_{i}",
            )

    # Stationary bosses on the door carry the two rotating upper-corner latches.
    latch_origins = [(-0.188, 0.019, 0.520), (0.188, 0.019, 0.520)]
    for i, (x, y, z) in enumerate(latch_origins):
        latch_boss_name = ("latch_boss_0", "latch_boss_1")[i]
        door.visual(
            Cylinder(radius=0.013, length=0.006),
            origin=Origin(xyz=(x, y - 0.003, z), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=metal_mat,
            name=latch_boss_name,
        )

    model.articulation(
        "housing_to_filter_door",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=door,
        origin=Origin(xyz=(0.0, HINGE_Y, HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2, lower=0.0, upper=1.75),
    )

    for i, (x, y, z) in enumerate(latch_origins):
        latch = model.part(f"upper_latch_{i}")
        latch.visual(
            Cylinder(radius=0.016, length=0.008),
            origin=Origin(xyz=(0.0, 0.004, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=latch_mat,
            name="latch_disk",
        )
        latch.visual(
            Box((0.030, 0.006, 0.090)),
            origin=Origin(xyz=(0.0, 0.008, 0.045)),
            material=latch_mat,
            name="latch_tab",
        )
        latch.visual(
            Box((0.038, 0.008, 0.012)),
            origin=Origin(xyz=(0.0, 0.010, 0.086)),
            material=latch_mat,
            name="detent_hook",
        )
        model.articulation(
            f"door_to_latch_{i}",
            ArticulationType.REVOLUTE,
            parent=door,
            child=latch,
            origin=Origin(xyz=(x, y, z)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=1.0, velocity=2.0, lower=-0.65, upper=0.65),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
