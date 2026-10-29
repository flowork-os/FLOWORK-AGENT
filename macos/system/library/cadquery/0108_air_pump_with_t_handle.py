# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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
def _rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    """Centered rounded rectangular solid used for stamped plastic plates."""
    return (
        cq.Workplane("XY")
        .box(length, width, height)
        .edges("|Z")
        .fillet(min(radius, length * 0.45, width * 0.45, height * 0.45))
    )
def _annular_tube(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    """Open cylindrical shell/collar with a real central bore."""
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(height)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_camping_pump")

    dark_plastic = model.material("matte_black_plastic", rgba=(0.02, 0.025, 0.025, 1.0))
    barrel_blue = model.material("anodized_blue_barrel", rgba=(0.05, 0.28, 0.62, 1.0))
    rubber = model.material("soft_black_rubber", rgba=(0.005, 0.005, 0.006, 1.0))
    metal = model.material("brushed_steel", rgba=(0.72, 0.74, 0.75, 1.0))

    base_barrel = model.part("base_barrel")
    base_barrel.visual(
        mesh_from_cadquery(_rounded_box(0.180, 0.070, 0.018, 0.014), "base_plate"),
        origin=Origin(xyz=(0.0, 0.0, 0.009)),
        material=dark_plastic,
        name="base_plate",
    )
    base_barrel.visual(
        Cylinder(radius=0.040, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.024)),
        material=dark_plastic,
        name="barrel_socket",
    )
    base_barrel.visual(
        mesh_from_cadquery(_annular_tube(0.033, 0.026, 0.240), "barrel_shell"),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=barrel_blue,
        name="barrel_shell",
    )
    base_barrel.visual(
        mesh_from_cadquery(_annular_tube(0.038, 0.014, 0.016), "top_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.258)),
        material=dark_plastic,
        name="top_collar",
    )
    base_barrel.visual(
        mesh_from_cadquery(_annular_tube(0.014, 0.006, 0.012), "guide_bushing"),
        origin=Origin(xyz=(0.0, 0.0, 0.260)),
        material=metal,
        name="guide_bushing",
    )

    # Four fixed hinge cheeks make two side clevises for the folding feet.
    for lug_name, x, y in (
        ("side_0_hinge_lug_0", -0.048, 0.041),
        ("side_0_hinge_lug_1", 0.048, 0.041),
        ("side_1_hinge_lug_0", -0.048, -0.041),
        ("side_1_hinge_lug_1", 0.048, -0.041),
    ):
        base_barrel.visual(
            Box((0.014, 0.012, 0.026)),
            origin=Origin(xyz=(x, y, 0.031)),
            material=dark_plastic,
            name=lug_name,
        )
    for cap_name, x, y in (
        ("side_0_hinge_cap_0", -0.059, 0.041),
        ("side_0_hinge_cap_1", 0.059, 0.041),
        ("side_1_hinge_cap_0", -0.059, -0.041),
        ("side_1_hinge_cap_1", 0.059, -0.041),
    ):
        base_barrel.visual(
            Cylinder(radius=0.004, length=0.008),
            origin=Origin(xyz=(x, y, 0.031), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal,
            name=cap_name,
        )

    handle_rod = model.part("handle_rod")
    handle_rod.visual(
        Cylinder(radius=0.006, length=0.380),
        origin=Origin(xyz=(0.0, 0.0, 0.035)),
        material=metal,
        name="rod",
    )
    handle_rod.visual(
        Cylinder(radius=0.014, length=0.170),
        origin=Origin(xyz=(0.0, 0.0, 0.225), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="t_grip",
    )
    for x in (-0.085, 0.085):
        handle_rod.visual(
            Sphere(radius=0.0145),
            origin=Origin(xyz=(x, 0.0, 0.225)),
            material=rubber,
            name=f"grip_end_{0 if x < 0 else 1}",
        )
    handle_rod.visual(
        Box((0.030, 0.024, 0.024)),
        origin=Origin(xyz=(0.0, 0.0, 0.205)),
        material=rubber,
        name="grip_hub",
    )

    foot_plate_mesh = mesh_from_cadquery(_rounded_box(0.135, 0.085, 0.010, 0.012), "foot_plate")
    for foot_name in ("foot_0", "foot_1"):
        foot = model.part(foot_name)
        foot.visual(
            Cylinder(radius=0.006, length=0.082),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=metal,
            name="hinge_barrel",
        )
        foot.visual(
            Box((0.030, 0.045, 0.018)),
            origin=Origin(xyz=(0.0, 0.016, -0.014)),
            material=dark_plastic,
            name="hinge_web",
        )
        foot.visual(
            foot_plate_mesh,
            origin=Origin(xyz=(0.0, 0.062, -0.025)),
            material=dark_plastic,
            name="foot_plate",
        )

    model.articulation(
        "barrel_to_handle",
        ArticulationType.PRISMATIC,
        parent=base_barrel,
        child=handle_rod,
        origin=Origin(xyz=(0.0, 0.0, 0.274)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=55.0, velocity=0.30, lower=0.0, upper=0.100),
    )
    model.articulation(
        "base_to_foot_0",
        ArticulationType.REVOLUTE,
        parent=base_barrel,
        child="foot_0",
        origin=Origin(xyz=(0.0, 0.047, 0.031)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=0.0, upper=1.55),
    )
    model.articulation(
        "base_to_foot_1",
        ArticulationType.REVOLUTE,
        parent=base_barrel,
        child="foot_1",
        origin=Origin(xyz=(0.0, -0.047, 0.031), rpy=(0.0, 0.0, math.pi)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=0.0, upper=1.55),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
