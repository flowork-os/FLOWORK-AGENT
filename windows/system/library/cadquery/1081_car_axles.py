# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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

class Mimic:
    def __init__(self, joint, multiplier=1.0, offset=0.0):
        self.joint = str(joint)
        self.multiplier = float(multiplier)
        self.offset = float(offset)

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
SHAFT_AXIS_RPY = (0.0, math.pi / 2.0, 0.0)
INPUT_Z = 0.20
OUTPUT_Z = -0.20
def _annular_boss(z_center: float, outer_radius: float, inner_radius: float, thickness: float):
    """A bearing-boss ring extruded along the vehicle/wheel shaft axis (X)."""
    return (
        cq.Workplane("YZ")
        .center(0.0, z_center)
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(thickness)
        .translate((-thickness / 2.0, 0.0, 0.0))
    )
def _round_bolt(x_face: float, y: float, z: float, radius: float = 0.013):
    """Short round bolt head on the outboard face of the cast housing."""
    return (
        cq.Workplane("YZ")
        .center(y, z)
        .circle(radius)
        .extrude(0.024)
        .translate((x_face, 0.0, 0.0))
    )
def _build_housing_shape():
    upper = _annular_boss(INPUT_Z, outer_radius=0.155, inner_radius=0.060, thickness=0.230)
    lower = _annular_boss(OUTPUT_Z, outer_radius=0.205, inner_radius=0.108, thickness=0.250)

    # Cast side webs join the two bearing bosses while keeping the center visibly
    # recessed/open like a serviceable portal reduction case.
    rail_a = cq.Workplane("XY").box(0.190, 0.058, 0.430).translate((0.0, 0.142, 0.0))
    rail_b = cq.Workplane("XY").box(0.190, 0.058, 0.430).translate((0.0, -0.142, 0.0))
    center_rib = cq.Workplane("XY").box(0.105, 0.055, 0.330).translate((-0.045, 0.0, 0.0))

    shape = upper.union(lower).union(rail_a).union(rail_b).union(center_rib)

    # Bolt circles on the removable outboard cover face.
    for count, circle_radius, z_center, head_radius in (
        (6, 0.122, INPUT_Z, 0.012),
        (8, 0.162, OUTPUT_Z, 0.014),
    ):
        for i in range(count):
            angle = 2.0 * math.pi * i / count
            y = circle_radius * math.cos(angle)
            z = z_center + circle_radius * math.sin(angle)
            shape = shape.union(_round_bolt(0.106, y, z, head_radius))

    # A small drain boss at the bottom gives the vertical casting an oil-filled
    # gearbox character and connects directly into the lower boss.
    drain = cq.Workplane("XY").box(0.090, 0.070, 0.045).translate((0.0, 0.0, OUTPUT_Z - 0.205))
    return shape.union(drain)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portal_axle_hub_reduction")

    cast_iron = model.material("dark_cast_iron", rgba=(0.12, 0.13, 0.13, 1.0))
    machined = model.material("machined_steel", rgba=(0.62, 0.64, 0.62, 1.0))
    dark_steel = model.material("blackened_fasteners", rgba=(0.025, 0.025, 0.023, 1.0))
    rubber_seal = model.material("black_rubber_seal", rgba=(0.005, 0.005, 0.004, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_build_housing_shape(), "portal_gear_housing", tolerance=0.0008),
        material=cast_iron,
        name="cast_portal_case",
    )
    # Static seals at the two shaft openings make the rotating members read as
    # bearing-supported rather than floating from the case.
    housing.visual(
        mesh_from_cadquery(
            _annular_boss(INPUT_Z, outer_radius=0.071, inner_radius=0.043, thickness=0.018).translate(
                (-0.124, 0.0, 0.0)
            ),
            "input_annular_seal",
            tolerance=0.0008,
        ),
        origin=Origin(),
        material=rubber_seal,
        name="input_shaft_seal",
    )
    housing.visual(
        mesh_from_cadquery(
            _annular_boss(OUTPUT_Z, outer_radius=0.120, inner_radius=0.062, thickness=0.020).translate(
                (0.128, 0.0, 0.0)
            ),
            "hub_annular_seal",
            tolerance=0.0008,
        ),
        origin=Origin(),
        material=rubber_seal,
        name="hub_oil_seal",
    )

    input_shaft = model.part("input_shaft")
    input_shaft.visual(
        Cylinder(radius=0.036, length=0.340),
        origin=Origin(xyz=(-0.300, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=machined,
        name="axle_stub",
    )
    input_shaft.visual(
        Cylinder(radius=0.078, length=0.042),
        origin=Origin(xyz=(-0.154, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=machined,
        name="input_flange",
    )
    input_shaft.visual(
        Cylinder(radius=0.044, length=0.090),
        origin=Origin(xyz=(-0.455, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=dark_steel,
        name="splined_end",
    )
    for i in range(8):
        angle = 2.0 * math.pi * i / 8
        y = 0.042 * math.cos(angle)
        z = 0.042 * math.sin(angle)
        input_shaft.visual(
            Box((0.085, 0.006, 0.006)),
            origin=Origin(xyz=(-0.455, y, z), rpy=(angle, 0.0, 0.0)),
            material=machined,
            name=f"spline_{i}",
        )

    wheel_hub = model.part("wheel_hub")
    wheel_hub.visual(
        Cylinder(radius=0.054, length=0.280),
        origin=Origin(xyz=(0.270, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=machined,
        name="output_spindle",
    )
    wheel_hub.visual(
        Cylinder(radius=0.103, length=0.095),
        origin=Origin(xyz=(0.185, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=machined,
        name="inner_hub_barrel",
    )
    wheel_hub.visual(
        Cylinder(radius=0.180, length=0.052),
        origin=Origin(xyz=(0.335, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=machined,
        name="wheel_flange",
    )
    wheel_hub.visual(
        Cylinder(radius=0.075, length=0.070),
        origin=Origin(xyz=(0.398, 0.0, 0.0), rpy=SHAFT_AXIS_RPY),
        material=dark_steel,
        name="pilot_register",
    )
    for i in range(5):
        angle = 2.0 * math.pi * i / 5
        y = 0.136 * math.cos(angle)
        z = 0.136 * math.sin(angle)
        wheel_hub.visual(
            Cylinder(radius=0.012, length=0.095),
            origin=Origin(xyz=(0.405, y, z), rpy=SHAFT_AXIS_RPY),
            material=dark_steel,
            name=f"wheel_stud_{i}",
        )
        wheel_hub.visual(
            Cylinder(radius=0.019, length=0.026),
            origin=Origin(xyz=(0.462, y, z), rpy=SHAFT_AXIS_RPY),
            material=machined,
            name=f"lug_nut_{i}",
        )

    input_spin = model.articulation(
        "input_spin",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=input_shaft,
        origin=Origin(xyz=(0.0, 0.0, INPUT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=220.0, velocity=45.0),
    )
    model.articulation(
        "hub_spin",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=wheel_hub,
        origin=Origin(xyz=(0.0, 0.0, OUTPUT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=600.0, velocity=22.0),
        mimic=Mimic(joint=input_spin.name, multiplier=-0.5),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
