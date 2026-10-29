# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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
def _build_body_shell():
    shell = (
        cq.Workplane("XY")
        .box(0.044, 0.031, 0.094, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.004)
        .edges(">Z")
        .fillet(0.002)
    )

    control_pocket = (
        cq.Workplane("XY")
        .box(0.032, 0.004, 0.062, centered=(True, True, False))
        .translate((0.0, -0.0135, 0.018))
    )
    return shell.cut(control_pocket)
def _build_head_shell():
    return (
        cq.Workplane("XY")
        .box(0.068, 0.044, 0.036)
        .edges("|Z")
        .fillet(0.0045)
        .edges(">Z")
        .fillet(0.002)
    )
def _add_button(
    model: ArticulatedObject,
    body,
    button_material,
    name: str,
    *,
    joint_xyz: tuple[float, float, float],
    cap_size: tuple[float, float],
) -> None:
    cap_x, cap_z = cap_size
    button = model.part(name)
    button.visual(
        Box((cap_x, 0.0026, cap_z)),
        origin=Origin(xyz=(0.0, -0.0013, 0.0)),
        material=button_material,
        name="cap",
    )
    button.visual(
        Box((cap_x * 0.60, 0.0040, cap_z * 0.60)),
        origin=Origin(xyz=(0.0, 0.0020, 0.0)),
        material=button_material,
        name="stem",
    )
    model.articulation(
        f"body_to_{name}",
        ArticulationType.PRISMATIC,
        parent=body,
        child=button,
        origin=Origin(xyz=joint_xyz),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=0.04,
            lower=-0.0015,
            upper=0.0,
        ),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="travel_flash")

    body_black = model.material("body_black", rgba=(0.13, 0.13, 0.14, 1.0))
    head_black = model.material("head_black", rgba=(0.10, 0.10, 0.11, 1.0))
    button_gray = model.material("button_gray", rgba=(0.30, 0.31, 0.33, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.36, 0.37, 0.40, 1.0))
    screen_bezel = model.material("screen_bezel", rgba=(0.09, 0.09, 0.10, 1.0))
    screen_glass = model.material("screen_glass", rgba=(0.17, 0.29, 0.33, 0.55))
    diffuser = model.material("diffuser", rgba=(0.95, 0.95, 0.97, 0.96))
    shoe_metal = model.material("shoe_metal", rgba=(0.63, 0.66, 0.70, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_build_body_shell(), "flash_body_shell"),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=body_black,
        name="body_shell",
    )
    body.visual(
        Box((0.024, 0.020, 0.006)),
        origin=Origin(xyz=(0.0, 0.002, 0.115)),
        material=body_black,
        name="neck_collar",
    )
    body.visual(
        Box((0.014, 0.016, 0.015)),
        origin=Origin(xyz=(0.0, 0.0, 0.0105)),
        material=body_black,
        name="shoe_stem",
    )
    body.visual(
        Box((0.018, 0.020, 0.003)),
        origin=Origin(xyz=(0.0, 0.0, 0.0015)),
        material=shoe_metal,
        name="shoe_plate",
    )
    body.visual(
        Box((0.022, 0.005, 0.0015)),
        origin=Origin(xyz=(0.0, 0.0075, 0.00225)),
        material=shoe_metal,
        name="shoe_rail_front",
    )
    body.visual(
        Box((0.022, 0.005, 0.0015)),
        origin=Origin(xyz=(0.0, -0.0075, 0.00225)),
        material=shoe_metal,
        name="shoe_rail_rear",
    )
    body.visual(
        Box((0.020, 0.0012, 0.008)),
        origin=Origin(xyz=(0.0, 0.0155, 0.061)),
        material=trim_gray,
        name="front_window",
    )

    screen = model.part("screen")
    screen.visual(
        Box((0.024, 0.0008, 0.018)),
        origin=Origin(xyz=(0.0, 0.0004, 0.0)),
        material=screen_bezel,
        name="bezel",
    )
    screen.visual(
        Box((0.018, 0.0006, 0.012)),
        origin=Origin(xyz=(0.0, 0.0011, 0.0)),
        material=screen_glass,
        name="glass",
    )
    model.articulation(
        "body_to_screen",
        ArticulationType.FIXED,
        parent=body,
        child=screen,
        origin=Origin(xyz=(0.0, -0.0155, 0.079)),
    )

    _add_button(
        model,
        body,
        button_gray,
        "top_button",
        joint_xyz=(0.0, -0.0155, 0.090),
        cap_size=(0.010, 0.006),
    )
    _add_button(
        model,
        body,
        button_gray,
        "left_button",
        joint_xyz=(-0.015, -0.0155, 0.079),
        cap_size=(0.006, 0.010),
    )
    _add_button(
        model,
        body,
        button_gray,
        "right_button",
        joint_xyz=(0.015, -0.0155, 0.079),
        cap_size=(0.006, 0.010),
    )
    _add_button(
        model,
        body,
        button_gray,
        "bottom_button",
        joint_xyz=(0.0, -0.0155, 0.068),
        cap_size=(0.010, 0.006),
    )
    _add_button(
        model,
        body,
        button_gray,
        "mode_button",
        joint_xyz=(0.0, -0.0155, 0.053),
        cap_size=(0.013, 0.006),
    )

    swivel = model.part("swivel")
    swivel.visual(
        Cylinder(radius=0.014, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=head_black,
        name="turret_base",
    )
    swivel.visual(
        Box((0.020, 0.018, 0.020)),
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
        material=head_black,
        name="swivel_post",
    )
    swivel.visual(
        Box((0.078, 0.010, 0.008)),
        origin=Origin(xyz=(0.0, -0.003, 0.030)),
        material=head_black,
        name="cradle_bridge",
    )
    swivel.visual(
        Box((0.004, 0.020, 0.022)),
        origin=Origin(xyz=(-0.037, 0.006, 0.040)),
        material=head_black,
        name="arm_0",
    )
    swivel.visual(
        Box((0.004, 0.020, 0.022)),
        origin=Origin(xyz=(0.037, 0.006, 0.040)),
        material=head_black,
        name="arm_1",
    )
    model.articulation(
        "body_to_swivel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=swivel,
        origin=Origin(xyz=(0.0, 0.002, 0.118)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=2.5,
            lower=-1.65,
            upper=1.65,
        ),
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_build_head_shell(), "flash_head_shell"),
        origin=Origin(xyz=(0.0, 0.028, 0.013)),
        material=head_black,
        name="head_shell",
    )
    head.visual(
        Box((0.060, 0.003, 0.028)),
        origin=Origin(xyz=(0.0, 0.0505, 0.013)),
        material=diffuser,
        name="diffuser",
    )
    head.visual(
        Box((0.046, 0.018, 0.0015)),
        origin=Origin(xyz=(0.0, 0.026, 0.03125)),
        material=trim_gray,
        name="top_panel",
    )
    head.visual(
        Box((0.020, 0.004, 0.006)),
        origin=Origin(xyz=(0.0, 0.004, 0.001)),
        material=trim_gray,
        name="hinge_block",
    )
    head.visual(
        Box((0.002, 0.008, 0.008)),
        origin=Origin(xyz=(-0.034, 0.004, 0.002)),
        material=trim_gray,
        name="boss_0",
    )
    head.visual(
        Box((0.002, 0.008, 0.008)),
        origin=Origin(xyz=(0.034, 0.004, 0.002)),
        material=trim_gray,
        name="boss_1",
    )
    model.articulation(
        "swivel_to_head",
        ArticulationType.REVOLUTE,
        parent=swivel,
        child=head,
        origin=Origin(xyz=(0.0, 0.006, 0.040)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=2.0,
            lower=-math.radians(12.0),
            upper=math.radians(78.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
