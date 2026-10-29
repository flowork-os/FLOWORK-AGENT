# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_dropper_seatpost_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_dropper_seatpost_assembly

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
def _cq_centered_cylinder(radius: float, length: float, axis: str = "z") -> cq.Workplane:
    cyl = cq.Workplane("XY").circle(radius).extrude(length, both=True)
    if axis == "x":
        return cyl.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "y":
        return cyl.rotate((0, 0, 0), (1, 0, 0), 90)
    return cyl
def _cq_tube(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
    )
def _binder_ring_shape() -> cq.Workplane:
    height = 0.032
    ring = (
        cq.Workplane("XY")
        .circle(0.024)
        .circle(0.0140)
        .extrude(height, both=True)
    )
    # A real quick-release collar has a saw slot and two clamp ears.
    slot = cq.Workplane("XY").box(0.028, 0.012, height * 1.4).translate((0.019, 0.0, 0.0))
    lug_a = cq.Workplane("XY").box(0.026, 0.008, 0.025).translate((0.028, 0.017, 0.0))
    lug_b = cq.Workplane("XY").box(0.026, 0.008, 0.025).translate((0.028, -0.017, 0.0))
    body = ring.cut(slot).union(lug_a).union(lug_b)
    pivot_hole = _cq_centered_cylinder(0.0033, 0.070, "y").translate((0.036, 0.0, 0.0))
    return body.cut(pivot_hole)
def _quick_lever_shape() -> cq.Workplane:
    barrel = _cq_centered_cylinder(0.0052, 0.008, "y")
    pin = _cq_centered_cylinder(0.0035, 0.046, "y")
    neck = cq.Workplane("XY").box(0.014, 0.008, 0.018).translate((0.007, 0.0, -0.010))
    blade = (
        cq.Workplane("XY")
        .box(0.018, 0.008, 0.078)
        .translate((0.020, 0.0, -0.050))
        .edges("|Y")
        .fillet(0.002)
    )
    cam_lobe = _cq_centered_cylinder(0.007, 0.006, "y").translate((0.004, 0.0, -0.003))
    return barrel.union(pin).union(neck).union(blade).union(cam_lobe)
def _post_head_shape() -> cq.Workplane:
    neck = _cq_centered_cylinder(0.016, 0.030, "z").translate((0.0, 0.0, 0.186))
    cradle = (
        cq.Workplane("XY")
        .box(0.090, 0.060, 0.014)
        .translate((0.0, 0.0, 0.205))
        .edges("|Z")
        .fillet(0.006)
    )
    rail_seat_0 = _cq_centered_cylinder(0.0042, 0.082, "x").translate((0.0, -0.022, 0.212))
    rail_seat_1 = _cq_centered_cylinder(0.0042, 0.082, "x").translate((0.0, 0.022, 0.212))
    return neck.union(cradle).cut(rail_seat_0).cut(rail_seat_1)
def _clamp_plate_shape() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(0.096, 0.060, 0.010)
        .edges("|Z")
        .fillet(0.006)
    )
    for x in (-0.027, 0.027):
        cutter = _cq_centered_cylinder(0.0035, 0.020, "z").translate((x, 0.0, 0.0))
        plate = plate.cut(cutter)
    return plate
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="hydraulic_dropper_seatpost")

    black = model.material("black_anodized", color=(0.015, 0.016, 0.018, 1.0))
    satin = model.material("satin_aluminum", color=(0.72, 0.70, 0.66, 1.0))
    gunmetal = model.material("gunmetal", color=(0.18, 0.19, 0.20, 1.0))
    brass = model.material("bronze_stanchion", color=(0.78, 0.61, 0.36, 1.0))
    rubber = model.material("black_rubber", color=(0.004, 0.004, 0.004, 1.0))

    lower_body = model.part("lower_body")
    lower_body.visual(
        mesh_from_cadquery(_cq_tube(0.014, 0.0118, 0.360), "outer_tube", tolerance=0.0005),
        material=black,
        name="outer_tube",
    )
    lower_body.visual(
        mesh_from_cadquery(_cq_tube(0.01185, 0.0103, 0.014), "lower_bushing", tolerance=0.0005),
        origin=Origin(xyz=(0.0, 0.0, 0.150)),
        material=rubber,
        name="lower_bushing",
    )
    lower_body.visual(
        mesh_from_cadquery(_cq_tube(0.01185, 0.0103, 0.014), "upper_bushing", tolerance=0.0005),
        origin=Origin(xyz=(0.0, 0.0, 0.306)),
        material=rubber,
        name="upper_bushing",
    )

    binder_ring = model.part("binder_ring")
    binder_ring.visual(
        mesh_from_cadquery(_binder_ring_shape(), "binder_ring", tolerance=0.0005),
        material=gunmetal,
        name="split_collar",
    )
    model.articulation(
        "lower_to_binder",
        ArticulationType.FIXED,
        parent=lower_body,
        child=binder_ring,
        origin=Origin(xyz=(0.0, 0.0, 0.344)),
    )

    quick_lever = model.part("quick_lever")
    quick_lever.visual(
        mesh_from_cadquery(_quick_lever_shape(), "quick_lever", tolerance=0.0005),
        material=satin,
        name="cam_lever",
    )
    model.articulation(
        "binder_to_lever",
        ArticulationType.REVOLUTE,
        parent=binder_ring,
        child=quick_lever,
        origin=Origin(xyz=(0.036, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=3.0, lower=0.0, upper=1.55),
    )

    inner_post = model.part("inner_post")
    inner_post.visual(
        Cylinder(radius=0.0105, length=0.350),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=brass,
        name="stanchion",
    )
    inner_post.visual(
        mesh_from_cadquery(_post_head_shape(), "post_head", tolerance=0.0005),
        material=black,
        name="saddle_cradle",
    )
    model.articulation(
        "lower_to_inner",
        ArticulationType.PRISMATIC,
        parent=lower_body,
        child=inner_post,
        origin=Origin(xyz=(0.0, 0.0, 0.310)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=220.0, velocity=0.35, lower=0.0, upper=0.100),
    )

    clamp_plate = model.part("clamp_plate")
    clamp_plate.visual(
        mesh_from_cadquery(_clamp_plate_shape(), "clamp_plate", tolerance=0.0005),
        material=black,
        name="upper_plate",
    )
    model.articulation(
        "inner_to_plate",
        ArticulationType.FIXED,
        parent=inner_post,
        child=clamp_plate,
        origin=Origin(xyz=(0.0, 0.0, 0.225)),
    )

    for idx, y in enumerate((-0.022, 0.022)):
        rail = model.part(f"rail_{idx}")
        rail.visual(
            Cylinder(radius=0.004, length=0.168),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=satin,
            name="round_rail",
        )
        model.articulation(
            f"inner_to_rail_{idx}",
            ArticulationType.FIXED,
            parent=inner_post,
            child=rail,
            origin=Origin(xyz=(0.0, y, 0.216)),
        )

    for idx, x in enumerate((-0.027, 0.027)):
        bolt = model.part(f"bolt_{idx}")
        bolt.visual(
            Cylinder(radius=0.0027, length=0.032),
            origin=Origin(xyz=(0.0, 0.0, -0.008)),
            material=satin,
            name="bolt_shank",
        )
        bolt.visual(
            Cylinder(radius=0.0062, length=0.005),
            origin=Origin(xyz=(0.0, 0.0, 0.0075)),
            material=satin,
            name="bolt_head",
        )
        bolt.visual(
            Box((0.010, 0.0022, 0.0012)),
            origin=Origin(xyz=(0.0, 0.0, 0.0102)),
            material=gunmetal,
            name="hex_slot",
        )
        model.articulation(
            f"plate_to_bolt_{idx}",
            ArticulationType.CONTINUOUS,
            parent=clamp_plate,
            child=bolt,
            origin=Origin(xyz=(x, 0.0, 0.0)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=1.2, velocity=8.0),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
