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
BASE_RADIUS = 0.17
BASE_THICKNESS = 0.044
BASE_BOSS_RADIUS = 0.072
BASE_BOSS_HEIGHT = 0.028
BASE_TOTAL_HEIGHT = BASE_THICKNESS + BASE_BOSS_HEIGHT
MAST_RADIUS = 0.027
MAST_HEIGHT = 0.37
MAST_FLANGE_RADIUS = 0.045
MAST_FLANGE_HEIGHT = 0.015
MAST_CAP_RADIUS = 0.032
MAST_CAP_HEIGHT = 0.014
CLAMP_RING_RADIUS = 0.051
CLAMP_HEIGHT = 0.042
CLAMP_BLOCK_WIDTH = 0.052
SUPPORT_AXIS_OFFSET = 0.104
SUPPORT_BLOCK_LENGTH = 0.034
SUPPORT_BLOCK_HEIGHT = 0.05
SUPPORT_BLOCK_WIDTH = 0.046
LONG_BRANCH_LENGTH = 0.34
LONG_BRANCH_WIDTH = 0.032
LONG_BRANCH_HEIGHT = 0.025
SHORT_BRANCH_LENGTH = 0.22
SHORT_BRANCH_WIDTH = 0.029
SHORT_BRANCH_HEIGHT = 0.022
BRANCH_HOUSING_RADIUS = 0.026
BRANCH_HOUSING_HEIGHT = 0.02
BRANCH_CAP_RADIUS = 0.018
BRANCH_CAP_HEIGHT = 0.01
BRANCH_ROOT_LENGTH = 0.052
LONG_COLLAR_Z = 0.31
SHORT_COLLAR_Z = 0.235
ROTARY_LIMIT = 2.5
def _base_shape() -> cq.Workplane:
    foot = (
        cq.Workplane("XY")
        .circle(BASE_RADIUS)
        .extrude(BASE_THICKNESS)
        .faces(">Z")
        .edges()
        .chamfer(0.007)
    )
    boss = (
        cq.Workplane("XY")
        .circle(BASE_BOSS_RADIUS)
        .extrude(BASE_BOSS_HEIGHT)
        .translate((0.0, 0.0, BASE_THICKNESS))
    )
    return foot.union(boss)
def _mast_shape() -> cq.Workplane:
    flange = cq.Workplane("XY").circle(MAST_FLANGE_RADIUS).extrude(MAST_FLANGE_HEIGHT)
    shaft = cq.Workplane("XY").circle(MAST_RADIUS).extrude(MAST_HEIGHT)
    cap = (
        cq.Workplane("XY")
        .circle(MAST_CAP_RADIUS)
        .extrude(MAST_CAP_HEIGHT)
        .translate((0.0, 0.0, MAST_HEIGHT))
    )
    return flange.union(shaft).union(_collar_block_shape(-1.0, SHORT_COLLAR_Z)).union(
        _collar_block_shape(1.0, LONG_COLLAR_Z)
    ).union(cap)
def _collar_block_shape(side: float, support_top_z: float) -> cq.Workplane:
    clamp_bottom_z = support_top_z - CLAMP_HEIGHT
    clamp_center_z = clamp_bottom_z + (CLAMP_HEIGHT / 2.0)
    support_center_x = side * (SUPPORT_AXIS_OFFSET - (SUPPORT_BLOCK_LENGTH / 2.0))
    support_center_z = support_top_z - (SUPPORT_BLOCK_HEIGHT / 2.0)
    bridge_start_x = side * CLAMP_RING_RADIUS
    bridge_end_x = side * (SUPPORT_AXIS_OFFSET - SUPPORT_BLOCK_LENGTH)
    bridge_length = abs(bridge_end_x - bridge_start_x)
    bridge_center_x = (bridge_start_x + bridge_end_x) / 2.0

    ring = (
        cq.Workplane("XY")
        .circle(CLAMP_RING_RADIUS)
        .extrude(CLAMP_HEIGHT)
        .translate((0.0, 0.0, clamp_bottom_z))
    )
    bridge = (
        cq.Workplane("XY")
        .box(bridge_length, CLAMP_BLOCK_WIDTH, CLAMP_HEIGHT)
        .translate((bridge_center_x, 0.0, clamp_center_z))
    )
    support_block = (
        cq.Workplane("XY")
        .box(SUPPORT_BLOCK_LENGTH, SUPPORT_BLOCK_WIDTH, SUPPORT_BLOCK_HEIGHT)
        .translate((support_center_x, 0.0, support_center_z))
    )
    rib = (
        cq.Workplane("XZ")
        .polyline(
            [
                (side * (CLAMP_RING_RADIUS - 0.01), clamp_bottom_z + 0.006),
                (side * (CLAMP_RING_RADIUS + 0.012), clamp_bottom_z + CLAMP_HEIGHT - 0.004),
                (side * (SUPPORT_AXIS_OFFSET - SUPPORT_BLOCK_LENGTH + 0.004), support_top_z - 0.008),
                (side * (SUPPORT_AXIS_OFFSET - SUPPORT_BLOCK_LENGTH + 0.004), clamp_bottom_z + 0.008),
            ]
        )
        .close()
        .extrude(CLAMP_BLOCK_WIDTH * 0.42)
        .translate((0.0, -(CLAMP_BLOCK_WIDTH * 0.21), 0.0))
    )

    return ring.union(bridge).union(support_block).union(rib)
def _branch_shape(
    *,
    arm_length: float,
    arm_width: float,
    arm_height: float,
    name_bias: str,
) -> cq.Workplane:
    root_width = arm_width * 1.35
    root_height = max(arm_height + 0.006, 0.028)
    root_block = (
        cq.Workplane("XY")
        .box(BRANCH_ROOT_LENGTH, root_width, root_height)
        .translate((BRANCH_ROOT_LENGTH / 2.0, 0.0, root_height / 2.0))
    )
    housing_center_x = BRANCH_HOUSING_RADIUS
    housing = (
        cq.Workplane("XY")
        .circle(BRANCH_HOUSING_RADIUS)
        .extrude(BRANCH_HOUSING_HEIGHT)
        .translate((housing_center_x, 0.0, 0.0))
    )
    hub_cap = (
        cq.Workplane("XY")
        .circle(BRANCH_CAP_RADIUS)
        .extrude(BRANCH_CAP_HEIGHT)
        .translate((housing_center_x, 0.0, BRANCH_HOUSING_HEIGHT))
    )

    beam_start_x = BRANCH_ROOT_LENGTH - 0.004
    beam_center_x = beam_start_x + (arm_length / 2.0)
    beam_center_z = max(root_height * 0.48, arm_height / 2.0)
    beam = cq.Workplane("XY").box(
        arm_length,
        arm_width,
        arm_height,
    ).translate((beam_center_x, 0.0, beam_center_z))

    tip_radius = max(arm_width * 0.72, 0.019 if name_bias == "short" else 0.022)
    tip_height = arm_height * 1.35
    tip = (
        cq.Workplane("XY")
        .circle(tip_radius)
        .extrude(tip_height)
        .translate(
            (
                beam_start_x + arm_length - (tip_radius * 0.18),
                0.0,
                0.0,
            )
        )
    )

    gusset_thickness = arm_width * 0.58
    gusset_end_x = beam_start_x + min(0.11, arm_length * 0.42)
    gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.0, 0.0),
                (BRANCH_ROOT_LENGTH * 0.38, root_height + 0.003),
                (beam_start_x + 0.055, arm_height * 0.95),
                (gusset_end_x, arm_height * 0.24),
            ]
        )
        .close()
        .extrude(gusset_thickness)
        .translate((0.0, -gusset_thickness / 2.0, 0.0))
    )

    return root_block.union(housing).union(hub_cap).union(beam).union(tip).union(gusset)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mast_two_branch_rotary_head")

    model.material("powder_black", rgba=(0.16, 0.17, 0.18, 1.0))
    model.material("dark_steel", rgba=(0.27, 0.29, 0.31, 1.0))
    model.material("cast_aluminum", rgba=(0.68, 0.70, 0.73, 1.0))

    base_foot = model.part("base_foot")
    base_foot.visual(
        mesh_from_cadquery(_base_shape(), "base_foot"),
        material="powder_black",
        name="base_shell",
    )
    base_foot.inertial = Inertial.from_geometry(
        Cylinder(radius=BASE_RADIUS, length=BASE_TOTAL_HEIGHT),
        mass=8.0,
        origin=Origin(xyz=(0.0, 0.0, BASE_TOTAL_HEIGHT / 2.0)),
    )

    mast = model.part("mast")
    mast.visual(
        mesh_from_cadquery(_mast_shape(), "mast"),
        material="dark_steel",
        name="mast_shell",
    )
    mast.inertial = Inertial.from_geometry(
        Cylinder(radius=MAST_FLANGE_RADIUS, length=MAST_HEIGHT + MAST_CAP_HEIGHT),
        mass=2.4,
        origin=Origin(xyz=(0.0, 0.0, (MAST_HEIGHT + MAST_CAP_HEIGHT) / 2.0)),
    )

    long_branch = model.part("long_branch")
    long_branch.visual(
        mesh_from_cadquery(
            _branch_shape(
                arm_length=LONG_BRANCH_LENGTH,
                arm_width=LONG_BRANCH_WIDTH,
                arm_height=LONG_BRANCH_HEIGHT,
                name_bias="long",
            ),
            "long_branch",
        ),
        material="cast_aluminum",
        name="long_branch_body",
    )

    short_branch = model.part("short_branch")
    short_branch.visual(
        mesh_from_cadquery(
            _branch_shape(
                arm_length=SHORT_BRANCH_LENGTH,
                arm_width=SHORT_BRANCH_WIDTH,
                arm_height=SHORT_BRANCH_HEIGHT,
                name_bias="short",
            ),
            "short_branch",
        ),
        material="cast_aluminum",
        name="short_branch_body",
    )

    model.articulation(
        "base_to_mast",
        ArticulationType.FIXED,
        parent=base_foot,
        child=mast,
        origin=Origin(xyz=(0.0, 0.0, BASE_TOTAL_HEIGHT)),
    )
    model.articulation(
        "mast_to_long_branch",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=long_branch,
        origin=Origin(xyz=(SUPPORT_AXIS_OFFSET, 0.0, LONG_COLLAR_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=-ROTARY_LIMIT,
            upper=ROTARY_LIMIT,
            effort=22.0,
            velocity=1.8,
        ),
    )
    model.articulation(
        "mast_to_short_branch",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=short_branch,
        origin=Origin(xyz=(-SUPPORT_AXIS_OFFSET, 0.0, SHORT_COLLAR_Z), rpy=(0.0, 0.0, pi)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=-ROTARY_LIMIT,
            upper=ROTARY_LIMIT,
            effort=18.0,
            velocity=1.8,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
