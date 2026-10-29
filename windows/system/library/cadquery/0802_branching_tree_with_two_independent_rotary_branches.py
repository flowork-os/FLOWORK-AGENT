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
FRAME_HEIGHT = 0.42
FRAME_WIDTH = 0.12
FRAME_DEPTH = 0.026
RAIL_WIDTH = 0.018
RUNG_DEPTH = 0.022
RUNG_HEIGHT = 0.014
RUNG_ZS = (0.055, 0.145, 0.255, 0.365)
LEFT_SUPPORT_Z = 0.14
RIGHT_SUPPORT_Z = 0.30
SUPPORT_X = 0.072
SUPPORT_OUTER_SPAN_Y = 0.044
SUPPORT_HEIGHT = 0.058
SUPPORT_INWARD_REACH = 0.012
SUPPORT_NOSE_WIDTH = 0.026
SUPPORT_NOSE_HEIGHT = 0.038
SUPPORT_BACKPLATE_THICKNESS = 0.006
LEFT_ARM_REACH = 0.088
RIGHT_ARM_REACH = 0.138
ROOT_PAD_LENGTH = 0.010
ROOT_HEEL_RADIUS = 0.012
def _frame_shape() -> cq.Workplane:
    rung_length = FRAME_WIDTH - 2.0 * RAIL_WIDTH + 0.004
    rail_x = FRAME_WIDTH / 2.0 - RAIL_WIDTH / 2.0

    solids = [
        cq.Workplane("XY")
        .box(RAIL_WIDTH, FRAME_DEPTH, FRAME_HEIGHT)
        .translate((rail_x, 0.0, FRAME_HEIGHT / 2.0))
        .val(),
        cq.Workplane("XY")
        .box(RAIL_WIDTH, FRAME_DEPTH, FRAME_HEIGHT)
        .translate((-rail_x, 0.0, FRAME_HEIGHT / 2.0))
        .val(),
    ]

    for z in RUNG_ZS:
        solids.append(
            cq.Workplane("XY")
            .box(rung_length, RUNG_DEPTH, RUNG_HEIGHT)
            .translate((0.0, 0.0, z))
            .val()
        )

    frame = cq.Workplane(obj=solids[0])
    for solid in solids[1:]:
        frame = frame.union(cq.Workplane(obj=solid))

    return frame
def _cheek_block_shape(side: int) -> cq.Workplane:
    cheek_face = (
        cq.Workplane("XY")
        .box(SUPPORT_INWARD_REACH * 0.45, SUPPORT_NOSE_WIDTH, SUPPORT_NOSE_HEIGHT)
        .translate((side * (SUPPORT_INWARD_REACH * 0.225), 0.0, 0.0))
    )
    backplate = (
        cq.Workplane("XY")
        .box(SUPPORT_BACKPLATE_THICKNESS, SUPPORT_OUTER_SPAN_Y, SUPPORT_HEIGHT)
        .translate(
            (
                side * (SUPPORT_INWARD_REACH - SUPPORT_BACKPLATE_THICKNESS / 2.0),
                0.0,
                0.0,
            )
        )
    )
    web = (
        cq.Workplane("XZ")
        .moveTo(0.0, -SUPPORT_NOSE_HEIGHT / 2.0)
        .lineTo(0.0, SUPPORT_NOSE_HEIGHT / 2.0)
        .lineTo(side * (SUPPORT_INWARD_REACH - SUPPORT_BACKPLATE_THICKNESS), SUPPORT_HEIGHT / 2.0)
        .lineTo(side * (SUPPORT_INWARD_REACH - SUPPORT_BACKPLATE_THICKNESS), -SUPPORT_HEIGHT / 2.0)
        .close()
        .extrude(SUPPORT_NOSE_WIDTH * 0.42, both=True)
    )
    return cheek_face.union(backplate).union(web)
def _arm_shape(direction: int, reach: float, arm_width: float, arm_thickness: float) -> cq.Workplane:
    beam_center_x = direction * (ROOT_PAD_LENGTH + reach / 2.0)
    tip_center_x = direction * (ROOT_PAD_LENGTH + reach)
    heel_center_x = direction * ROOT_HEEL_RADIUS

    root_pad = (
        cq.Workplane("XY")
        .box(ROOT_PAD_LENGTH, arm_width, arm_thickness)
        .translate((direction * (ROOT_PAD_LENGTH / 2.0), 0.0, 0.0))
    )
    heel = (
        cq.Workplane("XZ")
        .circle(ROOT_HEEL_RADIUS)
        .extrude(arm_width / 2.0, both=True)
        .translate((heel_center_x, 0.0, 0.0))
    )
    beam = (
        cq.Workplane("XY")
        .box(reach, arm_width, arm_thickness * 0.86)
        .translate((beam_center_x, 0.0, 0.0))
    )
    tip = (
        cq.Workplane("XZ")
        .circle(arm_thickness * 0.44)
        .extrude(arm_width / 2.0, both=True)
        .translate((tip_center_x, 0.0, 0.0))
    )
    brace = (
        cq.Workplane("XZ")
        .moveTo(direction * ROOT_PAD_LENGTH, -arm_thickness * 0.43)
        .lineTo(direction * (ROOT_PAD_LENGTH + reach * 0.46), -arm_thickness * 0.43)
        .lineTo(direction * (ROOT_PAD_LENGTH + reach * 0.22), arm_thickness * 0.58)
        .close()
        .extrude(arm_width * 0.34, both=True)
    )

    return root_pad.union(heel).union(beam).union(tip).union(brace)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="ladder_frame_two_branch_fixture")

    frame_mat = model.material("frame_graphite", rgba=(0.20, 0.22, 0.24, 1.0))
    cheek_mat = model.material("cheek_steel", rgba=(0.42, 0.45, 0.49, 1.0))
    arm_mat = model.material("arm_amber", rgba=(0.72, 0.50, 0.18, 1.0))

    frame = model.part("frame")
    frame.visual(
        mesh_from_cadquery(_frame_shape(), "frame_shell"),
        origin=Origin(),
        material=frame_mat,
        name="frame_shell",
    )

    left_cheek = model.part("left_cheek")
    left_cheek.visual(
        mesh_from_cadquery(_cheek_block_shape(side=1), "left_cheek_shell"),
        origin=Origin(),
        material=cheek_mat,
        name="left_cheek_shell",
    )

    right_cheek = model.part("right_cheek")
    right_cheek.visual(
        mesh_from_cadquery(_cheek_block_shape(side=-1), "right_cheek_shell"),
        origin=Origin(),
        material=cheek_mat,
        name="right_cheek_shell",
    )

    left_arm = model.part("left_arm")
    left_arm.visual(
        mesh_from_cadquery(
            _arm_shape(direction=-1, reach=LEFT_ARM_REACH, arm_width=0.016, arm_thickness=0.018),
            "left_arm_shell",
        ),
        origin=Origin(),
        material=arm_mat,
        name="left_arm_shell",
    )

    right_arm = model.part("right_arm")
    right_arm.visual(
        mesh_from_cadquery(
            _arm_shape(direction=1, reach=RIGHT_ARM_REACH, arm_width=0.018, arm_thickness=0.022),
            "right_arm_shell",
        ),
        origin=Origin(),
        material=arm_mat,
        name="right_arm_shell",
    )

    model.articulation(
        "frame_to_left_cheek",
        ArticulationType.FIXED,
        parent=frame,
        child=left_cheek,
        origin=Origin(xyz=(-SUPPORT_X, 0.0, LEFT_SUPPORT_Z)),
    )
    model.articulation(
        "frame_to_right_cheek",
        ArticulationType.FIXED,
        parent=frame,
        child=right_cheek,
        origin=Origin(xyz=(SUPPORT_X, 0.0, RIGHT_SUPPORT_Z)),
    )
    model.articulation(
        "left_cheek_to_left_arm",
        ArticulationType.REVOLUTE,
        parent=left_cheek,
        child=left_arm,
        origin=Origin(),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.35, upper=1.05),
    )
    model.articulation(
        "right_cheek_to_right_arm",
        ArticulationType.REVOLUTE,
        parent=right_cheek,
        child=right_arm,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.20, upper=1.10),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
