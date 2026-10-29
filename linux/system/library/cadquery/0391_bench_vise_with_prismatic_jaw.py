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
import cadquery as cq
SWIVEL_GAP = 0.0
JAW_TRAVEL = 0.075
SWIVEL_LIMIT = 1.10
def _swivel_base_shape() -> cq.Workplane:
    base = cq.Workplane("XY").box(0.245, 0.155, 0.014).translate((0.0, 0.0, 0.007))

    top_ring = cq.Workplane("XY").circle(0.078).extrude(0.009).translate((0.0, 0.0, 0.013))
    center_recess = cq.Workplane("XY").circle(0.048).extrude(0.004).translate((0.0, 0.0, 0.018))

    slot_left = (
        cq.Workplane("XY").box(0.044, 0.010, 0.022).translate((0.072, 0.0, 0.007))
    )
    slot_left = slot_left.union(cq.Workplane("XY").cylinder(0.022, 0.005).translate((0.094, 0.0, 0.007)))
    slot_left = slot_left.union(cq.Workplane("XY").cylinder(0.022, 0.005).translate((0.050, 0.0, 0.007)))

    return base.union(top_ring).cut(center_recess).cut(slot_left).cut(slot_left.translate((-0.144, 0.0, 0.0)))
def _upper_body_shape() -> cq.Workplane:
    swivel_plate = cq.Workplane("XY").circle(0.073).extrude(0.010)
    pedestal = cq.Workplane("XY").box(0.150, 0.085, 0.022).translate((0.0, 0.0, 0.021))
    bed = cq.Workplane("XY").box(0.190, 0.090, 0.010).translate((0.010, 0.0, 0.037))

    left_rail = cq.Workplane("XY").box(0.170, 0.014, 0.012).translate((0.020, -0.038, 0.048))
    right_rail = cq.Workplane("XY").box(0.170, 0.014, 0.012).translate((0.020, 0.038, 0.048))

    rear_buttress = cq.Workplane("XY").box(0.056, 0.090, 0.028).translate((-0.068, 0.0, 0.056))
    fixed_jaw_block = cq.Workplane("XY").box(0.024, 0.072, 0.040).translate((-0.040, 0.0, 0.062))

    side_support = cq.Workplane("XY").box(0.065, 0.020, 0.020).translate((0.030, 0.046, 0.030))
    screw_housing = cq.Workplane("YZ").circle(0.010).extrude(0.127).translate((-0.005, 0.050, 0.030))
    bearing_boss = cq.Workplane("YZ").circle(0.0095).extrude(0.011).translate((0.122, 0.050, 0.030))

    clearance_slot = cq.Workplane("XY").box(0.140, 0.064, 0.050).translate((0.050, 0.0, 0.067))

    return (
        swivel_plate.union(pedestal)
        .union(bed)
        .union(left_rail)
        .union(right_rail)
        .union(rear_buttress)
        .union(fixed_jaw_block)
        .union(side_support)
        .union(screw_housing)
        .union(bearing_boss)
        .cut(clearance_slot)
    )
def _front_jaw_shape() -> cq.Workplane:
    shoe = cq.Workplane("XY").box(0.110, 0.058, 0.010).translate((0.035, 0.0, 0.005))
    carriage = cq.Workplane("XY").box(0.036, 0.058, 0.030).translate((0.000, 0.0, 0.025))
    jaw_cap = cq.Workplane("XY").box(0.014, 0.062, 0.040).translate((-0.012, 0.0, 0.030))
    nose = cq.Workplane("XY").box(0.018, 0.046, 0.020).translate((0.020, 0.0, 0.022))
    return shoe.union(carriage).union(jaw_cap).union(nose)
def _handwheel_shape() -> cq.Workplane:
    rim = cq.Workplane("XY").circle(0.040).circle(0.032).extrude(0.010)
    hub = cq.Workplane("XY").circle(0.018).circle(0.0105).extrude(0.010)
    spoke = cq.Workplane("XY").rect(0.005, 0.020).extrude(0.010).translate((0.0, 0.025, 0.0))

    wheel = rim.union(hub)
    for angle_deg in (0.0, 120.0, 240.0):
        wheel = wheel.union(spoke.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))

    spinner_stem = cq.Workplane("XY").circle(0.0032).extrude(0.010).translate((0.0, 0.034, 0.0))
    spinner_knob = cq.Workplane("XY").circle(0.0062).extrude(0.020).translate((0.0, 0.034, 0.006))
    return wheel.union(spinner_stem).union(spinner_knob).translate((0.0, 0.0, -0.005))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="angle_lock_drill_vise")

    cast_blue = model.material("cast_blue", rgba=(0.18, 0.34, 0.54, 1.0))
    base_gray = model.material("base_gray", rgba=(0.48, 0.50, 0.54, 1.0))
    steel = model.material("steel", rgba=(0.72, 0.74, 0.77, 1.0))
    oxide = model.material("oxide", rgba=(0.11, 0.11, 0.12, 1.0))

    swivel_base = model.part("swivel_base")
    swivel_base.visual(
        mesh_from_cadquery(_swivel_base_shape(), "drill_vise_swivel_base"),
        material=base_gray,
        name="base_casting",
    )

    upper_body = model.part("upper_body")
    upper_body.visual(
        mesh_from_cadquery(_upper_body_shape(), "drill_vise_upper_body"),
        material=cast_blue,
        name="body_casting",
    )
    upper_body.visual(
        Box((0.004, 0.072, 0.026)),
        origin=Origin(xyz=(-0.028, 0.0, 0.055)),
        material=steel,
        name="fixed_jaw_face",
    )
    upper_body.visual(
        Cylinder(radius=0.017, length=0.001),
        origin=Origin(xyz=(0.1225, 0.050, 0.030), rpy=(0.0, 1.5707963267948966, 0.0)),
        material=steel,
        name="wheel_retainer",
    )

    front_jaw = model.part("front_jaw")
    front_jaw.visual(
        mesh_from_cadquery(_front_jaw_shape(), "drill_vise_front_jaw"),
        material=cast_blue,
        name="jaw_carriage",
    )
    front_jaw.visual(
        Box((0.004, 0.060, 0.026)),
        origin=Origin(xyz=(-0.020, 0.0, 0.023)),
        material=steel,
        name="front_jaw_face",
    )

    handwheel = model.part("handwheel")
    handwheel.visual(
        mesh_from_cadquery(_handwheel_shape(), "drill_vise_handwheel"),
        origin=Origin(rpy=(0.0, 1.5707963267948966, 0.0)),
        material=oxide,
        name="wheel",
    )

    model.articulation(
        "base_to_upper_body",
        ArticulationType.REVOLUTE,
        parent=swivel_base,
        child=upper_body,
        origin=Origin(xyz=(0.0, 0.0, 0.022 + SWIVEL_GAP)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=80.0,
            velocity=1.4,
            lower=-SWIVEL_LIMIT,
            upper=SWIVEL_LIMIT,
        ),
    )
    model.articulation(
        "body_to_front_jaw",
        ArticulationType.PRISMATIC,
        parent=upper_body,
        child=front_jaw,
        origin=Origin(xyz=(0.006, 0.0, 0.042)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=140.0,
            velocity=0.08,
            lower=0.0,
            upper=JAW_TRAVEL,
        ),
    )
    model.articulation(
        "body_to_handwheel",
        ArticulationType.CONTINUOUS,
        parent=upper_body,
        child=handwheel,
        origin=Origin(xyz=(0.128, 0.050, 0.030)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=2.0,
            velocity=12.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
