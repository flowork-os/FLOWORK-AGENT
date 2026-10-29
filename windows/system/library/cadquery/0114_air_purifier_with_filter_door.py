# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_HEIGHT = 0.315
UPPER_HEIGHT = 0.245
BODY_RADIUS = 0.108
UPPER_RADIUS = 0.114
WALL_THICKNESS = 0.004
FILTER_TRAVEL = 0.165
TWIST_TRAVEL = math.radians(38.0)
BUTTON_TRAVEL = 0.0035
def _lower_body_shape():
    shell = cq.Workplane("XY").circle(BODY_RADIUS).extrude(BODY_HEIGHT)
    shell = shell.faces(">Z").shell(-WALL_THICKNESS)

    foot_ring = (
        cq.Workplane("XY")
        .circle(BODY_RADIUS + 0.006)
        .circle(BODY_RADIUS - 0.014)
        .extrude(0.018)
    )
    guide_collar = (
        cq.Workplane("XY")
        .circle(BODY_RADIUS - WALL_THICKNESS)
        .circle(BODY_RADIUS - 0.014)
        .extrude(0.024)
        .translate((0.0, 0.0, BODY_HEIGHT - 0.024))
    )
    return shell.union(foot_ring).union(guide_collar)
def _upper_shell_shape():
    shell = cq.Workplane("XY").circle(UPPER_RADIUS).extrude(UPPER_HEIGHT)
    shell = shell.faces("<Z").shell(-WALL_THICKNESS)
    shell = shell.faces(">Z").workplane().circle(0.046).cutBlind(-0.010)

    seat_ring = (
        cq.Workplane("XY")
        .circle(UPPER_RADIUS - WALL_THICKNESS)
        .circle(BODY_RADIUS - WALL_THICKNESS)
        .extrude(0.008)
    )
    bar_a = cq.Workplane("XY").box(0.098, 0.008, 0.003).translate(
        (0.0, 0.0, UPPER_HEIGHT - 0.0015)
    )
    bar_b = cq.Workplane("XY").box(0.008, 0.098, 0.003).translate(
        (0.0, 0.0, UPPER_HEIGHT - 0.0015)
    )
    return shell.union(seat_ring).union(bar_a).union(bar_b)
def _filter_shape():
    media_outer_radius = 0.083
    media_inner_radius = 0.031
    media_height = 0.220
    top_cap_height = 0.010
    bottom_cap_height = 0.015
    cap_radius = 0.086

    top_cap = (
        cq.Workplane("XY")
        .circle(cap_radius)
        .circle(media_inner_radius)
        .extrude(top_cap_height)
        .translate((0.0, 0.0, -top_cap_height))
    )
    media = (
        cq.Workplane("XY")
        .circle(media_outer_radius)
        .circle(media_inner_radius)
        .extrude(media_height)
        .translate((0.0, 0.0, -(top_cap_height + media_height)))
    )
    bottom_cap = (
        cq.Workplane("XY")
        .circle(cap_radius)
        .circle(media_inner_radius)
        .extrude(bottom_cap_height)
        .translate((0.0, 0.0, -(top_cap_height + media_height + bottom_cap_height)))
    )
    guide_ring = (
        cq.Workplane("XY")
        .circle(BODY_RADIUS - 0.014)
        .circle(cap_radius - 0.002)
        .extrude(0.010)
        .translate((0.0, 0.0, -0.013))
    )

    handle_spine = cq.Workplane("XY").box(0.074, 0.010, 0.008)
    handle_bridge = cq.Workplane("XY").box(0.060, 0.014, 0.008).translate((0.0, 0.0, 0.022))
    handle_post_a = cq.Workplane("XY").box(0.010, 0.010, 0.024).translate((0.020, 0.0, 0.010))
    handle_post_b = cq.Workplane("XY").box(0.010, 0.010, 0.024).translate((-0.020, 0.0, 0.010))

    filter_shape = (
        top_cap.union(media)
        .union(bottom_cap)
        .union(guide_ring)
        .union(handle_spine)
        .union(handle_bridge)
        .union(handle_post_a)
        .union(handle_post_b)
    )

    rib_z = -(top_cap_height + media_height * 0.5)
    for rib_index in range(18):
        angle_deg = 360.0 * rib_index / 18.0
        rib = (
            cq.Workplane("XY")
            .box(0.006, 0.014, media_height * 0.94)
            .translate((media_outer_radius, 0.0, rib_z))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        )
        filter_shape = filter_shape.union(rib)

    return filter_shape
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cylindrical_purifier")

    shell_white = model.material("shell_white", rgba=(0.93, 0.94, 0.92, 1.0))
    shell_grey = model.material("shell_grey", rgba=(0.83, 0.84, 0.82, 1.0))
    charcoal = model.material("charcoal", rgba=(0.17, 0.18, 0.19, 1.0))
    filter_cream = model.material("filter_cream", rgba=(0.95, 0.94, 0.88, 1.0))
    button_black = model.material("button_black", rgba=(0.09, 0.09, 0.10, 1.0))
    accent_blue = model.material("accent_blue", rgba=(0.35, 0.57, 0.72, 1.0))

    lower_body = model.part("lower_body")
    lower_body.visual(
        mesh_from_cadquery(_lower_body_shape(), "purifier_lower_body"),
        material=shell_grey,
        name="body_shell",
    )
    lower_body.visual(
        Box((0.020, 0.054, 0.074)),
        origin=Origin(xyz=(BODY_RADIUS + 0.004, 0.0, 0.155)),
        material=shell_white,
        name="button_pad",
    )

    upper_shell = model.part("upper_shell")
    upper_shell.visual(
        mesh_from_cadquery(_upper_shell_shape(), "purifier_upper_shell"),
        material=shell_white,
        name="shell_body",
    )
    upper_shell.visual(
        Box((0.006, 0.028, 0.050)),
        origin=Origin(xyz=(UPPER_RADIUS + 0.0015, 0.0, 0.145)),
        material=accent_blue,
        name="shell_badge",
    )

    filter_cylinder = model.part("filter_cylinder")
    filter_cylinder.visual(
        mesh_from_cadquery(_filter_shape(), "purifier_filter_cylinder"),
        material=filter_cream,
        name="filter_body",
    )

    power_button = model.part("power_button")
    power_button.visual(
        Cylinder(radius=0.013, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=button_black,
        name="button_cap",
    )

    model.articulation(
        "lower_body_to_upper_shell",
        ArticulationType.REVOLUTE,
        parent=lower_body,
        child=upper_shell,
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT - 0.005)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=1.2,
            lower=0.0,
            upper=TWIST_TRAVEL,
        ),
    )

    model.articulation(
        "lower_body_to_filter_cylinder",
        ArticulationType.PRISMATIC,
        parent=lower_body,
        child=filter_cylinder,
        origin=Origin(xyz=(0.0, 0.0, BODY_HEIGHT - 0.017)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=20.0,
            velocity=0.12,
            lower=0.0,
            upper=FILTER_TRAVEL,
        ),
    )

    model.articulation(
        "lower_body_to_power_button",
        ArticulationType.PRISMATIC,
        parent=lower_body,
        child=power_button,
        origin=Origin(
            xyz=(BODY_RADIUS + 0.014, 0.0, 0.155),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=0.04,
            lower=0.0,
            upper=BUTTON_TRAVEL,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
