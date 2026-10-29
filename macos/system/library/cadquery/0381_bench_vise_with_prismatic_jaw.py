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
def _v_block_body(width: float, depth: float, height: float) -> object:
    """Rectangular jaw block with a real V-groove cut along its width."""
    groove_width = depth * 0.70
    groove_depth = height * 0.34
    body = cq.Workplane("XY").box(width, depth, height)
    cutter = (
        cq.Workplane("YZ")
        .polyline(
            [
                (-groove_width / 2.0, height / 2.0 + 0.006),
                (0.0, height / 2.0 - groove_depth),
                (groove_width / 2.0, height / 2.0 + 0.006),
            ]
        )
        .close()
        .extrude(width + 0.020, both=True)
    )
    return body.cut(cutter)
def _centered_tube(outer_radius: float, inner_radius: float, length: float) -> object:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
def _hex_ring(outer_radius: float, inner_radius: float, length: float) -> object:
    points = [
        (
            outer_radius * math.cos(math.pi / 6.0 + i * math.tau / 6.0),
            outer_radius * math.sin(math.pi / 6.0 + i * math.tau / 6.0),
        )
        for i in range(6)
    ]
    body = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
    bore = (
        cq.Workplane("XY")
        .circle(inner_radius)
        .extrude(length + 0.010)
        .translate((0.0, 0.0, -(length + 0.010) / 2.0))
    )
    return body.cut(bore)
def _helix(radius: float, radius_eps: float, pitch: float, height: float, d: float = 0.0):
    turns = height / pitch

    def func(t: float) -> tuple[float, float, float]:
        z = height * t
        r = radius + radius_eps
        angle = math.tau * turns * t
        if t < 0.04:
            r = radius + radius_eps * math.sin(math.pi * t / 0.08)
        elif t > 0.96:
            r = radius + radius_eps * math.sin(math.pi * (1.0 - t) / 0.08)
        return (r * math.cos(angle), r * math.sin(angle), z + d)

    return func
def _threaded_shaft(core_radius: float, thread_radius: float, pitch: float, length: float) -> object:
    """A compact helical ridge on a cylindrical leadscrew core."""
    flank = pitch * 0.18
    core = cq.Workplane("XY").circle(core_radius).extrude(length)
    root_a = cq.Workplane("XY").parametricCurve(_helix(core_radius * 0.98, 0.0, pitch, length, -flank)).val()
    root_b = cq.Workplane("XY").parametricCurve(_helix(core_radius * 0.98, 0.0, pitch, length, flank)).val()
    crest_a = cq.Workplane("XY").parametricCurve(_helix(thread_radius, 0.0, pitch, length, -flank * 0.25)).val()
    crest_b = cq.Workplane("XY").parametricCurve(_helix(thread_radius, 0.0, pitch, length, flank * 0.25)).val()
    faces = [
        cq.Face.makeRuledSurface(root_a, root_b),
        cq.Face.makeRuledSurface(root_a, crest_a),
        cq.Face.makeRuledSurface(root_b, crest_b),
        cq.Face.makeRuledSurface(crest_a, crest_b),
    ]
    thread = cq.Solid.makeSolid(cq.Shell.makeShell(faces))
    return core.union(thread)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cross_drilling_vise")

    cast_iron = model.material("blue_gray_cast_iron", rgba=(0.22, 0.29, 0.34, 1.0))
    dark_iron = model.material("dark_burnished_steel", rgba=(0.06, 0.065, 0.07, 1.0))
    polished = model.material("polished_steel", rgba=(0.70, 0.72, 0.70, 1.0))
    black = model.material("black_recess", rgba=(0.005, 0.005, 0.006, 1.0))
    handle_red = model.material("red_handle_knobs", rgba=(0.65, 0.05, 0.035, 1.0))

    base = model.part("base_plate")
    base.visual(
        Box((0.66, 0.48, 0.035)),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material=cast_iron,
        name="base_plate",
    )
    base.visual(
        mesh_from_cadquery(_centered_tube(0.205, 0.188, 0.002), "swivel_shadow_ring"),
        origin=Origin(xyz=(0.0, 0.0, 0.036)),
        material=dark_iron,
        name="swivel_shadow_ring",
    )
    for idx, (x, y) in enumerate(((-0.24, -0.16), (0.24, -0.16), (-0.24, 0.16), (0.24, 0.16))):
        base.visual(
            Box((0.105, 0.030, 0.002)),
            origin=Origin(xyz=(x, y, 0.036)),
            material=black,
            name=f"mount_slot_{idx}",
        )

    turntable = model.part("turntable")
    turntable.visual(
        Cylinder(radius=0.185, length=0.025),
        origin=Origin(xyz=(0.0, 0.0, 0.0125)),
        material=cast_iron,
        name="turntable_disk",
    )
    turntable.visual(
        Box((0.48, 0.40, 0.032)),
        origin=Origin(xyz=(0.0, -0.040, 0.041)),
        material=cast_iron,
        name="rectangular_bed",
    )
    turntable.visual(
        Cylinder(radius=0.0105, length=0.365),
        origin=Origin(xyz=(-0.115, -0.040, 0.095), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished,
        name="guide_bar_0",
    )
    turntable.visual(
        Cylinder(radius=0.0105, length=0.365),
        origin=Origin(xyz=(0.115, -0.040, 0.095), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished,
        name="guide_bar_1",
    )
    for idx, x in enumerate((-0.115, 0.115)):
        turntable.visual(
            Box((0.054, 0.036, 0.052)),
            origin=Origin(xyz=(x, -0.220, 0.0825)),
            material=cast_iron,
            name=f"front_bar_lug_{idx}",
        )
    turntable.visual(
        mesh_from_cadquery(_centered_tube(0.024, 0.0105, 0.038), "front_screw_bearing"),
        origin=Origin(xyz=(0.0, -0.215, 0.095), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_iron,
        name="front_screw_bearing",
    )
    turntable.visual(
        Box((0.060, 0.036, 0.018)),
        origin=Origin(xyz=(0.0, -0.215, 0.064)),
        material=cast_iron,
        name="bearing_pedestal",
    )
    turntable.visual(
        Box((0.335, 0.058, 0.018)),
        origin=Origin(xyz=(0.0, 0.105, 0.128)),
        material=cast_iron,
        name="rear_saddle",
    )
    for idx, x in enumerate((-0.160, 0.160)):
        turntable.visual(
            Box((0.038, 0.052, 0.063)),
            origin=Origin(xyz=(x, 0.105, 0.0875)),
            material=cast_iron,
            name=f"rear_support_{idx}",
        )
    turntable.visual(
        mesh_from_cadquery(_v_block_body(0.335, 0.058, 0.090), "fixed_v_block"),
        origin=Origin(xyz=(0.0, 0.105, 0.180)),
        material=cast_iron,
        name="fixed_v_block",
    )
    turntable.visual(
        Box((0.330, 0.010, 0.030)),
        origin=Origin(xyz=(0.0, 0.072, 0.180)),
        material=dark_iron,
        name="fixed_jaw_face",
    )

    moving = model.part("moving_jaw")
    moving.visual(
        mesh_from_cadquery(_v_block_body(0.335, 0.058, 0.090), "moving_v_block"),
        origin=Origin(xyz=(0.0, 0.0, 0.180)),
        material=cast_iron,
        name="moving_v_block",
    )
    moving.visual(
        Box((0.335, 0.058, 0.020)),
        origin=Origin(xyz=(0.0, 0.0, 0.126)),
        material=cast_iron,
        name="moving_saddle",
    )
    moving.visual(
        Box((0.330, 0.010, 0.030)),
        origin=Origin(xyz=(0.0, 0.033, 0.180)),
        material=dark_iron,
        name="moving_jaw_face",
    )
    for idx, x in enumerate((-0.115, 0.115)):
        moving.visual(
            mesh_from_cadquery(_centered_tube(0.024, 0.0145, 0.058), f"guide_bushing_{idx}"),
            origin=Origin(xyz=(x, 0.0, 0.095), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=dark_iron,
            name=f"guide_bushing_{idx}",
        )
        moving.visual(
            Box((0.012, 0.050, 0.006)),
            origin=Origin(xyz=(x, 0.0, 0.0815)),
            material=dark_iron,
            name=f"guide_wear_pad_{idx}",
        )
    moving.visual(
        mesh_from_cadquery(_hex_ring(0.031, 0.0165, 0.040), "lead_nut"),
        origin=Origin(xyz=(0.0, 0.0, 0.095), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_iron,
        name="lead_nut",
    )

    leadscrew = model.part("leadscrew")
    leadscrew.visual(
        mesh_from_cadquery(_threaded_shaft(0.0105, 0.0130, 0.026, 0.355), "threaded_shaft", tolerance=0.0008),
        origin=Origin(xyz=(0.0, 0.015, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished,
        name="threaded_shaft",
    )
    for idx, y in enumerate(0.065 + i * 0.024 for i in range(11)):
        leadscrew.visual(
            Cylinder(radius=0.0128, length=0.0022),
            origin=Origin(xyz=(0.0, y, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=polished,
            name=f"thread_ridge_{idx}",
        )
    leadscrew.visual(
        mesh_from_cadquery(_hex_ring(0.021, 0.0001, 0.038), "hex_drive_hub"),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_iron,
        name="hex_drive_hub",
    )
    leadscrew.visual(
        Cylinder(radius=0.0075, length=0.185),
        origin=Origin(xyz=(0.0, -0.012, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="t_bar",
    )
    leadscrew.visual(
        Sphere(radius=0.014),
        origin=Origin(xyz=(-0.097, -0.012, 0.0)),
        material=handle_red,
        name="handle_knob_0",
    )
    leadscrew.visual(
        Sphere(radius=0.014),
        origin=Origin(xyz=(0.097, -0.012, 0.0)),
        material=handle_red,
        name="handle_knob_1",
    )

    model.articulation(
        "base_to_turntable",
        ArticulationType.CONTINUOUS,
        parent=base,
        child=turntable,
        origin=Origin(xyz=(0.0, 0.0, 0.035)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=80.0, velocity=1.0),
    )
    model.articulation(
        "turntable_to_moving_jaw",
        ArticulationType.PRISMATIC,
        parent=turntable,
        child=moving,
        origin=Origin(xyz=(0.0, -0.045, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=300.0, velocity=0.06, lower=0.0, upper=0.085),
    )
    model.articulation(
        "turntable_to_leadscrew",
        ArticulationType.CONTINUOUS,
        parent=turntable,
        child=leadscrew,
        origin=Origin(xyz=(0.0, -0.255, 0.095)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=4.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
