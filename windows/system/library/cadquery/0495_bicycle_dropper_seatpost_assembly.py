# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_dropper_seatpost_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_dropper_seatpost_assembly

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
def _annular_tube(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """Hollow round tube with open bore along local +Z, authored in meters."""
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(length)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="wireless_dropper_seatpost")

    dark_anodized = model.material("dark_anodized", rgba=(0.015, 0.016, 0.017, 1.0))
    satin_black = model.material("satin_black", rgba=(0.02, 0.022, 0.025, 1.0))
    frame_gray = model.material("frame_gray", rgba=(0.12, 0.13, 0.14, 1.0))
    polished = model.material("polished_steel", rgba=(0.72, 0.70, 0.66, 1.0))
    stanchion = model.material("black_stanchion", rgba=(0.03, 0.032, 0.034, 1.0))
    blue_led = model.material("blue_status_led", rgba=(0.0, 0.35, 1.0, 1.0))

    outer_tube = model.part("outer_tube")

    # Bike frame references: a hollow seat tube and clamp show the dropper
    # inserted into and clamped by the frame, while also carrying the handlebar
    # remote so the wireless assembly is not floating.
    outer_tube.visual(
        mesh_from_cadquery(_annular_tube(0.023, 0.0168, 0.38), "frame_seat_tube"),
        origin=Origin(xyz=(0.0, 0.0, -0.11)),
        material=frame_gray,
        name="frame_seat_tube",
    )
    outer_tube.visual(
        mesh_from_cadquery(_annular_tube(0.027, 0.0155, 0.044), "seat_clamp_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.245)),
        material=satin_black,
        name="seat_clamp_collar",
    )
    outer_tube.visual(
        Box((0.034, 0.014, 0.030)),
        origin=Origin(xyz=(0.0, -0.030, 0.267)),
        material=satin_black,
        name="clamp_split_lug",
    )
    outer_tube.visual(
        Cylinder(radius=0.0035, length=0.052),
        origin=Origin(xyz=(0.0, -0.037, 0.267), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=polished,
        name="clamp_bolt",
    )

    # The stationary lower post is a true hollow round sleeve.  Its through bore
    # gives the moving inner stanchion real radial clearance instead of relying
    # on an overlap allowance.
    outer_tube.visual(
        mesh_from_cadquery(_annular_tube(0.0159, 0.0134, 0.34), "outer_sleeve_shell"),
        origin=Origin(xyz=(0.0, 0.0, 0.05)),
        material=dark_anodized,
        name="outer_sleeve_shell",
    )
    outer_tube.visual(
        mesh_from_cadquery(_annular_tube(0.0190, 0.0128, 0.018), "wiper_seal"),
        origin=Origin(xyz=(0.0, 0.0, 0.385)),
        material=satin_black,
        name="wiper_seal",
    )
    outer_tube.visual(
        Box((0.018, 0.010, 0.074)),
        origin=Origin(xyz=(-0.019, 0.0, 0.255)),
        material=satin_black,
        name="electronics_pod",
    )
    outer_tube.visual(
        Sphere(radius=0.0025),
        origin=Origin(xyz=(-0.024, 0.0, 0.277)),
        material=blue_led,
        name="status_led",
    )

    # Simplified bicycle frame/handlebar support for the wireless remote.
    outer_tube.visual(
        Cylinder(radius=0.014, length=0.55),
        origin=Origin(xyz=(0.310, 0.0, 0.220), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=frame_gray,
        name="top_tube",
    )
    outer_tube.visual(
        Box((0.052, 0.028, 0.028)),
        origin=Origin(xyz=(0.045, 0.0, 0.220)),
        material=frame_gray,
        name="top_tube_gusset",
    )
    outer_tube.visual(
        Cylinder(radius=0.018, length=0.18),
        origin=Origin(xyz=(0.55, 0.0, 0.310)),
        material=frame_gray,
        name="head_tube",
    )
    outer_tube.visual(
        Cylinder(radius=0.011, length=0.19),
        origin=Origin(xyz=(0.55, 0.0, 0.475)),
        material=frame_gray,
        name="stem",
    )
    outer_tube.visual(
        Cylinder(radius=0.011, length=0.62),
        origin=Origin(xyz=(0.55, 0.0, 0.570), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=frame_gray,
        name="handlebar",
    )
    outer_tube.visual(
        mesh_from_cadquery(_annular_tube(0.017, 0.0106, 0.026), "remote_bar_clamp"),
        origin=Origin(xyz=(0.55, -0.193, 0.570), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=satin_black,
        name="remote_bar_clamp",
    )
    outer_tube.visual(
        Box((0.042, 0.024, 0.018)),
        origin=Origin(xyz=(0.538, -0.180, 0.548)),
        material=satin_black,
        name="remote_body",
    )
    for i, y in enumerate((-0.1955, -0.1645)):
        outer_tube.visual(
            Box((0.024, 0.012, 0.024)),
            origin=Origin(xyz=(0.510, y, 0.536)),
            material=satin_black,
            name=f"remote_yoke_{i}",
        )
    outer_tube.visual(
        Cylinder(radius=0.0045, length=0.030),
        origin=Origin(xyz=(0.505, -0.180, 0.530), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=polished,
        name="remote_pivot_pin",
    )

    inner_tube = model.part("inner_tube")
    inner_tube.visual(
        Cylinder(radius=0.0121, length=0.510),
        origin=Origin(xyz=(0.0, 0.0, 0.035)),
        material=stanchion,
        name="inner_stanchion",
    )
    inner_tube.visual(
        Cylinder(radius=0.017, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.300)),
        material=dark_anodized,
        name="saddle_clamp_head",
    )
    inner_tube.visual(
        Box((0.052, 0.034, 0.014)),
        origin=Origin(xyz=(0.0, 0.0, 0.318)),
        material=dark_anodized,
        name="rail_cradle",
    )
    for y in (-0.014, 0.014):
        inner_tube.visual(
            Cylinder(radius=0.0027, length=0.150),
            origin=Origin(xyz=(0.0, y, 0.327), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=polished,
            name=f"saddle_rail_{0 if y < 0 else 1}",
        )
    inner_tube.visual(
        Box((0.070, 0.050, 0.012)),
        origin=Origin(xyz=(0.0, 0.0, 0.334)),
        material=satin_black,
        name="saddle_base_pad",
    )

    remote_lever = model.part("remote_lever")
    remote_lever.visual(
        Cylinder(radius=0.0065, length=0.018),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=satin_black,
        name="lever_boss",
    )
    remote_lever.visual(
        Box((0.018, 0.014, 0.016)),
        origin=Origin(xyz=(-0.010, 0.0, -0.006)),
        material=satin_black,
        name="lever_root_web",
    )
    remote_lever.visual(
        Box((0.074, 0.012, 0.006)),
        origin=Origin(xyz=(-0.047, 0.0, -0.014)),
        material=satin_black,
        name="lever_blade",
    )
    remote_lever.visual(
        Box((0.028, 0.018, 0.008)),
        origin=Origin(xyz=(-0.085, 0.0, -0.015)),
        material=satin_black,
        name="thumb_paddle",
    )

    model.articulation(
        "outer_to_inner",
        ArticulationType.PRISMATIC,
        parent=outer_tube,
        child=inner_tube,
        origin=Origin(xyz=(0.0, 0.0, 0.403)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=160.0, velocity=0.35, lower=0.0, upper=0.125),
    )
    model.articulation(
        "remote_hinge",
        ArticulationType.REVOLUTE,
        parent=outer_tube,
        child=remote_lever,
        origin=Origin(xyz=(0.505, -0.180, 0.530)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=6.0, lower=0.0, upper=0.55),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
