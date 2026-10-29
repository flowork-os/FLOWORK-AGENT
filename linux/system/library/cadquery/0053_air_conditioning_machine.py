# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_conditioning_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_conditioning_machine

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
WIDTH = 0.86
DEPTH = 0.24
HEIGHT = 0.60
CORNER_RADIUS = 0.012
SHELL_WALL = 0.008
BACK_WALL = 0.014
BOTTOM_WALL = 0.020
FRONT_FACE = 0.028
TOP_FACE = 0.012
INTAKE_WIDTH = 0.74
INTAKE_HEIGHT = 0.34
INTAKE_CENTER_Z = 0.28
OUTLET_WIDTH = 0.76
OUTLET_DEPTH = 0.055
OUTLET_FRONT_LIP = 0.014
OUTLET_CENTER_X = DEPTH / 2.0 - OUTLET_FRONT_LIP - OUTLET_DEPTH / 2.0
OUTLET_HINGE_X = DEPTH / 2.0 - OUTLET_FRONT_LIP
FLAP_WIDTH = OUTLET_WIDTH - 0.018
FLAP_DEPTH = 0.058
FLAP_THICKNESS = 0.006
DRAWER_FACE_WIDTH = INTAKE_WIDTH - 0.022
DRAWER_FACE_HEIGHT = INTAKE_HEIGHT - 0.024
DRAWER_FACE_THICKNESS = 0.004
DRAWER_TRAVEL = 0.075
DRAWER_HOME_X = DEPTH / 2.0 - 0.007
GUIDE_LENGTH = 0.075
GUIDE_WIDTH = 0.038
GUIDE_HEIGHT = 0.014
GUIDE_CENTER_X = 0.057
GUIDE_CENTER_Z = INTAKE_CENTER_Z + 0.032
GUIDE_CENTER_Y = DRAWER_FACE_WIDTH / 2.0 - 0.008
RUNNER_LENGTH = 0.100
RUNNER_WIDTH = 0.016
RUNNER_HEIGHT = 0.014
RUNNER_CENTER_X = -(RUNNER_LENGTH / 2.0 + DRAWER_FACE_THICKNESS / 2.0)
RUNNER_CENTER_Y = DRAWER_FACE_WIDTH / 2.0 - RUNNER_WIDTH / 2.0
RUNNER_CENTER_Z = GUIDE_CENTER_Z - INTAKE_CENTER_Z - (GUIDE_HEIGHT + RUNNER_HEIGHT) / 2.0
def _add_box(
    part,
    *,
    size: tuple[float, float, float],
    xyz: tuple[float, float, float],
    material: str,
    name: str,
    rpy: tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    part.visual(
        Box(size),
        origin=Origin(xyz=xyz, rpy=rpy),
        material=material,
        name=name,
    )
def _build_body_shell() -> cq.Workplane:
    shell = cq.Workplane("XY").box(DEPTH, WIDTH, HEIGHT).translate((0.0, 0.0, HEIGHT / 2.0))
    shell = shell.edges("|Z").fillet(CORNER_RADIUS)
    shell = shell.edges(">Z").fillet(0.008)

    cavity_depth = DEPTH - FRONT_FACE - BACK_WALL
    cavity_height = HEIGHT - BOTTOM_WALL - TOP_FACE
    cavity_center_x = (BACK_WALL - FRONT_FACE) / 2.0
    cavity_center_z = BOTTOM_WALL + cavity_height / 2.0
    shell = shell.cut(
        cq.Workplane("XY")
        .box(cavity_depth, WIDTH - 2.0 * SHELL_WALL, cavity_height)
        .translate((cavity_center_x, 0.0, cavity_center_z))
    )

    front_cut_depth = FRONT_FACE + 0.022
    front_cut_x = DEPTH / 2.0 - front_cut_depth / 2.0 + 0.002
    shell = shell.cut(
        cq.Workplane("XY")
        .box(front_cut_depth, INTAKE_WIDTH, INTAKE_HEIGHT)
        .translate((front_cut_x, 0.0, INTAKE_CENTER_Z))
    )

    outlet_cut_height = TOP_FACE + 0.018
    outlet_cut_z = HEIGHT - outlet_cut_height / 2.0 + 0.006
    shell = shell.cut(
        cq.Workplane("XY")
        .box(OUTLET_DEPTH, OUTLET_WIDTH, outlet_cut_height)
        .translate((OUTLET_CENTER_X, 0.0, outlet_cut_z))
    )

    return shell
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_console_air_conditioner")

    model.material("shell_white", color=(0.92, 0.93, 0.95))
    model.material("grille_white", color=(0.88, 0.89, 0.91))
    model.material("shadow_dark", color=(0.20, 0.22, 0.24))
    model.material("rail_gray", color=(0.66, 0.69, 0.72))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shell(), "console_body_shell"),
        material="shell_white",
        name="body_shell",
    )
    for index, side in enumerate((-1.0, 1.0)):
        _add_box(
            body,
            size=(GUIDE_LENGTH, GUIDE_WIDTH, GUIDE_HEIGHT),
            xyz=(GUIDE_CENTER_X, side * GUIDE_CENTER_Y, GUIDE_CENTER_Z),
            material="rail_gray",
            name=f"guide_{index}",
        )

    flap = model.part("discharge_flap")
    _add_box(
        flap,
        size=(FLAP_DEPTH, FLAP_WIDTH, FLAP_THICKNESS),
        xyz=(-FLAP_DEPTH / 2.0, 0.0, FLAP_THICKNESS / 2.0),
        material="grille_white",
        name="flap_panel",
    )

    drawer = model.part("filter_drawer")
    drawer.visual(
        mesh_from_geometry(
            SlotPatternPanelGeometry(
                (DRAWER_FACE_WIDTH, DRAWER_FACE_HEIGHT),
                DRAWER_FACE_THICKNESS,
                slot_size=(0.090, 0.006),
                pitch=(0.112, 0.018),
                frame=0.014,
                corner_radius=0.006,
            ),
            "filter_drawer_grille",
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(pi / 2.0, 0.0, pi / 2.0)),
        material="grille_white",
        name="grille_face",
    )
    _add_box(
        drawer,
        size=(0.006, DRAWER_FACE_WIDTH - 0.040, DRAWER_FACE_HEIGHT - 0.040),
        xyz=(-0.005, 0.0, 0.0),
        material="shadow_dark",
        name="filter_media",
    )
    _add_box(
        drawer,
        size=(0.008, 0.090, 0.012),
        xyz=(0.005, 0.0, -DRAWER_FACE_HEIGHT / 2.0 + 0.012),
        material="grille_white",
        name="pull_tab",
    )
    for index, side in enumerate((-1.0, 1.0)):
        _add_box(
            drawer,
            size=(RUNNER_LENGTH, RUNNER_WIDTH, RUNNER_HEIGHT),
            xyz=(RUNNER_CENTER_X, side * RUNNER_CENTER_Y, RUNNER_CENTER_Z),
            material="rail_gray",
            name=f"runner_{index}",
        )

    model.articulation(
        "body_to_discharge_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flap,
        origin=Origin(xyz=(OUTLET_HINGE_X, 0.0, HEIGHT)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.25, effort=8.0, velocity=1.6),
    )
    model.articulation(
        "body_to_filter_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(DRAWER_HOME_X, 0.0, INTAKE_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=DRAWER_TRAVEL, effort=30.0, velocity=0.20),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
