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
BASE_WIDTH = 0.230
BASE_DEPTH = 0.185
BASE_HEIGHT = 0.022
COLUMN_RADIUS = 0.013
COLUMN_Y = 0.034
BODY_JOINT_Z = 0.286
STAGE_CENTER = (0.0, -0.010, 0.184)
TUBE_ANGLE = math.radians(32.0)
def _base_foot_shape() -> cq.Workplane:
    foot = cq.Workplane("XY").box(BASE_WIDTH, BASE_DEPTH, BASE_HEIGHT)
    foot = foot.edges("|Z").fillet(0.016)
    pedestal = cq.Workplane("XY").box(0.095, 0.080, 0.022).translate((0.0, 0.040, 0.022))
    return foot.union(pedestal)
def _body_sleeve_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.034)
        .circle(COLUMN_RADIUS + 0.003)
        .extrude(0.115)
        .translate((0.0, 0.0, -0.055))
    )
def _body_head_shape() -> cq.Workplane:
    head = cq.Workplane("XY").box(0.060, 0.050, 0.032).translate((0.0, -0.050, 0.030))
    head = head.edges("|Z").fillet(0.006)
    side_neck = cq.Workplane("XY").box(0.012, 0.054, 0.028).translate((0.027, -0.026, 0.016))
    return head.union(side_neck)
def _stage_plate_shape() -> cq.Workplane:
    plate = cq.Workplane("XY").box(0.118, 0.106, 0.008)
    plate = plate.edges("|Z").fillet(0.004)
    plate = plate.faces(">Z").workplane().circle(0.016).cutThruAll()
    plate = plate.faces(">Z").workplane().center(0.0, 0.041).circle(0.022).cutThruAll()
    right_bracket = cq.Workplane("XY").box(0.018, 0.050, 0.020).translate((0.068, 0.010, 0.004))
    rail_front = cq.Workplane("XY").box(0.050, 0.008, 0.005).translate((0.040, -0.024, 0.0065))
    rail_rear = cq.Workplane("XY").box(0.050, 0.008, 0.005).translate((0.040, 0.024, 0.0065))
    return plate.union(right_bracket).union(rail_front).union(rail_rear)
def _carriage_shape() -> cq.Workplane:
    carriage_block = cq.Workplane("XY").box(0.030, 0.056, 0.014).translate((0.019, 0.0, 0.007))
    carriage_block = carriage_block.edges("|Z").fillet(0.003)
    clamp_bar = cq.Workplane("XY").box(0.030, 0.006, 0.010).translate((0.015, 0.026, 0.015))
    clamp_post = cq.Workplane("XY").box(0.008, 0.050, 0.018).translate((0.030, 0.000, 0.013))
    return carriage_block.union(clamp_bar).union(clamp_post)
def _outer_stage_knob_shape() -> cq.Workplane:
    body = cq.Workplane("YZ").circle(0.0165).circle(0.0065).extrude(0.010)
    rim = cq.Workplane("YZ").circle(0.018).circle(0.0065).extrude(0.002).translate((0.008, 0.0, 0.0))
    return body.union(rim)
def _inner_stage_knob_shape() -> cq.Workplane:
    shaft = cq.Workplane("YZ").circle(0.0038).extrude(0.018)
    body = cq.Workplane("YZ").circle(0.009).extrude(0.010).translate((0.018, 0.0, 0.0))
    cap = cq.Workplane("YZ").circle(0.0105).extrude(0.002).translate((0.026, 0.0, 0.0))
    return shaft.union(body).union(cap)
def _tube_center(base_point: tuple[float, float, float], length: float) -> tuple[float, float, float]:
    axis = (0.0, math.sin(TUBE_ANGLE), math.cos(TUBE_ANGLE))
    return (
        base_point[0] + axis[0] * (length * 0.5),
        base_point[1] + axis[1] * (length * 0.5),
        base_point[2] + axis[2] * (length * 0.5),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="teaching_microscope")

    cast_white = model.material("cast_white", rgba=(0.93, 0.94, 0.92, 1.0))
    warm_gray = model.material("warm_gray", rgba=(0.74, 0.75, 0.77, 1.0))
    charcoal = model.material("charcoal", rgba=(0.18, 0.19, 0.21, 1.0))
    steel = model.material("steel", rgba=(0.69, 0.71, 0.74, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.34, 0.36, 0.39, 1.0))
    black = model.material("black", rgba=(0.09, 0.09, 0.10, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_foot_shape(), "microscope_base_foot"),
        material=cast_white,
        name="foot",
    )
    base.visual(
        Box((0.040, 0.020, 0.260)),
        origin=Origin(xyz=(0.0, 0.079, 0.153)),
        material=cast_white,
        name="spine",
    )
    base.visual(
        Box((0.056, 0.022, 0.080)),
        origin=Origin(xyz=(0.0, 0.078, 0.300)),
        material=cast_white,
        name="shoulder",
    )
    base.visual(
        Box((0.028, 0.010, 0.014)),
        origin=Origin(xyz=(-0.032, 0.079, 0.180)),
        material=cast_white,
        name="arm_bridge",
    )
    base.visual(
        Box((0.020, 0.024, 0.022)),
        origin=Origin(xyz=(-0.050, 0.072, 0.180)),
        material=cast_white,
        name="stage_support",
    )
    base.visual(
        Cylinder(radius=COLUMN_RADIUS, length=0.400),
        origin=Origin(xyz=(0.0, COLUMN_Y, 0.218)),
        material=steel,
        name="column",
    )

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_sleeve_shape(), "microscope_body_sleeve"),
        material=warm_gray,
        name="sleeve",
    )
    body.visual(
        mesh_from_cadquery(_body_head_shape(), "microscope_body_head"),
        material=cast_white,
        name="head",
    )
    body.visual(
        Box((0.012, 0.028, 0.022)),
        origin=Origin(xyz=(0.028, -0.006, 0.020)),
        material=cast_white,
        name="head_bridge",
    )
    body.visual(
        Cylinder(radius=0.016, length=0.012),
        origin=Origin(xyz=(0.0, -0.044, 0.008)),
        material=dark_steel,
        name="nose_mount",
    )
    tube_base = (0.032, -0.056, 0.058)
    tube_length = 0.110
    tube_center = _tube_center(tube_base, tube_length)
    body.visual(
        Cylinder(radius=0.015, length=tube_length),
        origin=Origin(xyz=tube_center, rpy=(-TUBE_ANGLE, 0.0, 0.0)),
        material=charcoal,
        name="tube",
    )
    eyepiece_length = 0.045
    eyepiece_base = _tube_center(tube_base, tube_length * 2.0)
    eyepiece_center = _tube_center(eyepiece_base, eyepiece_length)
    body.visual(
        Cylinder(radius=0.012, length=eyepiece_length),
        origin=Origin(xyz=eyepiece_center, rpy=(-TUBE_ANGLE, 0.0, 0.0)),
        material=black,
        name="eyepiece",
    )
    eyecup_length = 0.018
    eyecup_base = _tube_center(eyepiece_base, eyepiece_length * 2.0)
    eyecup_center = _tube_center(eyecup_base, eyecup_length)
    body.visual(
        Cylinder(radius=0.0135, length=eyecup_length),
        origin=Origin(xyz=eyecup_center, rpy=(-TUBE_ANGLE, 0.0, 0.0)),
        material=black,
        name="eyecup",
    )
    body.visual(
        Box((0.014, 0.018, 0.010)),
        origin=Origin(xyz=(0.028, -0.048, 0.051)),
        material=charcoal,
        name="tube_mount",
    )

    turret = model.part("turret")
    turret.visual(
        Cylinder(radius=0.029, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=dark_steel,
        name="turret_cap",
    )
    turret.visual(
        Cylinder(radius=0.012, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=steel,
        name="nosepiece",
    )
    objective_specs = (
        ("objective_long", (0.018, 0.000, -0.031), 0.0065, 0.044),
        ("objective_mid", (-0.009, 0.0156, -0.025), 0.0060, 0.032),
        ("objective_short", (-0.009, -0.0156, -0.021), 0.0054, 0.024),
    )
    for name, xyz, radius, length in objective_specs:
        turret.visual(
            Cylinder(radius=radius, length=length),
            origin=Origin(xyz=xyz),
            material=steel,
            name=name,
        )
        turret.visual(
            Cylinder(radius=radius * 0.78, length=0.014),
            origin=Origin(xyz=(xyz[0], xyz[1], xyz[2] - length * 0.5 - 0.006)),
            material=black,
            name=f"{name}_tip",
        )

    stage = model.part("stage")
    stage.visual(
        mesh_from_cadquery(_stage_plate_shape(), "microscope_stage_plate"),
        material=charcoal,
        name="plate",
    )
    stage.visual(
        Box((0.028, 0.040, 0.022)),
        origin=Origin(xyz=(-0.038, 0.050, -0.004)),
        material=warm_gray,
        name="mount",
    )

    carriage = model.part("carriage")
    carriage.visual(
        mesh_from_cadquery(_carriage_shape(), "microscope_stage_carriage"),
        material=dark_steel,
        name="carriage_plate",
    )

    stage_knob = model.part("stage_knob")
    stage_knob.visual(
        mesh_from_cadquery(_outer_stage_knob_shape(), "microscope_stage_knob"),
        material=black,
        name="knob",
    )

    stage_trim = model.part("stage_trim")
    stage_trim.visual(
        mesh_from_cadquery(_inner_stage_knob_shape(), "microscope_stage_trim"),
        material=black,
        name="knob",
    )

    model.articulation(
        "base_to_body",
        ArticulationType.PRISMATIC,
        parent=base,
        child=body,
        origin=Origin(xyz=(0.0, COLUMN_Y, BODY_JOINT_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=14.0, velocity=0.05, lower=0.0, upper=0.055),
    )
    model.articulation(
        "body_to_turret",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=turret,
        origin=Origin(xyz=(0.0, -0.078, 0.002)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.6, velocity=4.0),
    )
    model.articulation(
        "base_to_stage",
        ArticulationType.FIXED,
        parent=base,
        child=stage,
        origin=Origin(xyz=STAGE_CENTER),
    )
    model.articulation(
        "stage_to_carriage",
        ArticulationType.PRISMATIC,
        parent=stage,
        child=carriage,
        origin=Origin(xyz=(0.036, 0.0, 0.014)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=0.03, lower=-0.015, upper=0.015),
    )
    model.articulation(
        "stage_to_knob",
        ArticulationType.CONTINUOUS,
        parent=stage,
        child=stage_knob,
        origin=Origin(xyz=(0.077, 0.010, 0.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.08, velocity=5.0),
    )
    model.articulation(
        "stage_to_trim",
        ArticulationType.CONTINUOUS,
        parent=stage,
        child=stage_trim,
        origin=Origin(xyz=(0.077, 0.010, 0.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.08, velocity=5.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
