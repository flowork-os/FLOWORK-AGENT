# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_sunroof_cassette, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_sunroof_cassette

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
OUTER_L = 1.70
OUTER_W = 0.92
FRAME_H = 0.055
OPEN_L = 1.05
OPEN_W = 0.62
OPEN_X = -0.20
RAIL_Y = 0.365
RAIL_L = 1.50
RAIL_W = 0.090
RAIL_H = 0.018
SLOT_W = 0.045
SLOT_CUT_H = 0.018
SLOT_FLOOR_H = 0.003
HINGE_X = OPEN_X - OPEN_L / 2.0
HINGE_Z = 0.055
SLIDE_TRAVEL = 0.42
PANEL_L = 1.04
PANEL_W = 0.66
PANEL_T = 0.020
def _cassette_shell() -> cq.Workplane:
    """One connected cassette frame with a through roof opening and two rail grooves."""

    frame = cq.Workplane("XY").box(OUTER_L, OUTER_W, FRAME_H)
    opening = cq.Workplane("XY").box(OPEN_L, OPEN_W, FRAME_H * 3.0).translate(
        (OPEN_X, 0.0, 0.0)
    )
    frame = frame.cut(opening)

    rail_z = FRAME_H / 2.0 + RAIL_H / 2.0
    slot_top = FRAME_H / 2.0 + RAIL_H
    for y in (-RAIL_Y, RAIL_Y):
        rail = cq.Workplane("XY").box(RAIL_L, RAIL_W, RAIL_H).translate(
            (0.0, y, rail_z)
        )
        frame = frame.union(rail)

        slot_cut = cq.Workplane("XY").box(RAIL_L, SLOT_W, SLOT_CUT_H).translate(
            (0.0, y, slot_top - SLOT_CUT_H / 2.0 + 0.002)
        )
        frame = frame.cut(slot_cut)

    return frame
def _glass_slab() -> cq.Workplane:
    """Rounded smoked-glass slab with its front edge just behind the hinge axis."""

    return (
        cq.Workplane("XY")
        .box(PANEL_L, PANEL_W, PANEL_T)
        .edges("|Z")
        .fillet(0.045)
        .translate((PANEL_L / 2.0 + 0.015, 0.0, 0.008 + PANEL_T / 2.0))
    )
def _hinge_barrel(y_center: float) -> cq.Workplane:
    """A short hollow hinge knuckle around the carriage pin."""

    length = 0.110
    barrel = (
        cq.Workplane("XY")
        .circle(0.017)
        .circle(0.0085)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
        .translate((0.0, y_center, 0.0))
    )
    return barrel
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="vent_slide_sunroof_cassette")

    dark_metal = model.material("dark_anodized_aluminum", rgba=(0.045, 0.048, 0.052, 1.0))
    black_plastic = model.material("black_track_plastic", rgba=(0.008, 0.009, 0.010, 1.0))
    smoked_glass = model.material("smoked_glass", rgba=(0.045, 0.120, 0.150, 0.38))
    ceramic_black = model.material("ceramic_black_frit", rgba=(0.002, 0.002, 0.002, 0.92))
    zinc = model.material("zinc_plated_steel", rgba=(0.58, 0.60, 0.58, 1.0))

    cassette = model.part("cassette")
    cassette.visual(
        mesh_from_cadquery(_cassette_shell(), "cassette_frame"),
        material=dark_metal,
        name="frame_shell",
    )

    slot_floor_z = FRAME_H / 2.0 + RAIL_H - SLOT_CUT_H + SLOT_FLOOR_H / 2.0
    for idx, y in enumerate((-RAIL_Y, RAIL_Y)):
        cassette.visual(
            Box((RAIL_L - 0.020, SLOT_W - 0.006, SLOT_FLOOR_H)),
            origin=Origin(xyz=(0.0, y, slot_floor_z)),
            material=black_plastic,
            name=f"rail_slot_{idx}",
        )

    # Shallow drain pockets at the cassette corners give the frame real sunroof
    # cassette character while remaining physically seated on the shell.
    for idx, (x, y) in enumerate(
        (
            (OPEN_X - OPEN_L / 2.0 - 0.050, -0.405),
            (OPEN_X - OPEN_L / 2.0 - 0.050, 0.405),
            (OPEN_X + OPEN_L / 2.0 + 0.070, -0.405),
            (OPEN_X + OPEN_L / 2.0 + 0.070, 0.405),
        )
    ):
        cassette.visual(
            Box((0.080, 0.055, 0.004)),
            origin=Origin(xyz=(x, y, FRAME_H / 2.0 + 0.002)),
            material=black_plastic,
            name=f"drain_pocket_{idx}",
        )

    carriage = model.part("carriage")
    carriage.visual(
        Cylinder(radius=0.0085, length=0.750),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=zinc,
        name="hinge_pin",
    )

    for idx, y in enumerate((-RAIL_Y, RAIL_Y)):
        carriage.visual(
            Box((0.480, 0.026, 0.009)),
            origin=Origin(xyz=(0.300, y, -0.020)),
            material=black_plastic,
            name=f"shoe_{idx}",
        )
        carriage.visual(
            Box((0.085, 0.024, 0.024)),
            origin=Origin(xyz=(0.035, y, -0.007)),
            material=zinc,
            name=f"front_bracket_{idx}",
        )

    glass_panel = model.part("glass_panel")
    glass_panel.visual(
        mesh_from_cadquery(_glass_slab(), "smoked_glass_panel"),
        material=smoked_glass,
        name="glass_slab",
    )
    glass_panel.visual(
        Box((0.090, PANEL_W - 0.070, 0.003)),
        origin=Origin(xyz=(0.060, 0.0, 0.0285)),
        material=ceramic_black,
        name="front_frit",
    )
    glass_panel.visual(
        Box((0.085, PANEL_W - 0.070, 0.003)),
        origin=Origin(xyz=(PANEL_L + 0.005, 0.0, 0.0285)),
        material=ceramic_black,
        name="rear_frit",
    )
    for idx, y in enumerate((-(PANEL_W / 2.0 - 0.020), PANEL_W / 2.0 - 0.020)):
        glass_panel.visual(
            Box((PANEL_L - 0.100, 0.032, 0.003)),
            origin=Origin(xyz=(0.545, y, 0.0285)),
            material=ceramic_black,
            name=f"side_frit_{idx}",
        )
    for idx, y in enumerate((-0.220, 0.0, 0.220)):
        glass_panel.visual(
            mesh_from_cadquery(_hinge_barrel(y), f"glass_hinge_barrel_{idx}"),
            material=ceramic_black,
            name=f"hinge_barrel_{idx}",
        )
        glass_panel.visual(
            Box((0.050, 0.070, 0.018)),
            origin=Origin(xyz=(0.025, y, 0.019)),
            material=ceramic_black,
            name=f"hinge_strap_{idx}",
        )

    model.articulation(
        "cassette_to_carriage",
        ArticulationType.PRISMATIC,
        parent=cassette,
        child=carriage,
        origin=Origin(xyz=(HINGE_X, 0.0, HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=180.0, velocity=0.35, lower=0.0, upper=SLIDE_TRAVEL),
    )
    model.articulation(
        "carriage_to_glass",
        ArticulationType.REVOLUTE,
        parent=carriage,
        child=glass_panel,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=45.0, velocity=1.2, lower=0.0, upper=0.23),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
