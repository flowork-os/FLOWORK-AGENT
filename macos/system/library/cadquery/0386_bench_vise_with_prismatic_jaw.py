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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
import cadquery as cq
from math import pi
BASE_FOOT_X = 0.260
BASE_FOOT_Y = 0.180
BASE_FOOT_Z = 0.014
BASE_PEDESTAL_X = 0.220
BASE_PEDESTAL_Y = 0.128
BASE_PEDESTAL_Z = 0.016
BASE_RAIL_X = 0.205
BASE_RAIL_Y = 0.024
BASE_RAIL_H = 0.014
BASE_RAIL_OFFSET_Y = 0.034
BASE_SEAT_Z = BASE_FOOT_Z + BASE_PEDESTAL_Z + BASE_RAIL_H
X_SLIDE_X = 0.180
X_SLIDE_Y = 0.115
X_SLIDE_Z = 0.024
X_TOP_RAIL_X = 0.020
X_TOP_RAIL_Y = 0.105
X_TOP_RAIL_H = 0.010
X_TOP_RAIL_OFFSET_X = 0.030
X_TOP_SEAT_Z = X_SLIDE_Z + X_TOP_RAIL_H
X_TRAVEL = 0.040
Y_SLIDE_X = 0.145
Y_SLIDE_Y = 0.100
Y_SLIDE_Z = 0.020
Y_BED_Y = 0.072
Y_BED_Z = 0.014
JAW_X = 0.124
JAW_Y = 0.012
JAW_Z = 0.028
JAW_FACE_T = 0.003
Y_TRAVEL = 0.035
X_HOUSING_R = 0.011
X_HOUSING_L = 0.028
X_HOUSING_Z = 0.030
Y_HOUSING_R = 0.010
Y_HOUSING_L = 0.026
Y_HOUSING_Z = 0.021
def _base_casting_shape():
    foot = cq.Workplane("XY").box(BASE_FOOT_X, BASE_FOOT_Y, BASE_FOOT_Z).translate((0.0, 0.0, BASE_FOOT_Z / 2.0))
    pedestal = (
        cq.Workplane("XY")
        .box(BASE_PEDESTAL_X, BASE_PEDESTAL_Y, BASE_PEDESTAL_Z)
        .translate((0.0, 0.0, BASE_FOOT_Z + BASE_PEDESTAL_Z / 2.0))
    )
    rail_z = BASE_FOOT_Z + BASE_PEDESTAL_Z + BASE_RAIL_H / 2.0
    left_rail = cq.Workplane("XY").box(BASE_RAIL_X, BASE_RAIL_Y, BASE_RAIL_H).translate((0.0, BASE_RAIL_OFFSET_Y, rail_z))
    right_rail = cq.Workplane("XY").box(BASE_RAIL_X, BASE_RAIL_Y, BASE_RAIL_H).translate((0.0, -BASE_RAIL_OFFSET_Y, rail_z))
    front_apron = (
        cq.Workplane("XY")
        .box(BASE_PEDESTAL_X * 0.90, 0.022, BASE_PEDESTAL_Z * 1.15)
        .translate((0.0, -(BASE_PEDESTAL_Y / 2.0 + 0.011), BASE_FOOT_Z + BASE_PEDESTAL_Z * 0.575))
    )
    rear_rib = (
        cq.Workplane("XY")
        .box(BASE_PEDESTAL_X * 0.84, 0.016, BASE_PEDESTAL_Z * 0.95)
        .translate((0.0, BASE_PEDESTAL_Y / 2.0 + 0.008, BASE_FOOT_Z + BASE_PEDESTAL_Z * 0.475))
    )
    cheek_left = (
        cq.Workplane("XY")
        .box(0.030, BASE_PEDESTAL_Y * 0.88, BASE_PEDESTAL_Z * 0.95)
        .translate((BASE_PEDESTAL_X / 2.0 - 0.015, 0.0, BASE_FOOT_Z + BASE_PEDESTAL_Z * 0.475))
    )
    cheek_right = (
        cq.Workplane("XY")
        .box(0.030, BASE_PEDESTAL_Y * 0.88, BASE_PEDESTAL_Z * 0.95)
        .translate((-(BASE_PEDESTAL_X / 2.0 - 0.015), 0.0, BASE_FOOT_Z + BASE_PEDESTAL_Z * 0.475))
    )
    return foot.union(pedestal).union(left_rail).union(right_rail).union(front_apron).union(rear_rib).union(cheek_left).union(cheek_right)
def _x_slide_shape():
    carriage = cq.Workplane("XY").box(X_SLIDE_X, X_SLIDE_Y, X_SLIDE_Z).translate((0.0, 0.0, X_SLIDE_Z / 2.0))
    left_rail = (
        cq.Workplane("XY")
        .box(X_TOP_RAIL_X, X_TOP_RAIL_Y, X_TOP_RAIL_H)
        .translate((X_TOP_RAIL_OFFSET_X, 0.0, X_SLIDE_Z + X_TOP_RAIL_H / 2.0))
    )
    right_rail = (
        cq.Workplane("XY")
        .box(X_TOP_RAIL_X, X_TOP_RAIL_Y, X_TOP_RAIL_H)
        .translate((-X_TOP_RAIL_OFFSET_X, 0.0, X_SLIDE_Z + X_TOP_RAIL_H / 2.0))
    )
    front_apron = (
        cq.Workplane("XY")
        .box(X_SLIDE_X * 0.88, 0.020, 0.018)
        .translate((0.0, -(X_SLIDE_Y / 2.0 + 0.010), 0.009))
    )
    rear_lip = (
        cq.Workplane("XY")
        .box(X_SLIDE_X * 0.72, 0.012, 0.010)
        .translate((0.0, X_SLIDE_Y / 2.0 + 0.006, 0.017))
    )
    return carriage.union(left_rail).union(right_rail).union(front_apron).union(rear_lip)
def _y_slide_shape():
    table = cq.Workplane("XY").box(Y_SLIDE_X, Y_SLIDE_Y, Y_SLIDE_Z).translate((0.0, 0.0, Y_SLIDE_Z / 2.0))
    vise_bed = cq.Workplane("XY").box(Y_SLIDE_X, Y_BED_Y, Y_BED_Z).translate((0.0, 0.0, Y_SLIDE_Z + Y_BED_Z / 2.0))
    jaw_z = Y_SLIDE_Z + Y_BED_Z + JAW_Z / 2.0
    fixed_jaw = cq.Workplane("XY").box(JAW_X, JAW_Y, JAW_Z).translate((0.0, 0.030, jaw_z))
    movable_jaw = cq.Workplane("XY").box(JAW_X, JAW_Y, JAW_Z).translate((0.0, -0.012, jaw_z))
    screw_cover = (
        cq.Workplane("XY")
        .box(0.020, 0.038, 0.012)
        .translate((0.0, 0.009, Y_SLIDE_Z + Y_BED_Z + 0.006))
    )
    return table.union(vise_bed).union(fixed_jaw).union(movable_jaw).union(screw_cover)
def _steel_jaw_face(y_center: float) -> Origin:
    return Origin(xyz=(0.0, y_center, Y_SLIDE_Z + Y_BED_Z + JAW_Z / 2.0))
def _handwheel_shape():
    shaft_len = 0.016
    shaft_r = 0.0045
    hub_r = 0.010
    hub_len = 0.010
    rim_outer = 0.028
    rim_inner = 0.023
    rim_thickness = 0.004
    wheel_z = shaft_len + 0.004

    shaft = cq.Workplane("XY").circle(shaft_r).extrude(shaft_len)
    hub = cq.Workplane("XY").circle(hub_r).extrude(shaft_len + hub_len)
    rim = (
        cq.Workplane("XY")
        .workplane(offset=wheel_z - rim_thickness / 2.0)
        .circle(rim_outer)
        .circle(rim_inner)
        .extrude(rim_thickness)
    )

    body = shaft.union(hub).union(rim)
    spoke = cq.Workplane("XY").box(0.022, 0.004, rim_thickness).translate((0.015, 0.0, wheel_z))
    for angle_deg in (0.0, 120.0, 240.0):
        body = body.union(spoke.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))

    crank_arm = cq.Workplane("XY").box(0.014, 0.005, 0.006).translate((0.022, 0.0, wheel_z + 0.003))
    grip = cq.Workplane("XY").workplane(offset=wheel_z + 0.006).center(0.022, 0.0).circle(0.0048).extrude(0.018)
    return body.union(crank_arm).union(grip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cross_slide_vise")

    cast_iron = model.material("cast_iron", rgba=(0.24, 0.26, 0.29, 1.0))
    machined_steel = model.material("machined_steel", rgba=(0.72, 0.74, 0.77, 1.0))
    handwheel_black = model.material("handwheel_black", rgba=(0.10, 0.10, 0.11, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.34, 0.36, 0.39, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_casting_shape(), "base_casting"),
        material=cast_iron,
        name="base_casting",
    )
    base.visual(
        Box((0.032, 0.030, 0.018)),
        origin=Origin(xyz=(0.0, -0.089, X_HOUSING_Z)),
        material=dark_steel,
        name="x_nut_block",
    )
    base.visual(
        Cylinder(radius=X_HOUSING_R, length=X_HOUSING_L),
        origin=Origin(
            xyz=(0.0, -(BASE_FOOT_Y / 2.0 + X_HOUSING_L / 2.0) + 0.002, X_HOUSING_Z),
            rpy=(pi / 2.0, 0.0, 0.0),
        ),
        material=machined_steel,
        name="x_screw_housing",
    )

    x_slide = model.part("x_slide")
    x_slide.visual(
        mesh_from_cadquery(_x_slide_shape(), "x_carriage"),
        material=cast_iron,
        name="x_carriage",
    )
    x_slide.visual(
        Cylinder(radius=Y_HOUSING_R, length=Y_HOUSING_L),
        origin=Origin(xyz=(X_SLIDE_X / 2.0 + Y_HOUSING_L / 2.0, 0.0, Y_HOUSING_Z), rpy=(0.0, pi / 2.0, 0.0)),
        material=machined_steel,
        name="y_screw_housing",
    )

    y_slide = model.part("y_slide")
    y_slide.visual(
        mesh_from_cadquery(_y_slide_shape(), "y_table"),
        material=cast_iron,
        name="y_table",
    )
    y_slide.visual(
        Box((JAW_X * 0.96, JAW_FACE_T, JAW_Z * 0.84)),
        origin=_steel_jaw_face(0.0245),
        material=machined_steel,
        name="fixed_jaw_face",
    )
    y_slide.visual(
        Box((JAW_X * 0.96, JAW_FACE_T, JAW_Z * 0.84)),
        origin=_steel_jaw_face(-0.0055),
        material=machined_steel,
        name="movable_jaw_face",
    )

    x_handle = model.part("x_handle")
    x_handle.visual(
        mesh_from_cadquery(_handwheel_shape(), "x_handwheel"),
        origin=Origin(rpy=(pi / 2.0, 0.0, 0.0)),
        material=handwheel_black,
        name="x_handwheel",
    )

    y_handle = model.part("y_handle")
    y_handle.visual(
        mesh_from_cadquery(_handwheel_shape(), "y_handwheel"),
        origin=Origin(rpy=(0.0, pi / 2.0, 0.0)),
        material=handwheel_black,
        name="y_handwheel",
    )

    model.articulation(
        "base_to_x_slide",
        ArticulationType.PRISMATIC,
        parent=base,
        child=x_slide,
        origin=Origin(xyz=(0.0, 0.0, BASE_SEAT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=850.0, velocity=0.08, lower=-X_TRAVEL, upper=X_TRAVEL),
    )
    model.articulation(
        "x_slide_to_y_slide",
        ArticulationType.PRISMATIC,
        parent=x_slide,
        child=y_slide,
        origin=Origin(xyz=(0.0, 0.0, X_TOP_SEAT_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=850.0, velocity=0.08, lower=-Y_TRAVEL, upper=Y_TRAVEL),
    )
    model.articulation(
        "base_to_x_handle",
        ArticulationType.CONTINUOUS,
        parent=base,
        child=x_handle,
        origin=Origin(xyz=(0.0, -(BASE_FOOT_Y / 2.0 + X_HOUSING_L) + 0.002, X_HOUSING_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=40.0, velocity=10.0),
    )
    model.articulation(
        "x_slide_to_y_handle",
        ArticulationType.CONTINUOUS,
        parent=x_slide,
        child=y_handle,
        origin=Origin(xyz=(X_SLIDE_X / 2.0 + Y_HOUSING_L, 0.0, Y_HOUSING_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=40.0, velocity=10.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
