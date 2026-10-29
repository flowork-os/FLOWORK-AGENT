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
BASE_RADIUS = 0.095
BASE_THICKNESS = 0.018
PEDESTAL_RADIUS = 0.022
PEDESTAL_HEIGHT = 0.036
SHOULDER_Z = 0.076
SHOULDER_CHEEK_DEPTH = 0.030
SHOULDER_CHEEK_THICKNESS = 0.007
SHOULDER_CHEEK_HEIGHT = 0.036
SHOULDER_GAP = 0.024
LOWER_ARM_LENGTH = 0.190
LOWER_ARM_PITCH = -0.88
UPPER_ARM_LENGTH = 0.165
UPPER_ARM_PITCH = -0.38
ARM_BAR_THICKNESS = 0.0045
ARM_BAR_HEIGHT = 0.010
ARM_BAR_OFFSET_Y = 0.014
LOWER_ROOT_BARREL_RADIUS = 0.0065
LOWER_ROOT_BARREL_LENGTH = 0.022
ELBOW_GAP = 0.022
ELBOW_CHEEK_THICKNESS = 0.005
ELBOW_CHEEK_DEPTH = 0.024
ELBOW_CHEEK_HEIGHT = 0.020
UPPER_ROOT_BARREL_RADIUS = 0.0060
UPPER_ROOT_BARREL_LENGTH = 0.020
TIP_GAP = 0.018
TIP_CHEEK_THICKNESS = 0.0045
TIP_CHEEK_DEPTH = 0.020
TIP_CHEEK_HEIGHT = 0.018
SHADE_BARREL_RADIUS = 0.0048
SHADE_BARREL_LENGTH = 0.016
SHADE_NECK_RADIUS = 0.010
SHADE_NECK_LENGTH = 0.028
SHADE_REST_PITCH = 0.58
SHADE_LENGTH = 0.112
SHADE_REAR_RADIUS = 0.024
SHADE_FRONT_RADIUS = 0.060
SHADE_WALL = 0.0018
SHADE_SOCKET_RADIUS = 0.012
def _local_x_vector(distance: float, pitch: float) -> tuple[float, float, float]:
    return (
        distance * math.cos(pitch),
        0.0,
        -distance * math.sin(pitch),
    )
def _vector_add(
    a: tuple[float, float, float], b: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _add_parallel_arm(
    part,
    *,
    prefix: str,
    arm_length: float,
    arm_pitch: float,
    root_barrel_radius: float,
    root_barrel_length: float,
    clevis_gap: float,
    clevis_thickness: float,
    clevis_depth: float,
    clevis_height: float,
    arm_material,
    hardware_material,
) -> tuple[float, float, float]:
    bar_inner_y = ARM_BAR_OFFSET_Y - ARM_BAR_THICKNESS / 2.0

    part.visual(
        Cylinder(radius=root_barrel_radius, length=root_barrel_length),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hardware_material,
        name=f"{prefix}_root_barrel",
    )

    root_link_width = max(bar_inner_y - root_barrel_length / 2.0 + 0.002, 0.003)
    root_link_center = _local_x_vector(0.006, arm_pitch)
    root_link_y = (root_barrel_length / 2.0 + bar_inner_y) / 2.0
    for index, y_sign in enumerate((-1.0, 1.0)):
        part.visual(
            Box((0.012, root_link_width, 0.008)),
            origin=Origin(
                xyz=(root_link_center[0], y_sign * root_link_y, root_link_center[2]),
                rpy=(0.0, arm_pitch, 0.0),
            ),
            material=hardware_material,
            name=f"{prefix}_root_link_{index}",
        )

    arm_center = _local_x_vector(arm_length / 2.0, arm_pitch)
    for index, y_sign in enumerate((-1.0, 1.0)):
        part.visual(
            Box((arm_length, ARM_BAR_THICKNESS, ARM_BAR_HEIGHT)),
            origin=Origin(
                xyz=(arm_center[0], y_sign * ARM_BAR_OFFSET_Y, arm_center[2]),
                rpy=(0.0, arm_pitch, 0.0),
            ),
            material=arm_material,
            name=f"{prefix}_bar_{index}",
        )

    elbow_origin = _local_x_vector(arm_length, arm_pitch)
    clevis_center = _vector_add(elbow_origin, _local_x_vector(clevis_depth / 2.0, arm_pitch))
    clevis_y = clevis_gap / 2.0 + clevis_thickness / 2.0

    for index, y_sign in enumerate((-1.0, 1.0)):
        part.visual(
            Box((clevis_depth, clevis_thickness, clevis_height)),
            origin=Origin(
                xyz=(clevis_center[0], y_sign * clevis_y, clevis_center[2]),
                rpy=(0.0, arm_pitch, 0.0),
            ),
            material=hardware_material,
            name=f"{prefix}_clevis_{index}",
        )

    brace_center = _local_x_vector(arm_length * 0.38, arm_pitch)
    part.visual(
        Box((0.016, 2.0 * bar_inner_y + 0.002, 0.007)),
        origin=Origin(
            xyz=brace_center,
            rpy=(0.0, arm_pitch, 0.0),
        ),
        material=hardware_material,
        name=f"{prefix}_brace",
    )
    return elbow_origin
def _build_shade_shell():
    inner_rear_radius = max(SHADE_REAR_RADIUS - SHADE_WALL, 0.004)
    inner_front_radius = SHADE_FRONT_RADIUS - SHADE_WALL

    outer = (
        cq.Workplane("YZ")
        .circle(SHADE_REAR_RADIUS)
        .workplane(offset=SHADE_LENGTH)
        .circle(SHADE_FRONT_RADIUS)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("YZ")
        .workplane(offset=SHADE_WALL)
        .circle(inner_rear_radius)
        .workplane(offset=SHADE_LENGTH - SHADE_WALL)
        .circle(inner_front_radius)
        .loft(combine=True)
    )
    rear_socket = (
        cq.Workplane("YZ")
        .circle(SHADE_SOCKET_RADIUS)
        .extrude(SHADE_REAR_RADIUS * 2.2)
    )
    return outer.cut(inner).cut(rear_socket)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="architect_desk_lamp")

    base_paint = model.material("base_paint", rgba=(0.13, 0.13, 0.14, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.68, 0.69, 0.72, 1.0))
    hardware = model.material("hardware", rgba=(0.34, 0.35, 0.37, 1.0))
    shade_paint = model.material("shade_paint", rgba=(0.16, 0.16, 0.17, 1.0))

    lower_arm_end = _local_x_vector(LOWER_ARM_LENGTH, LOWER_ARM_PITCH)
    upper_arm_end = _local_x_vector(UPPER_ARM_LENGTH, UPPER_ARM_PITCH)

    base = model.part("base")
    base.visual(
        Cylinder(radius=BASE_RADIUS, length=BASE_THICKNESS),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS / 2.0)),
        material=base_paint,
        name="base_disk",
    )
    base.visual(
        Cylinder(radius=PEDESTAL_RADIUS, length=PEDESTAL_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + PEDESTAL_HEIGHT / 2.0)),
        material=base_paint,
        name="pedestal",
    )
    base.visual(
        Cylinder(radius=0.027, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.061)),
        material=hardware,
        name="shoulder_collar",
    )
    shoulder_cheek_y = SHOULDER_GAP / 2.0 + SHOULDER_CHEEK_THICKNESS / 2.0
    for index, y_sign in enumerate((-1.0, 1.0)):
        base.visual(
            Box((SHOULDER_CHEEK_DEPTH, SHOULDER_CHEEK_THICKNESS, SHOULDER_CHEEK_HEIGHT)),
            origin=Origin(
                xyz=(0.010, y_sign * shoulder_cheek_y, 0.071),
            ),
            material=hardware,
            name=f"shoulder_cheek_{index}",
        )

    lower_arm = model.part("lower_arm")
    _add_parallel_arm(
        lower_arm,
        prefix="lower",
        arm_length=LOWER_ARM_LENGTH,
        arm_pitch=LOWER_ARM_PITCH,
        root_barrel_radius=LOWER_ROOT_BARREL_RADIUS,
        root_barrel_length=LOWER_ROOT_BARREL_LENGTH,
        clevis_gap=ELBOW_GAP,
        clevis_thickness=ELBOW_CHEEK_THICKNESS,
        clevis_depth=ELBOW_CHEEK_DEPTH,
        clevis_height=ELBOW_CHEEK_HEIGHT,
        arm_material=arm_finish,
        hardware_material=hardware,
    )

    upper_arm = model.part("upper_arm")
    _add_parallel_arm(
        upper_arm,
        prefix="upper",
        arm_length=UPPER_ARM_LENGTH,
        arm_pitch=UPPER_ARM_PITCH,
        root_barrel_radius=UPPER_ROOT_BARREL_RADIUS,
        root_barrel_length=UPPER_ROOT_BARREL_LENGTH,
        clevis_gap=TIP_GAP,
        clevis_thickness=TIP_CHEEK_THICKNESS,
        clevis_depth=TIP_CHEEK_DEPTH,
        clevis_height=TIP_CHEEK_HEIGHT,
        arm_material=arm_finish,
        hardware_material=hardware,
    )

    shade = model.part("shade")
    shade.visual(
        Cylinder(radius=SHADE_BARREL_RADIUS, length=SHADE_BARREL_LENGTH),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hardware,
        name="shade_barrel",
    )

    neck_center = _local_x_vector(SHADE_NECK_LENGTH / 2.0, SHADE_REST_PITCH)
    shade.visual(
        Cylinder(radius=SHADE_NECK_RADIUS, length=SHADE_NECK_LENGTH),
        origin=Origin(
            xyz=neck_center,
            rpy=(0.0, math.pi / 2.0 + SHADE_REST_PITCH, 0.0),
        ),
        material=hardware,
        name="shade_neck",
    )
    shade.visual(
        Cylinder(radius=0.015, length=0.010),
        origin=Origin(
            xyz=_local_x_vector(0.018, SHADE_REST_PITCH),
            rpy=(0.0, math.pi / 2.0 + SHADE_REST_PITCH, 0.0),
        ),
        material=hardware,
        name="shade_socket",
    )

    shade.visual(
        mesh_from_cadquery(_build_shade_shell(), "architect_lamp_shade_shell"),
        origin=Origin(
            xyz=_local_x_vector(0.015, SHADE_REST_PITCH),
            rpy=(0.0, SHADE_REST_PITCH, 0.0),
        ),
        material=shade_paint,
        name="shade_shell",
    )

    model.articulation(
        "base_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=base,
        child=lower_arm,
        origin=Origin(xyz=(0.0, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-0.70,
            upper=0.85,
            effort=20.0,
            velocity=1.8,
        ),
    )
    model.articulation(
        "lower_arm_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=lower_arm_end),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-1.05,
            upper=0.95,
            effort=14.0,
            velocity=2.0,
        ),
    )
    model.articulation(
        "upper_arm_to_shade",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=shade,
        origin=Origin(xyz=upper_arm_end),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=-0.45,
            upper=0.75,
            effort=8.0,
            velocity=2.4,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
