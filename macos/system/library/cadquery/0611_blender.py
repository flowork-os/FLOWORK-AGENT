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
BASE_HEIGHT = 0.145
JUG_HEIGHT = 0.220
JUG_BODY_OFFSET = 0.020
FLAP_OPEN_ANGLE = math.radians(115.0)
LEVER_SWING_ANGLE = math.radians(34.0)
def _build_base_shape() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .ellipse(0.105, 0.090)
        .workplane(offset=0.028)
        .ellipse(0.100, 0.085)
        .workplane(offset=0.075)
        .ellipse(0.079, 0.074)
        .workplane(offset=0.042)
        .ellipse(0.074, 0.069)
        .loft(combine=True)
    )

    body = body.faces(">Z").workplane().circle(0.046).cutBlind(-0.006)

    lever_pad = (
        cq.Workplane("XY")
        .box(0.062, 0.018, 0.050)
        .translate((0.054, 0.086, 0.050))
    )

    return body.union(lever_pad)
def _build_jug_shell() -> cq.Workplane:
    shell = (
        cq.Workplane("XY")
        .rect(0.094, 0.092)
        .workplane(offset=0.070)
        .rect(0.112, 0.108)
        .workplane(offset=0.085)
        .rect(0.132, 0.124)
        .workplane(offset=0.065)
        .rect(0.142, 0.128)
        .loft(combine=True)
    )
    shell = shell.faces(">Z").shell(-0.004)

    spout_lip = (
        cq.Workplane("XY")
        .box(0.020, 0.046, 0.008)
        .translate((0.073, 0.0, 0.216))
    )

    return shell.union(spout_lip)
def _build_jug_handle() -> cq.Workplane:
    handle = (
        cq.Workplane("XY")
        .box(0.038, 0.024, 0.020)
        .translate((-0.079, 0.0, 0.173))
        .union(
            cq.Workplane("XY")
            .box(0.050, 0.024, 0.018)
            .translate((-0.071, 0.0, 0.062))
        )
        .union(
            cq.Workplane("XY")
            .box(0.020, 0.026, 0.122)
            .translate((-0.100, 0.0, 0.116))
        )
    )
    return handle
def _build_jug_collar() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(0.100, 0.096, 0.032)
        .translate((0.0, 0.0, 0.016))
        .cut(cq.Workplane("XY").circle(0.030).extrude(0.040))
    )
def _build_lid_shape() -> cq.Workplane:
    lid = (
        cq.Workplane("XY")
        .box(0.144, 0.130, 0.012)
        .translate((0.0, 0.0, 0.006))
    )

    plug = (
        cq.Workplane("XY")
        .box(0.088, 0.078, 0.002)
        .translate((0.0, 0.0, -0.001))
    )

    rear_bridge = cq.Workplane("XY").box(0.018, 0.070, 0.010).translate((0.011, 0.0, 0.015))
    center_dome = cq.Workplane("XY").box(0.050, 0.060, 0.008).translate((-0.014, 0.0, 0.014))

    opening = cq.Workplane("XY").box(0.056, 0.046, 0.030).translate((0.037, 0.0, 0.006))

    return lid.union(plug).union(rear_bridge).union(center_dome).cut(opening)
def _build_flap_shape() -> cq.Workplane:
    knuckle = cq.Workplane("XZ").circle(0.0035).extrude(0.044, both=True)
    panel = (
        cq.Workplane("XY")
        .box(0.048, 0.050, 0.006)
        .translate((0.024, 0.0, -0.003))
    )
    finger_lip = cq.Workplane("XY").box(0.010, 0.032, 0.010).translate((0.047, 0.0, 0.004))
    return knuckle.union(panel).union(finger_lip)
def _build_blade_shape() -> cq.Workplane:
    blade = (
        cq.Workplane("XY")
        .circle(0.014)
        .extrude(0.008)
        .translate((0.0, 0.0, -0.004))
        .union(cq.Workplane("XY").circle(0.008).extrude(0.010).translate((0.0, 0.0, 0.004)))
    )

    blade_specs = (
        (35.0, 12.0, 0.003),
        (215.0, 12.0, 0.003),
        (125.0, -12.0, 0.007),
        (305.0, -12.0, 0.007),
    )
    for yaw_deg, pitch_deg, z_pos in blade_specs:
        wing = cq.Workplane("XY").box(0.042, 0.010, 0.002).translate((0.022, 0.0, z_pos))
        wing = wing.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), pitch_deg)
        wing = wing.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), yaw_deg)
        blade = blade.union(wing)

    return blade
def _build_pulse_lever_shape() -> cq.Workplane:
    barrel = cq.Workplane("YZ").circle(0.0045).extrude(0.034, both=True)
    paddle = cq.Workplane("XY").box(0.030, 0.010, 0.068).translate((0.0, 0.008, 0.034))
    finger_tab = cq.Workplane("XY").box(0.040, 0.014, 0.012).translate((0.0, 0.010, 0.067))
    return barrel.union(paddle).union(finger_tab)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="countertop_blender")

    base_body = model.material("base_body", rgba=(0.22, 0.24, 0.27, 1.0))
    trim_black = model.material("trim_black", rgba=(0.08, 0.08, 0.09, 1.0))
    jug_clear = model.material("jug_clear", rgba=(0.82, 0.90, 0.95, 0.38))
    blade_metal = model.material("blade_metal", rgba=(0.76, 0.78, 0.80, 1.0))
    lid_black = model.material("lid_black", rgba=(0.12, 0.12, 0.13, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_build_base_shape(), "base_shell"),
        material=base_body,
        name="base_shell",
    )
    jug = model.part("jug")
    jug.visual(
        mesh_from_cadquery(_build_jug_shell(), "jar_shell"),
        origin=Origin(xyz=(0.0, 0.0, JUG_BODY_OFFSET)),
        material=jug_clear,
        name="jar_shell",
    )
    jug.visual(
        mesh_from_cadquery(_build_jug_handle(), "jug_handle"),
        origin=Origin(xyz=(0.0, 0.0, JUG_BODY_OFFSET)),
        material=trim_black,
        name="jug_handle",
    )
    jug.visual(
        mesh_from_cadquery(_build_jug_collar(), "jug_collar"),
        material=trim_black,
        name="jug_collar",
    )
    jug.visual(
        Cylinder(radius=0.008, length=0.016),
        origin=Origin(xyz=(0.0, 0.0, 0.032)),
        material=trim_black,
        name="blade_bearing",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_build_lid_shape(), "lid_shell"),
        material=lid_black,
        name="lid_shell",
    )

    pour_flap = model.part("pour_flap")
    pour_flap.visual(
        mesh_from_cadquery(_build_flap_shape(), "flap_panel"),
        material=lid_black,
        name="flap_panel",
    )

    blade = model.part("blade")
    blade.visual(
        mesh_from_cadquery(_build_blade_shape(), "blade_cross"),
        material=blade_metal,
        name="blade_cross",
    )

    pulse_lever = model.part("pulse_lever")
    pulse_lever.visual(
        mesh_from_cadquery(_build_pulse_lever_shape(), "lever_paddle"),
        material=trim_black,
        name="lever_paddle",
    )

    model.articulation(
        "base_to_jug",
        ArticulationType.FIXED,
        parent=base,
        child=jug,
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT)),
    )
    model.articulation(
        "jug_to_lid",
        ArticulationType.FIXED,
        parent=jug,
        child=lid,
        origin=Origin(xyz=(0.0, 0.0, JUG_HEIGHT + JUG_BODY_OFFSET)),
    )
    model.articulation(
        "lid_to_pour_flap",
        ArticulationType.REVOLUTE,
        parent=lid,
        child=pour_flap,
        origin=Origin(xyz=(0.014, 0.0, 0.023)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=3.0,
            lower=0.0,
            upper=FLAP_OPEN_ANGLE,
        ),
    )
    model.articulation(
        "jug_to_blade",
        ArticulationType.CONTINUOUS,
        parent=jug,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.044)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=3.0, velocity=20.0),
    )
    model.articulation(
        "base_to_pulse_lever",
        ArticulationType.REVOLUTE,
        parent=base,
        child=pulse_lever,
        origin=Origin(xyz=(0.054, 0.099, 0.050)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.5,
            velocity=3.0,
            lower=0.0,
            upper=LEVER_SWING_ANGLE,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
