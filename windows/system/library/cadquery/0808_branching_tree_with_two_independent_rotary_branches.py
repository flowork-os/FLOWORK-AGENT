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
BASE_RADIUS = 0.22
BASE_THICK = 0.045
PLINTH_SIZE = 0.18
PLINTH_HEIGHT = 0.05
COLUMN_RADIUS = 0.05
COLUMN_HEIGHT = 1.12
TOP_CAP_THICK = 0.018
BLOCK_HEIGHT = 0.07
PAD_RADIUS = 0.042
PAD_HEIGHT = 0.015
PAD_CENTER_X = 0.135
HUB_RADIUS = 0.04
HUB_HEIGHT = 0.028
ARM_LENGTH = 0.29
ARM_WIDTH = 0.055
ARM_THICK = 0.036
STEM_LENGTH = 0.05
STEM_WIDTH = 0.04
STEM_HEIGHT = 0.085
FACEPLATE_THICK = 0.012
FACEPLATE_WIDTH = 0.095
FACEPLATE_HEIGHT = 0.11
LOWER_BLOCK_Z = BASE_THICK + 0.38
UPPER_BLOCK_Z = BASE_THICK + 0.76
def _make_pedestal_shape() -> cq.Workplane:
    base = cq.Workplane("XY").circle(BASE_RADIUS).extrude(BASE_THICK)
    plinth = cq.Workplane("XY").box(PLINTH_SIZE, PLINTH_SIZE, PLINTH_HEIGHT).translate(
        (0.0, 0.0, BASE_THICK + PLINTH_HEIGHT / 2.0)
    )
    column = cq.Workplane("XY").circle(COLUMN_RADIUS).extrude(COLUMN_HEIGHT).translate(
        (0.0, 0.0, BASE_THICK)
    )
    cap = cq.Workplane("XY").circle(COLUMN_RADIUS * 1.08).extrude(TOP_CAP_THICK).translate(
        (0.0, 0.0, BASE_THICK + COLUMN_HEIGHT)
    )

    gusset_profile = [
        (COLUMN_RADIUS + 0.004, BASE_THICK),
        (0.145, BASE_THICK),
        (0.115, BASE_THICK + 0.16),
        (COLUMN_RADIUS + 0.004, BASE_THICK + 0.24),
    ]
    gusset = (
        cq.Workplane("XZ")
        .polyline(gusset_profile)
        .close()
        .extrude(0.018, both=True)
    )

    pedestal = base.union(plinth).union(column).union(cap)
    for angle in (0, 90, 180, 270):
        pedestal = pedestal.union(gusset.rotate((0, 0, 0), (0, 0, 1), angle))

    lower_block = _make_support_block_shape().translate((0.0, 0.0, LOWER_BLOCK_Z))
    upper_block = _make_support_block_shape().rotate((0, 0, 0), (0, 0, 1), 180).translate(
        (0.0, 0.0, UPPER_BLOCK_Z)
    )
    pedestal = pedestal.union(lower_block).union(upper_block)
    return pedestal
def _make_support_block_shape() -> cq.Workplane:
    body_length = 0.10
    body_width = 0.08
    jaw_length = 0.022

    body = (
        cq.Workplane("XY")
        .box(body_length, body_width, BLOCK_HEIGHT)
        .translate((COLUMN_RADIUS + body_length / 2.0, 0.0, 0.0))
        .edges("|Z")
        .fillet(0.008)
    )
    jaw = cq.Workplane("XY").box(jaw_length, body_width * 0.88, BLOCK_HEIGHT * 0.92).translate(
        (COLUMN_RADIUS + jaw_length / 2.0, 0.0, 0.0)
    )
    pad = cq.Workplane("XY").circle(PAD_RADIUS).extrude(PAD_HEIGHT).translate(
        (PAD_CENTER_X, 0.0, BLOCK_HEIGHT / 2.0)
    )
    web = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.082, -BLOCK_HEIGHT * 0.20),
                (PAD_CENTER_X - 0.024, -BLOCK_HEIGHT * 0.20),
                (PAD_CENTER_X - 0.006, BLOCK_HEIGHT * 0.22),
                (0.092, BLOCK_HEIGHT * 0.14),
            ]
        )
        .close()
        .extrude(body_width * 0.5, both=True)
    )

    return body.union(jaw).union(web).union(pad)
def _make_branch_core_shape() -> cq.Workplane:
    hub = cq.Workplane("XY").circle(HUB_RADIUS).extrude(HUB_HEIGHT)
    beam = cq.Workplane("XY").box(ARM_LENGTH, ARM_WIDTH, ARM_THICK).translate(
        (ARM_LENGTH / 2.0, 0.0, HUB_HEIGHT + ARM_THICK / 2.0 - 0.01)
    )
    stem = cq.Workplane("XY").box(STEM_LENGTH, STEM_WIDTH, STEM_HEIGHT).translate(
        (ARM_LENGTH - 0.005, 0.0, 0.065)
    )
    rib = (
        cq.Workplane("XZ")
        .polyline(
            [
                (ARM_LENGTH - 0.10, HUB_HEIGHT * 0.55),
                (ARM_LENGTH - 0.025, HUB_HEIGHT * 0.55),
                (ARM_LENGTH - 0.025, 0.082),
            ]
        )
        .close()
        .extrude(0.038, both=True)
    )

    return hub.union(beam).union(stem).union(rib)
def _make_faceplate_shape() -> cq.Workplane:
    return cq.Workplane("XY").box(
        FACEPLATE_THICK,
        FACEPLATE_WIDTH,
        FACEPLATE_HEIGHT,
    ).translate((ARM_LENGTH + 0.023, 0.0, 0.095))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tooling_tree")

    model.material("pedestal_steel", color=(0.22, 0.24, 0.27))
    model.material("block_steel", color=(0.42, 0.44, 0.47))
    model.material("arm_paint", color=(0.83, 0.40, 0.12))
    model.material("plate_steel", color=(0.76, 0.78, 0.80))

    pedestal = model.part("pedestal")
    pedestal.visual(
        mesh_from_cadquery(_make_pedestal_shape(), "pedestal_shell"),
        material="pedestal_steel",
        name="pedestal_shell",
    )

    lower_branch = model.part("lower_branch")
    lower_branch.visual(
        mesh_from_cadquery(_make_branch_core_shape(), "lower_branch_core"),
        material="arm_paint",
        name="arm_core",
    )
    lower_branch.visual(
        mesh_from_cadquery(_make_faceplate_shape(), "lower_branch_faceplate"),
        material="plate_steel",
        name="faceplate",
    )

    upper_branch = model.part("upper_branch")
    upper_branch.visual(
        mesh_from_cadquery(_make_branch_core_shape(), "upper_branch_core"),
        material="arm_paint",
        name="arm_core",
    )
    upper_branch.visual(
        mesh_from_cadquery(_make_faceplate_shape(), "upper_branch_faceplate"),
        material="plate_steel",
        name="faceplate",
    )

    branch_limits = MotionLimits(
        effort=25.0,
        velocity=1.5,
        lower=-1.75,
        upper=1.75,
    )
    model.articulation(
        "pedestal_to_lower_branch",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=lower_branch,
        origin=Origin(
            xyz=(PAD_CENTER_X, 0.0, LOWER_BLOCK_Z + BLOCK_HEIGHT / 2.0 + PAD_HEIGHT)
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=branch_limits,
    )
    model.articulation(
        "pedestal_to_upper_branch",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=upper_branch,
        origin=Origin(
            xyz=(-PAD_CENTER_X, 0.0, UPPER_BLOCK_Z + BLOCK_HEIGHT / 2.0 + PAD_HEIGHT),
            rpy=(0.0, 0.0, math.pi),
        ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=25.0,
            velocity=1.5,
            lower=-1.75,
            upper=1.75,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
