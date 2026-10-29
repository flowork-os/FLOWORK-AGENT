# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_flash, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_flash

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
def _body_shell_shape():
    lower = (
        cq.Workplane("XY")
        .box(0.064, 0.044, 0.082)
        .edges("|Z")
        .fillet(0.005)
        .translate((0.000, 0.000, 0.059))
    )
    shoulder = (
        cq.Workplane("XY")
        .box(0.056, 0.040, 0.014)
        .edges("|Z")
        .fillet(0.003)
        .translate((0.004, 0.000, 0.100))
    )
    neck = (
        cq.Workplane("XY")
        .box(0.026, 0.028, 0.014)
        .edges("|Z")
        .fillet(0.0025)
        .translate((0.006, 0.000, 0.107))
    )
    return lower.union(shoulder).union(neck)
def _shoe_mount_shape():
    foot = cq.Workplane("XY").box(0.020, 0.018, 0.003).translate((0.000, 0.000, 0.0015))
    left_rail = cq.Workplane("XY").box(0.020, 0.002, 0.004).translate((0.000, 0.008, 0.0035))
    right_rail = cq.Workplane("XY").box(0.020, 0.002, 0.004).translate((0.000, -0.008, 0.0035))
    riser = (
        cq.Workplane("XY")
        .box(0.015, 0.016, 0.015)
        .edges("|Z")
        .fillet(0.0015)
        .translate((0.000, 0.000, 0.0105))
    )
    lock_wheel = (
        cq.Workplane("XY")
        .cylinder(0.005, 0.005)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((-0.006, -0.0105, 0.010))
    )
    clamp_tab = cq.Workplane("XY").box(0.004, 0.009, 0.002).translate((-0.001, -0.0095, 0.014))
    return foot.union(left_rail).union(right_rail).union(riser).union(lock_wheel).union(clamp_tab)
def _control_strip_shape():
    housing = (
        cq.Workplane("XY")
        .box(0.022, 0.014, 0.072)
        .edges("|Z")
        .fillet(0.002)
    )
    for slot_z in (-0.021, 0.0, 0.021):
        cutter = cq.Workplane("XY").box(0.016, 0.013, 0.016).translate((0.000, 0.0005, slot_z))
        housing = housing.cut(cutter)
    return housing
def _swivel_mount_shape():
    collar = cq.Workplane("XY").cylinder(0.012, 0.015)
    spine = (
        cq.Workplane("XY")
        .box(0.020, 0.028, 0.016)
        .edges("|Z")
        .fillet(0.002)
        .translate((0.004, 0.000, 0.010))
    )
    bridge = cq.Workplane("XY").box(0.012, 0.090, 0.012).translate((0.009, 0.000, 0.022))
    left_arm = (
        cq.Workplane("XY")
        .box(0.018, 0.006, 0.024)
        .edges("|Z")
        .fillet(0.001)
        .translate((0.023, 0.044, 0.022))
    )
    right_arm = (
        cq.Workplane("XY")
        .box(0.018, 0.006, 0.024)
        .edges("|Z")
        .fillet(0.001)
        .translate((0.023, -0.044, 0.022))
    )
    return collar.union(spine).union(bridge).union(left_arm).union(right_arm)
def _head_shell_shape():
    shell = (
        cq.Workplane("XY")
        .box(0.042, 0.074, 0.041)
        .edges("|Z")
        .fillet(0.004)
        .translate((0.017, 0.000, 0.008))
    )
    visor = cq.Workplane("XY").box(0.006, 0.074, 0.020).translate((-0.001, 0.000, 0.016))
    return shell.union(visor)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_speedlight_flash")

    shell_black = model.material("shell_black", rgba=(0.12, 0.13, 0.14, 1.0))
    shell_dark = model.material("shell_dark", rgba=(0.18, 0.19, 0.21, 1.0))
    panel_dark = model.material("panel_dark", rgba=(0.08, 0.09, 0.10, 1.0))
    button_gray = model.material("button_gray", rgba=(0.30, 0.32, 0.35, 1.0))
    shoe_metal = model.material("shoe_metal", rgba=(0.57, 0.60, 0.64, 1.0))
    diffuser = model.material("diffuser", rgba=(0.92, 0.95, 0.97, 0.82))
    sensor_red = model.material("sensor_red", rgba=(0.64, 0.12, 0.10, 0.85))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell_shape(), "speedlight_body_shell"),
        material=shell_black,
        name="body_shell",
    )
    body.visual(
        mesh_from_cadquery(_shoe_mount_shape(), "speedlight_shoe_mount"),
        material=shoe_metal,
        name="shoe_mount",
    )
    body.visual(
        Box((0.036, 0.0015, 0.054)),
        origin=Origin(xyz=(-0.002, -0.02275, 0.060)),
        material=panel_dark,
        name="battery_door",
    )
    body.visual(
        Box((0.0014, 0.016, 0.012)),
        origin=Origin(xyz=(0.0327, 0.000, 0.056)),
        material=sensor_red,
        name="sensor_window",
    )

    control_strip = model.part("control_strip")
    control_strip.visual(
        mesh_from_cadquery(_control_strip_shape(), "speedlight_control_strip"),
        material=shell_dark,
        name="housing",
    )
    model.articulation(
        "body_to_control_strip",
        ArticulationType.FIXED,
        parent=body,
        child=control_strip,
        origin=Origin(xyz=(-0.010, 0.029, 0.066)),
    )

    button_z_positions = (0.021, 0.0, -0.021)
    for index, local_z in enumerate(button_z_positions):
        button = model.part(f"mode_button_{index}")
        button.visual(
            Box((0.016, 0.0035, 0.016)),
            origin=Origin(xyz=(0.000, 0.00175, 0.000)),
            material=button_gray,
            name="button_cap",
        )
        button.visual(
            Box((0.012, 0.0040, 0.012)),
            origin=Origin(xyz=(0.000, -0.0020, 0.000)),
            material=button_gray,
            name="stem",
        )
        model.articulation(
            f"control_strip_to_mode_button_{index}",
            ArticulationType.PRISMATIC,
            parent=control_strip,
            child=button,
            origin=Origin(xyz=(0.000, 0.007, local_z)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=4.0,
                velocity=0.04,
                lower=0.0,
                upper=0.0018,
            ),
        )

    swivel = model.part("swivel")
    swivel.visual(
        mesh_from_cadquery(_swivel_mount_shape(), "speedlight_swivel_mount"),
        material=shell_dark,
        name="mount",
    )
    model.articulation(
        "body_to_swivel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=swivel,
        origin=Origin(xyz=(0.006, 0.000, 0.120)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.0,
            lower=-1.8,
            upper=1.8,
        ),
    )

    head = model.part("head")
    head.visual(
        mesh_from_cadquery(_head_shell_shape(), "speedlight_head_shell"),
        material=shell_black,
        name="head_shell",
    )
    head.visual(
        Box((0.004, 0.066, 0.030)),
        origin=Origin(xyz=(0.040, 0.000, 0.008)),
        material=diffuser,
        name="diffuser",
    )
    head.visual(
        Cylinder(radius=0.005, length=0.004),
        origin=Origin(xyz=(0.000, 0.039, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=panel_dark,
        name="trunnion_0",
    )
    head.visual(
        Cylinder(radius=0.005, length=0.004),
        origin=Origin(xyz=(0.000, -0.039, 0.000), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=panel_dark,
        name="trunnion_1",
    )
    model.articulation(
        "swivel_to_head",
        ArticulationType.REVOLUTE,
        parent=swivel,
        child=head,
        origin=Origin(xyz=(0.026, 0.000, 0.026)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=2.0,
            lower=-0.2,
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
