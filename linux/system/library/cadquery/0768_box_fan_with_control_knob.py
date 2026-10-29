# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, box_fan_with_control_knob, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: box_fan_with_control_knob

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
import cadquery as cq
def make_clamp_base():
    # A C-clamp shape.
    # We will build it on the XY plane and extrude.
    # The clamp sits on the desk, so the gap is around Z=0.
    # Let's make it open towards +Y.
    # Back spine along -Y.
    # Top jaw at Z = +0.03, bottom jaw at Z = -0.03.
    # Thickness = 0.015.
    
    # Profile in YZ plane, extruded along X.
    # Let's just use boolean boxes for simplicity.
    base = cq.Workplane("XY").box(0.06, 0.08, 0.08)
    # Cut out the inner part to make a C shape.
    # The opening will be on the +Y side.
    cutout = cq.Workplane("XY").center(0, 0.015).box(0.07, 0.06, 0.05)
    base = base.cut(cutout)
    
    # Add a small cylinder boss on top for the shoulder joint.
    boss = cq.Workplane("XY").workplane(offset=0.04).cylinder(0.01, 0.02)
    base = base.union(boss)
    return base
def make_capsule(length, radius=0.01):
    return (
        cq.Workplane("XY")
        .cylinder(length, radius)
        .faces(">Z").sphere(radius)
        .faces("<Z").sphere(radius)
    )
def make_fan_head():
    # A round fan head.
    # Let's make it a cylinder along Y axis, so it faces +Y.
    head = (
        cq.Workplane("XZ")
        .cylinder(0.05, 0.06)  # radius 0.06, length 0.05 along Y
    )
    # Hollow it out slightly from the front (+Y)
    cutout = (
        cq.Workplane("XZ")
        .workplane(offset=0.005)
        .cylinder(0.05, 0.055)
    )
    head = head.cut(cutout)
    
    # Add a mounting bracket on the bottom (-Z)
    bracket = (
        cq.Workplane("XY")
        .workplane(offset=-0.06)
        .box(0.02, 0.02, 0.02)
    )
    head = head.union(bracket)
    return head
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="desk_gooseneck_usb_fan")

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(make_clamp_base(), "clamp_base_geom"),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        name="clamp_base",
    )

    # The top of the clamp base boss is at Z = 0.04 + 0.01/2 = 0.045.
    # Wait, boss is cylinder(0.01, 0.02).
    # In CadQuery, cylinder(height, radius) -> wait, cylinder signature is `cylinder(height, radius)`.
    # Let me double check CadQuery cylinder signature. It's `cylinder(distance, radius)`.
    # So `cylinder(0.01, 0.02)` means height 0.01, radius 0.02.
    # The workplane was offset=0.04. The cylinder is centered on the workplane.
    # So it goes from Z=0.035 to Z=0.045.
    # The top of the base box is at Z=0.04. So the boss sticks out to 0.045.
    
    arm_radius = 0.01
    arm_length = 0.12
    
    arm_1 = model.part("arm_1")
    # Shift the visual so the bottom end is at the part origin.
    arm_1.visual(
        mesh_from_cadquery(make_capsule(arm_length, arm_radius), "arm_1_geom"),
        origin=Origin(xyz=(0.0, 0.0, arm_length / 2)),
        name="arm_1_shell",
    )

    arm_2 = model.part("arm_2")
    arm_2.visual(
        mesh_from_cadquery(make_capsule(arm_length, arm_radius), "arm_2_geom"),
        origin=Origin(xyz=(0.0, 0.0, arm_length / 2)),
        name="arm_2_shell",
    )

    arm_3 = model.part("arm_3")
    arm_3.visual(
        mesh_from_cadquery(make_capsule(arm_length, arm_radius), "arm_3_geom"),
        origin=Origin(xyz=(0.0, 0.0, arm_length / 2)),
        name="arm_3_shell",
    )

    fan_head = model.part("fan_head")
    fan_head.visual(
        mesh_from_cadquery(make_fan_head(), "fan_head_geom"),
        # The bracket bottom is at Z = -0.07. We want the origin to be at the bracket bottom.
        # Wait, bracket is offset=-0.06, size=0.02. So it goes from -0.05 to -0.07.
        # Let's shift the visual so the origin is exactly at Z=-0.07.
        origin=Origin(xyz=(0.0, 0.0, 0.07)),
        name="fan_head_shell",
    )

    dial = model.part("fan_dial")
    dial.visual(
        Cylinder(radius=0.015, length=0.01),
        # Origin at the front face of the dial so it sits flush on the rear face.
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        name="dial_shell",
    )

    # Articulations
    # Shoulder joint: base to arm_1
    model.articulation(
        "shoulder",
        ArticulationType.REVOLUTE,
        parent=base,
        child=arm_1,
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        axis=(0.0, 1.0, 0.0), # Pitch joint
        motion_limits=MotionLimits(effort=1.0, velocity=1.0, lower=-1.0, upper=1.0),
    )

    # Elbow 1: arm_1 to arm_2
    model.articulation(
        "elbow_1",
        ArticulationType.REVOLUTE,
        parent=arm_1,
        child=arm_2,
        origin=Origin(xyz=(0.0, 0.0, arm_length)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=1.0, lower=-1.5, upper=1.5),
    )

    # Elbow 2: arm_2 to arm_3
    model.articulation(
        "elbow_2",
        ArticulationType.REVOLUTE,
        parent=arm_2,
        child=arm_3,
        origin=Origin(xyz=(0.0, 0.0, arm_length)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=1.0, lower=-1.5, upper=1.5),
    )

    # Wrist: arm_3 to fan_head
    model.articulation(
        "wrist",
        ArticulationType.REVOLUTE,
        parent=arm_3,
        child=fan_head,
        origin=Origin(xyz=(0.0, 0.0, arm_length)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=1.0, lower=-1.0, upper=1.0),
    )

    # Dial joint: fan_head to dial
    # The fan head cylinder is along Y. The rear face is at Y = -0.025.
    model.articulation(
        "dial_spin",
        ArticulationType.REVOLUTE,
        parent=fan_head,
        child=dial,
        # Place it on the rear face. The dial's origin is at its flush face.
        # So we place it at Y = -0.025, and orient it so its local Z points along -Y.
        origin=Origin(xyz=(0.0, -0.025, 0.0), rpy=(-1.5708, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.1, velocity=1.0, lower=-3.14, upper=3.14),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
