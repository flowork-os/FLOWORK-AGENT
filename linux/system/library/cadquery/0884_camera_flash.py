# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

from __future__ import annotations

import cadquery as cq
import math
from typing import Iterable, Literal, Optional, Sequence, Tuple, Union

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

# ===== brackets_hinges_bezels (3 syms) =====
def _brackets_hinges_bezels_shift_to_z0(shape):
    bb = shape.BoundingBox()
    return shape.translate(cq.Vector(0.0, 0.0, -bb.zmin))

def _brackets_hinges_bezels_finish(target, model, center):
    shape = _to_shape(model)
    if not center:
        shape = _brackets_hinges_bezels_shift_to_z0(shape)
    target._set(shape)

class TrunnionYokeGeometry(MeshGeometry):
    """Build a trunnion support yoke with a bottom base and cheek-mounted trunnion bores."""

    def __init__(
        self,
        overall_size: Sequence[float],
        *,
        span_width: float,
        trunnion_diameter: float,
        trunnion_center_z: float,
        base_thickness: float,
        corner_radius: float = 0.0,
        center: bool = True,
    ):
        super().__init__()
        width = float(overall_size[0])
        depth = float(overall_size[1])
        height = float(overall_size[2])
        span_width = float(span_width)
        trunnion_diameter = float(trunnion_diameter)
        trunnion_center_z = float(trunnion_center_z)
        base_thickness = float(base_thickness)
        corner_radius = max(0.0, float(corner_radius))

        if width <= 0.0 or depth <= 0.0 or height <= 0.0:
            raise ValueError("overall_size values must be positive")
        if span_width <= 0.0 or span_width >= width:
            raise ValueError("span_width must be positive and less than overall_size[0]")
        cheek_thickness = 0.5 * (width - span_width)
        if cheek_thickness <= 1e-6:
            raise ValueError("span_width leaves no side wall material")
        if base_thickness <= 0.0 or base_thickness >= height:
            raise ValueError("base_thickness must be positive and less than overall_size[2]")
        if trunnion_diameter <= 0.0 or trunnion_diameter >= min(
            cheek_thickness * 2.0, depth, height
        ):
            raise ValueError("trunnion_diameter is too large for the yoke envelope")
        trunnion_radius = trunnion_diameter * 0.5
        if (
            trunnion_center_z - trunnion_radius <= base_thickness
            or trunnion_center_z + trunnion_radius >= height
        ):
            raise ValueError(
                "trunnion_center_z must leave material above the base and below the top edge"
            )

        base = (
            cq.Workplane("XY")
            .box(width, depth, base_thickness)
            .translate((0.0, 0.0, -height * 0.5 + base_thickness * 0.5))
        )
        cheek_height = height - base_thickness
        cheek_z = -height * 0.5 + base_thickness + cheek_height * 0.5
        left_cheek = (
            cq.Workplane("XY")
            .box(cheek_thickness, depth, cheek_height)
            .translate((-(span_width * 0.5 + cheek_thickness * 0.5), 0.0, cheek_z))
        )
        right_cheek = (
            cq.Workplane("XY")
            .box(cheek_thickness, depth, cheek_height)
            .translate(((span_width * 0.5 + cheek_thickness * 0.5), 0.0, cheek_z))
        )
        boss_radius = max(trunnion_radius * 1.4, cheek_thickness * 0.55)
        boss_length = min(cheek_thickness * 0.75, depth * 0.35)
        boss_z = -height * 0.5 + trunnion_center_z
        left_boss = (
            cq.Workplane("YZ")
            .circle(boss_radius)
            .extrude(boss_length, both=False)
            .translate((-(span_width * 0.5 + cheek_thickness), 0.0, boss_z))
        )
        right_boss = (
            cq.Workplane("YZ")
            .circle(boss_radius)
            .extrude(-boss_length, both=False)
            .translate(((span_width * 0.5 + cheek_thickness), 0.0, boss_z))
        )
        shape = base.union(left_cheek).union(right_cheek).union(left_boss).union(right_boss)
        if corner_radius > 0.0:
            shape = shape.edges("|Z").fillet(
                min(corner_radius, cheek_thickness * 0.5, depth * 0.2, height * 0.2)
            )

        trunnion_bore = (
            cq.Workplane("YZ")
            .circle(trunnion_radius)
            .extrude(
                width + boss_length * 2.0 + 0.01,
                both=True,
            )
            .translate((0.0, 0.0, boss_z))
        )
        shape = shape.cut(trunnion_bore)

        _brackets_hinges_bezels_finish(self, shape, center)

# ===== model =====
import math
import cadquery as cq
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """CadQuery cuboid with rounded vertical corners, centered locally."""
    sx, sy, sz = size
    return cq.Workplane("XY").box(sx, sy, sz).edges("|Z").fillet(radius)
def _body_shell() -> cq.Workplane:
    """Deep battery-housing body with a softly radiused professional shell."""
    body = cq.Workplane("XY").box(0.072, 0.078, 0.135).edges("|Z").fillet(0.008)
    # A very shallow rear control-panel recess keeps the body from reading as a
    # plain box while staying part of the molded shell.
    rear_boss = (
        cq.Workplane("XY")
        .box(0.058, 0.004, 0.070)
        .edges("|Z")
        .fillet(0.001)
        .translate((0.0, -0.041, 0.010))
    )
    return body.union(rear_boss).translate((0.0, 0.0, 0.0675))
def _head_shell() -> cq.Workplane:
    """Wide flash head: central block plus rounded side cheeks."""
    main = _rounded_box((0.098, 0.064, 0.048), 0.006)
    cheek_l = _rounded_box((0.020, 0.068, 0.052), 0.008).translate((-0.054, 0.0, 0.0))
    cheek_r = _rounded_box((0.020, 0.068, 0.052), 0.008).translate((0.054, 0.0, 0.0))
    return main.union(cheek_l).union(cheek_r)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_speedlight")

    matte_black = model.material("matte_black", rgba=(0.015, 0.014, 0.013, 1.0))
    satin_black = model.material("satin_black", rgba=(0.055, 0.052, 0.048, 1.0))
    dark_groove = model.material("dark_groove", rgba=(0.002, 0.002, 0.002, 1.0))
    warm_lens = model.material("warm_lens", rgba=(1.0, 0.88, 0.58, 0.58))
    glass = model.material("smoked_glass", rgba=(0.04, 0.06, 0.07, 0.72))
    metal = model.material("brushed_metal", rgba=(0.55, 0.55, 0.50, 1.0))
    red_window = model.material("red_window", rgba=(0.55, 0.03, 0.02, 0.82))

    body_w = 0.072
    body_d = 0.078
    body_h = 0.135
    side_x = body_w / 2.0

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell(), "body_shell", tolerance=0.0008),
        material=matte_black,
        name="body_shell",
    )

    # Professional flash foot and locking collar, connected to the molded body.
    body.visual(
        Box((0.050, 0.036, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, -0.003)),
        material=satin_black,
        name="locking_collar",
    )
    body.visual(
        Box((0.044, 0.030, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, -0.008)),
        material=metal,
        name="shoe_plate",
    )
    body.visual(
        Box((0.008, 0.030, 0.004)),
        origin=Origin(xyz=(-0.021, 0.0, -0.012)),
        material=metal,
        name="shoe_rail_0",
    )
    body.visual(
        Box((0.008, 0.030, 0.004)),
        origin=Origin(xyz=(0.021, 0.0, -0.012)),
        material=metal,
        name="shoe_rail_1",
    )

    # Fixed side seam/gasket showing the battery door's cut line in the body shell.
    hinge_y = -0.027
    door_width_y = 0.050
    door_center_y = hinge_y + door_width_y / 2.0
    door_center_z = 0.070
    door_height_z = 0.088
    for name, y in (("door_seam_rear", hinge_y), ("door_seam_front", hinge_y + door_width_y)):
        body.visual(
            Box((0.0008, 0.0012, door_height_z)),
            origin=Origin(xyz=(side_x + 0.0002, y, door_center_z)),
            material=dark_groove,
            name=name,
        )
    for name, z in (("door_seam_lower", door_center_z - door_height_z / 2.0), ("door_seam_upper", door_center_z + door_height_z / 2.0)):
        body.visual(
            Box((0.0008, door_width_y, 0.0012)),
            origin=Origin(xyz=(side_x + 0.0002, door_center_y, z)),
            material=dark_groove,
            name=name,
        )

    # Rear display and front assist window are surface treatments on the body, not moving controls.
    body.visual(
        Box((0.046, 0.006, 0.030)),
        origin=Origin(xyz=(0.0, -body_d / 2.0 - 0.005, 0.088)),
        material=glass,
        name="rear_display",
    )
    body.visual(
        Box((0.028, 0.002, 0.014)),
        origin=Origin(xyz=(0.0, body_d / 2.0 + 0.001, 0.047)),
        material=red_window,
        name="assist_window",
    )

    neck = model.part("neck")
    neck.visual(
        Cylinder(radius=0.032, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=satin_black,
        name="swivel_collar",
    )
    neck.visual(
        Box((0.030, 0.028, 0.040)),
        origin=Origin(xyz=(0.0, 0.0, 0.028)),
        material=matte_black,
        name="neck_column",
    )
    yoke = TrunnionYokeGeometry(
        (0.086, 0.040, 0.062),
        span_width=0.054,
        trunnion_diameter=0.018,
        trunnion_center_z=0.046,
        base_thickness=0.014,
        corner_radius=0.004,
        center=False,
    )
    neck.visual(
        mesh_from_geometry(yoke, "head_yoke"),
        origin=Origin(xyz=(0.0, 0.0, 0.026)),
        material=satin_black,
        name="head_yoke",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shell(), "flash_shell", tolerance=0.0007),
        origin=Origin(xyz=(0.0, 0.025, 0.044)),
        material=satin_black,
        name="flash_shell",
    )
    head.visual(
        Box((0.086, 0.006, 0.030)),
        origin=Origin(xyz=(0.0, 0.059, 0.046)),
        material=warm_lens,
        name="flash_lens",
    )
    head.visual(
        Box((0.042, 0.024, 0.020)),
        origin=Origin(xyz=(0.0, 0.008, 0.012)),
        material=satin_black,
        name="tilt_saddle",
    )
    head.visual(
        Cylinder(radius=0.0088, length=0.092),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="tilt_pin",
    )
    head.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(-0.050, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=satin_black,
        name="side_cheek_0",
    )
    head.visual(
        Cylinder(radius=0.010, length=0.014),
        origin=Origin(xyz=(0.050, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=satin_black,
        name="side_cheek_1",
    )

    door = model.part("battery_door")
    door.visual(
        Box((0.003, door_width_y, door_height_z)),
        origin=Origin(xyz=(-0.0015, door_width_y / 2.0, 0.0)),
        material=satin_black,
        name="door_panel",
    )
    door.visual(
        Box((0.0010, door_width_y - 0.008, door_height_z - 0.010)),
        origin=Origin(xyz=(0.0004, door_width_y / 2.0, 0.0)),
        material=dark_groove,
        name="door_recess",
    )
    for idx, z in enumerate((-0.030, 0.0, 0.030)):
        door.visual(
            Cylinder(radius=0.0030, length=0.018),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=satin_black,
            name=f"hinge_knuckle_{idx}",
        )

    model.articulation(
        "body_to_neck",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=neck,
        origin=Origin(xyz=(0.0, 0.0, body_h)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=4.0, velocity=4.0),
    )
    model.articulation(
        "neck_to_head",
        ArticulationType.REVOLUTE,
        parent=neck,
        child=head,
        origin=Origin(xyz=(0.0, 0.0, 0.072)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.25, upper=1.75),
    )
    model.articulation(
        "body_to_battery_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(side_x + 0.0035, hinge_y, door_center_z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=0.8, velocity=3.0, lower=0.0, upper=1.45),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
