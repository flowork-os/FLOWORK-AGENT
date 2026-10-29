# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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
def _tube_mesh(
    name: str,
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
):
    tube = (
        cq.Workplane("XY")
        .circle(outer_radius)
        .extrude(length)
        .faces(">Z")
        .workplane()
        .circle(inner_radius)
        .cutBlind(-length)
    )
    return mesh_from_cadquery(tube, name)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_training_pump")

    frame_black = model.material("frame_black", rgba=(0.11, 0.12, 0.13, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.08, 0.08, 0.08, 1.0))
    steel = model.material("steel", rgba=(0.74, 0.76, 0.79, 1.0))
    dial = model.material("dial", rgba=(0.95, 0.95, 0.93, 1.0))
    glass = model.material("glass", rgba=(0.72, 0.80, 0.86, 0.30))
    signal_red = model.material("signal_red", rgba=(0.82, 0.12, 0.10, 1.0))

    frame = model.part("frame")
    frame.visual(
        Box((0.300, 0.105, 0.018)),
        origin=Origin(xyz=(0.000, 0.000, 0.009)),
        material=frame_black,
        name="foot",
    )
    frame.visual(
        Box((0.030, 0.040, 0.022)),
        origin=Origin(xyz=(0.000, 0.002, 0.019)),
        material=frame_black,
        name="bridge",
    )
    frame.visual(
        Cylinder(radius=0.033, length=0.028),
        origin=Origin(xyz=(0.000, 0.020, 0.053)),
        material=frame_black,
        name="barrel_collar",
    )
    frame.visual(
        _tube_mesh(
            "pump_barrel_shell",
            outer_radius=0.028,
            inner_radius=0.024,
            length=0.230,
        ),
        origin=Origin(xyz=(0.000, 0.020, 0.053)),
        material=frame_black,
        name="barrel_shell",
    )
    for index, x_pos in enumerate((-0.020, 0.020)):
        frame.visual(
            Box((0.016, 0.030, 0.070)),
            origin=Origin(xyz=(x_pos, 0.020, 0.035)),
            material=frame_black,
            name=f"strut_{index}",
        )
    frame.visual(
        Box((0.040, 0.018, 0.090)),
        origin=Origin(xyz=(0.000, 0.052, 0.045)),
        material=frame_black,
        name="rear_brace",
    )
    frame.visual(
        Cylinder(radius=0.036, length=0.022),
        origin=Origin(xyz=(0.000, -0.018, 0.019)),
        material=frame_black,
        name="gauge_housing",
    )
    frame.visual(
        Cylinder(radius=0.038, length=0.006),
        origin=Origin(xyz=(0.000, -0.018, 0.032)),
        material=frame_black,
        name="gauge_bezel",
    )
    frame.visual(
        Cylinder(radius=0.030, length=0.0016),
        origin=Origin(xyz=(0.000, -0.018, 0.0297)),
        material=dial,
        name="gauge_face",
    )
    frame.visual(
        Cylinder(radius=0.029, length=0.0026),
        origin=Origin(xyz=(0.000, -0.018, 0.0335)),
        material=glass,
        name="gauge_glass",
    )
    frame.visual(
        _tube_mesh(
            "pump_button_boss",
            outer_radius=0.008,
            inner_radius=0.0056,
            length=0.011,
        ),
        origin=Origin(
            xyz=(0.0345, -0.018, 0.020),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=frame_black,
        name="button_boss",
    )
    frame.inertial = Inertial.from_geometry(
        Box((0.300, 0.105, 0.360)),
        mass=1.8,
        origin=Origin(xyz=(0.000, 0.000, 0.180)),
    )

    rod = model.part("rod")
    rod.visual(
        Cylinder(radius=0.006, length=0.220),
        origin=Origin(xyz=(0.000, 0.000, -0.110)),
        material=steel,
        name="shaft",
    )
    rod.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.000, 0.000, -0.206)),
        material=rubber_black,
        name="piston",
    )
    rod.visual(
        Cylinder(radius=0.010, length=0.050),
        origin=Origin(xyz=(0.000, 0.000, 0.025)),
        material=steel,
        name="stem",
    )
    rod.visual(
        Cylinder(radius=0.010, length=0.200),
        origin=Origin(
            xyz=(0.000, 0.000, 0.050),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=steel,
        name="handle_bar",
    )
    for index, x_pos in enumerate((-0.070, 0.070)):
        rod.visual(
            Cylinder(radius=0.013, length=0.060),
            origin=Origin(
                xyz=(x_pos, 0.000, 0.050),
                rpy=(0.0, math.pi / 2.0, 0.0),
            ),
            material=rubber_black,
            name=f"grip_{index}",
        )
    rod.inertial = Inertial.from_geometry(
        Box((0.220, 0.030, 0.285)),
        mass=0.45,
        origin=Origin(xyz=(0.000, 0.000, -0.078)),
    )

    needle = model.part("needle")
    needle.visual(
        Cylinder(radius=0.0042, length=0.0010),
        origin=Origin(xyz=(0.000, 0.000, 0.0005)),
        material=signal_red,
        name="hub",
    )
    needle.visual(
        Box((0.022, 0.0025, 0.0008)),
        origin=Origin(xyz=(0.011, 0.000, 0.0009)),
        material=signal_red,
        name="arm",
    )
    needle.visual(
        Box((0.012, 0.0040, 0.0008)),
        origin=Origin(xyz=(0.024, 0.000, 0.0009)),
        material=signal_red,
        name="tip",
    )
    needle.visual(
        Box((0.008, 0.0018, 0.0008)),
        origin=Origin(xyz=(-0.007, 0.000, 0.0009)),
        material=signal_red,
        name="counterweight",
    )
    needle.inertial = Inertial.from_geometry(
        Box((0.036, 0.008, 0.004)),
        mass=0.01,
        origin=Origin(xyz=(0.006, 0.000, 0.001)),
    )

    button = model.part("button")
    button.visual(
        Cylinder(radius=0.0048, length=0.010),
        origin=Origin(
            xyz=(0.005, 0.000, 0.000),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=signal_red,
        name="stem",
    )
    button.visual(
        Cylinder(radius=0.0070, length=0.006),
        origin=Origin(
            xyz=(0.012, 0.000, 0.000),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=signal_red,
        name="cap",
    )
    button.inertial = Inertial.from_geometry(
        Box((0.020, 0.016, 0.016)),
        mass=0.015,
        origin=Origin(xyz=(0.010, 0.000, 0.000)),
    )

    model.articulation(
        "frame_to_rod",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=rod,
        origin=Origin(xyz=(0.000, 0.020, 0.283)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=90.0,
            velocity=0.6,
            lower=0.0,
            upper=0.170,
        ),
    )
    model.articulation(
        "frame_to_needle",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=needle,
        origin=Origin(xyz=(0.000, -0.018, 0.0308)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.05,
            velocity=8.0,
            lower=-1.15,
            upper=1.15,
        ),
    )
    model.articulation(
        "frame_to_button",
        ArticulationType.PRISMATIC,
        parent=frame,
        child=button,
        origin=Origin(xyz=(0.036, -0.018, 0.020)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=0.05,
            lower=0.0,
            upper=0.003,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
