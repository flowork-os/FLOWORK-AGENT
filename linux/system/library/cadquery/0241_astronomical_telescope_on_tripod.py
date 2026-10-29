# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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
def _annular_cylinder_mesh(outer_radius: float, inner_radius: float, length: float, name: str):
    """A hollow cylinder centered on local Z, exported as a managed mesh."""

    body = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
    )
    return mesh_from_cadquery(body, name, tolerance=0.001, angular_tolerance=0.08)
def _leg_origin(angle: float, top_z: float, foot_radius: float, foot_z: float) -> tuple[Origin, float]:
    """Return a box origin whose local Z runs from the tripod hub to a foot."""

    x = foot_radius * math.cos(angle)
    y = foot_radius * math.sin(angle)
    dz = foot_z - top_z
    length = math.sqrt(x * x + y * y + dz * dz)
    center = (0.5 * x, 0.5 * y, 0.5 * (top_z + foot_z))
    pitch = math.acos(dz / length)
    return Origin(xyz=center, rpy=(0.0, pitch, angle)), length
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_sct_single_arm_equatorial")

    orange = model.material("powder_orange", rgba=(0.88, 0.33, 0.08, 1.0))
    black = model.material("satin_black", rgba=(0.015, 0.016, 0.018, 1.0))
    dark = model.material("matte_dark_gray", rgba=(0.07, 0.075, 0.08, 1.0))
    metal = model.material("brushed_metal", rgba=(0.56, 0.58, 0.60, 1.0))
    rubber = model.material("black_rubber", rgba=(0.0, 0.0, 0.0, 1.0))
    glass = model.material("faint_blue_glass", rgba=(0.55, 0.78, 0.95, 0.34))

    tilt = math.radians(35.0)

    tripod = model.part("tripod")
    tripod.visual(
        Cylinder(radius=0.065, length=0.50),
        origin=Origin(xyz=(0.0, 0.0, 0.285)),
        material=metal,
        name="center_column",
    )
    tripod.visual(
        Cylinder(radius=0.083, length=0.10),
        origin=Origin(xyz=(0.0, 0.0, 0.535)),
        material=metal,
        name="top_hub",
    )
    tripod.visual(
        Cylinder(radius=0.22, length=0.016),
        origin=Origin(xyz=(0.0, 0.0, 0.325)),
        material=metal,
        name="spreader_tray",
    )
    tripod.visual(
        Cylinder(radius=0.090, length=0.090),
        origin=Origin(xyz=(0.0, 0.0, 0.605)),
        material=metal,
        name="wedge_pier",
    )
    tripod.visual(
        Box((0.42, 0.31, 0.034)),
        origin=Origin(xyz=(0.0, 0.0, 0.650)),
        material=dark,
        name="wedge_lower_plate",
    )

    top_z = 0.535
    foot_z = 0.030
    foot_radius = 0.50
    for idx, angle in enumerate((math.radians(90.0), math.radians(210.0), math.radians(330.0))):
        leg_origin, leg_length = _leg_origin(angle, top_z, foot_radius, foot_z)
        tripod.visual(
            Box((0.042, 0.034, leg_length)),
            origin=leg_origin,
            material=metal,
            name=f"tripod_leg_{idx}",
        )
        tripod.visual(
            Box((0.17, 0.085, 0.030)),
            origin=Origin(
                xyz=(foot_radius * math.cos(angle), foot_radius * math.sin(angle), 0.015),
                rpy=(0.0, 0.0, angle),
            ),
            material=rubber,
            name=f"foot_pad_{idx}",
        )

    wedge_top = (0.0, 0.0, 0.765)
    wedge_normal = (-math.sin(tilt), 0.0, math.cos(tilt))
    wedge_center = tuple(wedge_top[i] - 0.5 * 0.036 * wedge_normal[i] for i in range(3))
    tripod.visual(
        Box((0.38, 0.29, 0.036)),
        origin=Origin(xyz=wedge_center, rpy=(0.0, -tilt, 0.0)),
        material=orange,
        name="wedge_plate",
    )
    tripod.visual(
        Box((0.24, 0.035, 0.15)),
        origin=Origin(xyz=(-0.015, 0.145, 0.700), rpy=(0.0, -0.5 * tilt, 0.0)),
        material=orange,
        name="wedge_side_cheek_0",
    )
    tripod.visual(
        Box((0.24, 0.035, 0.15)),
        origin=Origin(xyz=(-0.015, -0.145, 0.700), rpy=(0.0, -0.5 * tilt, 0.0)),
        material=orange,
        name="wedge_side_cheek_1",
    )

    polar_head = model.part("polar_head")
    polar_head.visual(
        Cylinder(radius=0.095, length=0.160),
        origin=Origin(xyz=(0.0, 0.0, 0.080)),
        material=dark,
        name="ra_bearing",
    )
    polar_head.visual(
        Cylinder(radius=0.025, length=0.240),
        origin=Origin(xyz=(-0.055, 0.0, 0.055), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="latitude_hinge_bar",
    )
    polar_head.visual(
        Box((0.18, 0.20, 0.075)),
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
        material=orange,
        name="tilt_base_block",
    )
    polar_head.visual(
        Box((0.012, 0.10, 0.070)),
        origin=Origin(xyz=(0.094, 0.0, 0.070)),
        material=metal,
        name="polar_scale_plate",
    )

    fork_arm = model.part("fork_arm")
    fork_arm.visual(
        Cylinder(radius=0.105, length=0.075),
        origin=Origin(xyz=(0.0, 0.0, 0.0375)),
        material=orange,
        name="ra_collar",
    )
    fork_arm.visual(
        Box((0.090, 0.230, 0.090)),
        origin=Origin(xyz=(0.0, -0.095, 0.075)),
        material=orange,
        name="arm_root_web",
    )
    fork_arm.visual(
        Box((0.078, 0.050, 0.420)),
        origin=Origin(xyz=(0.0, -0.215, 0.260)),
        material=orange,
        name="single_fork_arm",
    )
    fork_arm.visual(
        Box((0.095, 0.070, 0.100)),
        origin=Origin(xyz=(0.0, -0.215, 0.470)),
        material=orange,
        name="declination_cap",
    )
    fork_arm.visual(
        Cylinder(radius=0.075, length=0.050),
        origin=Origin(xyz=(0.0, -0.205, 0.470), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="declination_boss",
    )

    optical_tube = model.part("optical_tube")
    tube_shell = _annular_cylinder_mesh(0.120, 0.105, 0.420, "stubby_tube_shell")
    front_ring = _annular_cylinder_mesh(0.128, 0.103, 0.025, "front_retain_ring")
    optical_tube.visual(
        tube_shell,
        origin=Origin(xyz=(0.0, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=orange,
        name="tube_shell",
    )
    optical_tube.visual(
        front_ring,
        origin=Origin(xyz=(0.218, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="front_retain_ring",
    )
    optical_tube.visual(
        Cylinder(radius=0.103, length=0.008),
        origin=Origin(xyz=(0.214, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_corrector",
    )
    optical_tube.visual(
        Cylinder(radius=0.035, length=0.012),
        origin=Origin(xyz=(0.221, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="secondary_mirror",
    )
    optical_tube.visual(
        Cylinder(radius=0.130, length=0.055),
        origin=Origin(xyz=(-0.2275, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="rear_cell",
    )
    optical_tube.visual(
        Cylinder(radius=0.034, length=0.085),
        origin=Origin(xyz=(-0.2975, 0.170, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark,
        name="rear_visual_back",
    )
    optical_tube.visual(
        Cylinder(radius=0.013, length=0.030),
        origin=Origin(xyz=(-0.270, 0.255, 0.035), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal,
        name="focus_socket",
    )
    optical_tube.visual(
        Cylinder(radius=0.050, length=0.110),
        origin=Origin(xyz=(0.0, 0.055, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=metal,
        name="declination_shaft",
    )
    optical_tube.visual(
        Cylinder(radius=0.066, length=0.030),
        origin=Origin(xyz=(0.0, 0.015, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=orange,
        name="declination_side_cap",
    )
    optical_tube.visual(
        Cylinder(radius=0.023, length=0.230),
        origin=Origin(xyz=(-0.015, 0.170, 0.190), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="finder_scope",
    )
    for idx, x in enumerate((-0.080, 0.060)):
        optical_tube.visual(
            Box((0.020, 0.030, 0.082)),
            origin=Origin(xyz=(x, 0.170, 0.153)),
            material=metal,
            name=f"finder_bracket_{idx}",
        )

    focus_knob = model.part("focus_knob")
    focus_knob.visual(
        Cylinder(radius=0.018, length=0.035),
        origin=Origin(xyz=(-0.0175, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="knob_cap",
    )

    model.articulation(
        "polar_angle",
        ArticulationType.REVOLUTE,
        parent=tripod,
        child=polar_head,
        origin=Origin(xyz=wedge_top, rpy=(0.0, -tilt, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=60.0, velocity=0.25, lower=-0.22, upper=0.30),
    )
    model.articulation(
        "right_ascension",
        ArticulationType.CONTINUOUS,
        parent=polar_head,
        child=fork_arm,
        origin=Origin(xyz=(0.0, 0.0, 0.160)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=0.75),
    )
    model.articulation(
        "declination",
        ArticulationType.REVOLUTE,
        parent=fork_arm,
        child=optical_tube,
        origin=Origin(xyz=(0.0, -0.180, 0.470)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=0.65, lower=-0.75, upper=1.15),
    )
    model.articulation(
        "focus",
        ArticulationType.CONTINUOUS,
        parent=optical_tube,
        child=focus_knob,
        origin=Origin(xyz=(-0.285, 0.255, 0.035)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.6, velocity=6.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
