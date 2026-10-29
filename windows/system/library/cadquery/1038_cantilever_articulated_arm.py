# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cantilever_articulated_arm, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cantilever_articulated_arm

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
from math import pi
import cadquery as cq
BASE_LENGTH = 0.62
BASE_WIDTH = 0.42
BASE_THICKNESS = 0.065
PLINTH_LENGTH = 0.40
PLINTH_WIDTH = 0.26
PLINTH_HEIGHT = 0.095
COLUMN_LENGTH = 0.23
COLUMN_WIDTH = 0.19
COLUMN_HEIGHT = 0.60
SHOULDER_X = 0.31
SHOULDER_Z = BASE_THICKNESS + PLINTH_HEIGHT + COLUMN_HEIGHT + 0.055
SHOULDER_OUTER_WIDTH = 0.118
SHOULDER_PLATE_THICKNESS = 0.022
SHOULDER_GAP = SHOULDER_OUTER_WIDTH - 2.0 * SHOULDER_PLATE_THICKNESS
UPPER_LINK_LENGTH = 0.64
ELBOW_OUTER_WIDTH = 0.086
ELBOW_PLATE_THICKNESS = 0.020
ELBOW_GAP = ELBOW_OUTER_WIDTH - 2.0 * ELBOW_PLATE_THICKNESS
FOREARM_LENGTH = 0.42
FOREARM_WIDTH = 0.044
TOOL_FLANGE_RADIUS = 0.072
TOOL_FLANGE_THICKNESS = 0.016
TOOL_NOSE_RADIUS = 0.028
TOOL_NOSE_LENGTH = 0.020
def _pedestal_structure_shape() -> cq.Workplane:
    base_plate = (
        cq.Workplane("XY")
        .box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS)
        .translate((0.0, 0.0, BASE_THICKNESS / 2.0))
        .edges("|Z")
        .fillet(0.030)
        .edges(">Z")
        .fillet(0.010)
    )

    plinth = (
        cq.Workplane("XY")
        .box(PLINTH_LENGTH, PLINTH_WIDTH, PLINTH_HEIGHT)
        .translate((0.0, 0.0, BASE_THICKNESS + PLINTH_HEIGHT / 2.0))
        .edges("|Z")
        .fillet(0.022)
    )

    column = (
        cq.Workplane("XY")
        .box(COLUMN_LENGTH, COLUMN_WIDTH, COLUMN_HEIGHT)
        .translate((0.0, 0.0, BASE_THICKNESS + PLINTH_HEIGHT + COLUMN_HEIGHT / 2.0))
        .edges("|Z")
        .fillet(0.028)
    )

    shoulder_body = (
        cq.Workplane("XY")
        .box(0.150, 0.150, 0.165)
        .translate((SHOULDER_X - 0.120, 0.0, SHOULDER_Z - 0.015))
        .edges("|Y")
        .fillet(0.016)
    )

    offset_web = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.060, BASE_THICKNESS + PLINTH_HEIGHT + 0.14),
                (-0.020, BASE_THICKNESS + PLINTH_HEIGHT + COLUMN_HEIGHT - 0.06),
                (SHOULDER_X - 0.200, SHOULDER_Z - 0.110),
                (SHOULDER_X - 0.070, SHOULDER_Z - 0.095),
                (SHOULDER_X - 0.070, SHOULDER_Z - 0.040),
                (SHOULDER_X - 0.205, SHOULDER_Z - 0.030),
                (-0.030, BASE_THICKNESS + PLINTH_HEIGHT + COLUMN_HEIGHT - 0.11),
                (-0.060, BASE_THICKNESS + PLINTH_HEIGHT + 0.20),
            ]
        )
        .close()
        .extrude(0.064, both=True)
    )

    yoke_center_y = SHOULDER_GAP / 2.0 + SHOULDER_PLATE_THICKNESS / 2.0
    yoke_plate = (
        cq.Workplane("XY")
        .box(0.095, SHOULDER_PLATE_THICKNESS, 0.145)
        .translate((SHOULDER_X + 0.010, yoke_center_y, SHOULDER_Z))
    )
    yoke_boss = (
        cq.Workplane("XZ")
        .center(SHOULDER_X, SHOULDER_Z)
        .circle(0.048)
        .extrude(SHOULDER_PLATE_THICKNESS)
        .translate((0.0, yoke_center_y - SHOULDER_PLATE_THICKNESS / 2.0 - 0.001, 0.0))
    )
    left_plate = yoke_plate.union(yoke_boss)
    right_plate = left_plate.mirror("XZ")

    top_bridge = (
        cq.Workplane("XY")
        .box(0.050, SHOULDER_OUTER_WIDTH, 0.022)
        .translate((SHOULDER_X - 0.030, 0.0, SHOULDER_Z + 0.082))
    )

    pedestal = (
        base_plate.union(plinth)
        .union(column)
        .union(shoulder_body)
        .union(offset_web)
        .union(left_plate)
        .union(right_plate)
        .union(top_bridge)
    )

    return pedestal
def _upper_link_structure_shape() -> cq.Workplane:
    shoulder_hub_width = SHOULDER_GAP - 0.010
    shoulder_hub = (
        cq.Workplane("XZ")
        .circle(0.032)
        .extrude(shoulder_hub_width / 2.0, both=True)
    )

    main_beam = (
        cq.Workplane("XY")
        .box(0.470, 0.050, 0.082)
        .translate((0.295, 0.0, 0.0))
        .edges("|Y")
        .fillet(0.010)
    )
    lower_rib = (
        cq.Workplane("XY")
        .box(0.340, 0.028, 0.022)
        .translate((0.300, 0.0, -0.032))
    )
    top_rib = (
        cq.Workplane("XY")
        .box(0.220, 0.024, 0.018)
        .translate((0.240, 0.0, 0.028))
    )

    clevis_center_y = ELBOW_GAP / 2.0 + ELBOW_PLATE_THICKNESS / 2.0
    elbow_transition = (
        cq.Workplane("XY")
        .box(0.060, ELBOW_OUTER_WIDTH, 0.072)
        .translate((UPPER_LINK_LENGTH - 0.095, 0.0, 0.0))
    )
    elbow_plate = (
        cq.Workplane("XY")
        .box(0.090, ELBOW_PLATE_THICKNESS, 0.112)
        .translate((UPPER_LINK_LENGTH - 0.005, clevis_center_y, 0.0))
    )
    elbow_boss = (
        cq.Workplane("XZ")
        .center(UPPER_LINK_LENGTH, 0.0)
        .circle(0.040)
        .extrude(ELBOW_PLATE_THICKNESS)
        .translate((0.0, clevis_center_y - ELBOW_PLATE_THICKNESS / 2.0 - 0.001, 0.0))
    )
    left_plate = elbow_plate.union(elbow_boss)
    right_plate = left_plate.mirror("XZ")

    return (
        shoulder_hub.union(main_beam)
        .union(lower_rib)
        .union(top_rib)
        .union(elbow_transition)
        .union(left_plate)
        .union(right_plate)
    )
def _upper_link_cover_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(0.240, 0.032, 0.020)
        .translate((0.255, 0.0, 0.034))
        .edges("|Y")
        .fillet(0.008)
    )
def _forearm_structure_shape() -> cq.Workplane:
    elbow_hub_width = ELBOW_GAP - 0.010
    elbow_hub = (
        cq.Workplane("XZ")
        .circle(0.032)
        .extrude(elbow_hub_width / 2.0, both=True)
    )

    main_beam = (
        cq.Workplane("XY")
        .box(0.275, 0.040, 0.070)
        .translate((0.195, 0.0, 0.0))
        .edges("|Y")
        .fillet(0.008)
    )
    lower_rib = (
        cq.Workplane("XY")
        .box(0.190, 0.024, 0.018)
        .translate((0.190, 0.0, -0.028))
    )
    wrist_bridge = (
        cq.Workplane("XY")
        .box(0.060, FOREARM_WIDTH, 0.072)
        .translate((FOREARM_LENGTH - 0.070, 0.0, 0.0))
    )
    wrist_ring_outer = (
        cq.Workplane("YZ")
        .circle(0.055)
        .extrude(0.046, both=True)
        .translate((FOREARM_LENGTH, 0.0, 0.0))
    )
    wrist_ring_inner = (
        cq.Workplane("YZ")
        .circle(0.034)
        .extrude(0.048, both=True)
        .translate((FOREARM_LENGTH, 0.0, 0.0))
    )
    wrist_ring = wrist_ring_outer.cut(wrist_ring_inner)

    return elbow_hub.union(main_beam).union(lower_rib).union(wrist_bridge).union(wrist_ring)
def _forearm_cover_shape() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(0.170, 0.026, 0.018)
        .translate((0.190, 0.0, 0.028))
        .edges("|Y")
        .fillet(0.007)
    )
def _tool_flange_structure_shape() -> cq.Workplane:
    hub = (
        cq.Workplane("YZ")
        .circle(0.029)
        .extrude(0.030)
        .translate((-0.010, 0.0, 0.0))
    )
    flange = (
        cq.Workplane("YZ")
        .circle(TOOL_FLANGE_RADIUS)
        .extrude(TOOL_FLANGE_THICKNESS)
        .translate((0.026, 0.0, 0.0))
    )
    nose = (
        cq.Workplane("YZ")
        .circle(TOOL_NOSE_RADIUS)
        .extrude(TOOL_NOSE_LENGTH)
        .translate(
            (
                0.026 + TOOL_FLANGE_THICKNESS,
                0.0,
                0.0,
            )
        )
    )
    orientation_lug = (
        cq.Workplane("XY")
        .box(0.012, 0.022, 0.012)
        .translate((0.034, 0.0, 0.042))
    )

    body = hub.union(flange).union(nose).union(orientation_lug)

    bolt_cuts = (
        cq.Workplane("YZ")
        .pushPoints([(0.040, 0.0), (-0.040, 0.0), (0.0, 0.040), (0.0, -0.040)])
        .circle(0.0055)
        .extrude(0.080, both=True)
        .translate((0.026 + TOOL_FLANGE_THICKNESS / 2.0, 0.0, 0.0))
    )
    key_flat = (
        cq.Workplane("XY")
        .box(0.020, 0.040, 0.020)
        .translate((0.026 + TOOL_FLANGE_THICKNESS / 2.0, 0.0, 0.064))
    )
    return body.cut(bolt_cuts).cut(key_flat)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="service_arm")

    model.material("cast_iron", rgba=(0.29, 0.31, 0.34, 1.0))
    model.material("arm_gray", rgba=(0.54, 0.57, 0.61, 1.0))
    model.material("cover_black", rgba=(0.12, 0.13, 0.14, 1.0))
    model.material("machined_cap", rgba=(0.76, 0.78, 0.81, 1.0))
    model.material("graphite", rgba=(0.24, 0.25, 0.28, 1.0))

    pedestal = model.part("pedestal")
    pedestal.visual(
        mesh_from_cadquery(_pedestal_structure_shape(), "pedestal_structure"),
        material="cast_iron",
        name="pedestal_structure",
    )
    pedestal.inertial = Inertial.from_geometry(
        Box((0.36, 0.28, 0.86)),
        mass=46.0,
        origin=Origin(xyz=(0.0, 0.0, 0.43)),
    )

    upper_link = model.part("upper_link")
    upper_link.visual(
        mesh_from_cadquery(_upper_link_structure_shape(), "upper_link_structure"),
        material="arm_gray",
        name="upper_link_structure",
    )
    upper_link.visual(
        mesh_from_cadquery(_upper_link_cover_shape(), "upper_link_cover"),
        material="cover_black",
        name="upper_link_cover",
    )
    upper_link.inertial = Inertial.from_geometry(
        Box((0.66, 0.10, 0.16)),
        mass=12.0,
        origin=Origin(xyz=(0.32, 0.0, 0.0)),
    )

    forearm = model.part("forearm")
    forearm.visual(
        mesh_from_cadquery(_forearm_structure_shape(), "forearm_structure"),
        material="arm_gray",
        name="forearm_structure",
    )
    forearm.visual(
        mesh_from_cadquery(_forearm_cover_shape(), "forearm_cover"),
        material="cover_black",
        name="forearm_cover",
    )
    forearm.inertial = Inertial.from_geometry(
        Box((0.44, 0.08, 0.12)),
        mass=6.8,
        origin=Origin(xyz=(0.21, 0.0, 0.0)),
    )

    tool_flange = model.part("tool_flange")
    tool_flange.visual(
        mesh_from_cadquery(_tool_flange_structure_shape(), "tool_flange_structure"),
        material="machined_cap",
        name="tool_flange_structure",
    )
    tool_flange.inertial = Inertial.from_geometry(
        Box((0.085, 0.145, 0.145)),
        mass=1.3,
        origin=Origin(xyz=(0.040, 0.0, 0.0)),
    )

    model.articulation(
        "shoulder",
        ArticulationType.REVOLUTE,
        parent=pedestal,
        child=upper_link,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.55, upper=1.18, effort=220.0, velocity=0.9),
    )
    model.articulation(
        "elbow",
        ArticulationType.REVOLUTE,
        parent=upper_link,
        child=forearm,
        origin=Origin(xyz=(UPPER_LINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-1.45, upper=1.10, effort=140.0, velocity=1.2),
    )
    model.articulation(
        "wrist",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=tool_flange,
        origin=Origin(xyz=(FOREARM_LENGTH, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=-2.6, upper=2.6, effort=50.0, velocity=2.2),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
