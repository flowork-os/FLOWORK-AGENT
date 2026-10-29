# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bell_tower_with_swinging_bell, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bell_tower_with_swinging_bell

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
HINGE_X = 0.52
HINGE_Z = 2.36
def _cone_frustum(base_radius: float, top_radius: float, height: float, z0: float) -> cq.Workplane:
    """CadQuery cone with its base on z0 and top at z0 + height."""
    solid = cq.Solid.makeCone(
        base_radius,
        top_radius,
        height,
        pnt=cq.Vector(0.0, 0.0, z0),
        dir=cq.Vector(0.0, 0.0, 1.0),
    )
    return cq.Workplane("XY").add(solid)
def _frustum_shell(
    base_outer: float,
    top_outer: float,
    base_inner: float,
    top_inner: float,
    height: float,
    z0: float,
) -> cq.Workplane:
    outer = _cone_frustum(base_outer, top_outer, height, z0)
    inner = _cone_frustum(base_inner, top_inner, height + 0.020, z0 - 0.010)
    return outer.cut(inner)
def _cap_with_shingles() -> cq.Workplane:
    cap = _cone_frustum(0.42, 0.035, 0.48, 2.645)
    for z in (2.690, 2.775, 2.860, 2.945):
        # Raised courses protrude just outside the cone face and are unioned
        # into the cap so the roof remains a single connected timber assembly.
        t = (z - 2.645) / 0.48
        r0 = 0.42 + (0.035 - 0.42) * t + 0.020
        r1 = 0.42 + (0.035 - 0.42) * ((z + 0.032 - 2.645) / 0.48) + 0.014
        cap = cap.union(_cone_frustum(r0, max(r1, 0.030), 0.032, z))
    return cap
def _bell_shell() -> cq.Workplane:
    """A hollow flared iron bell, authored around the local Z axis."""
    shell = _frustum_shell(0.315, 0.070, 0.245, 0.035, 0.680, -0.780)
    flared_lip = _frustum_shell(0.335, 0.302, 0.252, 0.238, 0.070, -0.800)
    neck = _frustum_shell(0.088, 0.058, 0.040, 0.026, 0.100, -0.165)
    # A cast crown boss ties the hollow shell to the headstock block and gives
    # the top of the bell the heavier iron mass seen on harbor warning bells.
    crown = cq.Workplane("XY").cylinder(0.075, 0.072).translate((0.0, 0.0, -0.090))
    return shell.union(flared_lip).union(neck).union(crown)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="seaside_harbor_bell_tower")

    timber = model.material("weathered_timber", rgba=(0.46, 0.29, 0.16, 1.0))
    end_grain = model.material("dark_end_grain", rgba=(0.24, 0.14, 0.08, 1.0))
    shingle = model.material("salt_grey_shingle", rgba=(0.34, 0.33, 0.29, 1.0))
    iron = model.material("blackened_iron", rgba=(0.035, 0.037, 0.040, 1.0))
    worn_iron = model.material("worn_iron_edges", rgba=(0.12, 0.12, 0.11, 1.0))

    tower = model.part("tower")
    tower.visual(
        Cylinder(radius=0.13, length=2.64),
        origin=Origin(xyz=(0.0, 0.0, 1.32)),
        material=timber,
        name="post",
    )
    # Slightly proud horizontal checking bands break up the plain cylinder and
    # read as weathered timber grain without making the post a separate stack.
    for idx, z in enumerate((0.58, 1.18, 1.82, 2.36)):
        tower.visual(
            Cylinder(radius=0.133, length=0.035),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=end_grain,
            name=f"post_grain_{idx}",
        )

    tower.visual(
        Box((1.40, 0.17, 0.15)),
        origin=Origin(xyz=(0.25, 0.0, 2.585)),
        material=timber,
        name="crossbeam",
    )
    tower.visual(
        Box((0.035, 0.175, 0.155)),
        origin=Origin(xyz=(-0.45, 0.0, 2.585)),
        material=end_grain,
        name="beam_end_0",
    )
    tower.visual(
        Box((0.035, 0.175, 0.155)),
        origin=Origin(xyz=(0.95, 0.0, 2.585)),
        material=end_grain,
        name="beam_end_1",
    )

    # The cap is a low seaside cone centered on the post top, with overlapping
    # shingle courses so it reads as shingled rather than a smooth cone.
    tower.visual(
        mesh_from_cadquery(_cap_with_shingles(), "conical_cap"),
        material=shingle,
        name="conical_cap",
    )

    # Fixed iron cleat/hanger under the timber beam.  The two cheek plates flank
    # the moving hinge pin with a small visible clearance rather than colliding.
    tower.visual(
        Box((0.58, 0.13, 0.055)),
        origin=Origin(xyz=(HINGE_X, 0.0, 2.495)),
        material=iron,
        name="headstock_cleat",
    )
    tower.visual(
        Box((0.050, 0.125, 0.230)),
        origin=Origin(xyz=(HINGE_X - 0.245, 0.0, 2.390)),
        material=iron,
        name="cleat_plate_0",
    )
    tower.visual(
        Box((0.050, 0.125, 0.230)),
        origin=Origin(xyz=(HINGE_X + 0.245, 0.0, 2.390)),
        material=iron,
        name="cleat_plate_1",
    )

    bell = model.part("bell")
    bell.visual(
        mesh_from_cadquery(_bell_shell(), "bell_shell", tolerance=0.0008, angular_tolerance=0.06),
        material=iron,
        name="bell_shell",
    )
    bell.visual(
        Box((0.260, 0.092, 0.095)),
        origin=Origin(xyz=(0.0, 0.0, -0.055)),
        material=iron,
        name="headstock_block",
    )
    bell.visual(
        Cylinder(radius=0.029, length=0.520),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=worn_iron,
        name="hinge_pin",
    )

    model.articulation(
        "tower_to_bell",
        ArticulationType.REVOLUTE,
        parent=tower,
        child=bell,
        origin=Origin(xyz=(HINGE_X, 0.0, HINGE_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=25.0, velocity=1.4, lower=-0.75, upper=0.75),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
