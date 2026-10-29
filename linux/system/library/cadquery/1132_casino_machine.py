# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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

# ===== panels_vents (4 syms) =====
def _normalize_pitch_2d(pitch, *, name="pitch"):
    """Accept a positive scalar or a positive 2-sequence -> (pitch_x, pitch_y)."""
    if isinstance(pitch, Sequence) and not isinstance(pitch, (str, bytes)):
        values = list(pitch)
        if len(values) != 2:
            raise ValidationError("%s must be a positive scalar or a 2-tuple" % name)
        pitch_x = float(values[0])
        pitch_y = float(values[1])
    else:
        pitch_x = float(pitch)
        pitch_y = float(pitch)
    if pitch_x <= 0.0 or pitch_y <= 0.0:
        raise ValidationError("%s values must be positive" % name)
    return (pitch_x, pitch_y)

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

class SlotPatternPanelGeometry(MeshGeometry):
    """Rectangular plate (XY, extruded along Z) with a grid of rounded slots."""

    def __init__(
        self,
        panel_size,
        thickness,
        *,
        slot_size,
        pitch,
        frame=0.008,
        corner_radius=0.0,
        slot_angle_deg=0.0,
        stagger=False,
        center=True,
    ):
        super().__init__()
        panel_w = float(panel_size[0])
        panel_h = float(panel_size[1])
        thickness = float(thickness)
        slot_length = float(slot_size[0])
        slot_width = float(slot_size[1])
        frame = float(frame)
        corner_radius = max(0.0, float(corner_radius))
        slot_angle_deg = float(slot_angle_deg)
        pitch_x, pitch_y = _normalize_pitch_2d(pitch)

        if panel_w <= 0.0 or panel_h <= 0.0 or thickness <= 0.0:
            raise ValidationError("panel_size and thickness must be positive")
        if slot_length <= 0.0 or slot_width <= 0.0:
            raise ValidationError("slot_size values must be positive")
        if slot_length < slot_width:
            raise ValidationError("slot_size[0] must be greater than or equal to slot_size[1]")
        if frame < 0.0 or frame >= min(panel_w, panel_h) * 0.5:
            raise ValidationError("frame must be >= 0 and less than half of min(panel_size)")
        if abs(slot_angle_deg) >= 90.0:
            raise ValidationError("abs(slot_angle_deg) must be < 90")

        slot_angle_rad = slot_angle_deg * math.pi / 180.0
        slot_half_x = 0.5 * (
            abs(slot_length * math.cos(slot_angle_rad)) + abs(slot_width * math.sin(slot_angle_rad))
        )
        slot_half_y = 0.5 * (
            abs(slot_length * math.sin(slot_angle_rad)) + abs(slot_width * math.cos(slot_angle_rad))
        )
        if pitch_x <= 2.0 * slot_half_x or pitch_y <= 2.0 * slot_half_y:
            raise ValidationError("pitch must be greater than the rotated slot envelope on both axes")

        x_limit = panel_w * 0.5 - frame - slot_half_x
        y_limit = panel_h * 0.5 - frame - slot_half_y
        if x_limit < -1e-9 or y_limit < -1e-9:
            raise ValidationError("frame/slot_size leave no usable slot area")

        y_positions = _centered_axis_positions(y_limit, pitch_y)
        if not y_positions:
            raise ValidationError("No slot rows fit panel; increase panel size or reduce pitch")

        point_rows = []
        for row_index, y in enumerate(y_positions):
            x_offset = pitch_x * 0.5 if stagger and row_index % 2 == 1 else 0.0
            row_limit = x_limit - abs(x_offset)
            if row_limit < -1e-9:
                continue
            x_positions = _centered_axis_positions(row_limit, pitch_x)
            row_points = [(x + x_offset, y) for x in x_positions]
            if row_points:
                point_rows.append(row_points)
        if not point_rows:
            raise ValidationError("No slot columns fit panel; increase panel size or reduce pitch")

        shape = cq.Workplane("XY").box(panel_w, panel_h, thickness)
        if corner_radius > 0.0:
            shape = shape.edges("|Z").fillet(
                min(corner_radius, panel_w * 0.5 - 1e-4, panel_h * 0.5 - 1e-4)
            )

        cut_depth = thickness + max(0.002, thickness * 0.5)
        slot_core_length = max(slot_length - slot_width, 0.0)

        def build_slot_cut(center_xy):
            slot_cut = None
            if slot_core_length > 1e-6:
                slot_cut = cq.Workplane("XY").box(slot_core_length, slot_width, cut_depth)
            cap_radius = slot_width * 0.5
            cap_offset = slot_core_length * 0.5
            left_cap = (
                cq.Workplane("XY")
                .circle(cap_radius)
                .extrude(cut_depth, both=True)
                .translate((-cap_offset, 0.0, 0.0))
            )
            right_cap = (
                cq.Workplane("XY")
                .circle(cap_radius)
                .extrude(cut_depth, both=True)
                .translate((cap_offset, 0.0, 0.0))
            )
            slot_cut = (
                left_cap.union(right_cap)
                if slot_cut is None
                else slot_cut.union(left_cap).union(right_cap)
            )
            slot_cut = slot_cut.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), slot_angle_deg)
            return slot_cut.translate((center_xy[0], center_xy[1], 0.0))

        cut_shape = None
        for row_points in point_rows:
            for point in row_points:
                slot_cut = build_slot_cut(point)
                cut_shape = slot_cut if cut_shape is None else cut_shape.union(slot_cut)
        if cut_shape is not None:
            shape = shape.cut(cut_shape)

        _panels_vents_finish(self, shape, center)

# ===== model =====
import math
import cadquery as cq
def _button_sleeve_mesh():
    """A real hollow collar: the red plunger stem slides through the bore."""
    sleeve = (
        cq.Workplane("XY")
        .circle(0.066)
        .circle(0.034)
        .extrude(0.067)
    )
    return mesh_from_cadquery(sleeve, "spin_button_guide_sleeve", tolerance=0.0005)
def _tile_y(radius: float, z_offset: float, thickness: float) -> float:
    """Place flat reel symbol tiles so each tile locally bites into the drum skin."""
    surface = -math.sqrt(max(radius * radius - z_offset * z_offset, 0.0))
    return surface - 0.5 * thickness + 0.003
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="modern_five_reel_casino_cabinet")

    black = model.material("satin_black", rgba=(0.015, 0.014, 0.017, 1.0))
    graphite = model.material("graphite_metal", rgba=(0.10, 0.105, 0.115, 1.0))
    chrome = model.material("brushed_chrome", rgba=(0.72, 0.72, 0.68, 1.0))
    glass = model.material("smoked_glass", rgba=(0.08, 0.18, 0.26, 0.38))
    reel_plastic = model.material("warm_reel_plastic", rgba=(0.94, 0.89, 0.72, 1.0))
    red = model.material("translucent_red", rgba=(0.95, 0.03, 0.02, 1.0))
    amber = model.material("amber_led", rgba=(1.0, 0.62, 0.05, 1.0))
    blue_led = model.material("blue_led", rgba=(0.06, 0.30, 0.95, 1.0))
    green = model.material("green_symbol", rgba=(0.08, 0.72, 0.18, 1.0))
    gold = model.material("gold_symbol", rgba=(0.95, 0.76, 0.18, 1.0))
    violet = model.material("violet_symbol", rgba=(0.58, 0.20, 0.95, 1.0))
    white = model.material("white_symbol", rgba=(0.96, 0.95, 0.90, 1.0))

    cabinet = model.part("cabinet")

    # Main carcass: a broad, glossy machine body with a rear service opening.
    cabinet.visual(Box((1.20, 0.76, 0.20)), origin=Origin(xyz=(0.0, 0.0, 0.10)), material=graphite, name="base_plinth")
    cabinet.visual(Box((0.085, 0.76, 1.38)), origin=Origin(xyz=(-0.585, 0.0, 0.85)), material=black, name="side_column_0")
    cabinet.visual(Box((0.085, 0.76, 1.38)), origin=Origin(xyz=(0.585, 0.0, 0.85)), material=black, name="side_column_1")
    cabinet.visual(Box((1.20, 0.76, 0.12)), origin=Origin(xyz=(0.0, 0.0, 1.59)), material=black, name="top_cap")
    cabinet.visual(Box((1.13, 0.13, 0.56)), origin=Origin(xyz=(0.0, -0.335, 0.43)), material=graphite, name="lower_front_panel")
    cabinet.visual(Box((1.16, 0.34, 0.080)), origin=Origin(xyz=(0.0, -0.455, 0.620)), material=black, name="control_deck")
    cabinet.visual(Box((1.16, 0.020, 0.46)), origin=Origin(xyz=(0.0, 0.030, 1.14)), material=black, name="reel_shadow_box")

    # Front display face with a real framed opening rather than a solid panel.
    display_bezel = BezelGeometry(
        (0.995, 0.430),
        (1.145, 0.610),
        0.040,
        opening_shape="rounded_rect",
        outer_shape="rounded_rect",
        opening_corner_radius=0.030,
        outer_corner_radius=0.050,
    )
    cabinet.visual(
        mesh_from_geometry(display_bezel, "broad_display_bezel"),
        origin=Origin(xyz=(0.0, -0.370, 1.150), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="display_bezel",
    )
    cabinet.visual(Box((1.000, 0.006, 0.420)), origin=Origin(xyz=(0.0, -0.404, 1.150)), material=glass, name="display_glass")
    for idx, x in enumerate((-0.30, -0.10, 0.10, 0.30)):
        cabinet.visual(Box((0.014, 0.018, 0.440)), origin=Origin(xyz=(x, -0.398, 1.150)), material=chrome, name=f"reel_separator_{idx}")

    # Marquee and credit/readout strips on the broad face.
    cabinet.visual(Box((0.92, 0.030, 0.085)), origin=Origin(xyz=(0.0, -0.392, 1.475)), material=blue_led, name="top_marquee")
    cabinet.visual(Box((0.42, 0.010, 0.050)), origin=Origin(xyz=(-0.30, -0.618, 0.685)), material=amber, name="credit_display")

    # Rear frame around the hinged maintenance panel.
    cabinet.visual(Box((1.13, 0.040, 0.065)), origin=Origin(xyz=(0.0, 0.360, 1.475)), material=graphite, name="rear_top_rail")
    cabinet.visual(Box((1.13, 0.040, 0.065)), origin=Origin(xyz=(0.0, 0.360, 0.365)), material=graphite, name="rear_bottom_rail")
    cabinet.visual(Box((0.055, 0.040, 1.08)), origin=Origin(xyz=(-0.555, 0.360, 0.920)), material=graphite, name="rear_edge_0")
    cabinet.visual(Box((0.055, 0.040, 1.08)), origin=Origin(xyz=(0.555, 0.360, 0.920)), material=graphite, name="rear_edge_1")
    cabinet.visual(Cylinder(0.014, 1.08), origin=Origin(xyz=(-0.618, 0.392, 0.920)), material=chrome, name="rear_hinge_pin")

    # The static guide sleeve is a hollow ring proud of the shallow deck.
    cabinet.visual(
        _button_sleeve_mesh(),
        origin=Origin(xyz=(0.380, -0.520, 0.655)),
        material=chrome,
        name="spin_button_sleeve",
    )

    # Five independently rotating reels.  Each part carries its shaft segment,
    # drum, side flanges, and symbol tiles so the whole reel spins together.
    reel_radius = 0.180
    reel_width = 0.150
    tile_thickness = 0.010
    tile_mats: tuple[Material, ...] = (red, green, gold, violet, white)
    reel_xs = (-0.400, -0.200, 0.0, 0.200, 0.400)
    for i, x in enumerate(reel_xs):
        for side, sx in enumerate((x - 0.096, x + 0.096)):
            cabinet.visual(
                Box((0.016, 0.040, 0.028)),
                origin=Origin(xyz=(sx, -0.200, 1.122)),
                material=chrome,
                name=f"reel_{i}_bearing_{side}",
            )
            cabinet.visual(
                Box((0.016, 0.240, 0.020)),
                origin=Origin(xyz=(sx, -0.085, 1.108)),
                material=graphite,
                name=f"reel_{i}_bearing_arm_{side}",
            )
        reel = model.part(f"reel_{i}")
        reel.visual(
            Cylinder(reel_radius, reel_width),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_plastic,
            name="drum",
        )
        reel.visual(
            Cylinder(0.014, 0.190),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="shaft",
        )
        reel.visual(
            Cylinder(reel_radius + 0.006, 0.012),
            origin=Origin(xyz=(-0.078, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="flange_0",
        )
        reel.visual(
            Cylinder(reel_radius + 0.006, 0.012),
            origin=Origin(xyz=(0.078, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="flange_1",
        )
        for j, zoff in enumerate((-0.105, 0.0, 0.105)):
            reel.visual(
                Box((0.118, tile_thickness, 0.064)),
                origin=Origin(xyz=(0.0, _tile_y(reel_radius, zoff, tile_thickness), zoff)),
                material=tile_mats[(i + j) % len(tile_mats)],
                name=f"symbol_tile_{j}",
            )
        model.articulation(
            f"cabinet_to_reel_{i}",
            ArticulationType.CONTINUOUS,
            parent=cabinet,
            child=reel,
            origin=Origin(xyz=(x, -0.200, 1.150)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.5, velocity=20.0),
            motion_properties=MotionProperties(damping=0.015, friction=0.0),
        )

    # Spring-loaded spin button.  The child frame is at the underside of the cap
    # at the unpressed position; positive motion translates the plunger downward.
    spin_button = model.part("spin_button")
    spin_button.visual(Cylinder(0.055, 0.028), origin=Origin(xyz=(0.0, 0.0, 0.014)), material=red, name="cap")
    spin_button.visual(Cylinder(0.025, 0.050), origin=Origin(xyz=(0.0, 0.0, -0.025)), material=chrome, name="stem")
    model.articulation(
        "cabinet_to_spin_button",
        ArticulationType.PRISMATIC,
        parent=cabinet,
        child=spin_button,
        origin=Origin(xyz=(0.380, -0.520, 0.722)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=12.0, velocity=0.12, lower=0.0, upper=0.012),
    )

    # Rear maintenance panel, hinged along one vertical cabinet edge.
    panel = model.part("rear_panel")
    panel.visual(Box((1.050, 0.035, 1.050)), origin=Origin(xyz=(0.538, 0.0, 0.0)), material=graphite, name="panel_slab")
    panel.visual(Box((0.020, 0.024, 1.050)), origin=Origin(xyz=(0.005, 0.0, 0.0)), material=chrome, name="hinge_leaf")
    panel.visual(Box((0.070, 0.030, 0.160)), origin=Origin(xyz=(0.950, 0.030, 0.050)), material=black, name="pull_handle")
    rear_vent = SlotPatternPanelGeometry(
        (0.480, 0.300),
        0.004,
        slot_size=(0.060, 0.010),
        pitch=(0.085, 0.035),
        frame=0.020,
        corner_radius=0.012,
        stagger=True,
    )
    panel.visual(
        mesh_from_geometry(rear_vent, "rear_panel_slotted_vent"),
        origin=Origin(xyz=(0.550, 0.019, 0.120), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="service_vent",
    )
    model.articulation(
        "cabinet_to_rear_panel",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=panel,
        origin=Origin(xyz=(-0.600, 0.405, 0.920)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.0, lower=0.0, upper=1.75),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
