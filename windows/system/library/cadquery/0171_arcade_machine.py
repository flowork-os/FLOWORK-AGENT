# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

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
WIDTH = 0.74
SIDE_THICKNESS = 0.018
INNER_WIDTH = WIDTH - 2.0 * SIDE_THICKNESS
BODY_FRONT_X = 0.24
BODY_REAR_X = -0.36
HEIGHT = 1.78
OUTER_PROFILE = [
    (BODY_REAR_X, 0.00),
    (BODY_FRONT_X, 0.00),
    (BODY_FRONT_X, 0.94),
    (0.07, 1.10),
    (-0.02, 1.42),
    (0.10, 1.58),
    (0.10, HEIGHT),
    (-0.27, HEIGHT),
    (BODY_REAR_X, 1.42),
]
DOOR_WIDTH = 0.458
DOOR_HEIGHT = 0.578
DOOR_THICKNESS = 0.016
DOOR_BOTTOM_Z = 0.13
DOOR_HINGE_Y = DOOR_WIDTH / 2.0 + 0.004
DOOR_HINGE_X = BODY_FRONT_X
FLAP_WIDTH = 0.104
FLAP_HEIGHT = 0.056
FLAP_THICKNESS = 0.007
FLAP_HINGE_X = BODY_FRONT_X
FLAP_HINGE_Y = 0.10
FLAP_HINGE_Z = 0.86
COIN_SLOT_CENTER = (-0.11, 0.885)
DECK_ORIGIN_X = BODY_FRONT_X
DECK_ORIGIN_Z = 0.94
DECK_WIDTH = 0.64
DECK_PROFILE = [
    (0.00, 0.00),
    (0.20, 0.00),
    (0.20, 0.05),
    (0.00, 0.15),
]
DECK_TOP_REAR = (0.00, 0.15)
DECK_TOP_FRONT = (0.20, 0.05)
DECK_TOP_DX = DECK_TOP_FRONT[0] - DECK_TOP_REAR[0]
DECK_TOP_DZ = DECK_TOP_FRONT[1] - DECK_TOP_REAR[1]
DECK_TOP_NORMAL_LEN = math.hypot(-DECK_TOP_DZ, DECK_TOP_DX)
DECK_TOP_NORMAL = (
    -DECK_TOP_DZ / DECK_TOP_NORMAL_LEN,
    0.0,
    DECK_TOP_DX / DECK_TOP_NORMAL_LEN,
)
DECK_TOP_PITCH = math.atan2(DECK_TOP_NORMAL[0], DECK_TOP_NORMAL[2])
MONITOR_PITCH = math.radians(-15.7)
SCREEN_ORIGIN = (0.02, 0.0, 1.27)
SCREEN_NORMAL = (math.cos(MONITOR_PITCH), 0.0, -math.sin(MONITOR_PITCH))
MARQUEE_ORIGIN = (0.06, 0.0, 1.64)
MARQUEE_PITCH = math.radians(-3.0)
def _extruded_profile(profile: list[tuple[float, float]], width: float) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .polyline(profile)
        .close()
        .extrude(width)
        .translate((0.0, width / 2.0, 0.0))
    )
def _rotated_box(
    size: tuple[float, float, float],
    center: tuple[float, float, float],
    pitch_deg: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(*size)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), pitch_deg)
        .translate(center)
    )
def _body_shell() -> cq.Workplane:
    left_side = _extruded_profile(OUTER_PROFILE, SIDE_THICKNESS).translate((0.0, WIDTH / 2.0 - SIDE_THICKNESS / 2.0, 0.0))
    right_side = _extruded_profile(OUTER_PROFILE, SIDE_THICKNESS).translate((0.0, -WIDTH / 2.0 + SIDE_THICKNESS / 2.0, 0.0))

    bottom_panel = cq.Workplane("XY").box(0.48, INNER_WIDTH, SIDE_THICKNESS).translate((-0.08, 0.0, SIDE_THICKNESS / 2.0))
    lower_rear = cq.Workplane("XY").box(SIDE_THICKNESS, INNER_WIDTH, 1.42).translate((BODY_REAR_X + SIDE_THICKNESS / 2.0, 0.0, 0.71))
    upper_rear = cq.Workplane("XY").box(SIDE_THICKNESS, INNER_WIDTH, 0.36).translate((-0.27, 0.0, 1.60))
    roof = cq.Workplane("XY").box(0.37, INNER_WIDTH, SIDE_THICKNESS).translate((-0.085, 0.0, HEIGHT - SIDE_THICKNESS / 2.0))

    door_open_width = DOOR_WIDTH + 0.006
    stile_width = (INNER_WIDTH - door_open_width) / 2.0
    stile_center_y = door_open_width / 2.0 + stile_width / 2.0

    bottom_rail = cq.Workplane("XY").box(SIDE_THICKNESS, INNER_WIDTH, 0.13).translate((BODY_FRONT_X - SIDE_THICKNESS / 2.0, 0.0, 0.065))
    left_stile = cq.Workplane("XY").box(SIDE_THICKNESS, stile_width, 0.59).translate(
        (BODY_FRONT_X - SIDE_THICKNESS / 2.0, -stile_center_y, 0.425)
    )
    right_stile = cq.Workplane("XY").box(SIDE_THICKNESS, stile_width, 0.59).translate(
        (BODY_FRONT_X - SIDE_THICKNESS / 2.0, stile_center_y, 0.425)
    )

    flap_cut = cq.Workplane("XY").box(0.05, FLAP_WIDTH + 0.006, FLAP_HEIGHT + 0.006).translate(
        (BODY_FRONT_X - 0.012, FLAP_HINGE_Y, FLAP_HINGE_Z - FLAP_HEIGHT / 2.0)
    )
    coin_panel = (
        cq.Workplane("XY")
        .box(SIDE_THICKNESS, INNER_WIDTH, 0.20)
        .translate((BODY_FRONT_X - SIDE_THICKNESS / 2.0, 0.0, 0.82))
        .cut(flap_cut)
    )

    deck_shelf = cq.Workplane("XY").box(0.22, INNER_WIDTH, SIDE_THICKNESS).translate((0.04, 0.0, 0.93))
    deck_mount = cq.Workplane("XY").box(0.10, INNER_WIDTH, 0.12).translate((0.19, 0.0, 1.00))

    monitor_frame = _rotated_box((SIDE_THICKNESS, INNER_WIDTH, 0.74), (0.02, 0.0, 1.27), pitch_deg=math.degrees(MONITOR_PITCH))
    monitor_opening = _rotated_box((0.05, 0.50, 0.62), (0.02, 0.0, 1.27), pitch_deg=math.degrees(MONITOR_PITCH))
    monitor_frame = monitor_frame.cut(monitor_opening)

    marquee_frame = _rotated_box((SIDE_THICKNESS, INNER_WIDTH, 0.22), (0.091, 0.0, 1.64), pitch_deg=math.degrees(MARQUEE_PITCH))
    marquee_opening = _rotated_box((0.05, 0.56, 0.18), (0.091, 0.0, 1.64), pitch_deg=math.degrees(MARQUEE_PITCH))
    marquee_frame = marquee_frame.cut(marquee_opening)

    body = left_side.union(right_side)
    for piece in (
        bottom_panel,
        lower_rear,
        upper_rear,
        roof,
        bottom_rail,
        left_stile,
        right_stile,
        coin_panel,
        deck_shelf,
        deck_mount,
        monitor_frame,
        marquee_frame,
    ):
        body = body.union(piece)

    return body
def _control_panel_shell() -> cq.Workplane:
    local_profile = [(x, z) for x, z in DECK_PROFILE]
    return _extruded_profile(local_profile, DECK_WIDTH)
def _deck_top_z(local_x: float) -> float:
    t = local_x / DECK_TOP_DX
    return DECK_TOP_REAR[1] + t * DECK_TOP_DZ
def _deck_mount_center(local_x: float, local_y: float, length: float, embed: float) -> tuple[float, float, float]:
    top_z = _deck_top_z(local_x)
    offset = length / 2.0 - embed
    return (
        local_x + DECK_TOP_NORMAL[0] * offset,
        local_y,
        top_z + DECK_TOP_NORMAL[2] * offset,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="upright_arcade_cabinet")

    body_finish = model.material("body_finish", rgba=(0.08, 0.08, 0.09, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.15, 0.15, 0.16, 1.0))
    door_finish = model.material("door_finish", rgba=(0.18, 0.18, 0.19, 1.0))
    metal_finish = model.material("metal_finish", rgba=(0.63, 0.65, 0.69, 1.0))
    screen_finish = model.material("screen_finish", rgba=(0.04, 0.05, 0.06, 1.0))
    glass_finish = model.material("glass_finish", rgba=(0.10, 0.12, 0.15, 0.94))
    marquee_finish = model.material("marquee_finish", rgba=(0.92, 0.54, 0.18, 0.96))
    red_finish = model.material("red_finish", rgba=(0.76, 0.12, 0.10, 1.0))
    yellow_finish = model.material("yellow_finish", rgba=(0.86, 0.72, 0.16, 1.0))
    blue_finish = model.material("blue_finish", rgba=(0.12, 0.34, 0.78, 1.0))
    black_finish = model.material("black_finish", rgba=(0.03, 0.03, 0.03, 1.0))

    body = model.part("body")
    body.visual(mesh_from_cadquery(_body_shell(), "arcade_body"), material=body_finish, name="body_shell")
    body.visual(
        Box((0.008, 0.12, 0.09)),
        origin=Origin(xyz=(0.236, COIN_SLOT_CENTER[0], COIN_SLOT_CENTER[1])),
        material=metal_finish,
        name="coin_trim",
    )
    body.visual(
        Box((0.003, 0.070, 0.007)),
        origin=Origin(xyz=(0.239, COIN_SLOT_CENTER[0], COIN_SLOT_CENTER[1] + 0.010)),
        material=black_finish,
        name="coin_slot",
    )
    body.visual(
        Box((0.008, 0.500, 0.620)),
        origin=Origin(
            xyz=(
                SCREEN_ORIGIN[0] + SCREEN_NORMAL[0] * 0.002,
                0.0,
                SCREEN_ORIGIN[2] + SCREEN_NORMAL[2] * 0.002,
            ),
            rpy=(0.0, MONITOR_PITCH, 0.0),
        ),
        material=glass_finish,
        name="screen_glass",
    )
    body.visual(
        Box((0.004, 0.420, 0.520)),
        origin=Origin(
            xyz=(
                SCREEN_ORIGIN[0] - SCREEN_NORMAL[0] * 0.004,
                0.0,
                SCREEN_ORIGIN[2] - SCREEN_NORMAL[2] * 0.004,
            ),
            rpy=(0.0, MONITOR_PITCH, 0.0),
        ),
        material=screen_finish,
        name="screen_image",
    )
    body.visual(
        Box((0.020, 0.568, 0.188)),
        origin=Origin(xyz=(MARQUEE_ORIGIN[0] + 0.012, 0.0, MARQUEE_ORIGIN[2]), rpy=(0.0, MARQUEE_PITCH, 0.0)),
        material=marquee_finish,
        name="marquee_panel",
    )
    body.visual(
        Box((0.006, 0.500, 0.110)),
        origin=Origin(xyz=(MARQUEE_ORIGIN[0] + 0.009, 0.0, MARQUEE_ORIGIN[2]), rpy=(0.0, MARQUEE_PITCH, 0.0)),
        material=glass_finish,
        name="marquee_lens",
    )

    control_panel = model.part("control_panel")
    control_panel.visual(
        mesh_from_cadquery(_control_panel_shell(), "control_panel"),
        material=trim_finish,
        name="deck_shell",
    )

    joystick_base_center = _deck_mount_center(local_x=0.075, local_y=0.17, length=0.018, embed=0.005)
    joystick_stem_center = _deck_mount_center(local_x=0.075, local_y=0.17, length=0.120, embed=-0.002)
    joystick_ball_center = _deck_mount_center(local_x=0.075, local_y=0.17, length=0.162, embed=0.0)
    button_red_center = _deck_mount_center(local_x=0.118, local_y=-0.14, length=0.018, embed=0.005)
    button_yellow_center = _deck_mount_center(local_x=0.145, local_y=0.01, length=0.018, embed=0.005)
    button_blue_center = _deck_mount_center(local_x=0.165, local_y=0.15, length=0.018, embed=0.005)

    control_panel.visual(
        Cylinder(radius=0.032, length=0.018),
        origin=Origin(xyz=joystick_base_center, rpy=(0.0, DECK_TOP_PITCH, 0.0)),
        material=black_finish,
        name="joystick_base",
    )
    control_panel.visual(
        Cylinder(radius=0.009, length=0.120),
        origin=Origin(xyz=joystick_stem_center, rpy=(0.0, DECK_TOP_PITCH, 0.0)),
        material=metal_finish,
        name="joystick_stem",
    )
    control_panel.visual(
        Sphere(radius=0.018),
        origin=Origin(xyz=joystick_ball_center),
        material=red_finish,
        name="joystick_ball",
    )
    control_panel.visual(
        Cylinder(radius=0.028, length=0.018),
        origin=Origin(xyz=button_red_center, rpy=(0.0, DECK_TOP_PITCH, 0.0)),
        material=red_finish,
        name="button_red",
    )
    control_panel.visual(
        Cylinder(radius=0.028, length=0.018),
        origin=Origin(xyz=button_yellow_center, rpy=(0.0, DECK_TOP_PITCH, 0.0)),
        material=yellow_finish,
        name="button_yellow",
    )
    control_panel.visual(
        Cylinder(radius=0.028, length=0.018),
        origin=Origin(xyz=button_blue_center, rpy=(0.0, DECK_TOP_PITCH, 0.0)),
        material=blue_finish,
        name="button_blue",
    )

    service_door = model.part("service_door")
    service_door.visual(
        Box((DOOR_THICKNESS, DOOR_WIDTH, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_THICKNESS / 2.0, -DOOR_WIDTH / 2.0, DOOR_HEIGHT / 2.0)),
        material=door_finish,
        name="door_panel",
    )
    service_door.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(
            xyz=(DOOR_THICKNESS + 0.005, -DOOR_WIDTH + 0.060, DOOR_HEIGHT * 0.52),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=metal_finish,
        name="door_lock",
    )

    coin_flap = model.part("coin_flap")
    coin_flap.visual(
        Box((FLAP_THICKNESS, FLAP_WIDTH, FLAP_HEIGHT)),
        origin=Origin(xyz=(FLAP_THICKNESS / 2.0, 0.0, -FLAP_HEIGHT / 2.0)),
        material=metal_finish,
        name="flap_panel",
    )
    coin_flap.visual(
        Box((0.006, FLAP_WIDTH * 0.72, 0.012)),
        origin=Origin(xyz=(FLAP_THICKNESS + 0.001, 0.0, -FLAP_HEIGHT + 0.008)),
        material=trim_finish,
        name="flap_lip",
    )
    coin_flap.visual(
        Cylinder(radius=0.0035, length=FLAP_WIDTH * 0.98),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal_finish,
        name="flap_hinge",
    )

    model.articulation(
        "body_to_control_panel",
        ArticulationType.FIXED,
        parent=body,
        child=control_panel,
        origin=Origin(xyz=(DECK_ORIGIN_X, 0.0, DECK_ORIGIN_Z)),
    )
    model.articulation(
        "body_to_service_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=service_door,
        origin=Origin(xyz=(DOOR_HINGE_X, DOOR_HINGE_Y, DOOR_BOTTOM_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=20.0, velocity=1.5, lower=0.0, upper=1.45),
    )
    model.articulation(
        "body_to_coin_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=coin_flap,
        origin=Origin(xyz=(FLAP_HINGE_X, FLAP_HINGE_Y, FLAP_HINGE_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=4.0, lower=0.0, upper=0.90),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
