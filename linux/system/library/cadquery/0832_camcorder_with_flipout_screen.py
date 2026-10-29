# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

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
BODY_LEN = 0.300
BODY_W = 0.120
BODY_H = 0.140
BODY_SIDE_Y = BODY_W / 2.0
BODY_FRONT_X = BODY_LEN / 2.0
LENS_RING_X = 0.225
SCREEN_HINGE_X = 0.006
SCREEN_HINGE_Y = BODY_SIDE_Y + 0.006
SCREEN_OPEN_YAW = -math.radians(65.0)
SCREEN_CLOSE_Q = -SCREEN_OPEN_YAW
BUTTON_TRAVEL = 0.004
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    shape = cq.Workplane("XY").box(*size)
    if radius > 0.0:
        try:
            shape = shape.edges().fillet(radius)
        except Exception:
            # Keep the correctly scaled solid if an OCC fillet is too small or
            # has no stable edge set on the current primitive.
            pass
    return shape
def _rotate_xy(x: float, y: float, yaw: float) -> tuple[float, float]:
    c = math.cos(yaw)
    s = math.sin(yaw)
    return (x * c - y * s, x * s + y * c)
def _screen_origin(
    closed_xyz: tuple[float, float, float],
    *,
    yaw: float = SCREEN_OPEN_YAW,
) -> Origin:
    x, y = _rotate_xy(closed_xyz[0], closed_xyz[1], yaw)
    return Origin(xyz=(x, y, closed_xyz[2]), rpy=(0.0, 0.0, yaw))
def _lens_ring_geometry() -> cq.Workplane:
    """Hollow ribbed rubber sleeve, authored around local +X."""

    length = 0.056
    outer_r = 0.041
    inner_r = 0.0345
    tube = (
        cq.Workplane("YZ")
        .circle(outer_r)
        .circle(inner_r)
        .extrude(length / 2.0, both=True)
    )

    rib_count = 28
    rib_radial = 0.0035
    rib_tangent = 0.0040
    rib_length = length * 0.92
    radius = outer_r + rib_radial * 0.40
    for index in range(rib_count):
        angle = 360.0 * index / rib_count
        theta = math.radians(angle)
        y = -radius * math.sin(theta)
        z = radius * math.cos(theta)
        rib = (
            cq.Workplane("XY")
            .box(rib_length, rib_tangent, rib_radial)
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle)
            .translate((0.0, y, z))
        )
        tube = tube.union(rib)
    return tube
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="prosumer_camcorder")

    matte_black = model.material("matte_black", rgba=(0.015, 0.016, 0.018, 1.0))
    dark_plastic = model.material("dark_plastic", rgba=(0.055, 0.058, 0.064, 1.0))
    charcoal = model.material("charcoal", rgba=(0.10, 0.105, 0.112, 1.0))
    rubber = model.material("ribbed_rubber", rgba=(0.008, 0.008, 0.009, 1.0))
    lens_glass = model.material("coated_lens_glass", rgba=(0.02, 0.07, 0.095, 0.82))
    screen_glass = model.material("dark_screen_glass", rgba=(0.0, 0.012, 0.020, 1.0))
    button_blue = model.material("button_blue_gray", rgba=(0.08, 0.11, 0.135, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_rounded_box((BODY_LEN, BODY_W, BODY_H), 0.012), "main_shell"),
        material=dark_plastic,
        name="main_shell",
    )
    body.visual(
        mesh_from_cadquery(_rounded_box((0.074, 0.030, 0.116), 0.010), "handgrip"),
        origin=Origin(xyz=(0.072, BODY_SIDE_Y + 0.014, -0.006)),
        material=matte_black,
        name="handgrip",
    )
    body.visual(
        mesh_from_cadquery(_rounded_box((0.145, 0.026, 0.024), 0.006), "top_handle_bar"),
        origin=Origin(xyz=(-0.010, 0.0, BODY_H / 2.0 + 0.052)),
        material=matte_black,
        name="top_handle_bar",
    )
    for x in (-0.075, 0.050):
        body.visual(
            Box((0.020, 0.024, 0.070)),
            origin=Origin(xyz=(x, 0.0, BODY_H / 2.0 + 0.022)),
            material=matte_black,
            name=f"handle_post_{0 if x < 0 else 1}",
        )
    body.visual(
        mesh_from_cadquery(_rounded_box((0.065, 0.055, 0.035), 0.010), "viewfinder"),
        origin=Origin(xyz=(-BODY_LEN / 2.0 - 0.025, 0.0, 0.043)),
        material=matte_black,
        name="viewfinder",
    )
    body.visual(
        Box((0.118, 0.0025, 0.082)),
        origin=Origin(xyz=(-0.067, BODY_SIDE_Y + 0.0008, 0.006)),
        material=screen_glass,
        name="screen_bay",
    )
    body.visual(
        Box((0.128, 0.005, 0.094)),
        origin=Origin(xyz=(-0.067, BODY_SIDE_Y + 0.0013, 0.006)),
        material=charcoal,
        name="screen_recess_frame",
    )
    body.visual(
        Box((0.112, 0.006, 0.078)),
        origin=Origin(xyz=(-0.067, BODY_SIDE_Y + 0.0022, 0.006)),
        material=screen_glass,
        name="screen_opening",
    )

    # Deep, long front optics: static barrel pieces on the body plus a moving focus ring.
    body.visual(
        Cylinder(radius=0.055, length=0.030),
        origin=Origin(xyz=(BODY_FRONT_X + 0.014, 0.0, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=charcoal,
        name="lens_mount",
    )
    body.visual(
        Cylinder(radius=0.031, length=0.178),
        origin=Origin(xyz=(BODY_FRONT_X + 0.092, 0.0, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=matte_black,
        name="lens_barrel",
    )
    for name, x in (("rear_ring_shoulder", LENS_RING_X - 0.030), ("front_ring_shoulder", LENS_RING_X + 0.030)):
        body.visual(
            Cylinder(radius=0.042, length=0.004),
            origin=Origin(xyz=(x, 0.0, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=matte_black,
            name=name,
        )
    body.visual(
        Cylinder(radius=0.043, length=0.030),
        origin=Origin(xyz=(BODY_FRONT_X + 0.174, 0.0, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=matte_black,
        name="front_hood",
    )
    body.visual(
        Cylinder(radius=0.026, length=0.004),
        origin=Origin(xyz=(BODY_FRONT_X + 0.191, 0.0, 0.016), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=lens_glass,
        name="front_glass",
    )

    # Exposed vertical hinge knuckles mounted on the side wall for the flip-out monitor.
    for z in (-0.041, 0.047):
        body.visual(
            Cylinder(radius=0.0048, length=0.025),
            origin=Origin(xyz=(SCREEN_HINGE_X, SCREEN_HINGE_Y, z)),
            material=matte_black,
            name=f"screen_hinge_knuckle_{0 if z < 0 else 1}",
        )
        body.visual(
            Box((0.016, 0.010, 0.026)),
            origin=Origin(xyz=(SCREEN_HINGE_X, BODY_SIDE_Y + 0.0015, z)),
            material=charcoal,
            name=f"screen_hinge_boss_{0 if z < 0 else 1}",
        )

    button_xs = (-0.108, -0.073, -0.038)
    for index, x in enumerate(button_xs):
        body.visual(
            Cylinder(radius=0.0075, length=0.0015),
            origin=Origin(
                xyz=(x, BODY_SIDE_Y - 0.0008, -0.056),
                rpy=(-math.pi / 2.0, 0.0, 0.0),
            ),
            material=matte_black,
            name=f"button_socket_{index}",
        )

    ring = model.part("lens_ring")
    ring.visual(
        mesh_from_cadquery(_lens_ring_geometry(), "focus_ring", tolerance=0.0008, angular_tolerance=0.08),
        material=rubber,
        name="focus_ring",
    )
    model.articulation(
        "body_to_lens_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=ring,
        origin=Origin(xyz=(LENS_RING_X, 0.0, 0.016)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.8, velocity=8.0),
    )

    monitor = model.part("monitor")
    monitor.visual(
        Cylinder(radius=0.0040, length=0.034),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=matte_black,
        name="hinge_barrel",
    )
    monitor.visual(
        Box((0.012, 0.006, 0.076)),
        origin=_screen_origin((-0.006, 0.004, 0.004)),
        material=charcoal,
        name="hinge_leaf",
    )
    monitor.visual(
        mesh_from_cadquery(_rounded_box((0.116, 0.010, 0.078), 0.004), "monitor_panel"),
        origin=_screen_origin((-0.068, 0.009, 0.004)),
        material=charcoal,
        name="panel_shell",
    )
    monitor.visual(
        Box((0.094, 0.0020, 0.058)),
        origin=_screen_origin((-0.070, 0.0147, 0.004)),
        material=screen_glass,
        name="screen_glass",
    )
    model.articulation(
        "body_to_monitor",
        ArticulationType.REVOLUTE,
        parent=body,
        child=monitor,
        origin=Origin(xyz=(SCREEN_HINGE_X, SCREEN_HINGE_Y, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=-0.45, upper=SCREEN_CLOSE_Q),
    )

    for index, x in enumerate(button_xs):
        button = model.part(f"button_{index}")
        button.visual(
            Cylinder(radius=0.0058, length=0.0065),
            origin=Origin(xyz=(0.0, 0.00325, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
            material=button_blue,
            name="cap",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(x, BODY_SIDE_Y, -0.056)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(effort=2.0, velocity=0.12, lower=0.0, upper=BUTTON_TRAVEL),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
