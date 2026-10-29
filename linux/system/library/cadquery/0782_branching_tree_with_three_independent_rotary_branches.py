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
BASE_RADIUS = 0.18
BASE_THICKNESS = 0.05
PLINTH_HEIGHT = 0.045
SHAFT_RADIUS = 0.031
TOWER_TOP_Z = 0.385
COLLAR_INNER_RADIUS = 0.032
COLLAR_OUTER_RADIUS = 0.056
COLLAR_HEIGHT = 0.04
COLLAR_FLANGE_RADIUS = 0.063
COLLAR_FLANGE_THICKNESS = 0.004
SUPPORT_FLANGE_RADIUS = 0.05
SUPPORT_FLANGE_THICKNESS = 0.005
ARM_REACH = 0.34
ARM_ROOT_WIDTH = 0.05
ARM_TIP_WIDTH = 0.033
ARM_THICKNESS = 0.024
ROOT_START_X = 0.05
GUSSET_WIDTH = 0.018
GUSSET_END_X = 0.135
ARM_CENTERS_Z = (0.14, 0.23, 0.32)
ARM_REST_ANGLES = (0.0, 2.0 * pi / 3.0, -2.0 * pi / 3.0)
def _arm_shape() -> cq.Workplane:
    collar = (
        cq.Workplane("XY")
        .circle(COLLAR_OUTER_RADIUS)
        .circle(COLLAR_INNER_RADIUS)
        .extrude(COLLAR_HEIGHT / 2.0, both=True)
    )

    upper_flange = (
        cq.Workplane("XY")
        .workplane(offset=(COLLAR_HEIGHT / 2.0) - COLLAR_FLANGE_THICKNESS)
        .circle(COLLAR_FLANGE_RADIUS)
        .circle(COLLAR_INNER_RADIUS)
        .extrude(COLLAR_FLANGE_THICKNESS)
    )
    lower_flange = (
        cq.Workplane("XY")
        .workplane(offset=-(COLLAR_HEIGHT / 2.0))
        .circle(COLLAR_FLANGE_RADIUS)
        .circle(COLLAR_INNER_RADIUS)
        .extrude(COLLAR_FLANGE_THICKNESS)
    )

    beam = (
        cq.Workplane("XY")
        .moveTo(ROOT_START_X, -ARM_ROOT_WIDTH / 2.0)
        .lineTo(ARM_REACH - ARM_TIP_WIDTH / 2.0, -ARM_TIP_WIDTH / 2.0)
        .threePointArc(
            (ARM_REACH, 0.0),
            (ARM_REACH - ARM_TIP_WIDTH / 2.0, ARM_TIP_WIDTH / 2.0),
        )
        .lineTo(ROOT_START_X, ARM_ROOT_WIDTH / 2.0)
        .close()
        .extrude(ARM_THICKNESS / 2.0, both=True)
    )

    gusset = (
        cq.Workplane("XZ")
        .moveTo(COLLAR_OUTER_RADIUS - 0.004, -(COLLAR_HEIGHT / 2.0) + 0.002)
        .lineTo(GUSSET_END_X, -(ARM_THICKNESS / 2.0))
        .lineTo(COLLAR_OUTER_RADIUS + 0.014, -(ARM_THICKNESS / 2.0))
        .close()
        .extrude(GUSSET_WIDTH / 2.0, both=True)
    )

    tip_stop = (
        cq.Workplane("XY")
        .workplane(offset=ARM_THICKNESS / 2.0)
        .center(ARM_REACH - 0.018, 0.0)
        .circle(0.01)
        .extrude(0.018)
    )

    return collar.union(upper_flange).union(lower_flange).union(beam).union(gusset).union(tip_stop)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_mounted_three_branch_rotary_stand")

    model.material("powder_steel", rgba=(0.20, 0.22, 0.25, 1.0))
    model.material("brushed_aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    pedestal = model.part("pedestal")
    pedestal.visual(
        Cylinder(radius=BASE_RADIUS, length=BASE_THICKNESS),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS / 2.0)),
        material="powder_steel",
        name="base_disc",
    )
    pedestal.visual(
        Cylinder(radius=0.11, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + 0.009)),
        material="powder_steel",
        name="plinth_lower",
    )
    pedestal.visual(
        Cylinder(radius=0.083, length=0.016),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + 0.018 + 0.008)),
        material="powder_steel",
        name="plinth_middle",
    )
    pedestal.visual(
        Cylinder(radius=0.062, length=0.011),
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS + 0.034 + 0.0055)),
        material="powder_steel",
        name="plinth_upper",
    )
    pedestal.visual(
        Cylinder(radius=SHAFT_RADIUS, length=TOWER_TOP_Z - (BASE_THICKNESS + PLINTH_HEIGHT)),
        origin=Origin(
            xyz=(
                0.0,
                0.0,
                BASE_THICKNESS + PLINTH_HEIGHT
                + (TOWER_TOP_Z - (BASE_THICKNESS + PLINTH_HEIGHT)) / 2.0,
            )
        ),
        material="powder_steel",
        name="tower_shaft",
    )
    for index, center_z in enumerate(ARM_CENTERS_Z, start=1):
        pedestal.visual(
            Cylinder(radius=SUPPORT_FLANGE_RADIUS, length=SUPPORT_FLANGE_THICKNESS),
            origin=Origin(
                xyz=(
                    0.0,
                    0.0,
                    center_z - (COLLAR_HEIGHT / 2.0) - (SUPPORT_FLANGE_THICKNESS / 2.0),
                )
            ),
            material="powder_steel",
            name=f"support_flange_{index}",
        )
    pedestal.inertial = Inertial.from_geometry(
        Cylinder(radius=BASE_RADIUS, length=BASE_THICKNESS),
        mass=8.0,
        origin=Origin(xyz=(0.0, 0.0, BASE_THICKNESS / 2.0)),
    )

    arm_inertial = Inertial.from_geometry(
        Box((ARM_REACH + COLLAR_OUTER_RADIUS, ARM_ROOT_WIDTH, COLLAR_HEIGHT + 0.018)),
        mass=0.7,
        origin=Origin(xyz=((ARM_REACH - COLLAR_OUTER_RADIUS) / 2.0, 0.0, 0.0)),
    )

    arms = []
    for part_name in ("lower_arm", "middle_arm", "upper_arm"):
        arm = model.part(part_name, inertial=arm_inertial)
        arm.visual(
            mesh_from_cadquery(_arm_shape(), f"{part_name}_shell"),
            material="brushed_aluminum",
            name="arm_shell",
        )
        arms.append(arm)

    lower_arm, middle_arm, upper_arm = arms

    model.articulation(
        "pedestal_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=lower_arm,
        origin=Origin(xyz=(0.0, 0.0, ARM_CENTERS_Z[0]), rpy=(0.0, 0.0, ARM_REST_ANGLES[0])),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-2.3, upper=2.3, effort=22.0, velocity=1.8),
    )
    model.articulation(
        "pedestal_to_middle_arm",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=middle_arm,
        origin=Origin(xyz=(0.0, 0.0, ARM_CENTERS_Z[1]), rpy=(0.0, 0.0, ARM_REST_ANGLES[1])),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-2.3, upper=2.3, effort=22.0, velocity=1.8),
    )
    model.articulation(
        "pedestal_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=upper_arm,
        origin=Origin(xyz=(0.0, 0.0, ARM_CENTERS_Z[2]), rpy=(0.0, 0.0, ARM_REST_ANGLES[2])),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=-2.3, upper=2.3, effort=22.0, velocity=1.8),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
