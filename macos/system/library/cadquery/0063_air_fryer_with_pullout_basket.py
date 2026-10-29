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
BODY_RADIUS = 0.135
BODY_HEIGHT = 0.272
BODY_FRONT_X = 0.108
TOWER_DEPTH = 0.100
TOWER_WIDTH = 0.128
TOWER_HEIGHT = 0.094
TOWER_CENTER_X = 0.044
DRAWER_CENTER_Z = 0.105
CAVITY_WIDTH = 0.222
CAVITY_HEIGHT = 0.126
CAVITY_DEPTH = 0.186
DRAWER_FRONT_THICKNESS = 0.020
DRAWER_TRAVEL = 0.112
KEEP_WARM_TOP_X = 0.040
KEEP_WARM_TOP_Z = BODY_HEIGHT + TOWER_HEIGHT
def _body_shape() -> cq.Workplane:
    body = cq.Workplane("XY").circle(BODY_RADIUS).extrude(BODY_HEIGHT)

    front_flat = (
        cq.Workplane("XY")
        .box(0.260, 0.360, BODY_HEIGHT + TOWER_HEIGHT + 0.060)
        .translate((BODY_FRONT_X + 0.130, 0.0, (BODY_HEIGHT + TOWER_HEIGHT) * 0.5))
    )
    body = body.cut(front_flat)

    tower = (
        cq.Workplane("XY")
        .box(TOWER_DEPTH, TOWER_WIDTH, TOWER_HEIGHT)
        .translate((TOWER_CENTER_X, 0.0, BODY_HEIGHT + TOWER_HEIGHT * 0.5 - 0.004))
        .edges("|Z")
        .fillet(0.016)
    )
    body = body.union(tower)

    cavity = (
        cq.Workplane("YZ")
        .center(0.0, DRAWER_CENTER_Z)
        .rect(CAVITY_WIDTH, CAVITY_HEIGHT)
        .extrude(CAVITY_DEPTH + 0.008)
        .edges("|X")
        .fillet(0.018)
        .translate((BODY_FRONT_X - CAVITY_DEPTH - 0.004, 0.0, 0.0))
    )
    body = body.cut(cavity)

    keep_warm_well = (
        cq.Workplane("XY")
        .box(0.018, 0.028, 0.010)
        .translate((KEEP_WARM_TOP_X, 0.0, KEEP_WARM_TOP_Z - 0.005))
    )
    body = body.cut(keep_warm_well)

    for dial_z in (BODY_HEIGHT + 0.018, BODY_HEIGHT + 0.050):
        dial_bore = (
            cq.Workplane("YZ")
            .center(0.0, dial_z)
            .circle(0.0095)
            .extrude(0.006)
            .translate((BODY_FRONT_X - 0.006, 0.0, 0.0))
        )
        body = body.cut(dial_bore)

    return body
def _drawer_shape() -> cq.Workplane:
    floor = cq.Workplane("XY").box(0.164, 0.196, 0.004).translate((-0.080, 0.0, -0.047))
    rear_wall = cq.Workplane("XY").box(0.004, 0.204, 0.090).translate((-0.166, 0.0, -0.004))
    left_wall = cq.Workplane("XY").box(0.168, 0.004, 0.090).translate((-0.080, -0.100, -0.004))
    right_wall = cq.Workplane("XY").box(0.168, 0.004, 0.090).translate((-0.080, 0.100, -0.004))
    upper_left_rail = cq.Workplane("XY").box(0.156, 0.008, 0.004).translate((-0.080, -0.098, 0.039))
    upper_right_rail = cq.Workplane("XY").box(0.156, 0.008, 0.004).translate((-0.080, 0.098, 0.039))
    rear_rim = cq.Workplane("XY").box(0.008, 0.196, 0.004).translate((-0.162, 0.0, 0.039))

    guide_pad_0 = cq.Workplane("XY").box(0.042, 0.010, 0.024).translate((-0.040, -0.105, -0.008))
    guide_pad_1 = cq.Workplane("XY").box(0.042, 0.010, 0.024).translate((-0.040, 0.105, -0.008))
    guide_pad_2 = cq.Workplane("XY").box(0.042, 0.010, 0.024).translate((-0.120, -0.105, -0.008))
    guide_pad_3 = cq.Workplane("XY").box(0.042, 0.010, 0.024).translate((-0.120, 0.105, -0.008))

    fascia = (
        cq.Workplane("XY")
        .box(DRAWER_FRONT_THICKNESS, 0.224, 0.112)
        .translate((DRAWER_FRONT_THICKNESS * 0.5, 0.0, 0.0))
        .edges("|Z")
        .fillet(0.008)
    )

    drawer = floor.union(rear_wall).union(left_wall).union(right_wall)
    drawer = drawer.union(upper_left_rail).union(upper_right_rail).union(rear_rim).union(fascia)
    drawer = drawer.union(guide_pad_0).union(guide_pad_1).union(guide_pad_2).union(guide_pad_3)
    return drawer
def _basket_shape() -> cq.Workplane:
    floor = cq.Workplane("XY").box(0.124, 0.192, 0.004).translate((-0.082, 0.0, -0.041))
    rear_wall = cq.Workplane("XY").box(0.004, 0.184, 0.060).translate((-0.146, 0.0, -0.010))
    front_wall = cq.Workplane("XY").box(0.004, 0.184, 0.030).translate((-0.018, 0.0, -0.025))
    left_wall = cq.Workplane("XY").box(0.132, 0.004, 0.060).translate((-0.082, -0.096, -0.010))
    right_wall = cq.Workplane("XY").box(0.132, 0.004, 0.060).translate((-0.082, 0.096, -0.010))

    basket = floor.union(rear_wall).union(front_wall).union(left_wall).union(right_wall)

    for x_center in (-0.116, -0.082, -0.048):
        for y_center in (-0.052, -0.018, 0.018, 0.052):
            basket = basket.cut(
                cq.Workplane("XY")
                .box(0.016, 0.012, 0.006)
                .translate((x_center, y_center, -0.041))
            )
    return basket
def _handle_shape() -> cq.Workplane:
    rear_pad = cq.Workplane("XY").box(0.010, 0.090, 0.032).translate((0.005, 0.0, 0.0))
    top_bridge = cq.Workplane("XY").box(0.038, 0.110, 0.014).translate((0.021, 0.0, 0.021))
    front_grip = cq.Workplane("XY").box(0.014, 0.118, 0.026).translate((0.057, 0.0, -0.004))
    brace_0 = cq.Workplane("XY").box(0.048, 0.012, 0.034).translate((0.034, -0.052, 0.0))
    brace_1 = cq.Workplane("XY").box(0.048, 0.012, 0.034).translate((0.034, 0.052, 0.0))

    handle = rear_pad.union(top_bridge).union(front_grip).union(brace_0).union(brace_1)

    button_slot = cq.Workplane("XY").box(0.020, 0.038, 0.012).translate((0.022, 0.0, 0.022))
    stem_slot = cq.Workplane("XY").box(0.010, 0.024, 0.020).translate((0.026, 0.0, 0.012))
    return handle.cut(button_slot).cut(stem_slot)
def _release_button_shape() -> cq.Workplane:
    cap = cq.Workplane("XY").box(0.020, 0.040, 0.004).translate((0.0, 0.0, 0.002))
    stem = cq.Workplane("XY").box(0.010, 0.024, 0.010).translate((0.0, 0.0, -0.005))
    return cap.union(stem)
def _control_button_shape() -> cq.Workplane:
    cap = cq.Workplane("XY").box(0.022, 0.032, 0.004).translate((0.0, 0.0, 0.002))
    stem = cq.Workplane("XY").box(0.010, 0.018, 0.005).translate((0.0, 0.0, -0.0015))
    return cap.union(stem)
def _keep_warm_bezel_shape() -> cq.Workplane:
    outer = cq.Workplane("XY").box(0.026, 0.036, 0.006).translate((0.0, 0.0, 0.003))
    inner = cq.Workplane("XY").box(0.0185, 0.0285, 0.008).translate((0.0, 0.0, 0.003))
    return outer.cut(inner)
def _dial_shape() -> cq.Workplane:
    shaft = cq.Workplane("YZ").circle(0.009).extrude(0.004).translate((-0.004, 0.0, 0.0))
    skirt = cq.Workplane("YZ").circle(0.018).extrude(0.006)
    cap = skirt.faces(">X").workplane().circle(0.014).extrude(0.010)
    pointer = (
        cq.Workplane("YZ")
        .center(0.0, 0.0065)
        .rect(0.0018, 0.007)
        .extrude(0.002)
        .translate((0.0125, 0.0, 0.0))
    )
    return shaft.union(cap).union(pointer)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cylindrical_air_fryer")

    body_matte = model.material("body_matte", rgba=(0.17, 0.18, 0.19, 1.0))
    drawer_matte = model.material("drawer_matte", rgba=(0.13, 0.14, 0.15, 1.0))
    basket_dark = model.material("basket_dark", rgba=(0.10, 0.10, 0.11, 1.0))
    handle_dark = model.material("handle_dark", rgba=(0.08, 0.08, 0.09, 1.0))
    dial_dark = model.material("dial_dark", rgba=(0.12, 0.12, 0.13, 1.0))
    control_accent = model.material("control_accent", rgba=(0.52, 0.53, 0.54, 1.0))
    release_accent = model.material("release_accent", rgba=(0.72, 0.17, 0.14, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "air_fryer_body"),
        material=body_matte,
        name="body_shell",
    )

    drawer = model.part("drawer")
    drawer.visual(
        mesh_from_cadquery(_drawer_shape(), "air_fryer_drawer"),
        material=drawer_matte,
        name="drawer_shell",
    )
    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(BODY_FRONT_X - 0.0045, 0.0, DRAWER_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=35.0,
            velocity=0.18,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )

    basket = model.part("basket")
    basket.visual(
        mesh_from_cadquery(_basket_shape(), "air_fryer_basket"),
        material=basket_dark,
        name="basket_shell",
    )
    model.articulation(
        "drawer_to_basket",
        ArticulationType.FIXED,
        parent=drawer,
        child=basket,
        origin=Origin(),
    )

    handle = model.part("handle")
    handle.visual(
        mesh_from_cadquery(_handle_shape(), "air_fryer_handle"),
        material=handle_dark,
        name="handle_shell",
    )
    model.articulation(
        "drawer_to_handle",
        ArticulationType.FIXED,
        parent=drawer,
        child=handle,
        origin=Origin(xyz=(DRAWER_FRONT_THICKNESS, 0.0, -0.002)),
    )

    release_button = model.part("release_button")
    release_button.visual(
        mesh_from_cadquery(_release_button_shape(), "air_fryer_release_button"),
        material=release_accent,
        name="release_button_cap",
    )
    model.articulation(
        "handle_to_release_button",
        ArticulationType.PRISMATIC,
        parent=handle,
        child=release_button,
        origin=Origin(xyz=(0.022, 0.0, 0.028)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.05,
            lower=0.0,
            upper=0.003,
        ),
    )

    control_panel = model.part("control_panel")
    control_panel.visual(
        Box((0.004, 0.074, 0.092)),
        origin=Origin(xyz=(0.002, 0.0, 0.0)),
        material=drawer_matte,
        name="control_panel",
    )
    model.articulation(
        "body_to_control_panel",
        ArticulationType.FIXED,
        parent=body,
        child=control_panel,
        origin=Origin(xyz=(BODY_FRONT_X, 0.0, BODY_HEIGHT + 0.034)),
    )

    temperature_dial = model.part("temperature_dial")
    temperature_dial.visual(
        mesh_from_cadquery(_dial_shape(), "air_fryer_temperature_dial"),
        material=dial_dark,
        name="temperature_dial",
    )
    model.articulation(
        "control_panel_to_temperature_dial",
        ArticulationType.CONTINUOUS,
        parent=control_panel,
        child=temperature_dial,
        origin=Origin(xyz=(0.004, 0.0, -0.021)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.12, velocity=4.0),
    )

    time_dial = model.part("time_dial")
    time_dial.visual(
        mesh_from_cadquery(_dial_shape(), "air_fryer_time_dial"),
        material=dial_dark,
        name="time_dial",
    )
    model.articulation(
        "control_panel_to_time_dial",
        ArticulationType.CONTINUOUS,
        parent=control_panel,
        child=time_dial,
        origin=Origin(xyz=(0.004, 0.0, 0.021)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.12, velocity=4.0),
    )

    keep_warm_bezel = model.part("keep_warm_bezel")
    keep_warm_bezel.visual(
        mesh_from_cadquery(_keep_warm_bezel_shape(), "air_fryer_keep_warm_bezel"),
        material=drawer_matte,
        name="keep_warm_bezel",
    )
    model.articulation(
        "body_to_keep_warm_bezel",
        ArticulationType.FIXED,
        parent=body,
        child=keep_warm_bezel,
        origin=Origin(xyz=(KEEP_WARM_TOP_X, 0.0, KEEP_WARM_TOP_Z - 0.004)),
    )

    keep_warm_button = model.part("keep_warm_button")
    keep_warm_button.visual(
        mesh_from_cadquery(_control_button_shape(), "air_fryer_keep_warm_button"),
        material=control_accent,
        name="keep_warm_cap",
    )
    model.articulation(
        "keep_warm_bezel_to_button",
        ArticulationType.PRISMATIC,
        parent=keep_warm_bezel,
        child=keep_warm_button,
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.05,
            lower=0.0,
            upper=0.003,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
