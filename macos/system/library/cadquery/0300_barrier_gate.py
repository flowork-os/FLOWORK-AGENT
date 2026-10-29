# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, barrier_gate, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: barrier_gate

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
POST_TRAVEL = 0.82
SKIRT_UP_ANGLE = math.pi / 2.0
def _annular_disc(
    *,
    inner_radius: float,
    outer_radius: float,
    thickness: float,
    center_x: float = 0.0,
    center_z: float = 0.0,
):
    """A flat annular solid in the local XY plane."""
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(thickness)
        .translate((center_x, 0.0, center_z - thickness / 2.0))
    )
def _housing_sleeve_geometry():
    """Underground cylindrical sleeve plus flush annular rim flange."""
    sleeve = (
        cq.Workplane("XY")
        .circle(0.220)
        .circle(0.132)
        .extrude(1.10)
        .translate((0.0, 0.0, -1.10))
    )
    rim = (
        cq.Workplane("XY")
        .circle(0.360)
        .circle(0.132)
        .extrude(0.055)
        .translate((0.0, 0.0, -0.055))
    )
    return sleeve.union(rim)
def _ground_pad_geometry():
    pad = cq.Workplane("XY").box(1.10, 1.10, 0.080).translate((0.0, 0.0, -0.040))
    cutter = cq.Workplane("XY").circle(0.358).extrude(0.120).translate((0.0, 0.0, -0.090))
    return pad.cut(cutter)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="rising_bollard_barrier")

    brushed_steel = model.material("brushed_steel", rgba=(0.62, 0.64, 0.62, 1.0))
    dark_steel = model.material("dark_steel", rgba=(0.08, 0.085, 0.09, 1.0))
    asphalt = model.material("dark_asphalt", rgba=(0.10, 0.095, 0.085, 1.0))
    rubber = model.material("black_rubber", rgba=(0.01, 0.01, 0.009, 1.0))
    safety_yellow = model.material("safety_yellow", rgba=(1.0, 0.72, 0.04, 1.0))
    reflector_red = model.material("red_reflector", rgba=(0.95, 0.05, 0.025, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_ground_pad_geometry(), "ground_pad", tolerance=0.0015),
        material=asphalt,
        name="ground_pad",
    )
    housing.visual(
        mesh_from_cadquery(_housing_sleeve_geometry(), "rim_and_guide_sleeve", tolerance=0.001),
        material=brushed_steel,
        name="rim_flange",
    )
    housing.visual(
        mesh_from_cadquery(
            _annular_disc(inner_radius=0.132, outer_radius=0.164, thickness=0.012, center_z=0.006),
            "wiper_seal",
            tolerance=0.001,
        ),
        material=rubber,
        name="wiper_seal",
    )
    for index in range(8):
        if index == 4:
            # The rim-side hinge occupies this bolt station on the real flange.
            continue
        angle = index * math.tau / 8.0
        housing.visual(
            Cylinder(radius=0.014, length=0.010),
            origin=Origin(xyz=(0.290 * math.cos(angle), 0.290 * math.sin(angle), 0.005)),
            material=dark_steel,
            name=f"rim_bolt_{index}",
        )

    # Two fixed hinge leaves and alternating knuckles sit on the rim-side bracket.
    for y in (-0.125, 0.125):
        housing.visual(
            Box((0.070, 0.075, 0.020)),
            origin=Origin(xyz=(-0.350, y, 0.009)),
            material=dark_steel,
            name=f"fixed_leaf_{'neg' if y < 0 else 'pos'}",
        )
        housing.visual(
            Cylinder(radius=0.018, length=0.070),
            origin=Origin(xyz=(-0.310, y, 0.035), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=dark_steel,
            name=f"fixed_knuckle_{'neg' if y < 0 else 'pos'}",
        )
    for axis_name, sx, sy, x, y in (
        ("x_pos", 0.027, 0.050, 0.1185, 0.0),
        ("x_neg", 0.027, 0.050, -0.1185, 0.0),
        ("y_pos", 0.050, 0.027, 0.0, 0.1185),
        ("y_neg", 0.050, 0.027, 0.0, -0.1185),
    ):
        housing.visual(
            Box((sx, sy, 0.100)),
            origin=Origin(xyz=(x, y, -0.180)),
            material=rubber,
            name=f"guide_pad_{axis_name}",
        )

    post = model.part("steel_post")
    post.visual(
        Cylinder(radius=0.105, length=1.080),
        origin=Origin(xyz=(0.0, 0.0, -0.520)),
        material=brushed_steel,
        name="main_post",
    )
    post.visual(
        Cylinder(radius=0.118, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material=brushed_steel,
        name="top_cap",
    )
    post.visual(
        Cylinder(radius=0.122, length=0.080),
        origin=Origin(xyz=(0.0, 0.0, -1.035)),
        material=dark_steel,
        name="guide_shoe",
    )
    for z, mat, band_name in (
        (-0.145, safety_yellow, "upper_band"),
        (-0.310, reflector_red, "lower_band"),
    ):
        post.visual(
            Cylinder(radius=0.108, length=0.070),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=mat,
            name=band_name,
        )

    skirt = model.part("skirt_ring")
    skirt.visual(
        mesh_from_cadquery(
            _annular_disc(
                inner_radius=0.175,
                outer_radius=0.310,
                thickness=0.012,
                center_x=0.310,
                center_z=-0.023,
            ),
            "skirt_ring_plate",
            tolerance=0.001,
        ),
        material=safety_yellow,
        name="ring_plate",
    )
    skirt.visual(
        Box((0.070, 0.105, 0.024)),
        origin=Origin(xyz=(0.045, 0.0, -0.021)),
        material=dark_steel,
        name="moving_leaf",
    )
    skirt.visual(
        Cylinder(radius=0.018, length=0.110),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="moving_knuckle",
    )

    model.articulation(
        "housing_to_post",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=post,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2500.0, velocity=0.35, lower=0.0, upper=POST_TRAVEL),
    )

    model.articulation(
        "housing_to_skirt",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=skirt,
        origin=Origin(xyz=(-0.310, 0.0, 0.035)),
        # Positive revolute motion raises the ring from its flat pose.
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=1.2, lower=0.0, upper=SKIRT_UP_ANGLE),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
