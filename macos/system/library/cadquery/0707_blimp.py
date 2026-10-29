# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Literal, Optional
from dataclasses import dataclass, field
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

# ===== fans (5 syms) =====
def _fans_shift_to_z0(solid):
    """Place the rear-most face on z=0 (sdk center=False behaviour)."""
    bb = solid.BoundingBox()
    return solid.translate(cq.Vector(0.0, 0.0, -bb.zmin))

@dataclass(frozen=True)
class FanRotorBlade:
    shape: Literal["straight", "scimitar", "broad", "narrow"] = "straight"
    tip_pitch_deg: Optional[float] = None
    camber: float = 0.0
    tip_clearance: float = 0.0

@dataclass(frozen=True)
class FanRotorHub:
    style: Literal["flat", "domed", "capped", "spinner"] = "domed"
    rear_collar_height: Optional[float] = None
    rear_collar_radius: Optional[float] = None
    bore_diameter: Optional[float] = None

@dataclass(frozen=True)
class FanRotorShroud:
    thickness: float
    depth: Optional[float] = None
    clearance: float = 0.0
    lip_depth: float = 0.0

class FanRotorGeometry(MeshGeometry):
    """
    Build an axial fan rotor with a central hub and pitched blades.
    """

    def __init__(
        self,
        outer_radius: float,
        hub_radius: float,
        blade_count: int,
        *,
        thickness: float,
        blade_pitch_deg: float = 28.0,
        blade_sweep_deg: float = 20.0,
        blade_root_chord: Optional[float] = None,
        blade_tip_chord: Optional[float] = None,
        blade: Optional[FanRotorBlade] = None,
        hub: Optional[FanRotorHub] = None,
        shroud: Optional[FanRotorShroud] = None,
        center: bool = True,
    ):
        super().__init__()
        outer_radius = float(outer_radius)
        hub_radius = float(hub_radius)
        thickness = float(thickness)
        blade_pitch_deg = float(blade_pitch_deg)
        blade_sweep_deg = float(blade_sweep_deg)
        blade_count = int(blade_count)
        blade = blade or FanRotorBlade()
        hub = hub or FanRotorHub()

        if outer_radius <= 0.0 or hub_radius <= 0.0 or thickness <= 0.0:
            raise ValueError("outer_radius, hub_radius, and thickness must be positive")
        if blade_count < 2:
            raise ValueError("blade_count must be at least 2")
        if hub_radius >= outer_radius:
            raise ValueError("hub_radius must be less than outer_radius")
        if abs(blade_pitch_deg) >= 85.0:
            raise ValueError("abs(blade_pitch_deg) must be < 85")
        if abs(blade_sweep_deg) >= 85.0:
            raise ValueError("abs(blade_sweep_deg) must be < 85")

        radial_span = outer_radius - hub_radius
        root_chord = (
            float(blade_root_chord)
            if blade_root_chord is not None
            else max(radial_span * 0.32, thickness * 1.5)
        )
        tip_chord = (
            float(blade_tip_chord)
            if blade_tip_chord is not None
            else max(radial_span * 0.20, thickness * 1.2)
        )
        if root_chord <= 0.0 or tip_chord <= 0.0:
            raise ValueError("blade_root_chord and blade_tip_chord must be positive")
        if max(root_chord, tip_chord) >= outer_radius * 1.6:
            raise ValueError("blade chords are too large for the rotor envelope")

        blade_shape = str(blade.shape)
        if blade_shape not in {"straight", "scimitar", "broad", "narrow"}:
            raise ValueError("blade.shape must be one of straight, scimitar, broad, or narrow")
        hub_style = str(hub.style)
        if hub_style not in {"flat", "domed", "capped", "spinner"}:
            raise ValueError("hub.style must be one of flat, domed, capped, or spinner")

        tip_pitch_deg = (
            float(blade.tip_pitch_deg)
            if blade.tip_pitch_deg is not None
            else blade_pitch_deg * 0.56
        )
        if abs(tip_pitch_deg) >= 85.0:
            raise ValueError("abs(blade.tip_pitch_deg) must be < 85")
        camber = float(blade.camber)
        if abs(camber) > 0.50:
            raise ValueError("abs(blade.camber) must be <= 0.5")
        tip_clearance = float(blade.tip_clearance)
        if tip_clearance < 0.0:
            raise ValueError("blade.tip_clearance must be non-negative")

        shroud_thickness = 0.0
        shroud_depth = 0.0
        ring_inner_radius: Optional[float] = None
        ring_outer_radius: Optional[float] = None
        shroud_lip_depth = 0.0
        if shroud is not None:
            shroud_thickness = float(shroud.thickness)
            shroud_depth = (
                float(shroud.depth) if shroud.depth is not None else max(thickness * 0.80, 1.0e-4)
            )
            shroud_clearance = float(shroud.clearance)
            shroud_lip_depth = float(shroud.lip_depth)
            if shroud_thickness <= 0.0:
                raise ValueError("shroud.thickness must be positive")
            if shroud_depth <= 0.0:
                raise ValueError("shroud.depth must be positive")
            if shroud_clearance < 0.0:
                raise ValueError("shroud.clearance must be non-negative")
            if shroud_lip_depth < 0.0:
                raise ValueError("shroud.lip_depth must be non-negative")
            if tip_clearance > 1.0e-9:
                raise ValueError("blade.tip_clearance cannot be used with shroud")
            ring_outer_radius = outer_radius - shroud_clearance
            ring_inner_radius = ring_outer_radius - shroud_thickness
            if ring_outer_radius <= 0.0 or ring_inner_radius <= 0.0:
                raise ValueError("shroud dimensions exceed the rotor envelope")
            if ring_inner_radius <= hub_radius + max(thickness * 0.25, 1.0e-4):
                raise ValueError("shroud leaves no usable blade span")

        def lerp(a: float, b: float, t: float) -> float:
            return float(a) + (float(b) - float(a)) * float(t)

        def chord_scale(t: float) -> float:
            if blade_shape == "straight":
                return 1.00
            if blade_shape == "scimitar":
                return 1.08 - 0.16 * t + 0.05 * sin(pi * t)
            if blade_shape == "broad":
                return 1.05 + 0.10 * sin(pi * t) - 0.03 * t
            return 0.92 - 0.12 * t

        def sweep_factor(t: float) -> float:
            if blade_shape == "straight":
                return t
            if blade_shape == "scimitar":
                return min(1.25, 0.52 * t + 0.76 * t * t)
            if blade_shape == "broad":
                return min(1.08, 0.82 * t + 0.22 * sin(pi * t))
            return 0.82 * t

        def rotate_section_points(
            points: list,
            angle_rad: float,
        ) -> list:
            c = cos(angle_rad)
            s = sin(angle_rad)
            return [(y * c - z * s, y * s + z * c) for (y, z) in points]

        def blade_section_points(
            chord: float,
            section_thickness: float,
            pitch_deg: float,
            sweep_y: float,
            span_t: float,
        ) -> list:
            half_t = max(section_thickness * 0.5, chord * 0.011)
            camber_amplitude = camber * chord * 0.060
            skew_gain = 0.0
            if blade_shape == "scimitar":
                skew_gain = chord * (0.05 + 0.08 * span_t)
            elif blade_shape == "broad":
                skew_gain = chord * 0.03 * span_t
            elif blade_shape == "narrow":
                skew_gain = -chord * 0.04 * span_t

            upper: list = []
            lower: list = []
            for u in (0.00, 0.10, 0.24, 0.42, 0.62, 0.82, 1.00):
                chord_pos = (u - 0.5) * chord
                thickness_scale = max(0.12, sin(pi * u) ** 0.82)
                thickness_z = half_t * thickness_scale
                camber_z = camber_amplitude * sin(pi * u)
                skew_y = skew_gain * sin(pi * u) * (u - 0.20)
                upper.append((chord_pos + skew_y, camber_z + thickness_z))
                lower.append((chord_pos + skew_y, camber_z - thickness_z * 0.90))

            raw = upper + list(reversed(lower[1:-1]))
            rotated = rotate_section_points(raw, pitch_deg * pi / 180.0)
            return [(sweep_y + y, z) for (y, z) in rotated]

        hub_body_height = thickness * 0.36
        rear_collar_height = (
            float(hub.rear_collar_height)
            if hub.rear_collar_height is not None
            else thickness * 0.18
        )
        rear_collar_radius = (
            float(hub.rear_collar_radius)
            if hub.rear_collar_radius is not None
            else hub_radius * 0.78
        )
        if rear_collar_height < 0.0:
            raise ValueError("hub.rear_collar_height must be non-negative")
        if rear_collar_height > 1.0e-9 and rear_collar_radius <= 0.0:
            raise ValueError("hub.rear_collar_radius must be positive when rear_collar_height > 0")
        if rear_collar_radius >= hub_radius * 1.05:
            raise ValueError("hub.rear_collar_radius must fit within the hub radius")

        hub_body = cq.Workplane("XY").circle(hub_radius).extrude(hub_body_height * 0.5, both=True)
        shape = hub_body
        if rear_collar_height > 1.0e-9:
            rear_collar = (
                cq.Workplane("XY")
                .circle(rear_collar_radius)
                .extrude(rear_collar_height * 0.5, both=True)
                .translate((0.0, 0.0, -thickness * 0.24))
            )
            shape = shape.union(rear_collar)

        if hub_style == "capped":
            front_cap = (
                cq.Workplane("XY")
                .circle(hub_radius * 0.82)
                .extrude(max(thickness * 0.18, 1.0e-4))
                .translate((0.0, 0.0, hub_body_height * 0.5))
            )
            shape = shape.union(front_cap)
        elif hub_style in {"domed", "spinner"}:
            front_cap_height = thickness * (0.34 if hub_style == "domed" else 0.52)
            front_top_radius = hub_radius * (0.40 if hub_style == "domed" else 0.05)
            front_cap = (
                cq.Workplane("XY")
                .workplane(offset=hub_body_height * 0.5)
                .circle(hub_radius * 0.92)
                .workplane(offset=front_cap_height)
                .circle(max(front_top_radius, 1.0e-4))
                .loft(combine=True, ruled=False)
            )
            shape = shape.union(front_cap)

        if hub.bore_diameter is not None:
            bore_diameter = float(hub.bore_diameter)
            if bore_diameter <= 0.0:
                raise ValueError("hub.bore_diameter must be positive")
            bore_radius = bore_diameter * 0.5
            bore_limit = min(
                hub_radius, rear_collar_radius if rear_collar_height > 0.0 else hub_radius
            )
            if bore_radius >= bore_limit * 0.92:
                raise ValueError("hub.bore_diameter is too large for the hub")
            bore = (
                cq.Workplane("XY")
                .circle(bore_radius)
                .extrude(
                    max(thickness * 1.8, hub_body_height + rear_collar_height + shroud_depth),
                    both=True,
                )
            )
            shape = shape.cut(bore)

        root_radius = hub_radius * 0.82
        if shroud is not None:
            assert ring_inner_radius is not None
            tip_bridge = min(shroud_thickness * 0.18, max(thickness * 0.05, 5.0e-4))
            tip_radius = ring_inner_radius + tip_bridge
        else:
            tip_radius = outer_radius - tip_clearance
        if tip_radius <= root_radius + max(thickness * 0.22, 1.0e-4):
            raise ValueError("blade.tip_clearance leaves no usable blade span")

        blade_span = tip_radius - root_radius
        station_fracs = (0.00, 0.18, 0.42, 0.70, 1.00)
        stations = [root_radius + blade_span * frac for frac in station_fracs]
        section_chords = [
            lerp(root_chord, tip_chord, frac) * chord_scale(frac) for frac in station_fracs
        ]
        root_pitch_deg = blade_pitch_deg * 1.16
        section_pitches = [
            lerp(root_pitch_deg, tip_pitch_deg, frac**0.82) for frac in station_fracs
        ]
        root_section_t = max(thickness * 0.18, root_chord * 0.080)
        tip_section_t = max(thickness * 0.08, tip_chord * 0.048)
        thickness_shape_scale = {
            "straight": 1.00,
            "scimitar": 0.94,
            "broad": 1.08,
            "narrow": 0.88,
        }[blade_shape]
        section_thicknesses = [
            lerp(root_section_t, tip_section_t, frac**0.78) * thickness_shape_scale
            for frac in station_fracs
        ]
        sweep_amount = blade_span * sin(blade_sweep_deg * pi / 180.0) * 0.34
        section_sweeps = [sweep_amount * sweep_factor(frac) for frac in station_fracs]

        blade_wp = None
        previous_station = 0.0
        for station, chord, section_t, pitch_deg, sweep_y, span_t in zip(
            stations,
            section_chords,
            section_thicknesses,
            section_pitches,
            section_sweeps,
            station_fracs,
        ):
            section = blade_section_points(chord, section_t, pitch_deg, sweep_y, span_t)
            if blade_wp is None:
                blade_wp = cq.Workplane("YZ").workplane(offset=station).polyline(section).close()
            else:
                blade_wp = (
                    blade_wp.workplane(offset=station - previous_station).polyline(section).close()
                )
            previous_station = station
        assert blade_wp is not None
        blade_solid = blade_wp.loft(combine=True, ruled=False)

        angle_step = 360.0 / float(blade_count)
        for blade_index in range(blade_count):
            shape = shape.union(
                blade_solid.rotate(
                    (0.0, 0.0, 0.0),
                    (0.0, 0.0, 1.0),
                    angle_step * float(blade_index),
                )
            )

        if shroud is not None:
            assert ring_outer_radius is not None
            assert ring_inner_radius is not None
            tip_ring = (
                cq.Workplane("XY")
                .circle(ring_outer_radius)
                .circle(ring_inner_radius)
                .extrude(shroud_depth * 0.5, both=True)
            )
            shape = shape.union(tip_ring)
            if shroud_lip_depth > 1.0e-9:
                front_lip = (
                    cq.Workplane("XY")
                    .workplane(offset=shroud_depth * 0.5)
                    .circle(ring_outer_radius)
                    .circle(ring_inner_radius)
                    .extrude(shroud_lip_depth)
                )
                shape = shape.union(front_lip)

        solid = _to_shape(shape)
        if not center:
            solid = _fans_shift_to_z0(solid)
        self._set(solid)

# ===== section_loft (17 syms) =====
def _cq_shapes():
    """The low-level cadquery shape helpers the real sdk lofts through."""
    from cadquery.occ_impl import shapes as cq_shapes
    return cq_shapes

def _as_vec3(values, *, name):
    if len(values) != 3:
        raise ValidationError("%s must have 3 elements" % name)
    return (float(values[0]), float(values[1]), float(values[2]))

def _normalize_section_points(points, *, name):
    raw = [_as_vec3(point, name=name) for point in points]
    if len(raw) < 3:
        raise ValidationError("%s must contain at least 3 points" % name)

    out = []
    for point in raw:
        if not out or point != out[-1]:
            out.append(point)

    if len(out) >= 2 and out[0] == out[-1]:
        out.pop()

    if len(out) < 3:
        raise ValidationError("%s must contain at least 3 distinct points" % name)
    return out

@dataclass(frozen=True)
class LoftTessellation:
    tolerance: float = 0.001
    angular_tolerance: float = 0.1

    def __post_init__(self):
        if float(self.tolerance) <= 0.0:
            raise ValidationError("tessellation.tolerance must be > 0")
        if float(self.angular_tolerance) <= 0.0:
            raise ValidationError("tessellation.angular_tolerance must be > 0")
        object.__setattr__(self, "tolerance", float(self.tolerance))
        object.__setattr__(self, "angular_tolerance", float(self.angular_tolerance))

@dataclass(frozen=True)
class LoftSection:
    points: tuple

    def __post_init__(self):
        coerced = tuple(_normalize_section_points(self.points, name="section.points"))
        object.__setattr__(self, "points", coerced)

@dataclass(frozen=True)
class SectionLoftSpec:
    sections: tuple
    path: tuple = None
    guide_curves: dict = None
    cap: bool = True
    solid: bool = True
    symmetry: str = None
    ruled: bool = False
    continuity: str = "C2"
    parametrization: str = "uniform"
    degree: int = 3
    compat: bool = True
    smoothing: bool = False
    weights: tuple = (1.0, 1.0, 1.0)
    repair: str = "auto"
    tessellation: LoftTessellation = field(default_factory=LoftTessellation)

    def __post_init__(self):
        sections = tuple(_coerce_loft_section(section) for section in self.sections)
        if len(sections) < 2:
            raise ValidationError("SectionLoftSpec.sections must contain at least two sections")
        object.__setattr__(self, "sections", sections)

        if self.path is not None:
            object.__setattr__(
                self, "path",
                tuple(_as_vec3(point, name="path[]") for point in self.path),
            )
        if self.guide_curves is not None:
            guide_curves = {
                str(name): tuple(_as_vec3(point, name="guide_curves[%r][]" % name) for point in pts)
                for name, pts in self.guide_curves.items()
            }
            object.__setattr__(self, "guide_curves", guide_curves)

        if self.symmetry is not None and self.symmetry != "mirror_yz":
            raise ValidationError("symmetry must be 'mirror_yz' or None")
        if self.degree < 1:
            raise ValidationError("degree must be >= 1")
        if len(self.weights) != 3:
            raise ValidationError("weights must contain exactly 3 values")
        object.__setattr__(self, "degree", int(self.degree))
        object.__setattr__(
            self, "weights",
            (float(self.weights[0]), float(self.weights[1]), float(self.weights[2])),
        )

def _coerce_loft_section(value):
    if isinstance(value, LoftSection):
        return value
    return LoftSection(points=tuple(value))

def _coerce_loft_spec(spec):
    if isinstance(spec, SectionLoftSpec):
        return spec
    return SectionLoftSpec(sections=tuple(_coerce_loft_section(section) for section in spec))

def _build_section_wires(spec):
    cq_shapes = _cq_shapes()
    wires = []
    for idx, section in enumerate(spec.sections):
        points = tuple(section.points)
        try:
            wire = cq_shapes.polygon(*points)
        except Exception as exc:
            raise ValidationError("Failed to build wire for section[%d]" % idx)
        wires.append(wire)
    return wires

def _curve_from_points(points, *, name):
    cq_shapes = _cq_shapes()
    if len(points) < 2:
        raise ValidationError("%s must contain at least 2 points" % name)
    if len(points) == 2:
        return cq_shapes.segment(points[0], points[1])
    try:
        return cq_shapes.spline(*points)
    except Exception:
        try:
            return cq_shapes.polyline(*points)
        except Exception as exc:
            raise ValidationError("Failed to build %s" % name)

def _resolve_path_points(spec):
    if spec.path is not None:
        return spec.path
    if spec.guide_curves is None:
        return None
    return spec.guide_curves.get("spine")

def _resolve_aux_spine_points(spec):
    if spec.guide_curves is None:
        return None
    aux = spec.guide_curves.get("aux_spine")
    if aux is not None:
        return aux
    return spec.guide_curves.get("binormal")

def _validate_guide_curve_names(spec):
    if spec.guide_curves is None:
        return
    supported = {"spine", "aux_spine", "binormal"}
    unsupported = sorted(set(spec.guide_curves) - supported)
    if unsupported:
        raise ValidationError(
            "Unsupported guide_curves keys: "
            + ", ".join(repr(name) for name in unsupported)
            + ". Supported keys are 'spine', 'aux_spine', and 'binormal'."
        )

def _apply_symmetry_shape(shape, *, symmetry):
    if symmetry is None:
        return shape
    if symmetry != "mirror_yz":
        raise ValidationError("Unsupported symmetry mode: %r" % symmetry)
    try:
        mirrored = shape.mirror("YZ")
        if hasattr(shape, "fuse"):
            fused = shape.fuse(mirrored, glue=True)
        else:
            fused = shape
        if hasattr(fused, "fix"):
            fused = fused.fix()
        if hasattr(fused, "clean"):
            fused = fused.clean()
        return fused
    except Exception as exc:
        raise ValidationError("Failed to apply mirror_yz symmetry")

def _heal_shape(shape, *, solid):
    cq_shapes = _cq_shapes()
    if hasattr(shape, "fix"):
        shape = shape.fix()
    if solid:
        try:
            shape = cq_shapes.solid(shape)
        except Exception:
            pass
        if hasattr(shape, "fix"):
            shape = shape.fix()
    return shape

def section_loft(spec, /, **overrides):
    if overrides:
        spec = SectionLoftSpec(**({**_coerce_loft_spec(spec).__dict__, **overrides}))
    else:
        spec = _coerce_loft_spec(spec)

    cq_shapes = _cq_shapes()
    _validate_guide_curve_names(spec)
    wires = _build_section_wires(spec)
    path_points = _resolve_path_points(spec)
    aux_spine_points = _resolve_aux_spine_points(spec)

    if path_points is None:
        shape = cq_shapes.loft(
            wires,
            cap=bool(spec.cap and spec.solid),
            ruled=bool(spec.ruled),
            continuity=spec.continuity,
            parametrization=spec.parametrization,
            degree=int(spec.degree),
            compat=bool(spec.compat),
            smoothing=bool(spec.smoothing),
            weights=spec.weights,
        )
    else:
        path_curve = _curve_from_points(path_points, name="path")
        mode = None
        if aux_spine_points is not None:
            mode = _curve_from_points(aux_spine_points, name="guide_curves['aux_spine']")
        shape = cq_shapes.Solid.sweep_multi(
            wires,
            path_curve,
            makeSolid=bool(spec.solid and spec.cap),
            isFrenet=False,
            mode=mode,
        )

    shape = _apply_symmetry_shape(shape, symmetry=spec.symmetry)

    if spec.repair in {"auto", "kernel"}:
        shape = _heal_shape(shape, solid=bool(spec.solid and spec.cap))

    return MeshGeometry()._set(shape)

def repair_loft(geometry_or_spec, /, *, repair="auto"):
    # B-rep results are already exact/manifold, so mesh-side repair is a no-op
    # copy; spec/raw inputs are rebuilt through section_loft (honoring `repair`).
    if isinstance(geometry_or_spec, MeshGeometry):
        return geometry_or_spec.copy()
    spec = _coerce_loft_spec(geometry_or_spec)
    if repair != "auto":
        spec = SectionLoftSpec(**{**spec.__dict__, "repair": repair})
    return section_loft(spec)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
import cadquery as cq
TAIL_HINGE_X = -12.96
CABIN_ORIGIN = (1.10, 0.0, -4.315)
CABIN_HALF_WIDTH = 1.30
PYLON_PIVOT_OFFSET = 1.32
def _superellipse_section(
    x_pos: float,
    half_width: float,
    half_height: float,
    *,
    exponent: float = 2.4,
    samples: int = 40,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    power = 2.0 / exponent
    for idx in range(samples):
        angle = math.tau * idx / samples
        c = math.cos(angle)
        s = math.sin(angle)
        y = math.copysign(abs(c) ** power, c) * half_width
        z = math.copysign(abs(s) ** power, s) * half_height
        points.append((x_pos, y, z))
    return points
def _mesh_from_sections(
    sections: list[list[tuple[float, float, float]]],
    name: str,
):
    return mesh_from_geometry(repair_loft(section_loft(sections), repair="mesh"), name)
def _midpoint(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
def _distance(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> float:
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2)
def _rpy_for_cylinder(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    length_xy = math.hypot(dx, dy)
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(length_xy, dz)
    return (0.0, pitch, yaw)
def _add_member(
    part,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    *,
    radius: float,
    material,
    name: str,
) -> None:
    part.visual(
        Cylinder(radius=radius, length=_distance(a, b)),
        origin=Origin(xyz=_midpoint(a, b), rpy=_rpy_for_cylinder(a, b)),
        material=material,
        name=name,
    )
def _vertical_surface(points: list[tuple[float, float]], thickness: float):
    return cq.Workplane("XZ").polyline(points).close().extrude(thickness, both=True)
def _horizontal_surface(points: list[tuple[float, float]], thickness: float):
    return cq.Workplane("XY").polyline(points).close().extrude(thickness, both=True)
def _build_hull_mesh():
    sections = [
        _superellipse_section(-12.86, 0.05, 0.05, exponent=2.0),
        _superellipse_section(-12.20, 0.24, 0.26, exponent=2.0),
        _superellipse_section(-10.90, 0.78, 0.82, exponent=2.1),
        _superellipse_section(-8.00, 1.55, 1.62, exponent=2.2),
        _superellipse_section(-3.20, 2.30, 2.38, exponent=2.25),
        _superellipse_section(1.50, 2.58, 2.66, exponent=2.25),
        _superellipse_section(6.00, 2.45, 2.54, exponent=2.25),
        _superellipse_section(10.00, 2.02, 2.10, exponent=2.2),
        _superellipse_section(12.20, 1.28, 1.34, exponent=2.15),
        _superellipse_section(13.50, 0.54, 0.58, exponent=2.05),
        _superellipse_section(14.25, 0.10, 0.11, exponent=2.0),
    ]
    return _mesh_from_sections(sections, "hull_envelope")
def _build_cabin_mesh():
    sections = [
        _superellipse_section(-4.10, 0.10, 0.14, exponent=2.5),
        _superellipse_section(-3.50, 0.55, 0.60, exponent=2.8),
        _superellipse_section(-2.40, 1.05, 0.85, exponent=3.2),
        _superellipse_section(-0.60, 1.28, 0.99, exponent=3.3),
        _superellipse_section(2.20, 1.30, 1.02, exponent=3.3),
        _superellipse_section(3.30, 1.15, 0.90, exponent=3.0),
        _superellipse_section(4.10, 0.36, 0.40, exponent=2.6),
    ]
    return _mesh_from_sections(sections, "cabin_shell")
def _build_pod_mesh():
    sections = [
        _superellipse_section(-0.72, 0.04, 0.04, exponent=2.0),
        _superellipse_section(-0.48, 0.16, 0.16, exponent=2.0),
        _superellipse_section(-0.12, 0.23, 0.24, exponent=2.15),
        _superellipse_section(0.40, 0.23, 0.24, exponent=2.15),
        _superellipse_section(0.82, 0.16, 0.18, exponent=2.1),
        _superellipse_section(1.06, 0.05, 0.05, exponent=2.0),
    ]
    return _mesh_from_sections(sections, "engine_pod_shell")
def _build_rudder_mesh():
    return mesh_from_cadquery(
        _vertical_surface(
            [
                (0.0, 0.60),
                (-0.10, 0.82),
                (-0.78, 1.26),
                (-1.22, 1.46),
                (-1.22, -1.46),
                (-0.78, -1.26),
                (-0.10, -0.82),
                (0.0, -0.60),
            ],
            0.12,
        ),
        "rudder_surface",
    )
def _build_elevator_mesh(side_sign: float):
    span = 1.34 * side_sign
    profile = [
        (0.0, 0.0),
        (-0.10, 0.16 * side_sign),
        (-0.94, 0.98 * side_sign),
        (-0.74, span),
        (0.0, 1.26 * side_sign),
    ]
    return mesh_from_cadquery(
        _horizontal_surface(profile, 0.10),
        "elevator_surface_pos" if side_sign > 0.0 else "elevator_surface_neg",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sightseeing_blimp")

    envelope_paint = model.material("envelope_paint", rgba=(0.92, 0.93, 0.95, 1.0))
    cabin_paint = model.material("cabin_paint", rgba=(0.83, 0.85, 0.88, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.34, 0.36, 0.39, 1.0))
    pod_gray = model.material("pod_gray", rgba=(0.56, 0.59, 0.63, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.18, 0.19, 0.20, 1.0))
    prop_black = model.material("prop_black", rgba=(0.08, 0.08, 0.09, 1.0))
    glass_tint = model.material("glass_tint", rgba=(0.46, 0.60, 0.68, 0.48))

    hull = model.part("hull")
    hull.visual(_build_hull_mesh(), material=envelope_paint, name="envelope")
    hull.visual(
        mesh_from_cadquery(
            _vertical_surface(
                [
                    (-10.10, 0.24),
                    (-9.55, 0.92),
                    (-10.08, 1.76),
                    (TAIL_HINGE_X, 1.08),
                    (TAIL_HINGE_X, 0.56),
                ],
                0.22,
            ),
            "upper_fin_root",
        ),
        material=envelope_paint,
        name="upper_fin_root",
    )
    hull.visual(
        mesh_from_cadquery(
            _vertical_surface(
                [
                    (-10.10, -0.24),
                    (TAIL_HINGE_X, -0.56),
                    (TAIL_HINGE_X, -1.08),
                    (-10.08, -1.76),
                    (-9.55, -0.92),
                ],
                0.22,
            ),
            "lower_fin_root",
        ),
        material=envelope_paint,
        name="lower_fin_root",
    )
    hull.visual(
        mesh_from_cadquery(
            _horizontal_surface(
                [
                    (-9.95, 0.18),
                    (-9.35, 0.96),
                    (-10.12, 1.66),
                    (TAIL_HINGE_X, 1.72),
                    (TAIL_HINGE_X, 0.55),
                ],
                0.16,
            ),
            "left_tailplane_root",
        ),
        material=envelope_paint,
        name="left_tailplane_root",
    )
    hull.visual(
        mesh_from_cadquery(
            _horizontal_surface(
                [
                    (-9.95, -0.18),
                    (TAIL_HINGE_X, -0.55),
                    (TAIL_HINGE_X, -1.72),
                    (-10.12, -1.66),
                    (-9.35, -0.96),
                ],
                0.16,
            ),
            "right_tailplane_root",
        ),
        material=envelope_paint,
        name="right_tailplane_root",
    )
    for idx, (top, bottom) in enumerate(
        [
            ((-1.65, -0.55, -2.40), (-1.20, -0.82, -3.28)),
            ((-1.65, 0.55, -2.40), (-1.20, 0.82, -3.28)),
            ((2.10, -0.48, -2.46), (1.75, -0.76, -3.24)),
            ((2.10, 0.48, -2.46), (1.75, 0.76, -3.24)),
        ]
    ):
        _add_member(
            hull,
            top,
            bottom,
            radius=0.09,
            material=trim_gray,
            name=f"cabin_strut_{idx}",
        )

    cabin = model.part("cabin")
    cabin.visual(_build_cabin_mesh(), material=cabin_paint, name="cabin_shell")
    cabin.visual(
        Box((6.05, 0.03, 0.58)),
        origin=Origin(xyz=(0.25, 1.255, 0.20)),
        material=glass_tint,
        name="window_band_0",
    )
    cabin.visual(
        Box((6.05, 0.03, 0.58)),
        origin=Origin(xyz=(0.25, -1.255, 0.20)),
        material=glass_tint,
        name="window_band_1",
    )
    cabin.visual(
        Box((0.42, 1.18, 0.58)),
        origin=Origin(xyz=(3.76, 0.0, 0.24)),
        material=glass_tint,
        name="windscreen",
    )
    cabin.visual(
        Box((6.60, 2.05, 0.14)),
        origin=Origin(xyz=(0.10, 0.0, -0.96)),
        material=trim_gray,
        name="cabin_floor",
    )
    for idx, (x_pos, y_pos, z_pos) in enumerate(
        [
            (-2.30, -0.82, 0.88),
            (-2.30, 0.82, 0.88),
            (0.65, -0.76, 0.94),
            (0.65, 0.76, 0.94),
        ]
    ):
        cabin.visual(
            Cylinder(radius=0.14, length=0.22),
            origin=Origin(xyz=(x_pos, y_pos, z_pos)),
            material=trim_gray,
            name=f"roof_pad_{idx}",
        )

    left_pylon = model.part("left_pylon")
    left_pylon.visual(
        Box((0.22, 0.93, 0.20)),
        origin=Origin(xyz=(0.0, 0.495, 0.00)),
        material=trim_gray,
        name="beam",
    )
    left_pylon.visual(
        Box((0.32, 0.08, 0.30)),
        origin=Origin(xyz=(0.0, 0.028, -0.06)),
        material=trim_gray,
        name="root_fairing",
    )
    left_pylon.visual(
        Box((0.34, 0.04, 0.68)),
        origin=Origin(xyz=(0.0, 0.95, 0.00)),
        material=trim_gray,
        name="inner_fork",
    )
    left_pylon.visual(
        Box((0.34, 0.04, 0.68)),
        origin=Origin(xyz=(0.0, 1.69, 0.00)),
        material=trim_gray,
        name="outer_fork",
    )
    left_pylon.visual(
        Box((0.38, 0.78, 0.08)),
        origin=Origin(xyz=(0.0, 1.32, 0.34)),
        material=trim_gray,
        name="fork_bridge",
    )
    left_pylon.visual(
        Cylinder(radius=0.03, length=0.78),
        origin=Origin(xyz=(0.0, 1.32, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="pivot_pin",
    )
    _add_member(
        left_pylon,
        (0.0, 0.18, -0.18),
        (0.0, 0.94, -0.10),
        radius=0.05,
        material=trim_gray,
        name="brace",
    )

    right_pylon = model.part("right_pylon")
    right_pylon.visual(
        Box((0.22, 0.93, 0.20)),
        origin=Origin(xyz=(0.0, -0.495, 0.00)),
        material=trim_gray,
        name="beam",
    )
    right_pylon.visual(
        Box((0.32, 0.08, 0.30)),
        origin=Origin(xyz=(0.0, -0.028, -0.06)),
        material=trim_gray,
        name="root_fairing",
    )
    right_pylon.visual(
        Box((0.34, 0.04, 0.68)),
        origin=Origin(xyz=(0.0, -0.95, 0.00)),
        material=trim_gray,
        name="inner_fork",
    )
    right_pylon.visual(
        Box((0.34, 0.04, 0.68)),
        origin=Origin(xyz=(0.0, -1.69, 0.00)),
        material=trim_gray,
        name="outer_fork",
    )
    right_pylon.visual(
        Box((0.38, 0.78, 0.08)),
        origin=Origin(xyz=(0.0, -1.32, 0.34)),
        material=trim_gray,
        name="fork_bridge",
    )
    right_pylon.visual(
        Cylinder(radius=0.03, length=0.78),
        origin=Origin(xyz=(0.0, -1.32, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="pivot_pin",
    )
    _add_member(
        right_pylon,
        (0.0, -0.18, -0.18),
        (0.0, -0.94, -0.10),
        radius=0.05,
        material=trim_gray,
        name="brace",
    )

    left_pod = model.part("left_pod")
    left_pod.visual(_build_pod_mesh(), material=pod_gray, name="pod_shell")
    left_pod.visual(
        Cylinder(radius=0.055, length=0.70),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="pivot_sleeve",
    )
    left_pod.visual(
        Cylinder(radius=0.09, length=0.36),
        origin=Origin(xyz=(0.72, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="shaft_collar",
    )
    left_pod.visual(
        Cylinder(radius=0.09, length=0.36),
        origin=Origin(xyz=(-0.36, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="tail_exhaust",
    )

    right_pod = model.part("right_pod")
    right_pod.visual(_build_pod_mesh(), material=pod_gray, name="pod_shell")
    right_pod.visual(
        Cylinder(radius=0.055, length=0.70),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="pivot_sleeve",
    )
    right_pod.visual(
        Cylinder(radius=0.09, length=0.36),
        origin=Origin(xyz=(0.72, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="shaft_collar",
    )
    right_pod.visual(
        Cylinder(radius=0.09, length=0.36),
        origin=Origin(xyz=(-0.36, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="tail_exhaust",
    )

    rotor_mesh = mesh_from_geometry(
        FanRotorGeometry(
            0.72,
            0.14,
            3,
            thickness=0.16,
            blade_pitch_deg=30.0,
            blade_sweep_deg=18.0,
            blade=FanRotorBlade(shape="broad", camber=0.10),
            hub=FanRotorHub(style="spinner", bore_diameter=0.04),
        ),
        "propeller_rotor",
    )

    left_propeller = model.part("left_propeller")
    left_propeller.visual(
        rotor_mesh,
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=prop_black,
        name="rotor",
    )
    left_propeller.visual(
        Cylinder(radius=0.09, length=0.26),
        origin=Origin(xyz=(-0.05, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="hub_barrel",
    )

    right_propeller = model.part("right_propeller")
    right_propeller.visual(
        rotor_mesh,
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=prop_black,
        name="rotor",
    )
    right_propeller.visual(
        Cylinder(radius=0.09, length=0.26),
        origin=Origin(xyz=(-0.05, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_metal,
        name="hub_barrel",
    )

    rudder = model.part("rudder")
    rudder.visual(_build_rudder_mesh(), material=envelope_paint, name="rudder_surface")

    left_elevator = model.part("left_elevator")
    left_elevator.visual(
        _build_elevator_mesh(1.0),
        material=envelope_paint,
        name="elevator_surface",
    )

    right_elevator = model.part("right_elevator")
    right_elevator.visual(
        _build_elevator_mesh(-1.0),
        material=envelope_paint,
        name="elevator_surface",
    )

    model.articulation(
        "hull_to_cabin",
        ArticulationType.FIXED,
        parent=hull,
        child=cabin,
        origin=Origin(xyz=CABIN_ORIGIN),
    )
    model.articulation(
        "cabin_to_left_pylon",
        ArticulationType.FIXED,
        parent=cabin,
        child=left_pylon,
        origin=Origin(xyz=(0.85, CABIN_HALF_WIDTH + 0.012, 0.00)),
    )
    model.articulation(
        "cabin_to_right_pylon",
        ArticulationType.FIXED,
        parent=cabin,
        child=right_pylon,
        origin=Origin(xyz=(0.85, -(CABIN_HALF_WIDTH + 0.012), 0.00)),
    )
    model.articulation(
        "left_pylon_to_left_pod",
        ArticulationType.REVOLUTE,
        parent=left_pylon,
        child=left_pod,
        origin=Origin(xyz=(0.0, PYLON_PIVOT_OFFSET, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=1.2,
            lower=math.radians(-35.0),
            upper=math.radians(55.0),
        ),
    )
    model.articulation(
        "right_pylon_to_right_pod",
        ArticulationType.REVOLUTE,
        parent=right_pylon,
        child=right_pod,
        origin=Origin(xyz=(0.0, -PYLON_PIVOT_OFFSET, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=1.2,
            lower=math.radians(-35.0),
            upper=math.radians(55.0),
        ),
    )
    model.articulation(
        "left_pod_to_left_propeller",
        ArticulationType.CONTINUOUS,
        parent=left_pod,
        child=left_propeller,
        origin=Origin(xyz=(1.16, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=40.0),
    )
    model.articulation(
        "right_pod_to_right_propeller",
        ArticulationType.CONTINUOUS,
        parent=right_pod,
        child=right_propeller,
        origin=Origin(xyz=(1.16, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=40.0),
    )
    model.articulation(
        "hull_to_rudder",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=rudder,
        origin=Origin(xyz=(TAIL_HINGE_X, 0.0, 0.0)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.6,
            lower=math.radians(-28.0),
            upper=math.radians(28.0),
        ),
    )
    model.articulation(
        "hull_to_left_elevator",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=left_elevator,
        origin=Origin(xyz=(TAIL_HINGE_X, 0.55, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=14.0,
            velocity=1.3,
            lower=math.radians(-18.0),
            upper=math.radians(24.0),
        ),
    )
    model.articulation(
        "hull_to_right_elevator",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=right_elevator,
        origin=Origin(xyz=(TAIL_HINGE_X, -0.55, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=14.0,
            velocity=1.3,
            lower=math.radians(-18.0),
            upper=math.radians(24.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
