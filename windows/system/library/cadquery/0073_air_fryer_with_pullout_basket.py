# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_fryer_with_pullout_basket, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_fryer_with_pullout_basket

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
HOUSING_DEPTH = 0.370
HOUSING_WIDTH = 0.310
HOUSING_HEIGHT = 0.360
HOUSING_WALL = 0.012
OPENING_Z = 0.115
DRAWER_JOINT_X = 0.167
CHAMBER_DEPTH = 0.252
CHAMBER_WIDTH = 0.252
CHAMBER_HEIGHT = 0.138
CHAMBER_WALL = 0.004
DRAWER_DEPTH = 0.236
DRAWER_WIDTH = 0.236
DRAWER_HEIGHT = 0.126
DRAWER_WALL = 0.0045
DRAWER_FRONT_THICKNESS = 0.018
BASKET_DEPTH = 0.214
BASKET_WIDTH = 0.214
BASKET_HEIGHT = 0.094
BASKET_WALL = 0.003
DRAWER_TRAVEL = 0.118
PANEL_PITCH = 0.42
PANEL_CENTER = (0.066, 0.0, 0.311)
PANEL_SIZE = (0.172, 0.228, 0.018)
def _rot_y(local_xyz: tuple[float, float, float], angle: float) -> tuple[float, float, float]:
    x, y, z = local_xyz
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (x * cos_a + z * sin_a, y, -x * sin_a + z * cos_a)
def _panel_world(local_xyz: tuple[float, float, float]) -> tuple[float, float, float]:
    rx, ry, rz = _rot_y(local_xyz, PANEL_PITCH)
    return (PANEL_CENTER[0] + rx, PANEL_CENTER[1] + ry, PANEL_CENTER[2] + rz)
def _build_housing_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .box(HOUSING_DEPTH, HOUSING_WIDTH, HOUSING_HEIGHT)
        .translate((0.0, 0.0, HOUSING_HEIGHT * 0.5))
        .edges("|Z")
        .fillet(0.042)
        .edges(">Z")
        .fillet(0.016)
    )
    inner = (
        cq.Workplane("XY")
        .box(
            HOUSING_DEPTH - 2.0 * HOUSING_WALL,
            HOUSING_WIDTH - 2.0 * HOUSING_WALL,
            HOUSING_HEIGHT - 0.028,
        )
        .translate((-0.008, 0.0, HOUSING_HEIGHT * 0.5 + 0.006))
    )
    shell = outer.cut(inner)

    opening = (
        cq.Workplane("XY")
        .box(0.090, 0.254, 0.148)
        .translate((HOUSING_DEPTH * 0.5 - 0.045, 0.0, OPENING_Z))
    )
    shell = shell.cut(opening)

    for slot_y in (-0.090, -0.060, -0.030, 0.030, 0.060, 0.090):
        vent_slot = (
            cq.Workplane("XY")
            .box(0.082, 0.007, 0.016)
            .translate((-0.118, slot_y, 0.268))
        )
        shell = shell.cut(vent_slot)

    return shell
def _build_control_panel() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(*PANEL_SIZE)
        .edges("|Z")
        .fillet(0.010)
    )

    for local_y in (-0.060, 0.060):
        dial_well = (
            cq.Workplane("XY")
            .box(0.062, 0.062, 0.010)
            .translate((0.022, local_y, 0.004))
        )
        panel = panel.cut(dial_well)

    for local_y in (-0.024, 0.024):
        pocket = (
            cq.Workplane("XY")
            .box(0.032, 0.022, 0.012)
            .translate((-0.042, local_y, 0.003))
        )
        panel = panel.cut(pocket)

    return panel
def _build_basket_floor() -> cq.Workplane:
    floor = (
        cq.Workplane("XY")
        .box(BASKET_DEPTH - 0.006, BASKET_WIDTH - 0.006, BASKET_WALL)
        .translate((-BASKET_DEPTH * 0.5, 0.0, -BASKET_HEIGHT * 0.5 + BASKET_WALL * 0.5))
    )
    for hole_x in (-0.178, -0.146, -0.114, -0.082, -0.050):
        for hole_y in (-0.072, -0.036, 0.0, 0.036, 0.072):
            hole = (
                cq.Workplane("XY")
                .box(0.012, 0.012, 0.010)
                .translate((hole_x, hole_y, -BASKET_HEIGHT * 0.5 + BASKET_WALL * 0.5))
            )
            floor = floor.cut(hole)
    return floor
def _build_basket_side(sign: float) -> cq.Workplane:
    wall = (
        cq.Workplane("XY")
        .box(BASKET_DEPTH - 0.010, BASKET_WALL, BASKET_HEIGHT - 2.0 * BASKET_WALL)
        .translate((-BASKET_DEPTH * 0.5, sign * (BASKET_WIDTH * 0.5 - BASKET_WALL * 0.5), 0.0))
    )
    for slot_x in (-0.166, -0.130, -0.094, -0.058):
        for slot_z in (-0.014, 0.012):
            slot = (
                cq.Workplane("XY")
                .box(0.020, 0.010, 0.012)
                .translate((slot_x, sign * (BASKET_WIDTH * 0.5 - BASKET_WALL * 0.5), slot_z))
            )
            wall = wall.cut(slot)
    return wall
def _build_basket_rear() -> cq.Workplane:
    wall = (
        cq.Workplane("XY")
        .box(BASKET_WALL, BASKET_WIDTH - 0.014, BASKET_HEIGHT - 2.0 * BASKET_WALL)
        .translate((-BASKET_DEPTH + BASKET_WALL * 0.5, 0.0, 0.0))
    )
    for slot_y in (-0.070, -0.035, 0.0, 0.035, 0.070):
        slot = (
            cq.Workplane("XY")
            .box(0.010, 0.018, 0.012)
            .translate((-BASKET_DEPTH + BASKET_WALL * 0.5, slot_y, -0.004))
        )
        wall = wall.cut(slot)
    return wall
def _build_basket_handle() -> cq.Workplane:
    arm_left = (
        cq.Workplane("XY")
        .box(0.044, 0.018, 0.010)
        .translate((0.018, 0.028, 0.006))
    )
    arm_right = (
        cq.Workplane("XY")
        .box(0.044, 0.018, 0.010)
        .translate((0.018, -0.028, 0.006))
    )
    body = (
        cq.Workplane("XY")
        .box(0.052, 0.084, 0.018)
        .translate((0.058, 0.0, 0.010))
    )
    button_recess = (
        cq.Workplane("XY")
        .box(0.026, 0.040, 0.014)
        .translate((0.058, 0.0, 0.012))
    )
    return arm_left.union(arm_right).union(body.cut(button_recess))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="basket_air_fryer")

    housing_plastic = model.material("housing_plastic", rgba=(0.12, 0.12, 0.13, 1.0))
    panel_black = model.material("panel_black", rgba=(0.06, 0.06, 0.07, 1.0))
    drawer_plastic = model.material("drawer_plastic", rgba=(0.15, 0.15, 0.16, 1.0))
    basket_metal = model.material("basket_metal", rgba=(0.34, 0.36, 0.38, 1.0))
    chamber_metal = model.material("chamber_metal", rgba=(0.58, 0.59, 0.60, 1.0))
    rubber_dark = model.material("rubber_dark", rgba=(0.07, 0.07, 0.08, 1.0))
    button_grey = model.material("button_grey", rgba=(0.82, 0.83, 0.84, 1.0))
    safety_red = model.material("safety_red", rgba=(0.74, 0.16, 0.12, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_build_housing_shell(), "housing_shell"),
        material=housing_plastic,
        name="body_shell",
    )
    housing.visual(
        mesh_from_cadquery(_build_control_panel(), "control_panel"),
        origin=Origin(xyz=PANEL_CENTER, rpy=(0.0, PANEL_PITCH, 0.0)),
        material=panel_black,
        name="control_panel",
    )
    for index, (foot_x, foot_y) in enumerate(
        (
            (-0.125, -0.105),
            (-0.125, 0.105),
            (0.090, -0.105),
            (0.090, 0.105),
        )
    ):
        housing.visual(
            Cylinder(radius=0.012, length=0.010),
            origin=Origin(
                xyz=(foot_x, foot_y, 0.005),
                rpy=(math.pi * 0.5, 0.0, 0.0),
            ),
            material=rubber_dark,
            name=f"foot_{index}",
        )

    chamber = model.part("chamber")
    chamber.visual(
        Box((CHAMBER_DEPTH, CHAMBER_WIDTH, CHAMBER_WALL)),
        origin=Origin(xyz=(-CHAMBER_DEPTH * 0.5, 0.0, -CHAMBER_HEIGHT * 0.5 + CHAMBER_WALL * 0.5)),
        material=chamber_metal,
        name="chamber_floor",
    )
    chamber.visual(
        Box((CHAMBER_DEPTH, CHAMBER_WALL, CHAMBER_HEIGHT)),
        origin=Origin(xyz=(-CHAMBER_DEPTH * 0.5, CHAMBER_WIDTH * 0.5 - CHAMBER_WALL * 0.5, 0.0)),
        material=chamber_metal,
        name="chamber_side_0",
    )
    chamber.visual(
        Box((CHAMBER_DEPTH, CHAMBER_WALL, CHAMBER_HEIGHT)),
        origin=Origin(xyz=(-CHAMBER_DEPTH * 0.5, -CHAMBER_WIDTH * 0.5 + CHAMBER_WALL * 0.5, 0.0)),
        material=chamber_metal,
        name="chamber_side_1",
    )
    chamber.visual(
        Box((CHAMBER_WALL, CHAMBER_WIDTH, CHAMBER_HEIGHT)),
        origin=Origin(xyz=(-CHAMBER_DEPTH + CHAMBER_WALL * 0.5, 0.0, 0.0)),
        material=chamber_metal,
        name="chamber_rear",
    )
    chamber.visual(
        Box((CHAMBER_DEPTH, CHAMBER_WIDTH, CHAMBER_WALL)),
        origin=Origin(xyz=(-CHAMBER_DEPTH * 0.5, 0.0, CHAMBER_HEIGHT * 0.5 - CHAMBER_WALL * 0.5)),
        material=chamber_metal,
        name="chamber_ceiling",
    )
    model.articulation(
        "housing_to_chamber",
        ArticulationType.FIXED,
        parent=housing,
        child=chamber,
        origin=Origin(xyz=(DRAWER_JOINT_X, 0.0, OPENING_Z)),
    )

    drawer = model.part("drawer")
    drawer.visual(
        Box((DRAWER_DEPTH, DRAWER_WIDTH, DRAWER_WALL)),
        origin=Origin(xyz=(-DRAWER_DEPTH * 0.5, 0.0, -DRAWER_HEIGHT * 0.5 + DRAWER_WALL * 0.5)),
        material=drawer_plastic,
        name="drawer_floor",
    )
    drawer.visual(
        Box((DRAWER_DEPTH, DRAWER_WALL, DRAWER_HEIGHT)),
        origin=Origin(xyz=(-DRAWER_DEPTH * 0.5, DRAWER_WIDTH * 0.5 - DRAWER_WALL * 0.5, 0.0)),
        material=drawer_plastic,
        name="drawer_side_0",
    )
    drawer.visual(
        Box((DRAWER_DEPTH, DRAWER_WALL, DRAWER_HEIGHT)),
        origin=Origin(xyz=(-DRAWER_DEPTH * 0.5, -DRAWER_WIDTH * 0.5 + DRAWER_WALL * 0.5, 0.0)),
        material=drawer_plastic,
        name="drawer_side_1",
    )
    drawer.visual(
        Box((DRAWER_WALL, DRAWER_WIDTH, DRAWER_HEIGHT)),
        origin=Origin(xyz=(-DRAWER_DEPTH + DRAWER_WALL * 0.5, 0.0, 0.0)),
        material=drawer_plastic,
        name="drawer_rear",
    )
    drawer.visual(
        Box((DRAWER_WALL, DRAWER_WIDTH, 0.070)),
        origin=Origin(xyz=(-DRAWER_WALL * 0.5, 0.0, -0.028)),
        material=drawer_plastic,
        name="drawer_front_lower",
    )
    drawer.visual(
        Box((DRAWER_WALL, 0.076, 0.048)),
        origin=Origin(xyz=(-DRAWER_WALL * 0.5, -0.090, 0.016)),
        material=drawer_plastic,
        name="drawer_front_cheek_0",
    )
    drawer.visual(
        Box((DRAWER_WALL, 0.076, 0.048)),
        origin=Origin(xyz=(-DRAWER_WALL * 0.5, 0.090, 0.016)),
        material=drawer_plastic,
        name="drawer_front_cheek_1",
    )
    drawer.visual(
        Box((DRAWER_FRONT_THICKNESS, 0.258, 0.074)),
        origin=Origin(xyz=(0.029, 0.0, -0.038)),
        material=drawer_plastic,
        name="drawer_front_lower_panel",
    )
    drawer.visual(
        Box((DRAWER_FRONT_THICKNESS, 0.258, 0.050)),
        origin=Origin(xyz=(0.029, 0.0, 0.050)),
        material=drawer_plastic,
        name="drawer_front_upper_panel",
    )
    drawer.visual(
        Box((DRAWER_FRONT_THICKNESS, 0.077, 0.048)),
        origin=Origin(xyz=(0.029, -0.0905, 0.016)),
        material=drawer_plastic,
        name="drawer_front_panel_0",
    )
    drawer.visual(
        Box((DRAWER_FRONT_THICKNESS, 0.077, 0.048)),
        origin=Origin(xyz=(0.029, 0.0905, 0.016)),
        material=drawer_plastic,
        name="drawer_front_panel_1",
    )
    drawer.visual(
        Box((0.024, 0.140, 0.036)),
        origin=Origin(xyz=(0.010, 0.0, -0.034)),
        material=drawer_plastic,
        name="drawer_front_mount_0",
    )
    drawer.visual(
        Box((0.024, 0.086, 0.024)),
        origin=Origin(xyz=(0.010, -0.0905, 0.016)),
        material=drawer_plastic,
        name="drawer_front_mount_1",
    )
    drawer.visual(
        Box((0.024, 0.086, 0.024)),
        origin=Origin(xyz=(0.010, 0.0905, 0.016)),
        material=drawer_plastic,
        name="drawer_front_mount_2",
    )
    drawer.visual(
        Box((0.030, 0.018, 0.032)),
        origin=Origin(xyz=(0.050, -0.055, -0.020)),
        material=drawer_plastic,
        name="handle_post_0",
    )
    drawer.visual(
        Box((0.030, 0.018, 0.032)),
        origin=Origin(xyz=(0.050, 0.055, -0.020)),
        material=drawer_plastic,
        name="handle_post_1",
    )
    drawer.visual(
        Box((0.034, 0.100, 0.012)),
        origin=Origin(xyz=(0.056, 0.0, -0.008)),
        material=drawer_plastic,
        name="handle_bridge",
    )
    drawer_joint = model.articulation(
        "housing_to_drawer",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=drawer,
        origin=Origin(xyz=(DRAWER_JOINT_X, 0.0, OPENING_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=60.0,
            velocity=0.35,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )

    basket = model.part("basket")
    basket.visual(
        mesh_from_cadquery(_build_basket_floor(), "basket_floor"),
        material=basket_metal,
        name="basket_floor",
    )
    basket.visual(
        mesh_from_cadquery(_build_basket_side(1.0), "basket_side_0"),
        material=basket_metal,
        name="basket_side_0",
    )
    basket.visual(
        mesh_from_cadquery(_build_basket_side(-1.0), "basket_side_1"),
        material=basket_metal,
        name="basket_side_1",
    )
    basket.visual(
        mesh_from_cadquery(_build_basket_rear(), "basket_rear"),
        material=basket_metal,
        name="basket_rear",
    )
    basket.visual(
        Box((BASKET_WALL, BASKET_WIDTH, 0.078)),
        origin=Origin(xyz=(-BASKET_WALL * 0.5, 0.0, -0.005)),
        material=basket_metal,
        name="basket_front",
    )
    for index, (foot_x, foot_y) in enumerate(
        (
            (-0.174, -0.074),
            (-0.174, 0.074),
            (-0.058, -0.074),
            (-0.058, 0.074),
        )
    ):
        basket.visual(
            Box((0.014, 0.014, 0.016)),
            origin=Origin(xyz=(foot_x, foot_y, -BASKET_HEIGHT * 0.5 - 0.008)),
            material=basket_metal,
            name=f"basket_foot_{index}",
        )
    basket.visual(
        mesh_from_cadquery(_build_basket_handle(), "basket_handle"),
        material=drawer_plastic,
        name="basket_handle",
    )
    model.articulation(
        "drawer_to_basket",
        ArticulationType.FIXED,
        parent=drawer,
        child=basket,
        origin=Origin(),
    )

    release_button = model.part("release_button")
    release_button.visual(
        Box((0.022, 0.034, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material=safety_red,
        name="release_button",
    )
    model.articulation(
        "basket_to_release_button",
        ArticulationType.PRISMATIC,
        parent=basket,
        child=release_button,
        origin=Origin(xyz=(0.058, 0.0, 0.005)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=0.08,
            lower=0.0,
            upper=0.004,
        ),
    )

    for dial_name, local_y in (("temp_dial", -0.060), ("time_dial", 0.060)):
        dial = model.part(dial_name)
        dial.visual(
            Cylinder(radius=0.028, length=0.010),
            origin=Origin(xyz=(0.0, 0.0, 0.005)),
            material=button_grey,
            name="dial_skirt",
        )
        dial.visual(
            Cylinder(radius=0.022, length=0.016),
            origin=Origin(xyz=(0.0, 0.0, 0.013)),
            material=drawer_plastic,
            name="dial_cap",
        )
        dial.visual(
            Cylinder(radius=0.010, length=0.010),
            origin=Origin(xyz=(0.0, 0.0, -0.005)),
            material=drawer_plastic,
            name="dial_hub",
        )
        dial.visual(
            Box((0.014, 0.004, 0.004)),
            origin=Origin(xyz=(0.012, 0.0, 0.020)),
            material=safety_red if dial_name == "temp_dial" else panel_black,
            name="dial_indicator",
        )
        model.articulation(
            f"housing_to_{dial_name}",
            ArticulationType.CONTINUOUS,
            parent=housing,
            child=dial,
            origin=Origin(
                xyz=_panel_world((0.022, local_y, PANEL_SIZE[2] * 0.5 - 0.003)),
                rpy=(0.0, PANEL_PITCH, 0.0),
            ),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(
                effort=0.12,
                velocity=6.0,
            ),
        )

    for button_name, local_y in (("preset_button_0", -0.024), ("preset_button_1", 0.024)):
        button = model.part(button_name)
        button.visual(
            Box((0.026, 0.018, 0.008)),
            origin=Origin(xyz=(0.0, 0.0, 0.004)),
            material=button_grey,
            name="button_cap",
        )
        button.visual(
            Box((0.016, 0.010, 0.006)),
            origin=Origin(xyz=(0.0, 0.0, -0.003)),
            material=button_grey,
            name="button_stem",
        )
        model.articulation(
            f"housing_to_{button_name}",
            ArticulationType.PRISMATIC,
            parent=housing,
            child=button,
            origin=Origin(
                xyz=_panel_world((-0.042, local_y, PANEL_SIZE[2] * 0.5 - 0.006)),
                rpy=(0.0, PANEL_PITCH, 0.0),
            ),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=5.0,
                velocity=0.08,
                lower=0.0,
                upper=0.004,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
