# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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
def _tapered_rect_beam(length: float, start_y: float, start_z: float, end_y: float, end_z: float):
    """Rectangular tapered beam from local x=0 to x=length."""
    return (
        cq.Workplane("YZ")
        .rect(start_y, start_z)
        .workplane(offset=length)
        .rect(end_y, end_z)
        .loft(combine=True)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wall_mounted_transfer_arm")

    steel = model.material("powder_coated_steel", rgba=(0.09, 0.11, 0.12, 1.0))
    plate_blue = model.material("blue_grey_structural_links", rgba=(0.20, 0.29, 0.34, 1.0))
    dark_bushing = model.material("black_bushed_knuckles", rgba=(0.015, 0.016, 0.015, 1.0))
    bolt_metal = model.material("brushed_bolt_heads", rgba=(0.62, 0.60, 0.56, 1.0))
    warning = model.material("yellow_load_label", rgba=(0.95, 0.72, 0.08, 1.0))

    # The root frame is the shoulder pivot center.  The wall plate sits behind it
    # on negative X and the arm reaches out along positive X in the rest pose.
    wall_mount = model.part("wall_mount")
    wall_mount.visual(
        Box((0.070, 0.420, 0.720)),
        origin=Origin(xyz=(-0.220, 0.0, -0.060)),
        material=steel,
        name="backplate",
    )
    wall_mount.visual(
        Box((0.070, 0.320, 0.380)),
        origin=Origin(xyz=(-0.145, 0.0, -0.020)),
        material=plate_blue,
        name="raised_spine",
    )
    wall_mount.visual(
        Box((0.230, 0.058, 0.052)),
        origin=Origin(xyz=(-0.075, 0.130, -0.055), rpy=(0.0, 0.45, 0.0)),
        material=plate_blue,
        name="angled_strut_pos",
    )
    wall_mount.visual(
        Box((0.230, 0.058, 0.052)),
        origin=Origin(xyz=(-0.075, -0.130, -0.055), rpy=(0.0, 0.45, 0.0)),
        material=plate_blue,
        name="angled_strut_neg",
    )
    wall_mount.visual(
        Box((0.210, 0.050, 0.042)),
        origin=Origin(xyz=(-0.082, 0.130, 0.070), rpy=(0.0, -0.34, 0.0)),
        material=plate_blue,
        name="upper_strut_pos",
    )
    wall_mount.visual(
        Box((0.210, 0.050, 0.042)),
        origin=Origin(xyz=(-0.082, -0.130, 0.070), rpy=(0.0, -0.34, 0.0)),
        material=plate_blue,
        name="upper_strut_neg",
    )
    wall_mount.visual(
        Box((0.130, 0.060, 0.220)),
        origin=Origin(xyz=(0.0, 0.130, 0.0)),
        material=steel,
        name="shoulder_cheek_pos",
    )
    wall_mount.visual(
        Box((0.130, 0.060, 0.220)),
        origin=Origin(xyz=(0.0, -0.130, 0.0)),
        material=steel,
        name="shoulder_cheek_neg",
    )
    wall_mount.visual(
        Cylinder(radius=0.066, length=0.020),
        origin=Origin(xyz=(0.0, 0.164, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="shoulder_bearing_pos",
    )
    wall_mount.visual(
        Cylinder(radius=0.066, length=0.020),
        origin=Origin(xyz=(0.0, -0.164, 0.0), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="shoulder_bearing_neg",
    )
    for idx, (y, z) in enumerate(((-0.145, -0.295), (0.145, -0.295), (-0.145, 0.195), (0.145, 0.195))):
        wall_mount.visual(
            Cylinder(radius=0.022, length=0.012),
            origin=Origin(xyz=(-0.179, y, z), rpy=(0.0, math.pi / 2, 0.0)),
            material=bolt_metal,
            name=f"backplate_bolt_{idx}",
        )
    wall_mount.visual(
        Box((0.008, 0.165, 0.038)),
        origin=Origin(xyz=(-0.111, 0.0, 0.115)),
        material=warning,
        name="load_label",
    )

    first_link = model.part("first_link")
    first_link.visual(
        Cylinder(radius=0.055, length=0.200),
        origin=Origin(rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="shoulder_barrel",
    )
    first_link.visual(
        mesh_from_cadquery(
            _tapered_rect_beam(0.680, 0.135, 0.155, 0.104, 0.112),
            "first_link_tapered_beam",
            tolerance=0.0015,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.045, 0.0, -0.020)),
        material=plate_blue,
        name="tapered_beam",
    )
    first_link.visual(
        Box((0.560, 0.050, 0.026)),
        origin=Origin(xyz=(0.365, 0.0, 0.058)),
        material=steel,
        name="top_reinforcing_rib",
    )
    first_link.visual(
        Box((0.080, 0.290, 0.180)),
        origin=Origin(xyz=(0.705, 0.0, -0.120)),
        material=steel,
        name="elbow_rear_bridge",
    )
    first_link.visual(
        Box((0.170, 0.055, 0.240)),
        origin=Origin(xyz=(0.820, 0.112, -0.120)),
        material=steel,
        name="elbow_cheek_pos",
    )
    first_link.visual(
        Box((0.170, 0.055, 0.240)),
        origin=Origin(xyz=(0.820, -0.112, -0.120)),
        material=steel,
        name="elbow_cheek_neg",
    )
    first_link.visual(
        Cylinder(radius=0.068, length=0.018),
        origin=Origin(xyz=(0.820, 0.146, -0.120), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="elbow_cap_pos",
    )
    first_link.visual(
        Cylinder(radius=0.068, length=0.018),
        origin=Origin(xyz=(0.820, -0.146, -0.120), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="elbow_cap_neg",
    )

    second_link = model.part("second_link")
    second_link.visual(
        Cylinder(radius=0.052, length=0.169),
        origin=Origin(rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="elbow_barrel",
    )
    second_link.visual(
        mesh_from_cadquery(
            _tapered_rect_beam(0.460, 0.108, 0.105, 0.132, 0.122),
            "second_link_tapered_beam",
            tolerance=0.0015,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.045, 0.0, 0.012)),
        material=plate_blue,
        name="short_beam",
    )
    second_link.visual(
        Box((0.090, 0.240, 0.120)),
        origin=Origin(xyz=(0.455, 0.0, 0.010)),
        material=steel,
        name="wrist_bridge",
    )
    second_link.visual(
        Box((0.120, 0.045, 0.170)),
        origin=Origin(xyz=(0.560, 0.100, 0.020)),
        material=steel,
        name="wrist_cheek_pos",
    )
    second_link.visual(
        Box((0.120, 0.045, 0.170)),
        origin=Origin(xyz=(0.560, -0.100, 0.020)),
        material=steel,
        name="wrist_cheek_neg",
    )
    second_link.visual(
        Cylinder(radius=0.050, length=0.016),
        origin=Origin(xyz=(0.560, 0.129, 0.020), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="wrist_cap_pos",
    )
    second_link.visual(
        Cylinder(radius=0.050, length=0.016),
        origin=Origin(xyz=(0.560, -0.129, 0.020), rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="wrist_cap_neg",
    )

    end_plate = model.part("end_plate")
    end_plate.visual(
        Cylinder(radius=0.043, length=0.155),
        origin=Origin(rpy=(math.pi / 2, 0.0, 0.0)),
        material=dark_bushing,
        name="wrist_barrel",
    )
    end_plate.visual(
        Box((0.225, 0.100, 0.100)),
        origin=Origin(xyz=(0.140, 0.0, 0.0)),
        material=dark_bushing,
        name="wrist_neck",
    )
    end_plate.visual(
        Box((0.050, 0.300, 0.300)),
        origin=Origin(xyz=(0.275, 0.0, 0.0)),
        material=steel,
        name="square_plate",
    )
    end_plate.visual(
        Cylinder(radius=0.018, length=0.014),
        origin=Origin(xyz=(0.306, 0.0, 0.0), rpy=(0.0, math.pi / 2, 0.0)),
        material=dark_bushing,
        name="center_boss",
    )
    for idx, (y, z) in enumerate(((-0.095, -0.095), (0.095, -0.095), (-0.095, 0.095), (0.095, 0.095))):
        end_plate.visual(
            Cylinder(radius=0.014, length=0.012),
            origin=Origin(xyz=(0.306, y, z), rpy=(0.0, math.pi / 2, 0.0)),
            material=bolt_metal,
            name=f"plate_bolt_{idx}",
        )

    shoulder = model.articulation(
        "shoulder_pivot",
        ArticulationType.REVOLUTE,
        parent=wall_mount,
        child=first_link,
        origin=Origin(),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=450.0, velocity=0.7, lower=-0.65, upper=0.95),
    )
    elbow = model.articulation(
        "elbow_pivot",
        ArticulationType.REVOLUTE,
        parent=first_link,
        child=second_link,
        origin=Origin(xyz=(0.820, 0.0, -0.120)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=330.0, velocity=0.8, lower=-1.15, upper=1.15),
    )
    wrist = model.articulation(
        "wrist_pivot",
        ArticulationType.REVOLUTE,
        parent=second_link,
        child=end_plate,
        origin=Origin(xyz=(0.560, 0.0, 0.020)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=120.0, velocity=1.2, lower=-0.75, upper=0.75),
    )

    # Keep local names referenced so linters do not treat the joints as unused;
    # the returned model stores them for the compiler and tests.
    _ = (shoulder, elbow, wrist)
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
