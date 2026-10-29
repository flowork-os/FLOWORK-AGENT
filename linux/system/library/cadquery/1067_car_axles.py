# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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

# ===== brackets_hinges_bezels (2 syms) =====
def _dot(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])

def _norm(v):
    return math.sqrt(_dot(v, v))

# ===== model =====
import math
import cadquery as cq
Point = tuple[float, float, float]
def _v(p: Point) -> cq.Vector:
    return cq.Vector(p[0], p[1], p[2])
def _cyl_between(a: Point, b: Point, radius: float) -> cq.Solid:
    va = _v(a)
    direction = _v((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
    length = direction.Length
    return cq.Solid.makeCylinder(radius, length, va, direction.normalized())
def _box(center: Point, size: Point) -> cq.Solid:
    p = (
        center[0] - size[0] / 2.0,
        center[1] - size[1] / 2.0,
        center[2] - size[2] / 2.0,
    )
    return cq.Solid.makeBox(size[0], size[1], size[2], _v(p))
def _sphere(center: Point, radius: float) -> cq.Solid:
    return cq.Solid.makeSphere(radius, _v(center))
def _union(solids: list[cq.Solid]) -> cq.Workplane:
    body = cq.Workplane("XY").newObject([solids[0]])
    for solid in solids[1:]:
        body = body.union(cq.Workplane("XY").newObject([solid]), clean=False)
    return body
def _wishbone_mesh(side: float, upper: bool) -> cq.Workplane:
    if upper:
        inner_y = 0.155
        outer_x = side * 0.305
        outer_z = -0.030
        tube_r = 0.016
        eye_r = 0.028
        ball_r = 0.030
    else:
        inner_y = 0.205
        outer_x = side * 0.360
        outer_z = 0.020
        tube_r = 0.021
        eye_r = 0.036
        ball_r = 0.038

    front = (0.0, inner_y, 0.0)
    rear = (0.0, -inner_y, 0.0)
    outer = (outer_x, 0.0, outer_z)
    brace = (side * 0.075, 0.0, 0.0)

    solids = [
        _cyl_between(front, outer, tube_r),
        _cyl_between(rear, outer, tube_r),
        _cyl_between(front, rear, tube_r * 0.85),
        _cyl_between(front, brace, tube_r * 0.70),
        _cyl_between(rear, brace, tube_r * 0.70),
        _cyl_between((0.0, inner_y - 0.040, 0.0), (0.0, inner_y + 0.040, 0.0), eye_r),
        _cyl_between((0.0, -inner_y - 0.040, 0.0), (0.0, -inner_y + 0.040, 0.0), eye_r),
        _sphere(outer, ball_r),
        _cyl_between(
            (outer_x - side * 0.020, 0.0, outer_z),
            (outer_x + side * 0.035, 0.0, outer_z),
            ball_r * 0.62,
        ),
    ]
    return _union(solids)
def _knuckle_mesh(side: float) -> cq.Workplane:
    lower = (0.0, 0.0, 0.0)
    upper = (-side * 0.130, 0.0, 0.230)
    hub = (side * 0.075, 0.0, 0.118)
    tab = (side * 0.025, 0.145, 0.105)

    solids = [
        _sphere(lower, 0.050),
        _sphere(upper, 0.044),
        _cyl_between((side * 0.010, 0.0, 0.015), (upper[0], 0.0, upper[2] - 0.010), 0.031),
        _cyl_between((side * 0.015, 0.0, 0.035), (hub[0] - side * 0.015, 0.0, hub[2]), 0.052),
        _cyl_between((hub[0] - side * 0.070, 0.0, hub[2]), (hub[0] + side * 0.020, 0.0, hub[2]), 0.073),
        _cyl_between((hub[0] - side * 0.010, 0.0, hub[2]), (hub[0] + side * 0.125, 0.0, hub[2]), 0.026),
        _box(tab, (0.125, 0.220, 0.030)),
        _cyl_between(
            (tab[0], tab[1] - 0.015, tab[2]),
            (tab[0], tab[1] + 0.095, tab[2]),
            0.026,
        ),
        _cyl_between(
            (tab[0], tab[1] + 0.070, tab[2] - 0.018),
            (tab[0], tab[1] + 0.070, tab[2] + 0.018),
            0.024,
        ),
    ]
    return _union(solids)
def _hub_mesh(side: float) -> cq.Workplane:
    solids: list[cq.Solid] = [
        _cyl_between((-side * 0.040, 0.0, 0.0), (-side * 0.005, 0.0, 0.0), 0.158),
        _cyl_between((-side * 0.020, 0.0, 0.0), (side * 0.030, 0.0, 0.0), 0.113),
        _cyl_between((side * 0.000, 0.0, 0.0), (side * 0.085, 0.0, 0.0), 0.065),
        _cyl_between((side * 0.070, 0.0, 0.0), (side * 0.105, 0.0, 0.0), 0.085),
        _cyl_between((side * 0.102, 0.0, 0.0), (side * 0.122, 0.0, 0.0), 0.036),
    ]
    for i in range(5):
        angle = 2.0 * math.pi * i / 5.0 + math.pi / 2.0
        y = 0.075 * math.cos(angle)
        z = 0.075 * math.sin(angle)
        solids.append(_cyl_between((side * 0.102, y, z), (side * 0.142, y, z), 0.0085))
        solids.append(_cyl_between((side * 0.123, y, z), (side * 0.137, y, z), 0.0140))
    return _union(solids)
def _subframe_mesh() -> cq.Workplane:
    solids: list[cq.Solid] = [
        _cyl_between((-0.470, 0.0, 0.240), (0.470, 0.0, 0.240), 0.044),
        _cyl_between((-0.420, 0.310, 0.025), (0.420, 0.310, 0.025), 0.030),
        _cyl_between((-0.420, -0.310, 0.025), (0.420, -0.310, 0.025), 0.030),
        _cyl_between((-0.315, 0.0, 0.455), (0.315, 0.0, 0.455), 0.030),
    ]

    for side in (-1.0, 1.0):
        x_low = side * 0.320
        x_up = side * 0.250
        solids.extend(
            [
                _cyl_between((side * 0.180, -0.315, 0.025), (side * 0.180, -0.035, 0.455), 0.026),
                _cyl_between((side * 0.180, 0.315, 0.025), (side * 0.180, 0.035, 0.455), 0.026),
                _box((side * 0.180, 0.0, 0.340), (0.045, 0.070, 0.240)),
            ]
        )
        for y in (-0.205, 0.205):
            y_sign = 1.0 if y > 0.0 else -1.0
            solids.extend(
                [
                    _box((x_low - side * 0.055, y, 0.100), (0.014, 0.092, 0.090)),
                    _box((x_low + side * 0.055, y, 0.100), (0.014, 0.092, 0.090)),
                    _box((x_low, y, 0.054), (0.120, 0.095, 0.022)),
                    _box((x_low, y + y_sign * 0.055, 0.054), (0.105, 0.090, 0.020)),
                    _cyl_between((x_low - side * 0.070, y, 0.145), (x_low + side * 0.070, y, 0.145), 0.010),
                ]
            )
        for y in (-0.155, 0.155):
            solids.extend(
                [
                    _box((x_up - side * 0.042, y, 0.380), (0.012, 0.075, 0.070)),
                    _box((x_up + side * 0.042, y, 0.380), (0.012, 0.075, 0.070)),
                    _box((x_up, y, 0.340), (0.095, 0.080, 0.020)),
                    _cyl_between((x_up - side * 0.052, y, 0.414), (x_up + side * 0.052, y, 0.414), 0.008),
                ]
            )
    return _union(solids)
def _norm(p: Point) -> Point:
    length = math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2])
    return (p[0] / length, p[1] / length, p[2] / length)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="independent_front_suspension_axle")

    model.material("powder_coat_black", rgba=(0.015, 0.016, 0.015, 1.0))
    model.material("satin_black_steel", rgba=(0.035, 0.037, 0.035, 1.0))
    model.material("forged_dark_iron", rgba=(0.11, 0.105, 0.095, 1.0))
    model.material("brake_steel", rgba=(0.42, 0.40, 0.37, 1.0))

    subframe = model.part("subframe")
    subframe.visual(
        mesh_from_cadquery(_subframe_mesh(), "subframe_weldment", tolerance=0.004),
        material="powder_coat_black",
        name="subframe_weldment",
    )

    side_data = [
        ("0", 1.0),
        ("1", -1.0),
    ]
    for suffix, side in side_data:
        lower = model.part(f"lower_wishbone_{suffix}")
        lower.visual(
            mesh_from_cadquery(_wishbone_mesh(side, upper=False), f"lower_wishbone_{suffix}", tolerance=0.003),
            material="satin_black_steel",
            name="lower_wishbone_forging",
        )

        upper = model.part(f"upper_wishbone_{suffix}")
        upper.visual(
            mesh_from_cadquery(_wishbone_mesh(side, upper=True), f"upper_wishbone_{suffix}", tolerance=0.003),
            material="satin_black_steel",
            name="upper_wishbone_forging",
        )

        knuckle = model.part(f"knuckle_{suffix}")
        knuckle.visual(
            mesh_from_cadquery(_knuckle_mesh(side), f"knuckle_{suffix}", tolerance=0.003),
            material="forged_dark_iron",
            name="knuckle_forging",
        )

        hub = model.part(f"hub_{suffix}")
        hub.visual(
            mesh_from_cadquery(_hub_mesh(side), f"hub_{suffix}", tolerance=0.0025),
            material="brake_steel",
            name="hub_rotor_lugs",
        )

        model.articulation(
            f"subframe_to_lower_{suffix}",
            ArticulationType.REVOLUTE,
            parent=subframe,
            child=lower,
            origin=Origin(xyz=(side * 0.320, 0.0, 0.100)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=1600.0, velocity=1.5, lower=-0.18, upper=0.18),
        )
        model.articulation(
            f"subframe_to_upper_{suffix}",
            ArticulationType.REVOLUTE,
            parent=subframe,
            child=upper,
            origin=Origin(xyz=(side * 0.250, 0.0, 0.380)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=900.0, velocity=1.5, lower=-0.15, upper=0.15),
        )

        steering_axis = _norm((-side * 0.130, 0.0, 0.230))
        model.articulation(
            f"lower_to_knuckle_{suffix}",
            ArticulationType.REVOLUTE,
            parent=lower,
            child=knuckle,
            origin=Origin(xyz=(side * 0.360, 0.0, 0.020)),
            axis=steering_axis,
            motion_limits=MotionLimits(effort=450.0, velocity=2.0, lower=-0.55, upper=0.55),
        )
        model.articulation(
            f"knuckle_to_hub_{suffix}",
            ArticulationType.CONTINUOUS,
            parent=knuckle,
            child=hub,
            origin=Origin(xyz=(side * 0.075, 0.0, 0.118)),
            axis=(side, 0.0, 0.0),
            motion_limits=MotionLimits(effort=300.0, velocity=25.0),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
