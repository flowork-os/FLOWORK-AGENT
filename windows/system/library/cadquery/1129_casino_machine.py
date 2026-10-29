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
CABINET_DEPTH = 0.66
FRONT_THICKNESS = 0.03
SIDE_THICKNESS = 0.03
BODY_HEIGHT = 1.58
INNER_WIDTH = CABINET_WIDTH - 2.0 * SIDE_THICKNESS
DOOR_WIDTH = 0.48
DOOR_HEIGHT = 0.52
DOOR_THICKNESS = 0.018
DOOR_OPENING_WIDTH = 0.50
DOOR_OPENING_HEIGHT = 0.54
DOOR_OPENING_BOTTOM = 0.14
DOOR_RECESS = 0.010
REEL_OPENING_WIDTH = 0.46
REEL_OPENING_HEIGHT = 0.34
REEL_OPENING_BOTTOM = 0.96
SHELF_WIDTH = 0.58
SHELF_DEPTH = 0.16
SHELF_HEIGHT = 0.10
SHELF_TOP_THICKNESS = 0.014
SHELF_WALL_THICKNESS = 0.015
SHELF_FRONT_APRON = 0.028
BUTTON_TRAVEL = 0.008
BUTTON_CAP_RADIUS = 0.029
BUTTON_STEM_RADIUS = 0.011
BUTTON_TOP_CLEARANCE = 0.009
BUTTON_CAP_HEIGHT = 0.016
BUTTON_STEM_LENGTH = 0.050
BUTTON_Y = -0.010
BUTTON_X_OFFSETS = (-0.14, 0.0, 0.14)
def _build_top_housing() -> object:
    return (
        cq.Workplane("XY")
        .box(0.68, 0.44, 0.34)
        .edges("|X and >Z")
        .fillet(0.12)
    )
def _build_shelf_body() -> object:
    top = (
        cq.Workplane("XY")
        .box(SHELF_WIDTH, SHELF_DEPTH, SHELF_TOP_THICKNESS)
        .translate((0.0, 0.0, SHELF_HEIGHT - SHELF_TOP_THICKNESS / 2.0))
    )
    rear = (
        cq.Workplane("XY")
        .box(SHELF_WIDTH, SHELF_WALL_THICKNESS, SHELF_HEIGHT)
        .translate((0.0, SHELF_DEPTH / 2.0 - SHELF_WALL_THICKNESS / 2.0, SHELF_HEIGHT / 2.0))
    )
    front = (
        cq.Workplane("XY")
        .box(SHELF_WIDTH, SHELF_FRONT_APRON, SHELF_HEIGHT * 0.64)
        .translate((0.0, -SHELF_DEPTH / 2.0 + SHELF_FRONT_APRON / 2.0, SHELF_HEIGHT * 0.32))
    )
    left = (
        cq.Workplane("XY")
        .box(SHELF_WALL_THICKNESS, SHELF_DEPTH, SHELF_HEIGHT)
        .translate((-SHELF_WIDTH / 2.0 + SHELF_WALL_THICKNESS / 2.0, 0.0, SHELF_HEIGHT / 2.0))
    )
    right = (
        cq.Workplane("XY")
        .box(SHELF_WALL_THICKNESS, SHELF_DEPTH, SHELF_HEIGHT)
        .translate((SHELF_WIDTH / 2.0 - SHELF_WALL_THICKNESS / 2.0, 0.0, SHELF_HEIGHT / 2.0))
    )
    shelf = top.union(rear).union(front).union(left).union(right)
    shelf = (
        shelf.faces(">Z")
        .workplane()
        .pushPoints([(x_pos, BUTTON_Y) for x_pos in BUTTON_X_OFFSETS])
        .circle(BUTTON_STEM_RADIUS + 0.0015)
        .cutBlind(-(SHELF_TOP_THICKNESS + 0.008))
    )
    return shelf
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="reel_slot_machine")

    cabinet_red = model.material("cabinet_red", rgba=(0.66, 0.08, 0.10, 1.0))
    cabinet_dark = model.material("cabinet_dark", rgba=(0.12, 0.12, 0.14, 1.0))
    cabinet_shadow = model.material("cabinet_shadow", rgba=(0.08, 0.08, 0.09, 1.0))
    gold_trim = model.material("gold_trim", rgba=(0.73, 0.60, 0.18, 1.0))
    chrome = model.material("chrome", rgba=(0.82, 0.84, 0.87, 1.0))
    smoked_glass = model.material("smoked_glass", rgba=(0.14, 0.24, 0.28, 0.35))
    reel_white = model.material("reel_white", rgba=(0.93, 0.93, 0.90, 1.0))
    reel_black = model.material("reel_black", rgba=(0.10, 0.10, 0.11, 1.0))
    button_red = model.material("button_red", rgba=(0.78, 0.12, 0.12, 1.0))
    button_amber = model.material("button_amber", rgba=(0.84, 0.57, 0.15, 1.0))
    button_blue = model.material("button_blue", rgba=(0.15, 0.36, 0.78, 1.0))
    marquee_glow = model.material("marquee_glow", rgba=(0.92, 0.63, 0.16, 0.55))

    cabinet = model.part("cabinet")

    cabinet.visual(
        Box((CABINET_WIDTH, CABINET_DEPTH * 0.94, 0.06)),
        origin=Origin(xyz=(0.0, 0.0, 0.03)),
        material=cabinet_dark,
        name="base_plinth",
    )
    cabinet.visual(
        Box((SIDE_THICKNESS, CABINET_DEPTH, BODY_HEIGHT)),
        origin=Origin(xyz=(-CABINET_WIDTH / 2.0 + SIDE_THICKNESS / 2.0, 0.0, BODY_HEIGHT / 2.0)),
        material=cabinet_red,
        name="side_wall_0",
    )
    cabinet.visual(
        Box((SIDE_THICKNESS, CABINET_DEPTH, BODY_HEIGHT)),
        origin=Origin(xyz=(CABINET_WIDTH / 2.0 - SIDE_THICKNESS / 2.0, 0.0, BODY_HEIGHT / 2.0)),
        material=cabinet_red,
        name="side_wall_1",
    )
    cabinet.visual(
        Box((INNER_WIDTH, SIDE_THICKNESS, BODY_HEIGHT)),
        origin=Origin(xyz=(0.0, CABINET_DEPTH / 2.0 - SIDE_THICKNESS / 2.0, BODY_HEIGHT / 2.0)),
        material=cabinet_red,
        name="back_wall",
    )
    cabinet.visual(
        Box((INNER_WIDTH, CABINET_DEPTH - FRONT_THICKNESS - SIDE_THICKNESS, SIDE_THICKNESS)),
        origin=Origin(
            xyz=(
                0.0,
                (CABINET_DEPTH / 2.0 - SIDE_THICKNESS / 2.0 + (-CABINET_DEPTH / 2.0 + FRONT_THICKNESS) / 2.0),
                SIDE_THICKNESS / 2.0,
            )
        ),
        material=cabinet_dark,
        name="floor",
    )
    cabinet.visual(
        Box((INNER_WIDTH, FRONT_THICKNESS, DOOR_OPENING_BOTTOM)),
        origin=Origin(
            xyz=(0.0, -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0, DOOR_OPENING_BOTTOM / 2.0)
        ),
        material=gold_trim,
        name="front_bottom_rail",
    )

    door_jamb_width = (INNER_WIDTH - DOOR_OPENING_WIDTH) / 2.0
    cabinet.visual(
        Box((door_jamb_width, FRONT_THICKNESS, DOOR_OPENING_HEIGHT)),
        origin=Origin(
            xyz=(
                -(DOOR_OPENING_WIDTH / 2.0 + door_jamb_width / 2.0),
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                DOOR_OPENING_BOTTOM + DOOR_OPENING_HEIGHT / 2.0,
            )
        ),
        material=gold_trim,
        name="door_jamb_0",
    )
    cabinet.visual(
        Box((door_jamb_width, FRONT_THICKNESS, DOOR_OPENING_HEIGHT)),
        origin=Origin(
            xyz=(
                DOOR_OPENING_WIDTH / 2.0 + door_jamb_width / 2.0,
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                DOOR_OPENING_BOTTOM + DOOR_OPENING_HEIGHT / 2.0,
            )
        ),
        material=gold_trim,
        name="door_jamb_1",
    )

    bridge_height = REEL_OPENING_BOTTOM - (DOOR_OPENING_BOTTOM + DOOR_OPENING_HEIGHT)
    cabinet.visual(
        Box((INNER_WIDTH, FRONT_THICKNESS, bridge_height)),
        origin=Origin(
            xyz=(
                0.0,
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                DOOR_OPENING_BOTTOM + DOOR_OPENING_HEIGHT + bridge_height / 2.0,
            )
        ),
        material=cabinet_red,
        name="front_bridge",
    )

    reel_jamb_width = (INNER_WIDTH - REEL_OPENING_WIDTH) / 2.0
    cabinet.visual(
        Box((reel_jamb_width, FRONT_THICKNESS, REEL_OPENING_HEIGHT)),
        origin=Origin(
            xyz=(
                -(REEL_OPENING_WIDTH / 2.0 + reel_jamb_width / 2.0),
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                REEL_OPENING_BOTTOM + REEL_OPENING_HEIGHT / 2.0,
            )
        ),
        material=gold_trim,
        name="reel_jamb_0",
    )
    cabinet.visual(
        Box((reel_jamb_width, FRONT_THICKNESS, REEL_OPENING_HEIGHT)),
        origin=Origin(
            xyz=(
                REEL_OPENING_WIDTH / 2.0 + reel_jamb_width / 2.0,
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                REEL_OPENING_BOTTOM + REEL_OPENING_HEIGHT / 2.0,
            )
        ),
        material=gold_trim,
        name="reel_jamb_1",
    )

    top_rail_height = 0.18
    cabinet.visual(
        Box((INNER_WIDTH, FRONT_THICKNESS, top_rail_height)),
        origin=Origin(
            xyz=(
                0.0,
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS / 2.0,
                REEL_OPENING_BOTTOM + REEL_OPENING_HEIGHT + top_rail_height / 2.0,
            )
        ),
        material=cabinet_red,
        name="reel_top_rail",
    )

    cabinet.visual(
        mesh_from_cadquery(_build_top_housing(), "slot_machine_top_housing"),
        origin=Origin(xyz=(0.0, -0.11, 1.64)),
        material=cabinet_red,
        name="top_housing",
    )
    cabinet.visual(
        Box((0.56, 0.006, 0.20)),
        origin=Origin(xyz=(0.0, -CABINET_DEPTH / 2.0 + 0.003, 1.63)),
        material=marquee_glow,
        name="marquee_panel",
    )

    reel_pack = model.part("reel_pack")
    reel_pack.visual(
        Box((REEL_OPENING_WIDTH - 0.016, 0.14, REEL_OPENING_HEIGHT - 0.020)),
        origin=Origin(xyz=(0.0, 0.072, 0.0)),
        material=reel_black,
        name="reel_box",
    )
    reel_pack.visual(
        Box((REEL_OPENING_WIDTH - 0.014, 0.004, REEL_OPENING_HEIGHT - 0.010)),
        origin=Origin(xyz=(0.0, 0.002, 0.0)),
        material=smoked_glass,
        name="window_glass",
    )
    reel_pack.visual(
        Box((INNER_WIDTH - 0.040, 0.012, 0.050)),
        origin=Origin(xyz=(0.0, 0.006, REEL_OPENING_HEIGHT / 2.0 + 0.025)),
        material=cabinet_shadow,
        name="reel_mount_top",
    )
    reel_pack.visual(
        Box((INNER_WIDTH - 0.040, 0.012, 0.050)),
        origin=Origin(xyz=(0.0, 0.006, -(REEL_OPENING_HEIGHT / 2.0 + 0.025))),
        material=cabinet_shadow,
        name="reel_mount_bottom",
    )
    reel_pack.visual(
        Box((0.070, 0.012, REEL_OPENING_HEIGHT + 0.060)),
        origin=Origin(xyz=(0.0, 0.006, 0.0)),
        material=cabinet_shadow,
        name="reel_mount_spine",
    )
    reel_pack.visual(
        Cylinder(radius=0.012, length=REEL_OPENING_WIDTH - 0.030),
        origin=Origin(xyz=(0.0, 0.072, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=chrome,
        name="reel_shaft",
    )
    for index, x_pos in enumerate((-0.14, 0.0, 0.14)):
        reel_pack.visual(
            Cylinder(radius=0.088, length=0.12),
            origin=Origin(xyz=(x_pos, 0.072, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=reel_white,
            name=f"reel_{index}",
        )

    model.articulation(
        "cabinet_to_reel_pack",
        ArticulationType.FIXED,
        parent=cabinet,
        child=reel_pack,
        origin=Origin(
            xyz=(
                0.0,
                -CABINET_DEPTH / 2.0 + FRONT_THICKNESS,
                REEL_OPENING_BOTTOM + REEL_OPENING_HEIGHT / 2.0,
            )
        ),
    )

    shelf = model.part("shelf")
    shelf.visual(
        mesh_from_cadquery(_build_shelf_body(), "slot_machine_button_shelf"),
        material=cabinet_dark,
        name="shelf_body",
    )
    shelf.visual(
        Box((SHELF_WIDTH - 0.040, 0.004, 0.012)),
        origin=Origin(xyz=(0.0, -SHELF_DEPTH / 2.0 - 0.002, SHELF_HEIGHT * 0.62)),
        material=gold_trim,
        name="shelf_trim",
    )
    model.articulation(
        "cabinet_to_shelf",
        ArticulationType.FIXED,
        parent=cabinet,
        child=shelf,
        origin=Origin(xyz=(0.0, -CABINET_DEPTH / 2.0 - SHELF_DEPTH / 2.0, 0.72)),
    )

    service_door = model.part("service_door")
    service_door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(-DOOR_WIDTH / 2.0, 0.0, DOOR_HEIGHT / 2.0)),
        material=cabinet_dark,
        name="door_panel",
    )
    service_door.visual(
        Box((0.060, 0.004, 0.028)),
        origin=Origin(
            xyz=(-DOOR_WIDTH + 0.055, -(DOOR_THICKNESS / 2.0 + 0.002), DOOR_HEIGHT * 0.58)
        ),
        material=chrome,
        name="door_pull",
    )
    service_door.visual(
        Cylinder(radius=0.010, length=0.004),
        origin=Origin(
            xyz=(-DOOR_WIDTH + 0.095, -(DOOR_THICKNESS / 2.0 + 0.002), DOOR_HEIGHT * 0.58)
        ),
        material=chrome,
        name="door_lock",
    )
    model.articulation(
        "cabinet_to_service_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=service_door,
        origin=Origin(
            xyz=(
                DOOR_WIDTH / 2.0,
                -CABINET_DEPTH / 2.0 + DOOR_RECESS + DOOR_THICKNESS / 2.0,
                DOOR_OPENING_BOTTOM,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.55, effort=20.0, velocity=1.4),
    )

    button_materials = (button_red, button_amber, button_blue)
    for index, (x_pos, cap_material) in enumerate(zip(BUTTON_X_OFFSETS, button_materials)):
        button = model.part(f"button_{index}")
        button.visual(
            Cylinder(radius=BUTTON_STEM_RADIUS, length=BUTTON_STEM_LENGTH),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_TOP_CLEARANCE - BUTTON_STEM_LENGTH / 2.0)),
            material=chrome,
            name="button_stem",
        )
        button.visual(
            Cylinder(radius=BUTTON_STEM_RADIUS + 0.0035, length=0.004),
            origin=Origin(xyz=(0.0, 0.0, -(SHELF_TOP_THICKNESS + 0.002))),
            material=chrome,
            name="button_collar",
        )
        button.visual(
            Cylinder(radius=BUTTON_CAP_RADIUS, length=BUTTON_CAP_HEIGHT),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_TOP_CLEARANCE + BUTTON_CAP_HEIGHT / 2.0)),
            material=cap_material,
            name="button_cap",
        )
        model.articulation(
            f"shelf_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=shelf,
            child=button,
            origin=Origin(xyz=(x_pos, BUTTON_Y, SHELF_HEIGHT)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                lower=0.0,
                upper=BUTTON_TRAVEL,
                effort=12.0,
                velocity=0.08,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
