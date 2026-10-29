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
CABINET_WIDTH = 0.70
CABINET_HEIGHT = 1.99
LOWER_DISPLAY_SIZE = (0.50, 0.040, 0.80)
LOWER_DISPLAY_CENTER = (0.0, -0.080, 1.12)
TOP_DISPLAY_SIZE = (0.46, 0.040, 0.26)
TOP_DISPLAY_CENTER = (0.0, -0.120, 1.74)
DOOR_WIDTH = 0.186
DOOR_HEIGHT = 0.300
DOOR_THICKNESS = 0.018
DOOR_CENTER_Z = 0.370
DOOR_HINGE_ORIGIN = (-0.104, -0.208, DOOR_CENTER_Z)
DECK_ROLL = math.radians(30.0)
DECK_CENTER = (0.0, -0.1320, 0.663)
DECK_SIZE = (0.56, 0.15, 0.030)
BUTTON_SIZE = (0.072, 0.040, 0.012)
BUTTON_XS = (-0.200, -0.100, 0.0, 0.100, 0.200)
def _cq_box(size: tuple[float, float, float], center: tuple[float, float, float]):
    sx, sy, sz = size
    cx, cy, cz = center
    return cq.Workplane("XY").box(sx, sy, sz).translate((cx, cy, cz))
def _cq_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
):
    cx, cy, cz = center
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((cx, cy, cz - (length * 0.5)))
    )
def _build_bill_door():
    panel = _cq_box(
        (DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT),
        (0.103, 0.019, 0.0),
    )
    hinge_leaf = _cq_box((0.020, 0.012, DOOR_HEIGHT), (0.012, 0.015, 0.0))

    slot_trim = _cq_box((0.102, 0.004, 0.028), (0.115, 0.008, 0.066))
    pull = _cq_box((0.060, 0.010, 0.016), (0.132, 0.008, -0.082))

    barrels = None
    for z_center in (-0.105, 0.0, 0.105):
        barrel = _cq_cylinder(0.0075, 0.030, (0.004, 0.010, z_center))
        barrels = barrel if barrels is None else barrels.union(barrel)

    acceptor_slot = _cq_box((0.086, 0.024, 0.008), (0.118, 0.018, 0.066))

    return panel.union(hinge_leaf).union(slot_trim).union(pull).union(barrels).cut(acceptor_slot)
def _build_side_panel():
    thickness = 0.028
    profile = [
        (-0.18, 0.00),
        (0.24, 0.00),
        (0.30, 0.42),
        (0.29, 0.78),
        (0.23, 1.16),
        (0.18, 1.46),
        (0.12, 1.73),
        (0.08, 1.90),
        (-0.02, CABINET_HEIGHT),
        (-0.09, 1.88),
        (-0.11, 1.58),
        (-0.02, 1.50),
        (-0.02, 0.76),
        (-0.12, 0.68),
        (-0.18, 0.58),
        (-0.18, 0.00),
    ]
    return cq.Workplane("YZ").polyline(profile).close().extrude(thickness)
def _add_display_module(
    part,
    *,
    outer_size: tuple[float, float, float],
    glass_margin_x: float,
    glass_margin_z: float,
    frame_material,
    glass_material,
):
    width, depth, height = outer_size
    part.visual(
        Box(outer_size),
        material=frame_material,
        name="frame",
    )
    part.visual(
        Box((width - glass_margin_x, 0.0035, height - glass_margin_z)),
        origin=Origin(xyz=(0.0, -(depth * 0.5) + 0.00175, 0.0)),
        material=glass_material,
        name="glass",
    )
    part.visual(
        Box((width - 0.10, depth * 0.55, height - 0.10)),
        origin=Origin(xyz=(0.0, 0.002, 0.0)),
        material=frame_material,
        name="backer",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="dual_screen_slot_cabinet")

    cabinet_finish = model.material("cabinet_finish", rgba=(0.10, 0.11, 0.13, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.20, 0.22, 0.25, 1.0))
    deck_finish = model.material("deck_finish", rgba=(0.14, 0.15, 0.17, 1.0))
    display_glass = model.material("display_glass", rgba=(0.10, 0.23, 0.30, 0.45))
    display_frame = model.material("display_frame", rgba=(0.05, 0.06, 0.07, 1.0))
    button_finish = model.material("button_finish", rgba=(0.88, 0.28, 0.10, 1.0))
    button_light = model.material("button_light", rgba=(0.98, 0.62, 0.16, 1.0))
    chrome = model.material("chrome", rgba=(0.76, 0.79, 0.82, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        Box((0.70, 0.56, 0.58)),
        origin=Origin(xyz=(0.0, 0.10, 0.29)),
        material=cabinet_finish,
        name="shell",
    )
    cabinet.visual(
        Box((0.70, 0.44, 1.02)),
        origin=Origin(xyz=(0.0, 0.16, 1.09)),
        material=cabinet_finish,
        name="lower_body",
    )
    cabinet.visual(
        Box((0.66, 0.36, 0.39)),
        origin=Origin(xyz=(0.0, 0.08, 1.795)),
        material=cabinet_finish,
        name="upper_body",
    )
    cabinet.visual(
        Box((0.64, 0.20, 0.12)),
        origin=Origin(xyz=(0.0, 0.07, 1.54)),
        material=trim_finish,
        name="display_bridge",
    )
    cabinet.visual(
        Box((0.62, 0.12, 0.08)),
        origin=Origin(xyz=(0.0, -0.07, 1.95)),
        material=trim_finish,
        name="top_cap",
    )
    cabinet.visual(
        Box((0.62, 0.010, 0.020)),
        origin=Origin(xyz=(0.0, -0.175, 0.020)),
        material=trim_finish,
        name="toe_trim",
    )
    side_panel_mesh = mesh_from_cadquery(_build_side_panel(), "slot_side_panel")
    cabinet.visual(
        side_panel_mesh,
        origin=Origin(xyz=(-CABINET_WIDTH * 0.5, 0.0, 0.0)),
        material=trim_finish,
        name="side_panel_0",
    )
    cabinet.visual(
        side_panel_mesh,
        origin=Origin(xyz=(CABINET_WIDTH * 0.5, 0.0, 0.0), rpy=(0.0, 0.0, math.pi)),
        material=trim_finish,
        name="side_panel_1",
    )

    lower_display = model.part("lower_display")
    _add_display_module(
        lower_display,
        outer_size=LOWER_DISPLAY_SIZE,
        glass_margin_x=0.070,
        glass_margin_z=0.090,
        frame_material=display_frame,
        glass_material=display_glass,
    )
    model.articulation(
        "cabinet_to_lower_display",
        ArticulationType.FIXED,
        parent=cabinet,
        child=lower_display,
        origin=Origin(xyz=LOWER_DISPLAY_CENTER),
    )

    top_display = model.part("top_display")
    _add_display_module(
        top_display,
        outer_size=TOP_DISPLAY_SIZE,
        glass_margin_x=0.060,
        glass_margin_z=0.060,
        frame_material=display_frame,
        glass_material=display_glass,
    )
    model.articulation(
        "cabinet_to_top_display",
        ArticulationType.FIXED,
        parent=cabinet,
        child=top_display,
        origin=Origin(xyz=TOP_DISPLAY_CENTER),
    )

    button_deck = model.part("button_deck")
    button_deck.visual(
        Box(DECK_SIZE),
        material=deck_finish,
        name="deck_body",
    )
    button_deck.visual(
        Box((DECK_SIZE[0], 0.018, 0.010)),
        origin=Origin(xyz=(0.0, -(DECK_SIZE[1] * 0.5) + 0.009, -0.010)),
        material=chrome,
        name="front_band",
    )
    model.articulation(
        "cabinet_to_button_deck",
        ArticulationType.FIXED,
        parent=cabinet,
        child=button_deck,
        origin=Origin(xyz=DECK_CENTER, rpy=(DECK_ROLL, 0.0, 0.0)),
    )

    bill_door = model.part("bill_door")
    bill_door.visual(
        mesh_from_cadquery(_build_bill_door(), "slot_bill_door"),
        material=trim_finish,
        name="door_panel",
    )
    model.articulation(
        "cabinet_to_bill_door",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=bill_door,
        origin=Origin(xyz=DOOR_HINGE_ORIGIN),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.6,
            lower=0.0,
            upper=1.35,
        ),
    )

    for index, x_pos in enumerate(BUTTON_XS):
        button = model.part(f"button_{index}")
        button.visual(
            Box(BUTTON_SIZE),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_SIZE[2] * 0.5)),
            material=button_finish,
            name="cap",
        )
        button.visual(
            Box((BUTTON_SIZE[0] * 0.68, 0.004, 0.003)),
            origin=Origin(xyz=(0.0, 0.012, 0.009)),
            material=button_light,
            name="legend",
        )
        model.articulation(
            f"button_deck_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=button_deck,
            child=button,
            origin=Origin(xyz=(x_pos, 0.0, DECK_SIZE[2] * 0.5)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(
                effort=6.0,
                velocity=0.08,
                lower=-0.003,
                upper=0.0,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
