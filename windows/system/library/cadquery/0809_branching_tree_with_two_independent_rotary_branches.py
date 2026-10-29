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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
BASE_RADIUS = 0.10
BASE_THICKNESS = 0.018
PEDESTAL_RADIUS = 0.055
PEDESTAL_HEIGHT = 0.040
MAST_RADIUS = 0.022
MAST_HEIGHT = 0.720
TOP_CAP_RADIUS = 0.030
TOP_CAP_HEIGHT = 0.014
HUB_COLLAR_X = 0.074
HUB_COLLAR_Y = 0.070
HUB_COLLAR_Z = 0.068
HUB_BRIDGE_X = 0.040
HUB_BRIDGE_Y = 0.042
HUB_BRIDGE_Z = 0.052
EAR_X = 0.024
EAR_Y = 0.010
EAR_Z = 0.050
ARM_BARREL_RADIUS = 0.015
ARM_BARREL_LENGTH = 0.036
ARM_WEB_THICKNESS = 0.014
ARM_TIP_RADIUS = 0.012
ARM_TIP_THICKNESS = 0.012
ARM_TIP_X = 0.165
EAR_OFFSET_Y = ARM_BARREL_LENGTH / 2.0 + EAR_Y / 2.0
UPPER_HUB_Z = 0.515
LOWER_HUB_Z = 0.315
PIVOT_OFFSET_X = MAST_RADIUS + HUB_BRIDGE_X + EAR_X / 2.0 + 0.008
def _make_base_and_mast() -> cq.Workplane:
    base = cq.Workplane("XY").circle(BASE_RADIUS).extrude(BASE_THICKNESS)
    pedestal = cq.Workplane("XY").circle(PEDESTAL_RADIUS).extrude(PEDESTAL_HEIGHT)
    mast = cq.Workplane("XY").circle(MAST_RADIUS).extrude(BASE_THICKNESS + MAST_HEIGHT)
    top_cap = (
        cq.Workplane("XY")
        .circle(TOP_CAP_RADIUS)
        .extrude(TOP_CAP_HEIGHT)
        .translate((0.0, 0.0, BASE_THICKNESS + MAST_HEIGHT - TOP_CAP_HEIGHT))
    )
    return base.union(pedestal).union(mast).union(top_cap)
def _make_hub_block(side: int) -> cq.Workplane:
    collar = cq.Workplane("XY").box(HUB_COLLAR_X, HUB_COLLAR_Y, HUB_COLLAR_Z)
    mast_bore = (
        cq.Workplane("XY")
        .circle(MAST_RADIUS)
        .extrude(HUB_COLLAR_Z / 2.0 + 0.01, both=True)
    )
    collar = collar.cut(mast_bore)

    bridge_center_x = side * (MAST_RADIUS + HUB_BRIDGE_X / 2.0)
    bridge = (
        cq.Workplane("XY")
        .box(HUB_BRIDGE_X, HUB_BRIDGE_Y, HUB_BRIDGE_Z)
        .translate((bridge_center_x, 0.0, 0.0))
    )

    pivot_center_x = side * PIVOT_OFFSET_X
    bridge_outer_x = abs(bridge_center_x) + HUB_BRIDGE_X / 2.0
    ear_inner_x = abs(pivot_center_x) - EAR_X / 2.0
    rib_length = max(0.002, ear_inner_x - bridge_outer_x)
    rib_center_x = side * (bridge_outer_x + rib_length / 2.0)
    upper_rib = (
        cq.Workplane("XY")
        .box(rib_length, EAR_Y, EAR_Z * 0.72)
        .translate((rib_center_x, EAR_OFFSET_Y, 0.0))
    )
    lower_rib = (
        cq.Workplane("XY")
        .box(rib_length, EAR_Y, EAR_Z * 0.72)
        .translate((rib_center_x, -EAR_OFFSET_Y, 0.0))
    )

    return collar.union(bridge).union(upper_rib).union(lower_rib)
def _make_spoke_arm_body() -> cq.Workplane:
    root_cheek = (
        cq.Workplane("XZ")
        .center(0.022, 0.0)
        .rect(0.036, 0.030)
        .extrude(0.009, both=True)
    )

    spoke = (
        cq.Workplane("XZ")
        .moveTo(0.006, -0.014)
        .lineTo(0.030, -0.012)
        .lineTo(0.138, -0.009)
        .lineTo(0.154, -0.006)
        .lineTo(0.154, 0.006)
        .lineTo(0.138, 0.009)
        .lineTo(0.030, 0.012)
        .lineTo(0.006, 0.014)
        .close()
        .extrude(ARM_WEB_THICKNESS / 2.0, both=True)
    )

    return root_cheek.union(spoke)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="hub_and_spoke_motion_rig")

    model.material("powder_steel", rgba=(0.20, 0.22, 0.25, 1.0))
    model.material("hub_casting", rgba=(0.34, 0.37, 0.41, 1.0))
    model.material("brushed_aluminum", rgba=(0.72, 0.74, 0.77, 1.0))
    model.material("arm_tip_dark", rgba=(0.18, 0.19, 0.21, 1.0))

    mast = model.part("mast")
    mast.visual(
        mesh_from_cadquery(_make_base_and_mast(), "mast_core"),
        material="powder_steel",
        name="mast_core",
    )
    mast.visual(
        mesh_from_cadquery(_make_hub_block(1), "upper_hub_block"),
        origin=Origin(xyz=(0.0, 0.0, UPPER_HUB_Z)),
        material="hub_casting",
        name="upper_hub",
    )
    mast.visual(
        mesh_from_cadquery(_make_hub_block(-1), "lower_hub_block"),
        origin=Origin(xyz=(0.0, 0.0, LOWER_HUB_Z)),
        material="hub_casting",
        name="lower_hub",
    )
    mast.visual(
        Box((EAR_X, EAR_Y, EAR_Z)),
        origin=Origin(xyz=(PIVOT_OFFSET_X, EAR_OFFSET_Y, UPPER_HUB_Z)),
        material="hub_casting",
        name="upper_hub_ear_pos",
    )
    mast.visual(
        Box((EAR_X, EAR_Y, EAR_Z)),
        origin=Origin(xyz=(PIVOT_OFFSET_X, -EAR_OFFSET_Y, UPPER_HUB_Z)),
        material="hub_casting",
        name="upper_hub_ear_neg",
    )
    mast.visual(
        Box((EAR_X, EAR_Y, EAR_Z)),
        origin=Origin(xyz=(-PIVOT_OFFSET_X, EAR_OFFSET_Y, LOWER_HUB_Z)),
        material="hub_casting",
        name="lower_hub_ear_pos",
    )
    mast.visual(
        Box((EAR_X, EAR_Y, EAR_Z)),
        origin=Origin(xyz=(-PIVOT_OFFSET_X, -EAR_OFFSET_Y, LOWER_HUB_Z)),
        material="hub_casting",
        name="lower_hub_ear_neg",
    )
    mast.inertial = Inertial.from_geometry(
        Box((0.22, 0.22, BASE_THICKNESS + MAST_HEIGHT)),
        mass=8.0,
        origin=Origin(xyz=(0.0, 0.0, (BASE_THICKNESS + MAST_HEIGHT) / 2.0)),
    )

    upper_arm = model.part("upper_spoke_arm")
    upper_arm.visual(
        Cylinder(radius=ARM_BARREL_RADIUS, length=ARM_BARREL_LENGTH),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material="brushed_aluminum",
        name="journal_barrel",
    )
    upper_arm.visual(
        mesh_from_cadquery(_make_spoke_arm_body(), "upper_spoke_body"),
        material="brushed_aluminum",
        name="spoke_body",
    )
    upper_arm.visual(
        Cylinder(radius=ARM_TIP_RADIUS, length=ARM_TIP_THICKNESS),
        origin=Origin(xyz=(ARM_TIP_X, 0.0, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="arm_tip_dark",
        name="tip_pad",
    )
    upper_arm.inertial = Inertial.from_geometry(
        Box((0.18, 0.04, 0.04)),
        mass=0.55,
        origin=Origin(xyz=(0.08, 0.0, 0.0)),
    )

    lower_arm = model.part("lower_spoke_arm")
    lower_arm.visual(
        Cylinder(radius=ARM_BARREL_RADIUS, length=ARM_BARREL_LENGTH),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material="brushed_aluminum",
        name="journal_barrel",
    )
    lower_arm.visual(
        mesh_from_cadquery(_make_spoke_arm_body(), "lower_spoke_body"),
        material="brushed_aluminum",
        name="spoke_body",
    )
    lower_arm.visual(
        Cylinder(radius=ARM_TIP_RADIUS, length=ARM_TIP_THICKNESS),
        origin=Origin(xyz=(ARM_TIP_X, 0.0, 0.0), rpy=(pi / 2.0, 0.0, 0.0)),
        material="arm_tip_dark",
        name="tip_pad",
    )
    lower_arm.inertial = Inertial.from_geometry(
        Box((0.18, 0.04, 0.04)),
        mass=0.55,
        origin=Origin(xyz=(0.08, 0.0, 0.0)),
    )

    model.articulation(
        "upper_hub_joint",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=upper_arm,
        origin=Origin(xyz=(PIVOT_OFFSET_X, 0.0, UPPER_HUB_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.55, upper=1.20, effort=12.0, velocity=1.6),
    )
    model.articulation(
        "lower_hub_joint",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=lower_arm,
        origin=Origin(xyz=(-PIVOT_OFFSET_X, 0.0, LOWER_HUB_Z), rpy=(0.0, 0.0, pi)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.55, upper=1.20, effort=12.0, velocity=1.6),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
