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
class CapsuleGeometry(MeshGeometry):
    def __init__(self, radius, length, *, radial_segments=24, height_segments=8):
        super().__init__()
        radius = float(radius)
        length = float(length)
        if radius <= 0.0:
            raise ValidationError("radius must be positive")
        if length < 0.0:
            raise ValidationError("length must be non-negative")

        sphere = cq.Solid.makeSphere(
            radius, angleDegrees1=-90, angleDegrees2=90, angleDegrees3=360
        )
        if length <= 1e-9:
            self._set(sphere)
            return

        half = length / 2.0
        # cylindrical body of height `length` centered, hemispherical caps at +-half
        body = cq.Solid.makeCylinder(
            radius, length, cq.Vector(0, 0, -half), cq.Vector(0, 0, 1)
        )
        top = sphere.translate(cq.Vector(0, 0, half))
        bottom = sphere.translate(cq.Vector(0, 0, -half))
        solid = body.fuse(top, bottom)
        try:
            solid = solid.clean()
        except Exception:
            pass
        self._set(solid)

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
def _cigar_envelope(length: float, radius_y: float, radius_z: float) -> MeshGeometry:
    """Tapered ellipsoidal airship envelope, long axis in X."""
    rings = 30
    segments = 72
    geom = MeshGeometry()

    tail_tip = geom.add_vertex(-length / 2.0, 0.0, 0.0)
    ring_ids: list[list[int]] = []
    for i in range(1, rings + 1):
        t = i / (rings + 1)
        x = (t - 0.5) * length
        # Fuller middle with softly pointed ends, slightly fuller nose.
        s = math.sin(math.pi * t) ** 0.52
        nose_fullness = 0.96 + 0.07 * t
        ry = radius_y * s * nose_fullness
        rz = radius_z * s * (0.98 + 0.04 * t)
        ring: list[int] = []
        for j in range(segments):
            a = 2.0 * math.pi * j / segments
            ring.append(geom.add_vertex(x, ry * math.cos(a), rz * math.sin(a)))
        ring_ids.append(ring)
    nose_tip = geom.add_vertex(length / 2.0, 0.0, 0.0)

    first = ring_ids[0]
    for j in range(segments):
        geom.add_face(tail_tip, first[(j + 1) % segments], first[j])

    for a, b in zip(ring_ids, ring_ids[1:]):
        for j in range(segments):
            j2 = (j + 1) % segments
            geom.add_face(a[j], a[j2], b[j2])
            geom.add_face(a[j], b[j2], b[j])

    last = ring_ids[-1]
    for j in range(segments):
        geom.add_face(last[j], last[(j + 1) % segments], nose_tip)
    return geom
def _prism_from_xz(points: list[tuple[float, float]], thickness_y: float) -> MeshGeometry:
    """Closed prism from an XZ polygon, extruded in Y."""
    geom = MeshGeometry()
    half = thickness_y / 2.0
    front = [geom.add_vertex(x, half, z) for x, z in points]
    back = [geom.add_vertex(x, -half, z) for x, z in points]
    n = len(points)

    for i in range(1, n - 1):
        geom.add_face(front[0], front[i], front[i + 1])
        geom.add_face(back[0], back[i + 1], back[i])
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(front[i], back[i], back[j])
        geom.add_face(front[i], back[j], front[j])
    return geom
def _prism_from_xy(points: list[tuple[float, float]], thickness_z: float) -> MeshGeometry:
    """Closed prism from an XY polygon, extruded in Z."""
    geom = MeshGeometry()
    half = thickness_z / 2.0
    top = [geom.add_vertex(x, y, half) for x, y in points]
    bottom = [geom.add_vertex(x, y, -half) for x, y in points]
    n = len(points)

    for i in range(1, n - 1):
        geom.add_face(top[0], top[i], top[i + 1])
        geom.add_face(bottom[0], bottom[i + 1], bottom[i])
    for i in range(n):
        j = (i + 1) % n
        geom.add_face(top[i], bottom[i], bottom[j])
        geom.add_face(top[i], bottom[j], top[j])
    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="communications_blimp")

    envelope_mat = model.material("silver_fabric", rgba=(0.78, 0.83, 0.86, 1.0))
    fin_mat = model.material("tail_blue", rgba=(0.10, 0.20, 0.38, 1.0))
    gondola_mat = model.material("gondola_white", rgba=(0.88, 0.90, 0.86, 1.0))
    window_mat = model.material("smoked_windows", rgba=(0.03, 0.09, 0.14, 1.0))
    metal_mat = model.material("brushed_metal", rgba=(0.45, 0.47, 0.46, 1.0))
    dark_mat = model.material("rubber_black", rgba=(0.01, 0.01, 0.012, 1.0))
    prop_mat = model.material("propeller_dark", rgba=(0.025, 0.025, 0.030, 1.0))
    warning_mat = model.material("orange_markings", rgba=(1.0, 0.42, 0.06, 1.0))

    hull = model.part("hull")
    hull.visual(
        mesh_from_geometry(_cigar_envelope(14.0, 1.58, 1.48), "cigar_envelope"),
        material=envelope_mat,
        name="cigar_envelope",
    )

    # Four fixed tail fins are embedded into the aft envelope as real stabilizer roots.
    upper_fin = _prism_from_xz(
        [(-5.05, 0.86), (-5.55, 2.18), (-6.35, 2.08), (-6.35, 0.78), (-5.45, 0.82)],
        0.11,
    )
    lower_fin = _prism_from_xz(
        [(-5.05, -0.86), (-5.55, -2.05), (-6.55, -1.88), (-6.35, -0.72), (-5.45, -0.82)],
        0.11,
    )
    side_fin_pos = _prism_from_xy(
        [(-5.08, 0.72), (-5.55, 2.14), (-6.35, 2.06), (-6.35, 0.70), (-5.42, 0.70)],
        0.11,
    )
    side_fin_neg = _prism_from_xy(
        [(-5.08, -0.72), (-5.55, -2.14), (-6.35, -2.06), (-6.35, -0.70), (-5.42, -0.70)],
        0.11,
    )
    hull.visual(mesh_from_geometry(upper_fin, "upper_fin"), material=fin_mat, name="upper_fin")
    hull.visual(mesh_from_geometry(lower_fin, "lower_fin"), material=fin_mat, name="lower_fin")
    hull.visual(mesh_from_geometry(side_fin_pos, "side_fin_0"), material=fin_mat, name="side_fin_0")
    hull.visual(mesh_from_geometry(side_fin_neg, "side_fin_1"), material=fin_mat, name="side_fin_1")
    hull.visual(
        Box((0.035, 0.16, 1.35)),
        origin=Origin(xyz=(-6.360, 0.0, 1.43)),
        material=metal_mat,
        name="rudder_hinge",
    )
    hull.visual(
        Box((0.035, 1.42, 0.12)),
        origin=Origin(xyz=(-6.360, 1.39, 0.0)),
        material=metal_mat,
        name="elevator_hinge_0",
    )
    hull.visual(
        Box((0.035, 1.42, 0.12)),
        origin=Origin(xyz=(-6.360, -1.39, 0.0)),
        material=metal_mat,
        name="elevator_hinge_1",
    )

    # Communication utility markings and a dorsal blade antenna seated into the fabric.
    hull.visual(
        Box((2.2, 0.035, 0.16)),
        origin=Origin(xyz=(1.6, 1.57, 0.0)),
        material=warning_mat,
        name="side_marking_0",
    )
    hull.visual(
        Box((2.2, 0.035, 0.16)),
        origin=Origin(xyz=(1.6, -1.57, 0.0)),
        material=warning_mat,
        name="side_marking_1",
    )
    hull.visual(
        Box((0.12, 0.05, 0.42)),
        origin=Origin(xyz=(0.2, 0.0, 1.67)),
        material=metal_mat,
        name="comms_blade",
    )

    gondola = model.part("gondola")
    gondola.visual(Box((3.20, 0.88, 0.70)), material=gondola_mat, name="equipment_cabin")
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(0.95, 0.445, 0.10)),
        material=window_mat,
        name="window_0",
    )
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(0.25, 0.445, 0.10)),
        material=window_mat,
        name="window_1",
    )
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(-0.45, 0.445, 0.10)),
        material=window_mat,
        name="window_2",
    )
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(0.95, -0.445, 0.10)),
        material=window_mat,
        name="window_3",
    )
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(0.25, -0.445, 0.10)),
        material=window_mat,
        name="window_4",
    )
    gondola.visual(
        Box((0.42, 0.035, 0.20)),
        origin=Origin(xyz=(-0.45, -0.445, 0.10)),
        material=window_mat,
        name="window_5",
    )
    # Four roof struts keep the gondola visibly suspended below the hull centerline.
    for idx, (x, y) in enumerate(((1.10, 0.32), (1.10, -0.32), (-1.10, 0.32), (-1.10, -0.32))):
        gondola.visual(
            Cylinder(radius=0.035, length=0.50),
            origin=Origin(xyz=(x, y, 0.60)),
            material=metal_mat,
            name=f"suspension_strut_{idx}",
        )
    gondola.visual(
        Box((2.60, 0.72, 0.06)),
        origin=Origin(xyz=(0.0, 0.0, 0.715)),
        material=metal_mat,
        name="suspension_spreader",
    )
    gondola.visual(
        Box((1.20, 0.10, 0.10)),
        origin=Origin(xyz=(0.60, 0.0, -0.34)),
        material=metal_mat,
        name="rear_equipment_rail",
    )

    model.articulation(
        "hull_to_gondola",
        ArticulationType.FIXED,
        parent=hull,
        child=gondola,
        origin=Origin(xyz=(0.0, 0.0, -2.25)),
    )

    # Side engine pods on short booms; each propeller is its own continuous rotor.
    for idx, sign in enumerate((1.0, -1.0)):
        engine = model.part(f"engine_pod_{idx}")
        engine.visual(
            mesh_from_geometry(CapsuleGeometry(0.22, 0.64, radial_segments=32), f"nacelle_{idx}"),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="nacelle",
        )
        engine.visual(
            Box((0.18, 0.34, 0.16)),
            origin=Origin(xyz=(0.0, -sign * 0.35, 0.0)),
            material=metal_mat,
            name="side_boom",
        )
        engine.visual(
            Cylinder(radius=0.08, length=0.16),
            origin=Origin(xyz=(0.50, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_mat,
            name="shaft_collar",
        )
        model.articulation(
            f"gondola_to_engine_pod_{idx}",
            ArticulationType.FIXED,
            parent=gondola,
            child=engine,
            origin=Origin(xyz=(0.50, sign * 0.93, -0.08)),
        )

        propeller = model.part(f"propeller_{idx}")
        propeller.visual(
            mesh_from_geometry(
                FanRotorGeometry(
                    0.42,
                    0.075,
                    5,
                    thickness=0.050,
                    blade_pitch_deg=34.0,
                    blade_sweep_deg=25.0,
                    blade=FanRotorBlade(shape="scimitar", tip_pitch_deg=15.0, camber=0.12),
                    hub=FanRotorHub(style="spinner", bore_diameter=0.016),
                ),
                f"propeller_rotor_{idx}",
            ),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=prop_mat,
            name="rotor",
        )
        propeller.visual(
            Cylinder(radius=0.024, length=0.17),
            origin=Origin(xyz=(-0.08, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal_mat,
            name="propeller_shaft",
        )
        model.articulation(
            f"engine_pod_{idx}_to_propeller",
            ArticulationType.CONTINUOUS,
            parent=engine,
            child=propeller,
            origin=Origin(xyz=(0.715, 0.0, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=80.0),
        )

    # Hinged tail control surfaces.
    rudder = model.part("rudder")
    rudder.visual(
        mesh_from_geometry(
            _prism_from_xz([(-0.02, -0.48), (-0.02, 0.56), (-0.68, 0.42), (-0.62, -0.36)], 0.09),
            "rudder_panel",
        ),
        material=fin_mat,
        name="rudder_panel",
    )
    model.articulation(
        "hull_to_rudder",
        ArticulationType.REVOLUTE,
        parent=hull,
        child=rudder,
        origin=Origin(xyz=(-6.35, 0.0, 1.45)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2, lower=-0.45, upper=0.45),
    )

    for idx, sign in enumerate((1.0, -1.0)):
        elevator = model.part(f"elevator_{idx}")
        inner = sign * 0.72
        outer = sign * 2.06
        mid = sign * 1.39
        elevator.visual(
            mesh_from_geometry(
                _prism_from_xy(
                    [
                        (-0.02, inner - mid),
                        (-0.02, outer - mid),
                        (-0.70, sign * 1.86 - mid),
                        (-0.62, sign * 0.78 - mid),
                    ],
                    0.085,
                ),
                f"elevator_panel_{idx}",
            ),
            material=fin_mat,
            name="elevator_panel",
        )
        model.articulation(
            f"hull_to_elevator_{idx}",
            ArticulationType.REVOLUTE,
            parent=hull,
            child=elevator,
            origin=Origin(xyz=(-6.35, mid, 0.0)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=14.0, velocity=1.1, lower=-0.35, upper=0.35),
        )

    # Rear mooring wheel and a short U fork mounted under the gondola tail.
    wheel_fork = model.part("wheel_fork")
    wheel_fork.visual(
        Box((0.40, 0.34, 0.060)),
        origin=Origin(xyz=(0.0, 0.0, -0.030)),
        material=metal_mat,
        name="fork_mount",
    )
    wheel_fork.visual(
        Box((0.14, 0.050, 0.38)),
        origin=Origin(xyz=(0.0, 0.135, -0.220)),
        material=metal_mat,
        name="fork_cheek_0",
    )
    wheel_fork.visual(
        Box((0.14, 0.050, 0.38)),
        origin=Origin(xyz=(0.0, -0.135, -0.220)),
        material=metal_mat,
        name="fork_cheek_1",
    )
    model.articulation(
        "gondola_to_wheel_fork",
        ArticulationType.FIXED,
        parent=gondola,
        child=wheel_fork,
        origin=Origin(xyz=(-1.12, 0.0, -0.34)),
    )

    mooring_wheel = model.part("mooring_wheel")
    mooring_wheel.visual(
        mesh_from_geometry(
            TireGeometry(
                0.165,
                0.095,
                inner_radius=0.115,
                tread=TireTread(style="ribbed", depth=0.006, count=18, land_ratio=0.60),
                sidewall=TireSidewall(style="rounded", bulge=0.04),
                shoulder=TireShoulder(width=0.006, radius=0.003),
            ),
            "mooring_tire",
        ),
        origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)),
        material=dark_mat,
        name="tire",
    )
    mooring_wheel.visual(
        mesh_from_geometry(
            WheelGeometry(
                0.112,
                0.070,
                rim=WheelRim(inner_radius=0.070, flange_height=0.006, flange_thickness=0.004),
                hub=WheelHub(radius=0.034, width=0.050, cap_style="domed"),
                face=WheelFace(dish_depth=0.004),
                spokes=WheelSpokes(style="straight", count=6, thickness=0.004, window_radius=0.012),
            ),
            "mooring_rim",
        ),
        origin=Origin(rpy=(0.0, 0.0, math.pi / 2.0)),
        material=metal_mat,
        name="rim",
    )
    mooring_wheel.visual(
        Cylinder(radius=0.020, length=0.25),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal_mat,
        name="axle_stub",
    )
    model.articulation(
        "wheel_fork_to_mooring_wheel",
        ArticulationType.CONTINUOUS,
        parent=wheel_fork,
        child=mooring_wheel,
        origin=Origin(xyz=(0.0, 0.0, -0.285)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=35.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
