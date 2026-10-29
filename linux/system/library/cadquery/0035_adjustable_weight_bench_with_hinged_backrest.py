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
def _mesh(shape: cq.Workplane, name: str):
    return mesh_from_cadquery(shape, name)
def _rounded_pad(width: float, length: float, thickness: float) -> cq.Workplane:
    pad = cq.Workplane("XY").box(
        width,
        length,
        thickness,
        centered=(True, True, False),
    )
    pad = pad.edges("|Z").fillet(min(0.025, width * 0.15, length * 0.06))
    pad = pad.faces(">Z").edges().fillet(min(0.010, thickness * 0.30))
    return pad
def _seat_pad_shape() -> cq.Workplane:
    return _rounded_pad(0.26, 0.29, 0.05).translate((0.0, -0.145, 0.002))
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="apartment_gym_bench")

    frame_paint = model.material("frame_paint", rgba=(0.18, 0.19, 0.20, 1.0))
    pad_vinyl = model.material("pad_vinyl", rgba=(0.10, 0.10, 0.11, 1.0))
    steel = model.material("steel", rgba=(0.64, 0.66, 0.69, 1.0))
    wheel_rubber = model.material("wheel_rubber", rgba=(0.08, 0.08, 0.09, 1.0))
    knob_rubber = model.material("knob_rubber", rgba=(0.16, 0.16, 0.17, 1.0))

    frame = model.part("frame")
    for name, size, xyz in (
        ("front_foot", (0.44, 0.08, 0.04), (0.0, -0.34, 0.02)),
        ("rear_foot", (0.34, 0.08, 0.04), (0.0, 0.32, 0.02)),
        ("spine", (0.08, 0.72, 0.04), (0.0, -0.03, 0.145)),
        ("front_riser", (0.08, 0.15, 0.19), (0.0, -0.29, 0.135)),
        ("rear_riser", (0.08, 0.14, 0.15), (0.0, 0.285, 0.115)),
        ("hinge_tower", (0.10, 0.16, 0.22), (0.0, 0.02, 0.29)),
        ("tower_web", (0.08, 0.16, 0.035), (0.0, 0.02, 0.1775)),
        ("seat_bridge", (0.12, 0.16, 0.022), (0.0, -0.10, 0.387)),
        ("hinge_bridge", (0.18, 0.12, 0.022), (0.0, 0.02, 0.387)),
        ("pivot_bridge", (0.16, 0.08, 0.03), (0.0, 0.16, 0.19)),
        ("pivot_web", (0.08, 0.06, 0.035), (0.0, 0.15, 0.1625)),
        ("pivot_lug_0", (0.018, 0.04, 0.06), (-0.078, 0.18, 0.205)),
        ("pivot_lug_1", (0.018, 0.04, 0.06), (0.078, 0.18, 0.205)),
        ("hinge_lug_0", (0.022, 0.045, 0.04), (-0.095, 0.03, 0.375)),
        ("hinge_lug_1", (0.022, 0.045, 0.04), (0.095, 0.03, 0.375)),
        ("selector_mount", (0.05, 0.05, 0.05), (0.070, 0.10, 0.295)),
    ):
        frame.visual(
            Box(size),
            origin=Origin(xyz=xyz),
            material=frame_paint,
            name=name,
        )
    frame.visual(
        Box((0.282, 0.028, 0.028)),
        origin=Origin(xyz=(0.0, -0.34, 0.080)),
        material=steel,
        name="front_axle",
    )
    frame.visual(
        Cylinder(radius=0.012, length=0.118),
        origin=Origin(xyz=(0.0, 0.20, 0.19), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="pivot_axle",
    )

    back_pad = model.part("back_pad")
    back_pad.visual(
        _mesh(_rounded_pad(0.26, 0.72, 0.05), "bench_back_cushion"),
        origin=Origin(xyz=(0.0, 0.36, 0.002)),
        material=pad_vinyl,
        name="back_cushion",
    )
    for index, x_pos in enumerate((-0.095, 0.095)):
        back_pad.visual(
            Box((0.030, 0.030, 0.040)),
            origin=Origin(xyz=(x_pos, 0.015, 0.008)),
            material=steel,
            name=f"hinge_strap_{index}",
        )
    for index, x_pos in enumerate((-0.095, 0.095)):
        back_pad.visual(
            Box((0.024, 0.018, 0.030)),
            origin=Origin(xyz=(x_pos, 0.001, 0.015)),
            material=steel,
            name=f"hinge_tab_{index}",
        )
    back_pad.visual(
        Box((0.034, 0.32, 0.055)),
        origin=Origin(xyz=(0.0, 0.52, -0.0255)),
        material=steel,
        name="ladder_rail",
    )
    for index, y_pos in enumerate((0.40, 0.48, 0.56, 0.64)):
        back_pad.visual(
            Box((0.056, 0.028, 0.024)),
            origin=Origin(xyz=(0.0, y_pos, -0.065)),
            material=steel,
            name=f"ladder_tooth_{index}",
        )

    seat_pad = model.part("seat_pad")
    seat_pad.visual(
        _mesh(_seat_pad_shape(), "bench_seat_pad"),
        material=pad_vinyl,
        name="seat_cushion",
    )

    rear_support = model.part("rear_support")
    for name, size, xyz in (
        ("support_arm_0", (0.018, 0.33, 0.028), (-0.070, 0.165, 0.0)),
        ("support_arm_1", (0.018, 0.33, 0.028), (0.070, 0.165, 0.0)),
        ("support_bridge", (0.158, 0.028, 0.028), (0.0, 0.340, 0.0)),
        ("support_head", (0.130, 0.052, 0.034), (0.0, 0.290, 0.008)),
    ):
        rear_support.visual(
            Box(size),
            origin=Origin(xyz=xyz),
            material=frame_paint,
            name=name,
        )
    rear_support.visual(
        Box((0.130, 0.032, 0.032)),
        origin=Origin(xyz=(0.0, 0.340, 0.010)),
        material=steel,
        name="support_roller",
    )
    rear_support.visual(
        Cylinder(radius=0.014, length=0.124),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="support_hub",
    )

    for index, x_pos in enumerate((-0.155, 0.155)):
        wheel = model.part(f"transport_wheel_{index}")
        wheel.visual(
            Cylinder(radius=0.036, length=0.028),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=wheel_rubber,
            name="tire",
        )
        wheel.visual(
            Cylinder(radius=0.020, length=0.026),
            origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
            material=steel,
            name="hub",
        )
        model.articulation(
            f"frame_to_transport_wheel_{index}",
            ArticulationType.CONTINUOUS,
            parent=frame,
            child=wheel,
            origin=Origin(xyz=(x_pos, -0.34, 0.080)),
            axis=(1.0, 0.0, 0.0),
            motion_limits=MotionLimits(effort=18.0, velocity=20.0),
        )

    selector_body = model.part("selector_body")
    selector_body.visual(
        Box((0.010, 0.052, 0.012)),
        origin=Origin(xyz=(0.005, 0.0, 0.018)),
        material=frame_paint,
        name="selector_plate",
    )
    selector_body.visual(
        Box((0.010, 0.052, 0.012)),
        origin=Origin(xyz=(0.005, 0.0, -0.018)),
        material=frame_paint,
        name="selector_plate_lower",
    )
    selector_body.visual(
        Box((0.032, 0.018, 0.010)),
        origin=Origin(xyz=(0.026, 0.0, 0.014)),
        material=steel,
        name="selector_guide_top",
    )
    selector_body.visual(
        Box((0.032, 0.018, 0.010)),
        origin=Origin(xyz=(0.026, 0.0, -0.014)),
        material=steel,
        name="selector_guide_bottom",
    )
    selector_body.visual(
        Box((0.012, 0.022, 0.030)),
        origin=Origin(xyz=(0.010, 0.0, 0.0)),
        material=steel,
        name="selector_boss",
    )
    model.articulation(
        "frame_to_selector_body",
        ArticulationType.FIXED,
        parent=frame,
        child=selector_body,
        origin=Origin(xyz=(0.095, 0.10, 0.295)),
    )

    selector_knob = model.part("selector_knob")
    selector_knob.visual(
        Cylinder(radius=0.006, length=0.028),
        origin=Origin(xyz=(0.012, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="selector_shaft",
    )
    selector_knob.visual(
        Cylinder(radius=0.016, length=0.016),
        origin=Origin(xyz=(0.030, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=knob_rubber,
        name="selector_pull",
    )
    selector_knob.visual(
        Cylinder(radius=0.004, length=0.012),
        origin=Origin(xyz=(-0.002, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="selector_tip",
    )
    model.articulation(
        "selector_body_to_selector_knob",
        ArticulationType.PRISMATIC,
        parent=selector_body,
        child=selector_knob,
        origin=Origin(xyz=(0.024, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.10,
            lower=0.0,
            upper=0.018,
        ),
    )

    model.articulation(
        "frame_to_back_pad",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=back_pad,
        origin=Origin(xyz=(0.0, 0.08, 0.410)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=180.0,
            velocity=1.5,
            lower=0.0,
            upper=1.18,
        ),
    )
    model.articulation(
        "frame_to_seat_pad",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=seat_pad,
        origin=Origin(xyz=(0.0, -0.05, 0.398)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=90.0,
            velocity=1.2,
            lower=0.0,
            upper=0.34,
        ),
    )
    model.articulation(
        "frame_to_rear_support",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=rear_support,
        origin=Origin(xyz=(0.0, 0.20, 0.190)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=120.0,
            velocity=1.4,
            lower=0.0,
            upper=1.05,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
