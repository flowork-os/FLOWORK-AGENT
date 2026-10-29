# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_fork_and_handlebar_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_fork_and_handlebar_assembly

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
def _hollow_tube_z(outer_radius: float, inner_radius: float, length: float):
    """CadQuery annular tube centered on local Z."""
    outer = cq.Workplane("XY").circle(outer_radius).extrude(length)
    cutter = cq.Workplane("XY").circle(inner_radius).extrude(length + 0.010).translate(
        (0.0, 0.0, -0.005)
    )
    return outer.cut(cutter).translate((0.0, 0.0, -0.5 * length))
def _hollow_tube_y(outer_radius: float, inner_radius: float, length: float):
    """CadQuery annular tube centered on local Y."""
    return _hollow_tube_z(outer_radius, inner_radius, length).rotate(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0
    )
def _stem_body():
    """One connected forged stem with real through holes for steerer and bar."""
    steerer_collar = _hollow_tube_z(0.033, 0.0175, 0.060)
    bar_clamp = _hollow_tube_y(0.030, 0.0140, 0.064).translate((0.130, 0.0, 0.0))
    extension = cq.Workplane("XY").box(0.092, 0.034, 0.022).translate((0.068, 0.0, 0.0))
    top_web = cq.Workplane("XY").box(0.070, 0.024, 0.014).translate((0.070, 0.0, 0.018))
    return steerer_collar.union(extension).union(top_web).union(bar_clamp)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="xc_suspension_fork")

    matte_carbon = model.material("matte_carbon", rgba=(0.05, 0.055, 0.06, 1.0))
    anodized_black = model.material("anodized_black", rgba=(0.01, 0.012, 0.014, 1.0))
    satin_graphite = model.material("satin_graphite", rgba=(0.16, 0.17, 0.18, 1.0))
    polished_alloy = model.material("polished_alloy", rgba=(0.72, 0.74, 0.72, 1.0))
    dark_rubber = model.material("dark_rubber", rgba=(0.015, 0.014, 0.013, 1.0))
    laser_mark = model.material("laser_mark", rgba=(0.60, 0.74, 0.78, 1.0))

    upper_fork = model.part("upper_fork")
    upper_fork.visual(
        Box((0.105, 0.345, 0.055)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=satin_graphite,
        name="crown_bridge",
    )
    upper_fork.visual(
        Box((0.012, 0.260, 0.003)),
        origin=Origin(xyz=(0.054, 0.0, 0.012)),
        material=laser_mark,
        name="crown_front_stripe",
    )
    upper_fork.visual(
        Cylinder(radius=0.018, length=0.370),
        origin=Origin(xyz=(0.0, 0.0, 0.187)),
        material=matte_carbon,
        name="round_steerer",
    )

    sleeve_mesh = mesh_from_cadquery(_hollow_tube_z(0.034, 0.0235, 0.300), "upper_leg_sleeve")
    seal_mesh = mesh_from_cadquery(_hollow_tube_z(0.037, 0.0215, 0.018), "black_dust_seal")
    for index, y in enumerate((-0.130, 0.130)):
        upper_fork.visual(
            sleeve_mesh,
            origin=Origin(xyz=(0.0, y, -0.170)),
            material=satin_graphite,
            name=f"upper_sleeve_{index}",
        )
        upper_fork.visual(
            seal_mesh,
            origin=Origin(xyz=(0.0, y, -0.311)),
            material=dark_rubber,
            name=f"dust_seal_{index}",
        )

    # Two separate sliding lower stanchions: the suffixes avoid inventing a
    # left/right convention for this front-facing, nearly symmetric fork.
    for index, y in enumerate((-0.130, 0.130)):
        side = -1.0 if y < 0.0 else 1.0
        lower = model.part(f"lower_stanchion_{index}")
        lower.visual(
            Cylinder(radius=0.020, length=0.440),
            origin=Origin(xyz=(0.0, 0.0, -0.140)),
            material=polished_alloy,
            name="slider_tube",
        )
        lower.visual(
            Cylinder(radius=0.024, length=0.028),
            origin=Origin(xyz=(0.0, 0.0, 0.064)),
            material=dark_rubber,
            name="upper_bushing_band",
        )
        lower.visual(
            Box((0.040, 0.030, 0.058)),
            origin=Origin(xyz=(0.0, side * 0.022, -0.385)),
            material=anodized_black,
            name="dropout_tab",
        )
        lower.visual(
            Cylinder(radius=0.016, length=0.045),
            origin=Origin(xyz=(0.0, side * 0.040, -0.393), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=anodized_black,
            name="axle_boss",
        )
        model.articulation(
            f"sleeve_to_lower_{index}",
            ArticulationType.PRISMATIC,
            parent=upper_fork,
            child=lower,
            origin=Origin(xyz=(0.0, y, -0.320)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=85.0, velocity=0.35, lower=0.0, upper=0.100),
        )

    stem = model.part("stem")
    stem.visual(
        mesh_from_cadquery(_stem_body(), "short_xc_stem"),
        origin=Origin(),
        material=anodized_black,
        name="stem_body",
    )
    stem.visual(
        Box((0.010, 0.050, 0.006)),
        origin=Origin(xyz=(-0.031, 0.0, 0.020)),
        material=polished_alloy,
        name="steerer_clamp_slot",
    )
    stem.visual(
        Cylinder(radius=0.004, length=0.050),
        origin=Origin(xyz=(-0.034, 0.0, 0.010), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished_alloy,
        name="steerer_clamp_bolt",
    )
    stem.visual(
        Box((0.010, 0.052, 0.006)),
        origin=Origin(xyz=(0.156, 0.0, 0.0)),
        material=polished_alloy,
        name="bar_clamp_faceplate",
    )
    model.articulation(
        "steerer_to_stem",
        ArticulationType.REVOLUTE,
        parent=upper_fork,
        child=stem,
        origin=Origin(xyz=(0.0, 0.0, 0.372)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=2.0, lower=-0.65, upper=0.65),
    )

    handlebar = model.part("handlebar")
    handlebar.visual(
        Cylinder(radius=0.0105, length=0.760),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=matte_carbon,
        name="flat_bar",
    )
    handlebar.visual(
        Box((0.006, 0.560, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=laser_mark,
        name="top_index_ridge",
    )
    handlebar.visual(
        Cylinder(radius=0.016, length=0.130),
        origin=Origin(xyz=(0.0, -0.315, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_rubber,
        name="grip_0",
    )
    handlebar.visual(
        Cylinder(radius=0.016, length=0.130),
        origin=Origin(xyz=(0.0, 0.315, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_rubber,
        name="grip_1",
    )
    handlebar.visual(
        Cylinder(radius=0.0145, length=0.070),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished_alloy,
        name="center_clamp_zone",
    )
    model.articulation(
        "stem_to_handlebar",
        ArticulationType.REVOLUTE,
        parent=stem,
        child=handlebar,
        origin=Origin(xyz=(0.130, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=2.0, lower=-0.55, upper=0.55),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
