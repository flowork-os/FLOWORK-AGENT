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
BRIDGE_WIDTH = 0.16
BRIDGE_LENGTH = 1.28
BRIDGE_HEIGHT = 0.09
BRACKET_PLATE_X = 0.09
BRACKET_PLATE_Y = 0.07
BRACKET_PLATE_Z = 0.018
BRACKET_PIVOT_Z = -(BRACKET_PLATE_Z + 0.072)
ARM_BODY_WIDTH = 0.014
BRANCH_LAYOUT = [
    ("left", -0.40, 0.58),
    ("center", 0.00, 0.68),
    ("right", 0.40, 0.58),
]
def make_bridge() -> cq.Workplane:
    beam = (
        cq.Workplane("XY")
        .box(BRIDGE_WIDTH, BRIDGE_LENGTH, BRIDGE_HEIGHT)
        .edges("|Y")
        .fillet(0.012)
    )
    spine = (
        cq.Workplane("XY")
        .box(0.07, BRIDGE_LENGTH * 0.82, 0.032)
        .translate((0.0, 0.0, BRIDGE_HEIGHT / 2 + 0.016))
    )
    end_caps = (
        cq.Workplane("XY")
        .box(BRIDGE_WIDTH * 0.82, 0.11, 0.03)
        .translate((0.0, BRIDGE_LENGTH * 0.5 - 0.055, BRIDGE_HEIGHT / 2 + 0.015))
        .union(
            cq.Workplane("XY")
            .box(BRIDGE_WIDTH * 0.82, 0.11, 0.03)
            .translate((0.0, -(BRIDGE_LENGTH * 0.5 - 0.055), BRIDGE_HEIGHT / 2 + 0.015))
        )
    )
    return beam.union(spine).union(end_caps)
def make_bracket() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(BRACKET_PLATE_X, BRACKET_PLATE_Y, BRACKET_PLATE_Z, centered=(True, True, False))
        .translate((0.0, 0.0, -BRACKET_PLATE_Z))
    )
    hanger_web = (
        cq.Workplane("XY")
        .box(0.022, 0.030, 0.062)
        .translate((0.0, 0.0, -0.049))
    )
    pivot_pad = (
        cq.Workplane("XY")
        .box(0.038, 0.024, 0.010)
        .translate((0.0, 0.0, BRACKET_PIVOT_Z + 0.005))
    )
    rib_profile = [
        (0.019, -BRACKET_PLATE_Z),
        (0.030, -BRACKET_PLATE_Z),
        (0.024, BRACKET_PIVOT_Z + 0.010),
        (0.011, BRACKET_PIVOT_Z + 0.010),
    ]
    rib_a = (
        cq.Workplane("XZ")
        .polyline(rib_profile)
        .close()
        .extrude(0.006)
        .translate((0.0, 0.012, 0.0))
    )
    rib_b = (
        cq.Workplane("XZ")
        .polyline(rib_profile)
        .close()
        .extrude(-0.006)
        .translate((0.0, -0.012, 0.0))
    )
    return plate.union(hanger_web).union(pivot_pad).union(rib_a).union(rib_b)
def make_arm(length: float) -> cq.Workplane:
    top_cap = (
        cq.Workplane("XY")
        .box(0.034, ARM_BODY_WIDTH, 0.010)
        .translate((0.0, 0.0, -0.005))
    )

    shoulder_half = 0.022
    mid_half = 0.018
    tip_half = 0.024
    profile = [
        (0.007, -0.010),
        (0.010, -0.085),
        (shoulder_half, -0.148),
        (mid_half, -(0.48 * length)),
        (0.024, -(length - 0.048)),
        (tip_half, -length),
        (-tip_half, -length),
        (-0.024, -(length - 0.048)),
        (-mid_half, -(0.48 * length)),
        (-shoulder_half, -0.148),
        (-0.010, -0.085),
        (-0.007, -0.010),
    ]
    blade = (
        cq.Workplane("XZ")
        .polyline(profile)
        .close()
        .extrude(ARM_BODY_WIDTH * 0.5, both=True)
    )

    return top_cap.union(blade)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="underslung_three_branch_rotary_frame")

    bridge_color = model.material("bridge_charcoal", rgba=(0.20, 0.22, 0.24, 1.0))
    bracket_color = model.material("bracket_steel", rgba=(0.56, 0.59, 0.62, 1.0))
    arm_color = model.material("arm_black", rgba=(0.10, 0.10, 0.11, 1.0))

    bridge = model.part("top_bridge")
    bridge.visual(
        mesh_from_cadquery(make_bridge(), "top_bridge"),
        material=bridge_color,
        name="bridge_shell",
    )

    for branch_name, y_pos, arm_length in BRANCH_LAYOUT:
        bracket = model.part(f"{branch_name}_bracket")
        bracket.visual(
            mesh_from_cadquery(make_bracket(), f"{branch_name}_bracket"),
            material=bracket_color,
            name="bracket_shell",
        )

        arm = model.part(f"{branch_name}_arm")
        arm.visual(
            mesh_from_cadquery(make_arm(arm_length), f"{branch_name}_arm"),
            material=arm_color,
            name="arm_shell",
        )

        model.articulation(
            f"bridge_to_{branch_name}_bracket",
            ArticulationType.FIXED,
            parent=bridge,
            child=bracket,
            origin=Origin(xyz=(0.0, y_pos, -BRIDGE_HEIGHT * 0.5)),
        )
        model.articulation(
            f"{branch_name}_bracket_to_{branch_name}_arm",
            ArticulationType.REVOLUTE,
            parent=bracket,
            child=arm,
            origin=Origin(xyz=(0.0, 0.0, BRACKET_PIVOT_Z)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=18.0,
                velocity=1.5,
                lower=-0.8,
                upper=0.8,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
