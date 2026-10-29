# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_W = 0.42
BODY_H = 0.68
BODY_D = 0.165
BODY_WALL = 0.018
BACK_WALL = 0.006
FACE_FRAME_D = 0.012
FRONT_STILE_W = 0.024
FRONT_RAIL_H = 0.028
COVER_W = BODY_W - 0.016
COVER_H = BODY_H - 0.020
COVER_D = 0.026
COVER_WALL = 0.006
COVER_FACE_T = 0.004
COVER_HINGE_X = BODY_D + 0.003
COVER_HINGE_Y = -COVER_W / 2.0
COVER_HINGE_Z = 0.0
COVER_OPENING_SIDE = 0.030
COVER_OPENING_Z0 = -0.255
COVER_OPENING_Z1 = 0.215
COVER_BAR_COUNT = 7
COVER_BAR_W = 0.008
COVER_BAR_D = 0.010
DRAWER_W = 0.352
DRAWER_H = 0.560
DRAWER_L = 0.145
DRAWER_FRAME_T = 0.014
DRAWER_FRONT_X = 0.153
DRAWER_CENTER_Z = -0.024
FILTER_D = 0.070
RUNNER_L = 0.120
RUNNER_W = 0.020
RUNNER_H = 0.010
RUNNER_Y = 0.122
RUNNER_Z = -DRAWER_H / 2.0 - RUNNER_H / 2.0 + 0.001
RAIL_H = 0.009
RAIL_TOP_Z = DRAWER_CENTER_Z + RUNNER_Z - RUNNER_H / 2.0
RAIL_CENTER_Z = RAIL_TOP_Z - RAIL_H / 2.0
RAIL_X = DRAWER_FRONT_X - 0.072
def _span_box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> cq.Workplane:
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)
    )
def _cover_shell_shape() -> cq.Workplane:
    outer = _span_box(0.0, COVER_D, 0.0, COVER_W, -COVER_H / 2.0, COVER_H / 2.0)
    outer = outer.edges("|Z").fillet(0.010)

    inner = _span_box(
        -0.003,
        COVER_D - COVER_FACE_T + 0.001,
        COVER_WALL,
        COVER_W - COVER_WALL,
        -COVER_H / 2.0 + COVER_WALL,
        COVER_H / 2.0 - COVER_WALL,
    )
    shell = outer.cut(inner)

    opening = _span_box(
        -0.002,
        COVER_D + 0.002,
        COVER_OPENING_SIDE,
        COVER_W - COVER_OPENING_SIDE,
        COVER_OPENING_Z0,
        COVER_OPENING_Z1,
    )
    shell = shell.cut(opening)

    opening_w = COVER_W - 2.0 * COVER_OPENING_SIDE
    pitch = opening_w / (COVER_BAR_COUNT + 1)
    for index in range(COVER_BAR_COUNT):
        y_center = COVER_OPENING_SIDE + (index + 1) * pitch
        bar = _span_box(
            COVER_D - COVER_FACE_T - COVER_BAR_D,
            COVER_D - 0.002,
            y_center - COVER_BAR_W / 2.0,
            y_center + COVER_BAR_W / 2.0,
            COVER_OPENING_Z0,
            COVER_OPENING_Z1,
        )
        shell = shell.union(bar)

    lip = _span_box(
        COVER_D - 0.012,
        COVER_D,
        COVER_W - 0.055,
        COVER_W - 0.012,
        -0.065,
        -0.015,
    )
    return shell.union(lip)
def _drawer_frame_shape() -> cq.Workplane:
    outer = _span_box(
        -DRAWER_L,
        0.0,
        -DRAWER_W / 2.0,
        DRAWER_W / 2.0,
        -DRAWER_H / 2.0,
        DRAWER_H / 2.0,
    )
    frame_opening = _span_box(
        -DRAWER_L - 0.002,
        0.002,
        -(DRAWER_W / 2.0 - DRAWER_FRAME_T),
        DRAWER_W / 2.0 - DRAWER_FRAME_T,
        -(DRAWER_H / 2.0 - DRAWER_FRAME_T),
        DRAWER_H / 2.0 - DRAWER_FRAME_T,
    )
    frame = outer.cut(frame_opening)

    rear_retainer = _span_box(
        -DRAWER_L + 0.010,
        -DRAWER_L + 0.016,
        -DRAWER_W / 2.0,
        DRAWER_W / 2.0,
        -DRAWER_H / 2.0 + 0.016,
        DRAWER_H / 2.0 - 0.016,
    )
    pull_tab = _span_box(
        -0.006,
        0.010,
        -0.060,
        0.060,
        -DRAWER_H / 2.0,
        -DRAWER_H / 2.0 + 0.052,
    )
    return frame.union(rear_retainer).union(pull_tab)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_air_purifier")

    shell_white = model.material("shell_white", rgba=(0.93, 0.94, 0.95, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.72, 0.74, 0.77, 1.0))
    charcoal = model.material("charcoal", rgba=(0.18, 0.20, 0.22, 1.0))
    filter_gray = model.material("filter_gray", rgba=(0.56, 0.60, 0.63, 1.0))
    tint = model.material("tint", rgba=(0.10, 0.12, 0.14, 0.95))

    body = model.part("body")
    body.visual(
        Box((BACK_WALL, BODY_W, BODY_H)),
        origin=Origin(xyz=(BACK_WALL / 2.0, 0.0, 0.0)),
        material=shell_white,
        name="rear_shell",
    )
    for index, y_sign in enumerate((-1.0, 1.0)):
        body.visual(
            Box((BODY_D - BACK_WALL, BODY_WALL, BODY_H)),
            origin=Origin(
                xyz=(
                    BACK_WALL + (BODY_D - BACK_WALL) / 2.0,
                    y_sign * (BODY_W / 2.0 - BODY_WALL / 2.0),
                    0.0,
                )
            ),
            material=shell_white,
            name=f"side_wall_{index}",
        )
    body.visual(
        Box((BODY_D - BACK_WALL, BODY_W - 2.0 * BODY_WALL, BODY_WALL)),
        origin=Origin(
            xyz=(
                BACK_WALL + (BODY_D - BACK_WALL) / 2.0,
                0.0,
                BODY_H / 2.0 - BODY_WALL / 2.0,
            )
        ),
        material=shell_white,
        name="top_wall",
    )
    body.visual(
        Box((BODY_D - BACK_WALL, BODY_W - 2.0 * BODY_WALL, BODY_WALL)),
        origin=Origin(
            xyz=(
                BACK_WALL + (BODY_D - BACK_WALL) / 2.0,
                0.0,
                -BODY_H / 2.0 + BODY_WALL / 2.0,
            )
        ),
        material=shell_white,
        name="bottom_wall",
    )
    for index, y_sign in enumerate((-1.0, 1.0)):
        body.visual(
            Box((FACE_FRAME_D, FRONT_STILE_W, BODY_H - 0.040)),
            origin=Origin(
                xyz=(
                    BODY_D - FACE_FRAME_D / 2.0,
                    y_sign * (BODY_W / 2.0 - FRONT_STILE_W / 2.0),
                    0.0,
                )
            ),
            material=shell_white,
            name=f"front_stile_{index}",
        )
    body.visual(
        Box((FACE_FRAME_D, BODY_W - 2.0 * FRONT_STILE_W, FRONT_RAIL_H)),
        origin=Origin(
            xyz=(
                BODY_D - FACE_FRAME_D / 2.0,
                0.0,
                BODY_H / 2.0 - FRONT_RAIL_H / 2.0,
            )
        ),
        material=shell_white,
        name="front_rail_top",
    )
    body.visual(
        Box((FACE_FRAME_D, BODY_W - 2.0 * FRONT_STILE_W, FRONT_RAIL_H)),
        origin=Origin(
            xyz=(
                BODY_D - FACE_FRAME_D / 2.0,
                0.0,
                -BODY_H / 2.0 + FRONT_RAIL_H / 2.0,
            )
        ),
        material=shell_white,
        name="front_rail_bottom",
    )
    body.visual(
        Box((0.006, 0.006, COVER_H)),
        origin=Origin(xyz=(COVER_HINGE_X - 0.003, COVER_HINGE_Y, 0.0)),
        material=trim_gray,
        name="hinge_leaf",
    )
    body.visual(
        Box((0.118, 0.248, 0.004)),
        origin=Origin(xyz=(BODY_D - 0.006, 0.0, BODY_H / 2.0 - 0.003)),
        material=charcoal,
        name="outlet_panel",
    )
    for index, y_sign in enumerate((-1.0, 1.0)):
        body.visual(
            Box((RUNNER_L, RUNNER_W + 0.002, RAIL_H)),
            origin=Origin(xyz=(RAIL_X, y_sign * RUNNER_Y, RAIL_CENTER_Z)),
            material=trim_gray,
            name=f"rail_{index}",
        )
    body.inertial = Inertial.from_geometry(
        Box((BODY_D, BODY_W, BODY_H)),
        mass=8.4,
        origin=Origin(xyz=(BODY_D / 2.0, 0.0, 0.0)),
    )

    cover = model.part("cover")
    cover.visual(
        mesh_from_cadquery(_cover_shell_shape(), "purifier_cover_shell"),
        material=shell_white,
        name="cover_shell",
    )
    cover.visual(
        Box((0.004, 0.006, COVER_H)),
        origin=Origin(xyz=(0.002, 0.003, 0.0)),
        material=trim_gray,
        name="hinge_stile",
    )
    cover.visual(
        Box((0.0024, 0.072, 0.016)),
        origin=Origin(xyz=(COVER_D - 0.0012, COVER_W / 2.0, COVER_H / 2.0 - 0.060)),
        material=tint,
        name="status_window",
    )
    cover.inertial = Inertial.from_geometry(
        Box((COVER_D, COVER_W, COVER_H)),
        mass=1.8,
        origin=Origin(xyz=(COVER_D / 2.0, COVER_W / 2.0, 0.0)),
    )

    drawer = model.part("drawer")
    drawer.visual(
        mesh_from_cadquery(_drawer_frame_shape(), "purifier_filter_drawer"),
        material=charcoal,
        name="drawer_frame",
    )
    drawer.visual(
        Box((FILTER_D, DRAWER_W - 2.0 * DRAWER_FRAME_T, DRAWER_H - 2.0 * DRAWER_FRAME_T)),
        origin=Origin(xyz=(-0.074, 0.0, 0.0)),
        material=filter_gray,
        name="filter_media",
    )
    for index, y_sign in enumerate((-1.0, 1.0)):
        drawer.visual(
            Box((RUNNER_L, RUNNER_W, RUNNER_H)),
            origin=Origin(xyz=(-0.072, y_sign * RUNNER_Y, RUNNER_Z)),
            material=trim_gray,
            name=f"runner_{index}",
        )
    drawer.inertial = Inertial.from_geometry(
        Box((DRAWER_L, DRAWER_W, DRAWER_H + RUNNER_H)),
        mass=1.2,
        origin=Origin(xyz=(-DRAWER_L / 2.0, 0.0, -RUNNER_H / 2.0)),
    )

    model.articulation(
        "body_to_cover",
        ArticulationType.REVOLUTE,
        parent=body,
        child=cover,
        origin=Origin(xyz=(COVER_HINGE_X, COVER_HINGE_Y, COVER_HINGE_Z)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.4,
            lower=0.0,
            upper=1.95,
        ),
    )
    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(DRAWER_FRONT_X, 0.0, DRAWER_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=60.0,
            velocity=0.16,
            lower=0.0,
            upper=0.090,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
