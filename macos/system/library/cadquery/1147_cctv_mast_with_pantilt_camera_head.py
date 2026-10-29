# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cctv_mast_with_pantilt_camera_head, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cctv_mast_with_pantilt_camera_head

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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """CadQuery rounded rectangular solid centered on the origin."""
    return cq.Workplane("XY").box(*size).edges().fillet(radius)
def _pan_yoke_mesh() -> cq.Workplane:
    """Connected rotating turntable, gearbox deck, and bored tilt yoke."""
    turntable = cq.Workplane("XY").cylinder(0.070, 0.120).translate((0.0, 0.0, 0.035))
    deck = (
        cq.Workplane("XY")
        .box(0.34, 0.34, 0.035)
        .edges("|Z")
        .fillet(0.018)
        .translate((0.10, 0.0, 0.0875))
    )

    # Two thick cheek plates flank the camera.  A bridge at the rear turns the
    # cheeks into one cast/bolted yoke, while the holes leave real clearance for
    # the camera trunnion.
    cheek_0 = (
        cq.Workplane("XY")
        .box(0.11, 0.034, 0.31)
        .edges("|Z")
        .fillet(0.010)
        .translate((0.16, 0.153, 0.250))
    )
    cheek_1 = cheek_0.mirror("XZ")
    rear_bridge = (
        cq.Workplane("XY")
        .box(0.060, 0.340, 0.230)
        .edges("|Z")
        .fillet(0.010)
        .translate((0.075, 0.0, 0.235))
    )
    bearing_0 = (
        cq.Workplane("XZ")
        .center(0.16, 0.285)
        .circle(0.045)
        .extrude(0.044, both=True)
        .translate((0.0, 0.153, 0.0))
    )
    bearing_1 = bearing_0.mirror("XZ")

    yoke = (
        turntable.union(deck)
        .union(cheek_0)
        .union(cheek_1)
        .union(rear_bridge)
        .union(bearing_0)
        .union(bearing_1)
    )
    bore = cq.Workplane("XZ").center(0.16, 0.285).circle(0.030).extrude(0.50, both=True)
    return yoke.cut(bore)
def _camera_body_mesh() -> cq.Workplane:
    """Weatherproof camera body with molded rear cap and forward lens barrel."""
    body = _rounded_box((0.38, 0.190, 0.165), 0.018).translate((0.210, 0.0, 0.0))
    rear_cap = (
        _rounded_box((0.055, 0.185, 0.155), 0.012)
        .translate((-0.005, 0.0, 0.0))
    )
    nose = (
        cq.Workplane("YZ")
        .circle(0.085)
        .extrude(0.060)
        .translate((0.400, 0.0, 0.0))
    )
    lower_heat_sink = (
        cq.Workplane("XY")
        .box(0.250, 0.160, 0.020)
        .edges("|Z")
        .fillet(0.006)
        .translate((0.205, 0.0, -0.092))
    )
    return body.union(rear_cap).union(nose).union(lower_heat_sink)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cctv_mast_pan_tilt")

    galvanized = model.material(name="galvanized_steel", rgba=(0.56, 0.58, 0.56, 1.0))
    dark_steel = model.material(name="dark_powder_coat", rgba=(0.05, 0.055, 0.055, 1.0))
    warm_gray = model.material(name="warm_gray_enclosure", rgba=(0.74, 0.75, 0.71, 1.0))
    black = model.material(name="black_rubber", rgba=(0.01, 0.011, 0.012, 1.0))
    glass = model.material(name="smoked_glass", rgba=(0.02, 0.04, 0.055, 0.78))
    cable_mat = model.material(name="matte_black_cable", rgba=(0.0, 0.0, 0.0, 1.0))
    warning_yellow = model.material(name="warning_label_yellow", rgba=(0.95, 0.78, 0.10, 1.0))

    mast = model.part("mast")
    mast.visual(
        Cylinder(radius=0.32, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
        material=galvanized,
        name="base_plate",
    )
    mast.visual(
        Cylinder(radius=0.070, length=2.420),
        origin=Origin(xyz=(0.0, 0.0, 1.250)),
        material=galvanized,
        name="support_pole",
    )
    mast.visual(
        Cylinder(radius=0.130, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 2.485)),
        material=galvanized,
        name="top_flange",
    )

    # Four anchor studs, nuts, and pole gussets make the base read as an
    # installed outdoor mast rather than a decorative stand.
    for index, (x, y) in enumerate(((0.225, 0.225), (-0.225, 0.225), (-0.225, -0.225), (0.225, -0.225))):
        mast.visual(
            Cylinder(radius=0.014, length=0.070),
            origin=Origin(xyz=(x, y, 0.075)),
            material=dark_steel,
            name=f"anchor_stud_{index}",
        )
        mast.visual(
            Cylinder(radius=0.030, length=0.020),
            origin=Origin(xyz=(x, y, 0.050)),
            material=dark_steel,
            name=f"anchor_nut_{index}",
        )

    for index, yaw in enumerate((0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0)):
        mast.visual(
            Box((0.018, 0.185, 0.270)),
            origin=Origin(xyz=(0.0, 0.090, 0.165), rpy=(0.0, 0.0, yaw)),
            material=galvanized,
            name=f"base_gusset_{index}",
        )

    mast.visual(
        Box((0.105, 0.230, 0.320)),
        origin=Origin(xyz=(-0.1225, 0.0, 1.050)),
        material=warm_gray,
        name="service_box",
    )
    mast.visual(
        Box((0.014, 0.200, 0.285)),
        origin=Origin(xyz=(-0.1820, 0.0, 1.050)),
        material=galvanized,
        name="service_door_panel",
    )
    mast.visual(
        Box((0.010, 0.030, 0.090)),
        origin=Origin(xyz=(-0.191, 0.100, 1.050)),
        material=dark_steel,
        name="service_latch",
    )
    mast.visual(
        Box((0.011, 0.120, 0.045)),
        origin=Origin(xyz=(-0.1915, -0.020, 1.155)),
        material=warning_yellow,
        name="surveillance_label",
    )

    # A real installation needs weatherproof cabling.  The conduit runs up the
    # back of the pole and is tied to it by metal straps.
    mast.visual(
        Cylinder(radius=0.011, length=1.250),
        origin=Origin(xyz=(-0.095, 0.0, 1.725)),
        material=cable_mat,
        name="vertical_conduit",
    )
    for index, z in enumerate((1.240, 1.620, 2.000, 2.360)):
        mast.visual(
            Box((0.055, 0.035, 0.030)),
            origin=Origin(xyz=(-0.071, 0.0, z)),
            material=dark_steel,
            name=f"conduit_strap_{index}",
        )
    mast.visual(
        Cylinder(radius=0.012, length=0.155),
        origin=Origin(xyz=(-0.110, 0.0, 1.225), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=cable_mat,
        name="box_cable_gland",
    )

    pan_base = model.part("pan_base")
    pan_base.visual(
        mesh_from_cadquery(_pan_yoke_mesh(), "pan_yoke"),
        material=galvanized,
        name="pan_yoke",
    )
    pan_base.visual(
        Box((0.055, 0.030, 0.040)),
        origin=Origin(xyz=(-0.070, 0.0, 0.125)),
        material=black,
        name="cable_exit_gland",
    )

    camera = model.part("camera")
    camera.visual(
        mesh_from_cadquery(_camera_body_mesh(), "camera_housing"),
        material=warm_gray,
        name="housing",
    )
    camera.visual(
        Box((0.455, 0.245, 0.026)),
        origin=Origin(xyz=(0.215, 0.0, 0.095)),
        material=warm_gray,
        name="sun_shield_top",
    )
    camera.visual(
        Box((0.345, 0.020, 0.075)),
        origin=Origin(xyz=(0.315, 0.122, 0.062)),
        material=warm_gray,
        name="sun_shield_side_0",
    )
    camera.visual(
        Box((0.345, 0.020, 0.075)),
        origin=Origin(xyz=(0.315, -0.122, 0.062)),
        material=warm_gray,
        name="sun_shield_side_1",
    )
    camera.visual(
        Cylinder(radius=0.070, length=0.115),
        origin=Origin(xyz=(0.495, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="lens_barrel",
    )
    camera.visual(
        Cylinder(radius=0.057, length=0.010),
        origin=Origin(xyz=(0.557, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_glass",
    )
    camera.visual(
        Cylinder(radius=0.030, length=0.335),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_steel,
        name="trunnion_pin",
    )
    for index, y in enumerate((-0.045, 0.0, 0.045)):
        camera.visual(
            Sphere(radius=0.012),
            origin=Origin(xyz=(0.557, y, -0.050)),
            material=glass,
            name=f"ir_led_{index}",
        )

    model.articulation(
        "mast_to_pan",
        ArticulationType.REVOLUTE,
        parent=mast,
        child=pan_base,
        origin=Origin(xyz=(0.0, 0.0, 2.510)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=85.0, velocity=1.2, lower=-2.90, upper=2.90),
        motion_properties=MotionProperties(damping=0.4, friction=0.12),
    )

    model.articulation(
        "pan_to_camera",
        ArticulationType.REVOLUTE,
        parent=pan_base,
        child=camera,
        origin=Origin(xyz=(0.160, 0.0, 0.285)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=35.0, velocity=0.8, lower=-0.70, upper=0.65),
        motion_properties=MotionProperties(damping=0.25, friction=0.08),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
