# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_three_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_three_independent_rotary_branches

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
BASE_RADIUS = 0.075
BASE_LOWER_HEIGHT = 0.022
BASE_UPPER_RADIUS = 0.050
BASE_UPPER_HEIGHT = 0.008
BASE_HEIGHT = BASE_LOWER_HEIGHT + BASE_UPPER_HEIGHT
POST_RADIUS = 0.015
POST_HEIGHT = 0.190
SUPPORT_OFFSET = 0.034
SUPPORT_BOSS_RADIUS = 0.009
SUPPORT_THICKNESS = 0.014
SUPPORT_WEB_WIDTH = 0.014
SUPPORT_SADDLE_DEPTH = 0.012
SUPPORT_SADDLE_WIDTH = 0.030
TAB_BARREL_OUTER_RADIUS = 0.013
TAB_ARM_LENGTH = 0.055
TAB_ARM_WIDTH = 0.012
TAB_ARM_HEIGHT = 0.010
OUTPUT_FACE_THICKNESS = 0.008
OUTPUT_FACE_WIDTH = 0.022
OUTPUT_FACE_HEIGHT = 0.020
TAB_LEVELS = (0.055, 0.105, 0.155)
TAB_ANGLES = (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)
TAB_LIMITS = (-0.90, 0.90)
def make_base_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(BASE_RADIUS)
        .extrude(BASE_LOWER_HEIGHT)
        .faces(">Z")
        .workplane()
        .circle(BASE_UPPER_RADIUS)
        .extrude(BASE_UPPER_HEIGHT)
    )
def make_support_shape() -> cq.Workplane:
    raw = (
        cq.Workplane("XY")
        .center(POST_RADIUS + SUPPORT_SADDLE_DEPTH / 2.0, 0.0)
        .rect(SUPPORT_SADDLE_DEPTH, SUPPORT_SADDLE_WIDTH)
        .extrude(SUPPORT_THICKNESS)
        .union(
            cq.Workplane("XY")
            .center(SUPPORT_OFFSET, 0.0)
            .circle(SUPPORT_BOSS_RADIUS)
            .extrude(SUPPORT_THICKNESS)
        )
        .union(
            cq.Workplane("XY")
            .center((POST_RADIUS + SUPPORT_OFFSET) / 2.0, 0.0)
            .rect(SUPPORT_OFFSET - POST_RADIUS, SUPPORT_WEB_WIDTH)
            .extrude(SUPPORT_THICKNESS)
        )
    )
    cleared = raw.cut(
        cq.Workplane("XY")
        .circle(POST_RADIUS)
        .extrude(SUPPORT_THICKNESS)
    )
    return cleared.translate((0.0, 0.0, -SUPPORT_THICKNESS / 2.0))
def make_tab_core_shape() -> cq.Workplane:
    arm_overlap = 0.003
    core = (
        cq.Workplane("XY")
        .circle(TAB_BARREL_OUTER_RADIUS)
        .extrude(TAB_ARM_HEIGHT)
        .union(
            cq.Workplane("XY")
            .center(TAB_BARREL_OUTER_RADIUS + TAB_ARM_LENGTH / 2.0 - arm_overlap / 2.0, 0.0)
            .rect(TAB_ARM_LENGTH + arm_overlap, TAB_ARM_WIDTH)
            .extrude(TAB_ARM_HEIGHT)
        )
    )
    return core
def polar_xyz(radius: float, angle: float, z: float) -> tuple[float, float, float]:
    return (radius * math.cos(angle), radius * math.sin(angle), z)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pedestal_three_branch_fixture")

    base_mat = model.material("base_powder_coat", rgba=(0.18, 0.19, 0.20, 1.0))
    post_mat = model.material("post_satin_aluminum", rgba=(0.70, 0.71, 0.73, 1.0))
    support_mat = model.material("support_dark_alloy", rgba=(0.32, 0.33, 0.36, 1.0))
    tab_mat = model.material("tab_orange_enamel", rgba=(0.82, 0.38, 0.12, 1.0))
    face_mat = model.material("output_face_machined", rgba=(0.83, 0.84, 0.86, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(make_base_shape(), "fixture_base"),
        material=base_mat,
        name="base_shell",
    )

    post = model.part("post")
    post.visual(
        Cylinder(radius=POST_RADIUS, length=POST_HEIGHT),
        origin=Origin(xyz=(0.0, 0.0, POST_HEIGHT / 2.0)),
        material=post_mat,
        name="post_shaft",
    )

    model.articulation(
        "base_to_post",
        ArticulationType.FIXED,
        parent=base,
        child=post,
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT)),
    )

    for index, (level, angle) in enumerate(zip(TAB_LEVELS, TAB_ANGLES), start=1):
        support = model.part(f"support_{index}")
        support.visual(
            mesh_from_cadquery(make_support_shape(), f"support_{index}_body"),
            material=support_mat,
            name="support_body",
        )

        model.articulation(
            f"post_to_support_{index}",
            ArticulationType.FIXED,
            parent=post,
            child=support,
            origin=Origin(
                xyz=polar_xyz(0.0, angle, level),
                rpy=(0.0, 0.0, angle),
            ),
        )

        tab = model.part(f"tab_{index}")
        tab.visual(
            mesh_from_cadquery(make_tab_core_shape(), f"tab_{index}_core"),
            material=tab_mat,
            name="tab_core",
        )
        tab.visual(
            Box((OUTPUT_FACE_THICKNESS, OUTPUT_FACE_WIDTH, OUTPUT_FACE_HEIGHT)),
            origin=Origin(
                xyz=(
                    TAB_BARREL_OUTER_RADIUS
                    + TAB_ARM_LENGTH
                    + OUTPUT_FACE_THICKNESS / 2.0,
                    0.0,
                    OUTPUT_FACE_HEIGHT / 2.0,
                )
            ),
            material=face_mat,
            name="output_face",
        )

        model.articulation(
            f"support_{index}_to_tab_{index}",
            ArticulationType.REVOLUTE,
            parent=support,
            child=tab,
            origin=Origin(xyz=(SUPPORT_OFFSET, 0.0, SUPPORT_THICKNESS / 2.0)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(
                effort=4.0,
                velocity=2.0,
                lower=TAB_LIMITS[0],
                upper=TAB_LIMITS[1],
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
