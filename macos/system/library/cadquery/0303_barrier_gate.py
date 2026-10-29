# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, barrier_gate, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: barrier_gate

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="barrier_gate")

    # Colors
    mat_housing = Material(name="mat_housing", color=(0.85, 0.45, 0.1)) # Orange-ish yellow
    mat_dark = Material(name="mat_dark", color=(0.2, 0.2, 0.2))
    mat_metal = Material(name="mat_metal", color=(0.7, 0.7, 0.7))
    mat_boom = Material(name="mat_boom", color=(0.95, 0.95, 0.95))
    mat_stripe = Material(name="mat_stripe", color=(0.85, 0.15, 0.15))
    mat_green = Material(name="mat_green", color=(0.1, 0.8, 0.1))
    mat_red = Material(name="mat_red", color=(0.8, 0.1, 0.1))
    mat_light = Material(name="mat_light", color=(1.0, 0.8, 0.1))

    # 1. Housing (Base)
    housing = model.part("housing")
    
    # Base plate
    housing.visual(
        Box((0.45, 0.45, 0.05)),
        origin=Origin(xyz=(0.0, 0.0, 0.025)),
        name="base_plate",
        material=mat_dark,
    )
    
    # Main body
    housing_shape = (
        cq.Workplane("XY")
        .box(0.35, 0.35, 0.95, centered=(True, True, False))
        .edges("|Z").fillet(0.05)
    )
    housing.visual(
        mesh_from_cadquery(housing_shape, "housing_body"),
        origin=Origin(xyz=(0.0, 0.0, 0.05)),
        name="main_body",
        material=mat_housing,
    )
    
    # Lid
    lid_shape = (
        cq.Workplane("XY")
        .rect(0.38, 0.38)
        .extrude(0.05)
        .edges(">Z").chamfer(0.02)
    )
    housing.visual(
        mesh_from_cadquery(lid_shape, "housing_lid"),
        origin=Origin(xyz=(0.0, 0.0, 1.0)),
        name="lid",
        material=mat_dark,
    )
    
    # Pivot shaft (extends from X=0.175 to X=0.25)
    housing.visual(
        Cylinder(radius=0.06, length=0.075),
        origin=Origin(xyz=(0.2125, 0.0, 0.85), rpy=(0.0, math.pi / 2, 0.0)),
        name="pivot_shaft",
        material=mat_metal,
    )
    
    # Control box on the -Y face
    housing.visual(
        Box((0.2, 0.05, 0.3)),
        origin=Origin(xyz=(0.0, -0.2, 0.6)),
        name="control_box",
        material=mat_metal,
    )
    
    # Buttons on the control box
    housing.visual(
        Cylinder(radius=0.02, length=0.02),
        origin=Origin(xyz=(0.05, -0.235, 0.65), rpy=(math.pi / 2, 0.0, 0.0)),
        name="btn_green",
        material=mat_green,
    )
    housing.visual(
        Cylinder(radius=0.02, length=0.02),
        origin=Origin(xyz=(-0.05, -0.235, 0.65), rpy=(math.pi / 2, 0.0, 0.0)),
        name="btn_red",
        material=mat_red,
    )
    
    # Vent grille on the +Y face
    housing.visual(
        Box((0.2, 0.02, 0.2)),
        origin=Origin(xyz=(0.0, 0.185, 0.3)),
        name="vent_grille",
        material=mat_dark,
    )
    
    # Warning light base on top of the lid
    housing.visual(
        Cylinder(radius=0.08, length=0.02),
        origin=Origin(xyz=(0.0, 0.0, 1.06)),
        name="light_base",
        material=mat_dark,
    )
    
    # Warning light dome
    housing.visual(
        Sphere(radius=0.06),
        origin=Origin(xyz=(0.0, 0.0, 1.09)),
        name="warning_light",
        material=mat_light,
    )

    # 2. Arm
    arm = model.part("arm")
    
    # Arm mount (clamp around the pivot axis)
    arm.visual(
        Cylinder(radius=0.1, length=0.1),
        origin=Origin(xyz=(0.05, 0.0, 0.0), rpy=(0.0, math.pi / 2, 0.0)),
        name="arm_mount",
        material=mat_dark,
    )
    
    # Boom (extends from Y=0.0 to Y=3.5)
    boom_shape = (
        cq.Workplane("XZ")
        .polygon(8, 0.1)
        .extrude(-3.5) # Y goes from 0 to 3.5
    )
    arm.visual(
        mesh_from_cadquery(boom_shape, "boom_tube"),
        origin=Origin(xyz=(0.05, 0.0, 0.0)),
        name="boom",
        material=mat_boom,
    )
    
    # Red stripes on the boom
    stripe_shape = (
        cq.Workplane("XZ")
        .polygon(8, 0.105)
        .extrude(-0.2)
    )
    for i in range(1, 7):
        y_pos = i * 0.5
        arm.visual(
            mesh_from_cadquery(stripe_shape, f"stripe_{i}"),
            origin=Origin(xyz=(0.05, y_pos, 0.0)),
            name=f"stripe_{i}",
            material=mat_stripe,
        )
        
    # Counterweight (extends from Y=0.0 to Y=-0.4)
    arm.visual(
        Box((0.08, 0.4, 0.15)),
        origin=Origin(xyz=(0.05, -0.2, 0.0)),
        name="counterweight",
        material=mat_dark,
    )

    # Articulation
    model.articulation(
        "housing_to_arm",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=arm,
        origin=Origin(xyz=(0.25, 0.0, 0.85)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=100.0, velocity=1.0, lower=0.0, upper=math.pi / 2),
    )

    # 3. Catch Post
    catch_post = model.part("catch_post")
    
    catch_post.visual(
        Box((0.2, 0.2, 0.05)),
        origin=Origin(xyz=(0.3, 3.4, 0.025)),
        name="post_base",
        material=mat_dark,
    )
    
    catch_post.visual(
        Box((0.08, 0.08, 0.73)),
        origin=Origin(xyz=(0.3, 3.4, 0.415)),
        name="post_body",
        material=mat_housing,
    )
    
    catch_post.visual(
        Box((0.16, 0.08, 0.02)),
        origin=Origin(xyz=(0.3, 3.4, 0.79)),
        name="post_bracket_base",
        material=mat_metal,
    )
    
    catch_post.visual(
        Box((0.02, 0.08, 0.05)),
        origin=Origin(xyz=(0.23, 3.4, 0.825)),
        name="post_fork_left",
        material=mat_metal,
    )
    
    catch_post.visual(
        Box((0.02, 0.08, 0.05)),
        origin=Origin(xyz=(0.37, 3.4, 0.825)),
        name="post_fork_right",
        material=mat_metal,
    )

    model.articulation(
        "housing_to_catch_post",
        ArticulationType.FIXED,
        parent=housing,
        child=catch_post,
        origin=Origin(),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
