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
def _radial_xy(radius: float, yaw: float, z: float) -> tuple[float, float, float]:
    return (radius * math.cos(yaw), radius * math.sin(yaw), z)
def _arm_backbone(
    *,
    arm_length: float,
    hub_outer: float,
    hub_inner: float,
    hub_height: float,
    bar_width: float,
    bar_height: float,
) -> cq.Workplane:
    """A hollow pivot sleeve welded to a straight tooling arm."""

    ring = (
        cq.Workplane("XY")
        .circle(hub_outer)
        .circle(hub_inner)
        .extrude(hub_height)
        .translate((0.0, 0.0, -hub_height / 2.0))
    )
    bar_start = hub_outer - 0.004
    bar = (
        cq.Workplane("XY")
        .box(arm_length, bar_width, bar_height)
        .translate((bar_start + arm_length / 2.0, 0.0, 0.0))
    )
    neck = (
        cq.Workplane("XY")
        .box(0.040, bar_width * 1.45, bar_height * 1.35)
        .translate((hub_outer + 0.012, 0.0, 0.0))
    )
    return ring.union(bar).union(neck)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="pedestal_tooling_tree")

    cast_iron = Material("cast_iron", rgba=(0.08, 0.085, 0.09, 1.0))
    column_metal = Material("brushed_column", rgba=(0.46, 0.47, 0.46, 1.0))
    clamp_paint = Material("clamp_graphite", rgba=(0.16, 0.17, 0.18, 1.0))
    pin_steel = Material("bearing_pin_steel", rgba=(0.72, 0.72, 0.68, 1.0))
    arm_paint = Material("tool_arm_blue", rgba=(0.05, 0.18, 0.36, 1.0))
    plate_yellow = Material("faceplate_yellow", rgba=(0.92, 0.65, 0.12, 1.0))
    black_oxide = Material("black_oxide", rgba=(0.015, 0.015, 0.012, 1.0))

    pedestal = model.part("pedestal")
    pedestal.visual(
        Cylinder(radius=0.260, length=0.070),
        origin=Origin(xyz=(0.0, 0.0, 0.035)),
        material=cast_iron,
        name="foot_disk",
    )
    pedestal.visual(
        Cylinder(radius=0.115, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0875)),
        material=cast_iron,
        name="base_boss",
    )
    pedestal.visual(
        Cylinder(radius=0.035, length=0.850),
        origin=Origin(xyz=(0.0, 0.0, 0.495)),
        material=column_metal,
        name="column",
    )
    pedestal.visual(
        Cylinder(radius=0.047, length=0.026),
        origin=Origin(xyz=(0.0, 0.0, 0.933)),
        material=column_metal,
        name="top_cap",
    )

    block_heights = (0.300, 0.550, 0.795)
    block_yaws = (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)
    pivot_radius = 0.185
    lug_outer_radius = 0.1525

    for idx, (height, yaw) in enumerate(zip(block_heights, block_yaws)):
        pedestal.visual(
            Box((0.125, 0.105, 0.070)),
            origin=Origin(xyz=(0.0, 0.0, height), rpy=(0.0, 0.0, yaw)),
            material=clamp_paint,
            name=f"clamp_{idx}",
        )
        pedestal.visual(
            Box((0.095, 0.080, 0.070)),
            origin=Origin(xyz=_radial_xy(0.105, yaw, height), rpy=(0.0, 0.0, yaw)),
            material=clamp_paint,
            name=f"lug_{idx}",
        )
        for plate_name, z_offset in (("lower_fork", -0.034), ("upper_fork", 0.034)):
            pedestal.visual(
                Box((0.075, 0.075, 0.010)),
                origin=Origin(
                    xyz=_radial_xy(0.185, yaw, height + z_offset),
                    rpy=(0.0, 0.0, yaw),
                ),
                material=clamp_paint,
                name=f"{plate_name}_{idx}",
            )
        pedestal.visual(
            Cylinder(radius=0.010, length=0.092),
            origin=Origin(xyz=_radial_xy(pivot_radius, yaw, height)),
            material=pin_steel,
            name=f"pin_{idx}",
        )
        for side in (-1.0, 1.0):
            local_r = 0.008
            tangential = 0.046 * side
            x = 0.100 * math.cos(yaw) - tangential * math.sin(yaw)
            y = 0.100 * math.sin(yaw) + tangential * math.cos(yaw)
            pedestal.visual(
                Cylinder(radius=local_r, length=0.012),
                origin=Origin(
                    xyz=(x, y, height + 0.018),
                    rpy=(math.pi / 2.0, 0.0, yaw),
                ),
                material=black_oxide,
                name=f"clamp_screw_{idx}_{int(side > 0)}",
            )

    arm_length = 0.300
    hub_outer = 0.024
    hub_inner = 0.013
    # The sleeve touches the fixed fork plates at its top and bottom faces, so
    # the rotary arm reads as physically carried by the clamp block rather than
    # floating around a clearance-only bearing.
    hub_height = 0.058
    bar_width = 0.028
    bar_height = 0.024
    face_thickness = 0.025
    face_center_x = hub_outer - 0.004 + arm_length + face_thickness / 2.0 - 0.002

    for idx, (height, yaw) in enumerate(zip(block_heights, block_yaws)):
        arm = model.part(f"arm_{idx}")
        arm.visual(
            mesh_from_cadquery(
                _arm_backbone(
                    arm_length=arm_length,
                    hub_outer=hub_outer,
                    hub_inner=hub_inner,
                    hub_height=hub_height,
                    bar_width=bar_width,
                    bar_height=bar_height,
                ),
                f"arm_backbone_{idx}",
                tolerance=0.0006,
                angular_tolerance=0.08,
            ),
            material=arm_paint,
            name=f"backbone_{idx}",
        )
        arm.visual(
            Box((face_thickness, 0.105, 0.075)),
            origin=Origin(xyz=(face_center_x, 0.0, 0.0)),
            material=plate_yellow,
            name=f"faceplate_{idx}",
        )
        for bolt_idx, (y, z) in enumerate(
            ((-0.031, -0.023), (-0.031, 0.023), (0.031, -0.023), (0.031, 0.023))
        ):
            arm.visual(
                Cylinder(radius=0.006, length=0.006),
                origin=Origin(
                    xyz=(face_center_x + face_thickness / 2.0 + 0.002, y, z),
                    rpy=(0.0, math.pi / 2.0, 0.0),
                ),
                material=black_oxide,
                name=f"face_bolt_{idx}_{bolt_idx}",
            )
        model.articulation(
            f"branch_{idx}_pivot",
            ArticulationType.REVOLUTE,
            parent=pedestal,
            child=arm,
            origin=Origin(xyz=_radial_xy(pivot_radius, yaw, height), rpy=(0.0, 0.0, yaw)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(effort=18.0, velocity=1.4, lower=-1.15, upper=1.15),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
