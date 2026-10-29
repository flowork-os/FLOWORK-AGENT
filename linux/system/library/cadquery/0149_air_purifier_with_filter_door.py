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
BODY_WIDTH = 0.56
BODY_HEIGHT = 0.78
BODY_DEPTH = 0.145
BODY_BACK_WALL = 0.010
CAVITY_SIDE_MARGIN = 0.028
CAVITY_TOP_MARGIN = 0.045
CAVITY_BOTTOM_MARGIN = 0.050
CAVITY_WIDTH = BODY_WIDTH - (2.0 * CAVITY_SIDE_MARGIN)
CAVITY_HEIGHT = BODY_HEIGHT - CAVITY_TOP_MARGIN - CAVITY_BOTTOM_MARGIN
CAVITY_FLOOR_Z = (-BODY_HEIGHT / 2.0) + CAVITY_BOTTOM_MARGIN
DOOR_WIDTH = BODY_WIDTH - 0.020
DOOR_HEIGHT = BODY_HEIGHT - 0.032
DOOR_THICKNESS = 0.018
DOOR_GAP = 0.0
DOOR_OPEN_LIMIT = 1.55
FILTER_WIDTH = CAVITY_WIDTH - 0.016
FILTER_HEIGHT = CAVITY_HEIGHT - 0.022
FILTER_DEPTH = 0.110
FILTER_FRAME_THICKNESS = 0.008
FILTER_TRAVEL = 0.072
FILTER_FRONT_Y = 0.052
FILTER_CENTER_Y = FILTER_FRONT_Y - (FILTER_DEPTH / 2.0)
FILTER_CENTER_Z = CAVITY_FLOOR_Z + 0.004 + (FILTER_HEIGHT / 2.0)
RAIL_WIDTH = 0.012
RAIL_HEIGHT = 0.005
RAIL_LENGTH = FILTER_DEPTH - 0.006
RAIL_CENTER_Y = FILTER_CENTER_Y
RAIL_CENTER_Z = CAVITY_FLOOR_Z + (RAIL_HEIGHT / 2.0) - 0.0005
RAIL_OFFSET_X = (FILTER_WIDTH / 2.0) - 0.034
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _build_door_shape() -> cq.Workplane:
    door = _box(
        (DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT),
        (DOOR_WIDTH / 2.0, DOOR_THICKNESS / 2.0, 0.0),
    )
    door = door.edges("|Z").fillet(0.0065)

    perimeter_recess = _box(
        (DOOR_WIDTH - 0.060, 0.0022, DOOR_HEIGHT - 0.080),
        (DOOR_WIDTH / 2.0, DOOR_THICKNESS - 0.0011, 0.0),
    )
    door = door.cut(perimeter_recess)

    slot_count = 7
    slot_span = DOOR_WIDTH - 0.160
    slot_pitch = slot_span / (slot_count - 1)
    slot_start_x = (DOOR_WIDTH / 2.0) - (slot_span / 2.0)
    for index in range(slot_count):
        slot = _box(
            (0.022, DOOR_THICKNESS + 0.004, 0.275),
            (slot_start_x + (index * slot_pitch), DOOR_THICKNESS / 2.0, -0.105),
        )
        door = door.cut(slot)

    pull_lip = _box(
        (0.016, 0.010, 0.120),
        (DOOR_WIDTH - 0.010, DOOR_THICKNESS + 0.002, -0.010),
    )
    door = door.union(pull_lip)

    indicator = _box(
        (0.160, 0.004, 0.018),
        (DOOR_WIDTH * 0.54, DOOR_THICKNESS - 0.001, DOOR_HEIGHT / 2.0 - 0.080),
    )
    door = door.union(indicator)

    return door
def _build_filter_shape() -> cq.Workplane:
    cartridge = _box(
        (FILTER_WIDTH, FILTER_DEPTH, FILTER_HEIGHT),
        (0.0, -FILTER_DEPTH / 2.0, 0.0),
    )

    inner_void = _box(
        (
            FILTER_WIDTH - (2.0 * FILTER_FRAME_THICKNESS),
            FILTER_DEPTH - (2.0 * FILTER_FRAME_THICKNESS),
            FILTER_HEIGHT - (2.0 * FILTER_FRAME_THICKNESS),
        ),
        (0.0, -FILTER_DEPTH / 2.0, 0.0),
    )
    cartridge = cartridge.cut(inner_void)

    media_width = FILTER_WIDTH - (2.0 * FILTER_FRAME_THICKNESS) + 0.002
    media_height = FILTER_HEIGHT - (2.0 * FILTER_FRAME_THICKNESS) + 0.002
    media_depth = FILTER_DEPTH - (2.0 * FILTER_FRAME_THICKNESS) + 0.002
    media = _box(
        (media_width, media_depth, media_height),
        (0.0, -FILTER_DEPTH / 2.0, 0.0),
    )
    cartridge = cartridge.union(media)

    rib_count = 11
    rib_span = media_width - 0.030
    rib_pitch = rib_span / (rib_count - 1)
    rib_start_x = -(rib_span / 2.0)
    rib_center_y = -FILTER_FRAME_THICKNESS - 0.004
    for index in range(rib_count):
        rib = _box(
            (0.010, 0.012, media_height),
            (rib_start_x + (index * rib_pitch), rib_center_y, 0.0),
        )
        cartridge = cartridge.union(rib)

    groove_width = RAIL_WIDTH + 0.004
    groove_height = RAIL_HEIGHT + 0.002
    groove_length = FILTER_DEPTH - 0.016
    groove_center_z = (-FILTER_HEIGHT / 2.0) + (groove_height / 2.0)
    for rail_sign in (-1.0, 1.0):
        groove = _box(
            (groove_width, groove_length, groove_height),
            (rail_sign * RAIL_OFFSET_X, -FILTER_DEPTH / 2.0, groove_center_z),
        )
        cartridge = cartridge.cut(groove)

    pull_tab = _box(
        (0.072, 0.018, 0.022),
        (0.0, 0.004, (FILTER_HEIGHT / 2.0) - 0.036),
    )
    cartridge = cartridge.union(pull_tab)

    return cartridge
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_panel_air_purifier")

    model.material("body_finish", rgba=(0.87, 0.89, 0.90, 1.0))
    model.material("door_finish", rgba=(0.95, 0.96, 0.96, 1.0))
    model.material("filter_finish", rgba=(0.29, 0.33, 0.36, 1.0))

    body = model.part("body")
    body.visual(
        Box((BODY_WIDTH, BODY_BACK_WALL, BODY_HEIGHT)),
        origin=Origin(xyz=(0.0, (-BODY_DEPTH / 2.0) + (BODY_BACK_WALL / 2.0), 0.0)),
        material="body_finish",
        name="back_panel",
    )
    body.visual(
        Box((CAVITY_SIDE_MARGIN, BODY_DEPTH - BODY_BACK_WALL + 0.001, BODY_HEIGHT)),
        origin=Origin(
            xyz=(
                (-BODY_WIDTH / 2.0) + (CAVITY_SIDE_MARGIN / 2.0),
                (BODY_BACK_WALL / 2.0) - 0.0005,
                0.0,
            )
        ),
        material="body_finish",
        name="side_wall_0",
    )
    body.visual(
        Box((CAVITY_SIDE_MARGIN, BODY_DEPTH - BODY_BACK_WALL + 0.001, BODY_HEIGHT)),
        origin=Origin(
            xyz=(
                (BODY_WIDTH / 2.0) - (CAVITY_SIDE_MARGIN / 2.0),
                (BODY_BACK_WALL / 2.0) - 0.0005,
                0.0,
            )
        ),
        material="body_finish",
        name="side_wall_1",
    )
    body.visual(
        Box((CAVITY_WIDTH + 0.002, BODY_DEPTH - BODY_BACK_WALL + 0.001, CAVITY_TOP_MARGIN)),
        origin=Origin(
            xyz=(
                0.0,
                (BODY_BACK_WALL / 2.0) - 0.0005,
                (BODY_HEIGHT / 2.0) - (CAVITY_TOP_MARGIN / 2.0),
            )
        ),
        material="body_finish",
        name="top_wall",
    )
    body.visual(
        Box((CAVITY_WIDTH + 0.002, BODY_DEPTH - BODY_BACK_WALL + 0.001, CAVITY_BOTTOM_MARGIN)),
        origin=Origin(
            xyz=(
                0.0,
                (BODY_BACK_WALL / 2.0) - 0.0005,
                (-BODY_HEIGHT / 2.0) + (CAVITY_BOTTOM_MARGIN / 2.0),
            )
        ),
        material="body_finish",
        name="bottom_wall",
    )
    body.visual(
        Box((RAIL_WIDTH, RAIL_LENGTH, RAIL_HEIGHT)),
        origin=Origin(xyz=(-RAIL_OFFSET_X, RAIL_CENTER_Y, RAIL_CENTER_Z)),
        material="body_finish",
        name="rail_0",
    )
    body.visual(
        Box((RAIL_WIDTH, RAIL_LENGTH, RAIL_HEIGHT)),
        origin=Origin(xyz=(RAIL_OFFSET_X, RAIL_CENTER_Y, RAIL_CENTER_Z)),
        material="body_finish",
        name="rail_1",
    )
    door = model.part("door")
    door.visual(
        mesh_from_cadquery(_build_door_shape(), "purifier_door"),
        material="door_finish",
        name="panel",
    )

    filter_cartridge = model.part("filter")
    filter_cartridge.visual(
        mesh_from_cadquery(_build_filter_shape(), "purifier_filter"),
        material="filter_finish",
        name="cartridge",
    )

    model.articulation(
        "door_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, (BODY_DEPTH / 2.0) + DOOR_GAP, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=DOOR_OPEN_LIMIT, effort=12.0, velocity=1.2),
    )
    model.articulation(
        "filter_slide",
        ArticulationType.PRISMATIC,
        parent=body,
        child=filter_cartridge,
        origin=Origin(xyz=(0.0, FILTER_FRONT_Y, FILTER_CENTER_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=FILTER_TRAVEL, effort=35.0, velocity=0.18),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
