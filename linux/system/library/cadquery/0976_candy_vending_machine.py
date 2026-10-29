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
BASE_RADIUS = 0.18
BASE_LOWER_H = 0.018
BASE_UPPER_H = 0.028
BASE_HEIGHT = BASE_LOWER_H + BASE_UPPER_H
COLUMN_RADIUS = 0.060
COLUMN_HEIGHT = 0.57
BODY_DEPTH = 0.20
BODY_WIDTH = 0.26
BODY_HEIGHT = 0.245
BODY_BASE_Z = 0.60
BODY_TOP_Z = BODY_BASE_Z + BODY_HEIGHT
BODY_FRONT_X = BODY_DEPTH / 2.0
NECK_RADIUS = 0.058
NECK_HEIGHT = 0.055
GLOBE_RADIUS = 0.195
GLOBE_THICKNESS = 0.007
GLOBE_CENTER_Z = 1.065
GLOBE_TOP_OPEN_RADIUS = 0.070
GLOBE_BOTTOM_OPEN_RADIUS = 0.056
TOP_COLLAR_OUTER_RADIUS = 0.085
TOP_COLLAR_INNER_RADIUS = 0.066
TOP_COLLAR_HEIGHT = 0.014
TOP_COLLAR_Z0 = 1.237
TOP_COLLAR_TOP_Z = TOP_COLLAR_Z0 + TOP_COLLAR_HEIGHT
LID_RADIUS = 0.078
LID_CENTER_X = 0.077
LID_HINGE_X = -0.074
LID_HINGE_Z = TOP_COLLAR_TOP_Z
COIN_PLATE_THICKNESS = 0.016
COIN_PLATE_WIDTH = 0.165
COIN_PLATE_HEIGHT = 0.205
KNOB_AXIS_X = 0.085
KNOB_AXIS_Z = BODY_BASE_Z + 0.185
CHUTE_OUTER_DEPTH = 0.072
CHUTE_OUTER_WIDTH = 0.124
CHUTE_OUTER_HEIGHT = 0.094
CHUTE_BASE_Z = BODY_BASE_Z + 0.028
CHUTE_FRONT_X = BODY_FRONT_X + CHUTE_OUTER_DEPTH - 0.006
FLAP_HINGE_X = CHUTE_FRONT_X + 0.016
FLAP_HINGE_Z = CHUTE_BASE_Z + 0.010
def _box(size_x: float, size_y: float, size_z: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(size_x, size_y, size_z).translate(center)
def _rounded_box(
    size_x: float,
    size_y: float,
    size_z: float,
    radius: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    solid = cq.Workplane("XY").box(size_x, size_y, size_z)
    if radius > 0.0 and min(size_x, size_y) > (radius * 2.5):
        solid = solid.edges("|Z").fillet(radius)
    return solid.translate(center)
def _cyl_z(
    radius: float,
    height: float,
    z0: float,
    *,
    x: float = 0.0,
    y: float = 0.0,
) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((x, y, z0))
def _cyl_x(
    radius: float,
    length: float,
    x0: float,
    *,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((x0, y, z))
def _cyl_y(
    radius: float,
    length: float,
    y0: float,
    *,
    x: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length).translate((x, y0, z))
def _build_body_shape() -> cq.Workplane:
    base = _cyl_z(BASE_RADIUS, BASE_LOWER_H, 0.0)
    base = base.union(_cyl_z(0.132, BASE_UPPER_H, BASE_LOWER_H))

    column = _cyl_z(COLUMN_RADIUS, COLUMN_HEIGHT, BASE_HEIGHT)
    shoulder = _cyl_z(0.086, 0.036, BODY_BASE_Z - 0.018)

    housing = _rounded_box(
        BODY_DEPTH,
        BODY_WIDTH,
        BODY_HEIGHT,
        0.024,
        (0.0, 0.0, BODY_BASE_Z + (BODY_HEIGHT / 2.0)),
    )
    neck = _cyl_z(0.070, 0.016, BODY_TOP_Z - 0.010)
    neck = neck.union(_cyl_z(NECK_RADIUS, NECK_HEIGHT, BODY_TOP_Z - 0.004))

    chute = _rounded_box(
        CHUTE_OUTER_DEPTH,
        CHUTE_OUTER_WIDTH,
        CHUTE_OUTER_HEIGHT,
        0.010,
        (
            BODY_FRONT_X + (CHUTE_OUTER_DEPTH / 2.0) - 0.006,
            0.0,
            CHUTE_BASE_Z + (CHUTE_OUTER_HEIGHT / 2.0),
        ),
    )
    chute_void = _box(
        0.090,
        0.088,
        0.062,
        (
            BODY_FRONT_X + 0.048,
            0.0,
            CHUTE_BASE_Z + 0.046,
        ),
    )

    knob_tunnel = _cyl_x(0.0135, 0.150, -0.030, z=KNOB_AXIS_Z)

    flap_knuckles = _cyl_y(0.005, 0.018, -0.036, x=FLAP_HINGE_X, z=FLAP_HINGE_Z)
    flap_knuckles = flap_knuckles.union(_cyl_y(0.005, 0.018, 0.018, x=FLAP_HINGE_X, z=FLAP_HINGE_Z))
    flap_ears = _box(0.024, 0.028, 0.020, (FLAP_HINGE_X - 0.008, -0.031, FLAP_HINGE_Z))
    flap_ears = flap_ears.union(_box(0.024, 0.028, 0.020, (FLAP_HINGE_X - 0.008, 0.031, FLAP_HINGE_Z)))

    body = base.union(column).union(shoulder).union(housing).union(neck).union(chute).union(flap_ears).union(flap_knuckles)
    body = body.cut(chute_void)
    body = body.cut(knob_tunnel)
    return body
def _build_coin_plate_shape() -> cq.Workplane:
    plate = _rounded_box(
        COIN_PLATE_THICKNESS,
        COIN_PLATE_WIDTH,
        COIN_PLATE_HEIGHT,
        0.016,
        (
            BODY_FRONT_X + (COIN_PLATE_THICKNESS / 2.0) + 0.001,
            0.0,
            BODY_BASE_Z + 0.142,
        ),
    )

    boss = _cyl_x(0.039, 0.018, BODY_FRONT_X + 0.004, z=KNOB_AXIS_Z)
    boss = boss.union(_cyl_x(0.028, 0.020, BODY_FRONT_X + 0.017, z=KNOB_AXIS_Z))

    coin_slot_hood = _box(
        0.018,
        0.066,
        0.020,
        (
            BODY_FRONT_X + 0.011,
            0.0,
            KNOB_AXIS_Z + 0.068,
        ),
    )

    slot_cut = _box(
        0.030,
        0.044,
        0.006,
        (
            BODY_FRONT_X + 0.010,
            0.0,
            KNOB_AXIS_Z + 0.066,
        ),
    )
    knob_hole = _cyl_x(0.0145, 0.060, BODY_FRONT_X - 0.010, z=KNOB_AXIS_Z)

    return plate.union(boss).union(coin_slot_hood).cut(slot_cut).cut(knob_hole)
def _build_globe_shape() -> cq.Workplane:
    outer = cq.Workplane("XY").sphere(GLOBE_RADIUS).translate((0.0, 0.0, GLOBE_CENTER_Z))
    inner = cq.Workplane("XY").sphere(GLOBE_RADIUS - GLOBE_THICKNESS).translate((0.0, 0.0, GLOBE_CENTER_Z))
    globe = outer.cut(inner)
    globe = globe.cut(_cyl_z(GLOBE_TOP_OPEN_RADIUS, 0.260, GLOBE_CENTER_Z + 0.020))
    globe = globe.cut(_cyl_z(GLOBE_BOTTOM_OPEN_RADIUS, 0.260, GLOBE_CENTER_Z - GLOBE_RADIUS - 0.025))
    return globe
def _build_top_collar_shape() -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .circle(TOP_COLLAR_OUTER_RADIUS)
        .circle(TOP_COLLAR_INNER_RADIUS)
        .extrude(TOP_COLLAR_HEIGHT)
        .translate((0.0, 0.0, TOP_COLLAR_Z0))
    )
    ring = ring.cut(_box(0.038, 0.034, 0.020, (LID_HINGE_X + 0.008, 0.0, TOP_COLLAR_Z0 + 0.010)))

    hinge_bridge = _box(0.020, 0.016, 0.010, (LID_HINGE_X + 0.006, -0.026, TOP_COLLAR_Z0 + 0.007))
    hinge_bridge = hinge_bridge.union(
        _box(0.020, 0.016, 0.010, (LID_HINGE_X + 0.006, 0.026, TOP_COLLAR_Z0 + 0.007))
    )
    hinge_knuckles = _cyl_y(0.006, 0.020, -0.035, x=LID_HINGE_X, z=LID_HINGE_Z)
    hinge_knuckles = hinge_knuckles.union(_cyl_y(0.006, 0.020, 0.015, x=LID_HINGE_X, z=LID_HINGE_Z))
    return ring.union(hinge_bridge).union(hinge_knuckles)
def _build_lid_cap_shape() -> cq.Workplane:
    cap = _cyl_z(LID_RADIUS, 0.008, 0.006, x=LID_CENTER_X)
    cap = cap.union(_cyl_z(0.066, 0.006, 0.014, x=LID_CENTER_X))
    finger_lip = _box(0.012, 0.050, 0.010, (LID_CENTER_X + 0.064, 0.0, 0.010))
    return cap.union(finger_lip)
def _build_lid_hinge_shape() -> cq.Workplane:
    rear_leaf = _box(0.038, 0.032, 0.004, (0.026, 0.0, 0.013))
    hinge_arm = _box(0.022, 0.014, 0.010, (0.010, -0.006, 0.006))
    knuckle = _cyl_y(0.006, 0.026, -0.013, x=0.0, z=0.0)
    return rear_leaf.union(hinge_arm).union(knuckle)
def _build_knob_cap_shape() -> cq.Workplane:
    hub = _cyl_x(0.024, 0.016, 0.054)
    cap = _cyl_x(0.045, 0.030, 0.068)
    face = _cyl_x(0.041, 0.010, 0.098)
    ridge = _cyl_x(0.048, 0.008, 0.066)
    slot = _box(0.014, 0.048, 0.006, (0.104, 0.0, 0.0))
    return hub.union(cap).union(face).union(ridge).cut(slot)
def _build_flap_panel_shape() -> cq.Workplane:
    panel = _box(0.005, 0.092, 0.058, (0.014, 0.0, 0.029))
    pull_lip = _box(0.012, 0.092, 0.010, (0.019, 0.0, 0.051))
    return panel.union(pull_lip)
def _build_flap_leaf_shape() -> cq.Workplane:
    return _box(0.028, 0.092, 0.008, (0.0185, 0.0, 0.004))
def _build_flap_hinge_shape() -> cq.Workplane:
    return _cyl_y(0.0045, 0.030, -0.015, x=0.0, z=0.0)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pedestal_gumball_machine")

    model.material("body_red", rgba=(0.78, 0.07, 0.10, 1.0))
    model.material("cast_metal", rgba=(0.76, 0.76, 0.79, 1.0))
    model.material("globe_clear", rgba=(0.84, 0.93, 1.00, 0.28))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shape(), "body_pedestal"),
        material="body_red",
        name="pedestal",
    )
    body.visual(
        mesh_from_cadquery(_build_coin_plate_shape(), "coin_plate"),
        material="cast_metal",
        name="coin_plate",
    )
    body.visual(
        mesh_from_cadquery(_build_globe_shape(), "globe"),
        material="globe_clear",
        name="globe",
    )
    body.visual(
        mesh_from_cadquery(_build_top_collar_shape(), "top_collar"),
        material="cast_metal",
        name="top_collar",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_build_lid_cap_shape(), "refill_lid_cap"),
        material="cast_metal",
        name="lid",
    )
    lid.visual(
        mesh_from_cadquery(_build_lid_hinge_shape(), "refill_lid_hinge"),
        material="cast_metal",
        name="hinge",
    )

    knob = model.part("knob")
    knob.visual(
        Cylinder(radius=0.012, length=0.104),
        origin=Origin(xyz=(0.007, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="cast_metal",
        name="shaft",
    )
    knob.visual(
        Cylinder(radius=0.022, length=0.006),
        origin=Origin(xyz=(0.055, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="cast_metal",
        name="collar",
    )
    knob.visual(
        mesh_from_cadquery(_build_knob_cap_shape(), "dispense_knob"),
        material="cast_metal",
        name="cap",
    )

    flap = model.part("flap")
    flap.visual(
        mesh_from_cadquery(_build_flap_panel_shape(), "chute_flap_panel"),
        material="cast_metal",
        name="flap",
    )
    flap.visual(
        mesh_from_cadquery(_build_flap_leaf_shape(), "chute_flap_leaf"),
        material="cast_metal",
        name="leaf",
    )
    flap.visual(
        mesh_from_cadquery(_build_flap_hinge_shape(), "chute_flap_hinge"),
        material="cast_metal",
        name="hinge",
    )

    model.articulation(
        "lid_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(LID_HINGE_X, 0.0, LID_HINGE_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.35, effort=6.0, velocity=1.8),
    )
    model.articulation(
        "knob_spin",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=knob,
        origin=Origin(xyz=(KNOB_AXIS_X, 0.0, KNOB_AXIS_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=5.0),
    )
    model.articulation(
        "flap_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flap,
        origin=Origin(xyz=(FLAP_HINGE_X, 0.0, FLAP_HINGE_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.10, effort=3.0, velocity=2.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
