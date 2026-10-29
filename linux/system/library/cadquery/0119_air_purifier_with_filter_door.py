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
BODY_DEPTH = 0.18
BODY_WIDTH = 0.22
BODY_HEIGHT = 0.42
BODY_WALL = 0.004
FRONT_OPENING_WIDTH = 0.182
FRONT_OPENING_HEIGHT = 0.158
FRONT_OPENING_BOTTOM = 0.040
PANEL_GAP = 0.002
PANEL_THICKNESS = 0.012
PANEL_WIDTH = FRONT_OPENING_WIDTH - (2.0 * PANEL_GAP)
PANEL_HEIGHT = FRONT_OPENING_HEIGHT - (2.0 * PANEL_GAP)
FILTER_WIDTH = 0.168
FILTER_HEIGHT = 0.148
FILTER_DEPTH = 0.140
FILTER_REST_RECESS = 0.016
FILTER_TRAVEL = 0.095
SWITCH_WIDTH = 0.018
SWITCH_X = -0.028
SWITCH_Y = 0.0
def _build_front_panel_shape() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(PANEL_THICKNESS, PANEL_WIDTH, PANEL_HEIGHT, centered=(False, False, True))
        .translate((0.0, 0.0, 0.0))
    )

    for slot_y in (
        0.022,
        0.046,
        0.070,
        0.094,
        0.118,
        0.142,
        0.166,
    ):
        slot = (
            cq.Workplane("XY")
            .box(PANEL_THICKNESS * 1.4, 0.009, PANEL_HEIGHT - 0.034, centered=(False, True, True))
            .translate((-0.001, slot_y, 0.0))
        )
        panel = panel.cut(slot)

    return panel
def _build_filter_shape() -> cq.Workplane:
    filter_shape = (
        cq.Workplane("XY")
        .box(FILTER_DEPTH, FILTER_WIDTH, FILTER_HEIGHT, centered=(False, True, True))
        .translate((-FILTER_DEPTH, 0.0, 0.0))
    )

    front_frame = (
        cq.Workplane("XY")
        .box(0.010, FILTER_WIDTH, FILTER_HEIGHT, centered=(False, True, True))
        .translate((-0.010, 0.0, 0.0))
    )
    inner_relief = (
        cq.Workplane("XY")
        .box(0.014, FILTER_WIDTH - 0.020, FILTER_HEIGHT - 0.020, centered=(False, True, True))
        .translate((-0.014, 0.0, 0.0))
    )
    filter_shape = filter_shape.union(front_frame.cut(inner_relief))

    for rib_y in (-0.060, -0.042, -0.024, -0.006, 0.012, 0.030, 0.048, 0.066):
        rib = (
            cq.Workplane("XY")
            .box(0.008, 0.006, FILTER_HEIGHT - 0.024, centered=(False, True, True))
            .translate((-0.008, rib_y, 0.0))
        )
        filter_shape = filter_shape.union(rib)

    return filter_shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_purifier")

    shell_white = model.material("shell_white", rgba=(0.92, 0.94, 0.95, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.74, 0.77, 0.79, 1.0))
    filter_gray = model.material("filter_gray", rgba=(0.46, 0.50, 0.53, 1.0))
    switch_black = model.material("switch_black", rgba=(0.09, 0.10, 0.11, 1.0))

    body = model.part("body")
    shell_overlap = 0.0005
    shell_span_x = BODY_DEPTH - BODY_WALL + shell_overlap
    shell_center_x = (BODY_WALL / 2.0) - (shell_overlap / 2.0)
    shell_inner_width = BODY_WIDTH - (2.0 * BODY_WALL) + shell_overlap
    opening_center_z = FRONT_OPENING_BOTTOM + (FRONT_OPENING_HEIGHT / 2.0)
    front_frame_width = ((BODY_WIDTH - FRONT_OPENING_WIDTH) / 2.0) + shell_overlap

    body.visual(
        Box((BODY_WALL, BODY_WIDTH, BODY_HEIGHT)),
        origin=Origin(xyz=((-BODY_DEPTH / 2.0) + (BODY_WALL / 2.0), 0.0, BODY_HEIGHT / 2.0)),
        material=shell_white,
        name="back_wall",
    )
    for index, y_center in enumerate(
        (
            (BODY_WIDTH / 2.0) - (BODY_WALL / 2.0),
            (-BODY_WIDTH / 2.0) + (BODY_WALL / 2.0),
        )
    ):
        body.visual(
            Box((shell_span_x, BODY_WALL, BODY_HEIGHT)),
            origin=Origin(xyz=(shell_center_x, y_center, BODY_HEIGHT / 2.0)),
            material=shell_white,
            name=f"side_wall_{index}",
        )
    body.visual(
        Box((shell_span_x, shell_inner_width, BODY_WALL)),
        origin=Origin(xyz=(shell_center_x, 0.0, BODY_WALL / 2.0)),
        material=shell_white,
        name="base_wall",
    )
    body.visual(
        Box((shell_span_x, shell_inner_width, BODY_WALL)),
        origin=Origin(xyz=(shell_center_x, 0.0, BODY_HEIGHT - (BODY_WALL / 2.0))),
        material=shell_white,
        name="top_wall",
    )
    body.visual(
        Box((BODY_WALL, BODY_WIDTH, FRONT_OPENING_BOTTOM + shell_overlap)),
        origin=Origin(
            xyz=(
                (BODY_DEPTH / 2.0) - (BODY_WALL / 2.0),
                0.0,
                (FRONT_OPENING_BOTTOM + shell_overlap) / 2.0,
            )
        ),
        material=shell_white,
        name="lower_rail",
    )
    body.visual(
        Box(
            (
                BODY_WALL,
                BODY_WIDTH,
                BODY_HEIGHT - (FRONT_OPENING_BOTTOM + FRONT_OPENING_HEIGHT) + shell_overlap,
            )
        ),
        origin=Origin(
            xyz=(
                (BODY_DEPTH / 2.0) - (BODY_WALL / 2.0),
                0.0,
                FRONT_OPENING_BOTTOM
                + FRONT_OPENING_HEIGHT
                + (BODY_HEIGHT - (FRONT_OPENING_BOTTOM + FRONT_OPENING_HEIGHT) + shell_overlap) / 2.0,
            )
        ),
        material=shell_white,
        name="upper_front",
    )
    for index, y_center in enumerate(
        (
            (FRONT_OPENING_WIDTH / 2.0) + (front_frame_width / 2.0),
            (-FRONT_OPENING_WIDTH / 2.0) - (front_frame_width / 2.0),
        )
    ):
        body.visual(
            Box((BODY_WALL, front_frame_width, FRONT_OPENING_HEIGHT + shell_overlap)),
            origin=Origin(
                xyz=(
                    (BODY_DEPTH / 2.0) - (BODY_WALL / 2.0),
                    y_center,
                    opening_center_z,
                )
            ),
            material=shell_white,
            name=f"front_stile_{index}",
        )
    for index, rail_y in enumerate((-0.095, 0.095)):
        body.visual(
            Box((0.110, 0.022, 0.012)),
            origin=Origin(xyz=(-0.012, rail_y, opening_center_z)),
            material=trim_gray,
            name=f"guide_rail_{index}",
        )
    for index, vent_y in enumerate((-0.056, -0.034, -0.012, 0.012, 0.034, 0.056)):
        body.visual(
            Box((0.090, 0.008, 0.002)),
            origin=Origin(xyz=(-0.008, vent_y, BODY_HEIGHT - 0.001)),
            material=trim_gray,
            name=f"top_vent_{index}",
        )

    front_panel = model.part("front_panel")
    front_panel.visual(
        mesh_from_cadquery(_build_front_panel_shape(), "front_panel"),
        material=trim_gray,
        name="panel",
    )
    front_panel.visual(
        Box((0.001, 0.006, PANEL_HEIGHT - 0.010)),
        origin=Origin(xyz=(0.0005, 0.0, 0.0)),
        material=trim_gray,
        name="hinge_leaf",
    )
    for index, z_center in enumerate((-0.057, 0.0, 0.057)):
        front_panel.visual(
            Cylinder(radius=0.0045, length=0.036 if index != 1 else 0.048),
            origin=Origin(xyz=(0.0045, 0.0, z_center)),
            material=trim_gray,
            name=f"knuckle_{index}",
        )

    filter_part = model.part("filter")
    filter_part.visual(
        mesh_from_cadquery(_build_filter_shape(), "filter_cartridge"),
        material=filter_gray,
        name="cartridge",
    )

    rocker_switch = model.part("rocker_switch")
    rocker_switch.visual(
        Box((0.012, SWITCH_WIDTH, 0.005)),
        origin=Origin(xyz=(0.006, 0.0, 0.001)),
        material=switch_black,
        name="switch_front",
    )
    rocker_switch.visual(
        Box((0.012, SWITCH_WIDTH, 0.005)),
        origin=Origin(xyz=(-0.006, 0.0, 0.001)),
        material=switch_black,
        name="switch_rear",
    )
    rocker_switch.visual(
        Box((0.006, SWITCH_WIDTH, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, -0.001)),
        material=switch_black,
        name="switch_bridge",
    )
    rocker_switch.visual(
        Box((0.006, 0.003, 0.006)),
        origin=Origin(xyz=(0.0, 0.0105, -0.002)),
        material=switch_black,
        name="switch_tab_0",
    )
    rocker_switch.visual(
        Box((0.006, 0.003, 0.006)),
        origin=Origin(xyz=(0.0, -0.0105, -0.002)),
        material=switch_black,
        name="switch_tab_1",
    )

    front_x = BODY_DEPTH / 2.0
    opening_center_z = FRONT_OPENING_BOTTOM + (FRONT_OPENING_HEIGHT / 2.0)
    filter_origin_x = front_x - PANEL_THICKNESS - FILTER_REST_RECESS

    model.articulation(
        "body_to_front_panel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=front_panel,
        origin=Origin(
            xyz=(
                front_x,
                (-FRONT_OPENING_WIDTH / 2.0) + PANEL_GAP,
                opening_center_z,
            )
        ),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=1.6,
            lower=0.0,
            upper=math.radians(78.0),
        ),
    )
    model.articulation(
        "body_to_filter",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_part,
        origin=Origin(xyz=(filter_origin_x, 0.0, opening_center_z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.15,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )
    model.articulation(
        "body_to_rocker_switch",
        ArticulationType.REVOLUTE,
        parent=body,
        child=rocker_switch,
        origin=Origin(xyz=(SWITCH_X, SWITCH_Y, BODY_HEIGHT + 0.005)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.5,
            velocity=2.5,
            lower=-0.30,
            upper=0.30,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
