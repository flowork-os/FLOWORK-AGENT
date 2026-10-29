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
def _make_base_shell() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .box(0.32, 0.24, 0.094)
        .translate((0.0, 0.0, 0.047))
        .edges("|Z")
        .fillet(0.022)
    )
    pedestal = cq.Workplane("XY").box(0.18, 0.15, 0.014).translate((0.0, 0.0, 0.101))
    front_recess = cq.Workplane("XY").box(0.036, 0.126, 0.030).translate((0.146, 0.0, 0.041))
    slider_channel = cq.Workplane("XY").box(0.050, 0.108, 0.016).translate((0.145, 0.0, 0.041))
    return body.union(pedestal).cut(front_recess).cut(slider_channel)
def _make_pitcher_shell() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .rect(0.145, 0.125)
        .workplane(offset=0.120)
        .rect(0.168, 0.148)
        .workplane(offset=0.116)
        .rect(0.190, 0.172)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, 0.0, 0.012))
        .rect(0.125, 0.105)
        .workplane(offset=0.116)
        .rect(0.150, 0.132)
        .workplane(offset=0.116)
        .rect(0.174, 0.156)
        .loft(combine=True)
    )
    return outer.cut(inner)
def _make_lid_shell() -> cq.Workplane:
    panel = (
        cq.Workplane("XY")
        .box(0.194, 0.188, 0.014)
        .translate((0.097, 0.0, 0.010))
        .edges("|Z")
        .fillet(0.008)
    )
    fill_cap = cq.Workplane("XY").cylinder(0.012, 0.034).translate((0.104, 0.0, 0.023))
    front_tab = cq.Workplane("XY").box(0.018, 0.050, 0.010).translate((0.194, 0.0, 0.008))
    return panel.union(fill_cap).union(front_tab)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="jug_blender")

    base_finish = model.material("base_finish", rgba=(0.15, 0.16, 0.18, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.05, 0.05, 0.06, 1.0))
    pitcher_glass = model.material("pitcher_glass", rgba=(0.78, 0.86, 0.92, 0.35))
    blade_metal = model.material("blade_metal", rgba=(0.78, 0.80, 0.82, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_make_base_shell(), "base_shell"),
        material=base_finish,
        name="base_shell",
    )

    pitcher = model.part("pitcher")
    pitcher.visual(
        mesh_from_cadquery(_make_pitcher_shell(), "pitcher_shell"),
        material=pitcher_glass,
        name="pitcher_shell",
    )
    pitcher.visual(
        Box((0.030, 0.044, 0.018)),
        origin=Origin(xyz=(-0.010, 0.090, 0.074)),
        material=trim_finish,
        name="handle_lower_mount",
    )
    pitcher.visual(
        Box((0.032, 0.048, 0.020)),
        origin=Origin(xyz=(-0.008, 0.092, 0.210)),
        material=trim_finish,
        name="handle_upper_mount",
    )
    pitcher.visual(
        Cylinder(radius=0.013, length=0.128),
        origin=Origin(xyz=(-0.008, 0.112, 0.142)),
        material=trim_finish,
        name="handle_grip",
    )
    pitcher.visual(
        Box((0.032, 0.056, 0.006)),
        origin=Origin(xyz=(0.100, 0.0, 0.233)),
        material=pitcher_glass,
        name="spout_lip",
    )
    pitcher.visual(
        Cylinder(radius=0.010, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        material=trim_finish,
        name="drive_socket",
    )
    pitcher.visual(
        Box((0.012, 0.046, 0.012)),
        origin=Origin(xyz=(-0.088, -0.064, 0.233)),
        material=trim_finish,
        name="hinge_pad_0",
    )
    pitcher.visual(
        Cylinder(radius=0.006, length=0.042),
        origin=Origin(xyz=(-0.094, -0.064, 0.233), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_finish,
        name="hinge_barrel_0",
    )
    pitcher.visual(
        Box((0.012, 0.046, 0.012)),
        origin=Origin(xyz=(-0.088, 0.064, 0.233)),
        material=trim_finish,
        name="hinge_pad_1",
    )
    pitcher.visual(
        Cylinder(radius=0.006, length=0.042),
        origin=Origin(xyz=(-0.094, 0.064, 0.233), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_finish,
        name="hinge_barrel_1",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_make_lid_shell(), "lid_shell"),
        material=trim_finish,
        name="lid_panel",
    )
    lid.visual(
        Box((0.138, 0.138, 0.008)),
        origin=Origin(xyz=(0.112, 0.0, -0.001)),
        material=trim_finish,
        name="lid_plug",
    )
    lid.visual(
        Cylinder(radius=0.006, length=0.080),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=trim_finish,
        name="hinge_barrel",
    )

    slider = model.part("slider")
    slider.visual(
        Box((0.044, 0.018, 0.016)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=trim_finish,
        name="slider_rail",
    )
    slider.visual(
        Box((0.026, 0.036, 0.022)),
        origin=Origin(xyz=(0.027, 0.0, 0.003)),
        material=trim_finish,
        name="slider_knob",
    )

    blade = model.part("blade")
    blade.visual(
        Cylinder(radius=0.013, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.009)),
        material=blade_metal,
        name="hub",
    )
    blade.visual(
        Cylinder(radius=0.0035, length=0.016),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=trim_finish,
        name="shaft",
    )
    blade.visual(
        Box((0.072, 0.012, 0.002)),
        origin=Origin(xyz=(0.0, 0.0, 0.012), rpy=(0.0, 0.22, 0.0)),
        material=blade_metal,
        name="lower_blade_a",
    )
    blade.visual(
        Box((0.072, 0.012, 0.002)),
        origin=Origin(xyz=(0.0, 0.0, 0.011), rpy=(0.0, -0.22, math.pi / 2.0)),
        material=blade_metal,
        name="lower_blade_b",
    )
    blade.visual(
        Box((0.050, 0.010, 0.002)),
        origin=Origin(xyz=(0.0, 0.0, 0.017), rpy=(0.0, -0.28, math.pi / 4.0)),
        material=blade_metal,
        name="upper_blade_a",
    )
    blade.visual(
        Box((0.050, 0.010, 0.002)),
        origin=Origin(xyz=(0.0, 0.0, 0.016), rpy=(0.0, 0.28, -math.pi / 4.0)),
        material=blade_metal,
        name="upper_blade_b",
    )

    model.articulation(
        "base_to_pitcher",
        ArticulationType.FIXED,
        parent=base,
        child=pitcher,
        origin=Origin(xyz=(0.0, 0.0, 0.108)),
    )
    model.articulation(
        "lid_hinge",
        ArticulationType.REVOLUTE,
        parent=pitcher,
        child=lid,
        origin=Origin(xyz=(-0.097, 0.0, 0.233)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=3.0,
            velocity=2.0,
            lower=0.0,
            upper=math.radians(95.0),
        ),
    )
    model.articulation(
        "speed_slider",
        ArticulationType.PRISMATIC,
        parent=base,
        child=slider,
        origin=Origin(xyz=(0.146, 0.0, 0.041)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=0.10,
            lower=-0.040,
            upper=0.040,
        ),
    )
    model.articulation(
        "blade_spin",
        ArticulationType.CONTINUOUS,
        parent=pitcher,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.4, velocity=45.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
