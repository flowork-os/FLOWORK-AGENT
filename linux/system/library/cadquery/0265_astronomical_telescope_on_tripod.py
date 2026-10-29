# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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

# ===== model =====
import math
import cadquery as cq
def _cylinder_between(start: tuple[float, float, float], end: tuple[float, float, float]) -> tuple[Cylinder, Origin]:
    """Return a cylinder and transform whose local +Z runs from start to end."""
    sx, sy, sz = start
    ex, ey, ez = end
    vx, vy, vz = ex - sx, ey - sy, ez - sz
    length = math.sqrt(vx * vx + vy * vy + vz * vz)
    yaw = math.atan2(vy, vx)
    pitch = math.atan2(math.sqrt(vx * vx + vy * vy), vz)
    center = ((sx + ex) * 0.5, (sy + ey) * 0.5, (sz + ez) * 0.5)
    return Cylinder(radius=0.018, length=length), Origin(xyz=center, rpy=(0.0, pitch, yaw))
def _annular_tube(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """CadQuery tube along local +Z with open bore and annular end faces."""
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(length)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="solar_halpha_refractor_altaz")

    black = model.material("satin_black", rgba=(0.015, 0.014, 0.013, 1.0))
    rubber = model.material("soft_rubber", rgba=(0.005, 0.005, 0.004, 1.0))
    red = model.material("halpha_red_anodized", rgba=(0.78, 0.08, 0.025, 1.0))
    gold = model.material("etalon_gold", rgba=(0.96, 0.62, 0.16, 1.0))
    silver = model.material("brushed_silver", rgba=(0.72, 0.72, 0.68, 1.0))
    glass = model.material("deep_solar_glass", rgba=(0.05, 0.13, 0.18, 0.72))

    tripod = model.part("tripod_head")
    tripod.visual(Cylinder(radius=0.040, length=0.78), origin=Origin(xyz=(0.0, 0.0, 0.56)), material=black, name="center_column")
    tripod.visual(Cylinder(radius=0.125, length=0.080), origin=Origin(xyz=(0.0, 0.0, 0.960)), material=black, name="azimuth_base")
    tripod.visual(Cylinder(radius=0.090, length=0.050), origin=Origin(xyz=(0.0, 0.0, 0.235)), material=black, name="leg_crown")
    tripod.visual(Sphere(radius=0.055), origin=Origin(xyz=(0.0, 0.0, 0.270)), material=black, name="crown_boss")
    for i, angle in enumerate((math.pi / 2.0, math.pi / 2.0 + 2.0 * math.pi / 3.0, math.pi / 2.0 + 4.0 * math.pi / 3.0)):
        hip = (0.070 * math.cos(angle), 0.070 * math.sin(angle), 0.250)
        foot = (0.620 * math.cos(angle), 0.620 * math.sin(angle), 0.040)
        leg_geom, leg_origin = _cylinder_between(hip, foot)
        tripod.visual(leg_geom, origin=leg_origin, material=black, name=f"tripod_leg_{i}")
        tripod.visual(
            Box((0.145, 0.050, 0.022)),
            origin=Origin(xyz=foot, rpy=(0.0, 0.0, angle)),
            material=black,
            name=f"rubber_foot_{i}",
        )

    arm = model.part("azimuth_arm")
    arm.visual(Cylinder(radius=0.108, length=0.052), origin=Origin(xyz=(0.0, 0.0, 0.026)), material=black, name="azimuth_cap")
    arm.visual(Cylinder(radius=0.045, length=0.280), origin=Origin(xyz=(0.0, 0.0, 0.166)), material=black, name="upright_post")
    arm.visual(Box((0.190, 0.240, 0.054)), origin=Origin(xyz=(0.070, 0.0, 0.295)), material=black, name="offset_bridge")
    arm.visual(Box((0.070, 0.030, 0.240)), origin=Origin(xyz=(0.140, 0.105, 0.295)), material=black, name="fork_cheek_0")
    arm.visual(Box((0.070, 0.030, 0.240)), origin=Origin(xyz=(0.140, -0.105, 0.295)), material=black, name="fork_cheek_1")
    arm.visual(Cylinder(radius=0.030, length=0.012), origin=Origin(xyz=(0.140, 0.126, 0.360), rpy=(math.pi / 2.0, 0.0, 0.0)), material=silver, name="altitude_bushing_0")
    arm.visual(Cylinder(radius=0.030, length=0.012), origin=Origin(xyz=(0.140, -0.126, 0.360), rpy=(math.pi / 2.0, 0.0, 0.0)), material=silver, name="altitude_bushing_1")

    telescope = model.part("telescope")
    telescope.visual(Cylinder(radius=0.045, length=0.530), origin=Origin(xyz=(-0.065, 0.0, 0.130), rpy=(0.0, math.pi / 2.0, 0.0)), material=red, name="main_tube")
    telescope.visual(Cylinder(radius=0.054, length=0.035), origin=Origin(xyz=(-0.345, 0.0, 0.130), rpy=(0.0, math.pi / 2.0, 0.0)), material=black, name="front_cell")
    telescope.visual(Cylinder(radius=0.044, length=0.006), origin=Origin(xyz=(-0.365, 0.0, 0.130), rpy=(0.0, math.pi / 2.0, 0.0)), material=glass, name="front_lens")
    telescope.visual(
        mesh_from_cadquery(_annular_tube(0.036, 0.025, 0.120), "etalon_filter_tube", tolerance=0.0008),
        origin=Origin(xyz=(0.200, 0.0, 0.130), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=gold,
        name="etalon_filter",
    )
    telescope.visual(Cylinder(radius=0.041, length=0.018), origin=Origin(xyz=(0.194, 0.0, 0.130), rpy=(0.0, math.pi / 2.0, 0.0)), material=black, name="rear_retaining_ring")
    telescope.visual(Box((0.260, 0.014, 0.010)), origin=Origin(xyz=(0.330, 0.0, 0.107)), material=black, name="focuser_lower_rail")
    telescope.visual(Box((0.350, 0.040, 0.030)), origin=Origin(xyz=(-0.015, 0.0, 0.075)), material=black, name="dovetail_rail")
    telescope.visual(Box((0.090, 0.070, 0.070)), origin=Origin(xyz=(0.0, 0.0, 0.040)), material=black, name="saddle_block")
    telescope.visual(Cylinder(radius=0.026, length=0.180), origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)), material=silver, name="altitude_shaft")

    draw_tube = model.part("draw_tube")
    draw_tube.visual(Cylinder(radius=0.018, length=0.260), origin=Origin(xyz=(0.030, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)), material=silver, name="sliding_tube")
    draw_tube.visual(Cylinder(radius=0.023, length=0.016), origin=Origin(xyz=(0.158, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)), material=black, name="eyepiece_stop")

    eyepiece = model.part("eyepiece_tube")
    eyepiece.visual(
        mesh_from_cadquery(_annular_tube(0.024, 0.014, 0.105), "eyepiece_tube", tolerance=0.0008),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="eyepiece_barrel",
    )
    eyepiece.visual(
        mesh_from_cadquery(_annular_tube(0.031, 0.018, 0.026), "eyecup_ring", tolerance=0.0008),
        origin=Origin(xyz=(0.102, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="rubber_eyecup",
    )

    model.articulation(
        "azimuth_bearing",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=arm,
        origin=Origin(xyz=(0.0, 0.0, 1.000)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=1.2),
    )
    model.articulation(
        "altitude_axis",
        ArticulationType.REVOLUTE,
        parent=arm,
        child=telescope,
        origin=Origin(xyz=(0.140, 0.0, 0.360)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.8, lower=-0.35, upper=1.15),
    )
    model.articulation(
        "focuser_draw",
        ArticulationType.PRISMATIC,
        parent=telescope,
        child=draw_tube,
        origin=Origin(xyz=(0.320, 0.0, 0.130)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=15.0, velocity=0.05, lower=0.0, upper=0.060),
    )
    model.articulation(
        "draw_to_eyepiece",
        ArticulationType.FIXED,
        parent=draw_tube,
        child=eyepiece,
        origin=Origin(xyz=(0.166, 0.0, 0.0)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
