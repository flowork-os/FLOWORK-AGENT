# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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
def build_barrel_shell() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(0.030)
        .circle(0.023)
        .extrude(0.422)
        .translate((0.0, 0.0, 0.014))
    )
def build_gauge_bezel() -> cq.Workplane:
    outer = (
        cq.Workplane("XZ")
        .center(0.0, 0.090)
        .circle(0.037)
        .extrude(0.022)
        .translate((0.0, 0.052, 0.0))
    )
    cavity = (
        cq.Workplane("XZ")
        .center(0.0, 0.090)
        .circle(0.031)
        .extrude(0.016)
        .translate((0.0, 0.058, 0.0))
    )
    return outer.cut(cavity)
def build_grip_sleeve() -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(0.019)
        .circle(0.012)
        .extrude(0.072)
        .translate((-0.036, 0.0, 0.0))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="floor_pump")

    model.material("frame_black", rgba=(0.13, 0.13, 0.14, 1.0))
    model.material("barrel_red", rgba=(0.73, 0.10, 0.10, 1.0))
    model.material("steel", rgba=(0.71, 0.73, 0.76, 1.0))
    model.material("rubber", rgba=(0.08, 0.08, 0.08, 1.0))
    model.material("gauge_white", rgba=(0.94, 0.94, 0.92, 1.0))
    model.material("needle_yellow", rgba=(0.94, 0.72, 0.10, 1.0))

    frame = model.part("frame")
    frame.visual(
        Box((0.300, 0.120, 0.016)),
        origin=Origin(xyz=(0.0, 0.0, 0.008)),
        material="frame_black",
        name="base",
    )
    frame.visual(
        Box((0.070, 0.040, 0.064)),
        origin=Origin(xyz=(0.0, -0.020, 0.048)),
        material="frame_black",
        name="lower_brace",
    )
    frame.visual(
        Box((0.018, 0.024, 0.438)),
        origin=Origin(xyz=(-0.050, -0.022, 0.235)),
        material="frame_black",
        name="support_0",
    )
    frame.visual(
        Box((0.018, 0.024, 0.438)),
        origin=Origin(xyz=(0.050, -0.022, 0.235)),
        material="frame_black",
        name="support_1",
    )
    frame.visual(
        Box((0.160, 0.020, 0.020)),
        origin=Origin(xyz=(0.0, -0.022, 0.455)),
        material="frame_black",
        name="top_bridge",
    )
    frame.visual(
        mesh_from_cadquery(build_barrel_shell(), "barrel_shell"),
        material="barrel_red",
        name="barrel_shell",
    )
    frame.visual(
        Box((0.018, 0.054, 0.016)),
        origin=Origin(xyz=(0.0, 0.027, 0.090)),
        material="frame_black",
        name="gauge_stem",
    )
    frame.visual(
        Box((0.006, 0.020, 0.024)),
        origin=Origin(xyz=(-0.0115, 0.0, 0.448)),
        material="frame_black",
        name="guide_0",
    )
    frame.visual(
        Box((0.006, 0.020, 0.024)),
        origin=Origin(xyz=(0.0115, 0.0, 0.448)),
        material="frame_black",
        name="guide_1",
    )
    frame.visual(
        Box((0.020, 0.006, 0.024)),
        origin=Origin(xyz=(0.0, -0.0115, 0.448)),
        material="frame_black",
        name="guide_2",
    )
    frame.visual(
        Box((0.020, 0.006, 0.024)),
        origin=Origin(xyz=(0.0, 0.0115, 0.448)),
        material="frame_black",
        name="guide_3",
    )
    frame.visual(
        mesh_from_cadquery(build_gauge_bezel(), "gauge_bezel"),
        material="gauge_white",
        name="gauge_bezel",
    )
    frame.visual(
        Cylinder(radius=0.0025, length=0.010),
        origin=Origin(xyz=(0.0, 0.058, 0.090), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="steel",
        name="gauge_axle",
    )
    frame.visual(
        Box((0.010, 0.036, 0.010)),
        origin=Origin(xyz=(0.061, 0.000, 0.340)),
        material="frame_black",
        name="hook_arm",
    )
    frame.visual(
        Box((0.010, 0.010, 0.020)),
        origin=Origin(xyz=(0.061, 0.018, 0.349)),
        material="frame_black",
        name="hook_tip",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.0085, length=0.500),
        origin=Origin(xyz=(0.0, 0.0, -0.040)),
        material="steel",
        name="rod",
    )
    handle.visual(
        Cylinder(radius=0.012, length=0.260),
        origin=Origin(xyz=(0.0, 0.0, 0.205), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="rubber",
        name="crossbar",
    )
    handle.visual(
        Cylinder(radius=0.015, length=0.026),
        origin=Origin(xyz=(0.0, 0.0, 0.167)),
        material="frame_black",
        name="handle_boss",
    )

    grip = model.part("grip")
    grip.visual(
        mesh_from_cadquery(build_grip_sleeve(), "grip_sleeve"),
        material="steel",
        name="sleeve",
    )
    grip.visual(
        Box((0.014, 0.022, 0.044)),
        origin=Origin(xyz=(-0.024, 0.014, -0.038)),
        material="frame_black",
        name="link_0",
    )
    grip.visual(
        Box((0.014, 0.022, 0.044)),
        origin=Origin(xyz=(0.024, 0.014, -0.038)),
        material="frame_black",
        name="link_1",
    )
    grip.visual(
        Cylinder(radius=0.013, length=0.110),
        origin=Origin(xyz=(0.0, 0.032, -0.060), rpy=(0.0, math.pi / 2.0, 0.0)),
        material="rubber",
        name="grip_bar",
    )

    needle = model.part("needle")
    needle.visual(
        Cylinder(radius=0.005, length=0.006),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material="needle_yellow",
        name="hub",
    )
    needle.visual(
        Box((0.003, 0.002, 0.024)),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material="needle_yellow",
        name="pointer",
    )
    needle.visual(
        Box((0.006, 0.002, 0.007)),
        origin=Origin(xyz=(0.0, 0.0, -0.004)),
        material="needle_yellow",
        name="counterweight",
    )

    model.articulation(
        "frame_to_handle",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=handle,
        origin=Origin(xyz=(0.0, 0.0, 0.436)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.180, effort=40.0, velocity=0.6),
    )
    model.articulation(
        "handle_to_grip",
        ArticulationType.CONTINUOUS,
        parent=handle,
        child=grip,
        origin=Origin(xyz=(0.045, 0.0, 0.205)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=6.0),
    )
    model.articulation(
        "frame_to_needle",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=needle,
        origin=Origin(xyz=(0.0, 0.066, 0.090)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.2, upper=1.2, effort=0.2, velocity=8.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
