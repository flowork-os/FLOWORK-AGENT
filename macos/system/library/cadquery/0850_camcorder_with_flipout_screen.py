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
BODY_LEN = 0.118
BODY_W = 0.050
BODY_H = 0.060
LENS_Z = 0.006
LENS_BARREL_R = 0.0148
LENS_BARREL_L = 0.026
ZOOM_INNER_R = 0.0162
ZOOM_OUTER_R = 0.0218
ZOOM_L = 0.014
ZOOM_X = BODY_LEN * 0.5 + 0.007
SHROUD_X = BODY_LEN * 0.5 + 0.023
SHROUD_L = 0.011
DISPLAY_LEN = 0.070
DISPLAY_T = 0.0035
DISPLAY_H = 0.046
DISPLAY_GAP = 0.0017
DISPLAY_HINGE_X = -0.030
LATCH_W = 0.012
LATCH_T = 0.0020
LATCH_H = 0.018
LATCH_Y = -0.010
LATCH_Z = 0.018
def _tube_shape(length: float, outer_radius: float, inner_radius: float) -> cq.Workplane:
    outer = (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .extrude(length)
        .translate((-length * 0.5, 0.0, 0.0))
    )
    inner_length = length + 0.003
    inner = (
        cq.Workplane("YZ")
        .circle(inner_radius)
        .extrude(inner_length)
        .translate((-inner_length * 0.5, 0.0, 0.0))
    )
    return outer.cut(inner)
def _body_shell_shape() -> cq.Workplane:
    base = cq.Workplane("XY").box(BODY_LEN, BODY_W, BODY_H)
    base = base.edges("|Z").fillet(0.007)

    top_hump = cq.Workplane("XY").box(0.050, BODY_W * 0.84, 0.012).translate(
        (-0.004, 0.0, BODY_H * 0.5 + 0.004)
    )
    battery_bulge = cq.Workplane("XY").box(0.024, 0.022, 0.032).translate(
        (-BODY_LEN * 0.5 + 0.011, -0.005, 0.006)
    )
    nose_cheek = cq.Workplane("XY").box(0.018, 0.032, 0.036).translate(
        (BODY_LEN * 0.5 - 0.012, 0.0, 0.002)
    )

    door_pocket = cq.Workplane("XY").box(DISPLAY_LEN - 0.006, 0.0022, DISPLAY_H - 0.006).translate(
        (DISPLAY_HINGE_X + DISPLAY_LEN * 0.5 + 0.002, BODY_W * 0.5 - 0.0011, -0.001)
    )

    return base.union(top_hump).union(battery_bulge).union(nose_cheek).cut(door_pocket)
def _display_door_shape() -> cq.Workplane:
    door = cq.Workplane("XY").box(DISPLAY_LEN, DISPLAY_T, DISPLAY_H)
    door = door.edges("|Y").fillet(0.0045)

    screen_recess_depth = 0.0016
    screen_recess = cq.Workplane("XY").box(
        DISPLAY_LEN - 0.016,
        screen_recess_depth,
        DISPLAY_H - 0.014,
    ).translate((0.004, -DISPLAY_T * 0.5 + screen_recess_depth * 0.5, 0.0))

    hinge_spine = (
        cq.Workplane("XY")
        .circle(0.0030)
        .extrude(DISPLAY_H * 0.80)
        .translate((-DISPLAY_LEN * 0.5 + 0.0012, 0.0, -DISPLAY_H * 0.40))
    )

    return door.cut(screen_recess).union(hinge_spine)
def _eyecup_shape() -> cq.Workplane:
    outer = (
        cq.Workplane("YZ")
        .circle(0.0125)
        .workplane(offset=0.018)
        .circle(0.0078)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("YZ")
        .circle(0.0088)
        .workplane(offset=0.018)
        .circle(0.0048)
        .loft(combine=True)
    )
    cup = outer.cut(inner).translate((-0.009, 0.0, 0.0))
    mount_lip = _tube_shape(0.004, 0.0096, 0.0064).translate((0.006, 0.0, 0.0))
    return cup.union(mount_lip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_camcorder")

    body_finish = model.material("body_finish", rgba=(0.18, 0.19, 0.21, 1.0))
    door_finish = model.material("door_finish", rgba=(0.24, 0.25, 0.28, 1.0))
    rubber_finish = model.material("rubber_finish", rgba=(0.07, 0.07, 0.08, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.50, 0.52, 0.56, 1.0))
    glass_finish = model.material("glass_finish", rgba=(0.12, 0.14, 0.17, 0.70))
    indicator_finish = model.material("indicator_finish", rgba=(0.88, 0.90, 0.92, 1.0))
    record_finish = model.material("record_finish", rgba=(0.72, 0.11, 0.09, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shell_shape(), "camcorder_body_shell"),
        material=body_finish,
        name="body_shell",
    )
    body.visual(
        Box((0.0050, 0.0012, 0.040)),
        origin=Origin(xyz=(DISPLAY_HINGE_X + 0.0012, 0.02485, 0.0)),
        material=body_finish,
        name="hinge_mount",
    )
    body.visual(
        Cylinder(radius=LENS_BARREL_R, length=LENS_BARREL_L),
        origin=Origin(xyz=(BODY_LEN * 0.5 + 0.009, 0.0, LENS_Z), rpy=(0.0, math.pi * 0.5, 0.0)),
        material=rubber_finish,
        name="lens_barrel",
    )
    body.visual(
        mesh_from_cadquery(_tube_shape(SHROUD_L, 0.0255, 0.0102), "camcorder_front_shroud"),
        origin=Origin(xyz=(SHROUD_X, 0.0, LENS_Z)),
        material=body_finish,
        name="front_shroud",
    )
    body.visual(
        Cylinder(radius=0.0104, length=0.004),
        origin=Origin(xyz=(BODY_LEN * 0.5 + 0.028, 0.0, LENS_Z), rpy=(0.0, math.pi * 0.5, 0.0)),
        material=glass_finish,
        name="lens_glass",
    )
    body.visual(
        Box((0.012, 0.016, 0.012)),
        origin=Origin(xyz=(-0.058, 0.009, 0.012)),
        material=body_finish,
        name="viewfinder_mount",
    )
    body.visual(
        mesh_from_cadquery(_eyecup_shape(), "camcorder_eyecup"),
        origin=Origin(xyz=(-0.068, 0.009, 0.012)),
        material=rubber_finish,
        name="eyecup",
    )
    body.visual(
        Box((0.060, 0.0025, 0.020)),
        origin=Origin(xyz=(0.004, -BODY_W * 0.5 - 0.0010, -0.004)),
        material=rubber_finish,
        name="strap_pad",
    )
    body.visual(
        Cylinder(radius=0.0040, length=0.004),
        origin=Origin(xyz=(-0.010, -0.011, BODY_H * 0.5 + 0.008), rpy=(0.0, 0.0, 0.0)),
        material=record_finish,
        name="record_button",
    )

    display_door = model.part("display_door")
    display_door.visual(
        mesh_from_cadquery(_display_door_shape(), "camcorder_display_door"),
        origin=Origin(xyz=(DISPLAY_LEN * 0.5, DISPLAY_T * 0.5, 0.0)),
        material=door_finish,
        name="door_shell",
    )
    display_door.visual(
        Box((0.050, 0.0007, 0.034)),
        origin=Origin(xyz=(0.038, 0.00065, 0.0)),
        material=glass_finish,
        name="screen_glass",
    )

    zoom_collar = model.part("zoom_collar")
    zoom_collar.visual(
        mesh_from_cadquery(_tube_shape(ZOOM_L, ZOOM_OUTER_R, ZOOM_INNER_R), "camcorder_zoom_collar"),
        material=rubber_finish,
        name="collar_ring",
    )
    zoom_collar.visual(
        Box((0.0030, 0.0055, 0.0016)),
        origin=Origin(xyz=(0.0, 0.0, ZOOM_OUTER_R + 0.0003)),
        material=indicator_finish,
        name="index_mark",
    )

    battery_latch = model.part("battery_latch")
    battery_latch.visual(
        Box((LATCH_T, LATCH_W, LATCH_H)),
        origin=Origin(xyz=(-LATCH_T * 0.5, 0.0, -0.0083)),
        material=trim_finish,
        name="latch_paddle",
    )
    battery_latch.visual(
        Cylinder(radius=0.0014, length=LATCH_W + 0.001),
        origin=Origin(
            xyz=(-0.0007, 0.0, 0.0),
            rpy=(math.pi * 0.5, 0.0, 0.0),
        ),
        material=trim_finish,
        name="latch_barrel",
    )

    model.articulation(
        "display_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=display_door,
        origin=Origin(xyz=(DISPLAY_HINGE_X, BODY_W * 0.5 + DISPLAY_GAP, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=2.2, effort=0.4, velocity=3.5),
    )
    model.articulation(
        "zoom_rotation",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=zoom_collar,
        origin=Origin(xyz=(ZOOM_X, 0.0, LENS_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.2, velocity=8.0),
    )
    model.articulation(
        "battery_release",
        ArticulationType.REVOLUTE,
        parent=body,
        child=battery_latch,
        origin=Origin(xyz=(-BODY_LEN * 0.5 - 0.0006, LATCH_Y, LATCH_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=0.75, effort=0.1, velocity=3.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
