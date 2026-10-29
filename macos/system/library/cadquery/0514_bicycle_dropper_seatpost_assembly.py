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
import cadquery as cq
import math
def _hollow_cylinder_mesh(
    outer_radius: float,
    inner_radius: float,
    length: float,
    name: str,
):
    """Closed tube/ring mesh, authored in meters with its base at local z=0."""
    tube = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
    )
    return mesh_from_cadquery(tube, name, tolerance=0.0007, angular_tolerance=0.08)
def _rounded_plate_with_holes(name: str):
    plate = (
        cq.Workplane("XY")
        .box(0.090, 0.060, 0.008)
        .edges("|Z")
        .fillet(0.007)
        .faces(">Z")
        .workplane()
        .pushPoints([(-0.026, 0.0), (0.026, 0.0)])
        .hole(0.007)
    )
    return mesh_from_cadquery(plate, name, tolerance=0.0006, angular_tolerance=0.08)
def _saddle_pad_mesh(name: str):
    # A tapered racing saddle planform: narrow nose, broad rear, rounded edges.
    outline = [
        (0.155, 0.000),
        (0.130, 0.023),
        (0.045, 0.034),
        (-0.075, 0.065),
        (-0.135, 0.074),
        (-0.158, 0.058),
        (-0.158, -0.058),
        (-0.135, -0.074),
        (-0.075, -0.065),
        (0.045, -0.034),
        (0.130, -0.023),
    ]
    pad = cq.Workplane("XY").polyline(outline).close().extrude(0.026)
    pad = pad.edges("|Z").fillet(0.012)
    pad = pad.edges(">Z").fillet(0.004)
    return mesh_from_cadquery(pad, name, tolerance=0.0008, angular_tolerance=0.10)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="two_bolt_collar_dropper_seatpost")

    matte_black = model.material("matte_black", rgba=(0.005, 0.006, 0.007, 1.0))
    satin_black = model.material("satin_black", rgba=(0.03, 0.032, 0.035, 1.0))
    dark_rubber = model.material("dark_rubber", rgba=(0.015, 0.015, 0.014, 1.0))
    gunmetal = model.material("gunmetal", rgba=(0.18, 0.18, 0.17, 1.0))
    brushed_steel = model.material("brushed_steel", rgba=(0.62, 0.60, 0.55, 1.0))
    bolt_dark = model.material("black_oxide", rgba=(0.02, 0.018, 0.016, 1.0))

    outer_tube = model.part("outer_tube")
    outer_tube.visual(
        _hollow_cylinder_mesh(0.0160, 0.0142, 0.430, "straight_outer_tube"),
        material=matte_black,
        name="outer_sleeve",
    )
    outer_tube.visual(
        _hollow_cylinder_mesh(0.0270, 0.0158, 0.032, "seat_tube_binder_ring"),
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        material=gunmetal,
        name="binder_ring",
    )
    # Split clamp ears and pinch bolt on the binder ring.  They are rigidly part
    # of the seat-tube clamp and visibly clamp the straight sleeve.
    for i, x in enumerate((-0.012, 0.012)):
        outer_tube.visual(
            Box((0.007, 0.028, 0.026)),
            origin=Origin(xyz=(x, -0.028, 0.061)),
            material=gunmetal,
            name=f"binder_ear_{i}",
        )
    outer_tube.visual(
        Cylinder(radius=0.0035, length=0.044),
        origin=Origin(xyz=(0.0, -0.041, 0.061), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=brushed_steel,
        name="binder_bolt",
    )
    outer_tube.visual(
        Box((0.004, 0.010, 0.034)),
        origin=Origin(xyz=(0.0, -0.017, 0.061)),
        material=bolt_dark,
        name="binder_split",
    )

    lock_collar = model.part("lock_collar")
    lock_collar.visual(
        _hollow_cylinder_mesh(0.0255, 0.0138, 0.035, "locking_collar_ring"),
        origin=Origin(xyz=(0.0, 0.0, -0.0175)),
        material=gunmetal,
        name="collar_ring",
    )
    lock_collar.visual(
        Box((0.006, 0.020, 0.028)),
        origin=Origin(xyz=(-0.010, -0.032, 0.000)),
        material=gunmetal,
        name="pivot_ear_0",
    )
    lock_collar.visual(
        Box((0.006, 0.020, 0.028)),
        origin=Origin(xyz=(0.010, -0.032, 0.000)),
        material=gunmetal,
        name="pivot_ear_1",
    )
    lock_collar.visual(
        Box((0.018, 0.006, 0.030)),
        origin=Origin(xyz=(0.0, -0.020, 0.000)),
        material=bolt_dark,
        name="collar_split",
    )

    model.articulation(
        "outer_to_collar",
        ArticulationType.FIXED,
        parent=outer_tube,
        child=lock_collar,
        origin=Origin(xyz=(0.0, 0.0, 0.4475)),
    )

    release_lever = model.part("release_lever")
    release_lever.visual(
        Cylinder(radius=0.0055, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=brushed_steel,
        name="lever_pivot",
    )
    release_lever.visual(
        Box((0.010, 0.082, 0.010)),
        origin=Origin(xyz=(0.0, -0.046, -0.002)),
        material=satin_black,
        name="lever_blade",
    )
    release_lever.visual(
        Box((0.020, 0.028, 0.006)),
        origin=Origin(xyz=(0.0, -0.092, -0.004)),
        material=dark_rubber,
        name="lever_paddle",
    )
    model.articulation(
        "collar_to_lever",
        ArticulationType.REVOLUTE,
        parent=lock_collar,
        child=release_lever,
        origin=Origin(xyz=(0.0, -0.032, 0.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=5.0, lower=0.0, upper=1.05),
    )

    inner_post = model.part("inner_post")
    inner_post.visual(
        Cylinder(radius=0.0125, length=0.570),
        origin=Origin(xyz=(0.0, 0.0, 0.075)),
        material=satin_black,
        name="inner_shaft",
    )
    inner_post.visual(
        Cylinder(radius=0.0124, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material=satin_black,
        name="collar_contact_sleeve",
    )
    inner_post.visual(
        Cylinder(radius=0.0180, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.0380)),
        material=gunmetal,
        name="actuator_shoulder",
    )
    inner_post.visual(
        Cylinder(radius=0.0170, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.369)),
        material=gunmetal,
        name="top_head",
    )
    model.articulation(
        "outer_to_inner",
        ArticulationType.PRISMATIC,
        parent=outer_tube,
        child=inner_post,
        origin=Origin(xyz=(0.0, 0.0, 0.430)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=220.0, velocity=0.35, lower=0.0, upper=0.160),
    )

    saddle_clamp = model.part("saddle_clamp")
    saddle_clamp.visual(
        Cylinder(radius=0.0165, length=0.016),
        origin=Origin(xyz=(0.0, 0.0, 0.008)),
        material=gunmetal,
        name="post_cap",
    )
    saddle_clamp.visual(
        Box((0.034, 0.038, 0.036)),
        origin=Origin(xyz=(0.012, 0.0, 0.030)),
        material=gunmetal,
        name="clamp_yoke",
    )
    saddle_clamp.visual(
        Box((0.088, 0.034, 0.008)),
        origin=Origin(xyz=(0.016, 0.0, 0.050)),
        material=gunmetal,
        name="upper_bridge",
    )
    saddle_clamp.visual(
        Box((0.076, 0.010, 0.006)),
        origin=Origin(xyz=(0.016, -0.022, 0.044)),
        material=gunmetal,
        name="rail_cradle_0",
    )
    saddle_clamp.visual(
        Box((0.076, 0.010, 0.006)),
        origin=Origin(xyz=(0.016, 0.022, 0.044)),
        material=gunmetal,
        name="rail_cradle_1",
    )
    saddle_clamp.visual(
        _rounded_plate_with_holes("two_bolt_clamp_plate"),
        origin=Origin(xyz=(0.016, 0.0, 0.058)),
        material=gunmetal,
        name="clamp_plate",
    )
    model.articulation(
        "post_to_clamp",
        ArticulationType.FIXED,
        parent=inner_post,
        child=saddle_clamp,
        origin=Origin(xyz=(0.0, 0.0, 0.378)),
    )

    saddle = model.part("saddle")
    saddle.visual(
        _saddle_pad_mesh("narrow_black_saddle"),
        origin=Origin(xyz=(0.020, 0.0, 0.092)),
        material=dark_rubber,
        name="saddle_pad",
    )
    saddle.visual(
        Box((0.145, 0.013, 0.002)),
        origin=Origin(xyz=(0.020, 0.0, 0.119)),
        material=matte_black,
        name="relief_channel",
    )
    for i, y in enumerate((-0.022, 0.022)):
        saddle.visual(
            Cylinder(radius=0.0030, length=0.170),
            origin=Origin(xyz=(0.016, y, 0.050), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=brushed_steel,
            name=f"saddle_rail_{i}",
        )
        for j, x in enumerate((-0.068, 0.092)):
            saddle.visual(
                Cylinder(radius=0.0023, length=0.040),
                origin=Origin(xyz=(x, y, 0.073)),
                material=brushed_steel,
                name=f"rail_strut_{i}_{j}",
            )
    model.articulation(
        "clamp_to_saddle",
        ArticulationType.FIXED,
        parent=saddle_clamp,
        child=saddle,
        origin=Origin(),
    )

    for idx, x in enumerate((-0.010, 0.042)):
        bolt = model.part(f"clamp_bolt_{idx}")
        bolt.visual(
            Cylinder(radius=0.0022, length=0.032),
            origin=Origin(xyz=(0.0, 0.0, -0.018)),
            material=brushed_steel,
            name="bolt_shank",
        )
        bolt.visual(
            Cylinder(radius=0.0065, length=0.006),
            origin=Origin(xyz=(0.0, 0.0, -0.001)),
            material=brushed_steel,
            name="bolt_head",
        )
        bolt.visual(
            Box((0.010, 0.002, 0.001)),
            origin=Origin(xyz=(0.0, 0.0, 0.0020)),
            material=bolt_dark,
            name="hex_slot",
        )
        model.articulation(
            f"clamp_to_bolt_{idx}",
            ArticulationType.REVOLUTE,
            parent=saddle_clamp,
            child=bolt,
            origin=Origin(xyz=(x, 0.0, 0.066)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=8.0, velocity=8.0, lower=-math.pi, upper=math.pi),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
