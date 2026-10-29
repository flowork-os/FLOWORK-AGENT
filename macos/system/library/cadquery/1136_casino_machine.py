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
CABINET_DEPTH = 0.55
CABINET_HEIGHT = 1.68
FRONT_Y = -CABINET_DEPTH / 2.0
def _mat(name: str, rgba: tuple[float, float, float, float]) -> Material:
    return Material(name, rgba=rgba)
def _cabinet_shell() -> cq.Workplane:
    """Filleted cabinet body with a real through-window and a shallow tray recess."""
    body = (
        cq.Workplane("XY")
        .box(CABINET_WIDTH, CABINET_DEPTH, CABINET_HEIGHT)
        .translate((0.0, 0.0, CABINET_HEIGHT / 2.0))
    )
    body = body.edges("|Z").fillet(0.035)
    body = body.edges(">Z").fillet(0.012)

    # The reel bay is a genuine opening, not a painted-on rectangle.
    reel_window_cut = (
        cq.Workplane("XY")
        .box(0.64, CABINET_DEPTH * 1.35, 0.38)
        .translate((0.0, 0.0, 1.07))
    )
    body = body.cut(reel_window_cut)

    # A front-only coin payout recess behind the hinged flap.
    tray_recess_cut = (
        cq.Workplane("XY")
        .box(0.50, 0.20, 0.24)
        .translate((0.0, FRONT_Y + 0.10, 0.43))
    )
    body = body.cut(tray_recess_cut)
    return body
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="classic_upright_slot_machine")

    red = _mat("deep_lacquer_red", (0.55, 0.02, 0.025, 1.0))
    dark_red = _mat("dark_red_shadow", (0.23, 0.01, 0.012, 1.0))
    chrome = _mat("polished_chrome", (0.82, 0.78, 0.70, 1.0))
    black = _mat("black_enamel", (0.006, 0.006, 0.007, 1.0))
    cream = _mat("aged_reel_ivory", (0.92, 0.84, 0.64, 1.0))
    brass = _mat("warm_brass", (0.90, 0.58, 0.16, 1.0))
    glass = _mat("slightly_blue_glass", (0.55, 0.80, 1.00, 0.33))
    white = _mat("milk_glass_white", (0.98, 0.95, 0.86, 1.0))
    symbol_red = _mat("symbol_red", (0.90, 0.06, 0.03, 1.0))
    symbol_black = _mat("symbol_black", (0.02, 0.02, 0.02, 1.0))
    symbol_gold = _mat("symbol_gold", (1.00, 0.78, 0.05, 1.0))
    symbol_green = _mat("symbol_green", (0.03, 0.45, 0.16, 1.0))

    cabinet = model.part("cabinet")
    cabinet.visual(
        mesh_from_cadquery(_cabinet_shell(), "cabinet_shell", tolerance=0.002),
        material=red,
        name="cabinet_shell",
    )

    # Substantial plinth and front treatment.
    cabinet.visual(
        Box((0.86, 0.62, 0.10)),
        origin=Origin(xyz=(0.0, 0.0, 0.05)),
        material=dark_red,
        name="base_plinth",
    )
    cabinet.visual(
        Box((0.56, 0.020, 0.20)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.010, 1.48)),
        material=brass,
        name="marquee_panel",
    )
    for x in (-0.22, -0.11, 0.0, 0.11, 0.22):
        cabinet.visual(
            Sphere(0.020),
            origin=Origin(xyz=(x, FRONT_Y - 0.026, 1.55)),
            material=white,
            name=f"marquee_bulb_{int((x + 0.22) * 100):02d}",
        )

    # Chrome and glass reel window.
    frame_y = FRONT_Y - 0.012
    cabinet.visual(
        Box((0.70, 0.024, 0.040)),
        origin=Origin(xyz=(0.0, frame_y, 1.285)),
        material=chrome,
        name="window_top_rail",
    )
    cabinet.visual(
        Box((0.70, 0.024, 0.040)),
        origin=Origin(xyz=(0.0, frame_y, 0.855)),
        material=chrome,
        name="window_bottom_rail",
    )
    for x, name in ((-0.345, "window_side_0"), (0.345, "window_side_1")):
        cabinet.visual(
            Box((0.035, 0.024, 0.430)),
            origin=Origin(xyz=(x, frame_y, 1.070)),
            material=chrome,
            name=name,
        )
    for x, name in ((-0.095, "reel_divider_0"), (0.095, "reel_divider_1")):
        cabinet.visual(
            Box((0.018, 0.024, 0.420)),
            origin=Origin(xyz=(x, frame_y, 1.070)),
            material=chrome,
            name=name,
        )
    cabinet.visual(
        Box((0.670, 0.006, 0.405)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.015, 1.070)),
        material=glass,
        name="glass_pane",
    )
    cabinet.visual(
        Box((0.680, 0.010, 0.012)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.018, 1.070)),
        material=symbol_red,
        name="payline_mark",
    )

    # Coin slot and fixed payout tray structure.
    cabinet.visual(
        Box((0.22, 0.018, 0.055)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.009, 0.705)),
        material=chrome,
        name="coin_slot_plate",
    )
    cabinet.visual(
        Box((0.135, 0.010, 0.012)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.017, 0.705)),
        material=black,
        name="coin_slot",
    )
    cabinet.visual(
        Box((0.56, 0.18, 0.035)),
        origin=Origin(xyz=(0.0, FRONT_Y - 0.075, 0.280)),
        material=chrome,
        name="tray_floor",
    )
    for x, name in ((-0.28, "tray_cheek_0"), (0.28, "tray_cheek_1")):
        cabinet.visual(
            Box((0.040, 0.18, 0.160)),
            origin=Origin(xyz=(x, FRONT_Y - 0.075, 0.360)),
            material=chrome,
            name=name,
        )
    for x, name in ((-0.260, "tray_hinge_barrel_0"), (0.260, "tray_hinge_barrel_1")):
        cabinet.visual(
            Cylinder(radius=0.011, length=0.080),
            origin=Origin(xyz=(x, FRONT_Y - 0.040, 0.340), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name=name,
        )

    # Side lever bearing fixed to the right side of the cabinet.
    cabinet.visual(
        Box((0.020, 0.18, 0.18)),
        origin=Origin(xyz=(CABINET_WIDTH / 2.0 + 0.010, -0.045, 1.150)),
        material=chrome,
        name="lever_side_plate",
    )
    cabinet.visual(
        Cylinder(radius=0.065, length=0.035),
        origin=Origin(
            xyz=(CABINET_WIDTH / 2.0 + 0.0175, -0.045, 1.150),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=chrome,
        name="lever_bearing",
    )

    # Stationary rear shaft rail and paired end bearings: these physically carry
    # the rotating reels while leaving the visible reel drums unobstructed.
    cabinet.visual(
        Box((0.660, 0.030, 0.030)),
        origin=Origin(xyz=(0.0, 0.035, 1.070)),
        material=chrome,
        name="reel_shaft_rail",
    )
    for i, x in enumerate((-0.190, 0.0, 0.190)):
        for side, dx in (("a", -0.084 - 0.009), ("b", 0.084 + 0.009)):
            cabinet.visual(
                Box((0.018, 0.035, 0.035)),
                origin=Origin(xyz=(x + dx, -0.120, 1.070)),
                material=chrome,
                name=f"reel_bearing_{i}_{side}",
            )
            cabinet.visual(
                Box((0.014, 0.185, 0.026)),
                origin=Origin(xyz=(x + dx, -0.0425, 1.070)),
                material=chrome,
                name=f"reel_bearing_bridge_{i}_{side}",
            )

    # Three independent continuously rotating reels behind the glass.
    reel_xs = (-0.190, 0.0, 0.190)
    symbol_materials = [
        (symbol_red, symbol_gold, symbol_black),
        (symbol_gold, symbol_black, symbol_green),
        (symbol_green, symbol_red, symbol_gold),
    ]
    for i, x in enumerate(reel_xs):
        reel = model.part(f"reel_{i}")
        reel.visual(
            Cylinder(radius=0.130, length=0.145),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=cream,
            name="reel_cylinder",
        )
        reel.visual(
            Cylinder(radius=0.036, length=0.168),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=chrome,
            name="shaft_hub",
        )
        for j, (z, material) in enumerate(zip((-0.040, 0.0, 0.040), symbol_materials[i])):
            y = -math.sqrt(0.130**2 - z**2) - 0.003
            reel.visual(
                Box((0.102, 0.008, 0.044)),
                origin=Origin(xyz=(0.0, y, z)),
                material=material,
                name=f"symbol_tile_{j}",
            )
        model.articulation(
            f"cabinet_to_reel_{i}",
            ArticulationType.CONTINUOUS,
            parent=cabinet,
            child=reel,
            origin=Origin(xyz=(x, -0.120, 1.070)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=20.0),
        )

    # Pull lever: a hub, upright arm, and ball knob rotating in the side plane.
    lever = model.part("side_lever")
    lever.visual(
        Cylinder(radius=0.060, length=0.046),
        origin=Origin(xyz=(0.023, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=chrome,
        name="lever_hub",
    )
    lever.visual(
        Cylinder(radius=0.018, length=0.420),
        origin=Origin(xyz=(0.055, 0.0, 0.210)),
        material=chrome,
        name="lever_arm",
    )
    lever.visual(
        Sphere(0.055),
        origin=Origin(xyz=(0.055, 0.0, 0.475)),
        material=white,
        name="handle_ball",
    )
    model.articulation(
        "cabinet_to_side_lever",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=lever,
        origin=Origin(xyz=(CABINET_WIDTH / 2.0 + 0.035, -0.045, 1.150)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=3.0, lower=0.0, upper=1.25),
    )

    # Hinged lower payout-tray flap.
    flap = model.part("tray_flap")
    flap.visual(
        Cylinder(radius=0.010, length=0.440),
        origin=Origin(xyz=(0.0, 0.0, -0.008), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=chrome,
        name="flap_hinge_knuckle",
    )
    flap.visual(
        Box((0.440, 0.040, 0.160)),
        origin=Origin(xyz=(0.0, -0.018, 0.080)),
        material=brass,
        name="flap_panel",
    )
    flap.visual(
        Box((0.405, 0.012, 0.065)),
        origin=Origin(xyz=(0.0, -0.044, 0.090)),
        material=black,
        name="flap_recess",
    )
    flap.visual(
        Box((0.440, 0.030, 0.020)),
        origin=Origin(xyz=(0.0, -0.026, 0.170)),
        material=chrome,
        name="flap_top_lip",
    )
    model.articulation(
        "cabinet_to_tray_flap",
        ArticulationType.REVOLUTE,
        parent=cabinet,
        child=flap,
        origin=Origin(xyz=(0.0, FRONT_Y - 0.040, 0.350)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=0.0, upper=1.05),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
