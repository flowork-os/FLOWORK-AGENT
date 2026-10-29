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
import cadquery as cq
SPINE_W = 0.08
SPINE_D = 0.06
SPINE_H = 1.30
PEDESTAL_H = 0.06
BASE_RAIL_H = 0.035
UPPER_HUB_Z = 1.02
LOWER_HUB_Z = 0.68
HUB_LENGTH = 0.058
BRANCH_HUB_RADIUS = 0.018
BRANCH_HUB_LENGTH = HUB_LENGTH
CHEEK_T = 0.014
CHEEK_LEN_X = 0.055
SADDLE_BLOCK_X = 0.03
CHEEK_OFFSET_Y = HUB_LENGTH / 2.0 + CHEEK_T / 2.0
HUB_X = SPINE_W / 2.0 + SADDLE_BLOCK_X + CHEEK_LEN_X / 2.0
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    sx, sy, sz = size
    x, y, z = center
    return cq.Workplane("XY").box(sx, sy, sz).translate((x, y, z))
def _side_saddle(sign: float, hub_z: float) -> cq.Workplane:
    hinge_x = sign * HUB_X
    block_x = sign * (SPINE_W / 2.0 + SADDLE_BLOCK_X / 2.0)
    cheek_center_x = hinge_x
    outer_face_y = CHEEK_OFFSET_Y + CHEEK_T / 2.0

    mount_block = _box((SADDLE_BLOCK_X, 0.10, 0.11), (block_x, 0.0, hub_z))

    front_cheek = _box((CHEEK_LEN_X, CHEEK_T, 0.11), (cheek_center_x, CHEEK_OFFSET_Y, hub_z))
    rear_cheek = _box((CHEEK_LEN_X, CHEEK_T, 0.11), (cheek_center_x, -CHEEK_OFFSET_Y, hub_z))

    front_boss = (
        cq.Workplane("XZ")
        .circle(0.031)
        .extrude(0.008)
        .translate((hinge_x, outer_face_y, hub_z))
    )
    rear_boss = (
        cq.Workplane("XZ")
        .circle(0.031)
        .extrude(-0.008)
        .translate((hinge_x, -outer_face_y, hub_z))
    )

    shoulder = _box((0.02, 0.088, 0.06), (sign * (SPINE_W / 2.0 + 0.01), 0.0, hub_z - 0.038))

    saddle = mount_block.union(front_cheek).union(rear_cheek).union(front_boss).union(rear_boss).union(shoulder)
    journal_bore = (
        cq.Workplane("XZ")
        .circle(BRANCH_HUB_RADIUS)
        .extrude(0.18, both=True)
        .translate((hinge_x, 0.0, hub_z))
    )
    return saddle.cut(journal_bore)
def _build_spine_shape() -> cq.Workplane:
    long_rail = _box((0.56, 0.09, BASE_RAIL_H), (0.0, 0.0, BASE_RAIL_H / 2.0))
    cross_rail = _box((0.18, 0.32, 0.03), (0.0, 0.0, 0.015))
    pedestal = _box((0.18, 0.14, PEDESTAL_H), (0.0, 0.0, BASE_RAIL_H + PEDESTAL_H / 2.0))
    spine = _box(
        (SPINE_W, SPINE_D, SPINE_H),
        (0.0, 0.0, BASE_RAIL_H + PEDESTAL_H + SPINE_H / 2.0),
    )
    top_cap = _box((0.09, 0.07, 0.018), (0.0, 0.0, BASE_RAIL_H + PEDESTAL_H + SPINE_H + 0.009))

    return (
        long_rail.union(cross_rail)
        .union(pedestal)
        .union(spine)
        .union(top_cap)
        .union(_side_saddle(-1.0, UPPER_HUB_Z))
        .union(_side_saddle(1.0, LOWER_HUB_Z))
    )
def _build_upper_branch_frame() -> cq.Workplane:
    root_pad = _box((0.06, 0.032, 0.05), (-0.02, 0.0, 0.0))
    hub_eye = cq.Workplane("XZ").circle(BRANCH_HUB_RADIUS).extrude(BRANCH_HUB_LENGTH / 2.0, both=True)
    beam = _box((0.216, 0.024, 0.034), (-0.151, 0.0, 0.0))
    head_block = _box((0.09, 0.045, 0.062), (-0.30, 0.0, 0.0))
    web = (
        cq.Workplane("XZ")
        .polyline([(-0.065, -0.014), (-0.11, -0.042), (-0.23, -0.042), (-0.195, -0.014)])
        .close()
        .extrude(0.010, both=True)
    )
    return root_pad.union(hub_eye).union(beam).union(head_block).union(web)
def _build_upper_pad() -> cq.Workplane:
    return _box((0.032, 0.10, 0.082), (-0.357, 0.0, 0.0))
def _build_lower_branch_frame() -> cq.Workplane:
    root_pad = _box((0.06, 0.032, 0.05), (0.02, 0.0, 0.0))
    hub_eye = cq.Workplane("XZ").circle(BRANCH_HUB_RADIUS).extrude(BRANCH_HUB_LENGTH / 2.0, both=True)
    beam = _box((0.216, 0.024, 0.034), (0.151, 0.0, 0.0))
    head_block = _box((0.09, 0.048, 0.062), (0.30, 0.0, 0.0))
    web = (
        cq.Workplane("XZ")
        .polyline([(0.065, -0.014), (0.11, -0.042), (0.23, -0.042), (0.195, -0.014)])
        .close()
        .extrude(0.010, both=True)
    )
    return root_pad.union(hub_eye).union(beam).union(head_block).union(web)
def _build_lower_fork() -> cq.Workplane:
    bridge = _box((0.040, 0.086, 0.064), (0.362, 0.0, 0.0))
    upper_tine = _box((0.078, 0.086, 0.016), (0.421, 0.0, 0.024))
    lower_tine = _box((0.078, 0.086, 0.016), (0.421, 0.0, -0.024))
    return bridge.union(upper_tine).union(lower_tine)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="two_branch_rotary_tree")

    dark_steel = model.material("dark_steel", rgba=(0.34, 0.36, 0.39, 1.0))
    satin_steel = model.material("satin_steel", rgba=(0.52, 0.54, 0.56, 1.0))
    pad_rubber = model.material("pad_rubber", rgba=(0.18, 0.18, 0.20, 1.0))

    spine = model.part("spine")
    spine.visual(
        mesh_from_cadquery(_build_spine_shape(), "spine_frame"),
        material=dark_steel,
        name="spine_frame",
    )

    upper_left_branch = model.part("upper_left_branch")
    upper_left_branch.visual(
        mesh_from_cadquery(_build_upper_branch_frame(), "upper_left_branch_frame"),
        material=satin_steel,
        name="branch_frame",
    )
    upper_left_branch.visual(
        mesh_from_cadquery(_build_upper_pad(), "upper_left_pad"),
        material=pad_rubber,
        name="pad_face",
    )

    lower_right_branch = model.part("lower_right_branch")
    lower_right_branch.visual(
        mesh_from_cadquery(_build_lower_branch_frame(), "lower_right_branch_frame"),
        material=satin_steel,
        name="branch_frame",
    )
    lower_right_branch.visual(
        mesh_from_cadquery(_build_lower_fork(), "lower_right_fork"),
        material=satin_steel,
        name="fork_head",
    )

    model.articulation(
        "spine_to_upper_left_branch",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=upper_left_branch,
        origin=Origin(xyz=(-HUB_X, 0.0, UPPER_HUB_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-0.35, upper=1.15),
    )
    model.articulation(
        "spine_to_lower_right_branch",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=lower_right_branch,
        origin=Origin(xyz=(HUB_X, 0.0, LOWER_HUB_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-0.30, upper=1.10),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
