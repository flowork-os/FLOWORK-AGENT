# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
FOCUS_RING_CENTER_X = 0.105
FOCUS_RING_WIDTH = 0.038
COLLAR_CENTER_X = 0.204
COLLAR_WIDTH = 0.024
def _x_cylinder(x_start: float, length: float, radius: float) -> cq.Workplane:
    return cq.Workplane("YZ").workplane(offset=x_start).circle(radius).extrude(length)
def _body_shape() -> cq.Workplane:
    focus_left_edge = FOCUS_RING_CENTER_X - (FOCUS_RING_WIDTH * 0.5)
    focus_right_edge = FOCUS_RING_CENTER_X + (FOCUS_RING_WIDTH * 0.5)
    collar_left_edge = COLLAR_CENTER_X - (COLLAR_WIDTH * 0.5)
    collar_right_edge = COLLAR_CENTER_X + (COLLAR_WIDTH * 0.5)

    body = _x_cylinder(0.000, 0.008, 0.0425)
    body = body.union(_x_cylinder(0.008, 0.030, 0.0410))
    body = body.union(_x_cylinder(0.038, 0.034, 0.0430))
    body = body.union(_x_cylinder(0.072, 0.066, 0.0445))
    body = body.union(_x_cylinder(0.138, 0.028, 0.0470))
    body = body.union(_x_cylinder(0.166, 0.016, 0.0510))
    body = body.union(_x_cylinder(0.182, 0.058, 0.0545))
    body = body.union(_x_cylinder(0.240, 0.016, 0.0580))
    body = body.union(_x_cylinder(focus_left_edge - 0.004, 0.004, 0.0462))
    body = body.union(_x_cylinder(focus_right_edge, 0.004, 0.0462))
    body = body.union(_x_cylinder(collar_left_edge - 0.004, 0.004, 0.0562))
    body = body.union(_x_cylinder(collar_right_edge, 0.004, 0.0562))

    front_bore = _x_cylinder(0.208, 0.048, 0.0430)
    front_recess = _x_cylinder(0.226, 0.030, 0.0465)
    rear_socket = _x_cylinder(0.000, 0.010, 0.0200)

    return body.cut(front_bore).cut(front_recess).cut(rear_socket)
def _geared_ring_shape(
    *,
    width: float,
    inner_radius: float,
    ring_radius: float,
    tooth_height: float,
    tooth_depth: float,
    tooth_count: int,
) -> cq.Workplane:
    ring = (
        cq.Workplane("YZ")
        .circle(ring_radius)
        .circle(inner_radius)
        .extrude(width / 2.0, both=True)
    )

    tooth_radius = ring_radius + (tooth_height * 0.5)
    for index in range(tooth_count):
        angle_deg = 360.0 * index / tooth_count
        tooth = (
            cq.Workplane("XY")
            .box(width, tooth_depth, tooth_height, centered=(True, True, True))
            .translate((0.0, 0.0, tooth_radius))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
        )
        ring = ring.union(tooth)
    return ring
def _orientation_collar_shape() -> cq.Workplane:
    collar = (
        cq.Workplane("YZ")
        .circle(0.0615)
        .circle(0.0558)
        .extrude(COLLAR_WIDTH / 2.0, both=True)
    )
    collar = collar.union(
        cq.Workplane("YZ")
        .circle(0.0635)
        .circle(0.0605)
        .extrude(0.0035, both=True)
        .translate((COLLAR_WIDTH * 0.5 - 0.0035, 0.0, 0.0))
    )
    collar = collar.union(
        cq.Workplane("YZ")
        .circle(0.0635)
        .circle(0.0605)
        .extrude(0.0035, both=True)
        .translate((-COLLAR_WIDTH * 0.5 + 0.0035, 0.0, 0.0))
    )

    rib_radius = 0.0624
    for index in range(32):
        angle_deg = 360.0 * index / 32.0
        rib = (
            cq.Workplane("XY")
            .box(COLLAR_WIDTH * 0.82, 0.0032, 0.0028, centered=(True, True, True))
            .translate((0.0, 0.0, rib_radius))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg)
        )
        collar = collar.union(rib)
    return collar
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cine_anamorphic_lens")

    barrel_black = model.material("barrel_black", rgba=(0.08, 0.08, 0.09, 1.0))
    ring_black = model.material("ring_black", rgba=(0.12, 0.12, 0.13, 1.0))
    trim_gray = model.material("trim_gray", rgba=(0.30, 0.31, 0.33, 1.0))
    glass_dark = model.material("glass_dark", rgba=(0.10, 0.14, 0.20, 0.55))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "anamorphic_body"),
        material=barrel_black,
        name="body_shell",
    )
    body.visual(
        Cylinder(radius=0.0470, length=0.0035),
        origin=Origin(xyz=(0.230, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass_dark,
        name="front_element",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(
            _geared_ring_shape(
                width=FOCUS_RING_WIDTH,
                inner_radius=0.0456,
                ring_radius=0.0503,
                tooth_height=0.0030,
                tooth_depth=0.0044,
                tooth_count=72,
            ),
            "focus_ring",
        ),
        material=ring_black,
        name="focus_band",
    )
    focus_ring.visual(
        Box((0.012, 0.004, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.0515)),
        material=trim_gray,
        name="focus_witness",
    )

    orientation_collar = model.part("orientation_collar")
    orientation_collar.visual(
        mesh_from_cadquery(_orientation_collar_shape(), "orientation_collar"),
        material=ring_black,
        name="collar_band",
    )
    orientation_collar.visual(
        Box((0.010, 0.0035, 0.004)),
        origin=Origin(xyz=(0.0, 0.0, 0.0633)),
        material=trim_gray,
        name="collar_witness",
    )

    model.articulation(
        "body_to_focus_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=focus_ring,
        origin=Origin(xyz=(FOCUS_RING_CENTER_X, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=8.0),
    )
    model.articulation(
        "body_to_orientation_collar",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=orientation_collar,
        origin=Origin(xyz=(COLLAR_CENTER_X, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=4.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
