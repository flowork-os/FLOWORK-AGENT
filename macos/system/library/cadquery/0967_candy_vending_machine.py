# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, candy_vending_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: candy_vending_machine

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
BASE_WIDTH = 0.228
BASE_DEPTH = 0.190
BASE_BODY_HEIGHT = 0.118
SHOULDER_RING_HEIGHT = 0.016
CANISTER_OUTER_RADIUS = 0.106
CANISTER_INNER_RADIUS = 0.101
CANISTER_HEIGHT = 0.250
CANISTER_APOTHEM = CANISTER_OUTER_RADIUS * math.cos(math.pi / 8.0)
CAP_RADIUS = 0.110
CAP_THICKNESS = 0.012
CAP_CLEARANCE = 0.0
DOOR_WIDTH = 0.092
DOOR_HEIGHT = 0.074
DOOR_THICKNESS = 0.008
def _regular_polygon_points(radius: float, *, sides: int = 8, rotation: float = math.pi / 8.0) -> list[tuple[float, float]]:
    return [
        (
            radius * math.cos(rotation + (2.0 * math.pi * index) / sides),
            radius * math.sin(rotation + (2.0 * math.pi * index) / sides),
        )
        for index in range(sides)
    ]
def _profile(points: list[tuple[float, float]]) -> cq.Workplane:
    wire = cq.Workplane("XY").moveTo(*points[0])
    for x_coord, y_coord in points[1:]:
        wire = wire.lineTo(x_coord, y_coord)
    return wire.close()
def _octagon_prism(radius: float, height: float) -> cq.Workplane:
    return _profile(_regular_polygon_points(radius)).extrude(height)
def _base_body_shape() -> cq.Workplane:
    lower = (
        cq.Workplane("XY")
        .box(BASE_WIDTH, BASE_DEPTH, 0.082, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.012)
    )
    upper = (
        cq.Workplane("XY")
        .box(0.186, 0.150, 0.036, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.010)
        .translate((0.0, 0.0, 0.082))
    )
    return lower.union(upper)
def _shoulder_ring_shape() -> cq.Workplane:
    outer = _octagon_prism(0.112, SHOULDER_RING_HEIGHT)
    inner = _octagon_prism(0.1015, SHOULDER_RING_HEIGHT)
    return outer.cut(inner)
def _canister_shape() -> cq.Workplane:
    outer = _octagon_prism(CANISTER_OUTER_RADIUS, CANISTER_HEIGHT)
    inner = _octagon_prism(CANISTER_INNER_RADIUS, CANISTER_HEIGHT)
    shell = outer.cut(inner)

    lower_band = _octagon_prism(CANISTER_OUTER_RADIUS, 0.020).cut(_octagon_prism(0.096, 0.020))
    top_band = (
        _octagon_prism(CANISTER_OUTER_RADIUS, 0.016)
        .cut(_octagon_prism(0.0975, 0.016))
        .translate((0.0, 0.0, CANISTER_HEIGHT - 0.016))
    )
    hinge_bridge = (
        cq.Workplane("XY")
        .box(0.074, 0.012, 0.010, centered=(True, True, False))
        .translate((0.0, -CANISTER_APOTHEM, CANISTER_HEIGHT - 0.010))
    )
    return shell.union(lower_band).union(top_band).union(hinge_bridge)
def _cap_shape() -> cq.Workplane:
    points = _regular_polygon_points(CAP_RADIUS)
    min_y = min(y_coord for _, y_coord in points)
    max_y = max(y_coord for _, y_coord in points)
    shifted = [(x_coord, y_coord - min_y) for x_coord, y_coord in points]

    panel = _profile(shifted).extrude(CAP_THICKNESS)
    hinge_leaf = (
        cq.Workplane("XY")
        .box(0.074, 0.010, 0.008, centered=(True, True, False))
        .translate((0.0, -0.005, 0.0))
    )
    finger_lip = (
        cq.Workplane("XY")
        .box(0.060, 0.009, 0.008, centered=(True, True, False))
        .translate((0.0, max_y - min_y + 0.0045, CAP_THICKNESS - 0.008))
    )
    return panel.union(hinge_leaf).union(finger_lip)
def _chute_tray_shape() -> cq.Workplane:
    tray = (
        cq.Workplane("XZ")
        .moveTo(-0.032, 0.0)
        .lineTo(0.032, 0.0)
        .lineTo(0.029, 0.005)
        .lineTo(0.023, 0.014)
        .lineTo(-0.023, 0.014)
        .lineTo(-0.029, 0.005)
        .close()
        .extrude(0.034, both=True)
        .translate((0.0, BASE_DEPTH / 2.0 + 0.017, 0.014))
    )
    lip = (
        cq.Workplane("XY")
        .box(0.060, 0.006, 0.005, centered=(True, True, False))
        .translate((0.0, BASE_DEPTH / 2.0 + 0.031, 0.024))
    )
    return tray.union(lip)
def _chute_hood_shape() -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .moveTo(-0.038, 0.0)
        .lineTo(0.038, 0.0)
        .lineTo(0.030, 0.018)
        .lineTo(-0.030, 0.018)
        .close()
        .extrude(0.026, both=True)
        .translate((0.0, BASE_DEPTH / 2.0 + 0.011, 0.026))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="octagonal_jellybean_dispenser")

    cast_metal = model.material("cast_metal", rgba=(0.56, 0.53, 0.49, 1.0))
    dark_metal = model.material("dark_metal", rgba=(0.24, 0.24, 0.25, 1.0))
    coin_metal = model.material("coin_metal", rgba=(0.74, 0.76, 0.78, 1.0))
    chute_dark = model.material("chute_dark", rgba=(0.22, 0.18, 0.16, 1.0))
    clear_tint = model.material("clear_tint", rgba=(0.76, 0.92, 0.97, 0.28))
    cap_red = model.material("cap_red", rgba=(0.70, 0.12, 0.10, 1.0))
    knob_red = model.material("knob_red", rgba=(0.78, 0.10, 0.10, 1.0))

    base = model.part("base")
    base.visual(mesh_from_cadquery(_base_body_shape(), "base_body"), material=cast_metal, name="body")
    base.visual(
        mesh_from_cadquery(_shoulder_ring_shape(), "shoulder_ring"),
        origin=Origin(xyz=(0.0, 0.0, BASE_BODY_HEIGHT - SHOULDER_RING_HEIGHT)),
        material=dark_metal,
        name="shoulder_ring",
    )
    base.visual(
        Box((0.072, 0.016, 0.060)),
        origin=Origin(xyz=(0.0, BASE_DEPTH / 2.0 - 0.008, 0.084)),
        material=coin_metal,
        name="coin_plate",
    )
    base.visual(
        Box((0.026, 0.004, 0.004)),
        origin=Origin(xyz=(0.0, BASE_DEPTH / 2.0 + 0.0005, 0.100)),
        material=dark_metal,
        name="coin_slot",
    )
    base.visual(
        Cylinder(radius=0.028, length=0.008),
        origin=Origin(xyz=(0.0, BASE_DEPTH / 2.0 + 0.004, 0.060), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=cast_metal,
        name="hub",
    )
    base.visual(mesh_from_cadquery(_chute_hood_shape(), "chute_hood"), material=cast_metal, name="chute_hood")
    base.visual(mesh_from_cadquery(_chute_tray_shape(), "chute_tray"), material=chute_dark, name="chute_tray")

    canister = model.part("canister")
    canister.visual(mesh_from_cadquery(_canister_shape(), "canister_shell"), material=clear_tint, name="canister_shell")

    cap = model.part("cap")
    cap.visual(mesh_from_cadquery(_cap_shape(), "refill_cap"), material=cap_red, name="cap_panel")

    knob = model.part("dispense_knob")
    knob.visual(
        Cylinder(radius=0.006, length=0.006),
        origin=Origin(xyz=(0.0, 0.003, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="shaft",
    )
    knob.visual(
        Cylinder(radius=0.019, length=0.018),
        origin=Origin(xyz=(0.0, 0.015, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_red,
        name="knob_body",
    )
    knob.visual(
        Box((0.010, 0.018, 0.004)),
        origin=Origin(xyz=(0.0, 0.015, 0.010)),
        material=coin_metal,
        name="pointer_rib",
    )

    door = model.part("service_door")
    door.visual(
        Box((DOOR_WIDTH, DOOR_THICKNESS, DOOR_HEIGHT)),
        origin=Origin(xyz=(DOOR_WIDTH / 2.0, DOOR_THICKNESS / 2.0, DOOR_HEIGHT / 2.0)),
        material=cast_metal,
        name="door_panel",
    )
    door.visual(
        Box((0.012, 0.005, 0.028)),
        origin=Origin(xyz=(DOOR_WIDTH - 0.014, DOOR_THICKNESS + 0.0025, DOOR_HEIGHT / 2.0)),
        material=dark_metal,
        name="door_pull",
    )

    model.articulation(
        "base_to_canister",
        ArticulationType.FIXED,
        parent=base,
        child=canister,
        origin=Origin(xyz=(0.0, 0.0, BASE_BODY_HEIGHT)),
    )
    model.articulation(
        "canister_to_cap",
        ArticulationType.REVOLUTE,
        parent=canister,
        child=cap,
        origin=Origin(xyz=(0.0, -CANISTER_APOTHEM, CANISTER_HEIGHT + CAP_CLEARANCE)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=2.4, lower=0.0, upper=1.30),
    )
    model.articulation(
        "base_to_dispense_knob",
        ArticulationType.CONTINUOUS,
        parent=base,
        child=knob,
        origin=Origin(xyz=(0.0, BASE_DEPTH / 2.0 + 0.008, 0.060)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.25, velocity=6.0),
    )
    model.articulation(
        "base_to_service_door",
        ArticulationType.REVOLUTE,
        parent=base,
        child=door,
        origin=Origin(
            xyz=(
                -DOOR_WIDTH / 2.0,
                -(BASE_DEPTH / 2.0 + DOOR_THICKNESS),
                0.026,
            )
        ),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=0.6, velocity=1.5, lower=0.0, upper=1.35),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
