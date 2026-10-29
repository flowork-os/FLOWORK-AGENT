# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cash_register, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cash_register

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
BASE_FRONT_X = 0.20
BASE_REAR_X = -0.18
BASE_WIDTH = 0.42
BASE_HEIGHT = 0.115
DRAWER_JOINT_Z = 0.050
DRAWER_TRAVEL = 0.17
DRAWER_SEATED_OFFSET = 0.003
DISPLAY_HINGE_X = -0.145
DISPLAY_HINGE_Z = 0.262
DISPLAY_BASELINE_TILT_DEG = -12.0
def _body_shape() -> cq.Workplane:
    base_depth = BASE_FRONT_X - BASE_REAR_X
    base_center_x = (BASE_FRONT_X + BASE_REAR_X) / 2.0

    base = (
        cq.Workplane("XY")
        .box(base_depth, BASE_WIDTH, BASE_HEIGHT)
        .translate((base_center_x, 0.0, BASE_HEIGHT / 2.0))
        .edges("|Z")
        .fillet(0.010)
    )

    drawer_cavity = (
        cq.Workplane("XY")
        .box(0.300, 0.340, 0.074)
        .translate((0.055, 0.0, DRAWER_JOINT_Z))
    )

    upper_housing = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.105, BASE_HEIGHT),
                (0.135, BASE_HEIGHT),
                (0.135, 0.150),
                (0.055, 0.205),
                (-0.060, 0.224),
                (-0.105, 0.186),
            ]
        )
        .close()
        .extrude(0.300)
        .translate((0.0, 0.150, 0.0))
    )

    display_support = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.168, BASE_HEIGHT),
                (-0.122, BASE_HEIGHT),
                (-0.122, 0.238),
                (-0.148, 0.238),
                (-0.168, 0.193),
            ]
        )
        .close()
        .extrude(0.090)
        .translate((0.0, 0.045, 0.0))
    )

    hinge_shelf = (
        cq.Workplane("XY")
        .box(0.060, 0.110, 0.014)
        .translate((DISPLAY_HINGE_X, 0.0, DISPLAY_HINGE_Z - 0.017))
    )

    return base.union(upper_housing).union(display_support).union(hinge_shelf).cut(drawer_cavity)
def _drawer_shape() -> cq.Workplane:
    tray_outer = (
        cq.Workplane("XY")
        .box(0.275, 0.326, 0.060)
        .translate((-0.1375, 0.0, 0.0))
    )
    tray_inner = (
        cq.Workplane("XY")
        .box(0.255, 0.306, 0.052)
        .translate((-0.132, 0.0, 0.012))
    )
    front_panel = (
        cq.Workplane("XY")
        .box(0.020, 0.348, 0.082)
        .translate((0.010, 0.0, 0.0))
    )
    left_skid = (
        cq.Workplane("XY")
        .box(0.235, 0.028, 0.007)
        .translate((-0.125, -0.105, -0.0335))
    )
    right_skid = (
        cq.Workplane("XY")
        .box(0.235, 0.028, 0.007)
        .translate((-0.125, 0.105, -0.0335))
    )

    drawer = tray_outer.cut(tray_inner).union(front_panel).union(left_skid).union(right_skid)
    drawer = (
        drawer.faces(">X")
        .workplane()
        .center(0.0, 0.010)
        .rect(0.110, 0.018)
        .cutBlind(0.010)
    )
    return drawer
def _display_shape() -> cq.Workplane:
    housing = (
        cq.Workplane("XY")
        .box(0.040, 0.148, 0.090)
        .translate((-0.022, 0.0, 0.052))
        .edges("|Y")
        .fillet(0.006)
    )
    housing = (
        housing.faces("<X")
        .workplane()
        .rect(0.118, 0.056)
        .cutBlind(0.004)
    )

    hinge_barrel = (
        cq.Workplane("XZ")
        .circle(0.010)
        .extrude(0.110)
        .translate((0.0, -0.055, 0.0))
    )

    return housing.union(hinge_barrel).rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), DISPLAY_BASELINE_TILT_DEG)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="countertop_cash_register")

    body_color = model.material("body_color", rgba=(0.23, 0.24, 0.26, 1.0))
    drawer_color = model.material("drawer_color", rgba=(0.19, 0.20, 0.22, 1.0))
    display_color = model.material("display_color", rgba=(0.07, 0.08, 0.09, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "body_shell"),
        material=body_color,
        name="body_shell",
    )

    drawer = model.part("drawer")
    drawer.visual(
        mesh_from_cadquery(_drawer_shape(), "drawer"),
        material=drawer_color,
        name="drawer",
    )

    display = model.part("display")
    display.visual(
        mesh_from_cadquery(_display_shape(), "display_housing"),
        material=display_color,
        name="display_housing",
    )

    model.articulation(
        "body_to_drawer",
        ArticulationType.PRISMATIC,
        parent=body,
        child=drawer,
        origin=Origin(xyz=(BASE_FRONT_X + DRAWER_SEATED_OFFSET, 0.0, DRAWER_JOINT_Z)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=DRAWER_TRAVEL, effort=80.0, velocity=0.28),
    )
    model.articulation(
        "body_to_display",
        ArticulationType.REVOLUTE,
        parent=body,
        child=display,
        origin=Origin(xyz=(DISPLAY_HINGE_X, 0.0, DISPLAY_HINGE_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            lower=math.radians(-12.0),
            upper=math.radians(28.0),
            effort=6.0,
            velocity=1.5,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
