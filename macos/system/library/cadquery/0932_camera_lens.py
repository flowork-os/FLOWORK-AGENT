# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
REAR_FLANGE_LEN = 0.004
APERTURE_SUPPORT_Z = REAR_FLANGE_LEN
APERTURE_SUPPORT_LEN = 0.012
APERTURE_RING_LEN = 0.010
APERTURE_CENTER_Z = APERTURE_SUPPORT_Z + APERTURE_SUPPORT_LEN * 0.5
REAR_FIXED_BAND_Z = APERTURE_SUPPORT_Z + APERTURE_SUPPORT_LEN
REAR_FIXED_BAND_LEN = 0.006
FOCUS_SUPPORT_Z = REAR_FIXED_BAND_Z + REAR_FIXED_BAND_LEN
FOCUS_SUPPORT_LEN = 0.036
FOCUS_RING_LEN = 0.034
FOCUS_CENTER_Z = FOCUS_SUPPORT_Z + FOCUS_SUPPORT_LEN * 0.5
FRONT_BARREL_Z = FOCUS_SUPPORT_Z + FOCUS_SUPPORT_LEN
FRONT_BARREL_LEN = 0.014
HOOD_MOUNT_Z = FRONT_BARREL_Z + FRONT_BARREL_LEN
HOOD_MOUNT_LEN = 0.008
HOOD_JOINT_Z = HOOD_MOUNT_Z + HOOD_MOUNT_LEN * 0.5
FOCUS_OUTER_RADIUS = 0.0345
FOCUS_INNER_RADIUS = 0.0310
APERTURE_OUTER_RADIUS = 0.0312
APERTURE_INNER_RADIUS = 0.0284
HOOD_MOUNT_OUTER_RADIUS = 0.0324
def _annulus(
    outer_radius: float,
    inner_radius: float,
    length: float,
    *,
    z0: float = 0.0,
    centered: bool = False,
):
    outer = cq.Workplane("XY").circle(outer_radius).extrude(length)
    inner = cq.Workplane("XY").circle(inner_radius).extrude(length + 0.002).translate((0.0, 0.0, -0.001))
    shape = outer.cut(inner)
    if centered:
        return shape.translate((0.0, 0.0, -length * 0.5))
    return shape.translate((0.0, 0.0, z0))
def _radial_box(
    *,
    radius: float,
    radial_depth: float,
    tangential_width: float,
    length: float,
    z_center: float,
    angle_deg: float,
):
    box = cq.Workplane("XY").box(
        radial_depth,
        tangential_width,
        length,
        centered=(True, True, True),
    )
    box = box.translate((radius - radial_depth * 0.5 + 0.0001, 0.0, z_center))
    return box.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
def _build_rear_band_shape():
    rear_band = _annulus(0.0300, 0.0190, REAR_FIXED_BAND_LEN, z0=REAR_FIXED_BAND_Z)
    distance_window = _radial_box(
        radius=0.0300,
        radial_depth=0.0016,
        tangential_width=0.010,
        length=0.0045,
        z_center=0.0195,
        angle_deg=90.0,
    )
    rear_band = rear_band.cut(distance_window)

    index_boss = _radial_box(
        radius=0.0320,
        radial_depth=0.0022,
        tangential_width=0.0024,
        length=0.006,
        z_center=REAR_FIXED_BAND_Z + REAR_FIXED_BAND_LEN * 0.5,
        angle_deg=90.0,
    )
    return rear_band.union(index_boss)
def _build_front_barrel_shape():
    front_barrel = _annulus(0.0298, 0.0168, FRONT_BARREL_LEN, z0=FRONT_BARREL_Z)
    front_name_ring = _annulus(0.0310, 0.0276, 0.003, z0=0.069)
    return front_barrel.union(front_name_ring)
def _build_ribbed_ring_shape(
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    groove_count: int,
    groove_depth: float,
    groove_width: float,
):
    ring = _annulus(outer_radius, inner_radius, length, centered=True)
    for index in range(groove_count):
        angle_deg = 360.0 * index / groove_count
        ring = ring.cut(
            _radial_box(
                radius=outer_radius,
                radial_depth=groove_depth,
                tangential_width=groove_width,
                length=length + 0.002,
                z_center=0.0,
                angle_deg=angle_deg,
            )
        )
    return ring
def _build_focus_ring_shape():
    ring = _build_ribbed_ring_shape(
        outer_radius=FOCUS_OUTER_RADIUS,
        inner_radius=FOCUS_INNER_RADIUS,
        length=FOCUS_RING_LEN,
        groove_count=44,
        groove_depth=0.0022,
        groove_width=0.0013,
    )
    front_land = _annulus(FOCUS_OUTER_RADIUS, FOCUS_OUTER_RADIUS - 0.0012, 0.0024, z0=0.0158, centered=True)
    rear_land = _annulus(FOCUS_OUTER_RADIUS, FOCUS_OUTER_RADIUS - 0.0012, 0.0024, z0=-0.0158, centered=True)
    return ring.union(front_land).union(rear_land)
def _build_aperture_ring_shape():
    ring = _build_ribbed_ring_shape(
        outer_radius=APERTURE_OUTER_RADIUS,
        inner_radius=APERTURE_INNER_RADIUS,
        length=APERTURE_RING_LEN,
        groove_count=30,
        groove_depth=0.0012,
        groove_width=0.0010,
    )
    detent_land = _annulus(APERTURE_OUTER_RADIUS, APERTURE_OUTER_RADIUS - 0.0010, 0.0018, z0=0.0, centered=True)
    return ring.union(detent_land)
def _build_hood_shape():
    hood = _annulus(0.0400, HOOD_MOUNT_OUTER_RADIUS, 0.016, z0=-0.004)
    hood = hood.union(_annulus(0.0415, 0.0348, 0.016, z0=0.012))
    hood = hood.union(_annulus(0.0445, 0.0395, 0.018, z0=0.028))

    for angle_deg in (0.0, 120.0, 240.0):
        twist_tab = _radial_box(
            radius=0.0458,
            radial_depth=0.0060,
            tangential_width=0.0130,
            length=0.005,
            z_center=0.004,
            angle_deg=angle_deg,
        )
        hood = hood.union(twist_tab)

    return hood
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="manual_focus_prime_lens")

    anodized_black = model.material("anodized_black", rgba=(0.11, 0.11, 0.12, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.07, 0.07, 0.08, 1.0))
    satin_black = model.material("satin_black", rgba=(0.14, 0.14, 0.15, 1.0))
    mount_steel = model.material("mount_steel", rgba=(0.70, 0.71, 0.74, 1.0))

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_annulus(0.0310, 0.0210, REAR_FLANGE_LEN, z0=0.0), "mount_shell"),
        material=mount_steel,
        name="mount_shell",
    )
    barrel.visual(
        mesh_from_cadquery(_annulus(0.0284, 0.0196, APERTURE_SUPPORT_LEN, z0=APERTURE_SUPPORT_Z), "aperture_drum"),
        material=anodized_black,
        name="aperture_drum",
    )
    barrel.visual(
        mesh_from_cadquery(_build_rear_band_shape(), "rear_band"),
        material=anodized_black,
        name="rear_band",
    )
    barrel.visual(
        mesh_from_cadquery(_annulus(0.0310, 0.0183, FOCUS_SUPPORT_LEN, z0=FOCUS_SUPPORT_Z), "focus_drum"),
        material=anodized_black,
        name="focus_drum",
    )
    barrel.visual(
        mesh_from_cadquery(_build_front_barrel_shape(), "front_barrel"),
        material=anodized_black,
        name="front_barrel",
    )
    barrel.visual(
        mesh_from_cadquery(_annulus(HOOD_MOUNT_OUTER_RADIUS, 0.0182, HOOD_MOUNT_LEN, z0=HOOD_MOUNT_Z), "hood_mount"),
        material=anodized_black,
        name="hood_mount",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(_build_focus_ring_shape(), "focus_ring_mesh"),
        material=rubber_black,
        name="focus_sleeve",
    )

    aperture_ring = model.part("aperture_ring")
    aperture_ring.visual(
        mesh_from_cadquery(_build_aperture_ring_shape(), "aperture_ring_mesh"),
        material=satin_black,
        name="aperture_sleeve",
    )

    hood = model.part("hood")
    hood.visual(
        mesh_from_cadquery(_build_hood_shape(), "hood_mesh"),
        material=satin_black,
        name="hood_collar",
    )

    model.articulation(
        "aperture_rotation",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=aperture_ring,
        origin=Origin(xyz=(0.0, 0.0, APERTURE_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.25, velocity=7.0),
    )
    model.articulation(
        "focus_rotation",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.0, 0.0, FOCUS_CENTER_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.35, velocity=8.0),
    )
    model.articulation(
        "hood_twist",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=hood,
        origin=Origin(xyz=(0.0, 0.0, HOOD_JOINT_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.25,
            velocity=3.0,
            lower=0.0,
            upper=math.radians(24.0),
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
