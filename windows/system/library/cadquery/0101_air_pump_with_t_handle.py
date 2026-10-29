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
GUIDE_LENGTH = 0.180
GUIDE_DEPTH = 0.056
GUIDE_HEIGHT = 0.038
GUIDE_CENTER_Z = 0.019
GUIDE_BORE_RADIUS = 0.013
SUPPORT_WIDTH = 0.070
SUPPORT_DEPTH = 0.040
SUPPORT_HEIGHT = 0.100
SUPPORT_CENTER_Z = 0.087
BARREL_BASE_Z = 0.136
BARREL_LENGTH = 0.340
BARREL_OUTER_RADIUS = 0.027
BARREL_INNER_RADIUS = 0.022
LOWER_COLLAR_START_Z = 0.124
LOWER_COLLAR_LENGTH = 0.022
TOP_COLLAR_LENGTH = 0.028
TOP_COLLAR_OUTER_RADIUS = 0.031
ROD_CLEAR_RADIUS = 0.0105
HANDLE_JOINT_Z = BARREL_BASE_Z + BARREL_LENGTH + TOP_COLLAR_LENGTH
GAUGE_STEM_LENGTH = 0.018
GAUGE_BODY_DEPTH = 0.022
GAUGE_BEZEL_DEPTH = 0.007
GAUGE_RADIUS = 0.042
GAUGE_BEZEL_RADIUS = 0.045
GAUGE_ATTACH_Z = 0.068
BUTTON_X = 0.020
BUTTON_Z = 0.018
BUTTON_COLLAR_RADIUS = 0.009
BUTTON_HOLE_RADIUS = 0.0058
BUTTON_POCKET_DEPTH = 0.014
GAUGE_FRONT_Y = GAUGE_STEM_LENGTH + GAUGE_BODY_DEPTH + GAUGE_BEZEL_DEPTH
def _guide_housing_shape():
    housing = cq.Workplane("XY").box(GUIDE_LENGTH, GUIDE_DEPTH, GUIDE_HEIGHT).translate(
        (0.0, 0.0, GUIDE_CENTER_Z)
    )
    housing = housing.edges("|X").fillet(0.006)
    bore = (
        cq.Workplane("YZ")
        .circle(GUIDE_BORE_RADIUS)
        .extrude(GUIDE_LENGTH + 0.030)
        .translate((-(GUIDE_LENGTH + 0.030) / 2.0, 0.0, GUIDE_CENTER_Z))
    )
    return housing.cut(bore)
def _barrel_shell_shape():
    shell = (
        cq.Workplane("XY")
        .circle(BARREL_OUTER_RADIUS)
        .circle(BARREL_INNER_RADIUS)
        .extrude(BARREL_LENGTH)
        .translate((0.0, 0.0, BARREL_BASE_Z))
    )
    lower_collar = (
        cq.Workplane("XY")
        .circle(TOP_COLLAR_OUTER_RADIUS)
        .circle(BARREL_INNER_RADIUS)
        .extrude(LOWER_COLLAR_LENGTH)
        .translate((0.0, 0.0, LOWER_COLLAR_START_Z))
    )
    top_collar = (
        cq.Workplane("XY")
        .circle(TOP_COLLAR_OUTER_RADIUS)
        .circle(ROD_CLEAR_RADIUS)
        .extrude(TOP_COLLAR_LENGTH)
        .translate((0.0, 0.0, BARREL_BASE_Z + BARREL_LENGTH))
    )
    return shell.union(lower_collar).union(top_collar)
def _gauge_shape():
    stem = (
        cq.Workplane("XY")
        .box(0.020, 0.060, GAUGE_STEM_LENGTH)
        .translate((0.0, 0.0, GAUGE_STEM_LENGTH / 2.0))
    )
    body = (
        cq.Workplane("XY")
        .circle(GAUGE_RADIUS)
        .extrude(GAUGE_BODY_DEPTH)
        .translate((0.0, 0.0, GAUGE_STEM_LENGTH))
    )
    bezel = (
        cq.Workplane("XY")
        .circle(GAUGE_BEZEL_RADIUS)
        .extrude(GAUGE_BEZEL_DEPTH)
        .translate((0.0, 0.0, GAUGE_STEM_LENGTH + GAUGE_BODY_DEPTH))
    )
    button_collar = (
        cq.Workplane("XY")
        .center(BUTTON_X, BUTTON_Z)
        .circle(BUTTON_COLLAR_RADIUS)
        .extrude(0.010)
        .translate((0.0, 0.0, GAUGE_FRONT_Y - 0.010))
    )
    button_pocket = (
        cq.Workplane("XY")
        .center(BUTTON_X, BUTTON_Z)
        .circle(BUTTON_HOLE_RADIUS)
        .extrude(BUTTON_POCKET_DEPTH)
        .translate((0.0, 0.0, GAUGE_FRONT_Y - BUTTON_POCKET_DEPTH))
    )
    return (
        stem.union(body)
        .union(bezel)
        .union(button_collar)
        .cut(button_pocket)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="industrial_floor_pump")

    powder_black = model.material("powder_black", rgba=(0.17, 0.17, 0.18, 1.0))
    graphite = model.material("graphite", rgba=(0.27, 0.28, 0.30, 1.0))
    steel = model.material("steel", rgba=(0.72, 0.74, 0.77, 1.0))
    chrome = model.material("chrome", rgba=(0.84, 0.85, 0.88, 1.0))
    rubber = model.material("rubber", rgba=(0.09, 0.09, 0.10, 1.0))
    signal_red = model.material("signal_red", rgba=(0.72, 0.09, 0.08, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_guide_housing_shape(), "pump_guide_housing"),
        material=graphite,
        name="guide_housing",
    )
    body.visual(
        Box((SUPPORT_WIDTH, SUPPORT_DEPTH, SUPPORT_HEIGHT)),
        origin=Origin(xyz=(0.0, 0.0, SUPPORT_CENTER_Z)),
        material=powder_black,
        name="support_spine",
    )
    body.visual(
        Box((0.024, 0.009, 0.060)),
        origin=Origin(xyz=(0.0, 0.020, GAUGE_ATTACH_Z)),
        material=powder_black,
        name="gauge_mount",
    )
    body.visual(
        mesh_from_cadquery(_barrel_shell_shape(), "pump_barrel_shell"),
        material=powder_black,
        name="barrel_shell",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.0085, length=0.400),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=chrome,
        name="rod",
    )
    handle.visual(
        Cylinder(radius=0.009, length=0.240),
        origin=Origin(xyz=(0.0, 0.0, 0.208), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="crossbar",
    )
    handle.visual(
        Cylinder(radius=0.013, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=steel,
        name="rod_collar",
    )
    handle.visual(
        Cylinder(radius=0.016, length=0.095),
        origin=Origin(xyz=(-0.074, 0.0, 0.208), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="grip_0",
    )
    handle.visual(
        Cylinder(radius=0.016, length=0.095),
        origin=Origin(xyz=(0.074, 0.0, 0.208), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="grip_1",
    )

    stabilizer_bar = model.part("stabilizer_bar")
    stabilizer_bar.visual(
        Cylinder(radius=0.011, length=0.340),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="stabilizer_bar",
    )
    stabilizer_bar.visual(
        Cylinder(radius=0.015, length=0.050),
        origin=Origin(xyz=(-0.145, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="foot_0",
    )
    stabilizer_bar.visual(
        Cylinder(radius=0.015, length=0.050),
        origin=Origin(xyz=(0.145, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=rubber,
        name="foot_1",
    )
    stabilizer_bar.visual(
        Cylinder(radius=0.017, length=0.010),
        origin=Origin(xyz=(0.095, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="stop_collar",
    )

    gauge = model.part("gauge")
    gauge.visual(
        mesh_from_cadquery(_gauge_shape(), "pump_gauge"),
        material=powder_black,
        name="gauge_body",
    )

    release_button = model.part("release_button")
    release_button.visual(
        Cylinder(radius=0.0048, length=0.008),
        origin=Origin(xyz=(0.0, -0.003, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="button_stem",
    )
    release_button.visual(
        Cylinder(radius=0.0065, length=0.006),
        origin=Origin(xyz=(0.0, 0.004, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=signal_red,
        name="release_button",
    )

    model.articulation(
        "body_to_handle",
        ArticulationType.PRISMATIC,
        parent=body,
        child=handle,
        origin=Origin(xyz=(0.0, 0.0, HANDLE_JOINT_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=180.0,
            velocity=0.80,
            lower=-0.140,
            upper=0.060,
        ),
    )
    model.articulation(
        "body_to_stabilizer_bar",
        ArticulationType.PRISMATIC,
        parent=body,
        child=stabilizer_bar,
        origin=Origin(xyz=(0.0, 0.0, GUIDE_CENTER_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=50.0,
            velocity=0.25,
            lower=0.0,
            upper=0.100,
        ),
    )
    model.articulation(
        "body_to_gauge",
        ArticulationType.FIXED,
        parent=body,
        child=gauge,
        origin=Origin(xyz=(0.0, GUIDE_DEPTH / 2.0 - 0.0035, GAUGE_ATTACH_Z)),
    )
    model.articulation(
        "gauge_to_release_button",
        ArticulationType.PRISMATIC,
        parent=gauge,
        child=release_button,
        origin=Origin(xyz=(BUTTON_X, GAUGE_FRONT_Y, BUTTON_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=4.0,
            velocity=0.05,
            lower=-0.004,
            upper=0.0,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
