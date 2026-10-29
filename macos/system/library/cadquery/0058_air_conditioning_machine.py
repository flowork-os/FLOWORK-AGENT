# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_conditioning_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_conditioning_machine

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
import cadquery as cq
BODY_WIDTH = 0.44
BODY_DEPTH = 0.36
BODY_HEIGHT = 0.79
BODY_WALL = 0.004
TOP_WALL = 0.020
BOTTOM_EXTENSION = 0.015
CORNER_RADIUS = 0.050
TOP_EDGE_RADIUS = 0.016
TOP_VENT_WIDTH = 0.240
TOP_VENT_DEPTH = 0.095
TOP_VENT_CENTER_Y = 0.035
TOP_VENT_HINGE_Y = TOP_VENT_CENTER_Y + TOP_VENT_DEPTH / 2.0 + 0.006
VENT_DOOR_WIDTH = TOP_VENT_WIDTH + 0.024
VENT_DOOR_DEPTH = TOP_VENT_DEPTH + 0.030
VENT_DOOR_THICKNESS = 0.005
VENT_DOOR_STANDOFF = 0.0
SERVICE_PANEL_WIDTH = 0.145
SERVICE_PANEL_HEIGHT = 0.245
SERVICE_PANEL_THICKNESS = 0.005
SERVICE_PANEL_BOTTOM_Z = 0.105
SERVICE_PANEL_REAR_Y = BODY_DEPTH / 2.0 - 0.026
SERVICE_PANEL_STANDOFF = 0.0
def _rounded_tower(width: float, depth: float, height: float, corner_radius: float, top_radius: float):
    shape = cq.Workplane("XY").box(width, depth, height, centered=(True, True, False))
    shape = shape.edges("|Z").fillet(corner_radius)
    shape = shape.edges(">Z").fillet(top_radius)
    return shape
def _box_at(
    size_x: float,
    size_y: float,
    size_z: float,
    *,
    center_x: float,
    center_y: float,
    bottom_z: float,
):
    return (
        cq.Workplane("XY")
        .box(size_x, size_y, size_z, centered=(True, True, False))
        .translate((center_x, center_y, bottom_z))
    )
def _build_housing_shape():
    outer = _rounded_tower(BODY_WIDTH, BODY_DEPTH, BODY_HEIGHT, CORNER_RADIUS, TOP_EDGE_RADIUS)
    inner = _rounded_tower(
        BODY_WIDTH - 2.0 * BODY_WALL,
        BODY_DEPTH - 2.0 * BODY_WALL,
        BODY_HEIGHT - TOP_WALL + BOTTOM_EXTENSION,
        max(CORNER_RADIUS - BODY_WALL, 0.006),
        max(TOP_EDGE_RADIUS - BODY_WALL, 0.004),
    ).translate((0.0, 0.0, -BOTTOM_EXTENSION))
    housing = outer.cut(inner)

    control_pocket = _box_at(
        0.155,
        0.058,
        0.0028,
        center_x=0.0,
        center_y=-0.088,
        bottom_z=BODY_HEIGHT - 0.0028,
    )
    housing = housing.cut(control_pocket)

    vent_recess = (
        _box_at(
            VENT_DOOR_WIDTH,
            TOP_VENT_DEPTH + 0.020,
            0.0035,
            center_x=0.0,
            center_y=TOP_VENT_CENTER_Y,
            bottom_z=BODY_HEIGHT - 0.0035,
        )
    )
    housing = housing.cut(vent_recess)
    for slot_offset in (-0.030, -0.010, 0.010, 0.030):
        vent_slot = _box_at(
            TOP_VENT_WIDTH - 0.028,
            0.010,
            TOP_WALL + 0.010,
            center_x=0.0,
            center_y=TOP_VENT_CENTER_Y + slot_offset,
            bottom_z=BODY_HEIGHT - TOP_WALL - 0.002,
        )
        housing = housing.cut(vent_slot)

    slot_width = BODY_WIDTH - 0.120
    slot_depth = BODY_WALL * 8.0
    slot_height = 0.010
    for index in range(11):
        slot_z = 0.170 + index * 0.024
        slot = (
            cq.Workplane("XY")
            .box(slot_width, slot_depth, slot_height, centered=(True, True, True))
            .translate((0.0, -BODY_DEPTH / 2.0 + slot_depth / 2.0, slot_z))
        )
        housing = housing.cut(slot)

    access_opening_width = SERVICE_PANEL_WIDTH - 0.022
    access_opening_height = SERVICE_PANEL_HEIGHT - 0.028
    access_opening_center_y = SERVICE_PANEL_REAR_Y - 0.010 - access_opening_width / 2.0
    access_opening = (
        cq.Workplane("XY")
        .box(0.020, access_opening_width, access_opening_height, centered=(False, True, False))
        .translate((BODY_WIDTH / 2.0 - 0.012, access_opening_center_y, SERVICE_PANEL_BOTTOM_Z + 0.012))
    )
    housing = housing.cut(access_opening)

    exhaust_hole = (
        cq.Workplane("XY")
        .cylinder(0.045, 0.072, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((0.0, BODY_DEPTH / 2.0 - 0.010, 0.515))
    )
    housing = housing.cut(exhaust_hole)

    return housing
def _build_vent_door_shape():
    panel = (
        cq.Workplane("XY")
        .box(VENT_DOOR_WIDTH, VENT_DOOR_DEPTH, VENT_DOOR_THICKNESS, centered=(True, False, False))
        .translate((0.0, -VENT_DOOR_DEPTH, 0.0))
        .edges("|Z")
        .fillet(0.0018)
        .edges("<Y")
        .fillet(0.0012)
    )
    front_lip = (
        cq.Workplane("XY")
        .box(VENT_DOOR_WIDTH - 0.050, 0.010, 0.008, centered=(True, False, False))
        .translate((0.0, -VENT_DOOR_DEPTH - 0.010, 0.0))
        .edges("|Z")
        .fillet(0.0015)
    )
    return panel.union(front_lip)
def _build_service_panel_shape():
    panel = (
        cq.Workplane("XY")
        .box(
            SERVICE_PANEL_THICKNESS,
            SERVICE_PANEL_WIDTH,
            SERVICE_PANEL_HEIGHT,
            centered=(False, False, False),
        )
        .translate((0.0, -SERVICE_PANEL_WIDTH, 0.0))
        .edges("|Z")
        .fillet(0.0018)
    )
    finger_pull = (
        cq.Workplane("XY")
        .cylinder(0.020, 0.012, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((SERVICE_PANEL_THICKNESS - 0.002, -SERVICE_PANEL_WIDTH + 0.016, SERVICE_PANEL_HEIGHT * 0.55))
    )
    return panel.cut(finger_pull)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_air_conditioner")

    housing_white = model.material("housing_white", rgba=(0.91, 0.92, 0.90, 1.0))
    panel_white = model.material("panel_white", rgba=(0.95, 0.95, 0.94, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_build_housing_shape(), "portable_ac_housing"),
        material=housing_white,
        name="housing_shell",
    )

    vent_door = model.part("vent_door")
    vent_door.visual(
        mesh_from_cadquery(_build_vent_door_shape(), "portable_ac_vent_door"),
        material=panel_white,
        name="door_leaf",
    )

    service_panel = model.part("service_panel")
    service_panel.visual(
        mesh_from_cadquery(_build_service_panel_shape(), "portable_ac_service_panel"),
        material=panel_white,
        name="panel_cover",
    )

    model.articulation(
        "top_vent_hinge",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=vent_door,
        origin=Origin(xyz=(0.0, TOP_VENT_HINGE_Y, BODY_HEIGHT + VENT_DOOR_STANDOFF)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.20, effort=12.0, velocity=1.4),
    )
    model.articulation(
        "service_panel_hinge",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=service_panel,
        origin=Origin(
            xyz=(
                BODY_WIDTH / 2.0 + SERVICE_PANEL_STANDOFF,
                SERVICE_PANEL_REAR_Y,
                SERVICE_PANEL_BOTTOM_Z,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.55, effort=10.0, velocity=1.2),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
