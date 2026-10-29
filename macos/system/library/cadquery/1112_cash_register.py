# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cash_register, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cash_register

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
BODY_LENGTH = 0.34
BODY_WIDTH = 0.30
BODY_HEIGHT = 0.10
DRAWER_TRAVEL = 0.12
POD_MOUNT_X = -0.015
POD_MOUNT_Z = BODY_HEIGHT
def _pod_shape() -> cq.Workplane:
    pedestal = (
        cq.Workplane("XY")
        .box(0.118, 0.120, 0.014, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.004)
    )
    neck = (
        cq.Workplane("XY")
        .box(0.094, 0.092, 0.016, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.004)
        .translate((0.004, 0.0, 0.014))
    )
    shell = (
        cq.Workplane("XY")
        .box(0.192, 0.164, 0.042, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.010)
        .translate((-0.010, 0.0, 0.026))
    )
    nose = (
        cq.Workplane("XY")
        .box(0.100, 0.140, 0.018, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.005)
        .translate((0.042, 0.0, 0.018))
    )
    key_deck = (
        cq.Workplane("XY")
        .box(0.152, 0.122, 0.004, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.0015)
        .translate((0.020, 0.0, 0.064))
    )
    display_mount = (
        cq.Workplane("XY")
        .box(0.082, 0.018, 0.012, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.0025)
        .translate((-0.070, 0.0, 0.056))
    )
    return pedestal.union(neck).union(shell).union(nose).union(key_deck).union(display_mount)
def _keycap_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(0.022, 0.018, 0.008, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.0025)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="boutique_cash_register")

    cream = model.material("cream", rgba=(0.89, 0.86, 0.80, 1.0))
    warm_white = model.material("warm_white", rgba=(0.95, 0.94, 0.91, 1.0))
    charcoal = model.material("charcoal", rgba=(0.18, 0.18, 0.19, 1.0))
    cocoa = model.material("cocoa", rgba=(0.30, 0.22, 0.17, 1.0))
    display_glow = model.material("display_glow", rgba=(0.24, 0.48, 0.45, 0.55))
    key_rose = model.material("key_rose", rgba=(0.84, 0.63, 0.61, 1.0))
    key_sage = model.material("key_sage", rgba=(0.69, 0.76, 0.65, 1.0))
    key_honey = model.material("key_honey", rgba=(0.84, 0.73, 0.49, 1.0))
    key_oat = model.material("key_oat", rgba=(0.86, 0.82, 0.71, 1.0))
    key_teal = model.material("key_teal", rgba=(0.60, 0.73, 0.74, 1.0))

    body = model.part("body")
    body.visual(
        Box((BODY_LENGTH, BODY_WIDTH, 0.010)),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=cream,
        name="bottom_plate",
    )
    body.visual(
        Box((BODY_LENGTH, 0.010, 0.084)),
        origin=Origin(xyz=(0.0, -0.145, 0.052)),
        material=cream,
        name="side_wall_0",
    )
    body.visual(
        Box((BODY_LENGTH, 0.010, 0.084)),
        origin=Origin(xyz=(0.0, 0.145, 0.052)),
        material=cream,
        name="side_wall_1",
    )
    body.visual(
        Box((0.016, 0.280, 0.084)),
        origin=Origin(xyz=(-0.162, 0.0, 0.052)),
        material=cream,
        name="back_wall",
    )
    body.visual(
        Box((0.186, 0.280, 0.012)),
        origin=Origin(xyz=(-0.077, 0.0, 0.094)),
        material=cream,
        name="top_cover",
    )
    drawer = model.part("drawer")
    drawer.visual(
        Box((0.258, 0.246, 0.006)),
        origin=Origin(xyz=(-0.129, 0.0, 0.003)),
        material=warm_white,
        name="tray_floor",
    )
    drawer.visual(
        Box((0.258, 0.008, 0.036)),
        origin=Origin(xyz=(-0.129, -0.119, 0.021)),
        material=warm_white,
        name="tray_wall_0",
    )
    drawer.visual(
        Box((0.258, 0.008, 0.036)),
        origin=Origin(xyz=(-0.129, 0.119, 0.021)),
        material=warm_white,
        name="tray_wall_1",
    )
    drawer.visual(
        Box((0.008, 0.230, 0.036)),
        origin=Origin(xyz=(-0.254, 0.0, 0.021)),
        material=warm_white,
        name="tray_back",
    )
    drawer.visual(
        Box((0.012, 0.266, 0.058)),
        origin=Origin(xyz=(-0.006, 0.0, 0.029)),
        material=warm_white,
        name="front_panel",
    )
    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(BODY_LENGTH * 0.5, 0.0, 0.010)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=0.25,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )

    keypad_pod = model.part("keypad_pod")
    keypad_pod.visual(
        mesh_from_cadquery(_pod_shape(), "cash_register_keypad_pod"),
        material=cocoa,
        name="pod_shell",
    )
    model.articulation(
        "body_to_keypad_pod",
        ArticulationType.FIXED,
        parent=body,
        child=keypad_pod,
        origin=Origin(xyz=(POD_MOUNT_X, 0.0, POD_MOUNT_Z)),
    )

    customer_display = model.part("customer_display")
    customer_display.visual(
        Cylinder(radius=0.004, length=0.088),
        origin=Origin(rpy=(math.pi * 0.5, 0.0, 0.0)),
        material=charcoal,
        name="hinge_barrel",
    )
    customer_display.visual(
        Box((0.032, 0.010, 0.010)),
        origin=Origin(xyz=(0.018, 0.0, 0.004)),
        material=charcoal,
        name="support_arm",
    )
    customer_display.visual(
        Box((0.052, 0.014, 0.036)),
        origin=Origin(xyz=(0.058, 0.0, 0.020)),
        material=charcoal,
        name="display_head",
    )
    customer_display.visual(
        Box((0.040, 0.003, 0.024)),
        origin=Origin(xyz=(0.065, 0.0, 0.021)),
        material=display_glow,
        name="display_glass",
    )
    model.articulation(
        "pod_to_customer_display",
        ArticulationType.REVOLUTE,
        parent=keypad_pod,
        child=customer_display,
        origin=Origin(xyz=(-0.106, 0.0, 0.068)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=2.5,
            lower=0.0,
            upper=1.20,
        ),
    )

    keycap_mesh = mesh_from_cadquery(_keycap_shape(), "cash_register_keycap")
    key_rows = (key_rose, key_sage, key_honey, key_oat, key_teal)
    key_x_positions = (0.000, 0.026, 0.052, 0.078)
    key_y_positions = (-0.052, -0.026, 0.000, 0.026, 0.052)

    for row_index, y_pos in enumerate(key_y_positions):
        for col_index, x_pos in enumerate(key_x_positions):
            key_name = f"key_{row_index}_{col_index}"
            key_part = model.part(key_name)
            key_part.visual(
                keycap_mesh,
                material=key_rows[row_index],
                name="keycap",
            )
            model.articulation(
                f"pod_to_{key_name}",
                ArticulationType.PRISMATIC,
                parent=keypad_pod,
                child=key_part,
                origin=Origin(xyz=(x_pos, y_pos, 0.068)),
                axis=(0.0, 0.0, -1.0),
                motion_limits=MotionLimits(
                    effort=1.5,
                    velocity=0.08,
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
