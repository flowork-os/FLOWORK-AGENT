# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_two_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_two_independent_rotary_branches

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
def _branch_body(name: str, *, length: float, side: float) -> object:
    """One connected outrigger branch: hollow pivot hub plus a radial arm."""
    hub_outer = 0.047
    hub_inner = 0.021
    thickness = 0.045
    arm_width = 0.038
    arm_thickness = 0.026
    overlap = 0.008

    hub = (
        cq.Workplane("XY")
        .circle(hub_outer)
        .circle(hub_inner)
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
    arm = cq.Workplane("XY").box(length, arm_width, arm_thickness).translate(
        (side * (hub_outer + length / 2.0 - overlap), 0.0, 0.0)
    )
    rounded_tip = (
        cq.Workplane("XY")
        .circle(arm_width * 0.58)
        .extrude(arm_thickness)
        .translate((side * (hub_outer + length - overlap), 0.0, -arm_thickness / 2.0))
    )
    top_rib = cq.Workplane("XY").box(length * 0.62, arm_width * 0.28, 0.010).translate(
        (side * (hub_outer + length * 0.45), 0.0, arm_thickness / 2.0 + 0.005)
    )
    return hub.union(arm).union(rounded_tip).union(top_rib)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mast_outrigger_rotary_head")

    cast_iron = Material("dark_cast_iron", rgba=(0.05, 0.055, 0.06, 1.0))
    brushed_steel = Material("brushed_steel", rgba=(0.62, 0.64, 0.62, 1.0))
    collar_paint = Material("charcoal_collars", rgba=(0.13, 0.14, 0.15, 1.0))
    bolt_metal = Material("blackened_bolts", rgba=(0.02, 0.02, 0.018, 1.0))
    long_paint = Material("safety_yellow_branch", rgba=(0.95, 0.68, 0.08, 1.0))
    short_paint = Material("blue_branch", rgba=(0.08, 0.24, 0.74, 1.0))

    stand = model.part("stand")
    stand.visual(
        Cylinder(radius=0.18, length=0.060),
        origin=Origin(xyz=(0.0, 0.0, 0.030)),
        material=cast_iron,
        name="heavy_foot",
    )
    stand.visual(
        Cylinder(radius=0.060, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 0.085)),
        material=cast_iron,
        name="foot_boss",
    )
    stand.visual(
        Cylinder(radius=0.025, length=0.560),
        origin=Origin(xyz=(0.0, 0.0, 0.340)),
        material=brushed_steel,
        name="short_mast",
    )

    # Lower collar block and bearing support for the longer branch.
    lower_pivot = (0.115, 0.0, 0.350)
    upper_pivot = (-0.105, 0.0, 0.500)
    branch_h = 0.045
    washer_h = 0.012
    bearing_gap = 0.0

    def add_collar(level: str, pivot: tuple[float, float, float], connector_x: float) -> None:
        px, py, pz = pivot
        washer_top = pz - branch_h / 2.0 - bearing_gap
        washer_center_z = washer_top - washer_h / 2.0
        connector_top = washer_center_z - washer_h / 2.0
        connector_center_z = connector_top - 0.020

        stand.visual(
            Box((0.086, 0.076, 0.068)),
            origin=Origin(xyz=(0.0, 0.0, connector_center_z)),
            material=collar_paint,
            name=f"{level}_collar_block",
        )
        stand.visual(
            Box((abs(px) + 0.060, 0.054, 0.040)),
            origin=Origin(xyz=(connector_x, py, connector_center_z)),
            material=collar_paint,
            name=f"{level}_support_lug",
        )
        if level == "lower":
            stand.visual(
                Cylinder(radius=0.052, length=washer_h),
                origin=Origin(xyz=(px, py, washer_center_z)),
                material=brushed_steel,
                name="lower_washer",
            )
        else:
            stand.visual(
                Cylinder(radius=0.052, length=washer_h),
                origin=Origin(xyz=(px, py, washer_center_z)),
                material=brushed_steel,
                name="upper_washer",
            )
        stand.visual(
            Cylinder(radius=0.014, length=branch_h + washer_h + 0.030),
            origin=Origin(xyz=(px, py, pz + 0.002)),
            material=brushed_steel,
            name=f"{level}_pivot_pin",
        )
        for y in (-0.043, 0.043):
            stand.visual(
                Cylinder(radius=0.009, length=0.010),
                origin=Origin(
                    xyz=(0.0, y, connector_center_z + 0.012),
                    rpy=(pi / 2.0, 0.0, 0.0),
                ),
                material=bolt_metal,
                name=f"{level}_clamp_bolt_{'front' if y < 0 else 'rear'}",
            )

    add_collar("lower", lower_pivot, connector_x=0.050)
    add_collar("upper", upper_pivot, connector_x=-0.045)

    long_branch = model.part("long_branch")
    long_branch.visual(
        mesh_from_cadquery(_branch_body("long_branch_body", length=0.410, side=1.0), "long_branch_body"),
        material=long_paint,
        name="long_branch_body",
    )

    short_branch = model.part("short_branch")
    short_branch.visual(
        mesh_from_cadquery(
            _branch_body("short_branch_body", length=0.250, side=-1.0),
            "short_branch_body",
        ),
        material=short_paint,
        name="short_branch_body",
    )

    model.articulation(
        "lower_branch_axis",
        ArticulationType.REVOLUTE,
        parent=stand,
        child=long_branch,
        origin=Origin(xyz=lower_pivot),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=-1.35, upper=1.35),
    )
    model.articulation(
        "upper_branch_axis",
        ArticulationType.REVOLUTE,
        parent=stand,
        child=short_branch,
        origin=Origin(xyz=upper_pivot),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=1.8, lower=-1.45, upper=1.45),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
