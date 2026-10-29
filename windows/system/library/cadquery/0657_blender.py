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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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
def _rounded_base(width: float, depth: float, height: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(width, depth, height)
        .edges("|Z")
        .fillet(0.025)
    )
def _hollow_tube(
    length: float,
    outer_radius: float,
    inner_radius: float,
    *,
    feed_window: bool = False,
) -> cq.Workplane:
    outer = cq.Workplane("YZ").circle(outer_radius).extrude(length, both=True)
    inner = cq.Workplane("YZ").circle(inner_radius).extrude(length + 0.030, both=True)
    tube = outer.cut(inner)
    if feed_window:
        port = (
            cq.Workplane("XY")
            .box(0.150, 0.120, outer_radius * 1.7)
            .translate((0.0, 0.0, outer_radius * 0.80))
        )
        tube = tube.cut(port)
    return tube
def _hopper_funnel(
    bottom_size: tuple[float, float],
    top_size: tuple[float, float],
    height: float,
    wall: float,
) -> cq.Workplane:
    bottom_x, bottom_y = bottom_size
    top_x, top_y = top_size
    outer = (
        cq.Workplane("XY")
        .rect(bottom_x, bottom_y)
        .workplane(offset=height)
        .rect(top_x, top_y)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("XY")
        .workplane(offset=-0.006)
        .rect(bottom_x - 2.0 * wall, bottom_y - 2.0 * wall)
        .workplane(offset=height + 0.012)
        .rect(top_x - 2.0 * wall, top_y - 2.0 * wall)
        .loft(combine=True)
    )
    return outer.cut(inner)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cold_press_slow_juicer")

    white_plastic = model.material("warm_white_plastic", rgba=(0.92, 0.91, 0.86, 1.0))
    dark_plastic = model.material("matte_black_plastic", rgba=(0.025, 0.025, 0.028, 1.0))
    smoked_clear = model.material("smoked_clear_plastic", rgba=(0.50, 0.68, 0.74, 0.38))
    auger_black = model.material("satin_black_auger", rgba=(0.015, 0.018, 0.020, 1.0))
    brushed_metal = model.material("brushed_steel", rgba=(0.58, 0.58, 0.55, 1.0))
    amber = model.material("amber_juice", rgba=(0.95, 0.58, 0.12, 0.70))

    body = model.part("body")

    body.visual(
        mesh_from_cadquery(_rounded_base(0.54, 0.32, 0.18), "rounded_motor_base"),
        origin=Origin(xyz=(0.0, 0.0, 0.09)),
        material=white_plastic,
        name="motor_base",
    )
    body.visual(
        Box((0.42, 0.020, 0.018)),
        origin=Origin(xyz=(0.0, -0.165, 0.160)),
        material=dark_plastic,
        name="front_trim",
    )
    body.visual(
        Box((0.125, 0.018, 0.080)),
        origin=Origin(xyz=(-0.185, -0.165, 0.095)),
        material=dark_plastic,
        name="control_panel",
    )

    chamber_length = 0.46
    chamber_outer = 0.085
    chamber_inner = 0.074
    chamber_center = (0.0, -0.020, 0.255)
    body.visual(
        mesh_from_cadquery(
            _hollow_tube(chamber_length, chamber_outer, chamber_inner, feed_window=True),
            "clear_auger_chamber",
            tolerance=0.0008,
        ),
        origin=Origin(xyz=chamber_center),
        material=smoked_clear,
        name="chamber_shell",
    )
    body.visual(
        mesh_from_cadquery(_hollow_tube(0.030, 0.092, chamber_inner), "front_chamber_band"),
        origin=Origin(xyz=(-0.245, chamber_center[1], chamber_center[2])),
        material=dark_plastic,
        name="chamber_band_0",
    )
    body.visual(
        mesh_from_cadquery(_hollow_tube(0.030, 0.092, chamber_inner), "rear_chamber_band"),
        origin=Origin(xyz=(0.245, chamber_center[1], chamber_center[2])),
        material=dark_plastic,
        name="chamber_band_1",
    )
    for i, x in enumerate((-0.232, 0.232)):
        body.visual(
            Cylinder(radius=0.028, length=0.020),
            origin=Origin(xyz=(x, chamber_center[1], chamber_center[2]), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=brushed_metal,
            name=f"bearing_socket_{i}",
        )
        body.visual(
            Box((0.018, 0.014, 0.060)),
            origin=Origin(xyz=(x, chamber_center[1], chamber_center[2] + 0.052)),
            material=brushed_metal,
            name=f"bearing_web_{i}",
        )

    body.visual(
        Box((0.070, 0.100, 0.032)),
        origin=Origin(xyz=(-0.125, -0.112, 0.205), rpy=(0.0, 0.0, -0.15)),
        material=dark_plastic,
        name="juice_spout",
    )
    body.visual(
        Box((0.058, 0.082, 0.010)),
        origin=Origin(xyz=(-0.125, -0.162, 0.180), rpy=(0.0, 0.0, -0.15)),
        material=amber,
        name="spout_opening",
    )

    body.visual(
        mesh_from_cadquery(
            _hopper_funnel((0.120, 0.085), (0.290, 0.225), 0.200, 0.010),
            "wide_hopper_funnel",
            tolerance=0.0008,
        ),
        origin=Origin(xyz=(0.0, -0.020, 0.335)),
        material=smoked_clear,
        name="hopper_shell",
    )
    body.visual(
        Box((0.150, 0.012, 0.080)),
        origin=Origin(xyz=(0.0, -0.072, 0.373)),
        material=smoked_clear,
        name="feed_neck_front",
    )
    body.visual(
        Box((0.150, 0.012, 0.080)),
        origin=Origin(xyz=(0.0, 0.032, 0.373)),
        material=smoked_clear,
        name="feed_neck_back",
    )
    body.visual(
        Box((0.012, 0.104, 0.080)),
        origin=Origin(xyz=(-0.075, -0.020, 0.373)),
        material=smoked_clear,
        name="feed_neck_side_0",
    )
    body.visual(
        Box((0.012, 0.104, 0.080)),
        origin=Origin(xyz=(0.075, -0.020, 0.373)),
        material=smoked_clear,
        name="feed_neck_side_1",
    )
    body.visual(
        Box((0.305, 0.020, 0.020)),
        origin=Origin(xyz=(0.0, 0.100, 0.532)),
        material=dark_plastic,
        name="back_hopper_rim",
    )

    hinge_y = 0.100
    hinge_z = 0.556
    for i, x in enumerate((-0.108, 0.108)):
        body.visual(
            Box((0.060, 0.020, 0.036)),
            origin=Origin(xyz=(x, hinge_y + 0.006, 0.529)),
            material=dark_plastic,
            name=f"hinge_leaf_{i}",
        )
        body.visual(
            Cylinder(radius=0.014, length=0.055),
            origin=Origin(xyz=(x, hinge_y, hinge_z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_plastic,
            name=f"hinge_barrel_{i}",
        )

    auger = model.part("auger")
    auger.visual(
        Cylinder(radius=0.018, length=0.480),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=brushed_metal,
        name="auger_shaft",
    )
    flight_radius_center = 0.034
    for i in range(13):
        x = -0.180 + i * 0.030
        angle = i * 0.82
        auger.visual(
            Box((0.032, 0.010, 0.054)),
            origin=Origin(
                xyz=(
                    x,
                    -flight_radius_center * math.sin(angle),
                    flight_radius_center * math.cos(angle),
                ),
                rpy=(angle, 0.0, 0.0),
            ),
            material=auger_black,
            name=f"auger_flight_{i}",
        )
    model.articulation(
        "body_to_auger",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=auger,
        origin=Origin(xyz=chamber_center),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=0.8),
        motion_properties=MotionProperties(damping=0.15, friction=0.04),
    )

    lid = model.part("hopper_lid")
    lid.visual(
        Box((0.310, 0.245, 0.014)),
        origin=Origin(xyz=(0.0, -0.1425, -0.011)),
        material=smoked_clear,
        name="lid_panel",
    )
    lid.visual(
        Cylinder(radius=0.014, length=0.120),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_plastic,
        name="lid_barrel",
    )
    lid.visual(
        Box((0.120, 0.030, 0.012)),
        origin=Origin(xyz=(0.0, -0.010, -0.008)),
        material=dark_plastic,
        name="lid_hinge_leaf",
    )
    lid.visual(
        Box((0.130, 0.026, 0.020)),
        origin=Origin(xyz=(0.0, -0.224, 0.003)),
        material=dark_plastic,
        name="front_lip",
    )
    model.articulation(
        "body_to_hopper_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(0.0, hinge_y, hinge_z)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=1.5, lower=0.0, upper=1.35),
    )

    control_knob = model.part("control_knob")
    control_knob.visual(
        Cylinder(radius=0.030, length=0.024),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=dark_plastic,
        name="knob_cap",
    )
    control_knob.visual(
        Cylinder(radius=0.010, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, -0.004)),
        material=dark_plastic,
        name="knob_stem",
    )
    control_knob.visual(
        Box((0.007, 0.040, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.026)),
        material=white_plastic,
        name="pointer_mark",
    )
    model.articulation(
        "body_to_control_knob",
        ArticulationType.REVOLUTE,
        parent=body,
        child=control_knob,
        origin=Origin(xyz=(-0.185, -0.174, 0.095), rpy=(math.pi / 2.0, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.4, velocity=2.0, lower=-0.75, upper=0.75),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
