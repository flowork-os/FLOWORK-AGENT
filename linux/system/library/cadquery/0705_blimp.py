# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Literal, Optional
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

# ===== primitives (1 syms) =====
class TorusGeometry(MeshGeometry):
    def __init__(self, radius, tube, *, radial_segments=16, tubular_segments=32):
        super().__init__()
        radius = float(radius)
        tube = float(tube)
        # ring radius `radius` in XY plane, tube radius `tube`, centered at origin
        solid = cq.Solid.makeTorus(radius, tube, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
        self._set(solid)

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import math
def _body_of_revolution_along_x(stations, *, segments: int = 56, z_scale: float = 0.93) -> MeshGeometry:
    """Closed streamlined body with circular-ish stations along the airship X axis."""
    geom = MeshGeometry()
    rings: list[list[int]] = []
    for x, radius in stations:
        ring: list[int] = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ring.append(geom.add_vertex(x, radius * math.cos(a), z_scale * radius * math.sin(a)))
        rings.append(ring)

    for ring_a, ring_b in zip(rings, rings[1:]):
        for i in range(segments):
            a0 = ring_a[i]
            a1 = ring_a[(i + 1) % segments]
            b0 = ring_b[i]
            b1 = ring_b[(i + 1) % segments]
            geom.add_face(a0, b0, b1)
            geom.add_face(a0, b1, a1)

    # Cap the small end rings so exact geometry remains a closed solid.
    for ring, reverse in ((rings[0], True), (rings[-1], False)):
        center_x = stations[0][0] if reverse else stations[-1][0]
        c = geom.add_vertex(center_x, 0.0, 0.0)
        for i in range(segments):
            a = ring[i]
            b = ring[(i + 1) % segments]
            if reverse:
                geom.add_face(c, b, a)
            else:
                geom.add_face(c, a, b)
    return geom
def _superellipse_loop_x(
    x: float,
    *,
    center_z: float,
    width: float,
    height: float,
    samples: int = 36,
    exponent: float = 3.2,
) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    half_w = width * 0.5
    half_h = height * 0.5
    p = 2.0 / exponent
    for i in range(samples):
        t = 2.0 * math.pi * i / samples
        ct = math.cos(t)
        st = math.sin(t)
        y = half_w * (1.0 if ct >= 0.0 else -1.0) * (abs(ct) ** p)
        z = center_z + half_h * (1.0 if st >= 0.0 else -1.0) * (abs(st) ** p)
        points.append((x, y, z))
    return points
def _loft_between_loops(loops: list[list[tuple[float, float, float]]]) -> MeshGeometry:
    geom = MeshGeometry()
    indices: list[list[int]] = []
    count = len(loops[0])
    for loop in loops:
        indices.append([geom.add_vertex(*p) for p in loop])

    for loop_a, loop_b in zip(indices, indices[1:]):
        for i in range(count):
            a0 = loop_a[i]
            a1 = loop_a[(i + 1) % count]
            b0 = loop_b[i]
            b1 = loop_b[(i + 1) % count]
            geom.add_face(a0, b0, b1)
            geom.add_face(a0, b1, a1)

    # End caps.
    for loop, reverse in ((indices[0], True), (indices[-1], False)):
        center = [0.0, 0.0, 0.0]
        for idx in loop:
            vx, vy, vz = geom.vertices[idx]
            center[0] += vx
            center[1] += vy
            center[2] += vz
        n = float(len(loop))
        c = geom.add_vertex(center[0] / n, center[1] / n, center[2] / n)
        for i in range(count):
            a = loop[i]
            b = loop[(i + 1) % count]
            if reverse:
                geom.add_face(c, b, a)
            else:
                geom.add_face(c, a, b)
    return geom
def _passenger_cabin_mesh() -> MeshGeometry:
    center_x = 1.5
    center_z = -8.65
    length = 18.0
    width = 3.35
    height = 2.20
    # Tiny end sections avoid a flat boxy cap while keeping the mesh closed.
    section_scales = (
        (-0.500, 0.08),
        (-0.455, 0.42),
        (-0.365, 0.78),
        (-0.250, 0.98),
        (0.250, 1.00),
        (0.365, 0.82),
        (0.455, 0.45),
        (0.500, 0.10),
    )
    loops = [
        _superellipse_loop_x(
            center_x + length * rel,
            center_z=center_z,
            width=width * scale,
            height=height * (0.72 + 0.28 * scale),
        )
        for rel, scale in section_scales
    ]
    return _loft_between_loops(loops)
def _vertical_prism(points_xz, *, thickness_y: float) -> MeshGeometry:
    geom = MeshGeometry()
    half = thickness_y * 0.5
    front = [geom.add_vertex(x, -half, z) for x, z in points_xz]
    back = [geom.add_vertex(x, half, z) for x, z in points_xz]
    n = len(points_xz)
    for i in range(1, n - 1):
        geom.add_face(front[0], front[i], front[i + 1])
        geom.add_face(back[0], back[i + 1], back[i])
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(front[i], back[i], back[j])
        geom.add_face(front[i], back[j], front[j])
    return geom
def _horizontal_prism(points_xy, *, thickness_z: float) -> MeshGeometry:
    geom = MeshGeometry()
    half = thickness_z * 0.5
    lower = [geom.add_vertex(x, y, -half) for x, y in points_xy]
    upper = [geom.add_vertex(x, y, half) for x, y in points_xy]
    n = len(points_xy)
    for i in range(1, n - 1):
        geom.add_face(lower[0], lower[i + 1], lower[i])
        geom.add_face(upper[0], upper[i], upper[i + 1])
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(lower[i], lower[j], upper[j])
        geom.add_face(lower[i], upper[j], upper[i])
    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="sightseeing_blimp")

    hull_fabric = model.material("warm_white_fabric", rgba=(0.88, 0.91, 0.88, 1.0))
    tail_blue = model.material("deep_tail_blue", rgba=(0.06, 0.18, 0.34, 1.0))
    cabin_white = model.material("cabin_white", rgba=(0.92, 0.93, 0.89, 1.0))
    glass = model.material("smoked_blue_glass", rgba=(0.05, 0.16, 0.23, 0.78))
    dark = model.material("matte_graphite", rgba=(0.015, 0.017, 0.018, 1.0))
    metal = model.material("brushed_aluminum", rgba=(0.58, 0.60, 0.58, 1.0))
    red = model.material("safety_red", rgba=(0.78, 0.07, 0.04, 1.0))

    hull = model.part("hull")

    envelope = _body_of_revolution_along_x(
        (
            (-27.5, 0.06),
            (-26.2, 0.75),
            (-24.0, 2.10),
            (-20.0, 4.35),
            (-14.0, 6.05),
            (-6.0, 7.10),
            (3.5, 7.55),
            (12.0, 7.10),
            (20.5, 5.05),
            (25.6, 2.05),
            (27.5, 0.08),
        )
    )
    hull.visual(mesh_from_geometry(envelope, "streamlined_envelope"), material=hull_fabric, name="envelope")

    # A long belly keel, passenger gondola, and four structural hangers make the
    # cabin visibly carried by the envelope rather than floating below it.
    hull.visual(
        Box((17.5, 0.82, 0.38)),
        origin=Origin(xyz=(1.5, 0.0, -7.15)),
        material=metal,
        name="belly_keel",
    )
    hull.visual(mesh_from_geometry(_passenger_cabin_mesh(), "passenger_cabin"), material=cabin_white, name="cabin")
    for i, x in enumerate((-5.8, -1.6, 2.6, 6.8)):
        hull.visual(
            Box((0.46, 0.28, 0.72)),
            origin=Origin(xyz=(x, 0.0, -7.62)),
            material=metal,
            name=f"cabin_hanger_{i}",
        )
    hull.visual(
        Box((13.4, 0.075, 0.44)),
        origin=Origin(xyz=(1.55, 1.70, -8.34)),
        material=glass,
        name="port_window_band",
    )
    hull.visual(
        Box((13.4, 0.075, 0.44)),
        origin=Origin(xyz=(1.55, -1.70, -8.34)),
        material=glass,
        name="starboard_window_band",
    )
    hull.visual(
        Box((12.0, 0.18, 0.11)),
        origin=Origin(xyz=(1.8, 0.0, -9.78)),
        material=metal,
        name="landing_skid",
    )

    # Side engine pylons are part of the fixed hull/gondola structure.  Their
    # outer tip faces are tangent to the rotating pod pivot lugs at q=0.
    hull.visual(
        Box((0.72, 2.90, 0.34)),
        origin=Origin(xyz=(1.0, 3.15, -8.62)),
        material=metal,
        name="port_pylon",
    )
    hull.visual(
        Box((0.86, 0.18, 0.86)),
        origin=Origin(xyz=(1.0, 4.51, -8.62)),
        material=metal,
        name="port_pylon_tip",
    )
    hull.visual(
        Box((1.10, 0.18, 0.64)),
        origin=Origin(xyz=(1.0, 1.73, -8.62)),
        material=metal,
        name="port_pylon_root",
    )
    hull.visual(
        Box((0.72, 2.90, 0.34)),
        origin=Origin(xyz=(1.0, -3.15, -8.62)),
        material=metal,
        name="starboard_pylon",
    )
    hull.visual(
        Box((0.86, 0.18, 0.86)),
        origin=Origin(xyz=(1.0, -4.51, -8.62)),
        material=metal,
        name="starboard_pylon_tip",
    )
    hull.visual(
        Box((1.10, 0.18, 0.64)),
        origin=Origin(xyz=(1.0, -1.73, -8.62)),
        material=metal,
        name="starboard_pylon_root",
    )

    # Cruciform tail: upper/lower vertical fins and port/starboard horizontal
    # tailplanes are fixed to the aft envelope.  Separate rudder/elevator parts
    # are mounted on the visible trailing hinge rods.
    top_fin = _vertical_prism(
        [(-22.2, 2.7), (-27.75, 0.55), (-23.8, 9.25), (-19.7, 3.25)],
        thickness_y=0.34,
    )
    bottom_fin = _vertical_prism(
        [(-22.2, -2.7), (-19.7, -3.25), (-23.8, -9.25), (-27.75, -0.55)],
        thickness_y=0.34,
    )
    hull.visual(mesh_from_geometry(top_fin, "top_fin"), material=tail_blue, name="top_fin")
    hull.visual(mesh_from_geometry(bottom_fin, "bottom_fin"), material=tail_blue, name="bottom_fin")

    port_tailplane = _horizontal_prism(
        [(-22.0, 3.55), (-25.40, 1.18), (-23.10, 8.85), (-19.7, 4.25)],
        thickness_z=0.30,
    )
    star_tailplane = _horizontal_prism(
        [(-22.0, -3.55), (-19.7, -4.25), (-23.10, -8.85), (-25.40, -1.18)],
        thickness_z=0.30,
    )
    hull.visual(mesh_from_geometry(port_tailplane, "port_tailplane"), material=tail_blue, name="port_tailplane")
    hull.visual(
        mesh_from_geometry(star_tailplane, "starboard_tailplane"),
        material=tail_blue,
        name="starboard_tailplane",
    )
    hull.visual(
        Cylinder(radius=0.060, length=7.20),
        origin=Origin(xyz=(-27.75, 0.0, 0.0)),
        material=metal,
        name="rudder_hinge",
    )
    hull.visual(
        Box((0.62, 0.26, 1.25)),
        origin=Origin(xyz=(-27.48, 0.0, 0.0)),
        material=metal,
        name="tail_post_fairing",
    )
    hull.visual(
        Box((1.30, 2.45, 0.32)),
        origin=Origin(xyz=(-24.72, 2.36, 0.0)),
        material=tail_blue,
        name="port_tailplane_root",
    )
    hull.visual(
        Box((1.30, 2.45, 0.32)),
        origin=Origin(xyz=(-24.72, -2.36, 0.0)),
        material=tail_blue,
        name="starboard_tailplane_root",
    )
    hull.visual(
        Cylinder(radius=0.055, length=5.50),
        origin=Origin(xyz=(-25.40, 3.98, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="port_elevator_hinge",
    )
    hull.visual(
        Cylinder(radius=0.055, length=5.50),
        origin=Origin(xyz=(-25.40, -3.98, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="starboard_elevator_hinge",
    )

    def add_engine(side_name: str, sign: float) -> None:
        pivot_y = sign * 4.60
        pod = model.part(f"{side_name}_pod")
        pod.visual(
            Cylinder(radius=0.44, length=1.78),
            origin=Origin(xyz=(0.02, sign * 0.64, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal,
            name="nacelle",
        )
        pod.visual(
            Box((0.70, 0.20, 0.78)),
            origin=Origin(xyz=(0.02, sign * 0.10, 0.0)),
            material=metal,
            name="pivot_lug",
        )
        pod.visual(
            mesh_from_geometry(TorusGeometry(0.44, 0.045, radial_segments=18, tubular_segments=40), f"{side_name}_cowl_ring"),
            origin=Origin(xyz=(0.952, sign * 0.64, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark,
            name="cowl_ring",
        )
        pod.visual(
            Cylinder(radius=0.28, length=0.30),
            origin=Origin(xyz=(-0.95, sign * 0.64, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark,
            name="aft_exhaust",
        )
        model.articulation(
            f"{side_name}_vector",
            ArticulationType.REVOLUTE,
            parent=hull,
            child=pod,
            origin=Origin(xyz=(1.0, pivot_y, -8.62)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=220.0, velocity=0.9, lower=-0.55, upper=0.55),
        )

        propeller = model.part(f"{side_name}_propeller")
        rotor = FanRotorGeometry(
            1.07,
            0.22,
            5,
            thickness=0.085,
            blade_pitch_deg=34.0,
            blade_sweep_deg=28.0,
            blade=FanRotorBlade(shape="scimitar", tip_pitch_deg=15.0, camber=0.12),
            hub=FanRotorHub(style="spinner", bore_diameter=0.10),
        )
        propeller.visual(mesh_from_geometry(rotor, f"{side_name}_propeller"), material=dark, name="rotor")
        propeller.visual(
            Cylinder(radius=0.070, length=0.46),
            origin=Origin(xyz=(0.0, 0.0, -0.23)),
            material=metal,
            name="shaft",
        )
        model.articulation(
            f"{side_name}_propeller_spin",
            ArticulationType.CONTINUOUS,
            parent=pod,
            child=propeller,
            origin=Origin(xyz=(1.22, sign * 0.64, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=90.0, velocity=120.0),
        )

    add_engine("port", 1.0)
    add_engine("starboard", -1.0)

    rudder = model.part("rudder")
    rudder_mesh = _vertical_prism(
        [(-0.060, -3.20), (-1.45, -2.35), (-1.55, 2.35), (-0.060, 3.20)],
        thickness_y=0.18,
    )
    rudder.visual(mesh_from_geometry(rudder_mesh, "rudder_panel"), material=tail_blue, name="panel")
    rudder.visual(
        Box((0.055, 0.20, 2.90)),
        origin=Origin(xyz=(-1.52, 0.0, 0.0)),
        material=red,
        name="red_trailing_edge",
    )
    model.articulation(
        "rudder_hinge",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=rudder,
        origin=Origin(xyz=(-27.75, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=260.0, velocity=0.75, lower=-0.44, upper=0.44),
    )

    def add_elevator(side_name: str, sign: float) -> None:
        elevator = model.part(f"{side_name}_elevator")
        points = [
            (-0.055, sign * 1.22),
            (-2.85, sign * 1.46),
            (-3.40, sign * 6.10),
            (-0.055, sign * 6.72),
        ]
        elevator.visual(
            mesh_from_geometry(_horizontal_prism(points, thickness_z=0.16), f"{side_name}_elevator_panel"),
            material=tail_blue,
            name="panel",
        )
        elevator.visual(
            Box((0.40, 0.78, 0.09)),
            origin=Origin(xyz=(-3.20, sign * 4.85, 0.0)),
            material=red,
            name="red_tip",
        )
        model.articulation(
            f"{side_name}_elevator_hinge",
            ArticulationType.REVOLUTE,
            parent=hull,
            child=elevator,
            origin=Origin(xyz=(-25.40, 0.0, 0.0)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=180.0, velocity=0.8, lower=-0.35, upper=0.35),
        )

    add_elevator("port", 1.0)
    add_elevator("starboard", -1.0)
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
