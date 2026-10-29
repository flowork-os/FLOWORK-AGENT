# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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
CABINET_WIDTH = 0.82
CABINET_DEPTH_REAR = -0.37
CABINET_HEIGHT = 1.93
BODY_PROFILE = (
    (CABINET_DEPTH_REAR, 0.00),
    (0.36, 0.00),
    (0.36, 0.72),
    (0.44, 0.84),
    (0.30, 0.96),
    (0.12, 1.58),
    (0.10, 1.84),
    (0.10, CABINET_HEIGHT),
    (CABINET_DEPTH_REAR, CABINET_HEIGHT),
)
BELLY_CAVITY_DEPTH = 0.18
BELLY_CAVITY_WIDTH = 0.56
BELLY_CAVITY_HEIGHT = 0.50
BELLY_CAVITY_CENTER_X = 0.27
BELLY_CAVITY_CENTER_Z = 0.34
DOOR_THICKNESS = 0.035
DOOR_WIDTH = 0.53
DOOR_HEIGHT = 0.46
DOOR_HINGE_X = 0.325
DOOR_BOTTOM_Z = 0.10
DISPLAY_PITCH = math.atan2(0.12 - 0.30, 1.58 - 0.96)
DISPLAY_CENTER_X = 0.21
DISPLAY_CENTER_Z = 1.28
DISPLAY_BEZEL_THICKNESS = 0.024
DISPLAY_BEZEL_WIDTH = 0.60
DISPLAY_BEZEL_HEIGHT = 0.48
DISPLAY_GLASS_THICKNESS = 0.006
DISPLAY_GLASS_WIDTH = 0.54
DISPLAY_GLASS_HEIGHT = 0.42
DECK_NORMAL_PITCH = math.atan2(0.12, 0.14)
BUTTON_RADIUS = 0.045
BUTTON_LENGTH = 0.030
BUTTON_SURFACE_X = 0.37
BUTTON_SURFACE_Z = 0.90
BUTTON_Y_POSITIONS = (-0.25, -0.08, 0.08, 0.25)
HANDLE_PIVOT_X = 0.22
HANDLE_PIVOT_Y = CABINET_WIDTH / 2.0 + 0.072
HANDLE_PIVOT_Z = 1.08
HANDLE_VECTOR_X = 0.34
HANDLE_VECTOR_Z = -0.20
HANDLE_ARM_LENGTH = math.hypot(HANDLE_VECTOR_X, HANDLE_VECTOR_Z)
HANDLE_ARM_PITCH = math.atan2(HANDLE_VECTOR_X, HANDLE_VECTOR_Z)
def _panel_normal_from_pitch(pitch: float) -> tuple[float, float, float]:
    return (math.cos(pitch), 0.0, -math.sin(pitch))
def _axis_from_pitch(pitch: float) -> tuple[float, float, float]:
    return (math.sin(pitch), 0.0, math.cos(pitch))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="slant_top_video_slot_machine")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.14, 0.15, 0.17, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.05, 0.05, 0.06, 1.0))
    screen_finish = model.material("screen_finish", rgba=(0.05, 0.09, 0.14, 1.0))
    button_red = model.material("button_red", rgba=(0.78, 0.13, 0.13, 1.0))
    button_green = model.material("button_green", rgba=(0.10, 0.55, 0.24, 1.0))
    button_blue = model.material("button_blue", rgba=(0.12, 0.34, 0.72, 1.0))
    button_gold = model.material("button_gold", rgba=(0.79, 0.62, 0.18, 1.0))
    door_finish = model.material("door_finish", rgba=(0.22, 0.22, 0.24, 1.0))
    metal_finish = model.material("metal_finish", rgba=(0.68, 0.69, 0.72, 1.0))
    handle_finish = model.material("handle_finish", rgba=(0.86, 0.87, 0.88, 1.0))
    knob_finish = model.material("knob_finish", rgba=(0.12, 0.12, 0.13, 1.0))

    cabinet = model.part("cabinet")

    shell = (
        cq.Workplane("XZ")
        .polyline(BODY_PROFILE)
        .close()
        .extrude(CABINET_WIDTH / 2.0, both=True)
    )
    belly_cavity = (
        cq.Workplane("XY")
        .box(BELLY_CAVITY_DEPTH, BELLY_CAVITY_WIDTH, BELLY_CAVITY_HEIGHT)
        .translate((BELLY_CAVITY_CENTER_X, 0.0, BELLY_CAVITY_CENTER_Z))
    )
    shell = shell.cut(belly_cavity)

    cabinet.visual(
        mesh_from_cadquery(shell, "slot_machine_shell"),
        material=cabinet_finish,
        name="shell",
    )

    display_normal = _panel_normal_from_pitch(DISPLAY_PITCH)
    bezel_center = (
        DISPLAY_CENTER_X + display_normal[0] * 0.004,
        0.0,
        DISPLAY_CENTER_Z + display_normal[2] * 0.004,
    )
    screen_center = (
        DISPLAY_CENTER_X + display_normal[0] * 0.012,
        0.0,
        DISPLAY_CENTER_Z + display_normal[2] * 0.012,
    )

    cabinet.visual(
        Box((DISPLAY_BEZEL_THICKNESS, DISPLAY_BEZEL_WIDTH, DISPLAY_BEZEL_HEIGHT)),
        origin=Origin(xyz=bezel_center, rpy=(0.0, DISPLAY_PITCH, 0.0)),
        material=trim_finish,
        name="display_bezel",
    )
    cabinet.visual(
        Box((DISPLAY_GLASS_THICKNESS, DISPLAY_GLASS_WIDTH, DISPLAY_GLASS_HEIGHT)),
        origin=Origin(xyz=screen_center, rpy=(0.0, DISPLAY_PITCH, 0.0)),
        material=screen_finish,
        name="screen",
    )

    button_axis = _axis_from_pitch(DECK_NORMAL_PITCH)
    button_materials = (button_red, button_green, button_blue, button_gold)
    for index, (y_pos, material) in enumerate(zip(BUTTON_Y_POSITIONS, button_materials)):
        button_center = (
            BUTTON_SURFACE_X + button_axis[0] * (BUTTON_LENGTH * 0.35),
            y_pos,
            BUTTON_SURFACE_Z + button_axis[2] * (BUTTON_LENGTH * 0.35),
        )
        cabinet.visual(
            Cylinder(radius=BUTTON_RADIUS, length=BUTTON_LENGTH),
            origin=Origin(xyz=button_center, rpy=(0.0, DECK_NORMAL_PITCH, 0.0)),
            material=material,
            name=f"button_{index}",
        )

    cabinet.visual(
        Box((0.020, 0.020, 0.50)),
        origin=Origin(xyz=(0.350, -0.275, 0.35)),
        material=metal_finish,
        name="door_jamb",
    )

    door = model.part("door")
    door.visual(
        Box((DOOR_THICKNESS, DOOR_WIDTH, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_THICKNESS / 2.0, DOOR_WIDTH / 2.0, DOOR_HEIGHT / 2.0)),
        material=door_finish,
        name="door_panel",
    )
    door.visual(
        Box((0.036, 0.020, 0.48)),
        origin=Origin(xyz=(0.053, -0.010, DOOR_HEIGHT / 2.0)),
        material=metal_finish,
        name="hinge_leaf",
    )
    door.visual(
        Box((0.020, 0.15, 0.04)),
        origin=Origin(xyz=(DOOR_THICKNESS + 0.005, DOOR_WIDTH * 0.54, 0.11)),
        material=metal_finish,
        name="door_pull",
    )
    door.visual(
        Cylinder(radius=0.018, length=0.020),
        origin=Origin(
            xyz=(DOOR_THICKNESS + 0.010, DOOR_WIDTH * 0.80, DOOR_HEIGHT * 0.58),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=metal_finish,
        name="door_lock",
    )

    bracket = model.part("bracket")
    bracket.visual(
        Box((0.22, 0.010, 0.40)),
        origin=Origin(xyz=(0.0, -0.067, 0.0)),
        material=metal_finish,
        name="mount_pad",
    )
    bracket.visual(
        Box((0.05, 0.050, 0.05)),
        origin=Origin(xyz=(0.0, -0.0425, 0.10)),
        material=metal_finish,
        name="upper_spacer",
    )
    bracket.visual(
        Box((0.05, 0.050, 0.05)),
        origin=Origin(xyz=(0.0, -0.0425, -0.10)),
        material=metal_finish,
        name="lower_spacer",
    )
    bracket.visual(
        Box((0.16, 0.010, 0.28)),
        origin=Origin(xyz=(0.0, -0.020, 0.0)),
        material=metal_finish,
        name="inner_ear",
    )
    bracket.visual(
        Box((0.16, 0.010, 0.28)),
        origin=Origin(xyz=(0.0, 0.020, 0.0)),
        material=metal_finish,
        name="outer_ear",
    )
    bracket.visual(
        Box((0.12, 0.040, 0.03)),
        origin=Origin(xyz=(0.0, 0.0, 0.135)),
        material=metal_finish,
        name="upper_bridge",
    )
    bracket.visual(
        Box((0.12, 0.040, 0.03)),
        origin=Origin(xyz=(0.0, 0.0, -0.135)),
        material=metal_finish,
        name="lower_bridge",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.024, length=0.030),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=handle_finish,
        name="hub",
    )
    handle.visual(
        Cylinder(radius=0.017, length=HANDLE_ARM_LENGTH),
        origin=Origin(
            xyz=(HANDLE_VECTOR_X / 2.0, 0.0, HANDLE_VECTOR_Z / 2.0),
            rpy=(0.0, HANDLE_ARM_PITCH, 0.0),
        ),
        material=handle_finish,
        name="arm",
    )
    handle.visual(
        Sphere(radius=0.043),
        origin=Origin(xyz=(HANDLE_VECTOR_X, 0.0, HANDLE_VECTOR_Z)),
        material=knob_finish,
        name="knob",
    )

    model.articulation(
        "cabinet_to_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=door,
        origin=Origin(xyz=(DOOR_HINGE_X, -DOOR_WIDTH / 2.0, DOOR_BOTTOM_Z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.40, effort=20.0, velocity=1.2),
    )
    model.articulation(
        "cabinet_to_bracket",
        ArticulationType.FIXED,
        parent=cabinet,
        child=bracket,
        origin=Origin(xyz=(HANDLE_PIVOT_X, HANDLE_PIVOT_Y, HANDLE_PIVOT_Z)),
    )
    model.articulation(
        "bracket_to_handle",
        ArticulationType.REVOLUTE,
        parent=bracket,
        child=handle,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.05, effort=15.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
