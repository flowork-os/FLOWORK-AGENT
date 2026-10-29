# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, multisegment_foldout_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: multisegment_foldout_arm

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
import cadquery as cq
from math import hypot
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="fold_out_support_arm")

    base_thickness = 0.006
    base_width = 0.045
    base_height = 0.090

    fork_length = 0.008
    tongue_length = 0.008
    outer_width = 0.020
    fork_gap = 0.011
    lug_width = (outer_width - fork_gap) / 2.0
    tongue_width = fork_gap
    bar_width = 0.013
    bar_height = 0.014
    base_hinge_offset = 0.014

    link_lengths = (0.068, 0.064, 0.060, 0.056)
    end_pad_length = 0.010

    bracket_ear_length = 0.008
    bracket_ear_height = 0.028
    bracket_plate_length = 0.038
    bracket_plate_width = 0.050
    bracket_plate_thickness = 0.004
    bracket_lip_thickness = 0.004
    bracket_lip_height = 0.014
    gusset_length = 0.018
    gusset_height = 0.014
    gusset_width = 0.020

    steel = model.material("steel", color=(0.28, 0.30, 0.33))
    zinc = model.material("zinc", color=(0.68, 0.70, 0.72))

    def add_fork(part, joint_x: float) -> None:
        x_center = joint_x + (fork_length / 2.0)
        y_offset = (fork_gap / 2.0) + (lug_width / 2.0)
        part.visual(
            Box((fork_length, lug_width, bar_height)),
            origin=Origin(xyz=(x_center, y_offset, 0.0)),
            material=steel,
            name="fork_upper",
        )
        part.visual(
            Box((fork_length, lug_width, bar_height)),
            origin=Origin(xyz=(x_center, -y_offset, 0.0)),
            material=steel,
            name="fork_lower",
        )

    def add_link(part, length: float, *, has_distal_fork: bool) -> None:
        part.visual(
            Box((tongue_length, tongue_width, bar_height)),
            origin=Origin(xyz=(tongue_length / 2.0, 0.0, 0.0)),
            material=steel,
            name="tongue",
        )

        core_length = length - tongue_length
        part.visual(
            Box((core_length, bar_width, bar_height)),
            origin=Origin(xyz=(tongue_length + (core_length / 2.0), 0.0, 0.0)),
            material=steel,
            name="core",
        )

        if has_distal_fork:
            add_fork(part, length)
        else:
            part.visual(
                Box((end_pad_length, outer_width, bar_height)),
                origin=Origin(xyz=(length + (end_pad_length / 2.0), 0.0, 0.0)),
                material=steel,
                name="end_pad",
            )

    base_plate = model.part("base_plate")
    base_plate.visual(
        Box((base_thickness, base_width, base_height)),
        origin=Origin(xyz=(-base_thickness / 2.0, 0.0, 0.0)),
        material=steel,
        name="plate",
    )
    base_plate.visual(
        Box((base_thickness * 0.75, base_width * 0.7, bar_height * 1.3)),
        origin=Origin(xyz=(-base_thickness * 0.55, 0.0, 0.0)),
        material=steel,
        name="hinge_reinforcement",
    )
    y_offset = (fork_gap / 2.0) + (lug_width / 2.0)
    base_plate.visual(
        Box((base_hinge_offset, lug_width, bar_height)),
        origin=Origin(xyz=(base_hinge_offset / 2.0, y_offset, 0.0)),
        material=steel,
        name="hinge_bridge_upper",
    )
    base_plate.visual(
        Box((base_hinge_offset, lug_width, bar_height)),
        origin=Origin(xyz=(base_hinge_offset / 2.0, -y_offset, 0.0)),
        material=steel,
        name="hinge_bridge_lower",
    )
    add_fork(base_plate, base_hinge_offset)

    link1 = model.part("link1")
    add_link(link1, link_lengths[0], has_distal_fork=True)

    link2 = model.part("link2")
    add_link(link2, link_lengths[1], has_distal_fork=True)

    link3 = model.part("link3")
    add_link(link3, link_lengths[2], has_distal_fork=True)

    link4 = model.part("link4")
    add_link(link4, link_lengths[3], has_distal_fork=False)

    bracket_shape = (
        cq.Workplane("XY")
        .box(0.004, 0.014, 0.002)
        .translate((0.002, 0.0, 0.008))
        .union(
            cq.Workplane("XY")
            .box(0.003, 0.012, 0.016)
            .translate((0.0055, 0.0, 0.016))
        )
        .union(
            cq.Workplane("XY")
            .box(0.028, bracket_plate_width * 0.90, 0.004)
            .edges("|Z")
            .fillet(0.0015)
            .translate((0.022, 0.0, 0.025))
        )
        .union(
            cq.Workplane("XY")
            .box(0.004, bracket_plate_width * 0.90, 0.014)
            .translate((0.034, 0.0, 0.018))
        )
        .union(
            cq.Workplane("XZ")
            .polyline(((0.007, 0.009), (0.007, 0.023), (0.020, 0.023)))
            .close()
            .extrude(0.006, both=True)
        )
        .faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .pushPoints([(-0.006, 0.0), (0.006, 0.0)])
        .hole(0.0045)
    )

    platform_bracket = model.part("platform_bracket")
    platform_bracket.visual(
        mesh_from_cadquery(bracket_shape, "platform_bracket"),
        material=zinc,
        name="bracket_shell",
    )

    revolute_limits = MotionLimits(
        effort=15.0,
        velocity=2.0,
        lower=-0.75,
        upper=0.75,
    )

    model.articulation(
        "base_to_link1",
        ArticulationType.REVOLUTE,
        parent=base_plate,
        child=link1,
        origin=Origin(xyz=(base_hinge_offset, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=revolute_limits,
    )
    model.articulation(
        "link1_to_link2",
        ArticulationType.REVOLUTE,
        parent=link1,
        child=link2,
        origin=Origin(xyz=(link_lengths[0], 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=revolute_limits,
    )
    model.articulation(
        "link2_to_link3",
        ArticulationType.REVOLUTE,
        parent=link2,
        child=link3,
        origin=Origin(xyz=(link_lengths[1], 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=revolute_limits,
    )
    model.articulation(
        "link3_to_link4",
        ArticulationType.REVOLUTE,
        parent=link3,
        child=link4,
        origin=Origin(xyz=(link_lengths[2], 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=revolute_limits,
    )
    model.articulation(
        "link4_to_platform_bracket",
        ArticulationType.FIXED,
        parent=link4,
        child=platform_bracket,
        origin=Origin(xyz=(link_lengths[3] + end_pad_length, 0.0, 0.0)),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
