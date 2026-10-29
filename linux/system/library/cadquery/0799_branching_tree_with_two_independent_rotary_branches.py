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
BASE_LENGTH = 0.34
BASE_WIDTH = 0.24
BASE_THICKNESS = 0.028
MAST_WIDTH = 0.06
MAST_DEPTH = 0.08
MAST_HEIGHT = 0.72
LOWER_HUB_HEIGHT = 0.31
UPPER_HUB_HEIGHT = 0.56
LOWER_HUB_Y = 0.024
UPPER_HUB_Y = -0.024
HUB_REAR = -0.057
HUB_FRONT = 0.003
HUB_DEPTH = HUB_FRONT - HUB_REAR
HUB_WIDTH = 0.056
HUB_HEIGHT = 0.078
HUB_BORE_RADIUS = 0.0072
ARM_PIVOT_RADIUS = 0.014
ARM_PIVOT_THICKNESS = 0.006
ARM_ROOT_LENGTH = 0.022
ARM_ROOT_WIDTH = 0.020
ARM_ROOT_HEIGHT = 0.024
ARM_BEAM_LENGTH = 0.14
ARM_BEAM_WIDTH = 0.016
ARM_BEAM_HEIGHT = 0.018
ARM_TIP_RADIUS = 0.012
ARM_TIP_LENGTH = 0.016
def make_base_mast() -> cq.Workplane:
    base = cq.Workplane("XY").box(
        BASE_LENGTH,
        BASE_WIDTH,
        BASE_THICKNESS,
        centered=(True, True, False),
    )
    mast = (
        cq.Workplane("XY")
        .box(MAST_WIDTH, MAST_DEPTH, MAST_HEIGHT, centered=(True, True, False))
        .translate((0.0, 0.0, BASE_THICKNESS))
    )

    gusset_profile = (
        cq.Workplane("XZ")
        .polyline(
            [
                (MAST_WIDTH / 2.0 - 0.004, BASE_THICKNESS),
                (MAST_WIDTH / 2.0 - 0.004, BASE_THICKNESS + 0.18),
                (0.13, BASE_THICKNESS),
            ]
        )
        .close()
    )
    right_gusset = gusset_profile.extrude(0.012).translate((0.0, -0.038, 0.0))
    left_gusset = right_gusset.mirror("XZ")

    return base.union(mast).union(right_gusset).union(left_gusset)
def make_hub_block(direction: int = 1) -> cq.Workplane:
    body_center_x = 0.5 * (HUB_REAR + HUB_FRONT)
    body = cq.Workplane("XY").box(HUB_DEPTH, HUB_WIDTH, HUB_HEIGHT).translate(
        (body_center_x, 0.0, 0.0)
    )
    bore = cq.Workplane("XZ").circle(HUB_BORE_RADIUS).extrude(
        0.5 * (HUB_WIDTH + 0.01), both=True
    )
    hub = body.cut(bore)
    if direction < 0:
        hub = hub.mirror("YZ")
    return hub
def make_spoke_arm(direction: int = 1) -> cq.Workplane:
    pivot_center_x = HUB_FRONT + 0.5 * ARM_PIVOT_THICKNESS
    root_start_x = HUB_FRONT + ARM_PIVOT_THICKNESS
    root_center_x = root_start_x + 0.5 * ARM_ROOT_LENGTH
    beam_start_x = root_start_x + ARM_ROOT_LENGTH
    beam_center_x = beam_start_x + 0.5 * ARM_BEAM_LENGTH
    tip_center_x = beam_start_x + ARM_BEAM_LENGTH + 0.5 * ARM_TIP_LENGTH - 0.001

    pivot = cq.Workplane("YZ").circle(ARM_PIVOT_RADIUS).extrude(
        0.5 * ARM_PIVOT_THICKNESS, both=True
    ).translate((pivot_center_x, 0.0, 0.0))
    root = cq.Workplane("XY").box(
        ARM_ROOT_LENGTH, ARM_ROOT_WIDTH, ARM_ROOT_HEIGHT
    ).translate((root_center_x, 0.0, 0.0))
    beam = cq.Workplane("XY").box(
        ARM_BEAM_LENGTH, ARM_BEAM_WIDTH, ARM_BEAM_HEIGHT
    ).translate((beam_center_x, 0.0, 0.0))
    tip = cq.Workplane("YZ").circle(ARM_TIP_RADIUS).extrude(
        0.5 * ARM_TIP_LENGTH, both=True
    ).translate((tip_center_x, 0.0, 0.0))

    arm = pivot.union(root).union(beam).union(tip)
    if direction < 0:
        arm = arm.mirror("YZ")
    return arm
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="two_branch_motion_rig")

    dark_frame = model.material("dark_frame", rgba=(0.22, 0.24, 0.27, 1.0))
    hub_finish = model.material("hub_finish", rgba=(0.52, 0.56, 0.62, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.84, 0.50, 0.18, 1.0))

    mast = model.part("mast")
    mast.visual(
        mesh_from_cadquery(make_base_mast(), "mast_frame"),
        material=dark_frame,
        name="frame_shell",
    )
    lower_hub_x = MAST_WIDTH / 2.0 - HUB_REAR
    upper_hub_x = -(MAST_WIDTH / 2.0 - HUB_REAR)
    mast.visual(
        mesh_from_cadquery(make_hub_block(1), "lower_hub_block"),
        origin=Origin(xyz=(lower_hub_x, LOWER_HUB_Y, LOWER_HUB_HEIGHT)),
        material=hub_finish,
        name="lower_hub_shell",
    )
    mast.visual(
        mesh_from_cadquery(make_hub_block(-1), "upper_hub_block"),
        origin=Origin(xyz=(upper_hub_x, UPPER_HUB_Y, UPPER_HUB_HEIGHT)),
        material=hub_finish,
        name="upper_hub_shell",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        mesh_from_cadquery(make_spoke_arm(1), "lower_spoke_arm"),
        material=arm_finish,
        name="arm_shell",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(make_spoke_arm(-1), "upper_spoke_arm"),
        material=arm_finish,
        name="arm_shell",
    )

    model.articulation(
        "mast_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=lower_arm,
        origin=Origin(xyz=(lower_hub_x, LOWER_HUB_Y, LOWER_HUB_HEIGHT)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.5,
            lower=-0.65,
            upper=1.20,
        ),
    )
    model.articulation(
        "mast_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=upper_arm,
        origin=Origin(xyz=(upper_hub_x, UPPER_HUB_Y, UPPER_HUB_HEIGHT)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.5,
            lower=-0.55,
            upper=1.25,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
