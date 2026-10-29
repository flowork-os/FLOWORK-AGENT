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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
BASE_DEPTH = 0.360
BASE_WIDTH = 0.330
BASE_HEIGHT = 0.095
SHELL_THICKNESS = 0.0035
DRAWER_OPENING_WIDTH = 0.286
DRAWER_OPENING_HEIGHT = 0.067
DRAWER_CENTER_Z = 0.044
DRAWER_TRAVEL = 0.130
POD_WIDTH = 0.252
PANEL_LOWER = (0.108, 0.112)
PANEL_UPPER = (0.058, 0.173)
PANEL_CENTER_X = (PANEL_LOWER[0] + PANEL_UPPER[0]) * 0.5
PANEL_CENTER_Z = (PANEL_LOWER[1] + PANEL_UPPER[1]) * 0.5
PANEL_TANGENT_X = PANEL_LOWER[0] - PANEL_UPPER[0]
PANEL_TANGENT_Z = PANEL_LOWER[1] - PANEL_UPPER[1]
PANEL_TANGENT_LEN = math.hypot(PANEL_TANGENT_X, PANEL_TANGENT_Z)
PANEL_DOWN_X = PANEL_TANGENT_X / PANEL_TANGENT_LEN
PANEL_DOWN_Z = PANEL_TANGENT_Z / PANEL_TANGENT_LEN
PANEL_NORMAL_X = -PANEL_DOWN_Z
PANEL_NORMAL_Z = PANEL_DOWN_X
PANEL_PITCH = math.atan2(PANEL_NORMAL_X, PANEL_NORMAL_Z)
PANEL_PITCH_DEG = math.degrees(PANEL_PITCH)
PANEL_RECESS_DEPTH = 0.0010
NUMERIC_RECESS_EXTRA = 0.0010
BUTTON_TRAVEL = 0.0026
MENU_KEYS = [
    ("menu_key_0", -0.026, -0.072),
    ("menu_key_1", -0.026, -0.040),
    ("menu_key_2", 0.004, -0.072),
    ("menu_key_3", 0.004, -0.040),
]
NUMERIC_KEYS = [
    ("numeric_key_1", -0.020, 0.031),
    ("numeric_key_2", -0.020, 0.057),
    ("numeric_key_3", -0.020, 0.083),
    ("numeric_key_4", 0.008, 0.031),
    ("numeric_key_5", 0.008, 0.057),
    ("numeric_key_6", 0.008, 0.083),
    ("numeric_key_7", 0.036, 0.031),
    ("numeric_key_8", 0.036, 0.057),
    ("numeric_key_9", 0.036, 0.083),
    ("numeric_key_clr", 0.064, 0.031),
    ("numeric_key_0", 0.064, 0.057),
    ("numeric_key_ent", 0.064, 0.083),
]
def _panel_point(local_x: float, local_y: float, normal_offset: float = 0.0) -> tuple[float, float, float]:
    return (
        PANEL_CENTER_X + local_x * PANEL_DOWN_X + normal_offset * PANEL_NORMAL_X,
        local_y,
        PANEL_CENTER_Z + local_x * PANEL_DOWN_Z + normal_offset * PANEL_NORMAL_Z,
    )
def _panel_origin(local_x: float, local_y: float, normal_offset: float = 0.0) -> Origin:
    return Origin(
        xyz=_panel_point(local_x, local_y, normal_offset),
        rpy=(0.0, PANEL_PITCH, 0.0),
    )
def _rotated_box(
    size_x: float,
    size_y: float,
    size_z: float,
    *,
    center_xyz: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(size_x, size_y, size_z, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), PANEL_PITCH_DEG)
        .translate(center_xyz)
    )
def _build_base_mesh():
    base = cq.Workplane("XY").box(
        BASE_DEPTH,
        BASE_WIDTH,
        BASE_HEIGHT,
        centered=(True, True, False),
    )
    base = base.edges("|Z").fillet(0.010)

    inner_base = (
        cq.Workplane("XY")
        .box(
            BASE_DEPTH - SHELL_THICKNESS * 2.0,
            BASE_WIDTH - SHELL_THICKNESS * 2.0,
            BASE_HEIGHT - SHELL_THICKNESS,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, SHELL_THICKNESS))
    )
    drawer_opening = (
        cq.Workplane("XY")
        .box(0.060, DRAWER_OPENING_WIDTH, DRAWER_OPENING_HEIGHT, centered=(True, True, True))
        .translate((BASE_DEPTH * 0.5 - 0.014, 0.0, DRAWER_CENTER_Z))
    )
    return base.cut(inner_base).cut(drawer_opening)
def _build_pod_mesh():
    pod_block = (
        cq.Workplane("XY")
        .box(0.245, POD_WIDTH, 0.086, centered=(True, True, False))
        .translate((0.000, 0.0, BASE_HEIGHT - 0.002))
    )
    front_cutter = _rotated_box(
        0.260,
        0.290,
        0.180,
        center_xyz=_panel_point(0.018, 0.000, 0.090),
    )
    rear_cutter = (
        cq.Workplane("XY")
        .box(0.120, POD_WIDTH + 0.020, 0.090, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -28.0)
        .translate((-0.150, 0.0, 0.205))
    )
    pod = pod_block.cut(front_cutter).cut(rear_cutter)

    inner_pod_block = (
        cq.Workplane("XY")
        .box(
            0.237,
            POD_WIDTH - SHELL_THICKNESS * 2.0,
            0.078,
            centered=(True, True, False),
        )
        .translate((0.000, 0.0, BASE_HEIGHT + SHELL_THICKNESS))
    )
    inner_front_cutter = _rotated_box(
        0.240,
        POD_WIDTH + 0.020,
        0.160,
        center_xyz=_panel_point(0.018, 0.000, 0.076),
    )
    inner_rear_cutter = (
        cq.Workplane("XY")
        .box(0.112, POD_WIDTH + 0.010, 0.085, centered=(True, True, True))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -28.0)
        .translate((-0.147, 0.0, 0.198))
    )
    pod = pod.cut(inner_pod_block.cut(inner_front_cutter).cut(inner_rear_cutter))

    main_recess = _rotated_box(
        0.094,
        0.224,
        PANEL_RECESS_DEPTH,
        center_xyz=_panel_point(0.016, 0.000, -PANEL_RECESS_DEPTH * 0.5),
    )
    numeric_recess = _rotated_box(
        0.098,
        0.090,
        PANEL_RECESS_DEPTH + NUMERIC_RECESS_EXTRA,
        center_xyz=_panel_point(
            0.022,
            0.057,
            -(PANEL_RECESS_DEPTH + NUMERIC_RECESS_EXTRA) * 0.5,
        ),
    )
    pod = pod.cut(main_recess).cut(numeric_recess)

    for _, local_x, local_y in MENU_KEYS:
        pod = pod.cut(
            _rotated_box(
                0.010,
                0.021,
                0.018,
                center_xyz=_panel_point(local_x, local_y, -0.0065),
            )
        )

    for _, local_x, local_y in NUMERIC_KEYS:
        pod = pod.cut(
            _rotated_box(
                0.013,
                0.013,
                0.018,
                center_xyz=_panel_point(local_x, local_y, -0.0070),
            )
        )

    return pod
def _add_button_part(
    model: ArticulatedObject,
    *,
    parent: str,
    name: str,
    local_x: float,
    local_y: float,
    cap_size: tuple[float, float, float],
    stem_size: tuple[float, float, float],
    material: str,
    seat_offset: float,
):
    button = model.part(name)
    button.visual(
        Box(stem_size),
        origin=Origin(xyz=(0.0, 0.0, -stem_size[2] * 0.5)),
        material=material,
        name="stem",
    )
    button.visual(
        Box(cap_size),
        origin=Origin(xyz=(0.0, 0.0, cap_size[2] * 0.5)),
        material=material,
        name="cap",
    )
    button.inertial = Inertial.from_geometry(
        Box((max(cap_size[0], stem_size[0]), max(cap_size[1], stem_size[1]), cap_size[2] + stem_size[2])),
        mass=0.008,
        origin=Origin(xyz=(0.0, 0.0, -0.001)),
    )
    model.articulation(
        f"{parent}_to_{name}",
        ArticulationType.PRISMATIC,
        parent=parent,
        child=button,
        origin=_panel_origin(local_x, local_y, seat_offset),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=0.05,
            lower=0.0,
            upper=BUTTON_TRAVEL,
        ),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pos_register")

    shell = model.material("shell", rgba=(0.24, 0.25, 0.27, 1.0))
    shell_dark = model.material("shell_dark", rgba=(0.16, 0.17, 0.18, 1.0))
    drawer_face = model.material("drawer_face", rgba=(0.33, 0.34, 0.36, 1.0))
    trim = model.material("trim", rgba=(0.52, 0.53, 0.56, 1.0))
    key_light = model.material("key_light", rgba=(0.86, 0.87, 0.88, 1.0))
    key_dark = model.material("key_dark", rgba=(0.47, 0.49, 0.51, 1.0))
    glass = model.material("glass", rgba=(0.17, 0.29, 0.35, 0.50))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_base_mesh(), "pos_body"),
        material=shell,
        name="shell",
    )
    body.visual(
        Box((0.220, 0.250, 0.014)),
        origin=Origin(xyz=(0.040, 0.0, 0.010)),
        material=shell_dark,
        name="drawer_floor",
    )
    body.visual(
        Cylinder(radius=0.028, length=0.018),
        origin=Origin(xyz=(-0.092, 0.0, BASE_HEIGHT + 0.001)),
        material=shell_dark,
        name="boss",
    )
    body.inertial = Inertial.from_geometry(
        Box((BASE_DEPTH, BASE_WIDTH, BASE_HEIGHT + 0.010)),
        mass=3.8,
        origin=Origin(xyz=(0.0, 0.0, 0.0525)),
    )

    pod = model.part("pod")
    pod.visual(
        mesh_from_cadquery(_build_pod_mesh(), "pos_pod"),
        material=shell,
        name="shell",
    )
    pod.inertial = Inertial.from_geometry(
        Box((0.245, POD_WIDTH, 0.086)),
        mass=1.2,
        origin=Origin(xyz=(0.0, 0.0, 0.136)),
    )
    model.articulation(
        "body_to_pod",
        ArticulationType.FIXED,
        parent=body,
        child=pod,
        origin=Origin(),
    )

    drawer = model.part("drawer")
    drawer.visual(
        Box((0.008, 0.280, 0.062)),
        origin=Origin(xyz=(-0.004, 0.0, 0.0)),
        material=drawer_face,
        name="front",
    )
    drawer.visual(
        Box((0.230, 0.272, 0.054)),
        origin=Origin(xyz=(-0.123, 0.0, 0.0)),
        material=drawer_face,
        name="tray",
    )
    drawer.visual(
        Box((0.006, 0.110, 0.012)),
        origin=Origin(xyz=(0.003, 0.0, 0.0)),
        material=trim,
        name="pull",
    )
    drawer.inertial = Inertial.from_geometry(
        Box((0.238, 0.280, 0.062)),
        mass=1.1,
        origin=Origin(xyz=(-0.119, 0.0, 0.0)),
    )
    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(BASE_DEPTH * 0.5 - 0.0025, 0.0, DRAWER_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=45.0,
            velocity=0.30,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )

    stem = model.part("stem")
    stem.visual(
        Cylinder(radius=0.025, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=shell_dark,
        name="turntable",
    )
    stem.visual(
        Cylinder(radius=0.015, length=0.118),
        origin=Origin(xyz=(0.0, 0.0, 0.067)),
        material=shell_dark,
        name="post",
    )
    stem.visual(
        Box((0.040, 0.024, 0.102)),
        origin=Origin(xyz=(-0.012, 0.0, 0.123)),
        material=shell_dark,
        name="neck",
    )
    stem.visual(
        Box((0.024, 0.170, 0.014)),
        origin=Origin(xyz=(-0.020, 0.0, 0.176)),
        material=shell_dark,
        name="yoke_bar",
    )
    stem.visual(
        Box((0.028, 0.012, 0.052)),
        origin=Origin(xyz=(-0.026, -0.079, 0.151)),
        material=shell_dark,
        name="ear_0",
    )
    stem.visual(
        Box((0.028, 0.012, 0.052)),
        origin=Origin(xyz=(-0.026, 0.079, 0.151)),
        material=shell_dark,
        name="ear_1",
    )
    stem.inertial = Inertial.from_geometry(
        Box((0.055, 0.170, 0.184)),
        mass=0.65,
        origin=Origin(xyz=(-0.010, 0.0, 0.092)),
    )
    model.articulation(
        "body_to_stem",
        ArticulationType.REVOLUTE,
        parent=body,
        child=stem,
        origin=Origin(xyz=(-0.092, 0.0, BASE_HEIGHT + 0.010)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=1.5,
            lower=-1.15,
            upper=1.15,
        ),
    )

    screen = model.part("screen")
    screen.visual(
        Box((0.028, 0.182, 0.122)),
        origin=Origin(xyz=(-0.040, 0.0, 0.0)),
        material=shell_dark,
        name="housing",
    )
    screen.visual(
        Box((0.006, 0.170, 0.110)),
        origin=Origin(xyz=(-0.056, 0.0, 0.0)),
        material=trim,
        name="bezel",
    )
    screen.visual(
        Box((0.002, 0.154, 0.094)),
        origin=Origin(xyz=(-0.060, 0.0, 0.0)),
        material=glass,
        name="glass",
    )
    screen.visual(
        Box((0.026, 0.146, 0.014)),
        origin=Origin(xyz=(-0.027, 0.0, 0.0)),
        material=shell_dark,
        name="axle_bar",
    )
    screen.inertial = Inertial.from_geometry(
        Box((0.062, 0.182, 0.122)),
        mass=0.72,
        origin=Origin(xyz=(-0.036, 0.0, 0.0)),
    )
    model.articulation(
        "stem_to_screen",
        ArticulationType.REVOLUTE,
        parent=stem,
        child=screen,
        origin=Origin(xyz=(-0.026, 0.0, 0.151)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=1.3,
            lower=-0.35,
            upper=0.55,
        ),
    )

    for name, local_x, local_y in MENU_KEYS:
        _add_button_part(
            model,
            parent="pod",
            name=name,
            local_x=local_x,
            local_y=local_y,
            cap_size=(0.014, 0.026, 0.0042),
            stem_size=(0.010, 0.020, 0.0080),
            material="key_dark",
            seat_offset=0.0060,
        )

    for name, local_x, local_y in NUMERIC_KEYS:
        _add_button_part(
            model,
            parent="pod",
            name=name,
            local_x=local_x,
            local_y=local_y,
            cap_size=(0.018, 0.018, 0.0044),
            stem_size=(0.013, 0.013, 0.0080),
            material="key_light",
            seat_offset=0.0050,
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
