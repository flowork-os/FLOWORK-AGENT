# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, binoculars, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: binoculars

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
def _tube_x(outer_radius: float, inner_radius: float, length: float):
    """Hollow cylindrical tube centered on the local X axis."""
    return (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length * 0.5, both=True)
    )
def _stabilizer_prism():
    """Small trapezoidal glass prism block, centered at the local origin."""
    return (
        cq.Workplane("YZ")
        .polyline(
            [
                (-0.011, -0.009),
                (0.011, -0.009),
                (0.008, 0.009),
                (-0.008, 0.009),
            ]
        )
        .close()
        .extrude(0.034, both=True)
    )
def _cylinder_x_origin(xyz):
    return Origin(xyz=xyz, rpy=(0.0, math.pi / 2.0, 0.0))
def _cylinder_y_origin(xyz):
    return Origin(xyz=xyz, rpy=(-math.pi / 2.0, 0.0, 0.0))
def _add_optical_barrel(
    part,
    *,
    center_y: float,
    mount_side: float,
    main_tube,
    objective_ring,
    eyepiece_ring,
    grip_band,
    rubber,
    black,
    glass,
    name_prefix: str,
) -> None:
    """Add one connected binocular barrel, with hollow front rings and lenses."""
    part.visual(
        main_tube,
        origin=Origin(xyz=(0.000, center_y, 0.0)),
        material=rubber,
        name=f"{name_prefix}_tube",
    )
    part.visual(
        objective_ring,
        origin=Origin(xyz=(0.090, center_y, 0.0)),
        material=black,
        name=f"{name_prefix}_objective_ring",
    )
    part.visual(
        eyepiece_ring,
        origin=Origin(xyz=(-0.092, center_y, 0.0)),
        material=black,
        name=f"{name_prefix}_eyepiece_ring",
    )

    for i, x in enumerate((-0.048, -0.030, -0.012)):
        part.visual(
            grip_band,
            origin=Origin(xyz=(x, center_y, 0.0)),
            material=black,
            name=f"{name_prefix}_grip_band_{i}",
        )

    part.visual(
        Cylinder(radius=0.027, length=0.004),
        origin=_cylinder_x_origin((0.099, center_y, 0.0)),
        material=glass,
        name=f"{name_prefix}_objective_lens",
    )
    part.visual(
        Cylinder(radius=0.016, length=0.004),
        origin=_cylinder_x_origin((-0.104, center_y, 0.0)),
        material=glass,
        name=f"{name_prefix}_eyepiece_lens",
    )

    # A molded lug on the inner side of the barrel gives the bridge/hinge a
    # real surface to carry, instead of leaving the tube visually floating.
    lug_center_y = center_y + mount_side * 0.036
    part.visual(
        Box((0.052, 0.012, 0.014)),
        origin=Origin(xyz=(0.000, lug_center_y, 0.0)),
        material=black,
        name=f"{name_prefix}_mount_lug",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="image_stabilized_binoculars")

    matte_black = model.material("matte_black", rgba=(0.015, 0.016, 0.017, 1.0))
    rubber = model.material("pebbled_rubber", rgba=(0.035, 0.036, 0.038, 1.0))
    graphite = model.material("graphite_bridge", rgba=(0.12, 0.13, 0.14, 1.0))
    gunmetal = model.material("gunmetal", rgba=(0.26, 0.27, 0.28, 1.0))
    coated_glass = model.material("green_coated_glass", rgba=(0.18, 0.44, 0.38, 0.55))
    prism_glass = model.material("stabilizer_glass", rgba=(0.42, 0.72, 0.92, 0.45))

    main_tube = mesh_from_cadquery(
        _tube_x(0.031, 0.021, 0.170),
        "barrel_main_tube",
        tolerance=0.0007,
        angular_tolerance=0.05,
    )
    objective_ring = mesh_from_cadquery(
        _tube_x(0.039, 0.026, 0.020),
        "objective_barrel_ring",
        tolerance=0.0007,
        angular_tolerance=0.05,
    )
    eyepiece_ring = mesh_from_cadquery(
        _tube_x(0.024, 0.015, 0.026),
        "eyepiece_ring",
        tolerance=0.0007,
        angular_tolerance=0.05,
    )
    grip_band = mesh_from_cadquery(
        _tube_x(0.033, 0.030, 0.004),
        "barrel_grip_band",
        tolerance=0.0007,
        angular_tolerance=0.05,
    )
    prism_mesh = mesh_from_cadquery(
        _stabilizer_prism(),
        "stabilizing_prism_block",
        tolerance=0.0005,
        angular_tolerance=0.05,
    )

    bridge = model.part("bridge")
    bridge.visual(
        Cylinder(radius=0.012, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=gunmetal,
        name="center_hinge_knuckle",
    )
    bridge.visual(
        Box((0.060, 0.020, 0.012)),
        origin=Origin(xyz=(0.0, -0.008, 0.0)),
        material=graphite,
        name="fixed_bridge_arm",
    )
    bridge.visual(
        Box((0.018, 0.012, 0.006)),
        origin=Origin(xyz=(0.0, -0.014, 0.0)),
        material=gunmetal,
        name="hinge_root_strap",
    )
    bridge.visual(
        Box((0.012, 0.008, 0.040)),
        origin=Origin(xyz=(0.0, -0.020, 0.025)),
        material=gunmetal,
        name="upper_bridge_post",
    )
    bridge.visual(
        Box((0.018, 0.030, 0.004)),
        origin=Origin(xyz=(0.0, -0.010, 0.045)),
        material=gunmetal,
        name="post_cap",
    )
    bridge.visual(
        Box((0.120, 0.012, 0.004)),
        origin=Origin(xyz=(0.000, 0.0, 0.045)),
        material=graphite,
        name="upper_bridge_plate",
    )
    bridge.visual(
        Box((0.052, 0.056, 0.006)),
        origin=Origin(xyz=(0.060, 0.0, 0.018)),
        material=graphite,
        name="prism_base",
    )
    bridge.visual(
        Box((0.016, 0.052, 0.004)),
        origin=Origin(xyz=(0.060, 0.0, 0.045)),
        material=gunmetal,
        name="prism_crossbar",
    )
    for suffix, y in (("neg", -0.023), ("pos", 0.023)):
        bridge.visual(
            Box((0.012, 0.006, 0.026)),
            origin=Origin(xyz=(0.060, y, 0.033)),
            material=gunmetal,
            name=f"prism_yoke_{suffix}",
        )
    bridge.visual(
        Box((0.025, 0.014, 0.026)),
        origin=Origin(xyz=(-0.012, 0.0, 0.057)),
        material=graphite,
        name="focus_web",
    )
    bridge.visual(
        Box((0.070, 0.018, 0.006)),
        origin=Origin(xyz=(-0.030, 0.0, 0.070)),
        material=graphite,
        name="focus_spine",
    )
    bridge.visual(
        Box((0.024, 0.050, 0.008)),
        origin=Origin(xyz=(-0.055, 0.0, 0.069)),
        material=graphite,
        name="focus_yoke_base",
    )
    for suffix, y in (("neg", -0.021), ("pos", 0.021)):
        bridge.visual(
            Box((0.012, 0.008, 0.036)),
            origin=Origin(xyz=(-0.055, y, 0.091)),
            material=gunmetal,
            name=f"focus_yoke_{suffix}",
        )

    fixed_barrel = model.part("fixed_barrel")
    _add_optical_barrel(
        fixed_barrel,
        center_y=0.0,
        mount_side=1.0,
        main_tube=main_tube,
        objective_ring=objective_ring,
        eyepiece_ring=eyepiece_ring,
        grip_band=grip_band,
        rubber=rubber,
        black=matte_black,
        glass=coated_glass,
        name_prefix="fixed",
    )

    swing_barrel = model.part("swing_barrel")
    swing_barrel.visual(
        Cylinder(radius=0.014, length=0.025),
        origin=Origin(xyz=(0.0, 0.0, 0.0295)),
        material=gunmetal,
        name="upper_hinge_knuckle",
    )
    swing_barrel.visual(
        Cylinder(radius=0.014, length=0.025),
        origin=Origin(xyz=(0.0, 0.0, -0.0295)),
        material=gunmetal,
        name="lower_hinge_knuckle",
    )
    swing_barrel.visual(
        Box((0.018, 0.004, 0.084)),
        origin=Origin(xyz=(0.0, 0.0155, 0.0)),
        material=gunmetal,
        name="hinge_strap",
    )
    swing_barrel.visual(
        Box((0.052, 0.034, 0.012)),
        origin=Origin(xyz=(0.0, 0.032, 0.0)),
        material=graphite,
        name="swing_bridge_arm",
    )
    _add_optical_barrel(
        swing_barrel,
        center_y=0.060,
        mount_side=-1.0,
        main_tube=main_tube,
        objective_ring=objective_ring,
        eyepiece_ring=eyepiece_ring,
        grip_band=grip_band,
        rubber=rubber,
        black=matte_black,
        glass=coated_glass,
        name_prefix="swing",
    )

    focus_wheel = model.part("focus_wheel")
    focus_wheel.visual(
        Cylinder(radius=0.018, length=0.026),
        origin=_cylinder_y_origin((0.0, 0.0, 0.0)),
        material=matte_black,
        name="wheel_body",
    )
    focus_wheel.visual(
        Cylinder(radius=0.004, length=0.034),
        origin=_cylinder_y_origin((0.0, 0.0, 0.0)),
        material=gunmetal,
        name="focus_axle",
    )
    for i in range(16):
        theta = 2.0 * math.pi * i / 16.0
        radial = 0.0195
        focus_wheel.visual(
            Box((0.0030, 0.030, 0.0050)),
            origin=Origin(
                xyz=(radial * math.cos(theta), 0.0, radial * math.sin(theta)),
                rpy=(0.0, -theta, 0.0),
            ),
            material=rubber,
            name=f"grip_rib_{i}",
        )

    prism_block = model.part("prism_block")
    prism_block.visual(
        prism_mesh,
        origin=Origin(),
        material=prism_glass,
        name="glass_prism",
    )
    prism_block.visual(
        Cylinder(radius=0.003, length=0.040),
        origin=_cylinder_y_origin((0.0, 0.0, 0.0)),
        material=gunmetal,
        name="gimbal_pin",
    )

    model.articulation(
        "bridge_to_fixed_barrel",
        ArticulationType.FIXED,
        parent=bridge,
        child=fixed_barrel,
        origin=Origin(xyz=(0.0, -0.060, 0.0)),
    )
    model.articulation(
        "ipd_hinge",
        ArticulationType.REVOLUTE,
        parent=bridge,
        child=swing_barrel,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=0.6, lower=0.0, upper=0.26),
    )
    model.articulation(
        "focus_spin",
        ArticulationType.CONTINUOUS,
        parent=bridge,
        child=focus_wheel,
        origin=Origin(xyz=(-0.055, 0.0, 0.091)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.3, velocity=6.0),
    )
    model.articulation(
        "prism_stabilizer",
        ArticulationType.REVOLUTE,
        parent=bridge,
        child=prism_block,
        origin=Origin(xyz=(0.060, 0.0, 0.033)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.1, velocity=1.0, lower=-0.08, upper=0.08),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
