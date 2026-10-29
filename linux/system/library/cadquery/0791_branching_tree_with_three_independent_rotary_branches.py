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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
SPINE_HEIGHT = 1.52
SPINE_WIDTH = 0.08
SPINE_DEPTH = 0.10
RIGHT_HUB_X = 0.082
LEFT_HUB_X = -RIGHT_HUB_X
HUB_HEIGHT = 0.05
LOWER_Z = 0.52
MIDDLE_Z = 0.88
UPPER_Z = 1.22
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _cylinder_z(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    cx, cy, cz = center
    return cq.Workplane("XY").circle(radius).extrude(length).translate((cx, cy, cz - length / 2.0))
def _rib_xz(points: list[tuple[float, float]], width_y: float) -> cq.Workplane:
    return cq.Workplane("XZ").polyline(points).close().extrude(width_y, both=True)
def _make_side_saddle(side: float, z_level: float) -> cq.Workplane:
    axis_x = RIGHT_HUB_X if side > 0.0 else LEFT_HUB_X
    bridge_center_x = side * 0.060

    top_bridge = _box((0.050, 0.102, 0.014), (bridge_center_x, 0.0, z_level + 0.032))
    bottom_bridge = _box((0.050, 0.102, 0.014), (bridge_center_x, 0.0, z_level - 0.032))
    top_disk = _cylinder_z(0.034, 0.014, (axis_x, 0.0, z_level + 0.032))
    bottom_disk = _cylinder_z(0.034, 0.014, (axis_x, 0.0, z_level - 0.032))

    return top_bridge.union(bottom_bridge).union(top_disk).union(bottom_disk)
def _make_spine_shape() -> cq.Workplane:
    long_foot = _box((0.62, 0.10, 0.055), (0.0, 0.0, 0.0275))
    cross_foot = _box((0.18, 0.46, 0.050), (0.0, 0.0, 0.025))
    plinth = _box((0.22, 0.18, 0.080), (0.0, 0.0, 0.090))
    upright = _box((SPINE_WIDTH, SPINE_DEPTH, 1.380), (0.0, 0.0, 0.820))
    top_cap = _box((0.10, 0.12, 0.045), (0.0, 0.0, SPINE_HEIGHT - 0.0225))

    spine = long_foot.union(cross_foot).union(plinth).union(upright).union(top_cap)
    spine = spine.union(_make_side_saddle(1.0, LOWER_Z))
    spine = spine.union(_make_side_saddle(-1.0, MIDDLE_Z))
    spine = spine.union(_make_side_saddle(1.0, UPPER_Z))
    return spine
def _make_branch_core(
    arm_length: float,
    beam_width: float,
    beam_height: float,
    rib_drop: float,
) -> cq.Workplane:
    hub_outer = _cylinder_z(0.028, HUB_HEIGHT, (0.0, 0.0, 0.0))
    hub_bore = _cylinder_z(0.020, HUB_HEIGHT + 0.006, (0.0, 0.0, 0.0))
    rear_relief = _box((0.064, beam_width + 0.090, HUB_HEIGHT + 0.010), (-0.032, 0.0, 0.0))
    hub = hub_outer.cut(hub_bore).cut(rear_relief)
    neck = _box((0.100, beam_width * 0.34, beam_height * 0.56), (0.074, 0.0, 0.0))
    shoulder = _box((0.044, beam_width + 0.014, beam_height + 0.008), (0.143, 0.0, 0.0))
    beam_center_x = 0.165 + arm_length / 2.0
    beam = _box((arm_length, beam_width, beam_height), (beam_center_x, 0.0, 0.0))
    rib = _rib_xz(
        [
            (0.108, -beam_height / 2.0),
            (0.212, -beam_height / 2.0),
            (0.160, -beam_height / 2.0 - rib_drop),
        ],
        beam_width * 0.44,
    )

    return hub.union(neck).union(shoulder).union(beam).union(rib)
def _make_pad_branch() -> cq.Workplane:
    branch = _make_branch_core(arm_length=0.235, beam_width=0.055, beam_height=0.030, rib_drop=0.032)
    pad_block = _box((0.034, 0.076, 0.048), (0.286, 0.0, 0.0))
    pad_face = _box((0.016, 0.108, 0.118), (0.311, 0.0, 0.010))
    return branch.union(pad_block).union(pad_face)
def _make_fork_branch() -> cq.Workplane:
    branch = _make_branch_core(arm_length=0.205, beam_width=0.050, beam_height=0.028, rib_drop=0.028)
    fork_body = _box((0.102, 0.086, 0.050), (0.258, 0.0, 0.0))
    slot = _box((0.078, 0.044, 0.070), (0.284, 0.0, 0.0))
    return branch.union(fork_body).cut(slot)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="rack_style_rotary_tree")

    spine_material = model.material("spine_charcoal", rgba=(0.20, 0.22, 0.24, 1.0))
    lower_material = model.material("lower_branch_blue", rgba=(0.28, 0.37, 0.50, 1.0))
    middle_material = model.material("middle_branch_olive", rgba=(0.40, 0.43, 0.28, 1.0))
    upper_material = model.material("upper_branch_silver", rgba=(0.63, 0.66, 0.68, 1.0))

    spine = model.part("spine")
    spine.visual(
        mesh_from_cadquery(_make_spine_shape(), "spine"),
        material=spine_material,
        name="spine_shell",
    )

    lower_branch = model.part("lower_branch")
    lower_branch.visual(
        mesh_from_cadquery(_make_pad_branch(), "lower_branch"),
        material=lower_material,
        name="lower_branch_shell",
    )

    middle_branch = model.part("middle_branch")
    middle_branch.visual(
        mesh_from_cadquery(_make_fork_branch(), "middle_branch"),
        material=middle_material,
        name="middle_branch_shell",
    )

    upper_branch = model.part("upper_branch")
    upper_branch.visual(
        Cylinder(radius=0.016, length=HUB_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=upper_material,
        name="upper_hub",
    )
    upper_branch.visual(
        Box((0.040, 0.022, 0.016)),
        origin=Origin(xyz=(0.036, 0.0, 0.0)),
        material=upper_material,
        name="upper_root_neck",
    )
    upper_branch.visual(
        Box((0.046, 0.048, 0.028)),
        origin=Origin(xyz=(0.079, 0.0, 0.0)),
        material=upper_material,
        name="upper_shoulder",
    )
    upper_branch.visual(
        Box((0.060, 0.016, 0.024)),
        origin=Origin(xyz=(0.120, 0.0, -0.025)),
        material=upper_material,
        name="upper_gusset",
    )
    upper_branch.visual(
        Box((0.180, 0.046, 0.026)),
        origin=Origin(xyz=(0.192, 0.0, 0.0)),
        material=upper_material,
        name="upper_beam",
    )
    upper_branch.visual(
        Box((0.046, 0.052, 0.036)),
        origin=Origin(xyz=(0.305, 0.0, 0.0)),
        material=upper_material,
        name="upper_tab_base",
    )
    upper_branch.visual(
        Box((0.018, 0.072, 0.124)),
        origin=Origin(xyz=(0.337, 0.0, 0.034)),
        material=upper_material,
        name="upper_branch_shell",
    )

    joint_limits = MotionLimits(effort=18.0, velocity=1.2, lower=-1.25, upper=1.25)
    middle_limits = MotionLimits(effort=18.0, velocity=1.2, lower=-1.15, upper=1.15)

    model.articulation(
        "spine_to_lower_branch",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=lower_branch,
        origin=Origin(xyz=(RIGHT_HUB_X, 0.0, LOWER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=joint_limits,
    )
    model.articulation(
        "spine_to_middle_branch",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=middle_branch,
        origin=Origin(xyz=(LEFT_HUB_X, 0.0, MIDDLE_Z), rpy=(0.0, 0.0, pi)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=middle_limits,
    )
    model.articulation(
        "spine_to_upper_branch",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=upper_branch,
        origin=Origin(xyz=(RIGHT_HUB_X, 0.0, UPPER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=joint_limits,
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
