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
import cadquery as cq
BASE_LENGTH = 0.240
BASE_WIDTH = 0.180
BASE_HEIGHT = 0.020
TOWER_WIDTH = 0.090
TOWER_DEPTH = 0.064
TOWER_COLUMN_HEIGHT = 0.176
TOP_PAD_RADIUS = 0.045
TOP_PAD_HEIGHT = 0.014
TOWER_TOP_Z = BASE_HEIGHT + TOWER_COLUMN_HEIGHT + TOP_PAD_HEIGHT
UPPER_LINK_LENGTH = 0.405
UPPER_LINK_Z = 0.030
FORELINK_LENGTH = 0.265
WRIST_BODY_LENGTH = 0.145
FACEPLATE_THICKNESS = 0.008
UPPER_CLEVIS_GAP = 0.054
FORE_CLEVIS_GAP = 0.046
CHEEK_THICKNESS = 0.010
def _box(length: float, width: float, height: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(length, width, height).translate(center)
def _y_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((0.0, 0.0, -length / 2.0))
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate(center)
    )
def _z_cylinder(
    radius: float,
    length: float,
    center: tuple[float, float, float],
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((center[0], center[1], center[2] - length / 2.0))
    )
def _tower_shape() -> cq.Workplane:
    base = _box(BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT, (0.0, 0.0, BASE_HEIGHT / 2.0))
    base = base.edges("|Z").fillet(0.010)

    column = _box(
        TOWER_WIDTH,
        TOWER_DEPTH,
        TOWER_COLUMN_HEIGHT,
        (0.0, 0.0, BASE_HEIGHT + TOWER_COLUMN_HEIGHT / 2.0),
    )
    column = column.edges("|Z").fillet(0.010)

    top_pad = _z_cylinder(
        TOP_PAD_RADIUS,
        TOP_PAD_HEIGHT,
        (0.0, 0.0, BASE_HEIGHT + TOWER_COLUMN_HEIGHT + TOP_PAD_HEIGHT / 2.0),
    )
    front_gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.030, BASE_HEIGHT),
                (0.030, BASE_HEIGHT),
                (0.030, BASE_HEIGHT + 0.050),
                (0.012, BASE_HEIGHT + 0.120),
                (-0.012, BASE_HEIGHT + 0.120),
                (-0.030, BASE_HEIGHT + 0.050),
            ]
        )
        .close()
        .extrude(0.020)
        .translate((0.0, -0.010, 0.0))
    )
    rear_gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.030, BASE_HEIGHT),
                (0.030, BASE_HEIGHT),
                (0.030, BASE_HEIGHT + 0.050),
                (0.012, BASE_HEIGHT + 0.118),
                (-0.012, BASE_HEIGHT + 0.118),
                (-0.030, BASE_HEIGHT + 0.050),
            ]
        )
        .close()
        .extrude(0.020)
        .translate((0.0, BASE_WIDTH / 2.0 - 0.010, 0.0))
    )

    tower = base.union(column).union(top_pad).union(front_gusset).union(rear_gusset)

    hole_points = [
        (-0.075, -0.050),
        (-0.075, 0.050),
        (0.075, -0.050),
        (0.075, 0.050),
    ]
    tower = (
        tower.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .pushPoints(hole_points)
        .hole(0.012)
    )
    return tower
def _upper_link_shape() -> cq.Workplane:
    collar = _z_cylinder(0.030, 0.050, (0.0, 0.0, 0.025))
    collar_flange = _z_cylinder(0.038, 0.010, (0.0, 0.0, 0.005))

    beam = _box(0.340, 0.046, 0.036, (0.195, 0.0, UPPER_LINK_Z))
    beam = beam.edges("|X").fillet(0.005)
    top_rib = _box(0.200, 0.024, 0.012, (0.205, 0.0, UPPER_LINK_Z + 0.020))

    root_shoulder = _box(0.080, 0.056, 0.042, (0.040, 0.0, UPPER_LINK_Z))

    cheek_y = UPPER_CLEVIS_GAP / 2.0 + CHEEK_THICKNESS / 2.0
    cheek_left = _box(0.030, CHEEK_THICKNESS, 0.056, (UPPER_LINK_LENGTH - 0.015, cheek_y, 0.030))
    cheek_right = _box(0.030, CHEEK_THICKNESS, 0.056, (UPPER_LINK_LENGTH - 0.015, -cheek_y, 0.030))
    clevis_bridge = _box(0.046, 0.074, 0.010, (UPPER_LINK_LENGTH - 0.023, 0.0, 0.055))
    clevis_riser = _box(0.034, 0.032, 0.022, (UPPER_LINK_LENGTH - 0.058, 0.0, 0.043))

    return (
        collar.union(collar_flange)
        .union(root_shoulder)
        .union(beam)
        .union(top_rib)
        .union(cheek_left)
        .union(cheek_right)
        .union(clevis_bridge)
        .union(clevis_riser)
    )
def _forelink_shape() -> cq.Workplane:
    elbow_barrel = _y_cylinder(0.019, UPPER_CLEVIS_GAP, (0.019, 0.0, 0.0))
    root_block = _box(0.058, 0.044, 0.036, (0.029, 0.0, 0.0))

    beam = _box(0.190, 0.036, 0.032, (0.145, 0.0, 0.0))
    beam = beam.edges("|X").fillet(0.004)
    top_rib = _box(0.112, 0.018, 0.010, (0.148, 0.0, 0.017))

    cheek_y = FORE_CLEVIS_GAP / 2.0 + CHEEK_THICKNESS / 2.0
    cheek_left = _box(0.022, CHEEK_THICKNESS, 0.054, (FORELINK_LENGTH - 0.011, cheek_y, 0.0))
    cheek_right = _box(0.022, CHEEK_THICKNESS, 0.054, (FORELINK_LENGTH - 0.011, -cheek_y, 0.0))
    clevis_bridge = _box(0.036, 0.064, 0.010, (FORELINK_LENGTH - 0.021, 0.0, 0.028))
    clevis_riser = _box(0.026, 0.026, 0.020, (FORELINK_LENGTH - 0.040, 0.0, 0.018))

    return (
        elbow_barrel.union(root_block)
        .union(beam)
        .union(top_rib)
        .union(cheek_left)
        .union(cheek_right)
        .union(clevis_bridge)
        .union(clevis_riser)
    )
def _wrist_body_shape() -> cq.Workplane:
    wrist_barrel = _y_cylinder(0.016, FORE_CLEVIS_GAP, (0.016, 0.0, 0.0))
    root_block = _box(0.044, 0.030, 0.026, (0.022, 0.0, 0.0))
    body = _box(0.118, 0.026, 0.030, (0.079, 0.0, 0.0))
    body = body.edges("|X").fillet(0.003)
    top_rib = _box(0.064, 0.014, 0.008, (0.090, 0.0, 0.016))
    nose = _box(0.018, 0.022, 0.026, (0.136, 0.0, 0.0))
    return wrist_barrel.union(root_block).union(body).union(top_rib).union(nose)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="tower_mounted_tooling_arm")

    model.material("tower_charcoal", rgba=(0.18, 0.19, 0.21, 1.0))
    model.material("arm_aluminum", rgba=(0.70, 0.72, 0.75, 1.0))
    model.material("forelink_aluminum", rgba=(0.76, 0.78, 0.81, 1.0))
    model.material("wrist_dark", rgba=(0.28, 0.30, 0.33, 1.0))
    model.material("plate_steel", rgba=(0.84, 0.85, 0.87, 1.0))

    tower = model.part("tower")
    tower.visual(
        mesh_from_cadquery(_tower_shape(), "tower_body"),
        material="tower_charcoal",
        name="tower_body",
    )
    tower.inertial = Inertial.from_geometry(
        Box((BASE_LENGTH, BASE_WIDTH, TOWER_TOP_Z)),
        mass=24.0,
        origin=Origin(xyz=(0.0, 0.0, TOWER_TOP_Z / 2.0)),
    )

    upper_link = model.part("upper_link")
    upper_link.visual(
        mesh_from_cadquery(_upper_link_shape(), "upper_link_body"),
        material="arm_aluminum",
        name="upper_link_body",
    )
    upper_link.inertial = Inertial.from_geometry(
        Box((UPPER_LINK_LENGTH, 0.080, 0.070)),
        mass=6.2,
        origin=Origin(xyz=(UPPER_LINK_LENGTH * 0.46, 0.0, 0.030)),
    )

    forelink = model.part("forelink")
    forelink.visual(
        mesh_from_cadquery(_forelink_shape(), "forelink_body"),
        material="forelink_aluminum",
        name="forelink_body",
    )
    forelink.inertial = Inertial.from_geometry(
        Box((FORELINK_LENGTH, 0.062, 0.060)),
        mass=3.4,
        origin=Origin(xyz=(FORELINK_LENGTH * 0.45, 0.0, 0.0)),
    )

    wrist = model.part("wrist_cartridge")
    wrist.visual(
        mesh_from_cadquery(_wrist_body_shape(), "wrist_body"),
        material="wrist_dark",
        name="wrist_body",
    )
    wrist.visual(
        Box((FACEPLATE_THICKNESS, 0.062, 0.088)),
        origin=Origin(xyz=(WRIST_BODY_LENGTH + FACEPLATE_THICKNESS / 2.0 - 0.0005, 0.0, 0.0)),
        material="plate_steel",
        name="faceplate",
    )
    wrist.inertial = Inertial.from_geometry(
        Box((WRIST_BODY_LENGTH + FACEPLATE_THICKNESS, 0.090, 0.090)),
        mass=1.7,
        origin=Origin(xyz=(0.086, 0.0, 0.0)),
    )

    model.articulation(
        "tower_yaw",
        ArticulationType.REVOLUTE,
        parent=tower,
        child=upper_link,
        origin=Origin(xyz=(0.0, 0.0, TOWER_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=70.0,
            velocity=1.2,
            lower=-1.35,
            upper=1.35,
        ),
    )
    model.articulation(
        "upper_to_forelink",
        ArticulationType.REVOLUTE,
        parent=upper_link,
        child=forelink,
        origin=Origin(xyz=(UPPER_LINK_LENGTH, 0.0, UPPER_LINK_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=1.5,
            lower=-0.55,
            upper=1.15,
        ),
    )
    model.articulation(
        "forelink_to_wrist",
        ArticulationType.REVOLUTE,
        parent=forelink,
        child=wrist,
        origin=Origin(xyz=(FORELINK_LENGTH, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=2.0,
            lower=-1.35,
            upper=1.35,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
