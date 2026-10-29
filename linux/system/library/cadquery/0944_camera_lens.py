# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
LENS_LENGTH = 0.240
FRONT_BORE_RADIUS = 0.031
FRONT_RECESS_RADIUS = 0.034
FOCUS_RING_CENTER_X = 0.163
FOCUS_RING_LENGTH = 0.070
IRIS_RING_CENTER_X = 0.040
IRIS_RING_LENGTH = 0.032
MARKER_SLOT_CENTER_X = 0.218
MARKER_SLOT_CENTER_Y = 0.039
MARKER_SLOT_LENGTH = 0.024
def _cylinder_segment(x0: float, x1: float, radius: float) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(x1 - x0).translate((x0, 0.0, 0.0))
def _union_all(shapes: list[cq.Workplane]) -> cq.Workplane:
    body = shapes[0]
    for shape in shapes[1:]:
        body = body.union(shape)
    return body
def _build_housing_shape() -> cq.Workplane:
    outer_segments = [
        _cylinder_segment(0.000, 0.018, 0.034),
        _cylinder_segment(0.018, 0.024, 0.0405),
        _cylinder_segment(0.024, 0.056, 0.0385),
        _cylinder_segment(0.056, 0.060, 0.0405),
        _cylinder_segment(0.060, 0.122, 0.040),
        _cylinder_segment(0.122, 0.128, 0.043),
        _cylinder_segment(0.128, 0.198, 0.041),
        _cylinder_segment(0.198, 0.204, 0.043),
        _cylinder_segment(0.204, 0.229, 0.046),
        _cylinder_segment(0.229, 0.240, 0.050),
    ]
    housing = _union_all(outer_segments)

    main_bore = cq.Workplane("YZ").circle(FRONT_BORE_RADIUS).extrude(LENS_LENGTH)
    front_recess = (
        cq.Workplane("YZ")
        .circle(FRONT_RECESS_RADIUS)
        .extrude(0.030)
        .translate((0.210, 0.0, 0.0))
    )
    slot_cut = (
        cq.Workplane("XY")
        .box(MARKER_SLOT_LENGTH, 0.024, 0.011)
        .translate((MARKER_SLOT_CENTER_X, MARKER_SLOT_CENTER_Y, 0.0))
    )

    return housing.cut(main_bore).cut(front_recess).cut(slot_cut)
def _build_geared_ring_shape(
    *,
    length: float,
    inner_radius: float,
    base_outer_radius: float,
    tooth_depth: float,
    tooth_count: int,
    smooth_patch_center_deg: float | None = None,
    smooth_patch_width_deg: float = 0.0,
) -> cq.Workplane:
    outer = (
        cq.Workplane("YZ")
        .circle(base_outer_radius)
        .extrude(length)
        .translate((-length * 0.5, 0.0, 0.0))
    )
    inner = (
        cq.Workplane("YZ")
        .circle(inner_radius)
        .extrude(length)
        .translate((-length * 0.5, 0.0, 0.0))
    )
    ring = outer.cut(inner)

    tooth_pitch = 360.0 / tooth_count
    tooth_width = (2.0 * math.pi * base_outer_radius / tooth_count) * 0.55
    patch_half_width = smooth_patch_width_deg * 0.5

    for idx in range(tooth_count):
        angle_deg = idx * tooth_pitch
        if smooth_patch_center_deg is not None:
            delta = ((angle_deg - smooth_patch_center_deg + 180.0) % 360.0) - 180.0
            if abs(delta) <= patch_half_width:
                continue

        tooth = (
            cq.Workplane("XY")
            .box(length, tooth_depth, tooth_width)
            .translate((0.0, base_outer_radius + tooth_depth * 0.5, 0.0))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
        )
        ring = ring.union(tooth)

    return ring
def _build_marker_tab_shape() -> cq.Workplane:
    cap = cq.Workplane("XY").box(0.010, 0.010, 0.009).translate((0.0, 0.010, 0.0))
    neck = cq.Workplane("XY").box(0.010, 0.024, 0.011).translate((0.0, 0.0, 0.0))
    shoe = cq.Workplane("XY").box(0.016, 0.008, 0.012).translate((0.0, -0.015, 0.0))
    return cap.union(neck).union(shoe)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="macro_cinema_lens")

    anodized_black = model.material("anodized_black", rgba=(0.12, 0.12, 0.13, 1.0))
    grip_black = model.material("grip_black", rgba=(0.08, 0.08, 0.08, 1.0))
    marker_cream = model.material("marker_cream", rgba=(0.85, 0.82, 0.72, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_build_housing_shape(), "housing_shell"),
        material=anodized_black,
        name="housing_shell",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(
            _build_geared_ring_shape(
                length=FOCUS_RING_LENGTH,
                inner_radius=0.0418,
                base_outer_radius=0.0465,
                tooth_depth=0.0032,
                tooth_count=40,
                smooth_patch_center_deg=90.0,
                smooth_patch_width_deg=22.0,
            ),
            "focus_ring_band",
        ),
        material=grip_black,
        name="focus_band",
    )

    iris_ring = model.part("iris_ring")
    iris_ring.visual(
        mesh_from_cadquery(
            _build_geared_ring_shape(
                length=IRIS_RING_LENGTH,
                inner_radius=0.0392,
                base_outer_radius=0.0425,
                tooth_depth=0.0023,
                tooth_count=28,
                smooth_patch_center_deg=88.0,
                smooth_patch_width_deg=16.0,
            ),
            "iris_ring_band",
        ),
        material=grip_black,
        name="iris_band",
    )

    marker_tab = model.part("marker_tab")
    marker_tab.visual(
        mesh_from_cadquery(_build_marker_tab_shape(), "marker_tab"),
        material=marker_cream,
        name="marker_body",
    )

    model.articulation(
        "focus_rotation",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=focus_ring,
        origin=Origin(xyz=(FOCUS_RING_CENTER_X, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.5, velocity=8.0),
    )
    model.articulation(
        "iris_rotation",
        ArticulationType.CONTINUOUS,
        parent=housing,
        child=iris_ring,
        origin=Origin(xyz=(IRIS_RING_CENTER_X, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.5, velocity=8.0),
    )
    model.articulation(
        "marker_slide",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=marker_tab,
        origin=Origin(xyz=(MARKER_SLOT_CENTER_X, MARKER_SLOT_CENTER_Y, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.8, velocity=0.03, lower=-0.006, upper=0.006),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
