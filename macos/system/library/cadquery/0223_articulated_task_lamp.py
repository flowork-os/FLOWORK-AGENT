# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

from __future__ import annotations

import cadquery as cq
import math

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
from math import cos, pi, sin
ARM_WIDTH = 0.084
SIDE_Y = ARM_WIDTH / 2.0
LOWER_LEN = 0.36
FOREARM_LEN = 0.33
def _shade_shell_mesh(
    *,
    start_x: float = 0.052,
    length: float = 0.180,
    radius: float = 0.055,
    wall: float = 0.006,
    center_z: float = -0.055,
    segments: int = 56,
) -> MeshGeometry:
    """Thin open cylindrical lampshade, with its cylinder axis along local +X."""

    inner_radius = radius - wall
    end_x = start_x + length
    geom = MeshGeometry()

    def add_ring(x: float, r: float) -> list[int]:
        ids: list[int] = []
        for i in range(segments):
            a = 2.0 * pi * i / segments
            ids.append(geom.add_vertex(x, r * cos(a), center_z + r * sin(a)))
        return ids

    outer_back = add_ring(start_x, radius)
    outer_front = add_ring(end_x, radius)
    inner_back = add_ring(start_x, inner_radius)
    inner_front = add_ring(end_x, inner_radius)

    def quad(a: int, b: int, c: int, d: int) -> None:
        geom.add_face(a, b, c)
        geom.add_face(a, c, d)

    for i in range(segments):
        j = (i + 1) % segments
        # outside, inside, front lip, and rear lip; front and rear remain open.
        quad(outer_back[i], outer_back[j], outer_front[j], outer_front[i])
        quad(inner_front[i], inner_front[j], inner_back[j], inner_back[i])
        quad(outer_front[i], outer_front[j], inner_front[j], inner_front[i])
        quad(inner_back[i], inner_back[j], outer_back[j], outer_back[i])

    return geom
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_mounted_task_lamp")

    model.material("matte_black", rgba=(0.025, 0.026, 0.028, 1.0))
    model.material("brushed_steel", rgba=(0.58, 0.60, 0.62, 1.0))
    model.material("dark_rubber", rgba=(0.010, 0.010, 0.012, 1.0))
    model.material("warm_light", rgba=(1.00, 0.78, 0.35, 0.90))
    model.material("soft_white", rgba=(0.96, 0.93, 0.84, 1.0))

    # The root frame is the shoulder hinge line.  The wall plate sits just
    # behind it on the -X side, so the arm clearly grows out from a wall mount.
    wall_mount = model.part("wall_mount")
    wall_mount.visual(
        Box((0.030, 0.180, 0.320)),
        origin=Origin(xyz=(-0.060, 0.0, 0.0)),
        material="matte_black",
        name="wall_plate",
    )
    wall_mount.visual(
        Box((0.045, 0.040, 0.050)),
        origin=Origin(xyz=(-0.0375, 0.0, 0.0)),
        material="matte_black",
        name="shoulder_standoff",
    )
    wall_mount.visual(
        Cylinder(radius=0.029, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="brushed_steel",
        name="shoulder_barrel",
    )
    # Four proud screw pads are slightly sunk into the plate face so they read
    # as mounted hardware rather than floating dots.
    for yi in (-0.055, 0.055):
        for zi in (-0.110, 0.110):
            wall_mount.visual(
                Cylinder(radius=0.012, length=0.006),
                origin=Origin(xyz=(-0.043, yi, zi), rpy=(0.0, pi / 2.0, 0.0)),
                material="brushed_steel",
                name=f"screw_{'p' if yi > 0 else 'n'}_{'p' if zi > 0 else 'n'}",
            )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        Cylinder(radius=0.010, length=0.105),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="dark_rubber",
        name="shoulder_pin",
    )
    for ear_name, bar_name, tab_name, y in (
        ("shoulder_ear_0", "side_bar_0", "shoulder_tab_0", -SIDE_Y),
        ("shoulder_ear_1", "side_bar_1", "shoulder_tab_1", SIDE_Y),
    ):
        lower_arm.visual(
            Cylinder(radius=0.022, length=0.018),
            origin=Origin(xyz=(0.0, y, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
            material="brushed_steel",
            name=ear_name,
        )
        lower_arm.visual(
            Box((0.320, 0.012, 0.018)),
            origin=Origin(xyz=(0.180, y, 0.0)),
            material="brushed_steel",
            name=bar_name,
        )
        lower_arm.visual(
            Box((0.050, 0.014, 0.016)),
            origin=Origin(xyz=(0.032, y, 0.0)),
            material="brushed_steel",
            name=tab_name,
        )
    lower_arm.visual(
        Box((0.018, 0.096, 0.016)),
        origin=Origin(xyz=(0.075, 0.0, 0.0)),
        material="brushed_steel",
        name="shoulder_bridge",
    )
    lower_arm.visual(
        Box((0.030, 0.096, 0.016)),
        origin=Origin(xyz=(LOWER_LEN - 0.040, 0.0, 0.0)),
        material="brushed_steel",
        name="elbow_bridge",
    )
    lower_arm.visual(
        Cylinder(radius=0.025, length=0.038),
        origin=Origin(xyz=(LOWER_LEN, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="brushed_steel",
        name="elbow_barrel",
    )

    forearm = model.part("forearm")
    forearm.visual(
        Cylinder(radius=0.010, length=0.105),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="dark_rubber",
        name="elbow_pin",
    )
    for ear_name, bar_name, tab_name, yoke_name, shade_tab_name, y in (
        ("elbow_ear_0", "side_bar_0", "elbow_tab_0", "shade_yoke_0", "shade_tab_0", -SIDE_Y),
        ("elbow_ear_1", "side_bar_1", "elbow_tab_1", "shade_yoke_1", "shade_tab_1", SIDE_Y),
    ):
        forearm.visual(
            Cylinder(radius=0.022, length=0.018),
            origin=Origin(xyz=(0.0, y, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
            material="brushed_steel",
            name=ear_name,
        )
        forearm.visual(
            Box((0.292, 0.012, 0.016)),
            origin=Origin(xyz=(0.165, y, 0.0)),
            material="brushed_steel",
            name=bar_name,
        )
        forearm.visual(
            Box((0.048, 0.014, 0.016)),
            origin=Origin(xyz=(0.030, y, 0.0)),
            material="brushed_steel",
            name=tab_name,
        )
        forearm.visual(
            Cylinder(radius=0.019, length=0.018),
            origin=Origin(xyz=(FOREARM_LEN, y, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
            material="brushed_steel",
            name=yoke_name,
        )
        forearm.visual(
            Box((0.070, 0.014, 0.0133)),
            origin=Origin(xyz=(FOREARM_LEN - 0.030, y, -0.02535)),
            material="brushed_steel",
            name=shade_tab_name,
        )
    forearm.visual(
        Box((0.018, 0.096, 0.014)),
        origin=Origin(xyz=(0.075, 0.0, 0.0)),
        material="brushed_steel",
        name="elbow_bridge",
    )
    forearm.visual(
        Box((0.018, 0.096, 0.014)),
        origin=Origin(xyz=(FOREARM_LEN - 0.080, 0.0, 0.0)),
        material="brushed_steel",
        name="tip_bridge",
    )

    shade = model.part("shade")
    shade.visual(
        mesh_from_geometry(_shade_shell_mesh(), "shade_shell"),
        material="matte_black",
        name="shade_shell",
    )
    shade.visual(
        Cylinder(radius=0.018, length=0.105),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material="brushed_steel",
        name="shade_barrel",
    )
    shade.visual(
        Box((0.060, 0.026, 0.036)),
        origin=Origin(xyz=(0.044, 0.0, -0.020)),
        material="matte_black",
        name="shade_neck",
    )
    shade.visual(
        Cylinder(radius=0.018, length=0.060),
        origin=Origin(xyz=(0.092, 0.0, -0.055), rpy=(0.0, pi / 2.0, 0.0)),
        material="soft_white",
        name="socket",
    )
    shade.visual(
        Sphere(radius=0.026),
        origin=Origin(xyz=(0.148, 0.0, -0.055)),
        material="warm_light",
        name="bulb",
    )

    model.articulation(
        "shoulder_hinge",
        ArticulationType.REVOLUTE,
        parent=wall_mount,
        child=lower_arm,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.70, upper=1.05, effort=18.0, velocity=1.4),
    )
    model.articulation(
        "elbow_hinge",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=forearm,
        origin=Origin(xyz=(LOWER_LEN, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.45, upper=1.45, effort=12.0, velocity=1.6),
    )
    model.articulation(
        "shade_swivel",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=shade,
        origin=Origin(xyz=(FOREARM_LEN, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.20, upper=1.20, effort=4.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
