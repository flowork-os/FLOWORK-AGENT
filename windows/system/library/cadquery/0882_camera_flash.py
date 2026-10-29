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
def _rounded_box(size: tuple[float, float, float], radius: float) -> object:
    """CadQuery rounded rectangular housing, authored in meters."""

    return cq.Workplane("XY").box(*size).edges().fillet(radius)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="professional_camera_flash")

    black = model.material("satin_black_polymer", rgba=(0.015, 0.014, 0.013, 1.0))
    rubber = model.material("matte_rubber_black", rgba=(0.004, 0.004, 0.004, 1.0))
    metal = model.material("dark_anodized_metal", rgba=(0.22, 0.22, 0.22, 1.0))
    glass = model.material("smoked_lcd_glass", rgba=(0.03, 0.10, 0.13, 0.92))
    lens = model.material("milky_flash_lens", rgba=(0.88, 0.86, 0.74, 0.78))
    white = model.material("white_legends", rgba=(0.86, 0.86, 0.82, 1.0))

    body = model.part("body")

    # Camera hot-shoe sized lower mount: broad enough for a DSLR/mirrorless shoe,
    # with visible metal rails and a locking collar above it.
    body.visual(
        Box((0.066, 0.064, 0.008)),
        origin=Origin(xyz=(0.000, 0.000, 0.004)),
        material=metal,
        name="mounting_foot",
    )
    body.visual(
        Box((0.060, 0.010, 0.006)),
        origin=Origin(xyz=(0.000, 0.031, 0.011)),
        material=metal,
        name="shoe_rail_0",
    )
    body.visual(
        Box((0.060, 0.010, 0.006)),
        origin=Origin(xyz=(0.000, -0.031, 0.011)),
        material=metal,
        name="shoe_rail_1",
    )
    body.visual(
        Box((0.074, 0.080, 0.018)),
        origin=Origin(xyz=(0.000, 0.000, 0.017)),
        material=black,
        name="foot_shoulder",
    )
    body.visual(
        Cylinder(radius=0.026, length=0.018),
        origin=Origin(xyz=(0.000, 0.000, 0.033)),
        material=black,
        name="neck_post",
    )
    body.visual(
        Cylinder(radius=0.039, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.033)),
        material=rubber,
        name="locking_collar",
    )

    body.visual(
        mesh_from_cadquery(_rounded_box((0.058, 0.074, 0.089), 0.007), "control_body_shell"),
        origin=Origin(xyz=(-0.010, 0.000, 0.0805)),
        material=black,
        name="control_body_shell",
    )
    body.visual(
        Box((0.003, 0.052, 0.028)),
        origin=Origin(xyz=(-0.0402, 0.000, 0.101)),
        material=glass,
        name="rear_lcd",
    )
    body.visual(
        Box((0.0015, 0.044, 0.0020)),
        origin=Origin(xyz=(-0.0420, 0.000, 0.113)),
        material=white,
        name="lcd_top_legend",
    )
    body.visual(
        Cylinder(radius=0.035, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.130)),
        material=black,
        name="swivel_socket",
    )

    yoke = model.part("swivel_yoke")
    yoke.visual(
        Cylinder(radius=0.037, length=0.010),
        origin=Origin(xyz=(0.000, 0.000, 0.005)),
        material=black,
        name="turntable_disk",
    )
    yoke.visual(
        Box((0.060, 0.112, 0.012)),
        origin=Origin(xyz=(0.025, 0.000, 0.012)),
        material=black,
        name="yoke_bridge",
    )
    yoke.visual(
        Box((0.028, 0.010, 0.046)),
        origin=Origin(xyz=(0.026, 0.048, 0.034)),
        material=black,
        name="yoke_arm_0",
    )
    yoke.visual(
        Box((0.028, 0.010, 0.046)),
        origin=Origin(xyz=(0.026, -0.048, 0.034)),
        material=black,
        name="yoke_arm_1",
    )
    yoke.visual(
        Cylinder(radius=0.012, length=0.010),
        origin=Origin(xyz=(0.026, 0.043, 0.037), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="pivot_bushing_0",
    )
    yoke.visual(
        Cylinder(radius=0.012, length=0.010),
        origin=Origin(xyz=(0.026, -0.043, 0.037), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="pivot_bushing_1",
    )

    flash_head = model.part("flash_head")
    flash_head.visual(
        mesh_from_cadquery(_rounded_box((0.112, 0.075, 0.050), 0.006), "flash_head_shell"),
        origin=Origin(xyz=(0.060, 0.000, 0.002)),
        material=black,
        name="head_shell",
    )
    flash_head.visual(
        Box((0.006, 0.061, 0.039)),
        origin=Origin(xyz=(0.119, 0.000, 0.002)),
        material=lens,
        name="flash_lens",
    )
    flash_head.visual(
        Box((0.002, 0.050, 0.0025)),
        origin=Origin(xyz=(0.123, 0.000, 0.015)),
        material=white,
        name="lens_diffuser_line_0",
    )
    flash_head.visual(
        Box((0.002, 0.050, 0.0025)),
        origin=Origin(xyz=(0.123, 0.000, -0.009)),
        material=white,
        name="lens_diffuser_line_1",
    )
    flash_head.visual(
        Cylinder(radius=0.011, length=0.006),
        origin=Origin(xyz=(0.000, 0.0395, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="head_pivot_0",
    )
    flash_head.visual(
        Cylinder(radius=0.011, length=0.006),
        origin=Origin(xyz=(0.000, -0.0395, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="head_pivot_1",
    )

    dial = model.part("rear_dial")
    dial.visual(
        Cylinder(radius=0.013, length=0.008),
        origin=Origin(xyz=(-0.004, 0.000, 0.000), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="dial_cap",
    )
    dial.visual(
        Box((0.0014, 0.003, 0.010)),
        origin=Origin(xyz=(-0.0084, 0.000, 0.007)),
        material=white,
        name="dial_index",
    )

    for index, (y, z) in enumerate(
        ((-0.018, 0.074), (0.018, 0.074), (-0.018, 0.058), (0.018, 0.058))
    ):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.004, 0.012, 0.007)),
            origin=Origin(xyz=(-0.002, 0.000, 0.000)),
            material=rubber,
            name="button_cap",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(-0.0390, y, z)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=1.0, velocity=0.06, lower=0.0, upper=0.003),
        )

    model.articulation(
        "body_to_rear_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(-0.0390, 0.000, 0.045)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.4, velocity=8.0),
    )
    model.articulation(
        "body_to_swivel_yoke",
        ArticulationType.REVOLUTE,
        parent=body,
        child=yoke,
        origin=Origin(xyz=(0.000, 0.000, 0.135)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=2.0, lower=-2.7, upper=2.7),
    )
    model.articulation(
        "yoke_to_flash_head",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=flash_head,
        origin=Origin(xyz=(0.026, 0.000, 0.037)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=2.0, lower=-0.18, upper=1.55),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
