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
JAW_TRAVEL = 0.18
JAW_REST_OFFSET = 0.10
def _disk(radius: float, thickness: float, center_xyz: tuple[float, float, float]):
    cx, cy, cz = center_xyz
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(thickness)
        .translate((cx, cy, cz - thickness * 0.5))
    )
def _base_casting_shape():
    lower_plate = _disk(0.147, 0.022, (-0.055, 0.0, -0.146))
    upper_plate = _disk(0.140, 0.018, (-0.055, 0.0, -0.126))
    pedestal = cq.Workplane("XY").box(0.170, 0.215, 0.070).translate((-0.055, 0.0, -0.090))
    body = cq.Workplane("XY").box(0.118, 0.285, 0.138).translate((-0.061, 0.0, 0.008))
    anvil = cq.Workplane("XY").box(0.102, 0.116, 0.012).translate((-0.060, 0.0, 0.083))
    screw_housing = (
        cq.Workplane("YZ")
        .circle(0.032)
        .extrude(0.070)
        .translate((-0.074, 0.0, 0.0))
    )
    cheek_pad = cq.Workplane("XY").box(0.050, 0.200, 0.050).translate((-0.050, 0.0, -0.060))
    return lower_plate.union(upper_plate).union(pedestal).union(body).union(anvil).union(screw_housing).union(cheek_pad)
def _jaw_carriage_shape():
    carriage = cq.Workplane("XY").box(0.082, 0.174, 0.138).translate((-0.022, 0.0, -0.016))
    front_plate = cq.Workplane("XY").box(0.026, 0.286, 0.120).translate((0.013, 0.0, 0.000))
    anvil = cq.Workplane("XY").box(0.076, 0.112, 0.012).translate((0.006, 0.0, 0.059))
    boss = (
        cq.Workplane("YZ")
        .circle(0.034)
        .extrude(0.034)
        .translate((0.026, 0.0, 0.0))
    )
    guide_clearance = cq.Workplane("XY").box(0.125, 0.118, 0.060).translate((-0.0025, 0.0, -0.052))
    return carriage.union(front_plate).union(anvil).union(boss).cut(guide_clearance)
def _handwheel_shape():
    rim = cq.Workplane("YZ").circle(0.052).circle(0.041).extrude(0.010, both=True)
    hub = cq.Workplane("YZ").circle(0.017).extrude(0.014, both=True)
    spoke = cq.Workplane("XY").box(0.008, 0.070, 0.012).translate((0.0, 0.035, 0.0))
    spokes = spoke.union(
        spoke.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 120.0)
    ).union(
        spoke.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 240.0)
    )
    return rim.union(hub).union(spokes)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="swivel_base_woodworking_vise")

    cast_iron = model.material("cast_iron", rgba=(0.24, 0.28, 0.34, 1.0))
    machined_steel = model.material("machined_steel", rgba=(0.71, 0.74, 0.78, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.18, 0.20, 0.22, 1.0))
    wood_pad = model.material("wood_pad", rgba=(0.59, 0.43, 0.24, 1.0))
    handle_grip = model.material("handle_grip", rgba=(0.09, 0.09, 0.10, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_casting_shape(), "vise_base_casting"),
        material=cast_iron,
        name="base_casting",
    )
    base.visual(
        Box((0.335, 0.100, 0.048)),
        origin=Origin(xyz=(0.1675, 0.0, -0.052)),
        material=machined_steel,
        name="guide_beam",
    )
    base.visual(
        Box((0.018, 0.240, 0.085)),
        origin=Origin(xyz=(-0.009, 0.0, 0.020)),
        material=wood_pad,
        name="fixed_pad",
    )
    base.visual(
        Cylinder(radius=0.015, length=0.020),
        origin=Origin(xyz=(-0.030, 0.139, -0.122), rpy=(1.5707963267948966, 0.0, 0.0)),
        material=machined_steel,
        name="lock_boss",
    )

    jaw = model.part("jaw")
    jaw.visual(
        mesh_from_cadquery(_jaw_carriage_shape(), "vise_jaw_carriage"),
        material=cast_iron,
        name="carriage",
    )
    jaw.visual(
        Box((0.018, 0.240, 0.085)),
        origin=Origin(xyz=(-0.009, 0.0, 0.020)),
        material=wood_pad,
        name="jaw_pad",
    )
    jaw.visual(
        Box((0.110, 0.108, 0.006)),
        origin=Origin(xyz=(-0.005, 0.0, -0.025)),
        material=machined_steel,
        name="guide_shoe",
    )

    handwheel = model.part("handwheel")
    handwheel.visual(
        mesh_from_cadquery(_handwheel_shape(), "vise_handwheel"),
        material=dark_steel,
        name="wheel",
    )
    handwheel.visual(
        Cylinder(radius=0.010, length=0.024),
        origin=Origin(xyz=(-0.012, 0.0, 0.0), rpy=(0.0, 1.5707963267948966, 0.0)),
        material=machined_steel,
        name="spindle",
    )

    swivel_lock = model.part("swivel_lock")
    swivel_lock.visual(
        Cylinder(radius=0.011, length=0.022),
        origin=Origin(xyz=(0.0, 0.011, 0.0), rpy=(1.5707963267948966, 0.0, 0.0)),
        material=machined_steel,
        name="hub",
    )
    swivel_lock.visual(
        Box((0.084, 0.020, 0.020)),
        origin=Origin(xyz=(0.042, 0.011, 0.0)),
        material=machined_steel,
        name="arm",
    )
    swivel_lock.visual(
        Cylinder(radius=0.014, length=0.038),
        origin=Origin(xyz=(0.084, 0.011, 0.0), rpy=(1.5707963267948966, 0.0, 0.0)),
        material=handle_grip,
        name="grip",
    )

    jaw_slide = model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=base,
        child=jaw,
        origin=Origin(xyz=(JAW_REST_OFFSET, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=2500.0,
            velocity=0.08,
            lower=0.0,
            upper=JAW_TRAVEL,
        ),
    )
    model.articulation(
        "handwheel_spin",
        ArticulationType.CONTINUOUS,
        parent=jaw,
        child=handwheel,
        origin=Origin(xyz=(0.084, 0.0, 0.040)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=35.0,
            velocity=8.0,
        ),
    )
    swivel_lock_pivot = model.articulation(
        "swivel_lock_pivot",
        ArticulationType.REVOLUTE,
        parent=base,
        child=swivel_lock,
        origin=Origin(xyz=(-0.030, 0.149, -0.122)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=2.0,
            lower=-0.75,
            upper=0.35,
        ),
    )

    base.meta["primary_motion"] = jaw_slide.name
    jaw.meta["role"] = "sliding_front_jaw"
    handwheel.meta["role"] = "front_drive_handwheel"
    swivel_lock.meta["role"] = "swivel_ring_lock"

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
