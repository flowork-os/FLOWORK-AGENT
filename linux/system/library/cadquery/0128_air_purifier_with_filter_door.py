# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

from __future__ import annotations

import cadquery as cq
import math
from typing import Optional, Sequence, Union
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

# ===== panels_vents (5 syms) =====
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

class PerforatedPanelGeometry(MeshGeometry):
    """Rectangular plate (XY, extruded along Z) with a grid of round holes."""

    def __init__(
        self,
        panel_size,
        thickness,
        *,
        hole_diameter,
        pitch,
        frame=0.008,
        corner_radius=0.0,
        stagger=False,
        center=True,
    ):
        super().__init__()
        panel_w = float(panel_size[0])
        panel_h = float(panel_size[1])
        thickness = float(thickness)
        hole_diameter = float(hole_diameter)
        frame = float(frame)
        corner_radius = max(0.0, float(corner_radius))
        pitch_x, pitch_y = _normalize_pitch_2d(pitch)

        if panel_w <= 0.0 or panel_h <= 0.0 or thickness <= 0.0:
            raise ValidationError("panel_size and thickness must be positive")
        if hole_diameter <= 0.0:
            raise ValidationError("hole_diameter must be positive")
        if frame < 0.0 or frame >= min(panel_w, panel_h) * 0.5:
            raise ValidationError("frame must be >= 0 and less than half of min(panel_size)")
        if pitch_x <= hole_diameter or pitch_y <= hole_diameter:
            raise ValidationError("pitch must be greater than hole_diameter on both axes")

        hole_radius = hole_diameter * 0.5
        x_limit = panel_w * 0.5 - frame - hole_radius
        y_limit = panel_h * 0.5 - frame - hole_radius
        if x_limit < -1e-9 or y_limit < -1e-9:
            raise ValidationError("frame/hole_diameter leave no usable perforation area")

        y_positions = _centered_axis_positions(y_limit, pitch_y)
        if not y_positions:
            raise ValidationError("No perforation rows fit panel; increase panel size or reduce pitch")

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
            raise ValidationError("No perforation columns fit panel; increase panel size or reduce pitch")

        shape = cq.Workplane("XY").box(panel_w, panel_h, thickness)
        if corner_radius > 0.0:
            shape = shape.edges("|Z").fillet(
                min(corner_radius, panel_w * 0.5 - 1e-4, panel_h * 0.5 - 1e-4)
            )

        cut_depth = thickness + max(0.002, thickness * 0.5)
        cut_shape = None
        for row_points in point_rows:
            row_cut = (
                cq.Workplane("XY")
                .pushPoints(row_points)
                .circle(hole_radius)
                .extrude(cut_depth, both=True)
            )
            cut_shape = row_cut if cut_shape is None else cut_shape.union(row_cut)
        if cut_shape is not None:
            shape = shape.cut(cut_shape)

        _panels_vents_finish(self, shape, center)

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bathroom_wall_air_purifier")

    white = model.material("warm_white_plastic", rgba=(0.92, 0.94, 0.91, 1.0))
    off_white = model.material("slightly_darker_cover", rgba=(0.86, 0.89, 0.86, 1.0))
    graphite = model.material("charcoal_filter_media", rgba=(0.08, 0.09, 0.09, 1.0))
    pale_filter = model.material("washable_blue_filter", rgba=(0.45, 0.70, 0.82, 1.0))
    bracket_grey = model.material("powder_coated_bracket", rgba=(0.56, 0.58, 0.58, 1.0))
    hinge_metal = model.material("brushed_hinge_metal", rgba=(0.65, 0.66, 0.62, 1.0))
    screw_dark = model.material("dark_screw_heads", rgba=(0.08, 0.08, 0.075, 1.0))

    width = 0.320
    height = 0.520
    depth = 0.120
    wall = 0.012

    # The root is the fixed wall mounting bracket.  Its frame coincides with the
    # rear-bottom-center of the purifier housing, so the housing can be fixed to
    # it with a clean, contact-supported joint.
    bracket = model.part("wall_bracket")
    bracket.visual(
        Box((0.250, 0.006, 0.410)),
        origin=Origin(xyz=(0.0, -0.012, height * 0.52)),
        material=bracket_grey,
        name="wall_plate",
    )
    for idx, z in enumerate((0.112, 0.438)):
        bracket.visual(
            Box((0.226, 0.012, 0.018)),
            origin=Origin(xyz=(0.0, -0.006, z)),
            material=bracket_grey,
            name=f"hook_rail_{idx}",
        )
    for idx, z in enumerate((0.126, 0.424)):
        bracket.visual(
            Cylinder(radius=0.013, length=0.004),
            origin=Origin(xyz=(0.0, -0.0165, z), rpy=(pi / 2.0, 0.0, 0.0)),
            material=screw_dark,
            name=f"screw_head_{idx}",
        )
        bracket.visual(
            Box((0.018, 0.0015, 0.003)),
            origin=Origin(xyz=(0.0, -0.019, z), rpy=(0.0, 0.0, 0.0)),
            material=bracket_grey,
            name=f"screw_slot_{idx}",
        )

    housing = model.part("housing")
    housing.visual(
        Box((width, wall, height)),
        origin=Origin(xyz=(0.0, wall / 2.0, height / 2.0)),
        material=white,
        name="rear_panel",
    )
    housing.visual(
        Box((wall, depth, height)),
        origin=Origin(xyz=(-width / 2.0 + wall / 2.0, depth / 2.0, height / 2.0)),
        material=white,
        name="side_wall_0",
    )
    housing.visual(
        Box((wall, depth, height)),
        origin=Origin(xyz=(width / 2.0 - wall / 2.0, depth / 2.0, height / 2.0)),
        material=white,
        name="side_wall_1",
    )
    housing.visual(
        Box((width, depth, wall)),
        origin=Origin(xyz=(0.0, depth / 2.0, height - wall / 2.0)),
        material=white,
        name="top_wall",
    )
    housing.visual(
        Box((width, depth, wall)),
        origin=Origin(xyz=(0.0, depth / 2.0, wall / 2.0)),
        material=white,
        name="bottom_wall",
    )
    # Internal tray slides and a small front base fascia make the tray read as a
    # guided washable-filter cassette rather than a loose floating insert.
    for idx, x in enumerate((-0.129, 0.129)):
        housing.visual(
            Box((0.014, depth - 0.010, 0.006)),
            origin=Origin(xyz=(x, depth / 2.0, 0.030)),
            material=off_white,
            name=f"tray_slide_{idx}",
        )
    housing.visual(
        Box((0.285, 0.006, 0.008)),
        origin=Origin(xyz=(0.0, depth - 0.003, 0.014)),
        material=white,
        name="base_fascia",
    )

    # Two visible stationary hinge knuckle mounts at the right edge.  The moving
    # knuckles live on the cover part and share the revolute axis.
    pivot_x = width / 2.0 + 0.014
    pivot_y = depth + 0.008
    for idx, zc in enumerate((0.146, 0.420)):
        housing.visual(
            Box((0.030, 0.006, 0.078)),
            origin=Origin(xyz=(width / 2.0 + 0.006, depth + 0.003, zc)),
            material=hinge_metal,
            name=f"hinge_leaf_{idx}",
        )
        housing.visual(
            Cylinder(radius=0.0055, length=0.022),
            origin=Origin(xyz=(pivot_x, pivot_y, zc - 0.026)),
            material=hinge_metal,
            name=f"fixed_knuckle_{idx}_0",
        )
        housing.visual(
            Cylinder(radius=0.0055, length=0.022),
            origin=Origin(xyz=(pivot_x, pivot_y, zc + 0.026)),
            material=hinge_metal,
            name=f"fixed_knuckle_{idx}_1",
        )

    model.articulation(
        "bracket_to_housing",
        ArticulationType.FIXED,
        parent=bracket,
        child=housing,
        origin=Origin(),
    )

    cover = model.part("front_cover")
    cover_width = 0.306
    cover_height = 0.455
    cover_bottom = 0.055
    cover_center_z = cover_bottom + cover_height / 2.0
    cover_x_right = -0.012
    cover_center_x = cover_x_right - cover_width / 2.0
    cover_t = 0.012
    stile = 0.022
    top_rail = 0.024

    cover.visual(
        Box((stile, cover_t, cover_height)),
        origin=Origin(xyz=(cover_x_right - cover_width + stile / 2.0, 0.0, cover_center_z)),
        material=off_white,
        name="cover_side_stile",
    )
    cover.visual(
        Box((0.030, cover_t, cover_height)),
        origin=Origin(xyz=(cover_x_right - 0.015, 0.0, cover_center_z)),
        material=off_white,
        name="cover_hinge_stile",
    )
    cover.visual(
        Box((cover_width, cover_t, top_rail)),
        origin=Origin(xyz=(cover_center_x, 0.0, cover_bottom + top_rail / 2.0)),
        material=off_white,
        name="cover_bottom_rail",
    )
    cover.visual(
        Box((cover_width, cover_t, top_rail)),
        origin=Origin(xyz=(cover_center_x, 0.0, cover_bottom + cover_height - top_rail / 2.0)),
        material=off_white,
        name="cover_top_rail",
    )

    grille = SlotPatternPanelGeometry(
        (0.265, 0.425),
        0.003,
        slot_size=(0.044, 0.006),
        pitch=(0.059, 0.018),
        frame=0.010,
        corner_radius=0.006,
        slot_angle_deg=0.0,
        stagger=True,
    )
    cover.visual(
        mesh_from_geometry(grille, "front_cover_grille"),
        origin=Origin(xyz=(cover_center_x, 0.0045, cover_center_z + 0.008), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=graphite,
        name="front_grille",
    )
    cover.visual(
        Box((0.010, 0.005, 0.190)),
        origin=Origin(xyz=(cover_x_right - cover_width + 0.022, 0.0075, cover_center_z - 0.010)),
        material=graphite,
        name="finger_pull",
    )

    for idx, zc in enumerate((0.146, 0.420)):
        cover.visual(
            Cylinder(radius=0.0052, length=0.026),
            origin=Origin(xyz=(0.0, 0.0, zc)),
            material=hinge_metal,
            name=f"moving_knuckle_{idx}",
        )
        cover.visual(
            Box((0.010, 0.005, 0.030)),
            origin=Origin(xyz=(-0.009, 0.0, zc)),
            material=hinge_metal,
            name=f"moving_leaf_{idx}",
        )

    model.articulation(
        "cover_hinge",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=cover,
        origin=Origin(xyz=(pivot_x, pivot_y, 0.0)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.2, lower=0.0, upper=1.75),
    )

    tray = model.part("filter_tray")
    tray_w = 0.252
    tray_l = 0.120
    tray_h = 0.018
    tray_y_center = 0.045
    tray_z = 0.030
    rail_w = 0.014
    lip_y = tray_y_center + tray_l / 2.0 + 0.007

    tray.visual(
        Box((rail_w, tray_l, tray_h)),
        origin=Origin(xyz=(-tray_w / 2.0 + rail_w / 2.0, tray_y_center, tray_z)),
        material=off_white,
        name="tray_side_0",
    )
    tray.visual(
        Box((rail_w, tray_l, tray_h)),
        origin=Origin(xyz=(tray_w / 2.0 - rail_w / 2.0, tray_y_center, tray_z)),
        material=off_white,
        name="tray_side_1",
    )
    tray.visual(
        Box((tray_w, 0.014, tray_h)),
        origin=Origin(xyz=(0.0, tray_y_center - tray_l / 2.0 + 0.007, tray_z)),
        material=off_white,
        name="tray_rear_rail",
    )
    tray.visual(
        Box((tray_w, 0.014, tray_h)),
        origin=Origin(xyz=(0.0, tray_y_center + tray_l / 2.0 - 0.007, tray_z)),
        material=off_white,
        name="tray_front_rail",
    )
    filter_mesh = PerforatedPanelGeometry(
        (0.232, 0.104),
        0.003,
        hole_diameter=0.0045,
        pitch=(0.011, 0.011),
        frame=0.006,
        corner_radius=0.004,
        stagger=True,
    )
    tray.visual(
        mesh_from_geometry(filter_mesh, "washable_filter_mesh"),
        origin=Origin(xyz=(0.0, tray_y_center, tray_z + 0.007)),
        material=pale_filter,
        name="filter_mesh",
    )
    tray.visual(
        Box((0.120, 0.014, 0.018)),
        origin=Origin(xyz=(0.0, lip_y, tray_z - 0.002)),
        material=graphite,
        name="tray_pull_lip",
    )

    model.articulation(
        "tray_slide",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=tray,
        origin=Origin(xyz=(0.0, 0.025, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=0.35, lower=0.0, upper=0.075),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
