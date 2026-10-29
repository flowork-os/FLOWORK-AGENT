# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_fryer_with_pullout_basket, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_fryer_with_pullout_basket

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
BODY_WIDTH = 0.340
DRAWER_SEAT_X = 0.150
DRAWER_CENTER_Z = 0.126
DRAWER_TRAVEL = 0.170
PANEL_LOWER_X = 0.182
PANEL_LOWER_Z = 0.278
PANEL_UPSLOPE_RUN = 0.106
PANEL_UPSLOPE_RISE = 0.082
PANEL_PITCH = math.atan2(PANEL_UPSLOPE_RISE, PANEL_UPSLOPE_RUN)
PANEL_TAN_X = -math.cos(PANEL_PITCH)
PANEL_TAN_Z = math.sin(PANEL_PITCH)
PANEL_NORM_X = math.sin(PANEL_PITCH)
PANEL_NORM_Z = math.cos(PANEL_PITCH)
def _panel_point(distance_up: float, lateral: float, normal_offset: float = 0.0) -> tuple[float, float, float]:
    return (
        PANEL_LOWER_X + PANEL_TAN_X * distance_up + PANEL_NORM_X * normal_offset,
        lateral,
        PANEL_LOWER_Z + PANEL_TAN_Z * distance_up + PANEL_NORM_Z * normal_offset,
    )
def _panel_origin(distance_up: float, lateral: float, normal_offset: float = 0.0) -> Origin:
    return Origin(
        xyz=_panel_point(distance_up, lateral, normal_offset),
        rpy=(0.0, PANEL_PITCH, 0.0),
    )
def _make_drawer_shell() -> cq.Workplane:
    drawer_length = 0.262
    drawer_width = 0.292
    drawer_height = 0.146
    wall = 0.005
    drawer_bottom = -0.074
    drawer_center_x = -0.126

    shell = (
        cq.Workplane("XY")
        .box(drawer_length, drawer_width, drawer_height, centered=(True, True, False))
        .translate((drawer_center_x, 0.0, drawer_bottom))
    )
    cavity = (
        cq.Workplane("XY")
        .box(drawer_length - 2.0 * wall, drawer_width - 2.0 * wall, drawer_height - wall, centered=(True, True, False))
        .translate((drawer_center_x - 0.003, 0.0, drawer_bottom + wall))
    )
    shell = shell.cut(cavity.val())

    rear_window = (
        cq.Workplane("XY")
        .box(0.040, drawer_width - 0.040, 0.070, centered=(True, True, False))
        .translate((-0.248, 0.0, -0.020))
    )
    shell = shell.cut(rear_window.val())

    fascia = (
        cq.Workplane("XY")
        .box(0.028, 0.312, 0.160, centered=(True, True, True))
        .translate((0.014, 0.0, 0.000))
    )

    handle = (
        cq.Workplane("XY")
        .box(0.058, 0.112, 0.030, centered=(True, True, False))
        .translate((0.044, 0.0, 0.006))
    )
    handle_grip = (
        cq.Workplane("XY")
        .box(0.038, 0.082, 0.015, centered=(True, True, False))
        .translate((0.052, 0.0, 0.006))
    )
    handle = handle.cut(handle_grip.val())

    latch_pocket = (
        cq.Workplane("XY")
        .box(0.022, 0.040, 0.014, centered=(True, True, False))
        .translate((0.050, 0.0, 0.022))
    )
    handle = handle.cut(latch_pocket.val())

    shell = shell.union(fascia.val()).union(handle.val())

    slot_length = 0.215
    slot_depth = 0.0032
    slot_height = 0.012
    slot_center_x = -0.140
    slot_base_z = 0.018
    half_width = drawer_width / 2.0
    for sign in (-1.0, 1.0):
        slot = (
            cq.Workplane("XY")
            .box(slot_length, slot_depth, slot_height, centered=(True, True, False))
            .translate((slot_center_x, sign * (half_width - slot_depth / 2.0), slot_base_z))
        )
        shell = shell.cut(slot.val())

    return shell
def _make_basket_shell() -> cq.Workplane:
    basket_length = 0.210
    basket_width = 0.248
    basket_height = 0.096
    wall = 0.003
    basket_bottom = -0.058
    basket_center_x = -0.148

    basket = (
        cq.Workplane("XY")
        .box(basket_length, basket_width, basket_height, centered=(True, True, False))
        .translate((basket_center_x, 0.0, basket_bottom))
    )
    inner = (
        cq.Workplane("XY")
        .box(basket_length - 2.0 * wall, basket_width - 2.0 * wall, basket_height - wall, centered=(True, True, False))
        .translate((basket_center_x, 0.0, basket_bottom + wall))
    )
    basket = basket.cut(inner.val())

    for foot_y in (-0.086, 0.086):
        foot = (
            cq.Workplane("XY")
            .box(0.132, 0.012, 0.011, centered=(True, True, False))
            .translate((basket_center_x - 0.010, foot_y, basket_bottom - 0.011))
        )
        basket = basket.union(foot.val())

    for slot_x in (-0.072, -0.028, 0.016):
        for slot_y in (-0.064, 0.0, 0.064):
            bottom_slot = (
                cq.Workplane("XY")
                .box(0.028, 0.018, 0.006, centered=(True, True, False))
                .translate((basket_center_x + slot_x, slot_y, basket_bottom - 0.001))
            )
            basket = basket.cut(bottom_slot.val())

    side_slot_centers = (-0.066, -0.016, 0.030)
    for sign in (-1.0, 1.0):
        for slot_x in side_slot_centers:
            side_slot = (
                cq.Workplane("XY")
                .box(0.032, 0.008, 0.026, centered=(True, True, False))
                .translate((basket_center_x + slot_x, sign * (basket_width / 2.0), basket_bottom + 0.024))
            )
            basket = basket.cut(side_slot.val())

    return basket
def _make_button(cap_x: float, cap_y: float, cap_height: float, stem_x: float, stem_y: float, stem_depth: float):
    cap = cq.Workplane("XY").box(cap_x, cap_y, cap_height, centered=(True, True, False))
    stem = (
        cq.Workplane("XY")
        .box(stem_x, stem_y, stem_depth, centered=(True, True, False))
        .translate((0.0, 0.0, -stem_depth))
    )
    return cap.union(stem.val())
def _make_selector_knob():
    stem = cq.Workplane("XY").circle(0.007).extrude(0.004).translate((0.0, 0.0, -0.004))
    skirt = cq.Workplane("XY").circle(0.025).extrude(0.004)
    body = cq.Workplane("XY").circle(0.021).extrude(0.016).translate((0.0, 0.0, 0.004))
    crown = cq.Workplane("XY").circle(0.018).extrude(0.008).translate((0.0, 0.0, 0.020))
    knob = stem.union(skirt.val()).union(body.val()).union(crown.val())
    indicator = (
        cq.Workplane("XY")
        .box(0.010, 0.0024, 0.0018, centered=(True, True, False))
        .translate((0.010, 0.0, 0.027))
    )
    return knob.union(indicator.val())
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="large_family_air_fryer")

    body_mat = model.material("body_matte_black", rgba=(0.11, 0.12, 0.13, 1.0))
    trim_mat = model.material("trim_dark_grey", rgba=(0.18, 0.19, 0.20, 1.0))
    drawer_mat = model.material("drawer_graphite", rgba=(0.16, 0.17, 0.18, 1.0))
    basket_mat = model.material("basket_dark", rgba=(0.24, 0.25, 0.26, 1.0))
    metal_mat = model.material("metal_grey", rgba=(0.58, 0.60, 0.62, 1.0))
    button_mat = model.material("button_black", rgba=(0.12, 0.13, 0.14, 1.0))
    latch_mat = model.material("latch_red", rgba=(0.79, 0.16, 0.13, 1.0))

    body = model.part("body")
    body.visual(
        Box((0.368, BODY_WIDTH, 0.012)),
        origin=Origin(xyz=(0.000, 0.000, 0.006)),
        material=body_mat,
        name="base_shell",
    )
    body.visual(
        Box((0.014, 0.320, 0.348)),
        origin=Origin(xyz=(-0.189, 0.000, 0.174)),
        material=body_mat,
        name="rear_shell",
    )
    body.visual(
        Box((0.330, 0.012, 0.236)),
        origin=Origin(xyz=(-0.021, -0.164, 0.174)),
        material=body_mat,
        name="left_shell",
    )
    body.visual(
        Box((0.330, 0.012, 0.236)),
        origin=Origin(xyz=(-0.021, 0.164, 0.174)),
        material=body_mat,
        name="right_shell",
    )
    body.visual(
        Box((0.270, 0.320, 0.012)),
        origin=Origin(xyz=(-0.061, 0.000, 0.354)),
        material=body_mat,
        name="top_shell",
    )
    body.visual(
        Box((0.136, 0.320, 0.012)),
        origin=_panel_origin(0.068, 0.0),
        material=body_mat,
        name="sloped_panel",
    )
    body.visual(
        Box((0.020, 0.320, 0.050)),
        origin=Origin(xyz=(0.141, 0.000, 0.255)),
        material=body_mat,
        name="front_upper",
    )
    body.visual(
        Box((0.020, 0.274, 0.040)),
        origin=Origin(xyz=(0.140, 0.000, 0.020)),
        material=body_mat,
        name="lower_sill",
    )
    body.visual(
        Box((0.018, 0.012, 0.194)),
        origin=Origin(xyz=(0.141, -0.164, 0.137)),
        material=body_mat,
        name="left_frame",
    )
    body.visual(
        Box((0.018, 0.012, 0.194)),
        origin=Origin(xyz=(0.141, 0.164, 0.137)),
        material=body_mat,
        name="right_frame",
    )

    rail_length = 0.250
    rail_thickness = 0.014
    rail_height = 0.012
    rail_center_x = 0.004
    rail_center_z = 0.150
    rail_center_y = 0.151
    body.visual(
        Box((rail_length, rail_thickness, rail_height)),
        origin=Origin(xyz=(rail_center_x, -rail_center_y, rail_center_z)),
        material=metal_mat,
        name="left_guide",
    )
    body.visual(
        Box((rail_length, rail_thickness, rail_height)),
        origin=Origin(xyz=(rail_center_x, rail_center_y, rail_center_z)),
        material=metal_mat,
        name="right_guide",
    )

    drawer = model.part("drawer")
    drawer.visual(
        mesh_from_cadquery(_make_drawer_shell(), "air_fryer_drawer"),
        material=drawer_mat,
        name="drawer_shell",
    )

    basket = model.part("basket")
    basket.visual(
        mesh_from_cadquery(_make_basket_shell(), "air_fryer_basket"),
        material=basket_mat,
        name="basket_shell",
    )

    selector_knob = model.part("selector_knob")
    selector_knob.visual(
        mesh_from_cadquery(_make_selector_knob(), "air_fryer_selector_knob"),
        material=trim_mat,
        name="knob",
    )

    preset_origins = (-0.105, -0.035, 0.035, 0.105)
    preset_buttons = []
    for index, lateral in enumerate(preset_origins):
        button = model.part(f"preset_button_{index}")
        button.visual(
            mesh_from_cadquery(
                _make_button(0.020, 0.050, 0.006, 0.010, 0.032, 0.003),
                f"air_fryer_preset_button_{index}",
            ),
            material=button_mat,
            name="button",
        )
        preset_buttons.append((button, lateral))

    latch_button = model.part("latch_button")
    latch_button.visual(
        mesh_from_cadquery(
            _make_button(0.022, 0.032, 0.006, 0.014, 0.020, 0.004),
            "air_fryer_latch_button",
        ),
        material=latch_mat,
        name="button",
    )

    drawer_joint = model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(DRAWER_SEAT_X, 0.0, DRAWER_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=120.0,
            velocity=0.35,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )
    basket_joint = model.articulation(
        "drawer_to_basket",
        ArticulationType.FIXED,
        parent=drawer,
        child=basket,
        origin=Origin(),
    )

    model.articulation(
        "body_to_selector_knob",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=selector_knob,
        origin=_panel_origin(0.074, 0.0, 0.010),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.5, velocity=8.0),
    )

    for index, (button, lateral) in enumerate(preset_buttons):
        model.articulation(
            f"body_to_preset_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=_panel_origin(0.032, lateral, 0.009),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=16.0,
                velocity=0.10,
                lower=0.0,
                upper=0.004,
            ),
        )

    model.articulation(
        "drawer_to_latch_button",
        ArticulationType.PRISMATIC,
        parent=drawer,
        child=latch_button,
        origin=Origin(xyz=(0.050, 0.0, 0.036)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.12,
            lower=0.0,
            upper=0.005,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
