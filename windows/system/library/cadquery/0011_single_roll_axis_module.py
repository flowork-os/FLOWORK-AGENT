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
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
FRAME_OUTER_X = 0.160
FRAME_OUTER_Y = 0.118
FRAME_OUTER_Z = 0.142
SIDE_PLATE_T = 0.014
RAIL_T = 0.015
FRAME_CLEAR_RADIUS = 0.018
CARTRIDGE_LEN = 0.016
CARTRIDGE_BODY = 0.052
CARTRIDGE_BOSS_LEN = 0.006
CARTRIDGE_BORE_R = 0.0105
CARTRIDGE_OUTER_R = 0.024
SHAFT_R = 0.0095
SHAFT_LEN = 0.224
COLLAR_LEN = 0.008
COLLAR_R = 0.017
LEFT_PLATE_CENTER_X = -(FRAME_OUTER_X / 2.0 - SIDE_PLATE_T / 2.0)
RIGHT_PLATE_CENTER_X = FRAME_OUTER_X / 2.0 - SIDE_PLATE_T / 2.0
LEFT_CARTRIDGE_CENTER_X = -(FRAME_OUTER_X / 2.0 + CARTRIDGE_LEN / 2.0)
RIGHT_CARTRIDGE_CENTER_X = FRAME_OUTER_X / 2.0 + CARTRIDGE_LEN / 2.0
LEFT_COLLAR_CENTER_X = -(FRAME_OUTER_X / 2.0 + CARTRIDGE_LEN + CARTRIDGE_BOSS_LEN + COLLAR_LEN / 2.0)
RIGHT_COLLAR_CENTER_X = FRAME_OUTER_X / 2.0 + CARTRIDGE_LEN + CARTRIDGE_BOSS_LEN + COLLAR_LEN / 2.0
def _x_cylinder(length: float, radius: float) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length / 2.0, both=True)
def _frame_shell() -> cq.Workplane:
    side_plate = cq.Workplane("XY").box(SIDE_PLATE_T, FRAME_OUTER_Y, FRAME_OUTER_Z)
    left_plate = side_plate.translate((LEFT_PLATE_CENTER_X, 0.0, 0.0))
    right_plate = side_plate.translate((RIGHT_PLATE_CENTER_X, 0.0, 0.0))

    rail_span_x = FRAME_OUTER_X - 2.0 * SIDE_PLATE_T
    top_rail = cq.Workplane("XY").box(rail_span_x, FRAME_OUTER_Y, RAIL_T).translate(
        (0.0, 0.0, FRAME_OUTER_Z / 2.0 - RAIL_T / 2.0)
    )
    bottom_rail = cq.Workplane("XY").box(rail_span_x, FRAME_OUTER_Y, RAIL_T).translate(
        (0.0, 0.0, -(FRAME_OUTER_Z / 2.0 - RAIL_T / 2.0))
    )

    hole_cutter = _x_cylinder(SIDE_PLATE_T + 0.010, FRAME_CLEAR_RADIUS)
    left_hole = hole_cutter.translate((LEFT_PLATE_CENTER_X, 0.0, 0.0))
    right_hole = hole_cutter.translate((RIGHT_PLATE_CENTER_X, 0.0, 0.0))

    return left_plate.union(right_plate).union(top_rail).union(bottom_rail).cut(left_hole).cut(right_hole)
def _bearing_cartridge(sign: float) -> cq.Workplane:
    center_x = LEFT_CARTRIDGE_CENTER_X if sign < 0 else RIGHT_CARTRIDGE_CENTER_X
    boss_shift = sign * (CARTRIDGE_LEN / 2.0 + CARTRIDGE_BOSS_LEN / 2.0)

    body = (
        cq.Workplane("XY")
        .box(CARTRIDGE_LEN, CARTRIDGE_BODY, CARTRIDGE_BODY)
        .edges("|X")
        .fillet(0.003)
    )
    boss = _x_cylinder(CARTRIDGE_BOSS_LEN, CARTRIDGE_OUTER_R).translate((boss_shift, 0.0, 0.0))
    bore = _x_cylinder(CARTRIDGE_LEN + CARTRIDGE_BOSS_LEN + 0.008, CARTRIDGE_BORE_R)
    return body.union(boss).cut(bore).translate((center_x, 0.0, 0.0))
def _shaft() -> cq.Workplane:
    return _x_cylinder(SHAFT_LEN, SHAFT_R)
def _collar(center_x: float) -> cq.Workplane:
    collar = _x_cylinder(COLLAR_LEN, COLLAR_R).cut(_x_cylinder(COLLAR_LEN + 0.004, SHAFT_R))
    return collar.translate((center_x, 0.0, 0.0))
def _payload_bracket() -> cq.Workplane:
    clamp_block = (
        cq.Workplane("XY")
        .box(0.026, 0.030, 0.018)
        .translate((0.0, 0.0, 0.012))
        .cut(_x_cylinder(0.032, SHAFT_R * 0.97))
    )
    upright = cq.Workplane("XY").box(0.016, 0.008, 0.028).translate((0.0, 0.012, 0.032))
    top_pad = cq.Workplane("XY").box(0.028, 0.020, 0.006).translate((0.0, 0.018, 0.046))
    gusset = (
        cq.Workplane("YZ")
        .moveTo(0.0, 0.016)
        .lineTo(0.0, 0.040)
        .lineTo(0.014, 0.040)
        .close()
        .extrude(0.016, both=True)
        .translate((0.0, 0.004, 0.0))
    )
    return clamp_block.union(upright).union(top_pad).union(gusset)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="precision_roll_axis_module", assets=ASSETS)

    frame_gray = model.material("frame_gray", rgba=(0.72, 0.74, 0.77, 1.0))
    steel_dark = model.material("steel_dark", rgba=(0.33, 0.35, 0.38, 1.0))
    bearing_black = model.material("bearing_black", rgba=(0.16, 0.17, 0.18, 1.0))
    bracket_gray = model.material("bracket_gray", rgba=(0.58, 0.60, 0.63, 1.0))

    frame = model.part("support_frame")
    frame.visual(
        mesh_from_cadquery(_frame_shell(), "support_frame_shell.obj", assets=ASSETS),
        name="frame_shell",
        material=frame_gray,
    )
    frame.visual(
        mesh_from_cadquery(_bearing_cartridge(-1.0), "left_bearing_cartridge.obj", assets=ASSETS),
        name="left_bearing_cartridge",
        material=bearing_black,
    )
    frame.visual(
        mesh_from_cadquery(_bearing_cartridge(1.0), "right_bearing_cartridge.obj", assets=ASSETS),
        name="right_bearing_cartridge",
        material=bearing_black,
    )
    frame.inertial = Inertial.from_geometry(
        Box((FRAME_OUTER_X + 2.0 * CARTRIDGE_LEN, FRAME_OUTER_Y, FRAME_OUTER_Z)),
        mass=2.0,
    )

    rotor = model.part("rotor")
    rotor.visual(
        mesh_from_cadquery(_shaft(), "rotary_shaft.obj", assets=ASSETS),
        name="shaft",
        material=steel_dark,
    )
    rotor.visual(
        mesh_from_cadquery(_collar(LEFT_COLLAR_CENTER_X), "left_retaining_collar.obj", assets=ASSETS),
        name="left_collar",
        material=steel_dark,
    )
    rotor.visual(
        mesh_from_cadquery(_collar(RIGHT_COLLAR_CENTER_X), "right_retaining_collar.obj", assets=ASSETS),
        name="right_collar",
        material=steel_dark,
    )
    rotor.visual(
        mesh_from_cadquery(_payload_bracket(), "payload_bracket.obj", assets=ASSETS),
        name="payload_bracket",
        material=bracket_gray,
    )
    rotor.inertial = Inertial.from_geometry(
        Box((SHAFT_LEN, 0.044, 0.060)),
        mass=0.85,
    )

    model.articulation(
        "frame_to_rotor",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=rotor,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=6.0,
            lower=-3.14159,
            upper=3.14159,
        ),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
