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

# ===== model =====
import math
import cadquery as cq
MAST_RADIUS = 0.024
MAST_HEIGHT = 0.320
BASE_RADIUS = 0.045
BASE_HEIGHT = 0.052
TOP_CAP_RADIUS = 0.031
TOP_CAP_HEIGHT = 0.016
HUB_HEIGHT = 0.040
HUB_BLOCK_THICKNESS = 0.030
HUB_BLOCK_WIDTH = 0.064
HUB_BLOCK_CENTER_X = MAST_RADIUS + HUB_BLOCK_THICKNESS / 2.0
PIVOT_BOSS_RADIUS = 0.015
PIVOT_BOSS_LENGTH = 0.052
PIVOT_X = 0.061
ARM_ROOT_LENGTH = 0.030
ARM_ROOT_WIDTH = 0.028
ARM_ROOT_HEIGHT = 0.026
ARM_BEAM_WIDTH = 0.020
ARM_BEAM_HEIGHT = 0.018
ARM_BEAM_START_X = PIVOT_BOSS_RADIUS + ARM_ROOT_LENGTH
PAD_THICKNESS = 0.010
PAD_WIDTH = 0.042
PAD_HEIGHT = 0.030
def make_pad_shape() -> cq.Workplane:
    pad = cq.Workplane("XY").box(
        PAD_THICKNESS, PAD_WIDTH, PAD_HEIGHT, centered=(True, True, True)
    )
    pad = (
        pad.faces(">X")
        .workplane()
        .pushPoints([(0.0, -0.010), (0.0, 0.010)])
        .hole(0.006)
    )
    return pad
BRANCH_CONFIGS = (
    {
        "name": "lower",
        "hub_name": "hub_lower",
        "arm_name": "arm_lower",
        "mount_name": "mast_to_hub_lower",
        "joint_name": "hub_lower_to_arm_lower",
        "height": 0.108,
        "yaw": 0.0,
        "pad_center_x": 0.165,
        "limits": (-0.75, 0.85),
    },
    {
        "name": "middle",
        "hub_name": "hub_middle",
        "arm_name": "arm_middle",
        "mount_name": "mast_to_hub_middle",
        "joint_name": "hub_middle_to_arm_middle",
        "height": 0.188,
        "yaw": math.radians(122.0),
        "pad_center_x": 0.152,
        "limits": (-0.70, 0.90),
    },
    {
        "name": "upper",
        "hub_name": "hub_upper",
        "arm_name": "arm_upper",
        "mount_name": "mast_to_hub_upper",
        "joint_name": "hub_upper_to_arm_upper",
        "height": 0.268,
        "yaw": math.radians(246.0),
        "pad_center_x": 0.170,
        "limits": (-0.80, 0.78),
    },
)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="three_branch_fixture_head")

    dark_steel = model.material("dark_steel", rgba=(0.23, 0.24, 0.27, 1.0))
    machine_gray = model.material("machine_gray", rgba=(0.60, 0.63, 0.67, 1.0))
    aluminum = model.material("aluminum", rgba=(0.73, 0.75, 0.78, 1.0))
    pad_gray = model.material("pad_gray", rgba=(0.48, 0.50, 0.53, 1.0))

    mast = model.part("mast")
    mast.visual(
        Cylinder(radius=BASE_RADIUS, length=BASE_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT / 2.0)),
        material=dark_steel,
        name="base_collar",
    )
    mast.visual(
        Cylinder(radius=MAST_RADIUS, length=MAST_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT + MAST_HEIGHT / 2.0)),
        material=machine_gray,
        name="mast_shaft",
    )
    mast.visual(
        Cylinder(radius=TOP_CAP_RADIUS, length=TOP_CAP_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT + MAST_HEIGHT + TOP_CAP_HEIGHT / 2.0)),
        material=dark_steel,
        name="top_cap",
    )
    mast.inertial = Inertial.from_geometry(
        Cylinder(radius=BASE_RADIUS, length=BASE_HEIGHT + MAST_HEIGHT + TOP_CAP_HEIGHT),
        mass=5.6,
        origin=Origin(
            xyz=(0.0, 0.0, (BASE_HEIGHT + MAST_HEIGHT + TOP_CAP_HEIGHT) / 2.0)
        ),
    )

    pad_shape = make_pad_shape()

    for branch in BRANCH_CONFIGS:
        hub = model.part(branch["hub_name"])
        hub.visual(
            Box((HUB_BLOCK_THICKNESS, HUB_BLOCK_WIDTH, HUB_HEIGHT)),
            origin=Origin(xyz=(HUB_BLOCK_CENTER_X, 0.0, 0.0)),
            material=machine_gray,
            name="hub_body",
        )
        hub.visual(
            Cylinder(radius=PIVOT_BOSS_RADIUS, length=PIVOT_BOSS_LENGTH),
            origin=Origin(xyz=(PIVOT_X, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=dark_steel,
            name="pivot_boss",
        )
        hub.inertial = Inertial.from_geometry(
            Box((0.080, 0.070, 0.050)),
            mass=0.9,
            origin=Origin(xyz=(0.040, 0.0, 0.0)),
        )

        model.articulation(
            branch["mount_name"],
            ArticulationType.FIXED,
            parent=mast,
            child=hub,
            origin=Origin(xyz=(0.0, 0.0, branch["height"]), rpy=(0.0, 0.0, branch["yaw"])),
        )

        arm = model.part(branch["arm_name"])
        arm.visual(
            Box((ARM_ROOT_LENGTH, ARM_ROOT_WIDTH, ARM_ROOT_HEIGHT)),
            origin=Origin(
                xyz=(PIVOT_BOSS_RADIUS + ARM_ROOT_LENGTH / 2.0, 0.0, 0.0)
            ),
            material=aluminum,
            name="root_lug",
        )
        arm.visual(
            Box(
                (
                    branch["pad_center_x"] - PAD_THICKNESS / 2.0 - ARM_BEAM_START_X,
                    ARM_BEAM_WIDTH,
                    ARM_BEAM_HEIGHT,
                )
            ),
            origin=Origin(
                xyz=(
                    (
                        ARM_BEAM_START_X
                        + branch["pad_center_x"]
                        - PAD_THICKNESS / 2.0
                    )
                    / 2.0,
                    0.0,
                    0.0,
                )
            ),
            material=aluminum,
            name="arm_body",
        )
        arm.visual(
            mesh_from_cadquery(pad_shape, f"{branch['name']}_mount_pad"),
            origin=Origin(xyz=(branch["pad_center_x"], 0.0, 0.0)),
            material=pad_gray,
            name="pad",
        )
        arm.inertial = Inertial.from_geometry(
            Box((branch["pad_center_x"], 0.050, 0.040)),
            mass=0.65,
            origin=Origin(xyz=(branch["pad_center_x"] / 2.0, 0.0, 0.0)),
        )

        lower, upper = branch["limits"]
        model.articulation(
            branch["joint_name"],
            ArticulationType.REVOLUTE,
            parent=hub,
            child=arm,
            origin=Origin(xyz=(PIVOT_X, 0.0, 0.0)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(
                effort=18.0,
                velocity=1.6,
                lower=lower,
                upper=upper,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
