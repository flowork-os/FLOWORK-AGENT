# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_pump_with_t_handle, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_pump_with_t_handle

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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

# ===== wheels_tires (1 syms) =====
pi = math.pi

# ===== model =====
from math import pi
import cadquery as cq
BARREL_OUTER_RADIUS = 0.024
BARREL_INNER_RADIUS = 0.0205
GUIDE_BORE_RADIUS = 0.0085
GUIDE_OUTER_RADIUS = 0.030
BASE_HUB_RADIUS = 0.050
BASE_HUB_HEIGHT = 0.018
BASE_COLLAR_RADIUS = 0.040
BASE_COLLAR_HEIGHT = 0.038
BARREL_TUBE_BOTTOM_Z = 0.030
BARREL_TUBE_TOP_Z = 0.482
GUIDE_BOTTOM_Z = BARREL_TUBE_TOP_Z
GUIDE_TOP_Z = 0.514
LOWER_COLLAR_BOTTOM_Z = 0.018
LOWER_COLLAR_HEIGHT = 0.046
LOWER_COLLAR_RADIUS = 0.031
CAVITY_BOTTOM_Z = 0.060
ROD_RADIUS = 0.0055
ROD_LENGTH = 0.420
ROD_CENTER_Z = -0.070
SLIDE_TRAVEL = 0.220
HANDLE_WIDTH = 0.285
HANDLE_DEPTH = 0.032
HANDLE_THICKNESS = 0.024
HANDLE_CENTER_Z = 0.148
PISTON_LENGTH = 0.012
PISTON_CENTER_Z = -0.258
PISTON_RADIUS = 0.0175
def _tripod_base_shape() -> cq.Workplane:
    hub = cq.Workplane("XY").circle(BASE_HUB_RADIUS).extrude(BASE_HUB_HEIGHT)
    collar = cq.Workplane("XY").circle(BASE_COLLAR_RADIUS).extrude(BASE_COLLAR_HEIGHT)

    foot = (
        cq.Workplane("XZ")
        .polyline(
            [
                (0.028, 0.004),
                (0.028, 0.020),
                (0.072, 0.023),
                (0.145, 0.014),
                (0.188, 0.008),
                (0.195, 0.002),
                (0.188, 0.000),
                (0.145, 0.000),
                (0.062, 0.003),
            ]
        )
        .close()
        .extrude(0.024, both=True)
    )

    base = hub.union(collar).union(foot)
    for angle_deg in (120.0, 240.0):
        base = base.union(foot.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg))

    return base
def _barrel_shell_shape() -> cq.Workplane:
    outer_tube = (
        cq.Workplane("XY")
        .workplane(offset=BARREL_TUBE_BOTTOM_Z)
        .circle(BARREL_OUTER_RADIUS)
        .extrude(BARREL_TUBE_TOP_Z - BARREL_TUBE_BOTTOM_Z)
    )
    lower_collar = (
        cq.Workplane("XY")
        .workplane(offset=LOWER_COLLAR_BOTTOM_Z)
        .circle(LOWER_COLLAR_RADIUS)
        .extrude(LOWER_COLLAR_HEIGHT)
    )
    top_guide = (
        cq.Workplane("XY")
        .workplane(offset=GUIDE_BOTTOM_Z)
        .circle(GUIDE_OUTER_RADIUS)
        .extrude(GUIDE_TOP_Z - GUIDE_BOTTOM_Z)
    )

    barrel = outer_tube.union(lower_collar).union(top_guide)

    barrel_cavity = (
        cq.Workplane("XY")
        .workplane(offset=CAVITY_BOTTOM_Z)
        .circle(BARREL_INNER_RADIUS)
        .extrude((BARREL_TUBE_TOP_Z - CAVITY_BOTTOM_Z) + 0.004)
    )
    guide_bore = (
        cq.Workplane("XY")
        .workplane(offset=GUIDE_BOTTOM_Z - 0.002)
        .circle(GUIDE_BORE_RADIUS)
        .extrude((GUIDE_TOP_Z - GUIDE_BOTTOM_Z) + 0.004)
    )

    return barrel.cut(barrel_cavity).cut(guide_bore)
def _handle_shape() -> cq.Workplane:
    grip = (
        cq.Workplane("YZ")
        .ellipse(HANDLE_DEPTH / 2.0, HANDLE_THICKNESS / 2.0)
        .extrude(HANDLE_WIDTH / 2.0, both=True)
        .translate((0.0, 0.0, HANDLE_CENTER_Z))
    )
    stem = (
        cq.Workplane("XY")
        .workplane(offset=0.026)
        .ellipse(0.014, 0.010)
        .extrude(0.096)
    )
    upper_spine = (
        cq.Workplane("XY")
        .workplane(offset=0.112)
        .rect(0.060, 0.028)
        .extrude(0.022)
    )

    return grip.union(stem).union(upper_spine)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="bicycle_track_pump")

    model.material("powder_gray", rgba=(0.28, 0.30, 0.32, 1.0))
    model.material("satin_aluminum", rgba=(0.74, 0.76, 0.79, 1.0))
    model.material("chrome", rgba=(0.84, 0.86, 0.88, 1.0))
    model.material("rubber_black", rgba=(0.08, 0.08, 0.09, 1.0))
    model.material("gauge_black", rgba=(0.05, 0.06, 0.07, 1.0))

    pump_body = model.part("pump_body")
    pump_body.visual(
        mesh_from_cadquery(_tripod_base_shape(), "tripod_base"),
        material="powder_gray",
        name="tripod_base",
    )
    pump_body.visual(
        mesh_from_cadquery(_barrel_shell_shape(), "barrel_shell"),
        material="satin_aluminum",
        name="barrel_shell",
    )
    pump_body.visual(
        Cylinder(radius=0.032, length=0.018),
        origin=Origin(xyz=(0.033, 0.0, 0.064), rpy=(0.0, pi / 2.0, 0.0)),
        material="powder_gray",
        name="gauge_housing",
    )
    pump_body.visual(
        Cylinder(radius=0.025, length=0.0025),
        origin=Origin(xyz=(0.04175, 0.0, 0.064), rpy=(0.0, pi / 2.0, 0.0)),
        material="gauge_black",
        name="gauge_face",
    )
    pump_body.inertial = Inertial.from_geometry(
        Box((0.39, 0.35, GUIDE_TOP_Z)),
        mass=3.1,
        origin=Origin(xyz=(0.0, 0.0, GUIDE_TOP_Z / 2.0)),
    )

    rod_handle = model.part("rod_handle")
    rod_handle.visual(
        Cylinder(radius=ROD_RADIUS, length=ROD_LENGTH),
        origin=Origin(xyz=(0.0, 0.0, ROD_CENTER_Z)),
        material="chrome",
        name="pump_rod",
    )
    rod_handle.visual(
        Cylinder(radius=PISTON_RADIUS, length=PISTON_LENGTH),
        origin=Origin(xyz=(0.0, 0.0, PISTON_CENTER_Z)),
        material="rubber_black",
        name="piston_head",
    )
    rod_handle.visual(
        mesh_from_cadquery(_handle_shape(), "t_handle"),
        material="rubber_black",
        name="t_handle",
    )
    rod_handle.inertial = Inertial.from_geometry(
        Box((HANDLE_WIDTH, HANDLE_DEPTH, 0.19)),
        mass=0.55,
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
    )

    model.articulation(
        "body_to_rod_handle",
        ArticulationType.PRISMATIC,
        parent=pump_body,
        child=rod_handle,
        origin=Origin(xyz=(0.0, 0.0, GUIDE_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            lower=0.0,
            upper=SLIDE_TRAVEL,
            effort=180.0,
            velocity=1.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
