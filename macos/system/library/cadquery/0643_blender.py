# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blender, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blender

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
import math
import cadquery as cq
BODY_W = 0.24
BODY_H = 0.072
TOWER_H = 0.135
CUP_PIVOT_Y = -0.022
CUP_PIVOT_Z = 0.118
CUP_CENTER_Y = 0.034
CUP_BOTTOM_Z = -0.028
CUP_TOP_Z = 0.120
CUP_BOTTOM_R = 0.042
CUP_TOP_R = 0.056
CUP_WALL = 0.0035
CUP_FLOOR = 0.006
CLAMP_HINGE_Y = 0.088
CLAMP_HINGE_Z = 0.253
CLAMP_REACH = 0.094
BLADE_AXIS_REL = (0.0, CUP_CENTER_Y, CUP_BOTTOM_Z + CUP_FLOOR)
def _x_cylinder(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(radius)
        .extrude(length)
        .translate((center[0] - length / 2.0, center[1], center[2]))
    )
def _make_housing_shape() -> cq.Workplane:
    rear_box = cq.Workplane("XY").box(BODY_W * 0.92, 0.110, BODY_H + TOWER_H).translate((0.0, 0.125, (BODY_H + TOWER_H) / 2.0))
    front_foot = cq.Workplane("XY").box(0.140, 0.042, 0.040).translate((0.0, -0.096, 0.020))
    center_spine = cq.Workplane("XY").box(0.040, 0.235, 0.040).translate((0.0, 0.0075, 0.020))
    return rear_box.union(front_foot).union(center_spine)
def _make_support_shape(sign: float) -> cq.Workplane:
    yoke_x = sign * 0.068
    yoke = cq.Workplane("XY").box(0.016, 0.068, 0.108).translate((yoke_x, -0.028, 0.126))
    lower_arm = cq.Workplane("XY").box(0.040, 0.080, 0.040).translate((sign * 0.0922, -0.030, 0.082))
    rear_rail = cq.Workplane("XY").box(0.024, 0.110, 0.130).translate((sign * 0.1224, 0.055, 0.095))
    return yoke.union(lower_arm).union(rear_rail)
def _make_hinge_mount_shape() -> cq.Workplane:
    pedestal = cq.Workplane("XY").box(0.152, 0.016, 0.040).translate((0.0, 0.106, CLAMP_HINGE_Z - 0.028))
    posts = cq.Workplane("XY").box(0.020, 0.018, 0.040).translate((0.050, 0.106, CLAMP_HINGE_Z - 0.020))
    posts = posts.union(cq.Workplane("XY").box(0.020, 0.018, 0.040).translate((-0.050, 0.106, CLAMP_HINGE_Z - 0.020)))
    return pedestal.union(posts)
def _make_cup_shape() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .workplane(offset=CUP_BOTTOM_Z)
        .circle(CUP_BOTTOM_R)
        .workplane(offset=CUP_TOP_Z - CUP_BOTTOM_Z)
        .circle(CUP_TOP_R)
        .loft(combine=True)
        .translate((0.0, CUP_CENTER_Y, 0.0))
    )
    inner = (
        cq.Workplane("XY")
        .workplane(offset=CUP_BOTTOM_Z + CUP_FLOOR)
        .circle(CUP_BOTTOM_R - CUP_WALL - 0.001)
        .workplane(offset=CUP_TOP_Z - CUP_BOTTOM_Z - CUP_FLOOR)
        .circle(CUP_TOP_R - CUP_WALL)
        .loft(combine=True)
        .translate((0.0, CUP_CENTER_Y, 0.0))
    )
    body = outer.cut(inner)

    pour_notch = cq.Workplane("XY").box(0.026, 0.018, 0.020).translate((0.0, CUP_CENTER_Y - CUP_TOP_R + 0.004, CUP_TOP_Z - 0.004))
    body = body.cut(pour_notch)

    lug_x = 0.049
    lug_bridge = cq.Workplane("XY").box(0.020, 0.034, 0.020).translate((lug_x, 0.014, 0.001))
    lug_bridge = lug_bridge.union(cq.Workplane("XY").box(0.020, 0.034, 0.020).translate((-lug_x, 0.014, 0.001)))

    pin_collars = _x_cylinder(0.009, 0.016, (0.052, 0.000, 0.000))
    pin_collars = pin_collars.union(_x_cylinder(0.009, 0.016, (-0.052, 0.000, 0.000)))
    drive_boss = (
        cq.Workplane("XY")
        .circle(0.015)
        .extrude(0.008)
        .translate((0.0, CUP_CENTER_Y, CUP_BOTTOM_Z - 0.008))
    )

    return body.union(lug_bridge).union(pin_collars).union(drive_boss)
def _make_clamp_frame_shape() -> cq.Workplane:
    arm_x = 0.054
    arm = cq.Workplane("XY").box(0.016, CLAMP_REACH, 0.014).translate((arm_x, -CLAMP_REACH / 2.0, 0.008))
    arm = arm.union(
        cq.Workplane("XY").box(0.016, CLAMP_REACH, 0.014).translate((-arm_x, -CLAMP_REACH / 2.0, 0.008))
    )
    front_bar = cq.Workplane("XY").box(0.118, 0.018, 0.014).translate((0.0, -CLAMP_REACH, 0.008))
    rear_cross = cq.Workplane("XY").box(0.118, 0.014, 0.012).translate((0.0, -0.010, 0.008))
    barrels = _x_cylinder(0.009, 0.022, (0.054, 0.000, 0.000))
    barrels = barrels.union(_x_cylinder(0.009, 0.022, (-0.054, 0.000, 0.000)))
    return arm.union(front_bar).union(rear_cross).union(barrels)
def _make_blade_shape() -> cq.Workplane:
    shaft = cq.Workplane("XY").circle(0.004).extrude(0.024)
    hub = cq.Workplane("XY").circle(0.011).extrude(0.008).translate((0.0, 0.0, 0.008))
    blade_a = cq.Workplane("XY").box(0.050, 0.010, 0.002).translate((0.0, 0.0, 0.017))
    blade_a = blade_a.rotate((0.0, 0.0, 0.017), (0.0, 1.0, 0.017), 12.0).rotate((0.0, 0.0, 0.017), (0.0, 0.0, 1.0), 18.0)
    blade_b = cq.Workplane("XY").box(0.046, 0.010, 0.002).translate((0.0, 0.0, 0.015))
    blade_b = blade_b.rotate((0.0, 0.0, 0.015), (0.0, 1.0, 0.015), -12.0).rotate((0.0, 0.0, 0.015), (0.0, 0.0, 1.0), 108.0)
    return shaft.union(hub).union(blade_a).union(blade_b)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="laboratory_blender")

    housing_finish = model.material("housing_finish", rgba=(0.84, 0.86, 0.88, 1.0))
    dark_trim = model.material("dark_trim", rgba=(0.18, 0.20, 0.22, 1.0))
    cup_finish = model.material("cup_finish", rgba=(0.70, 0.78, 0.82, 0.55))
    steel = model.material("steel", rgba=(0.74, 0.76, 0.79, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_make_housing_shape(), "housing_shell"),
        material=housing_finish,
        name="housing_shell",
    )

    support_0 = model.part("support_0")
    support_0.visual(
        mesh_from_cadquery(_make_support_shape(1.0), "support_0_shell"),
        material=housing_finish,
        name="support_0_shell",
    )

    support_1 = model.part("support_1")
    support_1.visual(
        mesh_from_cadquery(_make_support_shape(-1.0), "support_1_shell"),
        material=housing_finish,
        name="support_1_shell",
    )

    hinge_mount = model.part("hinge_mount")
    hinge_mount.visual(
        mesh_from_cadquery(_make_hinge_mount_shape(), "hinge_mount_shell"),
        material=housing_finish,
        name="hinge_mount_shell",
    )

    cup = model.part("cup")
    cup.visual(
        mesh_from_cadquery(_make_cup_shape(), "cup_body"),
        material=cup_finish,
        name="cup_body",
    )

    clamp = model.part("clamp")
    clamp.visual(
        mesh_from_cadquery(_make_clamp_frame_shape(), "clamp_frame"),
        material=dark_trim,
        name="clamp_frame",
    )
    clamp.visual(
        Box((0.084, 0.018, 0.014)),
        origin=Origin(xyz=(0.0, -CLAMP_REACH, -0.005)),
        material=steel,
        name="clamp_pad",
    )

    blade = model.part("blade")
    blade.visual(
        mesh_from_cadquery(_make_blade_shape(), "blade_rotor"),
        material=steel,
        name="blade_rotor",
    )

    model.articulation(
        "housing_to_support_0",
        ArticulationType.FIXED,
        parent=housing,
        child=support_0,
        origin=Origin(),
    )
    model.articulation(
        "housing_to_support_1",
        ArticulationType.FIXED,
        parent=housing,
        child=support_1,
        origin=Origin(),
    )
    model.articulation(
        "housing_to_hinge_mount",
        ArticulationType.FIXED,
        parent=housing,
        child=hinge_mount,
        origin=Origin(),
    )
    model.articulation(
        "cup_pitch",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=cup,
        origin=Origin(xyz=(0.0, CUP_PIVOT_Y, CUP_PIVOT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.72, effort=14.0, velocity=1.4),
    )
    model.articulation(
        "clamp_hinge",
        ArticulationType.REVOLUTE,
        parent=hinge_mount,
        child=clamp,
        origin=Origin(xyz=(0.0, CLAMP_HINGE_Y, CLAMP_HINGE_Z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.20, effort=8.0, velocity=1.8),
    )
    model.articulation(
        "blade_spin",
        ArticulationType.CONTINUOUS,
        parent=cup,
        child=blade,
        origin=Origin(xyz=BLADE_AXIS_REL),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=40.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
