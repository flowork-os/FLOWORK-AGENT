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

# ===== wheels_tires (3 syms) =====
cos = math.cos

sin = math.sin

pi = math.pi

# ===== model =====
import cadquery as cq
from math import cos, pi, radians, sin, sqrt
def _tube_shell(length: float, radius: float, wall: float) -> cq.Workplane:
    """Open annular tube, authored along CadQuery Z and centered on its length."""
    return (
        cq.Workplane("XY")
        .circle(radius)
        .circle(radius - wall)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
def _annular_sleeve(length: float, outer_radius: float, inner_radius: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="short_f5_newtonian_equatorial")

    matte_black = model.material("matte_black", rgba=(0.005, 0.006, 0.007, 1.0))
    satin_black = model.material("satin_black", rgba=(0.02, 0.022, 0.024, 1.0))
    white_enamel = model.material("white_enamel", rgba=(0.86, 0.88, 0.84, 1.0))
    dark_metal = model.material("dark_anodized_metal", rgba=(0.12, 0.125, 0.13, 1.0))
    steel = model.material("brushed_steel", rgba=(0.55, 0.56, 0.54, 1.0))
    glass = model.material("mirror_glass", rgba=(0.70, 0.78, 0.82, 1.0))
    red = model.material("red_index_marks", rgba=(0.85, 0.06, 0.04, 1.0))

    tube_length = 0.75
    tube_radius = 0.095
    wall = 0.006
    rail_length = 0.46
    rail_height = 0.030
    rail_bottom_z = -0.122

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.040, length=0.72),
        origin=Origin(xyz=(0.0, 0.0, 0.36)),
        material=dark_metal,
        name="pier",
    )
    tripod.visual(
        Cylinder(radius=0.070, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.730)),
        material=dark_metal,
        name="pier_cap",
    )
    # Three broad tripod legs run from the pier foot to rubber pads.
    for idx, yaw in enumerate((0.0, 2.0 * pi / 3.0, 4.0 * pi / 3.0)):
        r = 0.34
        x = r * cos(yaw)
        y = r * sin(yaw)
        tripod.visual(
            Box((0.58, 0.045, 0.040)),
            origin=Origin(
                xyz=(x / 2.0, y / 2.0, 0.080),
                rpy=(0.0, radians(10.0), yaw),
            ),
            material=dark_metal,
            name=f"tripod_leg_{idx}",
        )
        tripod.visual(
            Box((0.12, 0.075, 0.022)),
            origin=Origin(xyz=(x, y, 0.024), rpy=(0.0, 0.0, yaw)),
            material=satin_black,
            name=f"rubber_foot_{idx}",
        )

    # A tilted polar wedge gives the right-ascension housing a real sloped seat.
    latitude_tilt = radians(55.0)  # polar axis is 35 degrees above the horizon
    ra_joint_world = (0.0, 0.0, 0.82)
    polar_axis = (0.0, -sin(latitude_tilt), cos(latitude_tilt))
    wedge_half_thick = 0.018
    wedge_center = (
        ra_joint_world[0] - wedge_half_thick * polar_axis[0],
        ra_joint_world[1] - wedge_half_thick * polar_axis[1],
        ra_joint_world[2] - wedge_half_thick * polar_axis[2],
    )
    tripod.visual(
        Box((0.24, 0.15, 0.036)),
        origin=Origin(xyz=wedge_center, rpy=(latitude_tilt, 0.0, 0.0)),
        material=dark_metal,
        name="polar_wedge",
    )

    ra_axis = model.part("ra_axis")
    ra_axis.visual(
        Cylinder(radius=0.076, length=0.240),
        origin=Origin(xyz=(0.0, 0.0, 0.120)),
        material=satin_black,
        name="polar_housing",
    )
    ra_axis.visual(
        Cylinder(radius=0.052, length=0.260),
        origin=Origin(xyz=(0.0, 0.0, 0.150)),
        material=dark_metal,
        name="ra_shaft",
    )
    ra_axis.visual(
        Box((0.082, 0.090, 0.105)),
        origin=Origin(xyz=(0.105, 0.0, 0.120)),
        material=dark_metal,
        name="ra_motor_box",
    )
    ra_axis.visual(
        Cylinder(radius=0.028, length=0.020),
        origin=Origin(xyz=(0.105, -0.054, 0.120), rpy=(pi / 2.0, 0.0, 0.0)),
        material=satin_black,
        name="ra_motor_cap",
    )
    ra_axis.visual(
        Box((0.105, 0.004, 0.018)),
        origin=Origin(xyz=(0.105, -0.047, 0.120)),
        material=red,
        name="ra_index_mark",
    )

    saddle = model.part("saddle")
    saddle.visual(
        Cylinder(radius=0.055, length=0.260),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=satin_black,
        name="dec_hub",
    )
    saddle.visual(
        Box((0.250, 0.500, 0.035)),
        origin=Origin(xyz=(0.0, 0.0, 0.0475)),
        material=dark_metal,
        name="saddle_plate",
    )
    saddle.visual(
        Box((0.024, 0.455, 0.040)),
        origin=Origin(xyz=(0.070, 0.0, 0.085)),
        material=satin_black,
        name="dovetail_jaw_0",
    )
    saddle.visual(
        Box((0.024, 0.455, 0.040)),
        origin=Origin(xyz=(-0.070, 0.0, 0.085)),
        material=satin_black,
        name="dovetail_jaw_1",
    )
    saddle.visual(
        Box((0.035, 0.075, 0.030)),
        origin=Origin(xyz=(0.092, 0.190, 0.093)),
        material=steel,
        name="clamp_block",
    )
    saddle.visual(
        Cylinder(radius=0.018, length=0.028),
        origin=Origin(xyz=(0.113, 0.190, 0.093), rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="clamp_knob",
    )
    saddle.visual(
        Cylinder(radius=0.012, length=0.350),
        origin=Origin(xyz=(-0.300, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="counterweight_bar",
    )
    saddle.visual(
        Cylinder(radius=0.060, length=0.070),
        origin=Origin(xyz=(-0.400, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=dark_metal,
        name="counterweight",
    )
    saddle.visual(
        Box((0.078, 0.070, 0.060)),
        origin=Origin(xyz=(0.160, -0.165, 0.094)),
        material=dark_metal,
        name="dec_motor_box",
    )

    optical_tube = model.part("optical_tube")
    tube_mesh = mesh_from_cadquery(
        _tube_shell(tube_length, tube_radius, wall),
        "open_newtonian_tube",
        tolerance=0.0008,
        angular_tolerance=0.08,
    )
    optical_tube.visual(
        tube_mesh,
        origin=Origin(rpy=(-pi / 2.0, 0.0, 0.0)),
        material=white_enamel,
        name="tube_shell",
    )
    optical_tube.visual(
        Cylinder(radius=0.099, length=0.030),
        origin=Origin(xyz=(0.0, tube_length / 2.0 - 0.015, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=satin_black,
        name="front_rim",
    )
    optical_tube.visual(
        Cylinder(radius=0.098, length=0.028),
        origin=Origin(xyz=(0.0, -tube_length / 2.0 + 0.014, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=satin_black,
        name="mirror_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.073, length=0.006),
        origin=Origin(xyz=(0.0, -tube_length / 2.0 + 0.029, 0.0), rpy=(-pi / 2.0, 0.0, 0.0)),
        material=glass,
        name="primary_mirror",
    )
    # Spider vanes and secondary holder bridge the front aperture.
    optical_tube.visual(
        Box((0.180, 0.006, 0.004)),
        origin=Origin(xyz=(0.0, tube_length / 2.0 - 0.035, 0.0)),
        material=satin_black,
        name="spider_vane_x",
    )
    optical_tube.visual(
        Box((0.006, 0.006, 0.180)),
        origin=Origin(xyz=(0.0, tube_length / 2.0 - 0.035, 0.0)),
        material=satin_black,
        name="spider_vane_z",
    )
    optical_tube.visual(
        Cylinder(radius=0.022, length=0.014),
        origin=Origin(xyz=(0.0, tube_length / 2.0 - 0.035, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=dark_metal,
        name="secondary_holder",
    )
    optical_tube.visual(
        Box((0.060, rail_length, rail_height)),
        origin=Origin(xyz=(0.0, 0.0, rail_bottom_z + rail_height / 2.0)),
        material=dark_metal,
        name="dovetail_rail",
    )

    focuser_body = model.part("focuser_body")
    focuser_body.visual(
        Box((0.120, 0.120, 0.016)),
        origin=Origin(xyz=(0.0, 0.0, 0.018)),
        material=satin_black,
        name="curved_base_plate",
    )
    focuser_body.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=satin_black,
        name="mounting_foot",
    )
    focuser_body.visual(
        Box((0.016, 0.102, 0.095)),
        origin=Origin(xyz=(0.048, 0.0, 0.062)),
        material=dark_metal,
        name="focuser_cheek_0",
    )
    focuser_body.visual(
        Box((0.016, 0.102, 0.095)),
        origin=Origin(xyz=(-0.048, 0.0, 0.062)),
        material=dark_metal,
        name="focuser_cheek_1",
    )
    focuser_body.visual(
        Box((0.090, 0.016, 0.082)),
        origin=Origin(xyz=(0.0, 0.051, 0.057)),
        material=dark_metal,
        name="focuser_bridge",
    )
    collar_mesh = mesh_from_cadquery(
        _annular_sleeve(0.105, outer_radius=0.041, inner_radius=0.030),
        "focuser_collar",
        tolerance=0.0005,
        angular_tolerance=0.08,
    )
    focuser_body.visual(
        collar_mesh,
        origin=Origin(xyz=(0.0, 0.0, 0.076)),
        material=satin_black,
        name="collar",
    )
    focuser_body.visual(
        Box((0.085, 0.006, 0.012)),
        origin=Origin(xyz=(0.0, -0.049, 0.092)),
        material=steel,
        name="rack_window",
    )

    drawtube = model.part("drawtube")
    drawtube.visual(
        Cylinder(radius=0.025, length=0.160),
        origin=Origin(xyz=(0.0, 0.0, 0.060)),
        material=satin_black,
        name="drawtube_barrel",
    )
    drawtube.visual(
        Cylinder(radius=0.032, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 0.150)),
        material=dark_metal,
        name="eyepiece_clamp",
    )
    drawtube.visual(
        Box((0.010, 0.006, 0.090)),
        origin=Origin(xyz=(0.0, -0.027, 0.053)),
        material=steel,
        name="rack_strip",
    )
    for idx in range(7):
        drawtube.visual(
            Box((0.018, 0.004, 0.003)),
            origin=Origin(xyz=(0.0, -0.031, 0.012 + idx * 0.010)),
            material=steel,
            name=f"rack_tooth_{idx}",
        )

    focus_knob = model.part("focus_knob")
    focus_knob.visual(
        Cylinder(radius=0.005, length=0.128),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=steel,
        name="pinion_shaft",
    )
    focus_knob.visual(
        Cylinder(radius=0.025, length=0.022),
        origin=Origin(xyz=(0.073, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=satin_black,
        name="knob_cap_0",
    )
    focus_knob.visual(
        Cylinder(radius=0.025, length=0.022),
        origin=Origin(xyz=(-0.073, 0.0, 0.0), rpy=(0.0, pi / 2.0, 0.0)),
        material=satin_black,
        name="knob_cap_1",
    )

    model.articulation(
        "ra_drive",
        ArticulationType.CONTINUOUS,
        parent=tripod,
        child=ra_axis,
        origin=Origin(xyz=ra_joint_world, rpy=(latitude_tilt, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=45.0, velocity=0.020),
    )
    model.articulation(
        "declination_axis",
        ArticulationType.REVOLUTE,
        parent=ra_axis,
        child=saddle,
        origin=Origin(xyz=(0.0, 0.0, 0.335)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=32.0, velocity=0.25, lower=-pi / 2.0, upper=pi / 2.0),
    )
    model.articulation(
        "tube_clamp",
        ArticulationType.FIXED,
        parent=saddle,
        child=optical_tube,
        origin=Origin(xyz=(0.0, 0.0, 0.187)),
    )
    model.articulation(
        "focuser_mount",
        ArticulationType.FIXED,
        parent=optical_tube,
        child=focuser_body,
        origin=Origin(xyz=(0.0, 0.190, tube_radius - 0.0005)),
    )
    model.articulation(
        "drawtube_slide",
        ArticulationType.PRISMATIC,
        parent=focuser_body,
        child=drawtube,
        origin=Origin(xyz=(0.0, 0.0, 0.085)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=12.0, velocity=0.030, lower=0.0, upper=0.045),
    )
    model.articulation(
        "focus_pinion",
        ArticulationType.CONTINUOUS,
        parent=focuser_body,
        child=focus_knob,
        origin=Origin(xyz=(0.0, -0.055, 0.105)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.8, velocity=5.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
