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
BASE_WIDTH = 0.135
BASE_DEPTH = 0.110
BASE_HEIGHT = 0.082
BOTTLE_BODY_RADIUS = 0.038
BOTTLE_COLLAR_RADIUS = 0.043
BOTTLE_HEIGHT = 0.222
def _centered_box(size: tuple[float, float, float], xyz: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(xyz)
def _base_shape() -> cq.Workplane:
    housing = (
        cq.Workplane("XY")
        .box(BASE_WIDTH, BASE_DEPTH, BASE_HEIGHT)
        .translate((0.0, 0.0, BASE_HEIGHT / 2.0))
        .edges("|Z")
        .fillet(0.010)
    )

    deck_recess = (
        cq.Workplane("XY")
        .workplane(offset=BASE_HEIGHT)
        .circle(0.033)
        .extrude(-0.010)
    )
    housing = housing.cut(deck_recess)

    slot = _centered_box(
        (0.015, 0.006, 0.004),
        (0.0, 0.039, BASE_HEIGHT - 0.002),
    )
    for angle_deg in (0.0, 120.0, 240.0):
        housing = housing.cut(slot.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))

    switch_pocket = _centered_box(
        (0.036, 0.020, 0.026),
        (0.0, BASE_DEPTH / 2.0 - 0.008, 0.030),
    )
    housing = housing.cut(switch_pocket)

    return housing
def _bottle_shape() -> cq.Workplane:
    lower_body = cq.Workplane("XY").circle(BOTTLE_BODY_RADIUS).extrude(0.176)
    shoulder = (
        cq.Workplane("XY")
        .workplane(offset=0.176)
        .circle(BOTTLE_BODY_RADIUS)
        .workplane(offset=0.022)
        .circle(0.031)
        .loft(combine=True)
    )
    neck = cq.Workplane("XY").workplane(offset=0.198).circle(0.031).extrude(0.012)
    lid = cq.Workplane("XY").workplane(offset=0.210).circle(0.033).extrude(0.006)
    mount_collar = cq.Workplane("XY").circle(BOTTLE_COLLAR_RADIUS).extrude(0.011)

    bottle = lower_body.union(shoulder).union(neck).union(lid).union(mount_collar)

    tab = _centered_box((0.014, 0.005, 0.003), (0.0, 0.0385, 0.006))
    for angle_deg in (0.0, 120.0, 240.0):
        bottle = bottle.union(tab.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))

    spout_collar = (
        cq.Workplane("XY")
        .workplane(offset=0.210)
        .center(0.0, 0.018)
        .circle(0.011)
        .extrude(0.012)
    )
    hinge_pedestal = _centered_box((0.026, 0.010, 0.006), (0.0, 0.006, 0.219))
    bottle = bottle.union(spout_collar).union(hinge_pedestal)

    inner_body = cq.Workplane("XY").workplane(offset=0.004).circle(0.034).extrude(0.168)
    inner_shoulder = (
        cq.Workplane("XY")
        .workplane(offset=0.172)
        .circle(0.034)
        .workplane(offset=0.022)
        .circle(0.026)
        .loft(combine=True)
    )
    inner_neck = cq.Workplane("XY").workplane(offset=0.194).circle(0.026).extrude(0.016)
    spout_hole = (
        cq.Workplane("XY")
        .workplane(offset=0.204)
        .center(0.0, 0.018)
        .circle(0.006)
        .extrude(0.020)
    )
    drive_bore = cq.Workplane("XY").circle(0.006).extrude(0.014)

    bottle = bottle.cut(inner_body).cut(inner_shoulder).cut(inner_neck).cut(spout_hole).cut(drive_bore)
    return bottle
def _switch_shape() -> cq.Workplane:
    rocker = _centered_box((0.032, 0.014, 0.022), (0.0, 0.003, 0.0))
    mounting_flange = _centered_box((0.040, 0.002, 0.026), (0.0, -0.002, 0.0))
    return rocker.edges("|X").fillet(0.003).union(mounting_flange)
def _spout_cap_shape() -> cq.Workplane:
    barrel = (
        cq.Workplane("YZ")
        .circle(0.003)
        .extrude(0.024)
        .translate((-0.012, 0.0, 0.0))
    )
    cover = _centered_box((0.030, 0.026, 0.008), (0.0, 0.015, 0.001))
    plug = (
        cq.Workplane("XY")
        .workplane(offset=-0.006)
        .center(0.0, 0.012)
        .circle(0.0045)
        .extrude(0.004)
    )
    return barrel.union(cover.edges("|X").fillet(0.002)).union(plug)
def _blade_shape() -> cq.Workplane:
    hub = cq.Workplane("XY").workplane(offset=-0.004).circle(0.007).extrude(0.008)
    shaft = cq.Workplane("XY").workplane(offset=-0.024).circle(0.0045).extrude(0.026)
    coupling = cq.Workplane("XY").workplane(offset=-0.024).circle(0.0065).extrude(0.006)

    blade_x_pos = (
        _centered_box((0.030, 0.007, 0.0018), (0.017, 0.0, 0.001))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 18.0)
    )
    blade_x_neg = (
        _centered_box((0.030, 0.007, 0.0018), (-0.017, 0.0, 0.001))
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -18.0)
    )
    blade_y_pos = (
        _centered_box((0.007, 0.030, 0.0018), (0.0, 0.017, 0.001))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -18.0)
    )
    blade_y_neg = (
        _centered_box((0.007, 0.030, 0.0018), (0.0, -0.017, 0.001))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 18.0)
    )

    return (
        hub.union(shaft)
        .union(coupling)
        .union(blade_x_pos)
        .union(blade_x_neg)
        .union(blade_y_pos)
        .union(blade_y_neg)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_single_serve_blender")

    body_mat = model.material("body_mat", rgba=(0.92, 0.93, 0.94, 1.0))
    trim_mat = model.material("trim_mat", rgba=(0.16, 0.17, 0.19, 1.0))
    bottle_mat = model.material("bottle_mat", rgba=(0.80, 0.90, 0.98, 0.35))
    cap_mat = model.material("cap_mat", rgba=(0.20, 0.22, 0.25, 1.0))
    switch_mat = model.material("switch_mat", rgba=(0.70, 0.10, 0.10, 1.0))
    blade_mat = model.material("blade_mat", rgba=(0.78, 0.80, 0.82, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_base_shape(), "base_housing"),
        material=body_mat,
        name="housing",
    )

    bottle = model.part("bottle")
    bottle.visual(
        mesh_from_cadquery(_bottle_shape(), "bottle_shell"),
        material=bottle_mat,
        name="shell",
    )

    front_switch = model.part("front_switch")
    front_switch.visual(
        mesh_from_cadquery(_switch_shape(), "front_switch"),
        material=switch_mat,
        name="rocker",
    )

    spout_cap = model.part("spout_cap")
    spout_cap.visual(
        mesh_from_cadquery(_spout_cap_shape(), "spout_cap"),
        material=cap_mat,
        name="cover",
    )

    blade = model.part("blade")
    blade.visual(
        mesh_from_cadquery(_blade_shape(), "blade"),
        material=blade_mat,
        name="rotor",
    )

    model.articulation(
        "base_to_bottle",
        ArticulationType.REVOLUTE,
        parent=base,
        child=bottle,
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=2.0,
            lower=0.0,
            upper=1.0,
        ),
    )

    model.articulation(
        "base_to_front_switch",
        ArticulationType.REVOLUTE,
        parent=base,
        child=front_switch,
        origin=Origin(xyz=(0.0, BASE_DEPTH / 2.0 + 0.001, 0.030)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=3.0,
            lower=-0.30,
            upper=0.30,
        ),
    )

    model.articulation(
        "bottle_to_spout_cap",
        ArticulationType.REVOLUTE,
        parent=bottle,
        child=spout_cap,
        origin=Origin(xyz=(0.0, 0.006, BOTTLE_HEIGHT + 0.003)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.8,
            velocity=5.0,
            lower=0.0,
            upper=2.05,
        ),
    )

    model.articulation(
        "base_to_blade",
        ArticulationType.CONTINUOUS,
        parent=base,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, BASE_HEIGHT + 0.014)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=1.5,
            velocity=45.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
