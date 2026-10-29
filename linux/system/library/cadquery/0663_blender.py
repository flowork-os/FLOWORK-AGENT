# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blender, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blender

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
def _annular_cylinder(
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    z_min: float,
) -> cq.Workplane:
    """A hollow cylindrical ring authored directly in model coordinates."""
    outer = cq.Workplane("XY").circle(outer_radius).extrude(length)
    cutter = (
        cq.Workplane("XY")
        .circle(inner_radius)
        .extrude(length + 0.004)
        .translate((0.0, 0.0, -0.002))
    )
    return outer.cut(cutter).translate((0.0, 0.0, z_min))
def _shaft_foot_guard() -> cq.Workplane:
    """Stainless bell guard: open side struts and a bottom annular rim."""
    guard = _annular_cylinder(
        outer_radius=0.045,
        inner_radius=0.032,
        length=0.012,
        z_min=-0.362,
    )

    upper_boss = (
        cq.Workplane("XY")
        .circle(0.020)
        .extrude(0.030)
        .translate((0.0, 0.0, -0.302))
    )
    guard = guard.union(upper_boss)

    # Four arched-looking vertical cage ribs welded between the upper boss and
    # bottom rim.  They deliberately leave large windows so the cutter is seen.
    for angle in (45.0, 135.0, 225.0, 315.0):
        rib = (
            cq.Workplane("XY")
            .box(0.026, 0.010, 0.066)
            .translate((0.031, 0.0, -0.324))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        guard = guard.union(rib)

    return guard
def _blade_rotor() -> cq.Workplane:
    """Four sharpened, pitched triangular blades fused to a central hub."""
    rotor = cq.Workplane("XY").circle(0.010).extrude(0.014).translate((0, 0, -0.007))

    base_blade = (
        cq.Workplane("XY")
        .polyline(
            [
                (0.003, -0.006),
                (0.032, -0.010),
                (0.041, -0.001),
                (0.012, 0.009),
            ]
        )
        .close()
        .extrude(0.002)
        .translate((0.0, 0.0, -0.001))
    )

    for index, angle in enumerate((0.0, 90.0, 180.0, 270.0)):
        pitch = 13.0 if index % 2 == 0 else -13.0
        blade = (
            base_blade.rotate((0, 0, 0), (1, 0, 0), pitch)
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        rotor = rotor.union(blade)

    return rotor
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="immersion_hand_blender")

    white_plastic = model.material("warm_white_plastic", rgba=(0.92, 0.91, 0.86, 1.0))
    dark_rubber = model.material("charcoal_rubber", rgba=(0.04, 0.045, 0.05, 1.0))
    black_plastic = model.material("black_plastic", rgba=(0.01, 0.01, 0.012, 1.0))
    stainless = model.material("brushed_stainless", rgba=(0.73, 0.75, 0.74, 1.0))
    blade_steel = model.material("sharp_blade_steel", rgba=(0.86, 0.88, 0.88, 1.0))

    motor_handle = model.part("motor_handle")
    # Main motor housing: a realistic hand-sized cylindrical body.
    motor_handle.visual(
        Cylinder(radius=0.041, length=0.245),
        origin=Origin(xyz=(0.0, 0.0, 0.1375)),
        material=white_plastic,
        name="motor_body",
    )
    motor_handle.visual(
        Sphere(radius=0.041),
        origin=Origin(xyz=(0.0, 0.0, 0.260)),
        material=white_plastic,
        name="rounded_top",
    )
    motor_handle.visual(
        Cylinder(radius=0.043, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
        material=dark_rubber,
        name="grip_band",
    )
    motor_handle.visual(
        Cylinder(radius=0.043, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.218)),
        material=dark_rubber,
        name="upper_grip_band",
    )
    motor_handle.visual(
        mesh_from_cadquery(
            _annular_cylinder(outer_radius=0.035, inner_radius=0.022, length=0.050, z_min=-0.035),
            "socket_collar",
        ),
        material=black_plastic,
        name="socket_collar",
    )
    motor_handle.visual(
        Cylinder(radius=0.006, length=0.052),
        origin=Origin(xyz=(0.0, -0.046, 0.225), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_rubber,
        name="trigger_pivot_socket",
    )
    motor_handle.visual(
        Box((0.020, 0.004, 0.030)),
        origin=Origin(xyz=(0.0, -0.041, 0.175)),
        material=dark_rubber,
        name="trigger_recess",
    )
    # Bayonet slot marks on the collar show the twist-lock direction.
    motor_handle.visual(
        Box((0.020, 0.003, 0.006)),
        origin=Origin(xyz=(0.0, -0.036, -0.014)),
        material=white_plastic,
        name="lock_slot_mark",
    )
    motor_handle.visual(
        Box((0.004, 0.003, 0.018)),
        origin=Origin(xyz=(0.012, -0.036, -0.006)),
        material=white_plastic,
        name="lock_stop_mark",
    )

    shaft = model.part("shaft")
    # The top plug enters the hollow socket collar; small lugs underneath make
    # the bayonet/twist-lock readable without blocking the revolute motion.
    shaft.visual(
        Cylinder(radius=0.019, length=0.055),
        origin=Origin(xyz=(0.0, 0.0, -0.0175)),
        material=black_plastic,
        name="shaft_plug",
    )
    for angle, name in ((0.0, "lock_lug_0"), (math.pi, "lock_lug_1")):
        shaft.visual(
            Box((0.014, 0.008, 0.006)),
            origin=Origin(
                xyz=(0.026 * math.cos(angle), 0.026 * math.sin(angle), -0.038),
                rpy=(0.0, 0.0, angle),
            ),
            material=black_plastic,
            name=name,
        )
    shaft.visual(
        Cylinder(radius=0.011, length=0.285),
        origin=Origin(xyz=(0.0, 0.0, -0.170)),
        material=stainless,
        name="steel_tube",
    )
    shaft.visual(
        Cylinder(radius=0.006, length=0.028),
        origin=Origin(xyz=(0.0, 0.0, -0.314)),
        material=stainless,
        name="blade_axle_bearing",
    )
    shaft.visual(
        mesh_from_cadquery(_shaft_foot_guard(), "foot_guard"),
        material=stainless,
        name="foot_guard",
    )

    blade_rotor = model.part("blade_rotor")
    blade_rotor.visual(
        mesh_from_cadquery(_blade_rotor(), "blade_set", tolerance=0.0005),
        material=blade_steel,
        name="blade_set",
    )
    blade_rotor.visual(
        Cylinder(radius=0.004, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=blade_steel,
        name="drive_axle",
    )

    power_trigger = model.part("power_trigger")
    power_trigger.visual(
        Cylinder(radius=0.0045, length=0.040),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black_plastic,
        name="pivot_pin",
    )
    power_trigger.visual(
        Box((0.024, 0.009, 0.095)),
        origin=Origin(xyz=(0.0, -0.004, -0.052)),
        material=dark_rubber,
        name="trigger_pad",
    )

    model.articulation(
        "handle_to_shaft",
        ArticulationType.REVOLUTE,
        parent=motor_handle,
        child=shaft,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.2, lower=-0.45, upper=0.45),
    )
    model.articulation(
        "shaft_to_blade_rotor",
        ArticulationType.CONTINUOUS,
        parent=shaft,
        child=blade_rotor,
        origin=Origin(xyz=(0.0, 0.0, -0.337)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.25, velocity=80.0),
    )
    model.articulation(
        "handle_to_power_trigger",
        ArticulationType.REVOLUTE,
        parent=motor_handle,
        child=power_trigger,
        origin=Origin(xyz=(0.0, -0.046, 0.225)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=2.0, velocity=3.0, lower=0.0, upper=0.35),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
