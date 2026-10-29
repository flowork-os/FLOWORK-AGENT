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
BASE_W = 0.28
BASE_D = 0.24
BASE_T = 0.025
MAST_W = 0.12
MAST_D = 0.10
MAST_H = 0.62
MAST_WALL = 0.008
MAST_TOP_CAP = 0.01
LOWER_Z = 0.185
MID_Z = 0.355
UPPER_Z = 0.525
UPPER_SUPPORT_LEN = 0.080
UPPER_SUPPORT_W = 0.074
UPPER_SUPPORT_H = 0.062
MID_SUPPORT_LEN = 0.080
MID_SUPPORT_W = 0.096
MID_SUPPORT_H = 0.060
LOWER_SUPPORT_LEN = 0.080
LOWER_SUPPORT_W = 0.058
LOWER_SUPPORT_H = 0.052
def box_at(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def box_span(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    z0: float,
    z1: float,
) -> cq.Workplane:
    return box_at(
        (x1 - x0, y1 - y0, z1 - z0),
        ((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0),
    )
def cylinder_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length).translate(
        (center[0] - length / 2.0, center[1], center[2])
    )
def cylinder_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length).translate(
        (center[0], center[1] - length / 2.0, center[2])
    )
def build_mast_assembly() -> cq.Workplane:
    base = box_at((BASE_W, BASE_D, BASE_T), (0.0, 0.0, BASE_T / 2.0))

    mast_outer = box_at((MAST_W, MAST_D, MAST_H), (0.0, 0.0, BASE_T + MAST_H / 2.0))
    inner_height = MAST_H - MAST_TOP_CAP - 0.006
    mast_inner = box_at(
        (MAST_W - 2.0 * MAST_WALL, MAST_D - 2.0 * MAST_WALL, inner_height),
        (0.0, 0.0, BASE_T + 0.003 + inner_height / 2.0),
    )
    mast = mast_outer.cut(mast_inner)

    front_gusset = box_at((0.07, 0.012, 0.09), (0.0, 0.035, BASE_T + 0.045))
    rear_gusset = box_at((0.07, 0.012, 0.09), (0.0, -0.035, BASE_T + 0.045))

    upper_block = box_at(
        (UPPER_SUPPORT_LEN, UPPER_SUPPORT_W, UPPER_SUPPORT_H),
        (MAST_W / 2.0 + UPPER_SUPPORT_LEN / 2.0, 0.0, UPPER_Z),
    )
    upper_cap = cylinder_x(
        0.018,
        0.008,
        (MAST_W / 2.0 + UPPER_SUPPORT_LEN + 0.004, 0.0, UPPER_Z),
    )

    mid_block = box_at(
        (MID_SUPPORT_W, MID_SUPPORT_LEN, MID_SUPPORT_H),
        (0.0, MAST_D / 2.0 + MID_SUPPORT_LEN / 2.0, MID_Z),
    )
    mid_web_left = box_at((0.02, 0.02, 0.05), (-0.03, MAST_D / 2.0 + 0.01, MID_Z - 0.01))
    mid_web_right = box_at((0.02, 0.02, 0.05), (0.03, MAST_D / 2.0 + 0.01, MID_Z - 0.01))

    lower_pad = box_at(
        (LOWER_SUPPORT_LEN, 0.024, LOWER_SUPPORT_H),
        (-MAST_W / 2.0 - LOWER_SUPPORT_LEN / 2.0, 0.0, LOWER_Z),
    )
    lower_top_ear = box_at(
        (LOWER_SUPPORT_LEN * 0.75, LOWER_SUPPORT_W, 0.012),
        (-MAST_W / 2.0 - LOWER_SUPPORT_LEN * 0.375, 0.0, LOWER_Z + LOWER_SUPPORT_H / 2.0 - 0.006),
    )
    lower_bottom_ear = box_at(
        (LOWER_SUPPORT_LEN * 0.75, LOWER_SUPPORT_W, 0.012),
        (-MAST_W / 2.0 - LOWER_SUPPORT_LEN * 0.375, 0.0, LOWER_Z - LOWER_SUPPORT_H / 2.0 + 0.006),
    )

    assembly = (
        base.union(mast)
        .union(front_gusset)
        .union(rear_gusset)
        .union(upper_block)
        .union(upper_cap)
        .union(mid_block)
        .union(mid_web_left)
        .union(mid_web_right)
        .union(lower_pad)
        .union(lower_top_ear)
        .union(lower_bottom_ear)
    )

    return assembly
def build_fork_branch() -> cq.Workplane:
    x_off = 0.008
    collar = cylinder_x(0.014, 0.010, (0.005 + x_off, 0.0, 0.0))
    root_block = box_span(0.006 + x_off, 0.024 + x_off, -0.016, 0.026, -0.015, 0.015)
    spine = box_span(0.010 + x_off, 0.030 + x_off, 0.000, 0.164, -0.012, 0.012)
    tine_upper = box_span(0.008 + x_off, 0.022 + x_off, 0.164, 0.205, 0.010, 0.031)
    tine_lower = box_span(0.008 + x_off, 0.022 + x_off, 0.164, 0.205, -0.031, -0.010)
    return collar.union(root_block).union(spine).union(tine_upper).union(tine_lower)
def build_plate_branch() -> cq.Workplane:
    plate_t = 0.014
    y_off = 0.010
    collar = cylinder_y(0.013, 0.010, (0.0, 0.005 + y_off, 0.0))
    root_pad = box_span(-0.032, 0.0, 0.000 + y_off, 0.012 + y_off, -0.026, 0.026)
    plate_y = 0.012 + y_off
    profile = (
        cq.Workplane("XZ")
        .moveTo(0.0, -0.03)
        .lineTo(-0.07, -0.034)
        .lineTo(-0.22, -0.016)
        .threePointArc((-0.248, 0.008), (-0.222, 0.036))
        .lineTo(-0.10, 0.048)
        .lineTo(-0.02, 0.03)
        .close()
        .extrude(plate_t)
        .translate((0.0, plate_y, 0.0))
    )
    lightening_slot = (
        cq.Workplane("XZ")
        .slot2D(0.105, 0.02, 0)
        .extrude(plate_t + 0.002)
        .translate((-0.125, plate_y + 0.001, 0.006))
    )
    tip_hole = (
        cq.Workplane("XZ")
        .circle(0.012)
        .extrude(plate_t + 0.002)
        .translate((-0.205, plate_y + 0.001, 0.01))
    )
    return collar.union(root_pad).union(profile.cut(lightening_slot).cut(tip_hole))
def build_yoke_branch() -> cq.Workplane:
    collar = cylinder_x(0.013, 0.010, (-0.005, 0.0, 0.0))
    root_block = box_span(-0.024, -0.006, -0.026, 0.016, -0.015, 0.015)
    spine = box_span(-0.028, -0.010, -0.145, 0.000, -0.011, 0.011)
    tine_upper = box_span(-0.026, -0.012, -0.145, -0.104, 0.010, 0.030)
    tine_lower = box_span(-0.026, -0.012, -0.145, -0.104, -0.030, -0.010)
    return collar.union(root_block).union(spine).union(tine_upper).union(tine_lower)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tooling_tree")

    mast_finish = model.material("mast_finish", rgba=(0.22, 0.24, 0.26, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.57, 0.59, 0.62, 1.0))
    pin_finish = model.material("pin_finish", rgba=(0.72, 0.74, 0.77, 1.0))

    mast = model.part("mast")
    mast.visual(
        mesh_from_cadquery(build_mast_assembly(), "mast_assembly"),
        origin=Origin(),
        material=mast_finish,
        name="mast_body",
    )

    fork_branch = model.part("fork_branch")
    fork_branch.visual(
        mesh_from_cadquery(build_fork_branch(), "fork_branch_arm"),
        origin=Origin(),
        material=arm_finish,
        name="fork_arm",
    )

    plate_branch = model.part("plate_branch")
    plate_branch.visual(
        mesh_from_cadquery(build_plate_branch(), "plate_branch_arm"),
        origin=Origin(),
        material=arm_finish,
        name="plate_arm",
    )

    yoke_branch = model.part("yoke_branch")
    yoke_branch.visual(
        mesh_from_cadquery(build_yoke_branch(), "yoke_branch_arm"),
        origin=Origin(),
        material=arm_finish,
        name="yoke_arm",
    )

    model.articulation(
        "mast_to_fork_branch",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=fork_branch,
        origin=Origin(
            xyz=(
                MAST_W / 2.0 + UPPER_SUPPORT_LEN,
                0.0,
                UPPER_Z,
            )
        ),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=1.5, lower=-0.85, upper=0.95),
    )
    model.articulation(
        "mast_to_plate_branch",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=plate_branch,
        origin=Origin(
            xyz=(
                0.0,
                MAST_D / 2.0 + MID_SUPPORT_LEN,
                MID_Z,
            )
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=1.4, lower=-0.75, upper=0.85),
    )
    model.articulation(
        "mast_to_yoke_branch",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=yoke_branch,
        origin=Origin(
            xyz=(
                -MAST_W / 2.0 - LOWER_SUPPORT_LEN,
                0.0,
                LOWER_Z,
            )
        ),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.6, lower=-0.95, upper=0.7),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
