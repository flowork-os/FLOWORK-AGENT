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
import cadquery as cq
BASE_LENGTH = 0.35
BASE_WIDTH = 0.18
BASE_THICKNESS = 0.022
BASE_CORNER_RADIUS = 0.016
BARREL_CENTER_X = 0.062
BARREL_OUTER_RADIUS = 0.035
BARREL_INNER_RADIUS = 0.0315
BARREL_HEIGHT = 0.36
BARREL_BOTTOM_CAP = 0.012
BARREL_TOP_RING = 0.011
BARREL_LOWER_FLANGE = 0.018
ROD_GUIDE_RADIUS = 0.012
GLAND_HEIGHT = 0.012
YOKE_Z = 0.567
YOKE_LENGTH = 0.182
YOKE_WIDTH = 0.030
YOKE_THICKNESS = 0.020
HANDLE_STEM_RADIUS = 0.014
HANDLE_STEM_HEIGHT = 0.094
GRIP_RADIUS = 0.015
GRIP_LENGTH = 0.28
GRIP_SLEEVE_RADIUS = 0.0185
GRIP_SLEEVE_LENGTH = 0.064
GRIP_CENTER_Z = 0.118
ROD_RADIUS = 0.012
ROD_LENGTH = 0.322
PUMP_STROKE = 0.15
def _base_plate_shape() -> cq.Workplane:
    plate = cq.Workplane("XY").box(
        BASE_LENGTH,
        BASE_WIDTH,
        BASE_THICKNESS,
        centered=(True, True, False),
    )
    plate = plate.edges("|Z").fillet(BASE_CORNER_RADIUS)

    toe_ribs = (
        cq.Workplane("XY")
        .pushPoints(
            [
                (-0.115, 0.0),
                (0.115, 0.0),
            ]
        )
        .rect(0.065, BASE_WIDTH * 0.78)
        .extrude(0.005)
        .translate((0.0, 0.0, BASE_THICKNESS))
    )

    center_spine = (
        cq.Workplane("XY")
        .rect(0.12, 0.05)
        .extrude(0.012)
        .translate((0.0, 0.0, BASE_THICKNESS))
    )

    return plate.union(toe_ribs).union(center_spine)
def _barrel_shape(center_x: float) -> cq.Workplane:
    wall = (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(BARREL_OUTER_RADIUS)
        .circle(BARREL_INNER_RADIUS)
        .extrude(BARREL_HEIGHT)
    )

    bottom_disk = (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(BARREL_INNER_RADIUS)
        .extrude(BARREL_BOTTOM_CAP)
    )

    lower_flange = (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(BARREL_OUTER_RADIUS + 0.006)
        .circle(BARREL_OUTER_RADIUS)
        .extrude(BARREL_LOWER_FLANGE)
    )

    top_ring = (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(BARREL_INNER_RADIUS)
        .circle(ROD_GUIDE_RADIUS)
        .extrude(BARREL_TOP_RING)
        .translate((0.0, 0.0, BARREL_HEIGHT - BARREL_TOP_RING))
    )

    gland = (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(ROD_GUIDE_RADIUS + 0.004)
        .circle(ROD_GUIDE_RADIUS)
        .extrude(GLAND_HEIGHT)
        .translate((0.0, 0.0, BARREL_HEIGHT))
    )

    return (
        wall.union(bottom_disk)
        .union(lower_flange)
        .union(top_ring)
        .union(gland)
        .translate((0.0, 0.0, BASE_THICKNESS))
    )
def _gauge_shape() -> cq.Workplane:
    bracket = (
        cq.Workplane("XY")
        .box(
            0.07,
            0.028,
            0.058,
            centered=(True, True, False),
        )
        .translate((0.0, BASE_WIDTH * 0.31, BASE_THICKNESS))
    )

    gauge_body = (
        cq.Workplane("XZ")
        .center(0.0, BASE_THICKNESS + 0.064)
        .circle(0.034)
        .extrude(0.018)
        .translate((0.0, BASE_WIDTH / 2.0 - 0.018, 0.0))
    )

    return bracket.union(gauge_body)
def _handle_bridge_shape() -> cq.Workplane:
    yoke = cq.Workplane("XY").box(YOKE_LENGTH, YOKE_WIDTH, YOKE_THICKNESS)

    stem = (
        cq.Workplane("XY")
        .circle(HANDLE_STEM_RADIUS)
        .extrude(HANDLE_STEM_HEIGHT)
        .translate((0.0, 0.0, YOKE_THICKNESS / 2.0))
    )

    grip = (
        cq.Workplane("YZ")
        .circle(GRIP_RADIUS)
        .extrude(GRIP_LENGTH)
        .translate((-GRIP_LENGTH / 2.0, 0.0, GRIP_CENTER_Z))
    )

    left_sleeve = (
        cq.Workplane("YZ")
        .circle(GRIP_SLEEVE_RADIUS)
        .extrude(GRIP_SLEEVE_LENGTH)
        .translate((-GRIP_LENGTH / 2.0, 0.0, GRIP_CENTER_Z))
    )
    right_sleeve = (
        cq.Workplane("YZ")
        .circle(GRIP_SLEEVE_RADIUS)
        .extrude(GRIP_SLEEVE_LENGTH)
        .translate((GRIP_LENGTH / 2.0 - GRIP_SLEEVE_LENGTH, 0.0, GRIP_CENTER_Z))
    )

    return yoke.union(stem).union(grip).union(left_sleeve).union(right_sleeve)
def _rod_shape(center_x: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .center(center_x, 0.0)
        .circle(ROD_RADIUS)
        .extrude(ROD_LENGTH)
        .translate((0.0, 0.0, -ROD_LENGTH))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="double_barrel_floor_pump")

    model.material("base_black", rgba=(0.13, 0.14, 0.15, 1.0))
    model.material("steel", rgba=(0.73, 0.75, 0.78, 1.0))
    model.material("gauge_gray", rgba=(0.84, 0.85, 0.86, 1.0))
    model.material("handle_black", rgba=(0.09, 0.09, 0.10, 1.0))

    pump_body = model.part("pump_body")
    pump_body.visual(
        mesh_from_cadquery(_base_plate_shape(), "pump_base_plate"),
        material="base_black",
        name="base_plate",
    )
    pump_body.visual(
        mesh_from_cadquery(_barrel_shape(-BARREL_CENTER_X), "left_barrel_shell"),
        material="steel",
        name="left_barrel",
    )
    pump_body.visual(
        mesh_from_cadquery(_barrel_shape(BARREL_CENTER_X), "right_barrel_shell"),
        material="steel",
        name="right_barrel",
    )
    pump_body.visual(
        mesh_from_cadquery(_gauge_shape(), "front_gauge_housing"),
        material="gauge_gray",
        name="front_gauge",
    )

    handle_assembly = model.part("handle_assembly")
    handle_assembly.visual(
        mesh_from_cadquery(_handle_bridge_shape(), "t_handle_bridge"),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material="handle_black",
        name="handle_bridge",
    )
    handle_assembly.visual(
        mesh_from_cadquery(_rod_shape(-BARREL_CENTER_X), "left_pump_rod"),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material="steel",
        name="left_rod",
    )
    handle_assembly.visual(
        mesh_from_cadquery(_rod_shape(BARREL_CENTER_X), "right_pump_rod"),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material="steel",
        name="right_rod",
    )

    model.articulation(
        "body_to_handle",
        ArticulationType.PRISMATIC,
        parent=pump_body,
        child=handle_assembly,
        origin=Origin(xyz=(0.0, 0.0, YOKE_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=180.0,
            velocity=0.7,
            lower=-PUMP_STROKE,
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
