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
CABINET_WIDTH = 0.78
CABINET_DEPTH = 0.82
LOWER_HEIGHT = 0.95
TOTAL_HEIGHT = 1.72
PANEL_THICKNESS = 0.02
FRONT_Y = CABINET_DEPTH / 2.0 - PANEL_THICKNESS / 2.0
REAR_Y = -CABINET_DEPTH / 2.0 + PANEL_THICKNESS / 2.0
DECK_WIDTH = 0.78
DECK_DEPTH = 0.30
DECK_THICKNESS = 0.02
DECK_ROLL = -math.radians(14.0)
DECK_CENTER = (0.0, 0.19, 0.97)
SCREEN_WIDTH = 0.50
SCREEN_HEIGHT = 0.40
SCREEN_TILT = math.radians(12.0)
SCREEN_CENTER = (0.0, 0.105, 1.24)
MARQUEE_CENTER = (0.0, 0.015, 1.585)
DOOR_WIDTH = 0.32
DOOR_HEIGHT = 0.38
DOOR_THICKNESS = 0.018
DOOR_BOTTOM = 0.18
JOYSTICK_HOLE_RADIUS = 0.022
SUPPORT_OUTER_RADIUS = 0.027
SUPPORT_INNER_RADIUS = 0.018
JOYSTICK_PIVOT_LOCAL_Z = -0.020
JOYSTICK_SHAFT_RADIUS = 0.006
JOYSTICK_SHAFT_LENGTH = 0.115
JOYSTICK_BALL_RADIUS = 0.019
JOYSTICK_ACTUATOR_RADIUS = 0.009
JOYSTICK_ACTUATOR_LENGTH = 0.030
JOYSTICK_POSITIONS = (
    (-0.215, 0.01),
    (0.215, 0.01),
)
def _rot_x(point: tuple[float, float, float], roll: float) -> tuple[float, float, float]:
    x, y, z = point
    c = math.cos(roll)
    s = math.sin(roll)
    return (x, y * c - z * s, y * s + z * c)
def _offset(
    base: tuple[float, float, float],
    delta: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (base[0] + delta[0], base[1] + delta[1], base[2] + delta[2])
def _deck_point(local_x: float, local_y: float, local_z: float = 0.0) -> tuple[float, float, float]:
    return _offset(DECK_CENTER, _rot_x((local_x, local_y, local_z), DECK_ROLL))
def _deck_panel_mesh() -> object:
    panel = cq.Workplane("XY").box(DECK_WIDTH, DECK_DEPTH, DECK_THICKNESS)
    for local_x, local_y in JOYSTICK_POSITIONS:
        cutter = (
            cq.Workplane("XY")
            .center(local_x, local_y)
            .circle(JOYSTICK_HOLE_RADIUS)
            .extrude(DECK_THICKNESS * 4.0)
            .translate((0.0, 0.0, -DECK_THICKNESS * 2.0))
        )
        panel = panel.cut(cutter)
    return mesh_from_cadquery(panel, "arcade_control_deck")
def _ring_mesh(outer_radius: float, inner_radius: float, thickness: float, name: str) -> object:
    ring = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    return mesh_from_cadquery(ring, name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="two_player_arcade_machine")

    cabinet_black = model.material("cabinet_black", rgba=(0.10, 0.10, 0.11, 1.0))
    trim_grey = model.material("trim_grey", rgba=(0.21, 0.22, 0.24, 1.0))
    dark_grey = model.material("dark_grey", rgba=(0.16, 0.17, 0.18, 1.0))
    speaker_grey = model.material("speaker_grey", rgba=(0.30, 0.32, 0.34, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.07, 0.16, 0.20, 0.42))
    marquee_glow = model.material("marquee_glow", rgba=(0.82, 0.23, 0.20, 0.90))
    joystick_black = model.material("joystick_black", rgba=(0.08, 0.08, 0.09, 1.0))
    joystick_red = model.material("joystick_red", rgba=(0.78, 0.10, 0.11, 1.0))
    button_red = model.material("button_red", rgba=(0.74, 0.16, 0.15, 1.0))
    button_blue = model.material("button_blue", rgba=(0.16, 0.31, 0.70, 1.0))
    button_yellow = model.material("button_yellow", rgba=(0.83, 0.69, 0.16, 1.0))
    hinge_black = model.material("hinge_black", rgba=(0.07, 0.07, 0.08, 1.0))
    cashbox_grey = model.material("cashbox_grey", rgba=(0.36, 0.38, 0.40, 1.0))

    support_ring_mesh = _ring_mesh(
        SUPPORT_OUTER_RADIUS,
        SUPPORT_INNER_RADIUS,
        0.022,
        "arcade_joystick_support_ring",
    )
    cabinet = model.part("cabinet")

    cabinet.visual(
        Box((PANEL_THICKNESS, CABINET_DEPTH, LOWER_HEIGHT)),
        origin=Origin(xyz=(-CABINET_WIDTH / 2.0 + PANEL_THICKNESS / 2.0, 0.0, LOWER_HEIGHT / 2.0)),
        material=cabinet_black,
        name="left_side",
    )
    cabinet.visual(
        Box((PANEL_THICKNESS, CABINET_DEPTH, LOWER_HEIGHT)),
        origin=Origin(xyz=(CABINET_WIDTH / 2.0 - PANEL_THICKNESS / 2.0, 0.0, LOWER_HEIGHT / 2.0)),
        material=cabinet_black,
        name="right_side",
    )
    cabinet.visual(
        Box((CABINET_WIDTH - 2.0 * PANEL_THICKNESS, PANEL_THICKNESS, LOWER_HEIGHT)),
        origin=Origin(xyz=(0.0, REAR_Y, LOWER_HEIGHT / 2.0)),
        material=cabinet_black,
        name="rear_lower",
    )
    cabinet.visual(
        Box((CABINET_WIDTH - 2.0 * PANEL_THICKNESS, CABINET_DEPTH - 2.0 * PANEL_THICKNESS, PANEL_THICKNESS)),
        origin=Origin(
            xyz=(
                0.0,
                0.0,
                PANEL_THICKNESS / 2.0,
            )
        ),
        material=cabinet_black,
        name="floor",
    )
    cabinet.visual(
        Box((CABINET_WIDTH - 2.0 * PANEL_THICKNESS, 0.44, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.0, -0.18, LOWER_HEIGHT)),
        material=cabinet_black,
        name="lower_top_back",
    )
    cabinet.visual(
        Box((0.21, PANEL_THICKNESS, 0.82)),
        origin=Origin(xyz=(-0.275, FRONT_Y, 0.41)),
        material=cabinet_black,
        name="cashbox_frame_left",
    )
    cabinet.visual(
        Box((0.21, PANEL_THICKNESS, 0.82)),
        origin=Origin(xyz=(0.275, FRONT_Y, 0.41)),
        material=cabinet_black,
        name="cashbox_frame_right",
    )
    cabinet.visual(
        Box((DOOR_WIDTH, PANEL_THICKNESS, DOOR_BOTTOM)),
        origin=Origin(xyz=(0.0, FRONT_Y, DOOR_BOTTOM / 2.0)),
        material=cabinet_black,
        name="cashbox_frame_bottom",
    )
    cabinet.visual(
        Box((DOOR_WIDTH, PANEL_THICKNESS, 0.26)),
        origin=Origin(xyz=(0.0, FRONT_Y, 0.69)),
        material=cabinet_black,
        name="cashbox_frame_top",
    )
    cabinet.visual(
        Box((0.70, PANEL_THICKNESS, 0.12)),
        origin=Origin(xyz=(0.0, FRONT_Y, 0.88)),
        material=trim_grey,
        name="coin_tray_band",
    )
    cabinet.visual(
        Box((0.58, 0.40, TOTAL_HEIGHT - LOWER_HEIGHT)),
        origin=Origin(xyz=(0.0, -0.12, 1.335)),
        material=cabinet_black,
        name="upper_body",
    )
    cabinet.visual(
        Box((CABINET_WIDTH - 2.0 * PANEL_THICKNESS, PANEL_THICKNESS, TOTAL_HEIGHT - LOWER_HEIGHT)),
        origin=Origin(xyz=(0.0, -0.31, 1.335)),
        material=cabinet_black,
        name="rear_upper",
    )
    cabinet.visual(
        Box((CABINET_WIDTH - 2.0 * PANEL_THICKNESS, 0.40, PANEL_THICKNESS)),
        origin=Origin(xyz=(0.0, -0.12, TOTAL_HEIGHT - PANEL_THICKNESS / 2.0)),
        material=cabinet_black,
        name="roof",
    )
    cabinet.visual(
        _deck_panel_mesh(),
        origin=Origin(xyz=DECK_CENTER, rpy=(DECK_ROLL, 0.0, 0.0)),
        material=dark_grey,
        name="control_deck",
    )
    cabinet.visual(
        Box((0.74, 0.055, 0.11)),
        origin=Origin(xyz=(0.0, 0.27, 0.88), rpy=(DECK_ROLL, 0.0, 0.0)),
        material=trim_grey,
        name="deck_apron",
    )

    for index, (local_x, local_y) in enumerate(JOYSTICK_POSITIONS):
        cabinet.visual(
            support_ring_mesh,
            origin=Origin(
                xyz=_deck_point(local_x, local_y, 0.001),
                rpy=(DECK_ROLL, 0.0, 0.0),
            ),
            material=hinge_black,
            name=f"joystick_support_{index}",
        )

    button_layout = (
        ((-0.155, 0.028), button_red, "button_red_0"),
        ((-0.110, 0.052), button_blue, "button_blue_0"),
        ((-0.065, 0.074), button_yellow, "button_yellow_0"),
        ((0.065, 0.074), button_yellow, "button_yellow_1"),
        ((0.110, 0.052), button_blue, "button_blue_1"),
        ((0.155, 0.028), button_red, "button_red_1"),
    )
    for (local_x, local_y), material, name in button_layout:
        cabinet.visual(
            Cylinder(radius=0.016, length=0.018),
            origin=Origin(
                xyz=_deck_point(local_x, local_y, DECK_THICKNESS / 2.0 + 0.008),
                rpy=(DECK_ROLL, 0.0, 0.0),
            ),
            material=material,
            name=name,
        )

    start_button_positions = (-0.055, 0.055)
    for index, local_x in enumerate(start_button_positions):
        cabinet.visual(
            Cylinder(radius=0.011, length=0.010),
            origin=Origin(
                xyz=_deck_point(local_x, -0.090, DECK_THICKNESS / 2.0 + 0.004),
                rpy=(DECK_ROLL, 0.0, 0.0),
            ),
            material=speaker_grey,
            name=f"start_button_{index}",
        )

    cabinet.visual(
        Box((0.60, 0.032, 0.48)),
        origin=Origin(xyz=SCREEN_CENTER, rpy=(SCREEN_TILT, 0.0, 0.0)),
        material=trim_grey,
        name="screen_bezel",
    )
    cabinet.visual(
        Box((SCREEN_WIDTH, 0.010, SCREEN_HEIGHT)),
        origin=Origin(
            xyz=(
                SCREEN_CENTER[0],
                SCREEN_CENTER[1] + 0.007,
                SCREEN_CENTER[2] - 0.006,
            ),
            rpy=(SCREEN_TILT, 0.0, 0.0),
        ),
        material=screen_glass,
        name="screen_glass",
    )
    cabinet.visual(
        Box((0.60, 0.10, 0.16)),
        origin=Origin(xyz=MARQUEE_CENTER),
        material=cabinet_black,
        name="marquee_box",
    )
    cabinet.visual(
        Box((0.56, 0.012, 0.10)),
        origin=Origin(xyz=(0.0, 0.072, 1.585)),
        material=marquee_glow,
        name="marquee_face",
    )
    cabinet.visual(
        Box((0.22, PANEL_THICKNESS, 0.08)),
        origin=Origin(xyz=(-0.18, FRONT_Y, 0.87)),
        material=dark_grey,
        name="coin_mech_left",
    )
    cabinet.visual(
        Box((0.22, PANEL_THICKNESS, 0.08)),
        origin=Origin(xyz=(0.18, FRONT_Y, 0.87)),
        material=dark_grey,
        name="coin_mech_right",
    )
    cabinet.visual(
        Cylinder(radius=0.009, length=0.07),
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0 - 0.005, FRONT_Y, 0.37)),
        material=hinge_black,
        name="cashbox_hinge_mid",
    )

    cashbox_door = model.part("cashbox_door")
    cashbox_door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, -DOOR_THICKNESS / 2.0, DOOR_HEIGHT / 2.0)),
        material=cashbox_grey,
        name="door_panel",
    )
    cashbox_door.visual(
        Box((DOOR_WIDTH - 0.05, 0.006, DOOR_HEIGHT - 0.05)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, -0.003, DOOR_HEIGHT / 2.0)),
        material=trim_grey,
        name="door_inset",
    )
    cashbox_door.visual(
        Box((0.06, 0.010, 0.018)),
        origin=Origin(xyz=(0.23, -0.005, 0.13)),
        material=dark_grey,
        name="cashbox_pull",
    )
    cashbox_door.visual(
        Cylinder(radius=0.0065, length=0.11),
        origin=Origin(xyz=(0.0, -DOOR_THICKNESS / 2.0, 0.09)),
        material=hinge_black,
        name="hinge_lower",
    )
    cashbox_door.visual(
        Cylinder(radius=0.0065, length=0.11),
        origin=Origin(xyz=(0.0, -DOOR_THICKNESS / 2.0, DOOR_HEIGHT - 0.09)),
        material=hinge_black,
        name="hinge_upper",
    )

    model.articulation(
        "cabinet_to_cashbox_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=cashbox_door,
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, FRONT_Y + PANEL_THICKNESS / 2.0, DOOR_BOTTOM)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.4,
            lower=0.0,
            upper=math.radians(100.0),
        ),
    )

    for index, (local_x, local_y) in enumerate(JOYSTICK_POSITIONS):
        gimbal = model.part(f"joystick_gimbal_{index}")
        gimbal.visual(
            Box((0.024, 0.006, 0.020)),
            origin=Origin(xyz=(0.0, -0.015, 0.0)),
            material=hinge_black,
            name="rear_cheek",
        )
        gimbal.visual(
            Box((0.024, 0.006, 0.020)),
            origin=Origin(xyz=(0.0, 0.015, 0.0)),
            material=hinge_black,
            name="front_cheek",
        )
        gimbal.visual(
            Box((0.006, 0.036, 0.006)),
            origin=Origin(xyz=(0.015, 0.0, -0.013)),
            material=hinge_black,
            name="lower_bridge",
        )

        stick = model.part(f"joystick_{index}")
        stick.visual(
            Cylinder(radius=0.004, length=0.024),
            origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=joystick_black,
            name="trunnion",
        )
        stick.visual(
            Cylinder(radius=JOYSTICK_SHAFT_RADIUS, length=JOYSTICK_SHAFT_LENGTH),
            origin=Origin(xyz=(0.0, 0.0, JOYSTICK_SHAFT_LENGTH / 2.0)),
            material=joystick_black,
            name="shaft",
        )
        stick.visual(
            Sphere(radius=JOYSTICK_BALL_RADIUS),
            origin=Origin(xyz=(0.0, 0.0, JOYSTICK_SHAFT_LENGTH + JOYSTICK_BALL_RADIUS * 0.55)),
            material=joystick_red,
            name="ball",
        )
        stick.visual(
            Cylinder(radius=JOYSTICK_ACTUATOR_RADIUS, length=JOYSTICK_ACTUATOR_LENGTH),
            origin=Origin(xyz=(0.0, 0.0, -JOYSTICK_ACTUATOR_LENGTH / 2.0)),
            material=joystick_black,
            name="actuator",
        )

        pivot_xyz = _deck_point(local_x, local_y, JOYSTICK_PIVOT_LOCAL_Z)
        model.articulation(
            f"cabinet_to_joystick_gimbal_{index}",
            ArticulationType.REVOLUTE,
            parent=cabinet,
            child=gimbal,
            origin=Origin(xyz=pivot_xyz, rpy=(DECK_ROLL, 0.0, 0.0)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(
                effort=2.5,
                velocity=3.0,
                lower=-0.32,
                upper=0.32,
            ),
        )
        model.articulation(
            f"joystick_gimbal_{index}_to_joystick_{index}",
            ArticulationType.REVOLUTE,
            parent=gimbal,
            child=stick,
            origin=Origin(),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(
                effort=2.5,
                velocity=3.0,
                lower=-0.32,
                upper=0.32,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
