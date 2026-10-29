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
def _stand_shell_shape() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(0.240, 0.170, 0.022)
        .translate((0.0, 0.0, 0.011))
        .edges("|Z")
        .fillet(0.010)
    )

    outer_profile = [
        (-0.082, 0.022),
        (-0.090, 0.110),
        (-0.082, 0.210),
        (-0.052, 0.312),
        (-0.018, 0.382),
        (0.004, 0.402),
        (0.020, 0.390),
        (0.015, 0.332),
        (0.000, 0.248),
        (0.008, 0.142),
        (0.020, 0.080),
        (0.010, 0.050),
        (-0.005, 0.055),
        (-0.050, 0.056),
    ]
    inner_profile = [
        (-0.050, 0.085),
        (-0.058, 0.160),
        (-0.050, 0.242),
        (-0.028, 0.308),
        (-0.004, 0.348),
        (0.010, 0.352),
        (0.004, 0.292),
        (-0.006, 0.210),
        (0.000, 0.120),
        (0.010, 0.095),
        (0.004, 0.088),
        (-0.008, 0.094),
    ]
    arm_outer = (
        cq.Workplane("XZ").polyline(outer_profile).close().extrude(0.030).translate((0.0, 0.015, -0.004))
    )
    arm_inner = (
        cq.Workplane("XZ").polyline(inner_profile).close().extrude(0.034).translate((0.0, 0.017, -0.004))
    )
    arm = arm_outer.cut(arm_inner)

    return base.union(arm)
def _stage_plate_shape() -> cq.Workplane:
    plate = cq.Workplane("XY").box(0.106, 0.124, 0.008)
    opening = cq.Workplane("XY").box(0.026, 0.058, 0.020)
    finger_cut = cq.Workplane("XY").box(0.040, 0.018, 0.020).translate((0.040, 0.000, 0.0))
    return plate.cut(opening).cut(finger_cut)
def _head_shape() -> cq.Workplane:
    carriage = cq.Workplane("XY").box(0.052, 0.050, 0.102).translate((-0.035, 0.0, 0.078))
    guide_clearance = cq.Workplane("XY").box(0.024, 0.038, 0.192).translate((-0.035, 0.0, 0.060))
    carriage = carriage.cut(guide_clearance)

    bridge = cq.Workplane("XY").box(0.060, 0.040, 0.052).translate((-0.018, 0.0, 0.024))
    head_body = (
        cq.Workplane("XY")
        .box(0.060, 0.050, 0.030)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -25.0)
        .translate((-0.040, 0.0, 0.114))
    )
    eyepiece_tube = (
        cq.Workplane("XY")
        .cylinder(0.074, 0.014)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -25.0)
        .translate((-0.064, 0.0, 0.142))
    )
    eyepiece_collar = (
        cq.Workplane("XY")
        .cylinder(0.026, 0.016)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -25.0)
        .translate((-0.094, 0.0, 0.157))
    )
    return carriage.union(bridge).union(head_body).union(eyepiece_tube).union(eyepiece_collar)
def _stage_carriage_shape() -> cq.Workplane:
    frame = cq.Workplane("XY").box(0.100, 0.088, 0.006).translate((0.0, 0.0, 0.003))
    aperture = cq.Workplane("XY").box(0.024, 0.056, 0.012).translate((0.0, 0.0, 0.003))
    frame = frame.cut(aperture)

    side_block = cq.Workplane("XY").box(0.030, 0.028, 0.012).translate((0.010, 0.056, 0.006))
    pusher = cq.Workplane("XY").box(0.014, 0.014, 0.010).translate((0.022, 0.050, 0.012))
    return frame.union(side_block).union(pusher)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="student_monocular_microscope")

    model.material("frame_ivory", rgba=(0.84, 0.84, 0.80, 1.0))
    model.material("base_black", rgba=(0.12, 0.12, 0.13, 1.0))
    model.material("trim_black", rgba=(0.08, 0.08, 0.09, 1.0))
    model.material("guide_gray", rgba=(0.30, 0.32, 0.35, 1.0))
    model.material("metal", rgba=(0.72, 0.74, 0.78, 1.0))

    stand = model.part("stand")
    stand.visual(
        mesh_from_cadquery(_stand_shell_shape(), "stand_shell"),
        material="frame_ivory",
        name="stand_shell",
    )
    stand.visual(
        Box((0.016, 0.030, 0.150)),
        origin=Origin(xyz=(0.045, 0.000, 0.295)),
        material="guide_gray",
        name="guide_column",
    )
    stand.visual(
        mesh_from_cadquery(_stage_plate_shape(), "stage_plate"),
        origin=Origin(xyz=(0.085, 0.000, 0.190)),
        material="base_black",
        name="stage_plate",
    )
    stand.visual(
        Box((0.024, 0.034, 0.070)),
        origin=Origin(xyz=(0.020, 0.000, 0.151)),
        material="frame_ivory",
        name="stage_bracket",
    )
    stand.visual(
        Box((0.050, 0.028, 0.020)),
        origin=Origin(xyz=(0.025, 0.000, 0.220)),
        material="frame_ivory",
        name="guide_strut",
    )
    stand.visual(
        Cylinder(radius=0.030, length=0.006),
        origin=Origin(xyz=(0.085, 0.000, 0.183)),
        material="trim_black",
        name="condenser_flange",
    )
    stand.visual(
        Cylinder(radius=0.022, length=0.030),
        origin=Origin(xyz=(0.085, 0.000, 0.171)),
        material="trim_black",
        name="condenser_housing",
    )
    stand.visual(
        Cylinder(radius=0.016, length=0.010),
        origin=Origin(xyz=(0.085, 0.000, 0.151)),
        material="trim_black",
        name="condenser_lower",
    )
    stand.visual(
        Box((0.020, 0.016, 0.008)),
        origin=Origin(xyz=(0.097, 0.020, 0.168)),
        material="trim_black",
        name="pivot_bridge",
    )
    stand.visual(
        Cylinder(radius=0.004, length=0.008),
        origin=Origin(xyz=(0.105, 0.024, 0.164)),
        material="trim_black",
        name="pivot_post",
    )
    stand.visual(
        Box((0.220, 0.150, 0.006)),
        origin=Origin(xyz=(0.000, 0.000, 0.003)),
        material="base_black",
        name="base_pad",
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shape(), "head_shell"),
        material="frame_ivory",
        name="head_shell",
    )
    head.visual(
        Cylinder(radius=0.018, length=0.020),
        origin=Origin(xyz=(0.000, 0.000, 0.000)),
        material="frame_ivory",
        name="nose_mount",
    )
    head.visual(
        Cylinder(radius=0.016, length=0.018),
        origin=Origin(
            xyz=(-0.106, 0.000, 0.162),
            rpy=(0.0, math.radians(-25.0), 0.0),
        ),
        material="trim_black",
        name="eyecup",
    )

    turret = model.part("turret")
    turret.visual(
        Cylinder(radius=0.025, length=0.018),
        origin=Origin(xyz=(0.000, 0.000, -0.009)),
        material="metal",
        name="turret_hub",
    )
    for angle_deg, upper_len, lower_len in (
        (0.0, 0.010, 0.014),
        (120.0, 0.010, 0.012),
        (240.0, 0.010, 0.010),
    ):
        angle = math.radians(angle_deg)
        x_pos = 0.014 * math.cos(angle)
        y_pos = 0.014 * math.sin(angle)
        turret.visual(
            Cylinder(radius=0.007, length=upper_len),
            origin=Origin(xyz=(x_pos, y_pos, -0.021)),
            material="metal",
            name=f"objective_upper_{int(angle_deg)}",
        )
        turret.visual(
            Cylinder(radius=0.0055, length=lower_len),
            origin=Origin(xyz=(x_pos, y_pos, -0.031)),
            material="metal",
            name=f"objective_lower_{int(angle_deg)}",
        )

    stage_carriage = model.part("stage_carriage")
    stage_carriage.visual(
        mesh_from_cadquery(_stage_carriage_shape(), "stage_carriage"),
        material="trim_black",
        name="carriage_frame",
    )
    stage_carriage.visual(
        Cylinder(radius=0.008, length=0.012),
        origin=Origin(xyz=(0.010, 0.076, 0.006), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="trim_black",
        name="carriage_knob",
    )

    diaphragm_lever = model.part("diaphragm_lever")
    diaphragm_lever.visual(
        Cylinder(radius=0.0035, length=0.006),
        origin=Origin(xyz=(0.000, 0.000, -0.003)),
        material="trim_black",
        name="pivot_barrel",
    )
    diaphragm_lever.visual(
        Box((0.028, 0.006, 0.004)),
        origin=Origin(xyz=(0.016, 0.000, -0.004)),
        material="trim_black",
        name="lever_blade",
    )
    diaphragm_lever.visual(
        Box((0.010, 0.012, 0.003)),
        origin=Origin(xyz=(0.032, 0.000, -0.004)),
        material="trim_black",
        name="lever_tip",
    )

    model.articulation(
        "head_slide",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=head,
        origin=Origin(xyz=(0.085, 0.000, 0.250)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=25.0, velocity=0.050, lower=0.0, upper=0.045),
    )
    model.articulation(
        "turret_spin",
        ArticulationType.CONTINUOUS,
        parent=head,
        child=turret,
        origin=Origin(xyz=(0.000, 0.000, -0.010)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=3.0, velocity=6.0),
    )
    model.articulation(
        "stage_slide",
        ArticulationType.PRISMATIC,
        parent=stand,
        child=stage_carriage,
        origin=Origin(xyz=(0.085, 0.000, 0.194)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=0.040, lower=-0.018, upper=0.018),
    )
    model.articulation(
        "diaphragm_lever_joint",
        ArticulationType.REVOLUTE,
        parent=stand,
        child=diaphragm_lever,
        origin=Origin(xyz=(0.105, 0.024, 0.160)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=3.0,
            lower=math.radians(-45.0),
            upper=math.radians(20.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
