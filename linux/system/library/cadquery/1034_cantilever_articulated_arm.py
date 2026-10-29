# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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

# ===== model =====
from math import pi
import cadquery as cq
BASE_LENGTH = 0.34
BASE_WIDTH = 0.28
BASE_THICKNESS = 0.02
PEDESTAL_X = -0.055
PEDESTAL_LENGTH = 0.12
PEDESTAL_WIDTH = 0.09
PEDESTAL_HEIGHT = 0.34
SHOULDER_AXIS_Z = 0.455
SHOULDER_LINK_LENGTH = 0.36
FORELINK_LENGTH = 0.34
def _y_cylinder(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .translate(center)
    )
def _box(
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    fillet_axis: str | None = None,
    fillet_radius: float = 0.0,
) -> cq.Workplane:
    solid = cq.Workplane("XY").box(*size)
    if fillet_axis is not None and fillet_radius > 0.0:
        solid = solid.edges(f"|{fillet_axis.upper()}").fillet(fillet_radius)
    return solid.translate(center)
def _base_shape() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS)
        .edges("|Z")
        .fillet(0.028)
        .translate((0.0, 0.0, BASE_THICKNESS / 2.0))
    )
    for x_pos in (-0.115, 0.115):
        for y_pos in (-0.085, 0.085):
            plate = plate.cut(
                cq.Workplane("XY")
                .circle(0.0105)
                .extrude(BASE_THICKNESS + 0.004)
                .translate((x_pos, y_pos, -0.002))
            )

    pedestal = _box(
        (PEDESTAL_LENGTH, PEDESTAL_WIDTH, PEDESTAL_HEIGHT),
        (PEDESTAL_X, 0.0, BASE_THICKNESS + PEDESTAL_HEIGHT / 2.0),
        fillet_axis="Z",
        fillet_radius=0.010,
    )
    shoulder_head = _box(
        (0.105, 0.105, 0.058),
        (-0.062, 0.0, 0.398),
        fillet_axis="Y",
        fillet_radius=0.008,
    )
    front_gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.104, 0.228),
                (-0.016, 0.390),
                (-0.016, 0.428),
                (-0.104, 0.312),
            ]
        )
        .close()
        .extrude(PEDESTAL_WIDTH / 2.0, both=True)
    )

    ear_gap = 0.046
    ear_thickness = 0.014
    ear_y = ear_gap / 2.0 + ear_thickness / 2.0
    ear_height = 0.072
    ear_length = 0.060
    ear_cap_radius = 0.024

    ear_left = _box(
        (ear_length, ear_thickness, ear_height),
        (0.0, ear_y, SHOULDER_AXIS_Z - 0.010),
    ).union(_y_cylinder(ear_cap_radius, ear_thickness, (0.0, ear_y, SHOULDER_AXIS_Z)))
    ear_right = _box(
        (ear_length, ear_thickness, ear_height),
        (0.0, -ear_y, SHOULDER_AXIS_Z - 0.010),
    ).union(_y_cylinder(ear_cap_radius, ear_thickness, (0.0, -ear_y, SHOULDER_AXIS_Z)))

    return (
        plate.union(pedestal)
        .union(shoulder_head)
        .union(front_gusset)
        .union(ear_left)
        .union(ear_right)
    )
def _shoulder_link_shape() -> cq.Workplane:
    barrel = _y_cylinder(0.019, 0.046, (0.0, 0.0, 0.0))
    neck = _box((0.082, 0.038, 0.110), (0.041, 0.0, -0.004), fillet_axis="X", fillet_radius=0.008)
    main_body = _box((0.252, 0.070, 0.155), (0.186, 0.0, -0.004), fillet_axis="X", fillet_radius=0.012)
    distal_root = _box((0.050, 0.050, 0.100), (0.315, 0.0, 0.0), fillet_axis="X", fillet_radius=0.006)

    ear_gap = 0.038
    ear_thickness = 0.012
    ear_y = ear_gap / 2.0 + ear_thickness / 2.0
    ear_block = (0.040, ear_thickness, 0.072)
    elbow_x = SHOULDER_LINK_LENGTH

    ear_left = _box(ear_block, (0.340, ear_y, 0.0)).union(
        _y_cylinder(0.020, ear_thickness, (elbow_x, ear_y, 0.0))
    )
    ear_right = _box(ear_block, (0.340, -ear_y, 0.0)).union(
        _y_cylinder(0.020, ear_thickness, (elbow_x, -ear_y, 0.0))
    )

    return barrel.union(neck).union(main_body).union(distal_root).union(ear_left).union(ear_right)
def _forelink_shape() -> cq.Workplane:
    barrel = _y_cylinder(0.016, 0.038, (0.0, 0.0, 0.0))
    neck = _box((0.066, 0.030, 0.085), (0.033, 0.0, 0.0), fillet_axis="X", fillet_radius=0.006)
    main_body = _box((0.232, 0.052, 0.100), (0.176, 0.0, 0.0), fillet_axis="X", fillet_radius=0.010)
    distal_root = _box((0.045, 0.040, 0.076), (0.300, 0.0, 0.0), fillet_axis="X", fillet_radius=0.005)

    ear_gap = 0.034
    ear_thickness = 0.010
    ear_y = ear_gap / 2.0 + ear_thickness / 2.0
    wrist_x = FORELINK_LENGTH

    ear_left = _box((0.035, ear_thickness, 0.058), (0.3225, ear_y, 0.0)).union(
        _y_cylinder(0.016, ear_thickness, (wrist_x, ear_y, 0.0))
    )
    ear_right = _box((0.035, ear_thickness, 0.058), (0.3225, -ear_y, 0.0)).union(
        _y_cylinder(0.016, ear_thickness, (wrist_x, -ear_y, 0.0))
    )

    return barrel.union(neck).union(main_body).union(distal_root).union(ear_left).union(ear_right)
def _wrist_block_shape() -> cq.Workplane:
    barrel = _y_cylinder(0.013, 0.034, (0.0, 0.0, 0.0))
    neck = _box((0.040, 0.026, 0.060), (0.020, 0.0, 0.0), fillet_axis="X", fillet_radius=0.004)
    block = _box((0.092, 0.080, 0.078), (0.074, 0.0, 0.0), fillet_axis="X", fillet_radius=0.010)
    face_plate = _box((0.018, 0.092, 0.086), (0.129, 0.0, 0.0), fillet_axis="Y", fillet_radius=0.005)
    top_cap = _box((0.050, 0.060, 0.016), (0.090, 0.0, 0.039))
    return barrel.union(neck).union(block).union(face_plate).union(top_cap)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pedestal_inspection_arm")

    model.material("powder_charcoal", rgba=(0.18, 0.20, 0.22, 1.0))
    model.material("cast_aluminum", rgba=(0.67, 0.70, 0.73, 1.0))
    model.material("graphite", rgba=(0.30, 0.32, 0.35, 1.0))

    base = model.part("pedestal_base")
    base.visual(
        mesh_from_cadquery(_base_shape(), "pedestal_base"),
        material="powder_charcoal",
        name="base_shell",
    )
    base.inertial = Inertial.from_geometry(
        Box((0.20, 0.16, 0.46)),
        mass=28.0,
        origin=Origin(xyz=(-0.030, 0.0, 0.23)),
    )

    shoulder_link = model.part("shoulder_link")
    shoulder_link.visual(
        mesh_from_cadquery(_shoulder_link_shape(), "shoulder_link"),
        material="cast_aluminum",
        name="shoulder_shell",
    )
    shoulder_link.inertial = Inertial.from_geometry(
        Box((0.38, 0.07, 0.17)),
        mass=8.5,
        origin=Origin(xyz=(0.19, 0.0, 0.0)),
    )

    forelink = model.part("forelink")
    forelink.visual(
        mesh_from_cadquery(_forelink_shape(), "forelink"),
        material="cast_aluminum",
        name="forelink_shell",
    )
    forelink.inertial = Inertial.from_geometry(
        Box((0.35, 0.052, 0.10)),
        mass=4.6,
        origin=Origin(xyz=(0.175, 0.0, 0.0)),
    )

    wrist_block = model.part("wrist_block")
    wrist_block.visual(
        mesh_from_cadquery(_wrist_block_shape(), "wrist_block"),
        material="graphite",
        name="wrist_shell",
    )
    wrist_block.inertial = Inertial.from_geometry(
        Box((0.15, 0.092, 0.086)),
        mass=1.8,
        origin=Origin(xyz=(0.075, 0.0, 0.0)),
    )

    model.articulation(
        "base_to_shoulder",
        ArticulationType.REVOLUTE,
        parent=base,
        child=shoulder_link,
        origin=Origin(xyz=(0.0, 0.0, SHOULDER_AXIS_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.55, upper=1.20, effort=80.0, velocity=1.0),
    )
    model.articulation(
        "shoulder_to_forelink",
        ArticulationType.REVOLUTE,
        parent=shoulder_link,
        child=forelink,
        origin=Origin(xyz=(SHOULDER_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.30, upper=1.35, effort=55.0, velocity=1.3),
    )
    model.articulation(
        "forelink_to_wrist",
        ArticulationType.REVOLUTE,
        parent=forelink,
        child=wrist_block,
        origin=Origin(xyz=(FORELINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.10, upper=1.15, effort=22.0, velocity=1.8),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
