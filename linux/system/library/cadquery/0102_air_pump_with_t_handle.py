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

# ===== model =====
import cadquery as cq
BASE_L = 0.30
BASE_W = 0.16
BASE_T = 0.022
BASE_NOTCH_W = 0.10
BASE_NOTCH_D = 0.044
BASE_SOCKET_R = 0.040
BASE_SOCKET_H = 0.012
BARREL_OUTER_R = 0.0225
BARREL_INNER_R = 0.0180
BARREL_COLLAR_R = 0.0285
BARREL_LOWER_H = 0.038
BARREL_TUBE_H = 0.490
BARREL_TOP_H = 0.020
BARREL_TOTAL_H = BARREL_LOWER_H + BARREL_TUBE_H + BARREL_TOP_H
BARREL_BORE_Z0 = 0.020
BARREL_BORE_H = 0.516
ROD_GUIDE_R = 0.0070
CLIP_PIVOT_X = 0.032
CLIP_PIVOT_Z = 0.125
CLIP_BOSS_R = 0.0065
CLIP_BOSS_T = 0.004
ROD_R = 0.0070
ROD_BELOW_JOINT = 0.360
ROD_ABOVE_JOINT = 0.120
ROD_TOTAL_L = ROD_BELOW_JOINT + ROD_ABOVE_JOINT
ROD_CENTER_Z = (ROD_ABOVE_JOINT - ROD_BELOW_JOINT) / 2.0
HANDLE_BAR_Z = 0.122
HANDLE_BAR_L = 0.250
HANDLE_BAR_R = 0.010
HANDLE_GRIP_R = 0.0135
HANDLE_GRIP_L = 0.055
HANDLE_TRAVEL = 0.240
CLIP_T = 0.012
def _centered_cylinder(radius: float, length: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length).translate((0.0, 0.0, -length / 2.0))
def _make_base_shape() -> cq.Workplane:
    base = cq.Workplane("XY").box(BASE_L, BASE_W, BASE_T, centered=(True, True, False))

    front_notch = (
        cq.Workplane("XY")
        .center(0.0, (BASE_W / 2.0) - (BASE_NOTCH_D / 2.0))
        .box(BASE_NOTCH_W, BASE_NOTCH_D, BASE_T + 0.004, centered=(True, True, False))
    )
    back_notch = (
        cq.Workplane("XY")
        .center(0.0, -(BASE_W / 2.0) + (BASE_NOTCH_D / 2.0))
        .box(BASE_NOTCH_W, BASE_NOTCH_D, BASE_T + 0.004, centered=(True, True, False))
    )
    socket = cq.Workplane("XY").circle(BASE_SOCKET_R).extrude(BASE_SOCKET_H).translate((0.0, 0.0, BASE_T))

    return base.cut(front_notch).cut(back_notch).union(socket)
def _make_barrel_shape() -> cq.Workplane:
    lower_collar = _centered_cylinder(BARREL_COLLAR_R, BARREL_LOWER_H).translate(
        (0.0, 0.0, BARREL_LOWER_H / 2.0)
    )
    main_tube = _centered_cylinder(BARREL_OUTER_R, BARREL_TUBE_H).translate(
        (0.0, 0.0, BARREL_LOWER_H + (BARREL_TUBE_H / 2.0))
    )
    top_cap = _centered_cylinder(BARREL_COLLAR_R, BARREL_TOP_H).translate(
        (0.0, 0.0, BARREL_LOWER_H + BARREL_TUBE_H + (BARREL_TOP_H / 2.0))
    )
    bore = _centered_cylinder(BARREL_INNER_R, BARREL_BORE_H).translate(
        (0.0, 0.0, BARREL_BORE_Z0 + (BARREL_BORE_H / 2.0))
    )
    guide_hole = _centered_cylinder(ROD_GUIDE_R, BARREL_TOP_H + 0.004).translate(
        (0.0, 0.0, BARREL_LOWER_H + BARREL_TUBE_H + (BARREL_TOP_H / 2.0))
    )

    boss = (
        _centered_cylinder(CLIP_BOSS_R, CLIP_BOSS_T)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((CLIP_PIVOT_X, 0.0, CLIP_PIVOT_Z))
    )
    strut_start_x = BARREL_OUTER_R - 0.005
    strut_len = CLIP_PIVOT_X - strut_start_x
    rear_strut = cq.Workplane("XY").box(strut_len, 0.010, 0.020).translate(
        ((strut_start_x + (strut_len / 2.0)), 0.0, CLIP_PIVOT_Z)
    )
    mount_pad = cq.Workplane("XY").box(0.003, 0.010, 0.016).translate((0.0375, 0.0, CLIP_PIVOT_Z))

    return (
        lower_collar.union(main_tube)
        .union(top_cap)
        .cut(bore)
        .cut(guide_hole)
        .union(rear_strut)
        .union(boss)
        .union(mount_pad)
    )
def _make_handle_rod_shape() -> cq.Workplane:
    rod = _centered_cylinder(ROD_R, ROD_TOTAL_L).translate((0.0, 0.0, ROD_CENTER_Z))
    hub = _centered_cylinder(0.013, 0.030).translate((0.0, 0.0, 0.108))
    top_stub = _centered_cylinder(0.009, 0.022).translate((0.0, 0.0, 0.126))
    return rod.union(hub).union(top_stub)
def _make_handle_grip_shape() -> cq.Workplane:
    crossbar = (
        _centered_cylinder(HANDLE_BAR_R, HANDLE_BAR_L)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((0.0, 0.0, HANDLE_BAR_Z))
    )
    left_grip = (
        _centered_cylinder(HANDLE_GRIP_R, HANDLE_GRIP_L)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate((-(HANDLE_BAR_L / 2.0) + (HANDLE_GRIP_L / 2.0), 0.0, HANDLE_BAR_Z))
    )
    right_grip = (
        _centered_cylinder(HANDLE_GRIP_R, HANDLE_GRIP_L)
        .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
        .translate(((HANDLE_BAR_L / 2.0) - (HANDLE_GRIP_L / 2.0), 0.0, HANDLE_BAR_Z))
    )
    return crossbar.union(left_grip).union(right_grip)
def _make_clip_shape() -> cq.Workplane:
    pivot_cheek = (
        _centered_cylinder(0.006, 0.006)
        .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0)
        .translate((0.013, 0.0, 0.0))
    )
    upper_bridge = cq.Workplane("XY").box(0.016, CLIP_T, 0.018).translate((0.018, 0.0, -0.010))
    arm = cq.Workplane("XY").box(0.015, CLIP_T, 0.058).translate((0.019, 0.0, -0.040))
    hook = cq.Workplane("XY").box(0.032, CLIP_T, 0.013).translate((0.030, 0.0, -0.0715))
    return_lip = cq.Workplane("XY").box(0.010, CLIP_T, 0.020).translate((0.041, 0.0, -0.061))
    opening = cq.Workplane("XY").box(0.019, CLIP_T + 0.004, 0.036).translate((0.025, 0.0, -0.049))
    return pivot_cheek.union(upper_bridge).union(arm).union(hook).union(return_lip).cut(opening)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="garage_floor_pump")

    model.material("base_steel", rgba=(0.19, 0.20, 0.22, 1.0))
    model.material("barrel_alloy", rgba=(0.72, 0.74, 0.77, 1.0))
    model.material("rod_steel", rgba=(0.80, 0.81, 0.82, 1.0))
    model.material("handle_black", rgba=(0.12, 0.12, 0.13, 1.0))
    model.material("clip_black", rgba=(0.16, 0.17, 0.18, 1.0))

    base = model.part("base")
    base.visual(mesh_from_cadquery(_make_base_shape(), "pump_base"), material="base_steel", name="base_shell")
    base.inertial = Inertial.from_geometry(
        Box((BASE_L, BASE_W, BASE_T + BASE_SOCKET_H)),
        mass=2.3,
        origin=Origin(xyz=(0.0, 0.0, (BASE_T + BASE_SOCKET_H) / 2.0)),
    )

    barrel = model.part("barrel")
    barrel.visual(mesh_from_cadquery(_make_barrel_shape(), "pump_barrel"), material="barrel_alloy", name="barrel_shell")
    barrel.inertial = Inertial.from_geometry(
        Cylinder(radius=BARREL_COLLAR_R, length=BARREL_TOTAL_H),
        mass=1.2,
        origin=Origin(xyz=(0.0, 0.0, BARREL_TOTAL_H / 2.0)),
    )

    handle = model.part("handle_assembly")
    handle.visual(
        mesh_from_cadquery(_make_handle_rod_shape(), "pump_handle_rod"),
        material="rod_steel",
        name="handle_rod",
    )
    handle.visual(
        mesh_from_cadquery(_make_handle_grip_shape(), "pump_handle_grip"),
        material="handle_black",
        name="handle_grip",
    )
    handle.inertial = Inertial.from_geometry(
        Box((HANDLE_BAR_L, 0.035, ROD_TOTAL_L + 0.020)),
        mass=0.55,
        origin=Origin(xyz=(0.0, 0.0, 0.020)),
    )

    clip = model.part("hose_clip")
    clip.visual(mesh_from_cadquery(_make_clip_shape(), "pump_hose_clip"), material="clip_black", name="clip_body")
    clip.inertial = Inertial.from_geometry(
        Box((0.040, CLIP_T, 0.085)),
        mass=0.08,
        origin=Origin(xyz=(0.022, 0.0, -0.038)),
    )

    model.articulation(
        "base_to_barrel",
        ArticulationType.FIXED,
        parent=base,
        child=barrel,
        origin=Origin(xyz=(0.0, 0.0, BASE_T + BASE_SOCKET_H)),
    )
    model.articulation(
        "barrel_to_handle",
        ArticulationType.PRISMATIC,
        parent=barrel,
        child=handle,
        origin=Origin(xyz=(0.0, 0.0, BARREL_TOTAL_H)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=HANDLE_TRAVEL, effort=120.0, velocity=0.80),
    )
    model.articulation(
        "barrel_to_hose_clip",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=clip,
        origin=Origin(xyz=(CLIP_PIVOT_X, 0.0, CLIP_PIVOT_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.35, effort=2.0, velocity=1.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
