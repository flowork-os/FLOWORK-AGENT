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
import math
import cadquery as cq
def _base_casting_shape() -> cq.Workplane:
    sole = cq.Workplane("XY").box(0.225, 0.165, 0.016, centered=(True, True, False))
    front_opening = (
        cq.Workplane("XY")
        .center(0.068, 0.0)
        .box(0.120, 0.084, 0.028, centered=(True, True, False))
    )
    sole = sole.cut(front_opening)

    upper_cast = (
        cq.Workplane("XY")
        .center(-0.028, 0.0)
        .rect(0.144, 0.126)
        .workplane(offset=0.026)
        .rect(0.114, 0.096)
        .loft(combine=True)
        .translate((0.0, 0.0, 0.016))
    )

    pedestal = (
        cq.Workplane("XY")
        .center(-0.048, 0.0)
        .box(0.052, 0.076, 0.040, centered=(True, True, False))
        .translate((0.0, 0.0, 0.016))
    )

    return sole.union(upper_cast).union(pedestal)
def _arm_body_shape() -> cq.Workplane:
    arm = (
        cq.Workplane("XY")
        .center(0.044, 0.0)
        .box(0.034, 0.060, 0.150, centered=(True, True, False))
        .translate((0.0, 0.0, 0.048))
    )
    bridge = (
        cq.Workplane("XY")
        .center(0.080, 0.0)
        .box(0.038, 0.056, 0.024, centered=(True, True, False))
        .translate((0.0, 0.0, 0.196))
    )
    head = (
        cq.Workplane("XY")
        .center(0.122, 0.0)
        .box(0.096, 0.056, 0.044, centered=(True, True, False))
        .translate((0.0, 0.0, 0.190))
    )
    stage_post = (
        cq.Workplane("XY")
        .center(0.094, 0.0)
        .box(0.012, 0.024, 0.058, centered=(True, True, False))
        .translate((0.0, 0.0, 0.086))
    )
    stage_bridge = (
        cq.Workplane("XY")
        .center(0.078, 0.0)
        .box(0.052, 0.024, 0.014, centered=(True, True, False))
        .translate((0.0, 0.0, 0.118))
    )
    nose_hub = (
        cq.Workplane("XY")
        .center(0.136, 0.0)
        .circle(0.019)
        .extrude(0.018)
        .translate((0.0, 0.0, 0.172))
    )
    return arm.union(bridge).union(head).union(stage_post).union(stage_bridge).union(nose_hub)
def _eyepiece_tube_shape() -> cq.Workplane:
    outer = cq.Workplane("XY").circle(0.014).extrude(0.078)
    inner = cq.Workplane("XY").circle(0.009).extrude(0.072).translate((0.0, 0.0, 0.006))
    collar = cq.Workplane("XY").circle(0.016).extrude(0.010)
    ocular = (
        cq.Workplane("XY")
        .circle(0.015)
        .extrude(0.016)
        .translate((0.0, 0.0, 0.062))
    )
    tube = outer.cut(inner).union(collar).union(ocular)
    tube = tube.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -40.0)
    return tube.translate((0.078, 0.0, 0.210))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="clinical_monocular_microscope")

    ivory = model.material("ivory_enamel", rgba=(0.82, 0.81, 0.76, 1.0))
    stage_black = model.material("stage_black", rgba=(0.11, 0.11, 0.12, 1.0))
    tube_black = model.material("tube_black", rgba=(0.15, 0.15, 0.16, 1.0))
    column_grey = model.material("column_grey", rgba=(0.56, 0.58, 0.61, 1.0))
    knob_black = model.material("knob_black", rgba=(0.08, 0.08, 0.09, 1.0))
    turret_dark = model.material("turret_dark", rgba=(0.17, 0.17, 0.18, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_casting_shape(), "microscope_base_casting"),
        material=ivory,
        name="base_casting",
    )
    base.visual(
        Box((0.038, 0.028, 0.230)),
        origin=Origin(xyz=(-0.048, 0.0, 0.170)),
        material=column_grey,
        name="column_rail",
    )

    carriage = model.part("carriage")
    carriage.visual(
        Box((0.066, 0.009, 0.095)),
        origin=Origin(xyz=(0.0, 0.0185, 0.0475)),
        material=ivory,
        name="sleeve_left",
    )
    carriage.visual(
        Box((0.066, 0.009, 0.095)),
        origin=Origin(xyz=(0.0, -0.0185, 0.0475)),
        material=ivory,
        name="sleeve_right",
    )
    carriage.visual(
        Box((0.014, 0.032, 0.095)),
        origin=Origin(xyz=(-0.0260, 0.0, 0.0475)),
        material=ivory,
        name="sleeve_rear",
    )
    carriage.visual(
        Box((0.014, 0.032, 0.095)),
        origin=Origin(xyz=(0.0260, 0.0, 0.0475)),
        material=ivory,
        name="sleeve_front",
    )
    carriage.visual(
        Box((0.030, 0.050, 0.022)),
        origin=Origin(xyz=(0.038, 0.0, 0.059)),
        material=ivory,
        name="carriage_sleeve",
    )
    carriage.visual(
        mesh_from_cadquery(_arm_body_shape(), "microscope_arm_body"),
        material=ivory,
        name="arm_body",
    )
    carriage.visual(
        mesh_from_cadquery(_eyepiece_tube_shape(), "microscope_eyepiece_tube"),
        material=tube_black,
        name="eyepiece_tube",
    )
    carriage.visual(
        Box((0.080, 0.022, 0.014)),
        origin=Origin(xyz=(0.174, 0.0, 0.086)),
        material=column_grey,
        name="stage_guide",
    )
    carriage.visual(
        Box((0.084, 0.018, 0.014)),
        origin=Origin(xyz=(0.132, 0.0, 0.086)),
        material=ivory,
        name="stage_beam",
    )
    carriage.visual(
        Cylinder(radius=0.020, length=0.010),
        origin=Origin(xyz=(0.040, 0.028, 0.106), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=ivory,
        name="focus_mount",
    )
    carriage.visual(
        Cylinder(radius=0.013, length=0.008),
        origin=Origin(xyz=(0.040, 0.028, 0.136), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=ivory,
        name="fine_mount",
    )
    carriage.visual(
        Cylinder(radius=0.013, length=0.030),
        origin=Origin(xyz=(0.174, 0.0, 0.175)),
        material=ivory,
        name="turret_mount",
    )

    stage = model.part("stage")
    stage.visual(
        Box((0.038, 0.090, 0.006)),
        origin=Origin(xyz=(0.031, 0.0, 0.019)),
        material=stage_black,
        name="stage_front_strip",
    )
    stage.visual(
        Box((0.038, 0.090, 0.006)),
        origin=Origin(xyz=(-0.031, 0.0, 0.019)),
        material=stage_black,
        name="stage_rear_strip",
    )
    stage.visual(
        Box((0.024, 0.030, 0.006)),
        origin=Origin(xyz=(0.0, 0.030, 0.019)),
        material=stage_black,
        name="stage_upper_strip",
    )
    stage.visual(
        Box((0.024, 0.030, 0.006)),
        origin=Origin(xyz=(0.0, -0.030, 0.019)),
        material=stage_black,
        name="stage_lower_strip",
    )
    stage.visual(
        Box((0.072, 0.050, 0.006)),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material=stage_black,
        name="stage_carriage",
    )
    stage.visual(
        Box((0.072, 0.010, 0.024)),
        origin=Origin(xyz=(0.0, 0.014, 0.002)),
        material=stage_black,
        name="stage_left_skirt",
    )
    stage.visual(
        Box((0.072, 0.010, 0.024)),
        origin=Origin(xyz=(0.0, -0.014, 0.002)),
        material=stage_black,
        name="stage_right_skirt",
    )
    stage.visual(
        Box((0.012, 0.090, 0.007)),
        origin=Origin(xyz=(0.040, 0.0, 0.0155)),
        material=stage_black,
        name="stage_lip",
    )

    turret = model.part("turret")
    turret.visual(
        Cylinder(radius=0.026, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=turret_dark,
        name="turret_body",
    )
    turret.visual(
        Cylinder(radius=0.011, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -0.012)),
        material=turret_dark,
        name="turret_spindle",
    )
    for index, angle_deg in enumerate((0.0, 120.0, 240.0)):
        angle = math.radians(angle_deg)
        x = 0.017 * math.cos(angle)
        y = 0.017 * math.sin(angle)
        objective_length = 0.022 + 0.002 * index
        tip_length = 0.010 + 0.0015 * index
        turret.visual(
            Cylinder(radius=0.007, length=objective_length),
            origin=Origin(xyz=(x, y, -0.010 - objective_length / 2.0)),
            material=turret_dark,
            name=f"objective_{index}",
        )
        turret.visual(
            Cylinder(radius=0.0045, length=tip_length),
            origin=Origin(
                xyz=(x, y, -0.010 - objective_length - tip_length / 2.0)
            ),
            material=turret_dark,
            name=f"objective_tip_{index}",
        )

    coarse_knob = model.part("coarse_knob")
    coarse_knob.visual(
        Cylinder(radius=0.022, length=0.009),
        origin=Origin(xyz=(0.0, 0.0045, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_black,
        name="coarse_knob",
    )
    coarse_knob.visual(
        Cylinder(radius=0.018, length=0.004),
        origin=Origin(xyz=(0.0, 0.011, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_black,
        name="coarse_cap",
    )

    fine_knob = model.part("fine_knob")
    fine_knob.visual(
        Cylinder(radius=0.010, length=0.007),
        origin=Origin(xyz=(0.0, 0.0035, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_black,
        name="fine_knob",
    )
    fine_knob.visual(
        Cylinder(radius=0.008, length=0.003),
        origin=Origin(xyz=(0.0, 0.0085, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_black,
        name="fine_cap",
    )

    base_to_carriage = model.articulation(
        "base_to_carriage",
        ArticulationType.PRISMATIC,
        parent=base,
        child=carriage,
        origin=Origin(xyz=(-0.048, 0.0, 0.085)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=35.0,
            velocity=0.04,
            lower=0.0,
            upper=0.095,
        ),
    )

    carriage_to_stage = model.articulation(
        "carriage_to_stage",
        ArticulationType.PRISMATIC,
        parent=carriage,
        child=stage,
        origin=Origin(xyz=(0.174, 0.0, 0.086)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.03,
            lower=0.0,
            upper=0.028,
        ),
    )

    model.articulation(
        "carriage_to_turret",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=turret,
        origin=Origin(xyz=(0.174, 0.0, 0.160)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.5, velocity=6.0),
    )

    coarse_knob_origin = Origin(xyz=(0.040, 0.033, 0.106))
    fine_knob_origin = Origin(xyz=(0.040, 0.032, 0.136))
    knob_limits = MotionLimits(effort=0.35, velocity=8.0)
    model.articulation(
        "carriage_to_coarse_knob",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=coarse_knob,
        origin=coarse_knob_origin,
        axis=(0.0, 1.0, 0.0),
        motion_limits=knob_limits,
    )
    model.articulation(
        "carriage_to_fine_knob",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=fine_knob,
        origin=fine_knob_origin,
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.18, velocity=10.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
