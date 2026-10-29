# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
import cadquery as cq
WIDTH = 0.34
DEPTH = 0.23
HEIGHT = 0.58
WALL = 0.0045
BOTTOM_THICKNESS = 0.010
TOP_THICKNESS = 0.012
CORNER_RADIUS = 0.016
GRILLE_OPENING_WIDTH = 0.242
GRILLE_OPENING_HEIGHT = 0.342
GRILLE_CENTER_Z = 0.225
GRILLE_PANEL_SIZE = (0.254, 0.354)
REAR_OPENING_WIDTH = 0.286
REAR_OPENING_HEIGHT = 0.448
REAR_OPENING_CENTER_Z = 0.290
DOOR_WIDTH = 0.294
DOOR_HEIGHT = 0.456
DOOR_THICKNESS = 0.008
DOOR_GAP = 0.0015
HINGE_KNUCKLE_RADIUS = 0.006
HINGE_KNUCKLE_LENGTH = 0.135
FILTER_WIDTH = 0.272
FILTER_HEIGHT = 0.428
FILTER_MAIN_DEPTH = 0.038
FILTER_TAIL_DEPTH = 0.110
FILTER_TRAVEL = 0.102
BUTTON_WIDTH = 0.044
BUTTON_HEIGHT = 0.022
BUTTON_DEPTH = 0.008
BUTTON_FACE_DEPTH = 0.0035
BUTTON_TRAVEL = 0.0045
BUTTON_SLOT_WIDTH = 0.0415
BUTTON_SLOT_HEIGHT = 0.0195
BUTTON_ROW_Z = 0.470
BUTTON_X_OFFSETS = (-0.052, 0.0, 0.052)
def _build_body_shell() -> cq.Workplane:
    outer = cq.Workplane("XY").box(WIDTH, DEPTH, HEIGHT).translate((0.0, 0.0, HEIGHT / 2.0))
    outer = outer.edges("|Z").fillet(CORNER_RADIUS)

    inner = (
        cq.Workplane("XY")
        .box(
            WIDTH - 2.0 * WALL,
            DEPTH - 2.0 * WALL,
            HEIGHT - BOTTOM_THICKNESS - TOP_THICKNESS,
        )
        .translate((0.0, 0.0, HEIGHT / 2.0 + (BOTTOM_THICKNESS - TOP_THICKNESS) / 2.0))
    )

    shell = outer.cut(inner)

    front_grille_cut = (
        cq.Workplane("XY")
        .box(GRILLE_OPENING_WIDTH, WALL * 3.0, GRILLE_OPENING_HEIGHT)
        .translate((0.0, DEPTH / 2.0 - WALL * 1.5, GRILLE_CENTER_Z))
    )
    shell = shell.cut(front_grille_cut)

    rear_filter_cut = (
        cq.Workplane("XY")
        .box(REAR_OPENING_WIDTH, WALL * 3.0, REAR_OPENING_HEIGHT)
        .translate((0.0, -DEPTH / 2.0 + WALL * 1.5, REAR_OPENING_CENTER_Z))
    )
    shell = shell.cut(rear_filter_cut)

    control_recess = (
        cq.Workplane("XY")
        .box(0.190, 0.005, 0.040)
        .translate((0.0, DEPTH / 2.0 - 0.0025, BUTTON_ROW_Z))
    )
    shell = shell.cut(control_recess)

    for button_x in BUTTON_X_OFFSETS:
        button_slot = (
            cq.Workplane("XY")
            .box(BUTTON_SLOT_WIDTH, WALL * 4.0, BUTTON_SLOT_HEIGHT)
            .translate((button_x, DEPTH / 2.0 - WALL * 1.8, BUTTON_ROW_Z))
        )
        shell = shell.cut(button_slot)

    badge_recess = (
        cq.Workplane("XY")
        .box(0.090, 0.0015, 0.010)
        .translate((0.0, DEPTH / 2.0 - 0.00075, 0.425))
    )
    shell = shell.cut(badge_recess)

    return shell
def _build_button_shape() -> cq.Workplane:
    cap = (
        cq.Workplane("XY")
        .box(BUTTON_WIDTH, BUTTON_FACE_DEPTH, BUTTON_HEIGHT)
        .edges("|Y")
        .fillet(0.0025)
        .translate((0.0, BUTTON_FACE_DEPTH / 2.0, 0.0))
    )
    stem = (
        cq.Workplane("XY")
        .box(BUTTON_SLOT_WIDTH, BUTTON_DEPTH, BUTTON_SLOT_HEIGHT)
        .translate((0.0, -BUTTON_DEPTH / 2.0, 0.0))
    )
    return cap.union(stem)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="floor_air_purifier")

    shell_white = model.material("shell_white", rgba=(0.92, 0.93, 0.91, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.62, 0.65, 0.66, 1.0))
    charcoal = model.material("charcoal", rgba=(0.18, 0.20, 0.22, 1.0))
    filter_black = model.material("filter_black", rgba=(0.14, 0.15, 0.16, 1.0))
    filter_gray = model.material("filter_gray", rgba=(0.36, 0.39, 0.41, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shell(), "purifier_body_shell"),
        material=shell_white,
        name="shell",
    )
    body.visual(
        mesh_from_geometry(
            VentGrilleGeometry(
                GRILLE_PANEL_SIZE,
                frame=0.010,
                face_thickness=0.0035,
                slat_pitch=0.016,
                slat_width=0.0085,
                slat_angle_deg=32.0,
                slats=VentGrilleSlats(profile="airfoil", direction="down", divider_count=2, divider_width=0.004),
                frame_profile=VentGrilleFrame(style="beveled", depth=0.0012),
                sleeve=VentGrilleSleeve(style="none"),
            ),
            "purifier_front_grille",
        ),
        origin=Origin(
            xyz=(0.0, DEPTH / 2.0 - 0.0032, GRILLE_CENTER_Z),
            rpy=(-math.pi / 2.0, 0.0, 0.0),
        ),
        material=trim_gray,
        name="front_grille",
    )
    body.visual(
        Box((0.088, 0.003, 0.008)),
        origin=Origin(xyz=(0.0, DEPTH / 2.0 - 0.0015, 0.425)),
        material=trim_gray,
        name="badge_strip",
    )
    body.visual(
        Box((0.250, DEPTH - 0.020, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=trim_gray,
        name="base_rail",
    )

    button_carrier = model.part("button_carrier")
    button_carrier.visual(
        Box((0.186, 0.006, 0.032)),
        origin=Origin(xyz=(0.0, -0.003, 0.0)),
        material=trim_gray,
        name="carrier_plate",
    )
    for side_index, side_sign in enumerate((-1.0, 1.0)):
        button_carrier.visual(
            Box((0.014, 0.010, 0.028)),
            origin=Origin(xyz=(side_sign * 0.094, -0.001, 0.0)),
            material=trim_gray,
            name=f"carrier_mount_{side_index}",
        )
    for index, button_x in enumerate(BUTTON_X_OFFSETS):
        for side_index, side_sign in enumerate((-1.0, 1.0)):
            button_carrier.visual(
                Box((0.006, 0.012, 0.022)),
                origin=Origin(
                    xyz=(
                        button_x + side_sign * (BUTTON_SLOT_WIDTH / 2.0 + 0.003),
                        -0.006,
                        0.0,
                    )
                ),
                material=trim_gray,
                name=f"button_guide_{index}_{side_index}",
            )

    filter_door = model.part("filter_door")
    filter_door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, -DOOR_THICKNESS / 2.0, 0.0)),
        material=shell_white,
        name="door_panel",
    )
    filter_door.visual(
        Cylinder(radius=HINGE_KNUCKLE_RADIUS, length=HINGE_KNUCKLE_LENGTH),
        origin=Origin(xyz=(0.0, -DOOR_THICKNESS / 2.0, 0.145)),
        material=trim_gray,
        name="hinge_knuckle_top",
    )
    filter_door.visual(
        Cylinder(radius=HINGE_KNUCKLE_RADIUS, length=HINGE_KNUCKLE_LENGTH),
        origin=Origin(xyz=(0.0, -DOOR_THICKNESS / 2.0, -0.145)),
        material=trim_gray,
        name="hinge_knuckle_bottom",
    )
    filter_door.visual(
        Box((0.040, 0.014, 0.090)),
        origin=Origin(xyz=(-DOOR_WIDTH + 0.030, -DOOR_THICKNESS - 0.007, 0.0)),
        material=trim_gray,
        name="door_handle",
    )

    filter_pack = model.part("filter_pack")
    filter_pack.visual(
        Box((FILTER_WIDTH, FILTER_MAIN_DEPTH, FILTER_HEIGHT)),
        origin=Origin(xyz=(0.0, FILTER_MAIN_DEPTH / 2.0, 0.0)),
        material=filter_gray,
        name="filter_frame",
    )
    filter_pack.visual(
        Box((FILTER_WIDTH - 0.022, FILTER_MAIN_DEPTH - 0.010, FILTER_HEIGHT - 0.024)),
        origin=Origin(xyz=(0.0, FILTER_MAIN_DEPTH / 2.0, 0.0)),
        material=filter_black,
        name="filter_media",
    )
    filter_pack.visual(
        Box((FILTER_WIDTH - 0.060, FILTER_TAIL_DEPTH, FILTER_HEIGHT - 0.120)),
        origin=Origin(xyz=(0.0, FILTER_MAIN_DEPTH + FILTER_TAIL_DEPTH / 2.0, 0.0)),
        material=charcoal,
        name="guide_tail",
    )
    filter_pack.visual(
        Box((0.085, 0.007, 0.028)),
        origin=Origin(xyz=(0.0, -0.0035, FILTER_HEIGHT / 2.0 - 0.034)),
        material=trim_gray,
        name="pull_tab",
    )

    button_mesh = mesh_from_cadquery(_build_button_shape(), "purifier_button")
    for index in range(3):
        button = model.part(f"button_{index}")
        button.visual(
            button_mesh,
            origin=Origin(),
            material=charcoal,
            name="button_cap",
        )

    model.articulation(
        "body_to_filter_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=filter_door,
        origin=Origin(
            xyz=(
                REAR_OPENING_WIDTH / 2.0 + 0.004,
                -DEPTH / 2.0 - DOOR_GAP,
                REAR_OPENING_CENTER_Z,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.2,
            lower=0.0,
            upper=math.radians(110.0),
        ),
    )

    model.articulation(
        "body_to_button_carrier",
        ArticulationType.FIXED,
        parent=body,
        child=button_carrier,
        origin=Origin(xyz=(0.0, DEPTH / 2.0 - WALL, BUTTON_ROW_Z)),
    )

    model.articulation(
        "body_to_filter_pack",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_pack,
        origin=Origin(
            xyz=(
                0.0,
                -DEPTH / 2.0 + WALL + 0.001,
                REAR_OPENING_CENTER_Z,
            )
        ),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.16,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    for index, button_x in enumerate(BUTTON_X_OFFSETS):
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=f"button_{index}",
            origin=Origin(xyz=(button_x, DEPTH / 2.0, BUTTON_ROW_Z)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=3.0,
                velocity=0.06,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
