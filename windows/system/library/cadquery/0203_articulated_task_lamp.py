# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

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
from math import pi
import cadquery as cq
ARM_LENGTH = 0.54
HEAD_LINK_LENGTH = 0.15
def _box(center: tuple[float, float, float], size: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _y_cylinder(center: tuple[float, float, float], radius: float, length: float) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length, both=True).translate(center)
def _z_cylinder(center: tuple[float, float, float], radius: float, length: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length, both=True).translate(center)
def _yoke(
    *,
    center_x: float,
    depth_x: float,
    cheek_thickness: float,
    gap_width: float,
    height_z: float,
    bridge_thickness_x: float,
    bridge_height_z: float,
    bore_radius: float,
) -> cq.Workplane:
    cheek_offset_y = gap_width / 2.0 + cheek_thickness / 2.0
    bridge_center_x = center_x - 0.5 * (depth_x - bridge_thickness_x)
    bridge_center_z = -height_z / 2.0 + bridge_height_z / 2.0

    yoke = _box((center_x, cheek_offset_y, 0.0), (depth_x, cheek_thickness, height_z))
    yoke = yoke.union(_box((center_x, -cheek_offset_y, 0.0), (depth_x, cheek_thickness, height_z)))
    yoke = yoke.union(
        _box(
            (bridge_center_x, 0.0, bridge_center_z),
            (bridge_thickness_x, gap_width + 2.0 * cheek_thickness, bridge_height_z),
        )
    )
    return yoke.cut(_y_cylinder((center_x, 0.0, 0.0), bore_radius, gap_width + 2.0 * cheek_thickness + 0.01))
def _clamp_body_shape() -> cq.Workplane:
    spine = _box((0.003, 0.0, -0.066), (0.028, 0.034, 0.108))
    top_jaw = _box((-0.047, 0.0, -0.020), (0.078, 0.034, 0.014))
    lower_carriage = _box((-0.026, 0.0, -0.096), (0.060, 0.034, 0.024))
    screw = _z_cylinder((-0.045, 0.0, -0.082), 0.006, 0.068)
    pressure_pad = _z_cylinder((-0.045, 0.0, -0.051), 0.011, 0.004)
    knob_wheel = _z_cylinder((-0.045, 0.0, -0.120), 0.018, 0.008)
    knob_crossbar = _y_cylinder((-0.045, 0.0, -0.120), 0.004, 0.044)

    clamp = spine.union(top_jaw)
    clamp = clamp.union(lower_carriage)
    clamp = clamp.union(screw)
    clamp = clamp.union(pressure_pad)
    clamp = clamp.union(knob_wheel)
    clamp = clamp.union(knob_crossbar)
    return clamp
def _clamp_yoke_shape() -> cq.Workplane:
    return _yoke(
        center_x=0.0,
        depth_x=0.026,
        cheek_thickness=0.010,
        gap_width=0.019,
        height_z=0.028,
        bridge_thickness_x=0.012,
        bridge_height_z=0.004,
        bore_radius=0.0045,
    )
def _arm_knuckle_shape() -> cq.Workplane:
    shoulder_boss = _y_cylinder((0.0, 0.0, 0.0), 0.0085, 0.017)
    root_neck = _box((0.021, 0.0, 0.0), (0.026, 0.014, 0.012))
    return shoulder_boss.union(root_neck)
def _arm_body_shape() -> cq.Workplane:
    beam = _box((0.285, 0.0, 0.0), (0.510, 0.022, 0.014)).edges("|X").fillet(0.0025)
    elbow_yoke = _yoke(
        center_x=ARM_LENGTH,
        depth_x=0.022,
        cheek_thickness=0.009,
        gap_width=0.016,
        height_z=0.024,
        bridge_thickness_x=0.010,
        bridge_height_z=0.003,
        bore_radius=0.0040,
    )
    return beam.union(elbow_yoke)
def _head_link_knuckle_shape() -> cq.Workplane:
    root_boss = _y_cylinder((0.0, 0.0, 0.0), 0.0075, 0.014)
    root_neck = _box((0.0175, 0.0, 0.0), (0.021, 0.011, 0.010))
    return root_boss.union(root_neck)
def _head_link_body_shape() -> cq.Workplane:
    beam = _box((0.087, 0.0, 0.0), (0.126, 0.018, 0.012)).edges("|X").fillet(0.0020)
    head_yoke = _yoke(
        center_x=HEAD_LINK_LENGTH,
        depth_x=0.020,
        cheek_thickness=0.009,
        gap_width=0.017,
        height_z=0.022,
        bridge_thickness_x=0.009,
        bridge_height_z=0.003,
        bore_radius=0.0040,
    )
    return beam.union(head_yoke)
def _lamp_head_knuckle_shape() -> cq.Workplane:
    rear_boss = _y_cylinder((0.0, 0.0, 0.0), 0.0075, 0.015)
    rear_neck = _box((0.0155, 0.0, 0.0), (0.017, 0.012, 0.010))
    return rear_boss.union(rear_neck)
def _lamp_head_body_shape() -> cq.Workplane:
    rear_housing = _box((0.044, 0.0, 0.0), (0.052, 0.044, 0.019)).edges("|X").fillet(0.0025)
    bar_body = _box((0.175, 0.0, 0.0), (0.310, 0.052, 0.013)).edges("|X").fillet(0.0035)
    return rear_housing.union(bar_body)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="task_lamp")

    graphite = model.material("graphite", rgba=(0.20, 0.22, 0.25, 1.0))
    joint_black = model.material("joint_black", rgba=(0.12, 0.13, 0.14, 1.0))
    diffuser = model.material("diffuser", rgba=(0.90, 0.92, 0.88, 0.95))

    clamp = model.part("clamp")
    clamp.visual(
        mesh_from_cadquery(_clamp_body_shape(), "lamp_clamp_body"),
        material=graphite,
        name="clamp_shell",
    )
    clamp.visual(
        mesh_from_cadquery(_clamp_yoke_shape(), "lamp_clamp_yoke"),
        material=joint_black,
        name="shoulder_yoke",
    )

    arm = model.part("arm")
    arm.visual(
        mesh_from_cadquery(_arm_knuckle_shape(), "lamp_arm_knuckle"),
        material=joint_black,
        name="shoulder_knuckle",
    )
    arm.visual(
        mesh_from_cadquery(_arm_body_shape(), "lamp_arm_body"),
        material=graphite,
        name="arm_shell",
    )

    head_link = model.part("head_link")
    head_link.visual(
        mesh_from_cadquery(_head_link_knuckle_shape(), "lamp_head_link_knuckle"),
        material=joint_black,
        name="link_knuckle",
    )
    head_link.visual(
        mesh_from_cadquery(_head_link_body_shape(), "lamp_head_link_body"),
        material=joint_black,
        name="link_shell",
    )

    lamp_head = model.part("lamp_head")
    lamp_head.visual(
        mesh_from_cadquery(_lamp_head_knuckle_shape(), "lamp_head_knuckle"),
        material=joint_black,
        name="head_knuckle",
    )
    lamp_head.visual(
        mesh_from_cadquery(_lamp_head_body_shape(), "lamp_head_body"),
        material=graphite,
        name="head_shell",
    )
    lamp_head.visual(
        Box((0.272, 0.030, 0.0025)),
        origin=Origin(xyz=(0.180, 0.0, -0.0055)),
        material=diffuser,
        name="diffuser",
    )

    model.articulation(
        "clamp_to_arm",
        ArticulationType.REVOLUTE,
        parent=clamp,
        child=arm,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.6,
            lower=-0.95,
            upper=1.20,
        ),
    )
    model.articulation(
        "arm_to_head_link",
        ArticulationType.REVOLUTE,
        parent=arm,
        child=head_link,
        origin=Origin(xyz=(ARM_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=14.0,
            velocity=1.8,
            lower=-1.10,
            upper=1.15,
        ),
    )
    model.articulation(
        "head_link_to_lamp_head",
        ArticulationType.REVOLUTE,
        parent=head_link,
        child=lamp_head,
        origin=Origin(xyz=(HEAD_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.2,
            lower=-0.95,
            upper=0.75,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
