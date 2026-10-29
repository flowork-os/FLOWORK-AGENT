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
def _ring(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(height)
def _y_cylinder(radius: float, length: float, center_xyz: tuple[float, float, float]) -> cq.Workplane:
    x, y, z = center_xyz
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((x, y + length / 2.0, z))
    )
def _make_bayonet_collar() -> cq.Workplane:
    ring = _ring(0.048, 0.0395, 0.022)
    shoulder = cq.Workplane("XY", origin=(0.0, 0.0, 0.003)).circle(0.055).circle(0.0405).extrude(0.006)
    return ring.union(shoulder)
def _make_cup_shell() -> cq.Workplane:
    shell_outer = (
        cq.Workplane("XY", origin=(0.0, 0.0, 0.020))
        .circle(0.043)
        .workplane(offset=0.090)
        .circle(0.047)
        .loft(combine=True)
    )
    shell_inner = (
        cq.Workplane("XY", origin=(0.0, 0.0, 0.024))
        .circle(0.0375)
        .workplane(offset=0.086)
        .circle(0.041)
        .loft(combine=True)
    )
    cup = shell_outer.cut(shell_inner)

    lug_radius = 0.0375
    for angle_deg in (0.0, 120.0, 240.0):
        angle_rad = math.radians(angle_deg)
        lug = (
            cq.Workplane("XY")
            .box(0.014, 0.008, 0.004)
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
            .translate((lug_radius * math.cos(angle_rad), lug_radius * math.sin(angle_rad), 0.020))
        )
        cup = cup.union(lug)

    support_z = 0.113
    for y_center in (-0.026, 0.026):
        arm = cq.Workplane("XY").box(0.012, 0.014, 0.010).translate((-0.050, y_center, support_z))
        cup = cup.union(arm)

    cup = cup.union(_y_cylinder(0.0045, 0.016, (-0.050, -0.026, 0.117)))
    cup = cup.union(_y_cylinder(0.0045, 0.016, (-0.050, 0.026, 0.117)))
    return cup
def _make_cup_rim() -> cq.Workplane:
    return _ring(0.050, 0.041, 0.002)
def _make_lid() -> cq.Workplane:
    lid_panel = (
        cq.Workplane("XY")
        .circle(0.047)
        .extrude(0.006)
        .translate((0.050, 0.0, -0.005))
    )
    front_tab = cq.Workplane("XY").box(0.014, 0.020, 0.006).translate((0.094, 0.0, -0.001))
    hinge_barrel = _y_cylinder(0.0045, 0.030, (0.000, 0.000, 0.000))
    return lid_panel.union(front_tab).union(hinge_barrel)
def _make_blade() -> cq.Workplane:
    hub = cq.Workplane("XY", origin=(0.0, 0.0, -0.004)).circle(0.006).extrude(0.010)
    shaft = cq.Workplane("XY", origin=(0.0, 0.0, -0.010)).circle(0.0025).extrude(0.006)

    lower_blade = (
        cq.Workplane("XY")
        .box(0.056, 0.010, 0.0014)
        .translate((0.0, 0.0, 0.001))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 14.0)
    )
    upper_blade = (
        cq.Workplane("XY")
        .box(0.010, 0.046, 0.0014)
        .translate((0.0, 0.0, 0.004))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -16.0)
    )
    return hub.union(shaft).union(lower_blade).union(upper_blade)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="laboratory_homogenizer_blender")

    model.material("housing_dark", rgba=(0.20, 0.22, 0.24, 1.0))
    model.material("housing_trim", rgba=(0.34, 0.36, 0.40, 1.0))
    model.material("metal", rgba=(0.72, 0.74, 0.77, 1.0))
    model.material("cup_clear", rgba=(0.76, 0.87, 0.96, 0.42))
    model.material("lid_clear", rgba=(0.84, 0.90, 0.95, 0.48))
    model.material("seal_dark", rgba=(0.10, 0.11, 0.12, 1.0))
    model.material("blade_metal", rgba=(0.79, 0.81, 0.84, 1.0))

    housing = model.part("housing")
    housing.visual(
        Box((0.205, 0.155, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material="housing_trim",
        name="base_plinth",
    )
    housing.visual(
        Box((0.188, 0.142, 0.082)),
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
        material="housing_dark",
        name="motor_housing",
    )
    housing.visual(
        Box((0.082, 0.018, 0.024)),
        origin=Origin(xyz=(0.034, -0.050, 0.102)),
        material="housing_trim",
        name="support_0",
    )
    housing.visual(
        Box((0.082, 0.018, 0.024)),
        origin=Origin(xyz=(0.034, 0.050, 0.102)),
        material="housing_trim",
        name="support_1",
    )
    housing.visual(
        Box((0.052, 0.092, 0.020)),
        origin=Origin(xyz=(-0.024, 0.0, 0.104)),
        material="housing_trim",
        name="support_bridge",
    )
    housing.visual(
        mesh_from_cadquery(_make_bayonet_collar(), "bayonet_collar"),
        origin=Origin(xyz=(0.048, 0.0, 0.096)),
        material="metal",
        name="bayonet_collar",
    )

    cup = model.part("cup")
    cup.visual(
        mesh_from_cadquery(_make_cup_shell(), "cup_shell"),
        material="cup_clear",
        name="cup_shell",
    )
    cup.visual(
        mesh_from_cadquery(_make_cup_rim(), "cup_rim"),
        origin=Origin(xyz=(0.0, 0.0, 0.110)),
        material="seal_dark",
        name="cup_rim",
    )
    cup.visual(
        Cylinder(radius=0.037, length=0.024),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material="seal_dark",
        name="cup_skirt",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_make_lid(), "lid_shell"),
        material="lid_clear",
        name="lid_shell",
    )

    blade = model.part("blade")
    blade.visual(
        mesh_from_cadquery(_make_blade(), "blade_rotor"),
        material="blade_metal",
        name="blade_rotor",
    )

    model.articulation(
        "housing_to_cup",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=cup,
        origin=Origin(xyz=(0.048, 0.0, 0.096)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=-math.radians(25.0),
            upper=math.radians(25.0),
            effort=2.0,
            velocity=1.5,
        ),
    )
    model.articulation(
        "cup_to_lid",
        ArticulationType.REVOLUTE,
        parent=cup,
        child=lid,
        origin=Origin(xyz=(-0.050, 0.0, 0.117)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            lower=0.0,
            upper=math.radians(112.0),
            effort=1.5,
            velocity=2.0,
        ),
    )
    model.articulation(
        "cup_to_blade",
        ArticulationType.CONTINUOUS,
        parent=cup,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.034)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=35.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
