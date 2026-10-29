# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bench_vise_with_prismatic_jaw, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bench_vise_with_prismatic_jaw

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
def _box(dx: float, dy: float, dz: float, cx: float, cy: float, cz: float):
    return cq.Workplane("XY").box(dx, dy, dz).translate((cx, cy, cz))
def _x_cylinder(radius: float, length: float, x0: float, y: float, z: float):
    return cq.Workplane("YZ").circle(radius).extrude(length).translate((x0, y, z))
def _x_rect_cut(width_y: float, height_z: float, length: float, x0: float, y: float, z: float):
    return cq.Workplane("YZ").rect(width_y, height_z).extrude(length).translate((x0, y, z))
def _z_cylinder(radius: float, length: float, x: float, y: float, z0: float):
    return cq.Workplane("XY").circle(radius).extrude(length).translate((x, y, z0))
def _make_base_body():
    """One-piece cast base with the fixed rear jaw and through mounting slots."""
    body = _box(0.400, 0.180, 0.025, 0.000, 0.000, 0.0125)
    body = body.union(_box(0.078, 0.156, 0.112, 0.111, 0.000, 0.081))
    body = body.union(_box(0.040, 0.126, 0.026, 0.100, 0.000, 0.038))
    body = body.union(_box(0.044, 0.052, 0.060, 0.151, 0.000, 0.070))

    # A round central bore clears the fine-adjust screw where it runs through
    # the rear jaw/nut casting.
    body = body.cut(_x_cylinder(0.017, 0.120, 0.048, 0.000, 0.065))

    # Four drill-table mounting slots in the flat base plate.
    for sx in (-0.125, 0.125):
        for sy in (-0.060, 0.060):
            body = body.cut(_box(0.036, 0.014, 0.040, sx, sy, 0.014))
            body = body.cut(_z_cylinder(0.007, 0.040, sx - 0.018, sy, -0.004))
            body = body.cut(_z_cylinder(0.007, 0.040, sx + 0.018, sy, -0.004))
    return body
def _make_moving_jaw_body():
    """Sliding front jaw casting with square guide-bar bores and screw clearance."""
    body = _box(0.058, 0.152, 0.088, -0.029, 0.000, 0.096)
    body = body.union(_box(0.074, 0.132, 0.030, -0.039, 0.000, 0.044))

    for y in (-0.045, 0.045):
        body = body.union(_box(0.102, 0.040, 0.040, -0.052, y, 0.055))

    # Side boss for the quick-release cam lever pivot.
    body = body.union(_box(0.038, 0.020, 0.038, -0.042, -0.085, 0.081))

    # Two square through-holes ride over the fixed guide bars with visible
    # clearance rather than interpenetrating them.
    for y in (-0.045, 0.045):
        body = body.cut(_x_rect_cut(0.024, 0.024, 0.140, -0.120, y, 0.040))

    # A central clearance bore lets the screw spin through the moving jaw.
    body = body.cut(_x_cylinder(0.015, 0.145, -0.118, 0.000, 0.065))
    return body
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="quick_action_drill_press_vise")

    cast_iron = model.material("dark_cast_iron", rgba=(0.10, 0.105, 0.11, 1.0))
    machined = model.material("machined_steel", rgba=(0.58, 0.60, 0.58, 1.0))
    blackened = model.material("blackened_steel", rgba=(0.025, 0.026, 0.028, 1.0))
    worn_edge = model.material("polished_wear", rgba=(0.78, 0.76, 0.70, 1.0))
    red_grip = model.material("red_release_grip", rgba=(0.75, 0.04, 0.025, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_make_base_body(), "base_casting", tolerance=0.0008),
        material=cast_iron,
        name="base_casting",
    )

    # Two fixed square-section guide bars, visibly captured in the rear casting.
    base.visual(
        Box((0.300, 0.018, 0.018)),
        origin=Origin(xyz=(-0.035, -0.045, 0.040)),
        material=machined,
        name="guide_bar_0",
    )
    base.visual(
        Box((0.300, 0.018, 0.018)),
        origin=Origin(xyz=(-0.035, 0.045, 0.040)),
        material=machined,
        name="guide_bar_1",
    )

    base.visual(
        Box((0.010, 0.140, 0.052)),
        origin=Origin(xyz=(0.075, 0.000, 0.105)),
        material=worn_edge,
        name="fixed_jaw_plate",
    )
    for i, z in enumerate((0.086, 0.096, 0.106, 0.116, 0.126)):
        base.visual(
            Box((0.003, 0.142, 0.003)),
            origin=Origin(xyz=(0.0685, 0.000, z)),
            material=machined,
            name=f"fixed_jaw_tooth_{i}",
        )

    moving_jaw = model.part("moving_jaw")
    moving_jaw.visual(
        mesh_from_cadquery(_make_moving_jaw_body(), "moving_jaw_casting", tolerance=0.0008),
        material=cast_iron,
        name="moving_jaw_casting",
    )
    moving_jaw.visual(
        Box((0.010, 0.140, 0.052)),
        origin=Origin(xyz=(0.005, 0.000, 0.105)),
        material=worn_edge,
        name="moving_jaw_plate",
    )
    for i, z in enumerate((0.086, 0.096, 0.106, 0.116, 0.126)):
        moving_jaw.visual(
            Box((0.003, 0.142, 0.003)),
            origin=Origin(xyz=(0.0115, 0.000, z)),
            material=machined,
            name=f"moving_jaw_tooth_{i}",
        )

    slide = model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=base,
        child=moving_jaw,
        origin=Origin(xyz=(0.045, 0.000, 0.000)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=450.0, velocity=0.35, lower=0.0, upper=0.120),
    )

    screw_handle = model.part("screw_handle")
    screw_handle.visual(
        Cylinder(radius=0.009, length=0.345),
        origin=Origin(xyz=(0.1325, 0.000, 0.000), rpy=(0.0, pi / 2.0, 0.0)),
        material=machined,
        name="threaded_screw",
    )
    for i, x in enumerate((0.050, 0.075, 0.100, 0.125, 0.150, 0.175, 0.200, 0.225)):
        screw_handle.visual(
            Cylinder(radius=0.0098, length=0.003),
            origin=Origin(xyz=(x, 0.000, 0.000), rpy=(0.0, pi / 2.0, 0.0)),
            material=blackened,
            name=f"screw_thread_band_{i}",
        )
    screw_handle.visual(
        Cylinder(radius=0.018, length=0.026),
        origin=Origin(xyz=(-0.034, 0.000, 0.000), rpy=(0.0, pi / 2.0, 0.0)),
        material=blackened,
        name="handle_hub",
    )
    screw_handle.visual(
        Cylinder(radius=0.006, length=0.145),
        origin=Origin(xyz=(-0.040, 0.000, 0.000), rpy=(pi / 2.0, 0.0, 0.0)),
        material=machined,
        name="tommy_bar",
    )
    screw_handle.visual(
        Sphere(radius=0.012),
        origin=Origin(xyz=(-0.040, -0.0725, 0.000)),
        material=blackened,
        name="handle_knob_0",
    )
    screw_handle.visual(
        Sphere(radius=0.012),
        origin=Origin(xyz=(-0.040, 0.0725, 0.000)),
        material=blackened,
        name="handle_knob_1",
    )

    screw = model.articulation(
        "screw_spin",
        ArticulationType.CONTINUOUS,
        parent=moving_jaw,
        child=screw_handle,
        origin=Origin(xyz=(-0.075, 0.000, 0.065)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=65.0, velocity=6.0),
    )

    cam_lever = model.part("cam_lever")
    cam_lever.visual(
        Cylinder(radius=0.018, length=0.014),
        origin=Origin(xyz=(0.000, -0.006, 0.000), rpy=(pi / 2.0, 0.0, 0.0)),
        material=blackened,
        name="cam_pivot",
    )
    cam_lever.visual(
        Box((0.018, 0.012, 0.070)),
        origin=Origin(xyz=(-0.020, -0.006, -0.034), rpy=(0.0, -0.22, 0.0)),
        material=blackened,
        name="lever_arm",
    )
    cam_lever.visual(
        Cylinder(radius=0.014, length=0.034),
        origin=Origin(xyz=(-0.032, -0.006, -0.064), rpy=(pi / 2.0, 0.0, 0.0)),
        material=red_grip,
        name="lever_grip",
    )

    cam = model.articulation(
        "cam_release",
        ArticulationType.REVOLUTE,
        parent=moving_jaw,
        child=cam_lever,
        origin=Origin(xyz=(-0.042, -0.096, 0.081)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=3.0, lower=-0.80, upper=0.80),
    )

    # Keep names referenced so static analysis does not confuse these authored
    # mechanisms with unused construction locals.
    assert slide is not None and screw is not None and cam is not None
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
