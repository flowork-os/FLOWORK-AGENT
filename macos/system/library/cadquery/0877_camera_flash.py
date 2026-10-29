# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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
import math
import cadquery as cq
BODY_DEPTH = 0.052
BODY_WIDTH = 0.070
LOWER_BODY_HEIGHT = 0.094
UPPER_BODY_HEIGHT = 0.022
BODY_BASE_Z = 0.012
BODY_TOP_Z = BODY_BASE_Z + LOWER_BODY_HEIGHT + UPPER_BODY_HEIGHT
SWIVEL_PLINTH_HEIGHT = 0.006
SWIVEL_Z = BODY_TOP_Z + SWIVEL_PLINTH_HEIGHT
HEAD_WIDTH = 0.084
HEAD_DEPTH = 0.050
HEAD_HEIGHT = 0.046
def _y_cylinder(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XZ", origin=center).circle(radius).extrude(length / 2.0, both=True)
def _x_cylinder(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("YZ", origin=center).circle(radius).extrude(length / 2.0, both=True)
def _z_cylinder(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY", origin=center).circle(radius).extrude(length / 2.0, both=True)
def _body_shell_shape() -> cq.Workplane:
    lower_outer = (
        cq.Workplane("XY")
        .box(BODY_DEPTH, BODY_WIDTH, LOWER_BODY_HEIGHT)
        .edges("|Z")
        .fillet(0.006)
        .translate((0.0, 0.0, BODY_BASE_Z + LOWER_BODY_HEIGHT / 2.0))
    )
    upper_outer = (
        cq.Workplane("XY")
        .box(0.046, 0.062, UPPER_BODY_HEIGHT)
        .edges("|Z")
        .fillet(0.004)
        .translate((0.0, 0.0, BODY_BASE_Z + LOWER_BODY_HEIGHT + UPPER_BODY_HEIGHT / 2.0))
    )
    swivel_plinth = (
        cq.Workplane("XY")
        .box(0.032, 0.024, SWIVEL_PLINTH_HEIGHT)
        .edges("|Z")
        .fillet(0.002)
        .translate((0.0, 0.0, BODY_TOP_Z + SWIVEL_PLINTH_HEIGHT / 2.0))
    )

    shell = lower_outer.union(upper_outer).union(swivel_plinth)

    inner_cavity = cq.Workplane("XY").box(0.042, 0.060, 0.092).translate((0.0, 0.0, 0.068))
    door_opening = cq.Workplane("XY").box(0.042, 0.020, 0.086).translate((0.0, 0.029, 0.068))

    return shell.cut(inner_cavity).cut(door_opening)
def _body_hinge_shape() -> cq.Workplane:
    hinge_x = -0.020
    hinge_y = BODY_WIDTH / 2.0 - 0.0015
    upper_knuckle = _z_cylinder(0.0024, 0.020, (hinge_x, hinge_y, 0.097))
    lower_knuckle = _z_cylinder(0.0024, 0.020, (hinge_x, hinge_y, 0.039))
    return upper_knuckle.union(lower_knuckle)
def _neck_base_shape() -> cq.Workplane:
    hinge_z = 0.046

    collar = cq.Workplane("XY").circle(0.016).extrude(0.008)
    column = cq.Workplane("XY").box(0.022, 0.018, 0.026).translate((0.0, 0.0, 0.019))
    bridge = cq.Workplane("XY").box(0.010, 0.100, 0.010).translate((-0.008, 0.0, 0.021))
    return collar.union(column).union(bridge)
def _neck_arm_shape(sign: float) -> cq.Workplane:
    arm_y = sign * 0.048
    hinge_z = 0.046
    arm = cq.Workplane("XY").box(0.014, 0.006, 0.038).translate((-0.003, arm_y, 0.032))
    boss = _y_cylinder(0.007, 0.008, (0.0, arm_y, hinge_z))
    bore = _y_cylinder(0.0052, 0.012, (0.0, arm_y, hinge_z))
    return arm.union(boss).cut(bore)
def _head_shell_shape() -> cq.Workplane:
    shell = (
        cq.Workplane("XY")
        .box(HEAD_DEPTH, HEAD_WIDTH, HEAD_HEIGHT)
        .edges("|Z")
        .fillet(0.006)
        .translate((0.027, 0.0, 0.030))
    )
    front_recess = cq.Workplane("XY").box(0.014, 0.070, 0.030).translate((0.047, 0.0, 0.030))
    shell = shell.cut(front_recess)
    left_cheek = _x_cylinder(0.009, 0.034, (0.024, 0.032, 0.030))
    right_cheek = _x_cylinder(0.009, 0.034, (0.024, -0.032, 0.030))
    shell = shell.union(left_cheek).union(right_cheek)
    left_lug = cq.Workplane("XY").box(0.010, 0.004, 0.014).translate((0.005, 0.040, 0.004))
    right_lug = cq.Workplane("XY").box(0.010, 0.004, 0.014).translate((0.005, -0.040, 0.004))
    shell = shell.union(left_lug).union(right_lug)

    trunnion_offset_y = HEAD_WIDTH / 2.0 + 0.005
    left_trunnion = _y_cylinder(0.0052, 0.010, (0.0, trunnion_offset_y, 0.0))
    right_trunnion = _y_cylinder(0.0052, 0.010, (0.0, -trunnion_offset_y, 0.0))

    return shell.union(left_trunnion).union(right_trunnion)
def _battery_door_hardware_shape() -> cq.Workplane:
    hinge_barrel = _z_cylinder(0.0022, 0.028, (0.0, 0.0, 0.0))
    hinge_web = cq.Workplane("XY").box(0.004, 0.003, 0.030).translate((0.002, 0.0, 0.0))
    return hinge_barrel.union(hinge_web)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="speedlight")

    body_black = model.material("body_black", color=(0.12, 0.12, 0.13))
    trim_dark = model.material("trim_dark", color=(0.18, 0.18, 0.20))
    diffuser_white = model.material("diffuser_white", color=(0.92, 0.92, 0.88))

    body = model.part("body")
    body.visual(mesh_from_cadquery(_body_shell_shape(), "body_shell"), material=body_black, name="body_shell")
    body.visual(mesh_from_cadquery(_body_hinge_shape(), "body_hinge"), material=trim_dark, name="door_hinge")
    body.visual(
        Box((0.030, 0.026, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, 0.008)),
        material=trim_dark,
        name="shoe_mount",
    )
    body.visual(
        Box((0.022, 0.018, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=trim_dark,
        name="shoe_foot",
    )

    neck = model.part("neck")
    neck.visual(mesh_from_cadquery(_neck_base_shape(), "neck_base"), material=body_black, name="neck_base")
    neck.visual(mesh_from_cadquery(_neck_arm_shape(1.0), "neck_arm_0"), material=body_black, name="arm_0")
    neck.visual(mesh_from_cadquery(_neck_arm_shape(-1.0), "neck_arm_1"), material=body_black, name="arm_1")

    head = model.part("head")
    head.visual(mesh_from_cadquery(_head_shell_shape(), "head_shell"), material=body_black, name="head_shell")
    head.visual(
        Box((0.006, 0.068, 0.028)),
        origin=Origin(xyz=(0.043, 0.0, 0.030)),
        material=diffuser_white,
        name="diffuser",
    )

    battery_door = model.part("battery_door")
    battery_door.visual(
        Box((0.037, 0.003, 0.084)),
        origin=Origin(xyz=(0.0225, 0.0, 0.0)),
        material=body_black,
        name="panel",
    )
    battery_door.visual(
        mesh_from_cadquery(_battery_door_hardware_shape(), "battery_door_hardware"),
        material=trim_dark,
        name="hinge_barrel",
    )

    model.articulation(
        "body_to_neck",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=neck,
        origin=Origin(xyz=(0.0, 0.0, SWIVEL_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=12.0, velocity=8.0),
    )
    model.articulation(
        "neck_to_head",
        ArticulationType.REVOLUTE,
        parent=neck,
        child=head,
        origin=Origin(xyz=(0.0, 0.0, 0.046)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=4.0, lower=-0.12, upper=1.57),
    )
    model.articulation(
        "body_to_battery_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=battery_door,
        origin=Origin(xyz=(-0.020, BODY_WIDTH / 2.0 - 0.0015, 0.068)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=3.0, lower=0.0, upper=2.10),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
