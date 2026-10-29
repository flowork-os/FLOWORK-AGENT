# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_conditioning_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_conditioning_machine

from __future__ import annotations

import cadquery as cq
import math
from dataclasses import dataclass
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
BODY_WIDTH = 0.420
BODY_DEPTH = 0.330
BODY_BOTTOM = 0.048
LOWER_BODY_HEIGHT = 0.512
UPPER_BODY_WIDTH = 0.392
UPPER_BODY_DEPTH = 0.304
UPPER_BODY_HEIGHT = 0.120
TOP_WIDTH = 0.400
TOP_DEPTH = 0.310
TOP_RING_HEIGHT = 0.048
TOP_Z0 = BODY_BOTTOM + LOWER_BODY_HEIGHT + UPPER_BODY_HEIGHT
TOP_Z1 = TOP_Z0 + TOP_RING_HEIGHT
OUTLET_WIDTH = 0.260
OUTLET_DEPTH = 0.110
OUTLET_CENTER_Y = 0.020
OUTLET_FRONT_Y = OUTLET_CENTER_Y + OUTLET_DEPTH * 0.5
CONTROL_PANEL_WIDTH = 0.240
CONTROL_PANEL_HEIGHT = 0.120
CONTROL_PANEL_DEPTH = 0.020
CONTROL_PANEL_CENTER_Z = 0.615
CONTROL_PANEL_FRONT_Y = UPPER_BODY_DEPTH * 0.5 + CONTROL_PANEL_DEPTH
def _add_caster(body, *, x: float, y: float, wheel_material: str, fork_material: str) -> None:
    body.visual(
        Cylinder(radius=0.005, length=0.014),
        origin=Origin(xyz=(x, y, 0.041)),
        material=fork_material,
        name=f"stem_{'p' if x >= 0 else 'n'}{'p' if y >= 0 else 'n'}",
    )
    body.visual(
        Box((0.018, 0.012, 0.010)),
        origin=Origin(xyz=(x, y, 0.029)),
        material=fork_material,
        name=f"fork_{'p' if x >= 0 else 'n'}{'p' if y >= 0 else 'n'}",
    )
    body.visual(
        Cylinder(radius=0.018, length=0.010),
        origin=Origin(
            xyz=(x, y, 0.018),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=wheel_material,
        name=f"wheel_{'p' if x >= 0 else 'n'}{'p' if y >= 0 else 'n'}",
    )
def _build_button_part(model: ArticulatedObject, name: str, material: str) -> None:
    button = model.part(name)
    button.visual(
        Box((0.026, 0.008, 0.014)),
        origin=Origin(xyz=(0.0, 0.004, 0.007)),
        material=material,
        name="base",
    )
    button.visual(
        Box((0.022, 0.006, 0.010)),
        origin=Origin(xyz=(0.0, 0.011, 0.007)),
        material=material,
        name="cap",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_room_ac")

    shell = model.material("shell", rgba=(0.90, 0.91, 0.92, 1.0))
    trim = model.material("trim", rgba=(0.79, 0.81, 0.83, 1.0))
    panel = model.material("panel", rgba=(0.20, 0.24, 0.28, 1.0))
    vent = model.material("vent", rgba=(0.18, 0.20, 0.22, 1.0))
    wheel = model.material("wheel", rgba=(0.12, 0.12, 0.13, 1.0))
    fork = model.material("fork", rgba=(0.55, 0.57, 0.60, 1.0))
    control = model.material("control", rgba=(0.83, 0.85, 0.87, 1.0))
    dial_finish = model.material("dial_finish", rgba=(0.16, 0.17, 0.18, 1.0))
    indicator = model.material("indicator", rgba=(0.90, 0.92, 0.95, 1.0))

    body = model.part("body")
    body.visual(
        Box((BODY_WIDTH, BODY_DEPTH, LOWER_BODY_HEIGHT)),
        origin=Origin(xyz=(0.0, 0.0, BODY_BOTTOM + LOWER_BODY_HEIGHT * 0.5)),
        material=shell,
        name="lower_shell",
    )
    body.visual(
        Box((UPPER_BODY_WIDTH, UPPER_BODY_DEPTH, UPPER_BODY_HEIGHT)),
        origin=Origin(xyz=(0.0, 0.0, BODY_BOTTOM + LOWER_BODY_HEIGHT + UPPER_BODY_HEIGHT * 0.5)),
        material=shell,
        name="upper_shell",
    )
    body.visual(
        Box((TOP_WIDTH, (TOP_DEPTH - OUTLET_DEPTH) * 0.5, TOP_RING_HEIGHT)),
        origin=Origin(
            xyz=(
                0.0,
                (OUTLET_FRONT_Y + TOP_DEPTH * 0.5) * 0.5,
                TOP_Z0 + TOP_RING_HEIGHT * 0.5,
            )
        ),
        material=trim,
        name="front_top",
    )
    body.visual(
        Box((TOP_WIDTH, 0.120, TOP_RING_HEIGHT)),
        origin=Origin(xyz=(0.0, -0.095, TOP_Z0 + TOP_RING_HEIGHT * 0.5)),
        material=trim,
        name="rear_top",
    )
    body.visual(
        Box(((TOP_WIDTH - OUTLET_WIDTH) * 0.5, TOP_DEPTH, TOP_RING_HEIGHT)),
        origin=Origin(xyz=(-0.165, 0.0, TOP_Z0 + TOP_RING_HEIGHT * 0.5)),
        material=trim,
        name="left_top",
    )
    body.visual(
        Box(((TOP_WIDTH - OUTLET_WIDTH) * 0.5, TOP_DEPTH, TOP_RING_HEIGHT)),
        origin=Origin(xyz=(0.165, 0.0, TOP_Z0 + TOP_RING_HEIGHT * 0.5)),
        material=trim,
        name="right_top",
    )
    body.visual(
        mesh_from_geometry(
            VentGrilleGeometry(
                (OUTLET_WIDTH, OUTLET_DEPTH),
                frame=0.010,
                face_thickness=0.004,
                duct_depth=0.018,
                slat_pitch=0.018,
                slat_width=0.008,
                slat_angle_deg=28.0,
                slats=VentGrilleSlats(profile="airfoil", direction="down"),
                sleeve=VentGrilleSleeve(style="none"),
            ),
            "portable_ac_top_grille",
        ),
        origin=Origin(xyz=(0.0, OUTLET_CENTER_Y, TOP_Z0 + 0.024)),
        material=vent,
        name="grille",
    )
    body.visual(
        Box((CONTROL_PANEL_WIDTH, CONTROL_PANEL_DEPTH, CONTROL_PANEL_HEIGHT)),
        origin=Origin(
            xyz=(
                0.0,
                UPPER_BODY_DEPTH * 0.5 + CONTROL_PANEL_DEPTH * 0.5,
                CONTROL_PANEL_CENTER_Z,
            )
        ),
        material=panel,
        name="panel",
    )
    body.visual(
        Box((0.080, 0.006, 0.020)),
        origin=Origin(
            xyz=(
                0.0,
                CONTROL_PANEL_FRONT_Y - 0.003,
                CONTROL_PANEL_CENTER_Z + 0.042,
            )
        ),
        material=trim,
        name="display_strip",
    )

    for x_sign in (-1.0, 1.0):
        body.visual(
            Box((0.012, 0.045, 0.090)),
            origin=Origin(
                xyz=(
                    x_sign * 0.176,
                    0.0,
                    BODY_BOTTOM + LOWER_BODY_HEIGHT - 0.010,
                )
            ),
            material=trim,
            name=f"side_cap_{0 if x_sign < 0 else 1}",
        )

    _add_caster(body, x=-0.155, y=-0.112, wheel_material=wheel, fork_material=fork)
    _add_caster(body, x=0.155, y=-0.112, wheel_material=wheel, fork_material=fork)
    _add_caster(body, x=-0.155, y=0.112, wheel_material=wheel, fork_material=fork)
    _add_caster(body, x=0.155, y=0.112, wheel_material=wheel, fork_material=fork)

    flap = model.part("flap")
    flap.visual(
        Box((0.244, 0.106, 0.005)),
        origin=Origin(xyz=(0.0, -0.053, 0.0025)),
        material=trim,
        name="panel",
    )
    flap.visual(
        Box((0.244, 0.006, 0.014)),
        origin=Origin(xyz=(0.0, -0.003, 0.007)),
        material=trim,
        name="nose",
    )
    flap.visual(
        Box((0.244, 0.008, 0.012)),
        origin=Origin(xyz=(0.0, -0.102, 0.006)),
        material=trim,
        name="rear_lip",
    )

    dial = model.part("dial")
    dial.visual(
        Cylinder(radius=0.025, length=0.008),
        origin=Origin(
            xyz=(0.0, 0.004, 0.0),
            rpy=(-math.pi / 2.0, 0.0, 0.0),
        ),
        material=panel,
        name="skirt",
    )
    dial.visual(
        Cylinder(radius=0.020, length=0.020),
        origin=Origin(
            xyz=(0.0, 0.014, 0.0),
            rpy=(-math.pi / 2.0, 0.0, 0.0),
        ),
        material=dial_finish,
        name="knob",
    )
    dial.visual(
        Box((0.003, 0.003, 0.014)),
        origin=Origin(xyz=(0.0, 0.0245, 0.011)),
        material=indicator,
        name="indicator",
    )

    button_positions = (-0.055, 0.0, 0.055)
    for index in range(3):
        _build_button_part(model, f"button_{index}", control)

    model.articulation(
        "body_to_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flap,
        origin=Origin(xyz=(0.0, OUTLET_FRONT_Y, TOP_Z1)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=5.0,
            velocity=2.5,
            lower=0.0,
            upper=1.20,
        ),
    )
    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(
            xyz=(
                0.0,
                CONTROL_PANEL_FRONT_Y,
                CONTROL_PANEL_CENTER_Z - 0.008,
            )
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.25, velocity=6.0),
    )

    for index, button_x in enumerate(button_positions):
        button = model.get_part(f"button_{index}")
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(
                xyz=(
                    button_x,
                    CONTROL_PANEL_FRONT_Y,
                    CONTROL_PANEL_CENTER_Z + 0.036,
                )
            ),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=5.0,
                velocity=0.08,
                lower=0.0,
                upper=0.004,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
