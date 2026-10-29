# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_RADIUS = 0.145
BASE_RADIUS = 0.150
BODY_HEIGHT = 0.520
BASE_HEIGHT = 0.018
SHELL_THICKNESS = 0.0035
REAR_FLAT = 0.095
REAR_PLANE_Y = -REAR_FLAT
TOP_SHOULDER_HEIGHT = 0.008
TOP_SHOULDER_OUTER_RADIUS = 0.128
TOP_SHOULDER_INNER_RADIUS = 0.099
VENT_RADIUS = 0.100
DOOR_OPENING_WIDTH = 0.194
DOOR_OPENING_HEIGHT = 0.370
DOOR_WIDTH = 0.208
DOOR_HEIGHT = 0.388
DOOR_THICKNESS = 0.005
DOOR_BOTTOM_Z = 0.074
HINGE_X = DOOR_WIDTH * 0.5 + 0.004
HINGE_Y = REAR_PLANE_Y - 0.004
HINGE_Z = DOOR_BOTTOM_Z + DOOR_HEIGHT * 0.5
FILTER_RADIUS = 0.093
FILTER_INNER_RADIUS = 0.062
FILTER_HEIGHT = 0.340
FILTER_CENTER_Y = 0.020
FILTER_JOINT_Y = REAR_PLANE_Y + SHELL_THICKNESS
FILTER_LOCAL_CENTER_Y = FILTER_CENTER_Y - FILTER_JOINT_Y
FILTER_TRAVEL = 0.110
RING_OUTER_RADIUS = 0.122
RING_INNER_RADIUS = 0.104
RING_HEIGHT = 0.016
RING_CENTER_Z = BODY_HEIGHT + RING_HEIGHT * 0.5
def _flat_keep_box(radius: float, height: float, rear_flat: float) -> cq.Workplane:
    front_extent = radius + 0.030
    y_size = front_extent + rear_flat
    y_center = (front_extent - rear_flat) * 0.5
    return (
        cq.Workplane("XY")
        .box(radius * 2.6, y_size, height, centered=(True, True, True))
        .translate((0.0, y_center, height * 0.5))
    )
def _vertical_cylinder(radius: float, height: float, *, x: float, y: float, z0: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((x, y, z0))
def _build_body_shape() -> cq.Workplane:
    main_shell = cq.Workplane("XY").circle(BODY_RADIUS).extrude(BODY_HEIGHT - TOP_SHOULDER_HEIGHT)
    main_shell = main_shell.intersect(_flat_keep_box(BODY_RADIUS, BODY_HEIGHT - TOP_SHOULDER_HEIGHT, REAR_FLAT))

    base = cq.Workplane("XY").circle(BASE_RADIUS).extrude(BASE_HEIGHT)
    base = base.intersect(_flat_keep_box(BASE_RADIUS, BASE_HEIGHT, REAR_FLAT))

    cavity = (
        cq.Workplane("XY")
        .circle(BODY_RADIUS - SHELL_THICKNESS)
        .extrude(BODY_HEIGHT - TOP_SHOULDER_HEIGHT - BASE_HEIGHT - 0.006)
        .translate((0.0, 0.0, BASE_HEIGHT))
    )
    cavity = cavity.intersect(
        _flat_keep_box(BODY_RADIUS - SHELL_THICKNESS, BODY_HEIGHT, REAR_FLAT - SHELL_THICKNESS)
    )

    housing = main_shell.union(base).cut(cavity)

    top_shoulder = (
        cq.Workplane("XY")
        .workplane(offset=BODY_HEIGHT - TOP_SHOULDER_HEIGHT)
        .circle(TOP_SHOULDER_OUTER_RADIUS)
        .circle(TOP_SHOULDER_INNER_RADIUS)
        .extrude(TOP_SHOULDER_HEIGHT)
    )

    vent = cq.Workplane("XY").workplane(offset=BODY_HEIGHT - 0.006).circle(VENT_RADIUS).extrude(0.006)
    vent = vent.cut(cq.Workplane("XY").workplane(offset=BODY_HEIGHT - 0.007).circle(0.021).extrude(0.008))
    for angle_deg in range(0, 360, 45):
        slot = (
            cq.Workplane("XY")
            .box(0.012, 0.046, 0.010, centered=(True, True, True))
            .translate((0.043, 0.0, BODY_HEIGHT - 0.002))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        )
        vent = vent.cut(slot)
    for angle_deg in (22.5, 67.5, 112.5, 157.5):
        spoke = (
            cq.Workplane("XY")
            .box(0.006, 0.130, 0.006, centered=(True, True, True))
            .translate((0.0, 0.0, BODY_HEIGHT - 0.003))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        )
        vent = vent.union(spoke)

    housing = housing.union(top_shoulder).union(vent)

    rear_opening = (
        cq.Workplane("XY")
        .box(DOOR_OPENING_WIDTH, 0.050, DOOR_OPENING_HEIGHT, centered=(True, True, True))
        .translate((0.0, REAR_PLANE_Y + 0.025, HINGE_Z))
    )
    housing = housing.cut(rear_opening)

    top_stop = (
        cq.Workplane("XY")
        .box(0.086, 0.005, 0.012, centered=(True, True, True))
        .translate((0.0, REAR_PLANE_Y, HINGE_Z + DOOR_OPENING_HEIGHT * 0.5 + 0.011))
    )
    bottom_stop = (
        cq.Workplane("XY")
        .box(0.086, 0.005, 0.012, centered=(True, True, True))
        .translate((0.0, REAR_PLANE_Y, HINGE_Z - DOOR_OPENING_HEIGHT * 0.5 - 0.011))
    )
    rail_z_center = (0.106 + BASE_HEIGHT) * 0.5
    rail_height = 0.106 - BASE_HEIGHT
    left_rail = (
        cq.Workplane("XY")
        .box(0.018, 0.230, rail_height, centered=(True, True, True))
        .translate((-0.073, 0.015, rail_z_center))
    )
    right_rail = (
        cq.Workplane("XY")
        .box(0.018, 0.230, rail_height, centered=(True, True, True))
        .translate((0.073, 0.015, rail_z_center))
    )
    housing = (
        housing.union(top_stop)
        .union(bottom_stop)
        .union(left_rail)
        .union(right_rail)
    )

    return housing
def _build_door_shape() -> cq.Workplane:
    panel_center_y = -0.001
    panel = (
        cq.Workplane("XY")
        .box(DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT, centered=(True, True, True))
        .translate((-DOOR_WIDTH * 0.5 - 0.006, panel_center_y, 0.0))
    )

    stile = (
        cq.Workplane("XY")
        .box(0.008, 0.008, DOOR_HEIGHT, centered=(True, True, True))
        .translate((-0.004, -0.001, 0.0))
    )

    pull = (
        cq.Workplane("XY")
        .box(0.022, 0.008, 0.120, centered=(True, True, True))
        .translate((-DOOR_WIDTH + 0.028, -0.005, 0.0))
    )
    return panel.union(stile).union(pull)
def _build_filter_shape() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .circle(FILTER_RADIUS)
        .extrude(FILTER_HEIGHT)
        .translate((0.0, FILTER_LOCAL_CENTER_Y, -FILTER_HEIGHT * 0.5))
    )
    outer = outer.cut(
        cq.Workplane("XY")
        .circle(FILTER_INNER_RADIUS)
        .extrude(FILTER_HEIGHT + 0.004)
        .translate((0.0, FILTER_LOCAL_CENTER_Y, -FILTER_HEIGHT * 0.5 - 0.002))
    )

    groove_cutter = (
        cq.Workplane("XY")
        .box(0.008, 0.028, FILTER_HEIGHT + 0.008, centered=(True, True, True))
        .translate((FILTER_RADIUS - 0.004, FILTER_LOCAL_CENTER_Y, 0.0))
    )
    for angle_deg in range(0, 360, 15):
        outer = outer.cut(
            groove_cutter.rotate(
                (0.0, FILTER_LOCAL_CENTER_Y, 0.0),
                (0.0, FILTER_LOCAL_CENTER_Y, 1.0),
                angle_deg,
            )
        )

    top_cap = _vertical_cylinder(
        FILTER_RADIUS,
        0.010,
        x=0.0,
        y=FILTER_LOCAL_CENTER_Y,
        z0=FILTER_HEIGHT * 0.5 - 0.010,
    )
    top_cap = top_cap.cut(
        _vertical_cylinder(
            FILTER_INNER_RADIUS,
            0.012,
            x=0.0,
            y=FILTER_LOCAL_CENTER_Y,
            z0=FILTER_HEIGHT * 0.5 - 0.011,
        )
    )

    bottom_cap = _vertical_cylinder(
        FILTER_RADIUS,
        0.010,
        x=0.0,
        y=FILTER_LOCAL_CENTER_Y,
        z0=-FILTER_HEIGHT * 0.5,
    )
    bottom_cap = bottom_cap.cut(
        _vertical_cylinder(
            FILTER_INNER_RADIUS,
            0.012,
            x=0.0,
            y=FILTER_LOCAL_CENTER_Y,
            z0=-FILTER_HEIGHT * 0.5 - 0.001,
        )
    )

    handle = (
        cq.Workplane("XY")
        .box(0.060, 0.014, 0.080, centered=(True, True, True))
        .translate((0.0, FILTER_LOCAL_CENTER_Y - FILTER_RADIUS + 0.010, 0.0))
    )

    return outer.union(top_cap).union(bottom_cap).union(handle)
def _build_control_ring_shape() -> cq.Workplane:
    ring = cq.Workplane("XY").circle(RING_OUTER_RADIUS).circle(RING_INNER_RADIUS).extrude(RING_HEIGHT)
    ring = ring.translate((0.0, 0.0, -RING_HEIGHT * 0.5))
    indicator = (
        cq.Workplane("XY")
        .box(0.012, 0.004, 0.003, centered=(True, True, True))
        .translate((RING_OUTER_RADIUS - 0.010, 0.0, RING_HEIGHT * 0.5 + 0.0015))
    )
    return ring.union(indicator)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cylindrical_air_purifier")

    body_white = model.material("body_white", rgba=(0.94, 0.95, 0.94, 1.0))
    door_white = model.material("door_white", rgba=(0.90, 0.91, 0.90, 1.0))
    filter_offwhite = model.material("filter_offwhite", rgba=(0.93, 0.92, 0.86, 1.0))
    ring_graphite = model.material("ring_graphite", rgba=(0.18, 0.19, 0.20, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shape(), "purifier_body"),
        material=body_white,
        name="housing",
    )

    rear_door = model.part("rear_door")
    rear_door.visual(
        mesh_from_cadquery(_build_door_shape(), "purifier_rear_door"),
        material=door_white,
        name="door_panel",
    )

    filter_part = model.part("filter")
    filter_part.visual(
        mesh_from_cadquery(_build_filter_shape(), "purifier_filter"),
        material=filter_offwhite,
        name="filter_cartridge",
    )

    control_ring = model.part("control_ring")
    control_ring.visual(
        mesh_from_cadquery(_build_control_ring_shape(), "purifier_control_ring"),
        material=ring_graphite,
        name="ring_shell",
    )

    model.articulation(
        "body_to_rear_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=rear_door,
        origin=Origin(xyz=(HINGE_X, HINGE_Y, HINGE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=1.4,
            lower=0.0,
            upper=math.radians(105.0),
        ),
    )

    model.articulation(
        "body_to_filter",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_part,
        origin=Origin(xyz=(0.0, FILTER_JOINT_Y, HINGE_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.18,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    model.articulation(
        "body_to_control_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=control_ring,
        origin=Origin(xyz=(0.0, 0.0, RING_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.5,
            velocity=4.5,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
