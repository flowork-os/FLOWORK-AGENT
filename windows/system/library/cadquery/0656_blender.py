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
def _hollow_ring(outer_radius: float, inner_radius: float, height: float, name: str):
    """CadQuery annular cylinder, authored from z=0 to z=height."""
    return mesh_from_cadquery(
        cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(height),
        name,
        tolerance=0.0007,
        angular_tolerance=0.08,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="nutribullet_sippy_blender")

    graphite = model.material("matte_graphite", rgba=(0.05, 0.052, 0.055, 1.0))
    black = model.material("soft_black_plastic", rgba=(0.012, 0.012, 0.014, 1.0))
    chrome = model.material("brushed_chrome", rgba=(0.74, 0.72, 0.68, 1.0))
    dark_rubber = model.material("dark_rubber", rgba=(0.01, 0.01, 0.011, 1.0))
    translucent = model.material("smoky_clear_copolyester", rgba=(0.78, 0.92, 1.0, 0.34))
    cup_gray = model.material("threaded_gray_plastic", rgba=(0.30, 0.31, 0.32, 1.0))
    stainless = model.material("sharpened_stainless", rgba=(0.88, 0.88, 0.84, 1.0))
    mark_white = model.material("etched_white_marks", rgba=(0.92, 0.96, 1.0, 0.78))

    # Root: a low, puck-like Nutribullet motor base with a raised drive socket.
    base = model.part("motor_base")
    base.visual(
        Cylinder(radius=0.115, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
        material=dark_rubber,
        name="rubber_foot_disc",
    )
    base.visual(
        Cylinder(radius=0.102, length=0.078),
        origin=Origin(xyz=(0.0, 0.0, 0.047)),
        material=graphite,
        name="base_body",
    )
    base.visual(
        Cylinder(radius=0.107, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.084)),
        material=chrome,
        name="chrome_shoulder",
    )
    base.visual(
        Cylinder(radius=0.087, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.090)),
        material=black,
        name="top_plate",
    )
    base.visual(
        _hollow_ring(0.035, 0.012, 0.012, "drive_socket"),
        origin=Origin(xyz=(0.0, 0.0, 0.096)),
        material=chrome,
        name="drive_socket",
    )
    # Three low bayonet lugs inside the threaded cup mouth; they are visibly
    # attached to the drive socket and do not collide with the cup collar.
    for i in range(3):
        yaw = i * (2.0 * math.pi / 3.0)
        r = 0.025
        base.visual(
            Box((0.015, 0.008, 0.006)),
            origin=Origin(
                xyz=(r * math.cos(yaw), r * math.sin(yaw), 0.109),
                rpy=(0.0, 0.0, yaw),
            ),
            material=chrome,
            name=f"drive_lug_{i}",
        )

    # The short, squat cup is shown in blending orientation: its threaded mouth
    # is down on the base, the clear hollow jar rises above it, and a drinking
    # flip-lid sits on the upper rim for use after blending.
    cup = model.part("cup_jar")
    cup.visual(
        _hollow_ring(0.078, 0.044, 0.022, "lower_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.096)),
        material=cup_gray,
        name="lower_collar",
    )
    for i, z in enumerate((0.100, 0.107, 0.114)):
        cup.visual(
            _hollow_ring(0.081, 0.077, 0.003, f"thread_band_{i}"),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=cup_gray,
            name=f"thread_band_{i}",
        )
    cup.visual(
        _hollow_ring(0.080, 0.073, 0.164, "clear_cup_wall"),
        origin=Origin(xyz=(0.0, 0.0, 0.116)),
        material=translucent,
        name="clear_cup_wall",
    )
    cup.visual(
        _hollow_ring(0.086, 0.071, 0.016, "top_rim"),
        origin=Origin(xyz=(0.0, 0.0, 0.276)),
        material=black,
        name="top_rim",
    )
    # Measuring ticks are slightly embedded in the outer wall so they read as
    # printed markings rather than floating decals.
    for i, z in enumerate((0.145, 0.170, 0.195, 0.220, 0.245)):
        tick_len = 0.032 if i % 2 == 0 else 0.022
        cup.visual(
            Box((tick_len, 0.0025, 0.004)),
            origin=Origin(xyz=(-0.030 + tick_len / 2.0, -0.079, z)),
            material=mark_white,
            name=f"fill_mark_{i}",
        )
    # Fixed hinge knuckles molded into the cup rim.
    for i, y in enumerate((-0.050, 0.050)):
        cup.visual(
            Box((0.018, 0.018, 0.012)),
            origin=Origin(xyz=(0.079, y, 0.291)),
            material=black,
            name=f"hinge_boss_{i}",
        )
        cup.visual(
            Cylinder(radius=0.006, length=0.024),
            origin=Origin(xyz=(0.084, y, 0.297), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=black,
            name=f"rim_hinge_knuckle_{i}",
        )

    model.articulation(
        "base_to_cup",
        ArticulationType.FIXED,
        parent=base,
        child=cup,
        origin=Origin(),
    )

    # Cross blade rotor at the downward cup mouth.  It spins about the vertical
    # drive axis and is dimensioned to clear the hollow cup wall.
    blade = model.part("blade_cross")
    blade.visual(
        Cylinder(radius=0.009, length=0.023),
        origin=Origin(xyz=(0.0, 0.0, -0.008)),
        material=chrome,
        name="drive_shaft",
    )
    blade.visual(
        Cylinder(radius=0.019, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.000)),
        material=chrome,
        name="blade_hub",
    )
    blade.visual(
        Box((0.028, 0.008, 0.008)),
        origin=Origin(xyz=(0.0, 0.0, -0.023)),
        material=chrome,
        name="drive_tang",
    )
    for i, arm_name in enumerate(("blade_arm_0", "blade_arm_1", "blade_arm_2", "blade_arm_3")):
        yaw = i * (math.pi / 2.0) + math.pi / 4.0
        r = 0.033
        # Two opposing blades pitch upward, two pitch downward, like the
        # stamped cross blades in personal blender blade caps.
        pitch = 0.20 if i % 2 == 0 else -0.20
        blade.visual(
            Box((0.058, 0.014, 0.003)),
            origin=Origin(
                xyz=(r * math.cos(yaw), r * math.sin(yaw), 0.003),
                rpy=(pitch, 0.0, yaw),
            ),
            material=stainless,
            name=arm_name,
        )

    model.articulation(
        "cup_to_blade",
        ArticulationType.CONTINUOUS,
        parent=cup,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.125)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=80.0),
    )

    # A hinged flip-top drinking cap at the upper rim.  The child frame is on
    # the hinge barrel; the cap disc extends inward in local -X when closed.
    flip_lid = model.part("flip_lid")
    flip_lid.visual(
        Cylinder(radius=0.081, length=0.010),
        origin=Origin(xyz=(-0.084, 0.0, 0.0005)),
        material=black,
        name="lid_disc",
    )
    flip_lid.visual(
        Cylinder(radius=0.006, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="hinge_barrel",
    )
    flip_lid.visual(
        Box((0.045, 0.026, 0.018)),
        origin=Origin(xyz=(-0.130, 0.0, 0.010)),
        material=black,
        name="sip_spout",
    )
    flip_lid.visual(
        Box((0.030, 0.018, 0.002)),
        origin=Origin(xyz=(-0.130, 0.0, 0.020)),
        material=dark_rubber,
        name="spout_slot",
    )
    flip_lid.visual(
        Box((0.018, 0.040, 0.006)),
        origin=Origin(xyz=(-0.162, 0.0, 0.000)),
        material=cup_gray,
        name="thumb_tab",
    )

    model.articulation(
        "cup_to_flip_lid",
        ArticulationType.REVOLUTE,
        parent=cup,
        child=flip_lid,
        origin=Origin(xyz=(0.084, 0.0, 0.297)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=3.0, lower=0.0, upper=1.70),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
