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
import math
import cadquery as cq
SPINE_SIZE = (0.09, 0.07, 0.42)
LOWER_JOINT_ORIGIN = (0.0, -0.118, 0.108)
FORWARD_JOINT_ORIGIN = (0.082, 0.0, 0.226)
UPPER_JOINT_ORIGIN = (0.0, 0.128, 0.318)
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _x_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("YZ", origin=(center[0] - (length / 2.0), center[1], center[2]))
        .circle(radius)
        .extrude(length)
    )
def _y_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("XY", origin=(0.0, 0.0, -(length / 2.0)))
        .circle(radius)
        .extrude(length)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate(center)
    )
def _z_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("XY", origin=(center[0], center[1], center[2] - (length / 2.0)))
        .circle(radius)
        .extrude(length)
    )
def _spine_column() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(*SPINE_SIZE)
        .edges("|Z")
        .fillet(0.008)
        .edges(">Z")
        .fillet(0.003)
        .translate((0.0, 0.0, SPINE_SIZE[2] / 2.0))
    )
def _lower_housing() -> cq.Workplane:
    strap = _box((0.086, 0.038, 0.088), (0.0, -0.054, 0.108))
    trunnion = _x_cylinder(0.024, 0.074, (0.0, -0.094, 0.108))
    rear_web = _box((0.052, 0.020, 0.056), (0.0, -0.074, 0.108))
    return strap.union(trunnion).union(rear_web)
def _forward_housing() -> cq.Workplane:
    collar = _box((0.050, 0.078, 0.058), (0.070, 0.0, 0.175))
    pedestal = _box((0.032, 0.052, 0.028), (0.082, 0.0, 0.204))
    stub = _z_cylinder(0.024, 0.022, (0.082, 0.0, 0.215))
    return collar.union(pedestal).union(stub)
def _upper_housing() -> cq.Workplane:
    strap = _box((0.080, 0.044, 0.072), (0.0, 0.052, 0.318))
    shaft_boss = _y_cylinder(0.022, 0.060, (0.0, 0.098, 0.318))
    lower_web = _box((0.046, 0.032, 0.048), (0.0, 0.061, 0.300))
    return strap.union(shaft_boss).union(lower_web)
def _lower_pivot() -> cq.Workplane:
    return _x_cylinder(0.018, 0.062, (0.0, -0.018, 0.0))
def _lower_beam() -> cq.Workplane:
    beam = _box((0.034, 0.150, 0.026), (0.0, -0.095, 0.0))
    rib = _box((0.024, 0.090, 0.040), (0.0, -0.092, -0.012))
    return beam.union(rib)
def _slot_pad() -> cq.Workplane:
    neck = _box((0.050, 0.024, 0.036), (0.0, -0.174, 0.0))
    plate = _box((0.092, 0.014, 0.064), (0.0, -0.194, 0.0))
    pad = neck.union(plate)
    for x_offset in (-0.026, 0.026):
        slot = (
            cq.Workplane("XZ", origin=(x_offset, -0.203, 0.0))
            .slot2D(0.024, 0.010, angle=90)
            .extrude(0.018)
        )
        pad = pad.cut(slot)
    return pad
def _forward_base() -> cq.Workplane:
    return _z_cylinder(0.028, 0.018, (0.0, 0.0, 0.009))
def _forward_beam() -> cq.Workplane:
    root_block = _box((0.040, 0.056, 0.020), (0.020, 0.0, 0.012))
    main_beam = _box((0.148, 0.034, 0.024), (0.094, 0.0, 0.020))
    rib_profile = (
        cq.Workplane("XZ", origin=(0.008, -0.009, 0.0))
        .polyline([(0.0, 0.0), (0.076, 0.0), (0.0, 0.028)])
        .close()
        .extrude(0.018)
    )
    return root_block.union(main_beam).union(rib_profile)
def _round_pad() -> cq.Workplane:
    neck = _box((0.038, 0.028, 0.030), (0.177, 0.0, 0.022))
    flange = _x_cylinder(0.042, 0.014, (0.198, 0.0, 0.022))
    pad = neck.union(flange)
    pad = pad.cut(_x_cylinder(0.011, 0.018, (0.198, 0.0, 0.022)))
    for angle in (0.0, (2.0 * math.pi) / 3.0, (4.0 * math.pi) / 3.0):
        y = 0.026 * math.cos(angle)
        z = 0.022 + (0.026 * math.sin(angle))
        pad = pad.cut(_x_cylinder(0.004, 0.018, (0.198, y, z)))
    return pad
def _upper_shaft_base() -> cq.Workplane:
    return _y_cylinder(0.018, 0.026, (0.0, 0.013, 0.0))
def _upper_shaft() -> cq.Workplane:
    return _y_cylinder(0.014, 0.144, (0.0, 0.098, 0.0))
def _fork_pad() -> cq.Workplane:
    riser = _box((0.020, 0.030, 0.052), (0.0, 0.158, 0.026))
    bridge = _box((0.030, 0.022, 0.024), (0.0, 0.182, 0.052))
    jaw_left = _box((0.014, 0.026, 0.056), (-0.025, 0.194, 0.052))
    jaw_right = _box((0.014, 0.026, 0.056), (0.025, 0.194, 0.052))
    pad = riser.union(bridge).union(jaw_left).union(jaw_right)
    pad = pad.cut(_x_cylinder(0.004, 0.020, (-0.025, 0.194, 0.052)))
    pad = pad.cut(_x_cylinder(0.004, 0.020, (0.025, 0.194, 0.052)))
    return pad
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="inspection_fixture_head")

    frame_mat = model.material("frame_graphite", rgba=(0.24, 0.26, 0.29, 1.0))
    arm_mat = model.material("machined_aluminum", rgba=(0.63, 0.66, 0.70, 1.0))
    pad_mat = model.material("tool_steel", rgba=(0.72, 0.74, 0.76, 1.0))

    spine = model.part("spine")
    spine.visual(
        mesh_from_cadquery(_spine_column(), "spine_column"),
        material=frame_mat,
        name="spine_column",
    )
    spine.visual(
        mesh_from_cadquery(_lower_housing(), "lower_housing"),
        material=frame_mat,
        name="lower_housing",
    )
    spine.visual(
        mesh_from_cadquery(_forward_housing(), "forward_housing"),
        material=frame_mat,
        name="forward_housing",
    )
    spine.visual(
        mesh_from_cadquery(_upper_housing(), "upper_housing"),
        material=frame_mat,
        name="upper_housing",
    )

    lower_arm = model.part("lower_arm")
    lower_arm.visual(
        mesh_from_cadquery(_lower_pivot(), "lower_pivot"),
        material=arm_mat,
        name="lower_pivot",
    )
    lower_arm.visual(
        mesh_from_cadquery(_lower_beam(), "lower_beam"),
        material=arm_mat,
        name="lower_beam",
    )
    lower_arm.visual(
        mesh_from_cadquery(_slot_pad(), "slot_pad"),
        material=pad_mat,
        name="slot_pad",
    )

    forward_arm = model.part("forward_arm")
    forward_arm.visual(
        mesh_from_cadquery(_forward_base(), "forward_base"),
        material=arm_mat,
        name="forward_base",
    )
    forward_arm.visual(
        mesh_from_cadquery(_forward_beam(), "forward_beam"),
        material=arm_mat,
        name="forward_beam",
    )
    forward_arm.visual(
        mesh_from_cadquery(_round_pad(), "round_pad"),
        material=pad_mat,
        name="round_pad",
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(_upper_shaft_base(), "upper_shaft_base"),
        material=arm_mat,
        name="upper_shaft_base",
    )
    upper_arm.visual(
        mesh_from_cadquery(_upper_shaft(), "upper_shaft"),
        material=arm_mat,
        name="upper_shaft",
    )
    upper_arm.visual(
        mesh_from_cadquery(_fork_pad(), "fork_pad"),
        material=pad_mat,
        name="fork_pad",
    )

    model.articulation(
        "spine_to_lower_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=lower_arm,
        origin=Origin(xyz=LOWER_JOINT_ORIGIN),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.8,
            lower=-0.75,
            upper=0.55,
        ),
    )
    model.articulation(
        "spine_to_forward_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=forward_arm,
        origin=Origin(xyz=FORWARD_JOINT_ORIGIN),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=14.0,
            velocity=1.6,
            lower=-1.05,
            upper=1.05,
        ),
    )
    model.articulation(
        "spine_to_upper_arm",
        ArticulationType.REVOLUTE,
        parent=spine,
        child=upper_arm,
        origin=Origin(xyz=UPPER_JOINT_ORIGIN),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.4,
            lower=-1.35,
            upper=1.35,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
