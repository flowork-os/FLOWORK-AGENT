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
BASE_W = 0.335
BASE_D = 0.365
BASE_H = 0.105
BOTTOM_T = 0.012
TOP_T = 0.012
WALL_T = 0.010
FOOT_H = 0.006
DRAWER_W = 0.286
DRAWER_D = 0.315
DRAWER_H = 0.062
DRAWER_FACE_T = 0.016
DRAWER_TRAVEL = 0.155
POD_W = 0.298
POD_D = 0.205
POD_FRONT_H = 0.028
POD_REAR_H = 0.070
POD_GAP = 0.028
POD_BOTTOM_Z = BASE_H + POD_GAP
POD_CENTER_Y = 0.060
POD_SLOPE = math.atan2(POD_REAR_H - POD_FRONT_H, POD_D)
SCREEN_POST_H = 0.110
SCREEN_W = 0.158
SCREEN_H = 0.108
SCREEN_T = 0.018
DEPT_KEYS = (
    ("dept_key_0", -0.078, -0.012),
    ("dept_key_1", -0.032, -0.012),
    ("dept_key_2", -0.078, 0.030),
    ("dept_key_3", -0.032, 0.030),
)
NUMBER_KEYS = (
    ("number_key_0", 0.028, -0.048),
    ("number_key_1", 0.056, -0.048),
    ("number_key_2", 0.084, -0.048),
    ("number_key_3", 0.028, -0.022),
    ("number_key_4", 0.056, -0.022),
    ("number_key_5", 0.084, -0.022),
    ("number_key_6", 0.028, 0.004),
    ("number_key_7", 0.056, 0.004),
    ("number_key_8", 0.084, 0.004),
    ("number_key_9", 0.028, 0.030),
    ("number_key_10", 0.056, 0.030),
    ("number_key_11", 0.084, 0.030),
)
def _pod_top_z(local_y: float) -> float:
    y_from_front = local_y + POD_D * 0.5
    return POD_FRONT_H + ((POD_REAR_H - POD_FRONT_H) * y_from_front / POD_D)
def _pod_mesh() -> object:
    half_d = POD_D * 0.5
    body = (
        cq.Workplane("YZ")
        .moveTo(-half_d, 0.0)
        .lineTo(-half_d, POD_FRONT_H)
        .lineTo(half_d, POD_REAR_H)
        .lineTo(half_d, 0.0)
        .close()
        .extrude(POD_W)
        .translate((-POD_W * 0.5, 0.0, 0.0))
    )
    body = body.edges("|X").fillet(0.004)

    dept_center = (
        math.sin(POD_SLOPE) * 0.005,
        math.cos(POD_SLOPE) * 0.005,
    )
    number_center = (
        math.sin(POD_SLOPE) * 0.00425,
        math.cos(POD_SLOPE) * 0.00425,
    )
    pocket_shift = (
        math.sin(POD_SLOPE) * 0.002,
        -math.cos(POD_SLOPE) * 0.002,
    )
    pocket_angle = -math.degrees(POD_SLOPE)

    for _, x, y in DEPT_KEYS:
        cutter = (
            cq.Workplane("XY")
            .box(0.044, 0.036, 0.016)
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), pocket_angle)
            .translate(
                (
                    x,
                    y + dept_center[0] + pocket_shift[0],
                    _pod_top_z(y) + dept_center[1] + pocket_shift[1],
                )
            )
        )
        body = body.cut(cutter)

    for _, x, y in NUMBER_KEYS:
        cutter = (
            cq.Workplane("XY")
            .box(0.026, 0.024, 0.013)
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), pocket_angle)
            .translate(
                (
                    x,
                    y + number_center[0] + pocket_shift[0],
                    _pod_top_z(y) + number_center[1] + pocket_shift[1],
                )
            )
        )
        body = body.cut(cutter)

    return body
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pos_register")

    housing_dark = model.material("housing_dark", rgba=(0.18, 0.19, 0.20, 1.0))
    housing_mid = model.material("housing_mid", rgba=(0.30, 0.31, 0.33, 1.0))
    drawer_dark = model.material("drawer_dark", rgba=(0.16, 0.17, 0.18, 1.0))
    trim_dark = model.material("trim_dark", rgba=(0.10, 0.11, 0.12, 1.0))
    key_light = model.material("key_light", rgba=(0.90, 0.90, 0.86, 1.0))
    key_dept = model.material("key_dept", rgba=(0.78, 0.78, 0.73, 1.0))
    glass = model.material("glass", rgba=(0.19, 0.29, 0.33, 0.45))

    housing = model.part("housing")
    wall_h = BASE_H - FOOT_H - BOTTOM_T - TOP_T
    wall_center_z = FOOT_H + BOTTOM_T + wall_h * 0.5

    housing.visual(
        Box((BASE_W, BASE_D, BOTTOM_T)),
        origin=Origin(xyz=(0.0, 0.0, FOOT_H + BOTTOM_T * 0.5)),
        material=housing_dark,
        name="bottom_plate",
    )
    housing.visual(
        Box((BASE_W, BASE_D, TOP_T)),
        origin=Origin(xyz=(0.0, 0.0, BASE_H - TOP_T * 0.5)),
        material=housing_dark,
        name="top_cover",
    )
    housing.visual(
        Box((WALL_T, BASE_D, wall_h)),
        origin=Origin(xyz=((BASE_W - WALL_T) * 0.5, 0.0, wall_center_z)),
        material=housing_dark,
        name="right_wall",
    )
    housing.visual(
        Box((WALL_T, BASE_D, wall_h)),
        origin=Origin(xyz=(-(BASE_W - WALL_T) * 0.5, 0.0, wall_center_z)),
        material=housing_dark,
        name="left_wall",
    )
    housing.visual(
        Box((BASE_W - 2.0 * WALL_T, WALL_T, wall_h)),
        origin=Origin(xyz=(0.0, (BASE_D - WALL_T) * 0.5, wall_center_z)),
        material=housing_dark,
        name="rear_wall",
    )
    housing.visual(
        Box((BASE_W - 2.0 * WALL_T, 0.026, 0.008)),
        origin=Origin(xyz=(0.0, -BASE_D * 0.5 + 0.013, BASE_H - 0.006 - 0.004)),
        material=housing_mid,
        name="front_header",
    )
    for idx, x in enumerate((-0.118, 0.118)):
        housing.visual(
            Box((0.036, 0.036, FOOT_H)),
            origin=Origin(xyz=(x, -0.125, FOOT_H * 0.5)),
            material=trim_dark,
            name=f"front_foot_{idx}",
        )
        housing.visual(
            Box((0.036, 0.036, FOOT_H)),
            origin=Origin(xyz=(x, 0.125, FOOT_H * 0.5)),
            material=trim_dark,
            name=f"rear_foot_{idx}",
        )

    support_w = 0.024
    support_d = 0.044
    support_h = POD_BOTTOM_Z - BASE_H
    support_z = BASE_H + support_h * 0.5
    for index, x in enumerate((-0.092, 0.092)):
        housing.visual(
            Box((support_w, support_d, support_h)),
            origin=Origin(xyz=(x, 0.112, support_z)),
            material=housing_mid,
            name=f"pod_post_{index}",
        )
    housing.visual(
        Box((0.208, 0.016, 0.010)),
        origin=Origin(xyz=(0.0, 0.124, BASE_H + 0.005)),
        material=housing_mid,
        name="pod_crossbar",
    )
    for index, x in enumerate((-0.1535, 0.1535)):
        housing.visual(
            Box((0.008, 0.278, 0.010)),
            origin=Origin(xyz=(x, -0.012, FOOT_H + BOTTOM_T + 0.028)),
            material=trim_dark,
            name=f"runner_{index}",
        )

    drawer = model.part("drawer")
    drawer.visual(
        Box((DRAWER_W - 0.012, DRAWER_D, DRAWER_H)),
        origin=Origin(xyz=(0.0, DRAWER_D * 0.5, DRAWER_H * 0.5)),
        material=drawer_dark,
        name="drawer_body",
    )
    drawer.visual(
        Box((DRAWER_W, DRAWER_FACE_T, DRAWER_H + 0.016)),
        origin=Origin(xyz=(0.0, -DRAWER_FACE_T * 0.5, (DRAWER_H + 0.016) * 0.5)),
        material=housing_mid,
        name="drawer_front",
    )
    drawer.visual(
        Cylinder(radius=0.006, length=0.094),
        origin=Origin(
            xyz=(0.0, -0.013, DRAWER_H * 0.48),
            rpy=(math.pi * 0.5, 0.0, 0.0),
        ),
        material=trim_dark,
        name="drawer_handle",
    )
    drawer.visual(
        Box((0.116, 0.008, 0.020)),
        origin=Origin(xyz=(0.0, -0.016, DRAWER_H * 0.48)),
        material=trim_dark,
        name="handle_bridge",
    )
    for index, x in enumerate((-0.136, 0.136)):
        drawer.visual(
            Box((0.006, DRAWER_D - 0.050, 0.008)),
            origin=Origin(xyz=(x, 0.165, 0.030)),
            material=trim_dark,
            name=f"slide_{index}",
        )

    model.articulation(
        "housing_to_drawer",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=drawer,
        origin=Origin(
            xyz=(
                0.0,
                -BASE_D * 0.5,
                FOOT_H + BOTTOM_T + 0.008,
            )
        ),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=45.0,
            velocity=0.28,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )

    pod = model.part("pod")
    pod.visual(
        mesh_from_cadquery(_pod_mesh(), "pos_register_pod"),
        material=housing_mid,
        name="pod_shell",
    )
    pod.visual(
        Box((POD_W - 0.020, 0.014, 0.010)),
        origin=Origin(xyz=(0.0, -POD_D * 0.5 + 0.007, POD_FRONT_H * 0.5 + 0.006)),
        material=trim_dark,
        name="front_skirt",
    )

    key_axis = (0.0, -math.sin(POD_SLOPE), math.cos(POD_SLOPE))
    key_seat = (
        0.0,
        math.sin(POD_SLOPE) * 0.002,
        -math.cos(POD_SLOPE) * 0.002,
    )
    dept_half_t = 0.005
    dept_mount = (0.0, math.sin(POD_SLOPE) * dept_half_t, math.cos(POD_SLOPE) * dept_half_t)
    number_half_t = 0.00425
    number_mount = (
        0.0,
        math.sin(POD_SLOPE) * number_half_t,
        math.cos(POD_SLOPE) * number_half_t,
    )

    for name, x, y in DEPT_KEYS:
        key_part = model.part(name)
        key_part.visual(
            Box((0.040, 0.032, 0.010)),
            origin=Origin(xyz=dept_mount, rpy=(-POD_SLOPE, 0.0, 0.0)),
            material=key_dept,
            name="keycap",
        )
        key_part.visual(
            Box((0.012, 0.012, 0.012)),
            origin=Origin(xyz=(0.0, 0.0, -0.0005)),
            material=trim_dark,
            name="stem",
        )
        model.articulation(
            f"pod_to_{name}",
            ArticulationType.PRISMATIC,
            parent=pod,
            child=key_part,
            origin=Origin(xyz=(x + key_seat[0], y + key_seat[1], _pod_top_z(y) + key_seat[2])),
            axis=key_axis,
            motion_limits=MotionLimits(
                effort=3.0,
                velocity=0.08,
                lower=-0.0030,
                upper=0.0,
            ),
        )

    for name, x, y in NUMBER_KEYS:
        key_part = model.part(name)
        key_part.visual(
            Box((0.022, 0.020, 0.0085)),
            origin=Origin(xyz=number_mount, rpy=(-POD_SLOPE, 0.0, 0.0)),
            material=key_light,
            name="keycap",
        )
        key_part.visual(
            Box((0.008, 0.008, 0.010)),
            origin=Origin(xyz=(0.0, 0.0, -0.0005)),
            material=trim_dark,
            name="stem",
        )
        model.articulation(
            f"pod_to_{name}",
            ArticulationType.PRISMATIC,
            parent=pod,
            child=key_part,
            origin=Origin(xyz=(x + key_seat[0], y + key_seat[1], _pod_top_z(y) + key_seat[2])),
            axis=key_axis,
            motion_limits=MotionLimits(
                effort=2.0,
                velocity=0.08,
                lower=-0.0022,
                upper=0.0,
            ),
        )

    model.articulation(
        "housing_to_pod",
        ArticulationType.FIXED,
        parent=housing,
        child=pod,
        origin=Origin(xyz=(0.0, POD_CENTER_Y, POD_BOTTOM_Z)),
    )

    swivel = model.part("screen_swivel")
    swivel.visual(
        Cylinder(radius=0.012, length=SCREEN_POST_H),
        origin=Origin(xyz=(0.0, 0.0, SCREEN_POST_H * 0.5)),
        material=trim_dark,
        name="post",
    )
    swivel.visual(
        Cylinder(radius=0.018, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material=trim_dark,
        name="post_base",
    )
    swivel.visual(
        Box((0.064, 0.028, 0.014)),
        origin=Origin(xyz=(0.0, 0.014, SCREEN_POST_H + 0.007)),
        material=trim_dark,
        name="tilt_head",
    )
    swivel.visual(
        Box((0.014, 0.028, 0.030)),
        origin=Origin(xyz=(-0.039, 0.014, SCREEN_POST_H + 0.008)),
        material=trim_dark,
        name="left_ear",
    )
    swivel.visual(
        Box((0.014, 0.028, 0.030)),
        origin=Origin(xyz=(0.039, 0.014, SCREEN_POST_H + 0.008)),
        material=trim_dark,
        name="right_ear",
    )

    model.articulation(
        "pod_to_screen_swivel",
        ArticulationType.REVOLUTE,
        parent=pod,
        child=swivel,
        origin=Origin(xyz=(0.0, POD_D * 0.5 - 0.030, POD_REAR_H - 0.004)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=1.8,
            lower=-1.10,
            upper=1.10,
        ),
    )

    screen = model.part("screen")
    screen.visual(
        Cylinder(radius=0.006, length=SCREEN_W - 0.026),
        origin=Origin(
            xyz=(0.0, -0.006, 0.0),
            rpy=(0.0, math.pi * 0.5, 0.0),
        ),
        material=trim_dark,
        name="hinge_bar",
    )
    screen.visual(
        Box((SCREEN_W, SCREEN_T, SCREEN_H)),
        origin=Origin(xyz=(0.0, -SCREEN_T * 0.5, SCREEN_H * 0.5)),
        material=housing_dark,
        name="screen_body",
    )
    screen.visual(
        Box((SCREEN_W - 0.018, 0.004, SCREEN_H - 0.020)),
        origin=Origin(xyz=(0.0, -SCREEN_T - 0.001, SCREEN_H * 0.5)),
        material=glass,
        name="display",
    )
    screen.visual(
        Box((0.050, 0.012, 0.010)),
        origin=Origin(xyz=(0.0, -0.008, SCREEN_H + 0.005)),
        material=trim_dark,
        name="top_bezel",
    )

    model.articulation(
        "swivel_to_screen",
        ArticulationType.REVOLUTE,
        parent=swivel,
        child=screen,
        origin=Origin(xyz=(0.0, 0.0, SCREEN_POST_H + 0.008)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=1.6,
            lower=-0.55,
            upper=0.40,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
