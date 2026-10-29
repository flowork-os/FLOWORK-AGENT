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
from math import radians
import cadquery as cq
PLATE_RADIUS = 0.055
PLATE_THICKNESS = 0.010
WALL_HUB_RADIUS = 0.018
WALL_HUB_LENGTH = 0.022
SHOULDER_X = 0.028
LOWER_ARM_LENGTH = 0.140
UPPER_ARM_LENGTH = 0.205
LOWER_TONGUE_LENGTH = 0.018
LOWER_TONGUE_WIDTH = 0.007
LOWER_TONGUE_HEIGHT = 0.018
LOWER_BODY_START = 0.012
LOWER_BODY_WIDTH = 0.016
LOWER_BODY_HEIGHT = 0.012
LOWER_YOKE_LENGTH = 0.018
LOWER_YOKE_GAP = 0.010
LOWER_YOKE_EAR = 0.005
LOWER_YOKE_HEIGHT = 0.024
UPPER_TONGUE_LENGTH = 0.018
UPPER_TONGUE_WIDTH = 0.007
UPPER_TONGUE_HEIGHT = 0.016
UPPER_BODY_START = 0.012
UPPER_BODY_WIDTH = 0.014
UPPER_BODY_HEIGHT = 0.010
UPPER_YOKE_LENGTH = 0.016
UPPER_YOKE_GAP = 0.008
UPPER_YOKE_EAR = 0.005
UPPER_YOKE_HEIGHT = 0.020
SHADE_TAB_LENGTH = 0.015
SHADE_TAB_WIDTH = 0.006
SHADE_TAB_HEIGHT = 0.016
SHADE_DROP = -0.018
SHADE_BRACKET_START = 0.012
SHADE_BRACKET_LENGTH = 0.030
SHADE_BRACKET_WIDTH = 0.012
SHADE_BRACKET_HEIGHT = 0.014
SHADE_COLLAR_START = 0.016
SHADE_COLLAR_LENGTH = 0.024
SHADE_COLLAR_RADIUS = 0.019
SHADE_SHELL_START = 0.028
SHADE_SHELL_LENGTH = 0.098
SHADE_REAR_RADIUS = 0.025
SHADE_FRONT_RADIUS = 0.055
SHADE_WALL = 0.0022
def _y_axis_knuckle(*, x_center: float, radius: float, width: float, z_center: float = 0.0):
    return (
        cq.Workplane("XZ")
        .circle(radius)
        .extrude(width)
        .translate((x_center, -width / 2.0, z_center))
    )
def _wall_plate_shape():
    shape = cq.Workplane("YZ").circle(PLATE_RADIUS).extrude(PLATE_THICKNESS)
    shape = shape.union(cq.Workplane("YZ").circle(WALL_HUB_RADIUS).extrude(WALL_HUB_LENGTH))

    return shape
def _yoke_ear(*, x_center: float, y_center: float, length: float, thickness: float, height: float):
    return (
        cq.Workplane("XY")
        .box(length, thickness, height, centered=(True, True, True))
        .translate((x_center, y_center, 0.0))
    )
def _wall_plate_ears():
    yoke_offset = (LOWER_YOKE_GAP / 2.0) + (LOWER_YOKE_EAR / 2.0)
    return [
        _yoke_ear(
            x_center=SHOULDER_X,
            y_center=sign * yoke_offset,
            length=LOWER_YOKE_LENGTH,
            thickness=LOWER_YOKE_EAR,
            height=LOWER_YOKE_HEIGHT,
        )
        for sign in (-1.0, 1.0)
    ]
def _lower_arm_shape():

    tongue = cq.Workplane("XY").box(
        LOWER_TONGUE_LENGTH,
        LOWER_TONGUE_WIDTH,
        LOWER_TONGUE_HEIGHT,
        centered=(False, True, True),
    )
    body = (
        cq.Workplane("XY")
        .box(
            LOWER_ARM_LENGTH - LOWER_BODY_START,
            LOWER_BODY_WIDTH,
            LOWER_BODY_HEIGHT,
            centered=(False, True, True),
        )
        .translate((LOWER_BODY_START, 0.0, 0.0))
    )
    knuckle = _y_axis_knuckle(
        x_center=0.007,
        radius=0.009,
        width=LOWER_TONGUE_WIDTH,
    )

    return tongue.union(body).union(knuckle)
def _lower_arm_ears():
    yoke_offset = (LOWER_YOKE_GAP / 2.0) + (LOWER_YOKE_EAR / 2.0)
    return [
        _yoke_ear(
            x_center=LOWER_ARM_LENGTH + 0.002,
            y_center=sign * yoke_offset,
            length=LOWER_YOKE_LENGTH,
            thickness=LOWER_YOKE_EAR,
            height=LOWER_YOKE_HEIGHT,
        )
        for sign in (-1.0, 1.0)
    ]
def _upper_arm_shape():
    tongue = cq.Workplane("XY").box(
        UPPER_TONGUE_LENGTH,
        UPPER_TONGUE_WIDTH,
        UPPER_TONGUE_HEIGHT,
        centered=(False, True, True),
    )
    body = (
        cq.Workplane("XY")
        .box(
            UPPER_ARM_LENGTH - UPPER_BODY_START,
            UPPER_BODY_WIDTH,
            UPPER_BODY_HEIGHT,
            centered=(False, True, True),
        )
        .translate((UPPER_BODY_START, 0.0, 0.0))
    )
    knuckle = _y_axis_knuckle(
        x_center=0.007,
        radius=0.008,
        width=UPPER_TONGUE_WIDTH,
    )

    return tongue.union(body).union(knuckle)
def _upper_arm_ears():
    yoke_offset = (UPPER_YOKE_GAP / 2.0) + (UPPER_YOKE_EAR / 2.0)
    return [
        _yoke_ear(
            x_center=UPPER_ARM_LENGTH + 0.002,
            y_center=sign * yoke_offset,
            length=UPPER_YOKE_LENGTH,
            thickness=UPPER_YOKE_EAR,
            height=UPPER_YOKE_HEIGHT,
        )
        for sign in (-1.0, 1.0)
    ]
def _shade_bracket_shape():
    tab = cq.Workplane("XY").box(
        SHADE_TAB_LENGTH,
        SHADE_TAB_WIDTH,
        SHADE_TAB_HEIGHT,
        centered=(False, True, True),
    )
    knuckle = _y_axis_knuckle(
        x_center=0.006,
        radius=0.008,
        width=SHADE_TAB_WIDTH,
    )
    bridge = (
        cq.Workplane("XY")
        .box(
            SHADE_BRACKET_LENGTH,
            SHADE_BRACKET_WIDTH,
            SHADE_BRACKET_HEIGHT,
            centered=(False, True, True),
        )
        .translate((SHADE_BRACKET_START, 0.0, -0.010))
    )
    collar = (
        cq.Workplane("YZ")
        .circle(SHADE_COLLAR_RADIUS)
        .extrude(SHADE_COLLAR_LENGTH)
        .translate((SHADE_COLLAR_START, 0.0, SHADE_DROP))
    )

    return tab.union(knuckle).union(bridge).union(collar)
def _shade_shell_shape():
    outer = (
        cq.Workplane("YZ")
        .circle(SHADE_REAR_RADIUS)
        .workplane(offset=SHADE_SHELL_LENGTH)
        .circle(SHADE_FRONT_RADIUS)
        .loft()
        .translate((SHADE_SHELL_START, 0.0, SHADE_DROP))
    )
    inner = (
        cq.Workplane("YZ")
        .circle(SHADE_REAR_RADIUS - (SHADE_WALL * 1.6))
        .workplane(offset=SHADE_SHELL_LENGTH + 0.003)
        .circle(SHADE_FRONT_RADIUS - SHADE_WALL)
        .loft()
        .translate((SHADE_SHELL_START + 0.012, 0.0, SHADE_DROP))
    )
    lip = (
        cq.Workplane("YZ")
        .circle(SHADE_FRONT_RADIUS + 0.002)
        .circle(SHADE_FRONT_RADIUS - 0.001)
        .extrude(0.004)
        .translate((SHADE_SHELL_START + SHADE_SHELL_LENGTH - 0.004, 0.0, SHADE_DROP))
    )

    return outer.cut(inner).union(lip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_task_lamp")

    model.material("graphite", rgba=(0.16, 0.16, 0.18, 1.0))
    model.material("shade_cream", rgba=(0.91, 0.89, 0.82, 1.0))

    wall_plate = model.part("wall_plate")
    wall_plate.visual(
        mesh_from_cadquery(_wall_plate_shape(), "wall_plate"),
        material="graphite",
        name="plate_body",
    )
    for index, ear in enumerate(_wall_plate_ears()):
        wall_plate.visual(
            mesh_from_cadquery(ear, f"wall_plate_ear_{index}"),
            material="graphite",
            name=f"plate_ear_{index}",
        )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        mesh_from_cadquery(_lower_arm_shape(), "lower_arm"),
        material="graphite",
        name="lower_link",
    )
    for index, ear in enumerate(_lower_arm_ears()):
        lower_arm.visual(
            mesh_from_cadquery(ear, f"lower_arm_ear_{index}"),
            material="graphite",
            name=f"lower_ear_{index}",
        )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(_upper_arm_shape(), "upper_arm"),
        material="graphite",
        name="upper_link",
    )
    for index, ear in enumerate(_upper_arm_ears()):
        upper_arm.visual(
            mesh_from_cadquery(ear, f"upper_arm_ear_{index}"),
            material="graphite",
            name=f"upper_ear_{index}",
        )

    shade = model.part("shade")
    shade.visual(
        mesh_from_cadquery(_shade_bracket_shape(), "shade_bracket"),
        material="graphite",
        name="shade_bracket",
    )
    shade.visual(
        mesh_from_cadquery(_shade_shell_shape(), "bell_shade"),
        material="shade_cream",
        name="bell_shell",
    )

    model.articulation(
        "wall_plate_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=wall_plate,
        child=lower_arm,
        origin=Origin(xyz=(SHOULDER_X, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=radians(-45.0),
            upper=radians(80.0),
            effort=16.0,
            velocity=1.5,
        ),
    )
    model.articulation(
        "lower_arm_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=(LOWER_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=radians(-75.0),
            upper=radians(95.0),
            effort=12.0,
            velocity=1.7,
        ),
    )
    model.articulation(
        "upper_arm_to_shade",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=shade,
        origin=Origin(xyz=(UPPER_ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=radians(-55.0),
            upper=radians(40.0),
            effort=8.0,
            velocity=2.2,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
