# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_three_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_three_independent_rotary_branches

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
def _annular_collar(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """Centered hollow cylindrical bearing/collar, with its bore along local Z."""
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, -0.5 * length))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="three_branch_inspection_fixture_head")

    cast_iron = model.material("dark_cast_iron", rgba=(0.18, 0.19, 0.20, 1.0))
    parkerized = model.material("parkerized_steel", rgba=(0.06, 0.065, 0.07, 1.0))
    blue_steel = model.material("blue_anodized_arms", rgba=(0.05, 0.17, 0.33, 1.0))
    satin_steel = model.material("satin_steel_faces", rgba=(0.62, 0.64, 0.62, 1.0))
    rubber = model.material("black_rubber_inserts", rgba=(0.01, 0.01, 0.012, 1.0))
    brass = model.material("brass_index_marks", rgba=(0.83, 0.64, 0.25, 1.0))

    spine = model.part("spine")
    spine.visual(
        Box((0.080, 0.070, 0.450)),
        origin=Origin(xyz=(0.0, 0.0, 0.260)),
        material=cast_iron,
        name="rectangular_spine",
    )
    spine.visual(
        Box((0.096, 0.086, 0.018)),
        origin=Origin(xyz=(0.0, 0.0, 0.026)),
        material=cast_iron,
        name="bottom_spine_cap",
    )
    spine.visual(
        Box((0.096, 0.086, 0.016)),
        origin=Origin(xyz=(0.0, 0.0, 0.493)),
        material=cast_iron,
        name="top_spine_cap",
    )

    # Low transverse trunnion housing: two cheek plates on a separate side collar.
    spine.visual(
        Box((0.045, 0.145, 0.070)),
        origin=Origin(xyz=(0.055, 0.0, 0.155)),
        material=cast_iron,
        name="low_trunnion_neck",
    )
    for suffix, y in (("0", 0.057), ("1", -0.057)):
        spine.visual(
            Box((0.075, 0.025, 0.085)),
            origin=Origin(xyz=(0.108, y, 0.155)),
            material=cast_iron,
            name=f"low_trunnion_cheek_{suffix}",
        )
        spine.visual(
            Cylinder(radius=0.022, length=0.006),
            origin=Origin(xyz=(0.112, y + (0.015 if y > 0 else -0.015), 0.155), rpy=(math.pi / 2, 0.0, 0.0)),
            material=parkerized,
            name=f"low_bore_boss_{suffix}",
        )

    # Forward vertical swivel collar: a real annular bearing on its own nose.
    spine.visual(
        Box((0.090, 0.040, 0.035)),
        origin=Origin(xyz=(0.0, -0.052, 0.285)),
        material=cast_iron,
        name="forward_collar_neck",
    )
    spine.visual(
        mesh_from_cadquery(_annular_collar(0.038, 0.018, 0.032), "forward_vertical_collar"),
        origin=Origin(xyz=(0.0, -0.105, 0.285)),
        material=cast_iron,
        name="forward_vertical_collar",
    )

    # High longitudinal bearing: a separate horizontal collar, not a shared hub.
    spine.visual(
        Box((0.035, 0.080, 0.070)),
        origin=Origin(xyz=(0.054, 0.0, 0.415)),
        material=cast_iron,
        name="high_collar_neck",
    )
    spine.visual(
        mesh_from_cadquery(_annular_collar(0.035, 0.017, 0.052), "high_longitudinal_collar"),
        origin=Origin(xyz=(0.083, 0.0, 0.415), rpy=(0.0, math.pi / 2, 0.0)),
        material=cast_iron,
        name="high_longitudinal_collar",
    )

    low_arm = model.part("low_arm")
    low_arm.visual(
        Cylinder(radius=0.017, length=0.089),
        origin=Origin(rpy=(math.pi / 2, 0.0, 0.0)),
        material=parkerized,
        name="low_pivot_barrel",
    )
    low_arm.visual(
        Box((0.295, 0.032, 0.024)),
        origin=Origin(xyz=(0.1595, 0.0, 0.0)),
        material=blue_steel,
        name="low_side_arm_tube",
    )
    low_arm.visual(
        Box((0.030, 0.115, 0.065)),
        origin=Origin(xyz=(0.322, 0.0, 0.0)),
        material=satin_steel,
        name="low_slotted_pad",
    )
    low_arm.visual(
        Box((0.008, 0.088, 0.014)),
        origin=Origin(xyz=(0.341, 0.0, 0.0)),
        material=rubber,
        name="low_slot_strip",
    )
    for suffix, y in (("0", 0.035), ("1", -0.035)):
        low_arm.visual(
            Cylinder(radius=0.009, length=0.004),
            origin=Origin(xyz=(0.347, y, 0.0), rpy=(0.0, math.pi / 2, 0.0)),
            material=rubber,
            name=f"low_slot_end_{suffix}",
        )

    forward_arm = model.part("forward_arm")
    forward_arm.visual(
        Cylinder(radius=0.0125, length=0.060),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=parkerized,
        name="forward_swivel_pin",
    )
    forward_arm.visual(
        Cylinder(radius=0.025, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.022)),
        material=blue_steel,
        name="forward_turntable_cap",
    )
    forward_arm.visual(
        Box((0.035, 0.276, 0.025)),
        origin=Origin(xyz=(0.0, -0.158, 0.040)),
        material=blue_steel,
        name="forward_arm_tube",
    )
    forward_arm.visual(
        Cylinder(radius=0.055, length=0.020),
        origin=Origin(xyz=(0.0, -0.306, 0.040), rpy=(math.pi / 2, 0.0, 0.0)),
        material=satin_steel,
        name="forward_round_pad",
    )
    for i, (x, z) in enumerate(((0.0, 0.076), (0.030, 0.022), (-0.030, 0.022))):
        forward_arm.visual(
            Cylinder(radius=0.006, length=0.004),
            origin=Origin(xyz=(x, -0.318, z), rpy=(math.pi / 2, 0.0, 0.0)),
            material=rubber,
            name=f"forward_pad_bolt_{i}",
        )

    high_arm = model.part("high_arm")
    high_arm.visual(
        Cylinder(radius=0.013, length=0.090),
        origin=Origin(xyz=(0.035, 0.0, 0.0), rpy=(0.0, math.pi / 2, 0.0)),
        material=parkerized,
        name="high_shaft",
    )
    high_arm.visual(
        Cylinder(radius=0.026, length=0.008),
        origin=Origin(xyz=(0.030, 0.0, 0.0), rpy=(0.0, math.pi / 2, 0.0)),
        material=parkerized,
        name="high_bearing_shoulder",
    )
    high_arm.visual(
        Box((0.260, 0.026, 0.034)),
        origin=Origin(xyz=(0.195, 0.0, 0.0)),
        material=blue_steel,
        name="high_arm_tube",
    )
    high_arm.visual(
        Box((0.060, 0.018, 0.012)),
        origin=Origin(xyz=(0.275, 0.0, 0.022)),
        material=brass,
        name="high_orientation_mark",
    )
    high_arm.visual(
        Box((0.038, 0.110, 0.075)),
        origin=Origin(xyz=(0.340, 0.0, 0.0)),
        material=satin_steel,
        name="high_clamp_pad",
    )
    for suffix, y in (("0", 0.030), ("1", -0.030)):
        high_arm.visual(
            Box((0.008, 0.014, 0.060)),
            origin=Origin(xyz=(0.363, y, 0.0)),
            material=rubber,
            name=f"high_clamp_jaw_{suffix}",
        )

    model.articulation(
        "spine_to_low_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=low_arm,
        origin=Origin(xyz=(0.112, 0.0, 0.155)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.8, lower=-0.70, upper=0.90),
    )
    model.articulation(
        "spine_to_forward_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=forward_arm,
        origin=Origin(xyz=(0.0, -0.105, 0.285)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=14.0, velocity=2.2, lower=-1.25, upper=1.25),
    )
    model.articulation(
        "spine_to_high_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=high_arm,
        origin=Origin(xyz=(0.083, 0.0, 0.415)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=2.0, lower=-1.60, upper=1.60),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
