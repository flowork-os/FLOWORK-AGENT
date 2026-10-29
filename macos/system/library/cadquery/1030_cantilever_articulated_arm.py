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

class _NoOp:
    """Universal no-op sentinel that is callable AND Path-like, so asset/IO
    expressions in model scripts (e.g. ASSETS.mesh_dir.mkdir(); dir / 'x.obj')
    are harmless in self-contained mode."""
    def __call__(self, *a, **k):
        return self

    def __getattr__(self, _n):
        return self

    def __truediv__(self, _o):
        return self

    def __rtruediv__(self, _o):
        return self

    def __fspath__(self):
        return "/tmp/_articraft_noop"

    def mkdir(self, *a, **k):
        return None

_NOOP = _NoOp()

class _NoopMeta(type):
    def __getattr__(cls, _name):
        def _noop(*a, **k):
            return cls()
        return _noop

class AssetContext(metaclass=_NoopMeta):
    def __init__(self, *a, **k):
        pass

    def __getattr__(self, _n):
        return _NOOP

# ===== model =====
import math
import cadquery as cq
ASSETS = AssetContext.from_script(__file__)
BASE_PLATE_X = 0.34
BASE_PLATE_Y = 0.26
BASE_PLATE_Z = 0.02
COLUMN_CENTER_X = -0.105
COLUMN_OUTER_X = 0.11
COLUMN_OUTER_Y = 0.10
COLUMN_HEIGHT = 0.34
COLUMN_WALL = 0.014
COLUMN_FRONT_X = COLUMN_CENTER_X + COLUMN_OUTER_X / 2.0
SHOULDER_X = 0.04
SHOULDER_Z = 0.338
SHOULDER_PLATE_GAP = 0.10
SHOULDER_PLATE_T = 0.012
SHOULDER_CARTRIDGE_T = 0.01
SHOULDER_CARTRIDGE_OUTER_R = 0.031
SHOULDER_HOLE_R = 0.0146
ELBOW_HOLE_R = 0.0146
UPPER_ARM_ELBOW_X = 0.44
TOOL_MOUNT_X = 0.355
def _box(center: tuple[float, float, float], size: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").transformed(offset=center).box(*size)
def _cyl_y(
    center: tuple[float, float, float],
    radius: float,
    length: float,
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XZ")
        .center(cx, cz)
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .translate((0.0, cy, 0.0))
    )
def _ring_y(
    center: tuple[float, float, float],
    outer_radius: float,
    inner_radius: float,
    length: float,
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XZ")
        .center(cx, cz)
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length / 2.0, both=True)
        .translate((0.0, cy, 0.0))
    )
def _cyl_x(
    center: tuple[float, float, float],
    radius: float,
    length: float,
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("YZ")
        .center(cy, cz)
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .translate((cx, 0.0, 0.0))
    )
def _cyl_z(
    center: tuple[float, float, float],
    radius: float,
    length: float,
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XY")
        .center(cx, cy)
        .circle(radius)
        .extrude(length / 2.0, both=True)
        .translate((0.0, 0.0, cz))
    )
def _slot_cut_xz(
    center: tuple[float, float, float],
    length_x: float,
    width_z: float,
    depth_y: float,
) -> cq.Workplane:
    cx, cy, cz = center
    return (
        cq.Workplane("XZ")
        .center(cx, cz)
        .slot2D(length_x, width_z)
        .extrude(depth_y / 2.0, both=True)
        .translate((0.0, cy, 0.0))
    )
def _bolt_heads_y(
    center_x: float,
    center_z: float,
    center_y: float,
    pitch_x: float,
    pitch_z: float,
    radius: float,
    thickness: float,
) -> cq.Workplane:
    bolts = cq.Workplane("XY")
    for x_sign in (-1.0, 1.0):
        for z_sign in (-1.0, 1.0):
            bolts = bolts.union(
                _cyl_y(
                    (
                        center_x + x_sign * pitch_x / 2.0,
                        center_y,
                        center_z + z_sign * pitch_z / 2.0,
                    ),
                    radius,
                    thickness,
                )
            )
    return bolts
def _make_base_structure_shape() -> cq.Workplane:
    base_plate = _box((0.0, 0.0, BASE_PLATE_Z / 2.0), (BASE_PLATE_X, BASE_PLATE_Y, BASE_PLATE_Z))
    pads = cq.Workplane("XY")
    for x in (-0.115, 0.115):
        for y in (-0.080, 0.080):
            pads = pads.union(_box((x, y, 0.030), (0.060, 0.050, 0.020)))
    base = base_plate.union(pads)
    for x in (-0.115, 0.115):
        for y in (-0.080, 0.080):
            base = base.cut(_cyl_z((x, y, 0.024), 0.010, 0.060))

    column_outer = _box(
        (COLUMN_CENTER_X, 0.0, BASE_PLATE_Z + COLUMN_HEIGHT / 2.0),
        (COLUMN_OUTER_X, COLUMN_OUTER_Y, COLUMN_HEIGHT),
    )
    column_inner = _box(
        (COLUMN_CENTER_X, 0.0, BASE_PLATE_Z + COLUMN_WALL + (COLUMN_HEIGHT - COLUMN_WALL) / 2.0),
        (
            COLUMN_OUTER_X - 2.0 * COLUMN_WALL,
            COLUMN_OUTER_Y - 2.0 * COLUMN_WALL,
            COLUMN_HEIGHT - COLUMN_WALL,
        ),
    )
    access_opening = _box((COLUMN_FRONT_X - 0.005, 0.0, 0.202), (0.020, 0.064, 0.182))
    column = column_outer.cut(column_inner).cut(access_opening)

    rear_gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (COLUMN_CENTER_X - 0.053, BASE_PLATE_Z),
                (COLUMN_CENTER_X + 0.008, BASE_PLATE_Z),
                (COLUMN_CENTER_X + 0.008, 0.190),
            ]
        )
        .close()
        .extrude(0.018, both=True)
    )
    gussets = rear_gusset.translate((0.0, 0.038, 0.0)).union(rear_gusset.translate((0.0, -0.038, 0.0)))

    shoulder_plate_profile = (
        cq.Workplane("XZ")
        .polyline(
            [
                (-0.034, 0.230),
                (-0.012, 0.286),
                (0.012, 0.344),
                (0.038, 0.372),
                (0.070, 0.372),
                (0.070, 0.320),
                (0.050, 0.252),
                (0.016, 0.228),
            ]
        )
        .close()
        .extrude(SHOULDER_PLATE_T, both=True)
    )
    shoulder_plate_profile = shoulder_plate_profile.cut(
        _cyl_y((SHOULDER_X, 0.0, SHOULDER_Z), SHOULDER_HOLE_R, SHOULDER_PLATE_T + 0.010)
    )
    shoulder_plate_profile = shoulder_plate_profile.cut(_slot_cut_xz((0.006, 0.0, 0.308), 0.034, 0.026, 0.040))
    shoulder_plate_profile = shoulder_plate_profile.cut(_slot_cut_xz((0.030, 0.0, 0.350), 0.030, 0.022, 0.040))
    shoulder_plate_center_y = SHOULDER_PLATE_GAP / 2.0 + SHOULDER_PLATE_T / 2.0
    shoulder_plates = shoulder_plate_profile.translate((0.0, shoulder_plate_center_y, 0.0)).union(
        shoulder_plate_profile.translate((0.0, -shoulder_plate_center_y, 0.0))
    )

    top_bridge = _box(
        (0.010, 0.0, 0.394),
        (0.088, SHOULDER_PLATE_GAP + 2.0 * SHOULDER_PLATE_T, 0.016),
    )
    lower_bridge = _box(
        (-0.010, 0.0, 0.246),
        (0.060, SHOULDER_PLATE_GAP + 2.0 * SHOULDER_PLATE_T, 0.018),
    )
    forward_web = (
        cq.Workplane("XZ")
        .polyline([(-0.020, 0.230), (0.018, 0.230), (0.010, 0.260)])
        .close()
        .extrude(0.018, both=True)
    )
    forward_webs = forward_web.translate((0.0, 0.030, 0.0)).union(forward_web.translate((0.0, -0.030, 0.0)))

    return base.union(column).union(gussets).union(shoulder_plates).union(top_bridge).union(lower_bridge).union(forward_webs)
def _make_base_hardware_shape() -> cq.Workplane:
    cartridge_center_y = SHOULDER_PLATE_GAP / 2.0 + SHOULDER_PLATE_T + SHOULDER_CARTRIDGE_T / 2.0
    hardware = _ring_y(
        (SHOULDER_X, cartridge_center_y, SHOULDER_Z),
        SHOULDER_CARTRIDGE_OUTER_R,
        SHOULDER_HOLE_R,
        SHOULDER_CARTRIDGE_T,
    ).union(
        _ring_y(
            (SHOULDER_X, -cartridge_center_y, SHOULDER_Z),
            SHOULDER_CARTRIDGE_OUTER_R,
            SHOULDER_HOLE_R,
            SHOULDER_CARTRIDGE_T,
        )
    )
    hardware = hardware.union(
        _bolt_heads_y(SHOULDER_X, SHOULDER_Z, cartridge_center_y, 0.036, 0.036, 0.0042, 0.004)
    ).union(
        _bolt_heads_y(SHOULDER_X, SHOULDER_Z, -cartridge_center_y, 0.036, 0.036, 0.0042, 0.004)
    )
    return hardware
def _make_base_access_cover_shape() -> cq.Workplane:
    cover = _box((COLUMN_FRONT_X + 0.0015, 0.0, 0.202), (0.004, 0.076, 0.190))
    for z in (0.130, 0.274):
        for y in (-0.030, 0.030):
            cover = cover.union(_cyl_x((COLUMN_FRONT_X + 0.004, y, z), 0.004, 0.004))
    return cover
def _make_upper_arm_structure_shape() -> cq.Workplane:
    shoulder_journal = _make_upper_arm_shoulder_journal_shape()
    root_block = _box((0.160, 0.0, -0.018), (0.072, 0.040, 0.046))
    root_block = root_block.cut(_box((0.160, 0.0, -0.018), (0.026, 0.018, 0.022)))

    beam_outer = _box((0.235, 0.0, -0.026), (0.250, 0.050, 0.048))
    beam_inner = _box((0.235, 0.0, -0.026), (0.206, 0.028, 0.026))
    beam = beam_outer.cut(beam_inner)
    beam = beam.cut(_box((0.238, 0.0, -0.004), (0.182, 0.018, 0.010)))
    beam = beam.cut(_box((0.170, 0.0, -0.044), (0.054, 0.024, 0.012)))

    root_web = (
        cq.Workplane("XZ")
        .polyline([(0.132, -0.034), (0.182, -0.034), (0.174, -0.010), (0.138, -0.010)])
        .close()
        .extrude(0.006, both=True)
        .translate((0.0, 0.020, 0.0))
    )
    root_webs = root_web.union(root_web.mirror("XZ"))

    side_rib = _box((0.240, 0.027, -0.024), (0.192, 0.004, 0.056))
    side_rib = side_rib.cut(_slot_cut_xz((0.184, 0.027, -0.024), 0.066, 0.012, 0.008))
    side_rib = side_rib.cut(_slot_cut_xz((0.286, 0.027, -0.024), 0.054, 0.010, 0.008))
    side_ribs = side_rib.union(side_rib.mirror("XZ"))

    clevis_ear = _box((0.430, 0.047, -0.004), (0.062, 0.010, 0.088))
    clevis_ear = clevis_ear.cut(_cyl_y((UPPER_ARM_ELBOW_X, 0.047, 0.0), ELBOW_HOLE_R, 0.024))
    clevis_bridge = _box((0.404, 0.0, -0.024), (0.026, 0.040, 0.034))
    clevis = clevis_ear.union(clevis_ear.mirror("XZ")).union(clevis_bridge)

    return shoulder_journal.union(root_block).union(root_webs).union(beam).union(side_ribs).union(clevis)
def _make_upper_arm_shoulder_journal_shape() -> cq.Workplane:
    journal = _cyl_y((0.0, 0.0, 0.0), 0.0140, 0.146)
    lock_nuts = _cyl_y((0.0, 0.076, 0.0), 0.018, 0.006).union(_cyl_y((0.0, -0.076, 0.0), 0.018, 0.006))
    transition = _box((0.082, 0.0, -0.014), (0.164, 0.022, 0.026))
    nose = _box((0.152, 0.0, -0.016), (0.024, 0.026, 0.026))
    return journal.union(lock_nuts).union(transition).union(nose)
def _make_upper_arm_hardware_shape() -> cq.Workplane:
    elbow_cartridge_center_y = 0.053
    elbow_hardware = _ring_y(
        (UPPER_ARM_ELBOW_X, elbow_cartridge_center_y, 0.0),
        0.0225,
        ELBOW_HOLE_R,
        0.008,
    ).union(
        _ring_y(
            (UPPER_ARM_ELBOW_X, -elbow_cartridge_center_y, 0.0),
            0.0225,
            ELBOW_HOLE_R,
            0.008,
        )
    )
    elbow_hardware = elbow_hardware.union(
        _bolt_heads_y(UPPER_ARM_ELBOW_X, 0.0, elbow_cartridge_center_y, 0.028, 0.028, 0.0035, 0.004)
    ).union(
        _bolt_heads_y(UPPER_ARM_ELBOW_X, 0.0, -elbow_cartridge_center_y, 0.028, 0.028, 0.0035, 0.004)
    )

    return elbow_hardware
def _make_forearm_structure_shape() -> cq.Workplane:
    elbow_journal = _cyl_y((0.0, 0.0, 0.0), 0.0140, 0.114)
    elbow_collars = _cyl_y((0.0, 0.061, 0.0), 0.017, 0.006).union(
        _cyl_y((0.0, -0.061, 0.0), 0.017, 0.006)
    )
    elbow_transition = _box((0.070, 0.0, -0.014), (0.140, 0.020, 0.024))
    elbow_nose = _box((0.118, 0.0, -0.016), (0.020, 0.024, 0.024))

    root_block = _box((0.118, 0.0, -0.018), (0.070, 0.032, 0.040))
    root_block = root_block.cut(_box((0.118, 0.0, -0.018), (0.024, 0.014, 0.018)))

    beam_outer = _box((0.190, 0.0, -0.024), (0.188, 0.040, 0.042))
    beam_inner = _box((0.190, 0.0, -0.024), (0.148, 0.022, 0.022))
    beam = beam_outer.cut(beam_inner)
    beam = beam.cut(_box((0.194, 0.0, -0.004), (0.122, 0.016, 0.010)))

    side_rib = _box((0.196, 0.022, -0.022), (0.140, 0.004, 0.050))
    side_rib = side_rib.cut(_slot_cut_xz((0.162, 0.022, -0.022), 0.050, 0.010, 0.008))
    side_rib = side_rib.cut(_slot_cut_xz((0.224, 0.022, -0.022), 0.040, 0.010, 0.008))
    side_ribs = side_rib.union(side_rib.mirror("XZ"))

    root_web = (
        cq.Workplane("XZ")
        .polyline([(0.100, -0.028), (0.140, -0.028), (0.134, -0.008), (0.106, -0.008)])
        .close()
        .extrude(0.006, both=True)
        .translate((0.0, 0.014, 0.0))
    )
    root_webs = root_web.union(root_web.mirror("XZ"))

    mount_block = _box((0.338, 0.0, -0.004), (0.034, 0.044, 0.060))
    mount_block = mount_block.cut(_box((0.334, 0.0, -0.004), (0.012, 0.018, 0.028)))

    tip_register = _cyl_x((TOOL_MOUNT_X - 0.012, 0.0, -0.004), 0.018, 0.010)

    return (
        elbow_journal.union(elbow_collars)
        .union(elbow_transition)
        .union(elbow_nose)
        .union(root_block)
        .union(root_webs)
        .union(beam)
        .union(side_ribs)
        .union(mount_block)
        .union(tip_register)
    )
def _make_tool_flange_shape() -> cq.Workplane:
    tool = _box((0.007, 0.0, -0.004), (0.014, 0.064, 0.072))
    tool = tool.union(_cyl_x((0.020, 0.0, -0.004), 0.022, 0.018))
    tool = tool.union(_cyl_x((0.040, 0.0, -0.004), 0.043, 0.014))
    tool = tool.union(_cyl_x((0.051, 0.0, -0.004), 0.018, 0.010))
    tool = tool.cut(_cyl_x((0.040, 0.0, -0.004), 0.008, 0.042))

    bolt_points = [
        (0.028 * math.cos(angle), 0.028 * math.sin(angle))
        for angle in [index * math.tau / 6.0 for index in range(6)]
    ]
    flange_bolt_holes = (
        cq.Workplane("YZ")
        .transformed(offset=(0.040, 0.0, -0.004))
        .pushPoints(bolt_points)
        .circle(0.0038)
        .extrude(0.028, both=True)
    )
    dowel_holes = (
        cq.Workplane("YZ")
        .transformed(offset=(0.040, 0.0, -0.004))
        .pushPoints([(0.0, 0.018), (0.0, -0.018)])
        .circle(0.0026)
        .extrude(0.028, both=True)
    )
    return tool.cut(flange_bolt_holes).cut(dowel_holes)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cantilever_articulated_arm", assets=ASSETS)

    steel_dark = model.material("steel_dark", rgba=(0.27, 0.29, 0.31, 1.0))
    steel_mid = model.material("steel_mid", rgba=(0.41, 0.44, 0.47, 1.0))
    oxide = model.material("oxide_black", rgba=(0.14, 0.15, 0.16, 1.0))
    machined = model.material("machined_steel", rgba=(0.63, 0.66, 0.69, 1.0))

    base = model.part("base_frame")
    base.visual(
        mesh_from_cadquery(_make_base_structure_shape(), "base_structure.obj", assets=ASSETS),
        material=steel_dark,
        name="base_structure",
    )
    base.visual(
        mesh_from_cadquery(_make_base_hardware_shape(), "base_hardware.obj", assets=ASSETS),
        material=machined,
        name="shoulder_cartridges",
    )
    base.visual(
        mesh_from_cadquery(_make_base_access_cover_shape(), "base_cover.obj", assets=ASSETS),
        material=oxide,
        name="access_cover",
    )
    base.inertial = Inertial.from_geometry(
        Box((0.34, 0.26, 0.40)),
        mass=46.0,
        origin=Origin(xyz=(0.0, 0.0, 0.20)),
    )

    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        mesh_from_cadquery(_make_upper_arm_structure_shape(), "upper_arm_structure.obj", assets=ASSETS),
        material=steel_mid,
        name="arm_structure",
    )
    upper_arm.visual(
        mesh_from_cadquery(_make_upper_arm_hardware_shape(), "upper_arm_hardware.obj", assets=ASSETS),
        material=machined,
        name="elbow_hardware",
    )
    upper_arm.inertial = Inertial.from_geometry(
        Box((0.48, 0.09, 0.13)),
        mass=15.5,
        origin=Origin(xyz=(0.19, 0.0, -0.03)),
    )

    forearm = model.part("forearm")
    forearm.visual(
        mesh_from_cadquery(_make_forearm_structure_shape(), "forearm_structure.obj", assets=ASSETS),
        material=oxide,
        name="arm_structure",
    )
    forearm.inertial = Inertial.from_geometry(
        Box((0.36, 0.08, 0.11)),
        mass=10.5,
        origin=Origin(xyz=(0.17, 0.0, -0.025)),
    )

    tool = model.part("tool_flange")
    tool.visual(
        mesh_from_cadquery(_make_tool_flange_shape(), "tool_flange.obj", assets=ASSETS),
        material=machined,
        name="flange_body",
    )
    tool.inertial = Inertial.from_geometry(
        Cylinder(radius=0.045, length=0.06),
        mass=2.4,
        origin=Origin(xyz=(0.03, 0.0, -0.004), rpy=(0.0, math.pi / 2.0, 0.0)),
    )

    model.articulation(
        "shoulder_pitch",
        ArticulationType.REVOLUTE,
        parent=base,
        child=upper_arm,
        origin=Origin(xyz=(SHOULDER_X, 0.0, SHOULDER_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=220.0, velocity=1.3, lower=-0.30, upper=1.10),
    )
    model.articulation(
        "elbow_pitch",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=forearm,
        origin=Origin(xyz=(UPPER_ARM_ELBOW_X, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=160.0, velocity=1.7, lower=-0.10, upper=1.90),
    )
    model.articulation(
        "forearm_to_tool",
        ArticulationType.FIXED,
        parent=forearm,
        child=tool,
        origin=Origin(xyz=(TOOL_MOUNT_X, 0.0, 0.0)),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
