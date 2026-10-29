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
import math
import cadquery as cq
BASE_RADIUS = 0.165
BASE_THICKNESS = 0.032
STEM_RADIUS = 0.015
SHOULDER_Z = 0.905
LOWER_ARM_LENGTH = 0.420
LOWER_ARM_REST_ANGLE = math.radians(24.0)
UPPER_ARM_LENGTH = 0.360
UPPER_ARM_REST_ANGLE = math.radians(18.0)
LOWER_ARM_WIDTH = 0.018
LOWER_ARM_HEIGHT = 0.014
UPPER_ARM_WIDTH = 0.016
UPPER_ARM_HEIGHT = 0.012
PLATE_THICKNESS = 0.006
LOWER_BARREL_RADIUS = 0.010
LOWER_BARREL_LENGTH = 0.019
UPPER_BARREL_RADIUS = 0.009
UPPER_BARREL_LENGTH = 0.017
SHADE_BARREL_RADIUS = 0.0085
SHADE_BARREL_LENGTH = 0.016
SHADE_LENGTH = 0.200
SHADE_REAR_X = 0.026
SHADE_AXIS_Z = -0.026
SHADE_REAR_RADIUS = 0.037
SHADE_FRONT_RADIUS = 0.108
SHADE_WALL = 0.0025
SHOULDER_LIMITS = (-0.35, 1.05)
ELBOW_LIMITS = (-0.95, 0.85)
SHADE_LIMITS = (-0.80, 0.50)
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    sx, sy, sz = size
    return cq.Workplane("XY").box(sx, sy, sz).translate(center)
def _cylinder_x(
    radius: float, length: float, center: tuple[float, float, float]
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((cx, cy, cz))
    )
def _cylinder_y(
    radius: float, length: float, center: tuple[float, float, float]
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
        .translate((cx, cy, cz))
    )
def _cylinder_z(
    radius: float, length: float, center: tuple[float, float, float]
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((cx, cy, cz - (length * 0.5)))
    )
def _rotate_up(shape: cq.Workplane, angle_rad: float) -> cq.Workplane:
    return shape.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -math.degrees(angle_rad))
def _fuse_all(*pieces: cq.Workplane) -> cq.Workplane:
    fused = pieces[0].val()
    for piece in pieces[1:]:
        fused = fused.fuse(piece.val())
    return cq.Workplane(obj=fused)
def _tip_coords(length: float, angle_rad: float) -> tuple[float, float, float]:
    return (
        length * math.cos(angle_rad),
        0.0,
        length * math.sin(angle_rad),
    )
def _build_base_shape() -> cq.Workplane:
    base_disk = cq.Workplane("XY").circle(BASE_RADIUS).extrude(BASE_THICKNESS)
    plinth = cq.Workplane("XY").circle(BASE_RADIUS * 0.72).extrude(0.010).translate(
        (0.0, 0.0, BASE_THICKNESS)
    )

    stem_height = SHOULDER_Z - BASE_THICKNESS - 0.045
    stem = _cylinder_z(
        STEM_RADIUS,
        stem_height,
        (0.0, 0.0, BASE_THICKNESS + (stem_height * 0.5)),
    )

    return _fuse_all(base_disk, plinth, stem)
def _build_shoulder_bracket_shape() -> cq.Workplane:
    shoulder_socket = _box(
        (0.026, 0.028, 0.050),
        (-0.034, 0.0, SHOULDER_Z - 0.034),
    )

    left_plate = _box(
        (0.018, PLATE_THICKNESS, 0.040),
        (-0.009, 0.0125, SHOULDER_Z),
    )
    right_plate = _box(
        (0.018, PLATE_THICKNESS, 0.040),
        (-0.009, -0.0125, SHOULDER_Z),
    )

    rear_gusset = _box((0.020, 0.022, 0.022), (-0.031, 0.0, SHOULDER_Z - 0.058))
    bridge = _box((0.018, 0.020, 0.028), (-0.020, 0.0, SHOULDER_Z - 0.038))
    left_brace = _box((0.018, 0.010, 0.020), (-0.011, 0.0105, SHOULDER_Z - 0.020))
    right_brace = _box((0.018, 0.010, 0.020), (-0.011, -0.0105, SHOULDER_Z - 0.020))

    return _fuse_all(
        shoulder_socket,
        left_plate,
        right_plate,
        rear_gusset,
        bridge,
        left_brace,
        right_brace,
    )
def _build_lower_arm_shape() -> cq.Workplane:
    barrel = _cylinder_y(LOWER_BARREL_RADIUS, LOWER_BARREL_LENGTH, (0.0, 0.0, 0.0))
    root_block = _box((0.030, LOWER_ARM_WIDTH, 0.018), (0.016, 0.0, 0.0))
    beam = _box(
        (LOWER_ARM_LENGTH - 0.038, LOWER_ARM_WIDTH, LOWER_ARM_HEIGHT),
        ((LOWER_ARM_LENGTH - 0.038) * 0.5, 0.0, 0.0),
    )
    elbow_block = _box((0.028, 0.022, 0.018), (LOWER_ARM_LENGTH - 0.024, 0.0, 0.0))
    left_plate = _box(
        (0.018, PLATE_THICKNESS, 0.032),
        (
            LOWER_ARM_LENGTH - 0.009,
            0.0115,
            0.0,
        ),
    )
    right_plate = _box(
        (0.018, PLATE_THICKNESS, 0.032),
        (
            LOWER_ARM_LENGTH - 0.009,
            -0.0115,
            0.0,
        ),
    )

    return _rotate_up(
        _fuse_all(barrel, root_block, beam, elbow_block, left_plate, right_plate),
        LOWER_ARM_REST_ANGLE,
    )
def _build_upper_arm_shape() -> cq.Workplane:
    barrel = _cylinder_y(UPPER_BARREL_RADIUS, UPPER_BARREL_LENGTH, (0.0, 0.0, 0.0))
    root_block = _box((0.028, UPPER_ARM_WIDTH, 0.016), (0.015, 0.0, 0.0))
    beam = _box(
        (UPPER_ARM_LENGTH - 0.038, UPPER_ARM_WIDTH, UPPER_ARM_HEIGHT),
        ((UPPER_ARM_LENGTH - 0.038) * 0.5, 0.0, 0.0),
    )
    tip_block = _box((0.040, 0.021, 0.016), (UPPER_ARM_LENGTH - 0.031, 0.0, 0.0))
    left_plate = _box(
        (0.016, 0.0055, 0.028),
        (
            UPPER_ARM_LENGTH - 0.008,
            0.01075,
            0.0,
        ),
    )
    right_plate = _box(
        (0.016, 0.0055, 0.028),
        (
            UPPER_ARM_LENGTH - 0.008,
            -0.01075,
            0.0,
        ),
    )

    return _rotate_up(
        _fuse_all(barrel, root_block, beam, tip_block, left_plate, right_plate),
        UPPER_ARM_REST_ANGLE,
    )
def _build_shade_shape() -> cq.Workplane:
    pivot_barrel = _cylinder_y(SHADE_BARREL_RADIUS, SHADE_BARREL_LENGTH, (0.0, 0.0, 0.0))
    support_spine = _box((0.028, 0.014, 0.010), (0.020, 0.0, -0.010))
    rear_collar = _cylinder_x(0.024, 0.028, (0.030, 0.0, SHADE_AXIS_Z))

    rear_hole_radius = 0.014
    rear_inner_x = SHADE_REAR_X + 0.006
    rear_inner_radius = SHADE_REAR_RADIUS - SHADE_WALL
    front_x = SHADE_REAR_X + SHADE_LENGTH
    front_inner_radius = SHADE_FRONT_RADIUS - SHADE_WALL

    shade_shell = (
        cq.Workplane("XZ")
        .moveTo(SHADE_REAR_X, SHADE_AXIS_Z + SHADE_REAR_RADIUS)
        .lineTo(front_x, SHADE_AXIS_Z + SHADE_FRONT_RADIUS)
        .lineTo(front_x, SHADE_AXIS_Z + front_inner_radius)
        .lineTo(rear_inner_x, SHADE_AXIS_Z + rear_inner_radius)
        .lineTo(SHADE_REAR_X, SHADE_AXIS_Z + rear_hole_radius)
        .close()
        .revolve(
            360.0,
            axisStart=(0.0, 0.0, SHADE_AXIS_Z),
            axisEnd=(1.0, 0.0, SHADE_AXIS_Z),
        )
    )

    return _fuse_all(pivot_barrel, support_spine, rear_collar, shade_shell)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="floor_task_lamp")

    powder_black = model.material("powder_black", rgba=(0.13, 0.13, 0.15, 1.0))
    satin_steel = model.material("satin_steel", rgba=(0.72, 0.74, 0.78, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_build_base_shape(), "lamp_base"),
        material=powder_black,
        name="base_shell",
    )

    shoulder_bracket = model.part("shoulder_bracket")
    shoulder_bracket.visual(
        mesh_from_cadquery(_build_shoulder_bracket_shape(), "shoulder_bracket"),
        material=powder_black,
        name="shoulder_bracket_shell",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        mesh_from_cadquery(_build_lower_arm_shape(), "lower_arm"),
        material=powder_black,
        name="lower_arm_shell",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(_build_upper_arm_shape(), "upper_arm"),
        material=powder_black,
        name="upper_arm_shell",
    )

    shade = model.part("shade")
    shade.visual(
        mesh_from_cadquery(_build_shade_shape(), "lamp_shade"),
        material=satin_steel,
        name="shade_shell",
    )

    lower_tip = _tip_coords(LOWER_ARM_LENGTH, LOWER_ARM_REST_ANGLE)
    upper_tip = _tip_coords(UPPER_ARM_LENGTH, UPPER_ARM_REST_ANGLE)

    model.articulation(
        "base_to_shoulder_bracket",
        ArticulationType.FIXED,
        parent=base,
        child=shoulder_bracket,
        origin=Origin(),
    )
    model.articulation(
        "base_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=shoulder_bracket,
        child=lower_arm,
        origin=Origin(xyz=(0.0, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.2,
            lower=SHOULDER_LIMITS[0],
            upper=SHOULDER_LIMITS[1],
        ),
    )
    model.articulation(
        "lower_arm_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=lower_arm,
        child=upper_arm,
        origin=Origin(xyz=lower_tip),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.4,
            lower=ELBOW_LIMITS[0],
            upper=ELBOW_LIMITS[1],
        ),
    )
    model.articulation(
        "upper_arm_to_shade",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=shade,
        origin=Origin(xyz=upper_tip),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=1.8,
            lower=SHADE_LIMITS[0],
            upper=SHADE_LIMITS[1],
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
