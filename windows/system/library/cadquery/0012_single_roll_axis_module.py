# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, single_roll_axis_module, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: single_roll_axis_module

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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

# ===== model =====
import math
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
FRAME_LEN = 0.186
FRAME_W = 0.100
FRAME_H = 0.130
PLATE_T = 0.016
RAIL_T = 0.014
FRAME_SIDE_X = FRAME_LEN / 2.0 - PLATE_T / 2.0
FRAME_INNER_FACE_X = FRAME_LEN / 2.0 - PLATE_T
CARTRIDGE_T = 0.022
CARTRIDGE_W = 0.064
CARTRIDGE_CENTER_X = FRAME_INNER_FACE_X - CARTRIDGE_T / 2.0
CARTRIDGE_INNER_FACE_X = CARTRIDGE_CENTER_X - CARTRIDGE_T / 2.0
JOURNAL_R = 0.0085
HUB_R = 0.013
SHOULDER_R = 0.0135
SHOULDER_T = 0.004
JOURNAL_LEN = CARTRIDGE_T
MAIN_SHAFT_LEN = 2.0 * CARTRIDGE_INNER_FACE_X
HUB_LEN = 0.044
MOUNT_PAD_L = 0.028
MOUNT_PAD_W = 0.022
MOUNT_PAD_T = 0.004
MOUNT_PAD_CENTER_Z = HUB_R
MOUNT_PAD_TOP_Z = MOUNT_PAD_CENTER_Z + MOUNT_PAD_T / 2.0
CLAMP_L = MOUNT_PAD_L
CLAMP_W = MOUNT_PAD_W
CLAMP_T = 0.005
WEB_L = 0.010
WEB_W = 0.022
WEB_H = 0.020
TOP_PLATE_L = 0.026
TOP_PLATE_W = 0.030
TOP_PLATE_T = 0.004
BRACKET_ORIGIN_Z = MOUNT_PAD_TOP_Z + CLAMP_T / 2.0
def _bearing_cartridge_shape() -> cq.Workplane:
    body = cq.Workplane("XY").box(CARTRIDGE_T, CARTRIDGE_W, CARTRIDGE_W)
    bore = cq.Workplane("YZ").circle(0.011).extrude(CARTRIDGE_T + 0.010, both=True)

    pocket_points = [
        (-0.018, -0.018),
        (-0.018, 0.018),
        (0.018, -0.018),
        (0.018, 0.018),
    ]
    front_pockets = (
        cq.Workplane("YZ")
        .pushPoints(pocket_points)
        .circle(0.0045)
        .extrude(0.0035)
        .translate((CARTRIDGE_T / 2.0 - 0.00175, 0.0, 0.0))
    )
    back_pockets = (
        cq.Workplane("YZ")
        .pushPoints(pocket_points)
        .circle(0.0045)
        .extrude(0.0035)
        .translate((-CARTRIDGE_T / 2.0 + 0.00175, 0.0, 0.0))
    )

    return body.cut(bore).cut(front_pockets).cut(back_pockets)
def _clamp_block_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(CLAMP_L, CLAMP_W, CLAMP_T)
        .edges("|Z")
        .fillet(0.0012)
    )
def _web_rib_shape() -> cq.Workplane:
    profile = [
        (-WEB_L / 2.0, -WEB_H / 2.0),
        (WEB_L / 2.0, -WEB_H / 2.0),
        (WEB_L * 0.32, WEB_H / 2.0),
        (-WEB_L * 0.32, WEB_H / 2.0),
    ]
    return cq.Workplane("XZ").polyline(profile).close().extrude(WEB_W / 2.0, both=True)
def _top_plate_shape() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(TOP_PLATE_L, TOP_PLATE_W, TOP_PLATE_T)
        .edges("|Z")
        .fillet(0.001)
    )
    return (
        plate.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .pushPoints([(-0.007, 0.0), (0.007, 0.0)])
        .hole(0.0045, depth=TOP_PLATE_T + 0.001)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="precision_roll_axis_rotary_module", assets=ASSETS)

    frame_gray = model.material("frame_gray", rgba=(0.25, 0.28, 0.31, 1.0))
    cartridge_aluminum = model.material("cartridge_aluminum", rgba=(0.74, 0.76, 0.80, 1.0))
    shaft_steel = model.material("shaft_steel", rgba=(0.62, 0.65, 0.69, 1.0))
    bracket_black = model.material("bracket_black", rgba=(0.16, 0.17, 0.19, 1.0))

    support_frame = model.part("support_frame")
    support_frame.visual(
        Box((PLATE_T, FRAME_W, FRAME_H)),
        origin=Origin(xyz=(-FRAME_SIDE_X, 0.0, 0.0)),
        material=frame_gray,
        name="left_plate",
    )
    support_frame.visual(
        Box((PLATE_T, FRAME_W, FRAME_H)),
        origin=Origin(xyz=(FRAME_SIDE_X, 0.0, 0.0)),
        material=frame_gray,
        name="right_plate",
    )
    support_frame.visual(
        Box((FRAME_LEN - 2.0 * PLATE_T, FRAME_W, RAIL_T)),
        origin=Origin(xyz=(0.0, 0.0, FRAME_H / 2.0 - RAIL_T / 2.0)),
        material=frame_gray,
        name="top_rail",
    )
    support_frame.visual(
        Box((FRAME_LEN - 2.0 * PLATE_T, FRAME_W, RAIL_T)),
        origin=Origin(xyz=(0.0, 0.0, -FRAME_H / 2.0 + RAIL_T / 2.0)),
        material=frame_gray,
        name="bottom_rail",
    )
    support_frame.inertial = Inertial.from_geometry(
        Box((FRAME_LEN, FRAME_W, FRAME_H)),
        mass=3.4,
    )

    bearing_mesh = mesh_from_cadquery(_bearing_cartridge_shape(), "bearing_cartridge.obj", assets=ASSETS)

    left_bearing = model.part("left_bearing_cartridge")
    left_bearing.visual(bearing_mesh, material=cartridge_aluminum, name="housing")
    left_bearing.inertial = Inertial.from_geometry(
        Box((CARTRIDGE_T, CARTRIDGE_W, CARTRIDGE_W)),
        mass=0.22,
    )

    right_bearing = model.part("right_bearing_cartridge")
    right_bearing.visual(bearing_mesh, material=cartridge_aluminum, name="housing")
    right_bearing.inertial = Inertial.from_geometry(
        Box((CARTRIDGE_T, CARTRIDGE_W, CARTRIDGE_W)),
        mass=0.22,
    )

    shaft = model.part("shaft")
    shaft.visual(
        Cylinder(radius=JOURNAL_R, length=JOURNAL_LEN),
        origin=Origin(xyz=(-CARTRIDGE_CENTER_X, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=shaft_steel,
        name="left_journal",
    )
    shaft.visual(
        Cylinder(radius=JOURNAL_R, length=JOURNAL_LEN),
        origin=Origin(xyz=(CARTRIDGE_CENTER_X, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=shaft_steel,
        name="right_journal",
    )
    shaft.visual(
        Cylinder(radius=SHOULDER_R, length=SHOULDER_T),
        origin=Origin(
            xyz=(-CARTRIDGE_INNER_FACE_X + SHOULDER_T / 2.0, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=shaft_steel,
        name="left_shoulder",
    )
    shaft.visual(
        Cylinder(radius=SHOULDER_R, length=SHOULDER_T),
        origin=Origin(
            xyz=(CARTRIDGE_INNER_FACE_X - SHOULDER_T / 2.0, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=shaft_steel,
        name="right_shoulder",
    )
    shaft.visual(
        Cylinder(radius=0.010, length=MAIN_SHAFT_LEN),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=shaft_steel,
        name="main_shaft",
    )
    shaft.visual(
        Cylinder(radius=HUB_R, length=HUB_LEN),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=shaft_steel,
        name="center_hub",
    )
    shaft.visual(
        Box((MOUNT_PAD_L, MOUNT_PAD_W, MOUNT_PAD_T)),
        origin=Origin(xyz=(0.0, 0.0, MOUNT_PAD_CENTER_Z)),
        material=shaft_steel,
        name="mount_pad",
    )
    shaft.inertial = Inertial.from_geometry(
        Box((FRAME_LEN - 0.020, 0.028, 0.028)),
        mass=0.68,
    )

    payload_bracket = model.part("payload_bracket")
    payload_bracket.visual(
        mesh_from_cadquery(_clamp_block_shape(), "payload_clamp_block.obj", assets=ASSETS),
        material=bracket_black,
        name="clamp_block",
    )
    payload_bracket.visual(
        mesh_from_cadquery(_web_rib_shape(), "payload_web_rib.obj", assets=ASSETS),
        origin=Origin(xyz=(0.0, 0.0, CLAMP_T / 2.0 + WEB_H / 2.0)),
        material=bracket_black,
        name="web_rib",
    )
    payload_bracket.visual(
        mesh_from_cadquery(_top_plate_shape(), "payload_top_plate.obj", assets=ASSETS),
        origin=Origin(xyz=(0.0, 0.0, CLAMP_T / 2.0 + WEB_H + TOP_PLATE_T / 2.0)),
        material=bracket_black,
        name="top_plate",
    )
    payload_bracket.inertial = Inertial.from_geometry(
        Box((TOP_PLATE_L, TOP_PLATE_W, CLAMP_T + WEB_H + TOP_PLATE_T)),
        mass=0.18,
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
    )

    model.articulation(
        "frame_to_left_bearing",
        ArticulationType.FIXED,
        parent=support_frame,
        child=left_bearing,
        origin=Origin(xyz=(-CARTRIDGE_CENTER_X, 0.0, 0.0)),
    )
    model.articulation(
        "frame_to_right_bearing",
        ArticulationType.FIXED,
        parent=support_frame,
        child=right_bearing,
        origin=Origin(xyz=(CARTRIDGE_CENTER_X, 0.0, 0.0)),
    )
    model.articulation(
        "frame_to_shaft_roll",
        ArticulationType.REVOLUTE,
        parent=support_frame,
        child=shaft,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=3.0,
            lower=-math.pi,
            upper=math.pi,
        ),
    )
    model.articulation(
        "shaft_to_payload_bracket",
        ArticulationType.FIXED,
        parent=shaft,
        child=payload_bracket,
        origin=Origin(xyz=(0.0, 0.0, BRACKET_ORIGIN_Z)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
