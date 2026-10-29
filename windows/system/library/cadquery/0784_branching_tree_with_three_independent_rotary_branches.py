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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
FRAME_HEIGHT = 0.82
FRAME_WIDTH = 0.15
FRAME_THICK = 0.032
RAIL_WIDTH = 0.028
INNER_GAP = 0.024
PLATE_THICKNESS = 0.006
BARREL_RADIUS = 0.0044
PIN_RADIUS = 0.0044
HOLE_CLEARANCE = 0.0
BRANCH_SPECS = {
    "lower_branch": {
        "joint": "frame_to_lower_branch",
        "support_z": 0.18,
        "support_y": 0.087,
        "pad_w": 0.064,
        "block_h": 0.070,
        "pad_x": 0.014,
        "plate_x": 0.028,
        "body_len": 0.155,
        "nose_len": 0.022,
        "root_w": 0.018,
        "root_h": 0.026,
        "tip_w": 0.015,
        "tip_h": 0.020,
        "mass": 0.62,
    },
    "middle_branch": {
        "joint": "frame_to_middle_branch",
        "support_z": 0.43,
        "support_y": -0.087,
        "pad_w": 0.072,
        "block_h": 0.082,
        "pad_x": 0.016,
        "plate_x": 0.032,
        "body_len": 0.235,
        "nose_len": 0.025,
        "root_w": 0.020,
        "root_h": 0.030,
        "tip_w": 0.016,
        "tip_h": 0.022,
        "mass": 0.78,
    },
    "upper_branch": {
        "joint": "frame_to_upper_branch",
        "support_z": 0.66,
        "support_y": 0.085,
        "pad_w": 0.058,
        "block_h": 0.066,
        "pad_x": 0.013,
        "plate_x": 0.026,
        "body_len": 0.132,
        "nose_len": 0.020,
        "root_w": 0.017,
        "root_h": 0.024,
        "tip_w": 0.014,
        "tip_h": 0.018,
        "mass": 0.54,
    },
}
def _box_at(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _cylinder_y(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return cq.Workplane(
        obj=cq.Solid.makeCylinder(
            radius,
            length,
            cq.Vector(center[0], center[1] - (length / 2.0), center[2]),
            cq.Vector(0.0, 1.0, 0.0),
        )
    )
def _support_pivot_x(spec: dict[str, float | str]) -> float:
    return ((FRAME_THICK / 2.0) - 0.004) + float(spec["pad_x"]) + float(spec["plate_x"]) + BARREL_RADIUS
def _build_support(spec: dict[str, float | str]) -> cq.Workplane:
    support_y = float(spec["support_y"])
    support_z = float(spec["support_z"])
    block_h = float(spec["block_h"])
    pad_x = float(spec["pad_x"])
    plate_x = float(spec["plate_x"])
    embed = 0.004
    total_y = INNER_GAP + (2.0 * PLATE_THICKNESS)
    full_depth = pad_x + plate_x
    rib_h = min(0.012, block_h * 0.22)
    open_h = block_h - (2.0 * rib_h)
    bracket_center_x = (FRAME_THICK / 2.0) + (full_depth / 2.0) - embed

    support = _box_at((full_depth, total_y, block_h), (bracket_center_x, support_y, support_z))
    support = support.cut(
        _box_at(
            (full_depth + 0.004, INNER_GAP, open_h),
            ((FRAME_THICK / 2.0) + (full_depth / 2.0), support_y, support_z),
        )
    )

    hole = _cylinder_y(
        PIN_RADIUS + HOLE_CLEARANCE,
        total_y + 0.010,
        (_support_pivot_x(spec), support_y, support_z),
    )
    return support.cut(hole)
def _build_frame_shape() -> cq.Shape:
    rail_y = (FRAME_WIDTH / 2.0) - (RAIL_WIDTH / 2.0)
    frame = _box_at((FRAME_THICK, RAIL_WIDTH, FRAME_HEIGHT), (0.0, rail_y, FRAME_HEIGHT / 2.0))
    frame = frame.union(
        _box_at((FRAME_THICK, RAIL_WIDTH, FRAME_HEIGHT), (0.0, -rail_y, FRAME_HEIGHT / 2.0))
    )

    rung_specs = (
        (0.052, 0.030, FRAME_WIDTH - 0.038, FRAME_THICK * 0.95),
        (0.245, 0.020, FRAME_WIDTH - 0.046, FRAME_THICK * 0.78),
        (0.445, 0.020, FRAME_WIDTH - 0.050, FRAME_THICK * 0.72),
        (0.635, 0.020, FRAME_WIDTH - 0.046, FRAME_THICK * 0.78),
        (0.768, 0.028, FRAME_WIDTH - 0.038, FRAME_THICK * 0.92),
    )
    for z_center, rung_h, rung_w, rung_x in rung_specs:
        frame = frame.union(_box_at((rung_x, rung_w, rung_h), (0.0, 0.0, z_center)))

    frame = frame.union(_box_at((0.018, 0.040, 0.58), (0.0, 0.0, 0.39)))

    for spec in BRANCH_SPECS.values():
        frame = frame.union(_build_support(spec))

    return frame.val()
def _build_branch_shape(spec: dict[str, float | str]) -> cq.Shape:
    body_len = float(spec["body_len"])
    nose_len = float(spec["nose_len"])
    root_w = float(spec["root_w"])
    root_h = float(spec["root_h"])
    tip_w = float(spec["tip_w"])
    tip_h = float(spec["tip_h"])
    arm_thickness = INNER_GAP - 0.006
    collar_len = 0.014
    collar_h = root_h * 0.86
    mid_x = collar_len + (body_len * 0.58)
    tip_x = collar_len + body_len
    nose_x = tip_x + nose_len

    barrel = _cylinder_y(BARREL_RADIUS, INNER_GAP, (0.0, 0.0, 0.0))
    collar = _box_at((collar_len, arm_thickness, collar_h), (collar_len / 2.0, 0.0, 0.0))
    beam = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.006, -(root_h * 0.42)),
                (mid_x, -(root_h * 0.26)),
                (tip_x, -(tip_h * 0.48)),
                (nose_x, 0.0),
                (tip_x, tip_h * 0.48),
                (mid_x, root_h * 0.26),
                (0.006, root_h * 0.42),
            ]
        )
        .close()
        .extrude(arm_thickness, both=True)
    )

    return barrel.union(collar).union(beam).val()
def _branch_inertial(spec: dict[str, float | str]) -> Inertial:
    body_len = float(spec["body_len"])
    nose_len = float(spec["nose_len"])
    root_w = float(spec["root_w"])
    root_h = float(spec["root_h"])
    mass = float(spec["mass"])
    approx_len = body_len + nose_len + 0.020
    return Inertial.from_geometry(
        Box((approx_len, root_w + 0.010, root_h + 0.010)),
        mass=mass,
        origin=Origin(xyz=(approx_len / 2.0, 0.0, 0.0)),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="three_branch_fixture")

    model.material("frame_steel", rgba=(0.22, 0.24, 0.27, 1.0))
    model.material("arm_aluminum", rgba=(0.70, 0.73, 0.77, 1.0))

    frame = model.part("frame")
    frame.visual(
        mesh_from_cadquery(_build_frame_shape(), "fixture_frame"),
        material="frame_steel",
        name="frame_skin",
    )
    frame.inertial = Inertial.from_geometry(
        Box((0.090, FRAME_WIDTH, FRAME_HEIGHT)),
        mass=7.2,
        origin=Origin(xyz=(0.0, 0.0, FRAME_HEIGHT / 2.0)),
    )

    for branch_name, spec in BRANCH_SPECS.items():
        branch = model.part(branch_name)
        branch.visual(
            mesh_from_cadquery(_build_branch_shape(spec), f"{branch_name}_skin"),
            material="arm_aluminum",
            name="arm_skin",
        )
        branch.inertial = _branch_inertial(spec)

        model.articulation(
            str(spec["joint"]),
            ArticulationType.REVOLUTE,
            parent=frame,
            child=branch,
            origin=Origin(
                xyz=(
                    _support_pivot_x(spec),
                    float(spec["support_y"]),
                    float(spec["support_z"]),
                )
            ),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                lower=-0.35,
                upper=1.15,
                effort=18.0,
                velocity=1.6,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
