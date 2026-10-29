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
COLUMN_Y = -0.032
FOCUS_Z0 = 0.105
FOCUS_TRAVEL = 0.075
STAGE_Y0 = 0.072
STAGE_TRAVEL = 0.018
OPTICAL_TILT = math.radians(32.0)
def _optical_offset(distance: float) -> tuple[float, float, float]:
    return (0.0, -math.sin(OPTICAL_TILT) * distance, math.cos(OPTICAL_TILT) * distance)
def _build_stage_ring_knob() -> cq.Workplane:
    outer_ring = cq.Workplane("YZ").circle(0.011).extrude(0.010)
    front_step = cq.Workplane("YZ").circle(0.009).extrude(0.004).translate((0.010, 0.0, 0.0))
    core_bore = cq.Workplane("YZ").circle(0.0046).extrude(0.016).translate((-0.001, 0.0, 0.0))
    return outer_ring.union(front_step).cut(core_bore)
def _add_rotated_x_cylinder(
    part,
    *,
    radius: float,
    length: float,
    xyz: tuple[float, float, float],
    material,
    name: str,
) -> None:
    part.visual(
        Cylinder(radius=radius, length=length),
        origin=Origin(xyz=xyz, rpy=(0.0, math.pi / 2.0, 0.0)),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="clinical_monocular_microscope")

    enamel = model.material("enamel", rgba=(0.87, 0.88, 0.84, 1.0))
    satin_steel = model.material("satin_steel", rgba=(0.73, 0.75, 0.78, 1.0))
    dark_trim = model.material("dark_trim", rgba=(0.18, 0.18, 0.19, 1.0))
    stage_black = model.material("stage_black", rgba=(0.15, 0.15, 0.16, 1.0))
    objective_black = model.material("objective_black", rgba=(0.12, 0.12, 0.13, 1.0))

    base = model.part("base")
    base.visual(
        Box((0.130, 0.185, 0.016)),
        origin=Origin(xyz=(0.0, 0.020, 0.008)),
        material=enamel,
        name="base_foot",
    )
    base.visual(
        Box((0.064, 0.072, 0.040)),
        origin=Origin(xyz=(0.0, -0.030, 0.028)),
        material=enamel,
        name="base_heel",
    )
    base.visual(
        Box((0.032, 0.042, 0.048)),
        origin=Origin(xyz=(0.0, -0.032, 0.050)),
        material=enamel,
        name="base_spine",
    )
    base.visual(
        Cylinder(radius=0.017, length=0.220),
        origin=Origin(xyz=(0.0, COLUMN_Y, 0.135)),
        material=enamel,
        name="column",
    )

    carriage = model.part("carriage")
    carriage.visual(
        Box((0.055, 0.010, 0.060)),
        origin=Origin(xyz=(0.0, 0.023, 0.0)),
        material=enamel,
        name="sleeve_front",
    )
    carriage.visual(
        Box((0.011, 0.046, 0.060)),
        origin=Origin(xyz=(-0.0225, 0.0, 0.0)),
        material=enamel,
        name="sleeve_side_0",
    )
    carriage.visual(
        Box((0.011, 0.046, 0.060)),
        origin=Origin(xyz=(0.0225, 0.0, 0.0)),
        material=enamel,
        name="sleeve_side_1",
    )
    carriage.visual(
        Box((0.040, 0.094, 0.010)),
        origin=Origin(xyz=(0.0, 0.070, -0.005)),
        material=enamel,
        name="carriage_arm",
    )
    carriage.visual(
        Box((0.016, 0.024, 0.084)),
        origin=Origin(xyz=(0.0, 0.048, 0.042)),
        material=enamel,
        name="carriage_riser",
    )
    carriage.visual(
        Box((0.030, 0.032, 0.032)),
        origin=Origin(xyz=(0.0, 0.076, 0.096)),
        material=enamel,
        name="head_block",
    )
    carriage.visual(
        Box((0.018, 0.070, 0.010)),
        origin=Origin(xyz=(0.0, STAGE_Y0 + 0.006, 0.000)),
        material=enamel,
        name="guide_support",
    )
    carriage.visual(
        Box((0.040, 0.024, 0.020)),
        origin=Origin(xyz=(0.020, STAGE_Y0, -0.006)),
        material=enamel,
        name="stage_bracket",
    )
    carriage.visual(
        Box((0.018, 0.070, 0.008)),
        origin=Origin(xyz=(0.0, STAGE_Y0 + 0.006, 0.009)),
        material=satin_steel,
        name="stage_guide",
    )

    nosepiece_origin = (0.0, 0.094, 0.074)
    main_tube_center = _optical_offset(0.046)
    eyepiece_center = _optical_offset(0.1195)
    eyecup_center = _optical_offset(0.155)

    carriage.visual(
        Cylinder(radius=0.0185, length=0.092),
        origin=Origin(
            xyz=(
                nosepiece_origin[0] + main_tube_center[0],
                nosepiece_origin[1] + main_tube_center[1],
                nosepiece_origin[2] + main_tube_center[2],
            ),
            rpy=(OPTICAL_TILT, 0.0, 0.0),
        ),
        material=satin_steel,
        name="body_tube",
    )
    carriage.visual(
        Cylinder(radius=0.010, length=0.055),
        origin=Origin(
            xyz=(
                nosepiece_origin[0] + eyepiece_center[0],
                nosepiece_origin[1] + eyepiece_center[1],
                nosepiece_origin[2] + eyepiece_center[2],
            ),
            rpy=(OPTICAL_TILT, 0.0, 0.0),
        ),
        material=dark_trim,
        name="eyepiece_tube",
    )
    carriage.visual(
        Cylinder(radius=0.012, length=0.018),
        origin=Origin(
            xyz=(
                nosepiece_origin[0] + eyecup_center[0],
                nosepiece_origin[1] + eyecup_center[1],
                nosepiece_origin[2] + eyecup_center[2],
            ),
            rpy=(OPTICAL_TILT, 0.0, 0.0),
        ),
        material=dark_trim,
        name="eyecup",
    )

    stage = model.part("stage")
    stage.visual(
        Box((0.072, 0.082, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=stage_black,
        name="stage_plate",
    )
    stage.visual(
        Box((0.005, 0.062, 0.018)),
        origin=Origin(xyz=(-0.0125, 0.0, 0.009)),
        material=stage_black,
        name="stage_rail_0",
    )
    stage.visual(
        Box((0.005, 0.062, 0.018)),
        origin=Origin(xyz=(0.0125, 0.0, 0.009)),
        material=stage_black,
        name="stage_rail_1",
    )
    stage.visual(
        Box((0.056, 0.008, 0.003)),
        origin=Origin(xyz=(0.0, 0.026, 0.021)),
        material=dark_trim,
        name="slide_clip",
    )

    turret = model.part("turret")
    turret.visual(
        Cylinder(radius=0.015, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=satin_steel,
        name="turret_hub",
    )
    for index, (x_pos, y_pos, radius, length) in enumerate(
        (
            (0.010, 0.000, 0.0060, 0.028),
            (-0.005, 0.008, 0.0050, 0.024),
            (-0.005, -0.008, 0.0048, 0.020),
        )
    ):
        turret.visual(
            Cylinder(radius=radius, length=length),
            origin=Origin(xyz=(x_pos, y_pos, -0.017)),
            material=objective_black,
            name=f"objective_{index}",
        )

    stage_control_0 = model.part("stage_control_0")
    stage_control_0.visual(
        mesh_from_cadquery(_build_stage_ring_knob(), "microscope_stage_control_ring"),
        material=dark_trim,
        name="control_knob",
    )

    stage_control_1 = model.part("stage_control_1")
    _add_rotated_x_cylinder(
        stage_control_1,
        radius=0.0030,
        length=0.021,
        xyz=(0.0105, 0.0, 0.0),
        material=dark_trim,
        name="control_shaft",
    )
    _add_rotated_x_cylinder(
        stage_control_1,
        radius=0.0065,
        length=0.010,
        xyz=(0.024, 0.0, 0.0),
        material=dark_trim,
        name="control_knob",
    )
    _add_rotated_x_cylinder(
        stage_control_1,
        radius=0.0045,
        length=0.004,
        xyz=(0.031, 0.0, 0.0),
        material=dark_trim,
        name="control_tip",
    )

    model.articulation(
        "base_to_carriage",
        ArticulationType.PRISMATIC,
        parent=base,
        child=carriage,
        origin=Origin(xyz=(0.0, COLUMN_Y, FOCUS_Z0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=65.0,
            velocity=0.12,
            lower=0.0,
            upper=FOCUS_TRAVEL,
        ),
    )
    model.articulation(
        "carriage_to_stage",
        ArticulationType.PRISMATIC,
        parent=carriage,
        child=stage,
        origin=Origin(xyz=(0.0, STAGE_Y0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.10,
            lower=-STAGE_TRAVEL,
            upper=STAGE_TRAVEL,
        ),
    )
    model.articulation(
        "carriage_to_turret",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=turret,
        origin=Origin(xyz=nosepiece_origin, rpy=(OPTICAL_TILT, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.5, velocity=10.0),
    )

    control_origin = Origin(xyz=(0.040, STAGE_Y0, 0.0))
    model.articulation(
        "carriage_to_stage_control_0",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=stage_control_0,
        origin=control_origin,
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.2, velocity=12.0),
    )
    model.articulation(
        "carriage_to_stage_control_1",
        ArticulationType.CONTINUOUS,
        parent=carriage,
        child=stage_control_1,
        origin=control_origin,
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.2, velocity=12.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
