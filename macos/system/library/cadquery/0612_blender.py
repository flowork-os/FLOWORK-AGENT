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
def _ring(outer_radius: float, inner_radius: float, height: float, z: float = 0.0):
    """CadQuery annular cylinder spanning z..z+height."""
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
def _cup_shell():
    bottom = cq.Workplane("XY").circle(0.085).extrude(0.008)
    wall = _ring(0.085, 0.079, 0.137, z=0.008)
    return bottom.union(wall)
def _socket_ring():
    # A stepped bayonet receiver: a wide shallow recess above a smaller bore.
    rim_deck = _ring(0.085, 0.056, 0.006, z=0.141)
    outer_wall = _ring(0.058, 0.052, 0.042, z=0.143)
    lower_shelf = _ring(0.052, 0.034, 0.010, z=0.143)
    return rim_deck.union(outer_wall).union(lower_shelf)
def _lock_flange():
    return _ring(0.057, 0.020, 0.006, z=0.0)
def _lock_sleeve():
    sleeve = _ring(0.031, 0.020, 0.032, z=-0.032)
    tab_a = cq.Workplane("XY").box(0.020, 0.010, 0.008).translate((0.038, 0.0, -0.014))
    tab_b = cq.Workplane("XY").box(0.020, 0.010, 0.008).translate((-0.038, 0.0, -0.014))
    return sleeve.union(tab_a).union(tab_b)
def _guard_cage():
    bottom_hoop = _ring(0.047, 0.039, 0.010, z=-0.135)
    center_boss = cq.Workplane("XY").circle(0.016).extrude(0.014).translate((0.0, 0.0, -0.122))
    shape = bottom_hoop.union(center_boss)
    for angle in (0.0, 90.0, 180.0, 270.0):
        spoke = (
            cq.Workplane("XY")
            .box(0.060, 0.006, 0.006)
            .translate((0.026, 0.0, -0.114))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        post = (
            cq.Workplane("XY")
            .box(0.006, 0.006, 0.024)
            .translate((0.043, 0.0, -0.123))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        shape = shape.union(spoke).union(post)
    return shape
def _blade_star():
    hub = cq.Workplane("XY").circle(0.008).extrude(0.015).translate((0.0, 0.0, -0.006))
    blade_profile = [(0.004, -0.004), (0.036, -0.011), (0.033, 0.006), (0.004, 0.005)]
    shape = hub
    for angle in (0.0, 120.0, 240.0):
        blade = (
            cq.Workplane("XY")
            .polyline(blade_profile)
            .close()
            .extrude(0.0025)
            .translate((0.0, 0.0, -0.00125))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        shape = shape.union(blade)
    return shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="smoothie_blender_wand")

    clear_plastic = model.material("clear_plastic", rgba=(0.65, 0.90, 1.0, 0.35))
    white_plastic = model.material("white_plastic", rgba=(0.93, 0.94, 0.91, 1.0))
    soft_gray = model.material("soft_gray", rgba=(0.42, 0.45, 0.47, 1.0))
    dark_gray = model.material("dark_gray", rgba=(0.08, 0.09, 0.10, 1.0))
    stainless = model.material("stainless", rgba=(0.70, 0.72, 0.72, 1.0))
    blade_metal = model.material("blade_metal", rgba=(0.90, 0.92, 0.95, 1.0))

    base_cup = model.part("base_cup")
    base_cup.visual(
        mesh_from_cadquery(_cup_shell(), "round_cup_shell", tolerance=0.0012),
        material=clear_plastic,
        name="cup_shell",
    )
    base_cup.visual(
        mesh_from_cadquery(_socket_ring(), "twist_socket_ring", tolerance=0.001),
        material=soft_gray,
        name="socket_ring",
    )
    base_cup.visual(
        Cylinder(radius=0.091, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=dark_gray,
        name="foot_ring",
    )

    lock_slide = model.part("lock_slide")
    lock_slide.visual(
        mesh_from_cadquery(_lock_flange(), "press_lock_flange", tolerance=0.0008),
        material=dark_gray,
        name="flange",
    )
    lock_slide.visual(
        mesh_from_cadquery(_lock_sleeve(), "press_lock_sleeve", tolerance=0.0008),
        material=dark_gray,
        name="sleeve_tabs",
    )

    wand_body = model.part("wand_body")
    wand_body.visual(
        Cylinder(radius=0.035, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=white_plastic,
        name="lock_collar",
    )
    wand_body.visual(
        Cylinder(radius=0.030, length=0.240),
        origin=Origin(xyz=(0.0, 0.0, 0.140)),
        material=white_plastic,
        name="motor_tube",
    )
    wand_body.visual(
        Sphere(radius=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.260)),
        material=white_plastic,
        name="rounded_cap",
    )
    wand_body.visual(
        Cylinder(radius=0.031, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
        material=soft_gray,
        name="lower_grip_band",
    )
    wand_body.visual(
        Cylinder(radius=0.031, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.205)),
        material=soft_gray,
        name="upper_grip_band",
    )
    wand_body.visual(
        Cylinder(radius=0.013, length=0.110),
        origin=Origin(xyz=(0.0, 0.0, -0.055)),
        material=stainless,
        name="wand_shaft",
    )
    wand_body.visual(
        mesh_from_cadquery(_guard_cage(), "blade_guard_cage", tolerance=0.0008),
        material=stainless,
        name="guard_cage",
    )

    blade = model.part("blade")
    blade.visual(
        mesh_from_cadquery(_blade_star(), "tri_blade_star", tolerance=0.0005),
        material=blade_metal,
        name="blade_star",
    )

    model.articulation(
        "base_to_lock_slide",
        ArticulationType.PRISMATIC,
        parent=base_cup,
        child=lock_slide,
        origin=Origin(xyz=(0.0, 0.0, 0.185)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=35.0, velocity=0.08, lower=0.0, upper=0.018),
    )
    model.articulation(
        "lock_slide_to_wand",
        ArticulationType.REVOLUTE,
        parent=lock_slide,
        child=wand_body,
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=6.0, velocity=1.0, lower=0.0, upper=math.radians(75.0)),
    )
    model.articulation(
        "wand_to_blade",
        ArticulationType.CONTINUOUS,
        parent=wand_body,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, -0.130)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.8, velocity=80.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
