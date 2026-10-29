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
METER_W = 0.245
METER_D = 0.205
METER_H = 0.118
HOPPER_H = 0.235
HOPPER_TOP_W = 0.228
HOPPER_TOP_D = 0.182
HOPPER_BOTTOM_W = 0.184
HOPPER_BOTTOM_D = 0.142
HOPPER_WALL = 0.0045
THROAT_W = 0.162
THROAT_D = 0.120
THROAT_H = 0.060
CHUTE_RECESS_W = 0.108
CHUTE_RECESS_D = 0.052
CHUTE_RECESS_H = 0.050
CHUTE_BOTTOM_Z = 0.022
WHEEL_R = 0.062
WHEEL_RING_THICKNESS = 0.012
WHEEL_T = 0.024
WHEEL_HUB_R = 0.022
WHEEL_CENTER_Z = 0.074
WHEEL_CENTER_Y = (METER_D / 2.0) + (WHEEL_T / 2.0)
LID_W = HOPPER_TOP_W + 0.010
LID_D = HOPPER_TOP_D + 0.012
LID_T = 0.005
LID_HINGE_R = 0.004
LID_HINGE_Y = -(HOPPER_TOP_D / 2.0) + 0.004
LID_HINGE_Z = METER_H + HOPPER_H + 0.006
FLAP_W = 0.092
FLAP_H = 0.042
FLAP_T = 0.004
FLAP_HINGE_Y = (METER_D / 2.0) - CHUTE_RECESS_D + 0.022
FLAP_HINGE_Z = CHUTE_BOTTOM_Z + 0.0022
def _build_hopper_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .rect(HOPPER_BOTTOM_W, HOPPER_BOTTOM_D)
        .workplane(offset=HOPPER_H)
        .rect(HOPPER_TOP_W, HOPPER_TOP_D)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("XY")
        .rect(HOPPER_BOTTOM_W - (2.0 * HOPPER_WALL), HOPPER_BOTTOM_D - (2.0 * HOPPER_WALL))
        .workplane(offset=HOPPER_H + 0.002)
        .rect(HOPPER_TOP_W - (2.0 * HOPPER_WALL), HOPPER_TOP_D - (2.0 * HOPPER_WALL))
        .loft(combine=True)
        .translate((0.0, 0.0, -0.001))
    )
    return outer.cut(inner).translate((0.0, 0.0, METER_H))
def _build_meter_box() -> cq.Workplane:
    box = cq.Workplane("XY").box(METER_W, METER_D, METER_H, centered=(True, True, False))

    feed_throat = (
        cq.Workplane("XY")
        .box(THROAT_W, THROAT_D, THROAT_H, centered=(True, True, False))
        .translate((0.0, 0.0, METER_H - THROAT_H))
    )

    chute_recess = (
        cq.Workplane("XY")
        .box(CHUTE_RECESS_W, CHUTE_RECESS_D + 0.002, CHUTE_RECESS_H, centered=(True, True, False))
        .translate(
            (
                0.0,
                (METER_D / 2.0) - ((CHUTE_RECESS_D + 0.002) / 2.0) + 0.001,
                CHUTE_BOTTOM_Z - 0.001,
            )
        )
    )

    wheel_boss = (
        cq.Workplane("XZ")
        .center(0.0, WHEEL_CENTER_Z)
        .circle(0.030)
        .extrude(0.007)
        .translate((0.0, (METER_D / 2.0) - 0.002, 0.0))
    )

    return box.cut(feed_throat).cut(chute_recess).union(wheel_boss)
def _build_lid() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(LID_W, LID_D, LID_T)
        .translate((0.0, (LID_D / 2.0) + 0.004, 0.0015))
    )
    front_pull = (
        cq.Workplane("XY")
        .box(0.090, 0.010, 0.006)
        .translate((0.0, LID_D + 0.001, 0.0035))
    )
    rear_bridge = (
        cq.Workplane("XY")
        .box(LID_W - 0.028, 0.012, 0.006)
        .translate((0.0, 0.004, 0.0005))
    )
    left_tab = (
        cq.Workplane("XY")
        .box(0.014, 0.010, 0.008)
        .translate((0.090, -0.004, -0.002))
    )
    right_tab = (
        cq.Workplane("XY")
        .box(0.014, 0.010, 0.008)
        .translate((-0.090, -0.004, -0.002))
    )
    hinge_barrel = cq.Workplane("YZ").circle(LID_HINGE_R).extrude((LID_W - 0.024) / 2.0, both=True)

    return panel.union(front_pull).union(rear_bridge).union(left_tab).union(right_tab).union(hinge_barrel)
def _build_wheel() -> cq.Workplane:
    ring = (
        cq.Workplane("XZ")
        .circle(WHEEL_R)
        .circle(WHEEL_R - WHEEL_RING_THICKNESS)
        .extrude(WHEEL_T / 2.0, both=True)
    )
    hub = cq.Workplane("XZ").circle(WHEEL_HUB_R).extrude(WHEEL_T / 2.0, both=True)

    wheel = ring.union(hub)
    spoke_len = (WHEEL_R - WHEEL_RING_THICKNESS) - WHEEL_HUB_R
    spoke_center_x = WHEEL_HUB_R + (spoke_len / 2.0)
    for angle in range(0, 360, 72):
        spoke = (
            cq.Workplane("XZ")
            .center(spoke_center_x, 0.0)
            .rect(spoke_len, 0.012)
            .extrude((WHEEL_T * 0.75) / 2.0, both=True)
            .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), angle)
        )
        wheel = wheel.union(spoke)

    return wheel
def _build_wheel_cap() -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(0.018)
        .extrude(0.004, both=True)
        .translate((0.0, (WHEEL_T / 2.0) - 0.002, 0.0))
    )
def _build_flap() -> cq.Workplane:
    panel = cq.Workplane("XY").box(FLAP_W, FLAP_T, FLAP_H, centered=(True, True, False))
    hinge_bead = cq.Workplane("YZ").circle(0.0032).extrude((FLAP_W - 0.008) / 2.0, both=True)
    pull_lip = (
        cq.Workplane("XY")
        .box(FLAP_W - 0.020, 0.005, 0.004)
        .translate((0.0, 0.0025, FLAP_H - 0.002))
    )
    return panel.union(hinge_bead).union(pull_lip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bulk_candy_vendor")

    model.material("clear_acrylic", rgba=(0.84, 0.94, 0.98, 0.34))
    model.material("smoked_acrylic", rgba=(0.18, 0.19, 0.21, 0.92))
    model.material("meter_box_finish", rgba=(0.61, 0.63, 0.66, 1.0))
    model.material("satin_metal", rgba=(0.77, 0.79, 0.82, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_meter_box(), "meter_box"),
        material="meter_box_finish",
        name="meter_box",
    )
    body.visual(
        mesh_from_cadquery(_build_hopper_shell(), "hopper_shell"),
        material="clear_acrylic",
        name="hopper_shell",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_build_lid(), "lid_panel"),
        material="clear_acrylic",
        name="lid_panel",
    )

    wheel = model.part("wheel")
    wheel.visual(
        mesh_from_cadquery(_build_wheel(), "dispense_wheel"),
        material="smoked_acrylic",
        name="wheel_rim",
    )
    wheel.visual(
        mesh_from_cadquery(_build_wheel_cap(), "wheel_cap"),
        material="satin_metal",
        name="wheel_cap",
    )

    flap = model.part("flap")
    flap.visual(
        mesh_from_cadquery(_build_flap(), "chute_flap"),
        material="smoked_acrylic",
        name="flap_panel",
    )

    model.articulation(
        "lid_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, LID_HINGE_Y, LID_HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.25, effort=4.0, velocity=1.6),
    )
    model.articulation(
        "wheel_spin",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=wheel,
        origin=Origin(xyz=(0.0, WHEEL_CENTER_Y, WHEEL_CENTER_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=7.0),
    )
    model.articulation(
        "flap_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flap,
        origin=Origin(xyz=(0.0, FLAP_HINGE_Y, FLAP_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.10, effort=1.0, velocity=2.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
