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

# ===== model =====
from math import radians
import cadquery as cq
BASE_LENGTH = 0.240
BASE_WIDTH = 0.180
BASE_HEIGHT = 0.028
STAGE_JOINT_XYZ = (-0.044, 0.0, 0.136)
BODY_JOINT_XYZ = (-0.060, 0.0, 0.176)
TURRET_JOINT_XYZ = (0.099, 0.0, 0.042)
STAGE_GUIDE_XYZ = (0.090, 0.072, 0.038)
CONDENSER_JOINT_XYZ = (0.058, 0.0, 0.021)
LEVER_PIVOT_XYZ = (0.018, 0.0, -0.025)
def _stand_shell_shape() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT)
        .translate((0.0, 0.0, BASE_HEIGHT / 2.0))
        .edges("|Z")
        .fillet(0.018)
    )
    arm_profile = [
        (-0.104, 0.018),
        (-0.068, 0.018),
        (-0.060, 0.070),
        (-0.050, 0.165),
        (-0.040, 0.255),
        (-0.032, 0.300),
        (-0.024, 0.286),
        (-0.032, 0.220),
        (-0.042, 0.128),
        (-0.056, 0.048),
        (-0.076, 0.018),
    ]
    arm = cq.Workplane("XZ").polyline(arm_profile).close().extrude(0.050).translate((0.0, -0.025, 0.0))
    return base.union(arm)
def _stage_deck_shape() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(0.112, 0.102, 0.008)
        .translate((0.064, 0.0, 0.025))
    )
    plate = plate.cut(
        cq.Workplane("XY")
        .box(0.038, 0.038, 0.016)
        .translate((0.058, 0.0, 0.025))
    )

    neck = (
        cq.Workplane("XY")
        .box(0.038, 0.048, 0.014)
        .translate((0.024, 0.0, 0.017))
    )
    return plate.union(neck)
def _stage_guide_shape() -> cq.Workplane:
    shelf = cq.Workplane("XY").box(0.094, 0.022, 0.006).translate((0.090, 0.060, 0.024))
    rod = (
        cq.Workplane("XY")
        .circle(0.0053)
        .extrude(0.086)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((0.047, 0.072, 0.038))
    )

    rear_boss = (
        cq.Workplane("XY")
        .box(0.010, 0.018, 0.010)
        .translate((0.049, 0.072, 0.038))
    )
    front_boss = (
        cq.Workplane("XY")
        .box(0.010, 0.018, 0.010)
        .translate((0.131, 0.072, 0.038))
    )
    rear_post = cq.Workplane("XY").box(0.006, 0.010, 0.018).translate((0.049, 0.068, 0.031))
    front_post = cq.Workplane("XY").box(0.006, 0.010, 0.018).translate((0.131, 0.068, 0.031))

    return shelf.union(rod).union(rear_boss).union(front_boss).union(rear_post).union(front_post)
def _condenser_shape() -> cq.Workplane:
    flange = cq.Workplane("XY").circle(0.014).extrude(0.003).translate((0.0, 0.0, -0.003))
    housing = cq.Workplane("XY").circle(0.015).extrude(0.024).translate((0.0, 0.0, -0.027))
    lower_collar = cq.Workplane("XY").circle(0.010).extrude(0.010).translate((0.0, 0.0, -0.037))
    lug = cq.Workplane("XY").box(0.014, 0.006, 0.008).translate((0.011, 0.0, -0.023))
    return flange.union(housing).union(lower_collar).union(lug)
def _body_shell_shape() -> cq.Workplane:
    clamp = (
        cq.Workplane("XY")
        .box(0.050, 0.056, 0.038)
        .translate((0.0, 0.0, 0.019))
    )
    clamp = clamp.cut(
        cq.Workplane("XY")
        .circle(0.0167)
        .extrude(0.044)
        .translate((0.0, 0.0, -0.003))
    )
    clamp = clamp.cut(
        cq.Workplane("XY")
        .box(0.030, 0.018, 0.042)
        .translate((-0.017, 0.0, 0.019))
    )

    mast = cq.Workplane("XY").box(0.018, 0.040, 0.070).translate((0.032, 0.0, 0.073))
    connector = cq.Workplane("XY").box(0.030, 0.040, 0.020).translate((0.052, 0.0, 0.088))
    head = cq.Workplane("XY").box(0.052, 0.050, 0.036).translate((0.072, 0.0, 0.108))
    nosepiece_stem = cq.Workplane("XY").circle(0.0088).extrude(0.046).translate((0.099, 0.0, 0.046))
    nosepiece_collar = (
        cq.Workplane("XY")
        .circle(0.014)
        .extrude(0.005)
        .cut(cq.Workplane("XY").circle(0.0086).extrude(0.007))
        .translate((0.099, 0.0, 0.042))
    )

    tube = (
        cq.Workplane("XY")
        .circle(0.017)
        .extrude(0.110)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -32.0)
        .translate((0.072, 0.0, 0.104))
    )
    eyepiece = (
        cq.Workplane("XY")
        .circle(0.0125)
        .extrude(0.028)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -32.0)
        .translate((0.072 - 0.058, 0.0, 0.104 + 0.093))
    )

    return (
        clamp.union(mast)
        .union(connector)
        .union(head)
        .union(nosepiece_stem)
        .union(nosepiece_collar)
        .union(tube)
        .union(eyepiece)
    )
def _turret_shape() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .circle(0.022)
        .extrude(0.010)
        .translate((0.0, 0.0, -0.010))
    )
    body = body.cut(
        cq.Workplane("XY")
        .circle(0.0096)
        .extrude(0.016)
        .translate((0.0, 0.0, -0.012))
    )

    objective_origins = [
        (0.0135, 0.0),
        (-0.00675, 0.01169),
        (-0.00675, -0.01169),
    ]
    lengths = (0.022, 0.027, 0.019)
    for (x_pos, y_pos), length in zip(objective_origins, lengths):
        upper_barrel = (
            cq.Workplane("XY")
            .circle(0.0055)
            .extrude(0.010)
            .translate((x_pos, y_pos, -0.020))
        )
        lower_barrel = (
            cq.Workplane("XY")
            .circle(0.0038)
            .extrude(length)
            .translate((x_pos, y_pos, -0.020 - length))
        )
        body = body.union(upper_barrel).union(lower_barrel)

    return body
def _carriage_shape() -> cq.Workplane:
    clamp = (
        cq.Workplane("XY")
        .box(0.024, 0.020, 0.022)
        .translate((0.0, 0.0, 0.0))
    )
    clamp = clamp.cut(
        cq.Workplane("XY")
        .circle(0.0058)
        .extrude(0.030)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((-0.015, 0.0, 0.0))
    )

    over_stage_arm = cq.Workplane("XY").box(0.040, 0.032, 0.006).translate((0.006, -0.018, 0.010))
    clip_lip = cq.Workplane("XY").box(0.008, 0.016, 0.012).translate((0.018, -0.034, 0.013))
    thumb_tab = cq.Workplane("XY").box(0.010, 0.014, 0.010).translate((-0.014, 0.012, 0.010))

    return clamp.union(over_stage_arm).union(clip_lip).union(thumb_tab)
def _lever_shape() -> cq.Workplane:
    eye = (
        cq.Workplane("XY")
        .circle(0.0056)
        .extrude(0.003)
        .translate((0.0, 0.0, -0.0015))
    )
    eye = eye.cut(
        cq.Workplane("XY")
        .circle(0.0032)
        .extrude(0.005)
        .translate((0.0, 0.0, -0.0025))
    )

    arm = cq.Workplane("XY").box(0.034, 0.006, 0.003).translate((0.019, 0.0, -0.0015))
    handle = cq.Workplane("XY").circle(0.0038).extrude(0.009).translate((0.036, 0.0, -0.006))
    return eye.union(arm).union(handle)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="teaching_microscope")

    model.material("enamel_ivory", rgba=(0.86, 0.86, 0.82, 1.0))
    model.material("stage_black", rgba=(0.11, 0.11, 0.12, 1.0))
    model.material("matte_black", rgba=(0.08, 0.08, 0.09, 1.0))
    model.material("optics_silver", rgba=(0.67, 0.69, 0.73, 1.0))
    model.material("knob_black", rgba=(0.10, 0.10, 0.11, 1.0))

    stand = model.part("stand")
    stand.visual(
        mesh_from_cadquery(_stand_shell_shape(), "microscope_stand_shell"),
        material="enamel_ivory",
        name="stand_shell",
    )
    stand.visual(
        Box((0.036, 0.050, 0.108)),
        origin=Origin(xyz=(-0.044, 0.0, 0.082)),
        material="enamel_ivory",
        name="stage_support",
    )
    stand.visual(
        Cylinder(radius=0.0165, length=0.210),
        origin=Origin(xyz=(-0.060, 0.0, 0.193)),
        material="optics_silver",
        name="focus_column",
    )

    stage = model.part("stage")
    stage.visual(
        Box((0.022, 0.038, 0.022)),
        origin=Origin(xyz=(0.010, 0.0, 0.011)),
        material="stage_black",
        name="stage_mount",
    )
    stage.visual(
        mesh_from_cadquery(_stage_deck_shape(), "microscope_stage_plate"),
        material="stage_black",
        name="stage_plate",
    )
    stage.visual(
        mesh_from_cadquery(_stage_guide_shape(), "microscope_stage_guide"),
        material="stage_black",
        name="stage_guide",
    )

    condenser = model.part("condenser")
    condenser.visual(
        mesh_from_cadquery(_condenser_shape(), "microscope_condenser"),
        material="matte_black",
        name="housing",
    )
    condenser.visual(
        Cylinder(radius=0.0028, length=0.006),
        origin=Origin(xyz=(0.018, 0.0, -0.020)),
        material="optics_silver",
        name="pivot_pin",
    )

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell_shape(), "microscope_body_shell"),
        material="enamel_ivory",
        name="body_shell",
    )

    turret = model.part("turret")
    turret.visual(
        mesh_from_cadquery(_turret_shape(), "microscope_turret"),
        material="optics_silver",
        name="turret",
    )

    side_carriage = model.part("side_carriage")
    side_carriage.visual(
        mesh_from_cadquery(_carriage_shape(), "microscope_side_carriage"),
        material="stage_black",
        name="carriage",
    )

    diaphragm_lever = model.part("diaphragm_lever")
    diaphragm_lever.visual(
        mesh_from_cadquery(_lever_shape(), "microscope_diaphragm_lever"),
        material="knob_black",
        name="lever",
    )

    model.articulation(
        "stand_to_stage",
        ArticulationType.FIXED,
        parent=stand,
        child=stage,
        origin=Origin(xyz=STAGE_JOINT_XYZ),
    )
    model.articulation(
        "stage_to_condenser",
        ArticulationType.FIXED,
        parent=stage,
        child=condenser,
        origin=Origin(xyz=CONDENSER_JOINT_XYZ),
    )
    model.articulation(
        "stand_to_body",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=body,
        origin=Origin(xyz=BODY_JOINT_XYZ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=30.0,
            velocity=0.10,
            lower=0.0,
            upper=0.070,
        ),
    )
    model.articulation(
        "body_to_turret",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=turret,
        origin=Origin(xyz=TURRET_JOINT_XYZ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=10.0,
        ),
    )
    model.articulation(
        "stage_to_side_carriage",
        ArticulationType.PRISMATIC,
        parent=stage,
        child=side_carriage,
        origin=Origin(xyz=STAGE_GUIDE_XYZ),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.08,
            lower=-0.018,
            upper=0.018,
        ),
    )
    model.articulation(
        "condenser_to_diaphragm_lever",
        ArticulationType.REVOLUTE,
        parent=condenser,
        child=diaphragm_lever,
        origin=Origin(xyz=LEVER_PIVOT_XYZ),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.5,
            velocity=2.0,
            lower=-radians(28.0),
            upper=radians(28.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
