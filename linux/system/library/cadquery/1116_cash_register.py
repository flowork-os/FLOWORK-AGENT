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
BODY_W = 0.290
BODY_D = 0.330
BODY_FRONT_H = 0.096
BODY_REAR_H = 0.155
SLOPE_START_Y = -0.015
SLOPE_END_Y = 0.095
DRAWER_FRONT_W = 0.242
DRAWER_FRONT_T = 0.012
DRAWER_FRONT_H = 0.062
DRAWER_TRAY_W = 0.226
DRAWER_TRAY_D = 0.230
DRAWER_WALL_T = 0.004
DRAWER_SIDE_H = 0.045
DRAWER_BOTTOM_T = 0.004
DRAWER_DIVIDER_T = 0.003
DRAWER_TRAVEL = 0.112
DRAWER_FLOOR_Z = 0.014
SCREEN_PIVOT_X = 0.104
SCREEN_PIVOT_Y = 0.122
SCREEN_MOUNT_H = 0.006
def _slope_z(y_pos: float) -> float:
    slope = (BODY_REAR_H - BODY_FRONT_H) / (SLOPE_END_Y - SLOPE_START_Y)
    return BODY_FRONT_H + (y_pos - SLOPE_START_Y) * slope
def _build_register_shell() -> cq.Workplane:
    side_profile = [
        (-BODY_D / 2.0, 0.0),
        (-BODY_D / 2.0, BODY_FRONT_H),
        (SLOPE_START_Y, BODY_FRONT_H),
        (SLOPE_END_Y, BODY_REAR_H),
        (BODY_D / 2.0, BODY_REAR_H),
        (BODY_D / 2.0, 0.0),
    ]
    shell = (
        cq.Workplane("YZ")
        .polyline(side_profile)
        .close()
        .extrude(BODY_W / 2.0, both=True)
    )

    drawer_bay = cq.Workplane("XY").box(0.248, 0.252, 0.066).translate(
        (0.0, -0.039, 0.046)
    )
    return shell.cut(drawer_bay)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pos_cash_register")

    body_color = model.material("body_charcoal", rgba=(0.18, 0.19, 0.21, 1.0))
    panel_color = model.material("panel_black", rgba=(0.10, 0.11, 0.12, 1.0))
    key_color = model.material("key_grey", rgba=(0.52, 0.55, 0.58, 1.0))
    accent_color = model.material("accent_blue", rgba=(0.14, 0.31, 0.45, 1.0))
    rubber_color = model.material("rubber_dark", rgba=(0.06, 0.06, 0.07, 1.0))
    drawer_color = model.material("drawer_dark", rgba=(0.20, 0.21, 0.23, 1.0))
    handle_color = model.material("handle_black", rgba=(0.08, 0.08, 0.09, 1.0))
    screen_body_color = model.material("screen_body", rgba=(0.17, 0.18, 0.20, 1.0))
    glass_color = model.material("glass_teal", rgba=(0.20, 0.49, 0.55, 0.45))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_register_shell(), "register_shell"),
        material=body_color,
        name="shell",
    )

    slope_angle = math.atan2(
        BODY_REAR_H - BODY_FRONT_H,
        SLOPE_END_Y - SLOPE_START_Y,
    )

    body.visual(
        Box((0.178, 0.096, 0.003)),
        origin=Origin(
            xyz=(0.0, 0.040, _slope_z(0.040) + 0.0008),
            rpy=(slope_angle, 0.0, 0.0),
        ),
        material=panel_color,
        name="keypad_plate",
    )

    key_centers_x = (-0.054, -0.018, 0.018, 0.054)
    key_centers_y = (-0.002, 0.024, 0.050, 0.076)
    for row_index, center_y in enumerate(key_centers_y):
        for col_index, center_x in enumerate(key_centers_x):
            body.visual(
                Box((0.024, 0.019, 0.006)),
                origin=Origin(
                    xyz=(center_x, center_y, _slope_z(center_y) + 0.0015),
                    rpy=(slope_angle, 0.0, 0.0),
                ),
                material=key_color,
                name=f"key_{row_index}_{col_index}",
            )

    for index, x_pos in enumerate((-0.082, -0.044, 0.044, 0.082)):
        body.visual(
            Box((0.022, 0.026, 0.006)),
            origin=Origin(
                xyz=(x_pos, 0.106, BODY_REAR_H + 0.0015),
            ),
            material=accent_color if index < 2 else key_color,
            name=f"rear_button_{index}",
        )

    body.visual(
        Box((0.118, 0.012, 0.003)),
        origin=Origin(xyz=(0.0, 0.121, BODY_REAR_H + 0.0015)),
        material=panel_color,
        name="receipt_slot",
    )

    body.visual(
        Box((0.248, 0.010, 0.070)),
        origin=Origin(xyz=(0.0, -BODY_D / 2.0 + 0.005, 0.049)),
        material=panel_color,
        name="drawer_frame",
    )
    body.visual(
        Cylinder(radius=0.012, length=SCREEN_MOUNT_H),
        origin=Origin(
            xyz=(SCREEN_PIVOT_X, SCREEN_PIVOT_Y, BODY_REAR_H + SCREEN_MOUNT_H / 2.0),
        ),
        material=panel_color,
        name="screen_mount",
    )
    for index, (x_pos, y_pos) in enumerate(
        (
            (-0.108, -0.122),
            (0.108, -0.122),
            (-0.108, 0.122),
            (0.108, 0.122),
        )
    ):
        body.visual(
            Box((0.030, 0.018, 0.006)),
            origin=Origin(xyz=(x_pos, y_pos, -0.003)),
            material=rubber_color,
            name=f"foot_{index}",
        )

    body.inertial = Inertial.from_geometry(
        Box((BODY_W, BODY_D, BODY_REAR_H + SCREEN_MOUNT_H)),
        mass=3.8,
        origin=Origin(xyz=(0.0, 0.0, (BODY_REAR_H + SCREEN_MOUNT_H) / 2.0)),
    )

    drawer = model.part("drawer")
    drawer.visual(
        Box((DRAWER_FRONT_W, DRAWER_FRONT_T, DRAWER_FRONT_H)),
        origin=Origin(
            xyz=(0.0, -DRAWER_FRONT_T / 2.0, DRAWER_FRONT_H / 2.0),
        ),
        material=drawer_color,
        name="drawer_front",
    )
    drawer.visual(
        Box((0.106, 0.006, 0.012)),
        origin=Origin(xyz=(0.0, -0.015, 0.031)),
        material=handle_color,
        name="drawer_pull",
    )
    drawer.visual(
        Box((DRAWER_TRAY_W, DRAWER_TRAY_D, DRAWER_BOTTOM_T)),
        origin=Origin(
            xyz=(0.0, DRAWER_TRAY_D / 2.0, DRAWER_BOTTOM_T / 2.0),
        ),
        material=drawer_color,
        name="tray_bottom",
    )
    side_wall_x = DRAWER_TRAY_W / 2.0 - DRAWER_WALL_T / 2.0
    side_wall_y = DRAWER_TRAY_D / 2.0
    side_wall_z = DRAWER_SIDE_H / 2.0 + DRAWER_BOTTOM_T
    drawer.visual(
        Box((DRAWER_WALL_T, DRAWER_TRAY_D, DRAWER_SIDE_H)),
        origin=Origin(xyz=(-side_wall_x, side_wall_y, side_wall_z)),
        material=drawer_color,
        name="side_wall_0",
    )
    drawer.visual(
        Box((DRAWER_WALL_T, DRAWER_TRAY_D, DRAWER_SIDE_H)),
        origin=Origin(xyz=(side_wall_x, side_wall_y, side_wall_z)),
        material=drawer_color,
        name="side_wall_1",
    )
    drawer.visual(
        Box((DRAWER_TRAY_W, DRAWER_WALL_T, DRAWER_SIDE_H)),
        origin=Origin(
            xyz=(0.0, DRAWER_TRAY_D - DRAWER_WALL_T / 2.0, side_wall_z),
        ),
        material=drawer_color,
        name="back_wall",
    )
    for index, x_pos in enumerate((-0.055, 0.0, 0.055)):
        drawer.visual(
            Box((DRAWER_DIVIDER_T, 0.152, 0.029)),
            origin=Origin(xyz=(x_pos, 0.138, 0.0185)),
            material=drawer_color,
            name=f"divider_{index}",
        )

    drawer.inertial = Inertial.from_geometry(
        Box((DRAWER_FRONT_W, DRAWER_TRAY_D + 0.010, DRAWER_FRONT_H)),
        mass=0.9,
        origin=Origin(xyz=(0.0, 0.110, 0.031)),
    )

    screen = model.part("screen")
    screen.visual(
        Cylinder(radius=0.008, length=0.060),
        origin=Origin(xyz=(0.0, 0.0, 0.030)),
        material=screen_body_color,
        name="post",
    )
    screen.visual(
        Box((0.044, 0.012, 0.030)),
        origin=Origin(xyz=(-0.022, -0.006, 0.075)),
        material=screen_body_color,
        name="neck",
    )
    screen.visual(
        Box((0.078, 0.016, 0.058)),
        origin=Origin(xyz=(-0.058, -0.008, 0.112)),
        material=screen_body_color,
        name="screen_panel",
    )
    screen.visual(
        Box((0.066, 0.004, 0.046)),
        origin=Origin(xyz=(-0.058, -0.018, 0.112)),
        material=glass_color,
        name="screen_glass",
    )
    screen.inertial = Inertial.from_geometry(
        Box((0.090, 0.020, 0.150)),
        mass=0.18,
        origin=Origin(xyz=(-0.040, -0.008, 0.080)),
    )

    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(0.0, -BODY_D / 2.0, DRAWER_FLOOR_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=45.0,
            velocity=0.25,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )
    model.articulation(
        "body_to_screen",
        ArticulationType.REVOLUTE,
        parent=body,
        child=screen,
        origin=Origin(
            xyz=(
                SCREEN_PIVOT_X,
                SCREEN_PIVOT_Y,
                BODY_REAR_H + SCREEN_MOUNT_H,
            )
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=2.0,
            lower=-1.0,
            upper=1.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
