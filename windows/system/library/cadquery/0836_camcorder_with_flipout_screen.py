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
MAIN_X = 0.150
MAIN_Y = 0.055
MAIN_Z = 0.066
SIDE_Y = -MAIN_Y / 2.0
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).edges().fillet(radius)
def _lens_ring_mesh() -> cq.Workplane:
    """Short hollow knurled ring, centered on the local X rotation axis."""

    outer_radius = 0.024
    # Slightly smaller than the fixed barrel radius; the authored overlap is
    # a hidden bearing/capture proxy and is explicitly allowed in tests.
    inner_radius = 0.0165
    length = 0.018
    ring = (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length, both=True)
    )

    # Raised rubber ribs around the outside so the rotating ring reads as a
    # gripped focus/zoom ring rather than a plain sleeve.
    for idx in range(18):
        angle = idx * 360.0 / 18.0
        rib = (
            cq.Workplane("XY")
            .box(length * 1.02, 0.0031, 0.0042)
            .translate((0.0, 0.0, outer_radius + 0.0017))
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle)
        )
        ring = ring.union(rib)
    return ring
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="palm_camcorder")

    body_mat = model.material("warm_dark_graphite", rgba=(0.09, 0.095, 0.10, 1.0))
    grip_mat = model.material("soft_rubber_black", rgba=(0.015, 0.014, 0.013, 1.0))
    trim_mat = model.material("satin_black_trim", rgba=(0.025, 0.027, 0.030, 1.0))
    screen_mat = model.material("inactive_lcd_glass", rgba=(0.02, 0.08, 0.12, 1.0))
    glass_mat = model.material("coated_lens_glass", rgba=(0.04, 0.12, 0.16, 0.82))
    label_mat = model.material("tiny_white_labels", rgba=(0.82, 0.86, 0.84, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_rounded_box((MAIN_X, MAIN_Y, MAIN_Z), 0.010), "rounded_body"),
        material=body_mat,
        name="rounded_body",
    )
    body.visual(
        mesh_from_cadquery(_rounded_box((0.105, 0.030, 0.052), 0.010), "rounded_handgrip"),
        origin=Origin(xyz=(-0.010, 0.040, -0.004)),
        material=grip_mat,
        name="rounded_handgrip",
    )
    body.visual(
        Box((0.076, 0.004, 0.036)),
        origin=Origin(xyz=(-0.010, 0.056, -0.004)),
        material=trim_mat,
        name="grip_strap_pad",
    )
    body.visual(
        Cylinder(radius=0.024, length=0.007),
        origin=Origin(xyz=(MAIN_X / 2.0 + 0.0035, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_mat,
        name="lens_shoulder",
    )
    body.visual(
        Cylinder(radius=0.017, length=0.050),
        origin=Origin(xyz=(MAIN_X / 2.0 + 0.025, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_mat,
        name="lens_barrel",
    )
    body.visual(
        Cylinder(radius=0.014, length=0.003),
        origin=Origin(xyz=(MAIN_X / 2.0 + 0.0515, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass_mat,
        name="front_glass",
    )
    body.visual(
        Box((0.010, 0.0065, 0.064)),
        origin=Origin(xyz=(-0.055, SIDE_Y - 0.00325, 0.0)),
        material=trim_mat,
        name="monitor_hinge_pedestal",
    )
    body.visual(
        Box((0.046, 0.0033, 0.005)),
        origin=Origin(xyz=(-0.012, SIDE_Y - 0.00065, -0.026)),
        material=trim_mat,
        name="port_hinge_ledge",
    )
    body.visual(
        Box((0.020, 0.0015, 0.006)),
        origin=Origin(xyz=(-0.012, SIDE_Y - 0.00075, -0.006)),
        material=label_mat,
        name="port_label",
    )

    lens_ring = model.part("lens_ring")
    lens_ring.visual(
        mesh_from_cadquery(_lens_ring_mesh(), "knurled_lens_ring", tolerance=0.0006),
        material=grip_mat,
        name="knurled_ring",
    )

    monitor = model.part("side_monitor")
    monitor.visual(
        Cylinder(radius=0.0035, length=0.058),
        origin=Origin(rpy=(0.0, 0.0, 0.0)),
        material=trim_mat,
        name="monitor_hinge_barrel",
    )
    monitor.visual(
        Box((0.011, 0.004, 0.052)),
        origin=Origin(xyz=(0.0055, -0.0040, 0.0)),
        material=trim_mat,
        name="monitor_hinge_leaf",
    )
    monitor.visual(
        Box((0.074, 0.006, 0.056)),
        origin=Origin(xyz=(0.037, -0.0080, 0.0)),
        material=body_mat,
        name="monitor_frame",
    )
    monitor.visual(
        Box((0.060, 0.001, 0.042)),
        origin=Origin(xyz=(0.041, -0.0115, 0.0)),
        material=screen_mat,
        name="lcd_screen",
    )

    port_cover = model.part("port_cover")
    port_cover.visual(
        Cylinder(radius=0.0022, length=0.044),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=trim_mat,
        name="cover_hinge_barrel",
    )
    port_cover.visual(
        Box((0.040, 0.0030, 0.0060)),
        origin=Origin(xyz=(0.0, -0.0027, 0.0035)),
        material=trim_mat,
        name="cover_hinge_leaf",
    )
    port_cover.visual(
        Box((0.040, 0.0040, 0.0220)),
        origin=Origin(xyz=(0.0, -0.0050, 0.0132)),
        material=body_mat,
        name="cover_panel",
    )
    port_cover.visual(
        Box((0.014, 0.0010, 0.0050)),
        origin=Origin(xyz=(0.0, -0.0075, 0.0150)),
        material=grip_mat,
        name="cover_pull_lip",
    )

    model.articulation(
        "body_to_lens_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=lens_ring,
        origin=Origin(xyz=(MAIN_X / 2.0 + 0.037, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.15, velocity=8.0),
    )
    model.articulation(
        "body_to_side_monitor",
        ArticulationType.REVOLUTE,
        parent=body,
        child=monitor,
        origin=Origin(xyz=(-0.055, SIDE_Y - 0.0100, 0.0)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(effort=0.35, velocity=2.5, lower=0.0, upper=1.62),
    )
    model.articulation(
        "body_to_port_cover",
        ArticulationType.REVOLUTE,
        parent=body,
        child=port_cover,
        origin=Origin(xyz=(-0.012, SIDE_Y - 0.0045, -0.026)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.12, velocity=2.0, lower=0.0, upper=1.25),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
