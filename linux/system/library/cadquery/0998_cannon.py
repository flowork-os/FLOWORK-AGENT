# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cannon, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cannon

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
def _x_cylinder(radius: float, length: float, center_x: float = 0.0) -> cq.Workplane:
    """CadQuery cylinder whose axis is the model X axis."""

    return cq.Workplane("YZ").cylinder(length, radius).translate((center_x, 0.0, 0.0))
def _bombard_barrel_mesh() -> cq.Workplane:
    """Short, wide, hollow cast-iron bombard barrel with stepped reinforces."""

    barrel = _x_cylinder(0.235, 1.05, 0.02)
    barrel = barrel.union(_x_cylinder(0.300, 0.18, 0.52))  # flared muzzle swell
    barrel = barrel.union(_x_cylinder(0.280, 0.24, -0.46))  # heavy closed breech
    barrel = barrel.union(_x_cylinder(0.258, 0.16, -0.06))  # trunnion reinforce band
    barrel = barrel.union(_x_cylinder(0.252, 0.055, 0.29))
    barrel = barrel.union(_x_cylinder(0.252, 0.050, -0.25))

    # Blind bore: open at the muzzle, terminating in a dark recessed chamber wall.
    bore = _x_cylinder(0.150, 1.16, 0.14)
    return barrel.cut(bore)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="medieval_bombard")

    wood = model.material("aged_oak", rgba=(0.42, 0.25, 0.12, 1.0))
    wood_dark = model.material("dark_endgrain", rgba=(0.25, 0.13, 0.055, 1.0))
    iron = model.material("blackened_cast_iron", rgba=(0.025, 0.028, 0.030, 1.0))
    iron_edge = model.material("worn_iron_edges", rgba=(0.12, 0.115, 0.105, 1.0))
    bore_black = model.material("sooty_bore", rgba=(0.002, 0.002, 0.002, 1.0))

    cradle = model.part("cradle")
    cradle.visual(
        Box((1.70, 0.74, 0.10)),
        origin=Origin(xyz=(-0.06, 0.0, 0.05)),
        material=wood,
        name="bed_plank",
    )
    cradle.visual(
        Box((1.82, 0.13, 0.16)),
        origin=Origin(xyz=(-0.04, 0.255, 0.095)),
        material=wood_dark,
        name="side_runner_0",
    )
    cradle.visual(
        Box((1.82, 0.13, 0.16)),
        origin=Origin(xyz=(-0.04, -0.255, 0.095)),
        material=wood_dark,
        name="side_runner_1",
    )
    for i, x in enumerate((-0.62, 0.48)):
        cradle.visual(
            Box((0.18, 0.82, 0.11)),
            origin=Origin(xyz=(x, 0.0, 0.110)),
            material=wood,
            name=f"cross_tie_{i}",
        )
    cradle.visual(
        Box((0.62, 0.24, 0.070)),
        origin=Origin(xyz=(0.11, 0.0, 0.130)),
        material=wood,
        name="barrel_saddle",
    )

    for idx, y in enumerate((0.345, -0.345)):
        cradle.visual(
            Box((0.66, 0.105, 0.24)),
            origin=Origin(xyz=(-0.05, y, 0.235)),
            material=wood,
            name=f"cheek_bed_{idx}",
        )
        cradle.visual(
            Box((0.13, 0.105, 0.52)),
            origin=Origin(xyz=(-0.325, y, 0.37)),
            material=wood,
            name=f"rear_cheek_{idx}",
        )
        cradle.visual(
            Box((0.13, 0.105, 0.52)),
            origin=Origin(xyz=(0.255, y, 0.37)),
            material=wood,
            name=f"front_cheek_{idx}",
        )
        cradle.visual(
            Box((0.68, 0.105, 0.09)),
            origin=Origin(xyz=(-0.035, y, 0.61)),
            material=wood_dark,
            name=f"cheek_cap_{idx}",
        )

        collar_y = 0.286 if y > 0 else -0.286
        cradle.visual(
            Cylinder(radius=0.128, length=0.046),
            origin=Origin(xyz=(0.0, collar_y, 0.48), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=iron_edge,
            name=f"pivot_collar_{idx}",
        )

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_bombard_barrel_mesh(), "bombard_barrel"),
        material=iron,
        name="barrel_shell",
    )
    barrel.visual(
        Cylinder(radius=0.075, length=0.82),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=iron_edge,
        name="trunnion_bar",
    )
    barrel.visual(
        Cylinder(radius=0.154, length=0.016),
        origin=Origin(xyz=(-0.432, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=bore_black,
        name="bore_shadow",
    )
    barrel.visual(
        Cylinder(radius=0.020, length=0.006),
        origin=Origin(xyz=(-0.340, 0.0, 0.282)),
        material=bore_black,
        name="touch_hole",
    )
    for idx, y in enumerate((0.106, -0.106)):
        barrel.visual(
            Box((0.036, 0.028, 0.068)),
            origin=Origin(xyz=(-0.430, y, 0.256)),
            material=iron_edge,
            name=f"cover_hinge_foot_{idx}",
        )
        barrel.visual(
            Box((0.050, 0.036, 0.052)),
            origin=Origin(xyz=(-0.430, y, 0.302)),
            material=iron_edge,
            name=f"cover_hinge_ear_{idx}",
        )

    model.articulation(
        "cradle_to_barrel",
        ArticulationType.REVOLUTE,
        parent=cradle,
        child=barrel,
        origin=Origin(xyz=(0.0, 0.0, 0.48)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=900.0, velocity=0.35, lower=0.0, upper=0.45),
    )

    cover = model.part("touch_cover")
    cover.visual(
        Cylinder(radius=0.018, length=0.160),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=iron_edge,
        name="hinge_knuckle",
    )
    cover.visual(
        Box((0.215, 0.158, 0.014)),
        origin=Origin(xyz=(0.108, 0.0, -0.010)),
        material=iron_edge,
        name="cover_plate",
    )
    cover.visual(
        Box((0.040, 0.082, 0.024)),
        origin=Origin(xyz=(0.188, 0.0, 0.007)),
        material=iron_edge,
        name="lift_tab",
    )

    model.articulation(
        "barrel_to_touch_cover",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=cover,
        origin=Origin(xyz=(-0.430, 0.0, 0.302)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=2.5, lower=0.0, upper=1.35),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
