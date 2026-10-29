# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, adjustable_weight_bench_with_hinged_backrest, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: adjustable_weight_bench_with_hinged_backrest

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
def _rounded_pad(length: float, width: float, thickness: float, radius: float, name: str):
    """A single upholstered pad with rounded plan corners."""
    solid = cq.Workplane("XY").box(length, width, thickness).edges("|Z").fillet(radius)
    return mesh_from_cadquery(solid, name, tolerance=0.0015, angular_tolerance=0.08)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="flat_incline_utility_bench")

    frame_mat = model.material("powder_coated_black", rgba=(0.02, 0.022, 0.024, 1.0))
    pin_mat = model.material("brushed_steel", rgba=(0.55, 0.57, 0.56, 1.0))
    pad_mat = model.material("black_vinyl", rgba=(0.015, 0.014, 0.013, 1.0))
    seam_mat = model.material("slightly_gloss_seam", rgba=(0.035, 0.035, 0.034, 1.0))
    rubber_mat = model.material("matte_rubber", rgba=(0.005, 0.005, 0.004, 1.0))

    hinge_z = 0.405
    tube_y = Origin(rpy=(math.pi / 2.0, 0.0, 0.0))

    base = model.part("base")

    # Lower rectangular transport frame.
    for y in (-0.24, 0.24):
        base.visual(
            Box((1.70, 0.045, 0.045)),
            origin=Origin(xyz=(0.0, y, 0.10)),
            material=frame_mat,
            name=f"side_rail_{0 if y < 0 else 1}",
        )
    for x, name in ((0.80, "front_crossmember"), (-0.80, "rear_crossmember"), (0.06, "center_crossmember")):
        base.visual(
            Box((0.080, 0.585, 0.045)),
            origin=Origin(xyz=(x, 0.0, 0.10)),
            material=frame_mat,
            name=name,
        )

    # Lift handle: two projecting arms welded to the front crossmember and a grip between the wheels.
    for y in (-0.055, 0.055):
        base.visual(
            Box((0.205, 0.030, 0.035)),
            origin=Origin(xyz=(0.932, y, 0.120)),
            material=frame_mat,
            name=f"front_handle_arm_{0 if y < 0 else 1}",
        )
    base.visual(
        Box((0.045, 0.185, 0.038)),
        origin=Origin(xyz=(1.055, 0.0, 0.120)),
        material=frame_mat,
        name="front_handle_grip",
    )

    # Small transport wheels tied together by a visible axle.
    base.visual(
        Cylinder(radius=0.012, length=0.66),
        origin=Origin(xyz=(0.82, 0.0, 0.070), rpy=tube_y.rpy),
        material=pin_mat,
        name="front_axle",
    )
    for y in (-0.315, 0.315):
        side = 0 if y < 0 else 1
        base.visual(
            Cylinder(radius=0.068, length=0.048),
            origin=Origin(xyz=(0.82, y, 0.070), rpy=tube_y.rpy),
            material=rubber_mat,
            name=f"wheel_tire_{side}",
        )
        base.visual(
            Cylinder(radius=0.032, length=0.054),
            origin=Origin(xyz=(0.82, y, 0.070), rpy=tube_y.rpy),
            material=pin_mat,
            name=f"wheel_hub_{side}",
        )

    # Upper support rails and diagonal braces carrying the pad hinges.
    for y in (-0.18, 0.18):
        side = 0 if y < 0 else 1
        base.visual(
            Box((0.76, 0.035, 0.035)),
            origin=Origin(xyz=(0.20, y, 0.360)),
            material=frame_mat,
            name=f"upper_rail_{side}",
        )
        base.visual(
            Box((0.72, 0.032, 0.032)),
            origin=Origin(xyz=(0.325, y, 0.235), rpy=(0.0, 0.395, 0.0)),
            material=frame_mat,
            name=f"front_brace_{side}",
        )
        base.visual(
            Box((0.80, 0.032, 0.032)),
            origin=Origin(xyz=(-0.415, y, 0.235), rpy=(0.0, -0.345, 0.0)),
            material=frame_mat,
            name=f"rear_brace_{side}",
        )

    # Hinge clevis plates and pins at the two pad pivots.
    for x, prefix in ((0.55, "seat"), (0.03, "back")):
        for y in (-0.205, 0.205):
            side = 0 if y < 0 else 1
            base.visual(
                Box((0.075, 0.030, 0.125)),
                origin=Origin(xyz=(x, y, 0.365)),
                material=frame_mat,
                name=f"{prefix}_hinge_plate_{side}",
            )
        base.visual(
            Cylinder(radius=0.008, length=0.49),
            origin=Origin(xyz=(x, 0.0, hinge_z), rpy=tube_y.rpy),
            material=pin_mat,
            name=f"{prefix}_hinge_pin",
        )

    # Lower rear pivot for the adjustable ladder support.
    for y in (-0.226, 0.226):
        side = 0 if y < 0 else 1
        base.visual(
            Box((0.060, 0.032, 0.130)),
            origin=Origin(xyz=(-0.82, y, 0.130)),
            material=frame_mat,
            name=f"rear_pivot_plate_{side}",
        )
    for y in (-0.251, 0.251):
        side = 0 if y < 0 else 1
        base.visual(
            Cylinder(radius=0.012, length=0.040),
            origin=Origin(xyz=(-0.82, y, 0.150), rpy=tube_y.rpy),
            material=pin_mat,
            name=f"rear_pivot_cap_{side}",
        )

    backrest = model.part("backrest")
    backrest.visual(
        _rounded_pad(0.96, 0.320, 0.075, 0.035, "backrest_pad_mesh"),
        origin=Origin(xyz=(-0.500, 0.0, 0.057)),
        material=pad_mat,
        name="back_pad",
    )
    backrest.visual(
        Box((0.008, 0.285, 0.004)),
        origin=Origin(xyz=(-0.500, 0.0, 0.096)),
        material=seam_mat,
        name="back_center_seam",
    )
    backrest.visual(
        Cylinder(radius=0.014, length=0.300),
        origin=Origin(rpy=tube_y.rpy),
        material=pin_mat,
        name="back_hinge_sleeve",
    )
    backrest.visual(
        Box((0.060, 0.315, 0.020)),
        origin=Origin(xyz=(-0.030, 0.0, 0.018)),
        material=pin_mat,
        name="back_hinge_leaf",
    )
    for y in (-0.128, 0.128):
        side = 0 if y < 0 else 1
        backrest.visual(
            Box((0.620, 0.026, 0.024)),
            origin=Origin(xyz=(-0.555, y, 0.012)),
            material=frame_mat,
            name=f"adjust_bracket_rail_{side}",
        )
    for i, x in enumerate((-0.360, -0.500, -0.640, -0.780)):
        backrest.visual(
            Box((0.035, 0.300, 0.026)),
            origin=Origin(xyz=(x, 0.0, 0.004)),
            material=pin_mat,
            name=f"adjust_ladder_catch_{i}",
        )

    seat = model.part("seat")
    seat.visual(
        _rounded_pad(0.490, 0.330, 0.075, 0.035, "seat_pad_mesh"),
        origin=Origin(xyz=(-0.245, 0.0, 0.057)),
        material=pad_mat,
        name="seat_pad",
    )
    seat.visual(
        Box((0.006, 0.295, 0.004)),
        origin=Origin(xyz=(-0.245, 0.0, 0.096)),
        material=seam_mat,
        name="seat_center_seam",
    )
    seat.visual(
        Cylinder(radius=0.014, length=0.300),
        origin=Origin(rpy=tube_y.rpy),
        material=pin_mat,
        name="seat_hinge_sleeve",
    )
    seat.visual(
        Box((0.060, 0.315, 0.020)),
        origin=Origin(xyz=(-0.030, 0.0, 0.018)),
        material=pin_mat,
        name="seat_hinge_leaf",
    )

    support = model.part("support_ladder")
    support.visual(
        Cylinder(radius=0.018, length=0.420),
        origin=Origin(rpy=tube_y.rpy),
        material=pin_mat,
        name="ladder_pivot_sleeve",
    )
    for y in (-0.195, 0.195):
        side = 0 if y < 0 else 1
        support.visual(
            Box((0.030, 0.030, 0.425)),
            origin=Origin(xyz=(-0.140, y, 0.160), rpy=(0.0, -0.720, 0.0)),
            material=frame_mat,
            name=f"ladder_side_rail_{side}",
        )
    for i, (x, z) in enumerate(((-0.070, 0.080), (-0.154, 0.176), (-0.238, 0.272))):
        support.visual(
            Box((0.038, 0.430, 0.026)),
            origin=Origin(xyz=(x, 0.0, z)),
            material=pin_mat,
            name=f"ladder_rung_{i}",
        )

    model.articulation(
        "back_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=backrest,
        origin=Origin(xyz=(0.03, 0.0, hinge_z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=80.0, velocity=1.4, lower=0.0, upper=1.22),
    )
    model.articulation(
        "seat_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=seat,
        origin=Origin(xyz=(0.55, 0.0, hinge_z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=45.0, velocity=1.2, lower=0.0, upper=0.36),
    )
    model.articulation(
        "support_pivot",
        ArticulationType.REVOLUTE,
        parent=base,
        child=support,
        origin=Origin(xyz=(-0.82, 0.0, 0.150)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=1.1, lower=0.0, upper=0.78),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
