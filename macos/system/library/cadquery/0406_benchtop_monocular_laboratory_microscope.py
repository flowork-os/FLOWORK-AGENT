# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, benchtop_monocular_laboratory_microscope, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: benchtop_monocular_laboratory_microscope

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
BASE_X = 0.190
BASE_Y = 0.145
BASE_Z = 0.028
COLUMN_X = 0.022
COLUMN_Y = 0.024
COLUMN_H = 0.205
COLUMN_Y_CENTER = 0.022
BODY_HOME_Z = 0.155
BODY_TRAVEL = 0.032
STAGE_Z = 0.086
STAGE_TRAVEL = 0.018
STAGE_Y_OFFSET = -0.040
BODY_COLUMN_FACE_Y = COLUMN_Y_CENTER - (COLUMN_Y / 2.0) - 0.001
def _stand_shape():
    base = (
        cq.Workplane("XY")
        .box(BASE_X, BASE_Y, BASE_Z)
        .translate((0.0, 0.0, BASE_Z / 2.0))
        .edges("|Z")
        .fillet(0.010)
    )

    pedestal = (
        cq.Workplane("XY")
        .box(0.078, 0.060, 0.014)
        .translate((0.0, 0.010, BASE_Z + 0.007))
        .edges("|Z")
        .fillet(0.006)
    )

    column = cq.Workplane("XY").box(COLUMN_X, COLUMN_Y, COLUMN_H).translate(
        (0.0, COLUMN_Y_CENTER, BASE_Z + (COLUMN_H / 2.0))
    )

    arm = (
        cq.Workplane("YZ")
        .moveTo(0.052, BASE_Z)
        .lineTo(0.052, 0.070)
        .threePointArc((0.045, 0.145), (0.034, 0.228))
        .lineTo(0.020, 0.228)
        .threePointArc((0.028, 0.148), (0.036, 0.066))
        .lineTo(0.036, BASE_Z)
        .close()
        .extrude(0.018)
        .translate((0.030, 0.0, 0.0))
    )

    top_bridge = cq.Workplane("XY").box(0.040, 0.016, 0.012).translate(
        (0.020, COLUMN_Y_CENTER + 0.002, 0.227)
    )

    return base.union(pedestal).union(column).union(arm).union(top_bridge)
def _stage_bracket_shape():
    bridge = cq.Workplane("XY").box(0.096, 0.060, 0.010).translate((0.0, 0.0, -0.009))
    left_rail = cq.Workplane("XY").box(0.088, 0.010, 0.008).translate((0.0, -0.029, -0.004))
    right_rail = cq.Workplane("XY").box(0.088, 0.010, 0.008).translate((0.0, 0.029, -0.004))
    mount_neck = cq.Workplane("XY").box(0.022, 0.034, 0.014).translate((0.0, 0.024, -0.012))
    column_mount = cq.Workplane("XY").box(0.028, 0.010, 0.024).translate((0.0, 0.044, -0.012))
    side_housing = cq.Workplane("XY").box(0.018, 0.046, 0.024).translate((0.054, 0.0, -0.012))
    return (
        bridge.union(left_rail)
        .union(right_rail)
        .union(mount_neck)
        .union(column_mount)
        .union(side_housing)
    )
def _stage_shape():
    plate = cq.Workplane("XY").box(0.120, 0.095, 0.006).translate((0.0, 0.0, 0.015))
    window_cut = cq.Workplane("XY").box(0.032, 0.026, 0.010).translate((0.0, 0.0, 0.015))
    connector = cq.Workplane("XY").box(0.040, 0.050, 0.014).translate((0.0, 0.0, 0.007))
    left_shoe = cq.Workplane("XY").box(0.055, 0.012, 0.004).translate((0.0, -0.029, 0.002))
    right_shoe = cq.Workplane("XY").box(0.055, 0.012, 0.004).translate((0.0, 0.029, 0.002))
    return plate.cut(window_cut).union(connector).union(left_shoe).union(right_shoe)
def _turret_shape():
    disk = cq.Workplane("XY").circle(0.020).extrude(0.010).translate((0.0, 0.0, -0.010))
    hub = cq.Workplane("XY").circle(0.010).extrude(0.004).translate((0.0, 0.0, -0.008))
    turret = disk.union(hub)

    for x_pos, y_pos in (
        (0.014, 0.000),
        (-0.007, 0.012),
        (-0.007, -0.012),
    ):
        barrel = cq.Workplane("XY").circle(0.006).extrude(0.024).translate((x_pos, y_pos, -0.034))
        turret = turret.union(barrel)

    return turret
def _ring_knob_shape(outer_radius: float, inner_radius: float, length: float):
    return cq.Workplane("YZ").circle(outer_radius).circle(inner_radius).extrude(length)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="lab_monocular_microscope")

    model.material("stand_cream", rgba=(0.92, 0.91, 0.84, 1.0))
    model.material("stage_black", rgba=(0.12, 0.13, 0.14, 1.0))
    model.material("knob_black", rgba=(0.10, 0.10, 0.11, 1.0))
    model.material("metal_dark", rgba=(0.28, 0.29, 0.31, 1.0))
    model.material("metal_light", rgba=(0.74, 0.76, 0.79, 1.0))
    model.material("glass_dark", rgba=(0.18, 0.22, 0.24, 0.55))

    stand = model.part("stand")
    stand.visual(
        mesh_from_cadquery(_stand_shape(), "microscope_stand"),
        material="stand_cream",
        name="stand_shell",
    )
    stand.visual(
        Box((0.028, 0.006, 0.024)),
        origin=Origin(xyz=(0.0, 0.012, STAGE_Z - 0.012)),
        material="stand_cream",
        name="stage_mount_pad",
    )
    stand.visual(
        Box((0.026, 0.006, 0.110)),
        origin=Origin(xyz=(0.0, 0.012, BODY_HOME_Z + (BODY_TRAVEL / 2.0))),
        material="stand_cream",
        name="body_guide",
    )

    stage_bracket = model.part("stage_bracket")
    stage_bracket.visual(
        mesh_from_cadquery(_stage_bracket_shape(), "microscope_stage_bracket"),
        material="metal_dark",
        name="stage_bracket_shell",
    )
    stage_bracket.visual(
        Cylinder(radius=0.014, length=0.010),
        origin=Origin(xyz=(0.065, 0.0, -0.012), rpy=(0.0, pi / 2.0, 0.0)),
        material="metal_dark",
        name="knob_boss",
    )

    stage = model.part("stage")
    stage.visual(
        mesh_from_cadquery(_stage_shape(), "microscope_stage"),
        material="stage_black",
        name="stage_plate",
    )
    stage.visual(
        Box((0.006, 0.032, 0.002)),
        origin=Origin(xyz=(-0.034, 0.0, 0.019)),
        material="metal_light",
        name="clip_0",
    )
    stage.visual(
        Box((0.006, 0.032, 0.002)),
        origin=Origin(xyz=(0.034, 0.0, 0.019)),
        material="metal_light",
        name="clip_1",
    )

    body = model.part("body")
    body.visual(
        Box((0.026, 0.012, 0.070)),
        origin=Origin(xyz=(0.0, -0.006, 0.0)),
        material="stand_cream",
        name="slide_pad",
    )
    body.visual(
        Box((0.046, 0.040, 0.026)),
        origin=Origin(xyz=(0.0, -0.026, 0.018)),
        material="stand_cream",
        name="prism_body",
    )
    body.visual(
        Box((0.032, 0.022, 0.018)),
        origin=Origin(xyz=(0.0, -0.037, 0.032)),
        material="stand_cream",
        name="head_block",
    )
    body.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(xyz=(0.0, -0.036, 0.004)),
        material="stand_cream",
        name="nose_mount",
    )
    body.visual(
        Cylinder(radius=0.012, length=0.058),
        origin=Origin(
            xyz=(0.0, -0.030, 0.057),
            rpy=(-0.46, 0.0, 0.0),
        ),
        material="metal_light",
        name="eyepiece_tube",
    )
    body.visual(
        Cylinder(radius=0.009, length=0.018),
        origin=Origin(
            xyz=(0.0, -0.017, 0.072),
            rpy=(-0.46, 0.0, 0.0),
        ),
        material="glass_dark",
        name="eyecup",
    )

    turret = model.part("turret")
    turret.visual(
        mesh_from_cadquery(_turret_shape(), "microscope_turret"),
        material="metal_light",
        name="nosepiece",
    )

    x_control = model.part("x_control")
    x_control.visual(
        mesh_from_cadquery(_ring_knob_shape(0.018, 0.0085, 0.016), "microscope_x_control"),
        material="knob_black",
        name="outer_knob",
    )

    y_control = model.part("y_control")
    y_control.visual(
        Cylinder(radius=0.0065, length=0.022),
        origin=Origin(xyz=(0.011, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material="knob_black",
        name="inner_knob",
    )

    model.articulation(
        "stand_to_stage_bracket",
        ArticulationType.FIXED,
        parent=stand,
        child=stage_bracket,
        origin=Origin(xyz=(0.0, STAGE_Y_OFFSET, STAGE_Z)),
    )
    model.articulation(
        "stage_bracket_to_stage",
        ArticulationType.PRISMATIC,
        parent=stage_bracket,
        child=stage,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=0.12,
            lower=-STAGE_TRAVEL,
            upper=STAGE_TRAVEL,
        ),
    )
    model.articulation(
        "stand_to_body",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=body,
        origin=Origin(xyz=(0.0, BODY_COLUMN_FACE_Y, BODY_HOME_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=0.10,
            lower=0.0,
            upper=BODY_TRAVEL,
        ),
    )
    model.articulation(
        "body_to_turret",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=turret,
        origin=Origin(xyz=(0.0, -0.036, -0.001)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=6.0),
    )
    for name, child in (("stage_bracket_to_x_control", x_control), ("stage_bracket_to_y_control", y_control)):
        model.articulation(
            name,
            ArticulationType.CONTINUOUS,
            parent=stage_bracket,
            child=child,
            origin=Origin(xyz=(0.070, 0.0, -0.012)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=0.6, velocity=8.0),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
