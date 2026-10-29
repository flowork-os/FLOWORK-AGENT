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
BACKPLATE_W = 0.22
BACKPLATE_H = 0.68
BACKPLATE_T = 0.008
SPINE_W = 0.062
SPINE_D = 0.046
SPINE_H = 0.56
SPINE_Z0 = 0.06
SPINE_CENTER_Y = BACKPLATE_T / 2.0 + SPINE_D / 2.0
HINGE_RADIUS = 0.058
PIN_RADIUS = 0.0065
POD_TOTAL_WIDTH = 0.026
EYE_INNER_RADIUS = PIN_RADIUS
EYE_OUTER_RADIUS = 0.013
EYE_WIDTH = 0.012
BRANCH_ARM_LENGTH = 0.164
END_PLATE_THICKNESS = 0.01
BRANCH_SPECS = (
    {
        "part": "lower_arm",
        "joint": "lower_branch_joint",
        "pod_visual": "lower_pod",
        "angle_deg": 155.0,
        "hinge_z": 0.16,
    },
    {
        "part": "middle_arm",
        "joint": "middle_branch_joint",
        "pod_visual": "middle_pod",
        "angle_deg": 90.0,
        "hinge_z": 0.34,
    },
    {
        "part": "upper_arm",
        "joint": "upper_branch_joint",
        "pod_visual": "upper_pod",
        "angle_deg": 25.0,
        "hinge_z": 0.52,
    },
)
def _polar_xy(radius: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    return (radius * math.cos(angle_rad), radius * math.sin(angle_rad))
def _place_branch_shape(shape: cq.Workplane, angle_deg: float, xyz: tuple[float, float, float]) -> cq.Workplane:
    return shape.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg).translate(xyz)
def _make_backplate_assembly() -> cq.Workplane:
    plate = cq.Workplane("XY").box(BACKPLATE_W, BACKPLATE_T, BACKPLATE_H, centered=(True, True, False))

    slot_cutters = (
        cq.Workplane("XZ")
        .pushPoints(
            [
                (-0.075, 0.14),
                (0.075, 0.14),
                (-0.075, 0.54),
                (0.075, 0.54),
            ]
        )
        .slot2D(0.028, 0.010, angle=90.0)
        .extrude(BACKPLATE_T * 2.0, both=True)
    )
    plate = plate.cut(slot_cutters)

    spine = (
        cq.Workplane("XY")
        .box(SPINE_W, SPINE_D, SPINE_H, centered=(True, True, False))
        .translate((0.0, SPINE_CENTER_Y, SPINE_Z0))
    )

    saddle = (
        cq.Workplane("XY")
        .box(0.102, 0.022, 0.24, centered=(True, True, False))
        .translate((0.0, BACKPLATE_T / 2.0 + 0.011, 0.22))
    )

    return plate.union(spine).union(saddle)
def _make_branch_pod() -> cq.Workplane:
    bridge = (
        cq.Workplane("XY")
        .box(0.040, 0.018, 0.022, centered=(False, True, True))
        .translate((-0.112, 0.0, 0.0))
    )
    housing = (
        cq.Workplane("XY")
        .box(0.046, 0.032, 0.046, centered=(False, True, True))
        .translate((-0.072, 0.0, 0.0))
    )
    left_cheek = (
        cq.Workplane("XY")
        .box(0.028, 0.005, 0.048, centered=(False, True, True))
        .translate((-0.028, 0.0105, 0.0))
    )
    right_cheek = (
        cq.Workplane("XY")
        .box(0.028, 0.005, 0.048, centered=(False, True, True))
        .translate((-0.028, -0.0105, 0.0))
    )
    pin = cq.Workplane("XZ").circle(PIN_RADIUS).extrude(POD_TOTAL_WIDTH / 2.0, both=True)
    return bridge.union(housing).union(left_cheek).union(right_cheek).union(pin)
def _make_arm_hub() -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(EYE_OUTER_RADIUS)
        .circle(EYE_INNER_RADIUS * 0.92)
        .extrude(EYE_WIDTH / 2.0, both=True)
    )
def _make_branch_arm_body() -> cq.Workplane:
    neck_start = 0.030
    beam_length = BRANCH_ARM_LENGTH - END_PLATE_THICKNESS - neck_start

    neck = (
        cq.Workplane("XY")
        .box(0.020, 0.010, 0.018, centered=(False, True, True))
        .translate((0.010, 0.0, 0.0))
    )
    root_block = (
        cq.Workplane("XY")
        .box(0.020, 0.016, 0.018, centered=(False, True, True))
        .translate((neck_start, 0.0, 0.0))
    )
    beam = (
        cq.Workplane("XY")
        .box(beam_length, 0.016, 0.014, centered=(False, True, True))
        .translate((neck_start, 0.0, 0.0))
    )
    lower_flanges = (
        cq.Workplane("XZ")
        .rect(0.090, 0.010)
        .extrude(0.006, both=True)
        .translate((0.070, 0.0, -0.012))
    )

    return neck.union(root_block).union(beam).union(lower_flanges)
def _make_end_plate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(END_PLATE_THICKNESS, 0.072, 0.095, centered=(False, True, True))
        .translate((BRANCH_ARM_LENGTH - END_PLATE_THICKNESS, 0.0, 0.0))
    )
    hole_cutters = (
        cq.Workplane("YZ")
        .pushPoints([(0.0, 0.026), (0.0, -0.026)])
        .circle(0.0035)
        .extrude(END_PLATE_THICKNESS * 2.0)
        .translate((BRANCH_ARM_LENGTH - END_PLATE_THICKNESS - 0.002, 0.0, 0.0))
    )
    return plate.cut(hole_cutters)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="service_panel_three_branch_bracket")

    frame_finish = model.material("frame_finish", rgba=(0.19, 0.20, 0.22, 1.0))
    arm_finish = model.material("arm_finish", rgba=(0.60, 0.62, 0.65, 1.0))
    plate_finish = model.material("plate_finish", rgba=(0.82, 0.84, 0.86, 1.0))

    frame = model.part("frame")
    frame.visual(
        mesh_from_cadquery(_make_backplate_assembly(), "frame_backplate_assembly"),
        material=frame_finish,
        name="backplate_assembly",
    )

    pod_shape = _make_branch_pod()
    arm_hub_shape = _make_arm_hub()
    arm_body_shape = _make_branch_arm_body()
    end_plate_shape = _make_end_plate()

    arm_parts = {}
    for spec in BRANCH_SPECS:
        px, py = _polar_xy(HINGE_RADIUS, spec["angle_deg"])
        hinge_xyz = (px, SPINE_CENTER_Y + py, spec["hinge_z"])

        frame.visual(
            mesh_from_cadquery(
                _place_branch_shape(pod_shape, spec["angle_deg"], hinge_xyz),
                f"{spec['pod_visual']}_mesh",
            ),
            material=frame_finish,
            name=spec["pod_visual"],
        )

        arm = model.part(spec["part"])
        arm.visual(
            mesh_from_cadquery(arm_hub_shape, f"{spec['part']}_hub_mesh"),
            material=arm_finish,
            name="arm_hub",
        )
        arm.visual(
            mesh_from_cadquery(arm_body_shape, f"{spec['part']}_body_mesh"),
            material=arm_finish,
            name="arm_body",
        )
        arm.visual(
            mesh_from_cadquery(end_plate_shape, f"{spec['part']}_end_plate_mesh"),
            material=plate_finish,
            name="end_plate",
        )
        arm_parts[spec["part"]] = arm

        model.articulation(
            spec["joint"],
            ArticulationType.REVOLUTE,
            parent=frame,
            child=arm,
            origin=Origin(
                xyz=hinge_xyz,
                rpy=(0.0, 0.0, math.radians(spec["angle_deg"])),
            ),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=12.0,
                velocity=1.8,
                lower=-0.45,
                upper=1.10,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
