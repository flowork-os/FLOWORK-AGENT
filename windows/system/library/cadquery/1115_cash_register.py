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
BODY_X = 0.280
BODY_Y = 0.215
BODY_FRONT_X = BODY_X / 2.0
POD_FRONT_POINT = (0.055, 0.0, 0.079)
POD_REAR_POINT = (-0.055, 0.0, 0.105)
POD_PITCH = math.atan2(POD_REAR_POINT[2] - POD_FRONT_POINT[2], POD_FRONT_POINT[0] - POD_REAR_POINT[0])
POD_TANGENT_REAR = (-math.cos(POD_PITCH), 0.0, math.sin(POD_PITCH))
POD_NORMAL = (math.sin(POD_PITCH), 0.0, math.cos(POD_PITCH))
def _add_vec(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _scale_vec(v: tuple[float, float, float], scale: float) -> tuple[float, float, float]:
    return (v[0] * scale, v[1] * scale, v[2] * scale)
def _pod_xyz(s_rear: float, y: float, lift: float = 0.0) -> tuple[float, float, float]:
    point = _add_vec(POD_FRONT_POINT, _scale_vec(POD_TANGENT_REAR, s_rear))
    point = (point[0], y, point[2])
    if lift != 0.0:
        point = _add_vec(point, _scale_vec(POD_NORMAL, lift))
    return point
def _make_body_shape() -> cq.Workplane:
    body = (
        cq.Workplane("XZ")
        .polyline(
            [
                (BODY_FRONT_X, 0.0),
                (-0.136, 0.0),
                (-0.136, 0.095),
                (-0.090, 0.105),
                (-0.055, 0.105),
                (0.055, 0.079),
                (0.122, 0.064),
                (BODY_FRONT_X, 0.050),
            ]
        )
        .close()
        .extrude(BODY_Y)
        .translate((0.0, BODY_Y / 2.0, 0.0))
        .edges("|Y")
        .fillet(0.006)
    )

    drawer_cut = (
        cq.Workplane("XY")
        .box(0.176, 0.194, 0.044)
        .translate((0.052, 0.0, 0.032))
    )
    receipt_tray_cut = (
        cq.Workplane("XY")
        .box(0.062, 0.070, 0.008)
        .translate((0.094, -0.068, 0.060))
    )
    return body.cut(drawer_cut).cut(receipt_tray_cut)
def _make_keycap_shape(length: float, width: float, height: float, edge: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(length, width, height)
        .translate((0.0, 0.0, height / 2.0))
        .edges("|Z")
        .fillet(edge)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="boutique_cash_register")

    body_color = model.material("body_cream", rgba=(0.90, 0.88, 0.82, 1.0))
    trim_dark = model.material("trim_charcoal", rgba=(0.20, 0.22, 0.24, 1.0))
    drawer_dark = model.material("drawer_charcoal", rgba=(0.17, 0.18, 0.20, 1.0))
    key_light = model.material("key_light", rgba=(0.95, 0.95, 0.93, 1.0))
    key_accent = model.material("key_accent", rgba=(0.88, 0.72, 0.53, 1.0))
    screen_dark = model.material("screen_dark", rgba=(0.17, 0.20, 0.21, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.38, 0.68, 0.70, 0.45))
    hinge_dark = model.material("hinge_dark", rgba=(0.28, 0.29, 0.31, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_make_body_shape(), "register_body"),
        material=body_color,
        name="housing_shell",
    )
    body.visual(
        Box((0.088, 0.082, 0.0050)),
        origin=Origin(
            xyz=_pod_xyz(0.050, -0.020, -0.0027),
            rpy=(0.0, POD_PITCH, 0.0),
        ),
        material=trim_dark,
        name="numeric_field",
    )
    for mount_index, y_pos in enumerate((-0.067, 0.028)):
        body.visual(
            Box((0.016, 0.014, 0.012)),
            origin=Origin(
                xyz=_pod_xyz(0.050, y_pos, -0.0060),
                rpy=(0.0, POD_PITCH, 0.0),
            ),
            material=trim_dark,
            name=f"numeric_mount_{mount_index}",
        )
    body.visual(
        Box((0.088, 0.022, 0.0050)),
        origin=Origin(
            xyz=_pod_xyz(0.050, 0.042, -0.0027),
            rpy=(0.0, POD_PITCH, 0.0),
        ),
        material=trim_dark,
        name="function_field",
    )
    body.visual(
        Box((0.016, 0.014, 0.012)),
        origin=Origin(
            xyz=_pod_xyz(0.050, 0.059, -0.0060),
            rpy=(0.0, POD_PITCH, 0.0),
        ),
        material=trim_dark,
        name="function_mount",
    )
    for y_pos in (-0.030, 0.030):
        body.visual(
            Cylinder(radius=0.0042, length=0.018),
            origin=Origin(
                xyz=(-0.097, y_pos, 0.101),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=hinge_dark,
            name=f"display_barrel_{0 if y_pos < 0.0 else 1}",
        )

    drawer = model.part("drawer")
    drawer.visual(
        Box((0.012, 0.206, 0.048)),
        origin=Origin(xyz=(0.006, 0.0, 0.024)),
        material=drawer_dark,
        name="drawer_face",
    )
    drawer.visual(
        Box((0.168, 0.182, 0.003)),
        origin=Origin(xyz=(-0.084, 0.0, 0.0015)),
        material=drawer_dark,
        name="tray_floor",
    )
    drawer.visual(
        Box((0.164, 0.004, 0.030)),
        origin=Origin(xyz=(-0.082, -0.089, 0.0165)),
        material=drawer_dark,
        name="tray_wall_0",
    )
    drawer.visual(
        Box((0.164, 0.004, 0.030)),
        origin=Origin(xyz=(-0.082, 0.089, 0.0165)),
        material=drawer_dark,
        name="tray_wall_1",
    )
    drawer.visual(
        Box((0.004, 0.182, 0.030)),
        origin=Origin(xyz=(-0.166, 0.0, 0.0165)),
        material=drawer_dark,
        name="tray_back",
    )
    drawer.visual(
        Box((0.008, 0.070, 0.012)),
        origin=Origin(xyz=(0.016, 0.0, 0.028)),
        material=trim_dark,
        name="drawer_pull",
    )

    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(0.141, 0.0, 0.010)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=0.25,
            lower=0.0,
            upper=0.078,
        ),
    )

    display = model.part("display")
    display.visual(
        Cylinder(radius=0.0034, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=hinge_dark,
        name="display_barrel",
    )
    display.visual(
        Box((0.060, 0.074, 0.012)),
        origin=Origin(xyz=(0.030, 0.0, 0.006)),
        material=screen_dark,
        name="display_housing",
    )
    display.visual(
        Box((0.050, 0.058, 0.0016)),
        origin=Origin(xyz=(0.031, 0.0, 0.0128)),
        material=screen_glass,
        name="screen_glass",
    )

    model.articulation(
        "body_to_display",
        ArticulationType.REVOLUTE,
        parent=body,
        child=display,
        origin=Origin(xyz=(-0.101, 0.0, 0.104)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=2.0,
            lower=0.0,
            upper=1.15,
        ),
    )

    num_key_mesh = mesh_from_cadquery(_make_keycap_shape(0.020, 0.020, 0.006, 0.002), "num_keycap")
    fn_key_mesh = mesh_from_cadquery(_make_keycap_shape(0.016, 0.019, 0.0052, 0.0016), "fn_keycap")
    num_row_s = (0.018, 0.040, 0.062, 0.084)
    num_col_y = (-0.047, -0.020, 0.007)
    for row_index, s_pos in enumerate(num_row_s):
        for col_index, y_pos in enumerate(num_col_y):
            key = model.part(f"num_key_{row_index}_{col_index}")
            key.visual(
                num_key_mesh,
                origin=Origin(xyz=(0.0, 0.0, 0.0)),
                material=key_light,
                name="keycap",
            )
            model.articulation(
                f"body_to_num_key_{row_index}_{col_index}",
                ArticulationType.PRISMATIC,
                parent=body,
                child=key,
                origin=Origin(
                    xyz=_pod_xyz(s_pos, y_pos),
                    rpy=(0.0, POD_PITCH, 0.0),
                ),
                axis=(0.0, 0.0, -1.0),
                motion_limits=MotionLimits(
                    effort=2.0,
                    velocity=0.08,
                    lower=0.0,
                    upper=0.0028,
                ),
            )

    fn_row_s = (0.018, 0.040, 0.062, 0.084)
    for row_index, s_pos in enumerate(fn_row_s):
        key = model.part(f"fn_key_{row_index}")
        key.visual(
            fn_key_mesh,
            origin=Origin(xyz=(0.0, 0.0, 0.0)),
            material=key_accent,
            name="keycap",
        )
        model.articulation(
            f"body_to_fn_key_{row_index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=key,
            origin=Origin(
                xyz=_pod_xyz(s_pos, 0.042),
                rpy=(0.0, POD_PITCH, 0.0),
            ),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=2.0,
                velocity=0.08,
                lower=0.0,
                upper=0.0024,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
