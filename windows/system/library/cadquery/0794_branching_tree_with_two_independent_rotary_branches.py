# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, branching_tree_with_two_independent_rotary_branches, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: branching_tree_with_two_independent_rotary_branches

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
BASE_Z = 0.011
NODE_Z = 0.61
LEFT_AXIS = (-0.176, 0.0, 0.56)
RIGHT_AXIS = (0.186, 0.0, 0.69)
SHAFT_R = 0.0155
SUPPORT_BLOCK_Y = 0.045
SUPPORT_BLOCK_LEN_Y = 0.028
SPLIT_OFFSET_Z = 0.006
def _mesh(shape: cq.Workplane, filename: str):
    return mesh_from_cadquery(shape, filename, assets=ASSETS, tolerance=0.0008, angular_tolerance=0.08)
def _cyl_z(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(length / 2.0, both=True).translate(center)
def _cyl_y(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XZ").circle(radius).extrude(length / 2.0, both=True).translate(center)
def _cyl_x(radius: float, length: float, center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("YZ").circle(radius).extrude(length / 2.0, both=True).translate(center)
def _make_backbone() -> cq.Workplane:
    rail_a = cq.Workplane("XY").box(0.44, 0.055, 0.022).translate((0.0, 0.085, BASE_Z))
    rail_b = cq.Workplane("XY").box(0.44, 0.055, 0.022).translate((0.0, -0.085, BASE_Z))
    cross_member = cq.Workplane("XY").box(0.18, 0.16, 0.022).translate((0.0, 0.0, BASE_Z))
    center_pad = cq.Workplane("XY").box(0.14, 0.12, 0.016).translate((0.0, 0.0, 0.028))

    column_outer = cq.Workplane("XY").box(0.09, 0.11, 0.46).translate((0.0, 0.0, 0.25))
    column_inner = cq.Workplane("XY").box(0.054, 0.074, 0.34).translate((0.0, 0.0, 0.29))
    column = (
        column_outer
        .cut(column_inner)
        .cut(cq.Workplane("XY").box(0.052, 0.14, 0.10).translate((0.0, 0.0, 0.19)))
        .cut(cq.Workplane("XY").box(0.052, 0.14, 0.12).translate((0.0, 0.0, 0.35)))
    )

    node_outer = cq.Workplane("XY").box(0.24, 0.17, 0.28).translate((0.0, 0.0, NODE_Z))
    node_inner = cq.Workplane("XY").box(0.16, 0.11, 0.18).translate((0.0, 0.0, NODE_Z))
    node = (
        node_outer
        .cut(node_inner)
        .cut(cq.Workplane("XY").box(0.12, 0.055, 0.14).translate((0.0, 0.058, NODE_Z)))
        .cut(cq.Workplane("XY").box(0.12, 0.055, 0.14).translate((0.0, -0.058, NODE_Z)))
    )

    gusset = (
        cq.Workplane("XZ")
        .polyline([(0.018, 0.39), (0.018, 0.49), (0.082, 0.54), (0.082, 0.43)])
        .close()
        .extrude(0.012, both=True)
    )
    gusset_mirror = gusset.mirror("YZ")

    rear_spine = cq.Workplane("XY").box(0.028, 0.03, 0.23).translate((0.0, -0.058, 0.47))
    crown = cq.Workplane("XY").box(0.10, 0.10, 0.016).translate((0.0, 0.0, 0.758))

    frame = rail_a.union(rail_b).union(cross_member).union(center_pad).union(column).union(node).union(gusset).union(gusset_mirror).union(rear_spine).union(crown)

    for x in (-0.16, 0.16):
        for y in (-0.085, 0.085):
            frame = frame.cut(_cyl_z(0.007, 0.05, (x, y, BASE_Z)))

    return frame
def _make_support(sign: float, axis_center: tuple[float, float, float]) -> cq.Workplane:
    sx, _, sz = axis_center
    split_z = sz + SPLIT_OFFSET_Z
    flange_x = sign * 0.127

    flange = cq.Workplane("XY").box(0.014, 0.14, 0.18).translate((flange_x, 0.0, sz))
    front_arm = cq.Workplane("XY").box(0.050, 0.018, 0.036).translate((sign * 0.150, SUPPORT_BLOCK_Y, sz - 0.030))
    rear_arm = cq.Workplane("XY").box(0.050, 0.018, 0.036).translate((sign * 0.150, -SUPPORT_BLOCK_Y, sz - 0.030))
    front_block = cq.Workplane("XY").box(0.078, SUPPORT_BLOCK_LEN_Y, 0.052).translate((sx, SUPPORT_BLOCK_Y, split_z - 0.026))
    rear_block = cq.Workplane("XY").box(0.078, SUPPORT_BLOCK_LEN_Y, 0.052).translate((sx, -SUPPORT_BLOCK_Y, split_z - 0.026))
    lower_tie = cq.Workplane("XY").box(0.050, 0.040, 0.018).translate((sign * 0.170, 0.0, sz - 0.055))

    rib_front = cq.Workplane("XY").box(0.060, 0.010, 0.074).rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -sign * 24.0).translate((sign * 0.152, SUPPORT_BLOCK_Y, sz - 0.024))
    rib_rear = cq.Workplane("XY").box(0.060, 0.010, 0.074).rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), -sign * 24.0).translate((sign * 0.152, -SUPPORT_BLOCK_Y, sz - 0.024))
    stop_block = cq.Workplane("XY").box(0.024, 0.032, 0.018).translate((sx + sign * 0.018, 0.0, sz - 0.055))

    support = flange.union(front_arm).union(rear_arm).union(front_block).union(rear_block).union(lower_tie).union(rib_front).union(rib_rear).union(stop_block)
    support = support.cut(_cyl_y(SHAFT_R, 0.042, (sx, SUPPORT_BLOCK_Y, sz))).cut(_cyl_y(SHAFT_R, 0.042, (sx, -SUPPORT_BLOCK_Y, sz)))

    for y in (-0.044, -0.018, 0.018, 0.044):
        for dz in (-0.048, 0.048):
            support = support.cut(_cyl_x(0.0035, 0.022, (flange_x, y, sz + dz)))

    return support
def _make_cap(axis_center: tuple[float, float, float]) -> cq.Workplane:
    sx, _, sz = axis_center
    split_z = sz + SPLIT_OFFSET_Z

    front_cap = cq.Workplane("XY").box(0.078, SUPPORT_BLOCK_LEN_Y, 0.034).translate((sx, SUPPORT_BLOCK_Y, split_z + 0.017))
    rear_cap = cq.Workplane("XY").box(0.078, SUPPORT_BLOCK_LEN_Y, 0.034).translate((sx, -SUPPORT_BLOCK_Y, split_z + 0.017))
    bridge = cq.Workplane("XY").box(0.050, 0.030, 0.010).translate((sx, 0.0, split_z + 0.046))
    cap = front_cap.union(rear_cap).union(bridge)

    cap = cap.cut(_cyl_y(SHAFT_R, 0.042, (sx, SUPPORT_BLOCK_Y, sz))).cut(_cyl_y(SHAFT_R, 0.042, (sx, -SUPPORT_BLOCK_Y, sz)))

    for y in (-SUPPORT_BLOCK_Y, SUPPORT_BLOCK_Y):
        for dx in (-0.024, 0.024):
            cap = cap.cut(_cyl_z(0.0035, 0.045, (sx + dx, y, split_z + 0.017)))
            cap = cap.union(_cyl_z(0.006, 0.006, (sx + dx, y, split_z + 0.037)))

    return cap
def _make_branch_arm(length: float, angle_deg: float, sign: float) -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    shaft = _cyl_y(SHAFT_R, 0.170, (0.0, 0.0, 0.0))
    hub = _cyl_y(0.036, 0.050, (0.0, 0.0, 0.0))
    collar_front = _cyl_y(0.022, 0.010, (0.0, 0.074, 0.0))
    collar_rear = _cyl_y(0.022, 0.010, (0.0, -0.074, 0.0))
    stop_tab = cq.Workplane("XY").box(0.026, 0.014, 0.012).translate((0.040, 0.0, -0.045))
    shaft_hub = shaft.union(hub).union(collar_front).union(collar_rear).union(stop_tab)

    beam_outer = cq.Workplane("XY").box(length, 0.050, 0.060).translate((length / 2.0, 0.0, 0.0))
    beam_inner = cq.Workplane("XY").box(length - 0.050, 0.028, 0.036).translate((length / 2.0 + 0.012, 0.0, 0.0))
    beam = beam_outer.cut(beam_inner)
    root_block = cq.Workplane("XY").box(0.072, 0.054, 0.046).translate((0.042, 0.0, 0.0))
    brace = (
        cq.Workplane("XZ")
        .polyline([(0.018, -0.018), (0.098, -0.018), (0.176, 0.048), (0.088, 0.018)])
        .close()
        .extrude(0.010, both=True)
    )
    arm_body = beam.union(root_block).union(brace).rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), angle_deg)

    pad_plate = cq.Workplane("XY").box(0.018, 0.076, 0.068).translate((length + 0.009, 0.0, 0.0))
    pad_spine = cq.Workplane("XY").box(0.030, 0.044, 0.032).translate((length - 0.010, 0.0, 0.0))
    gusset = (
        cq.Workplane("XZ")
        .polyline([(length - 0.070, -0.014), (length - 0.010, -0.014), (length + 0.006, 0.040), (length - 0.084, 0.010)])
        .close()
        .extrude(0.010, both=True)
    )
    mount_pad = pad_plate.union(pad_spine).union(gusset)
    for y in (-0.022, 0.022):
        for z in (-0.018, 0.018):
            mount_pad = mount_pad.cut(_cyl_x(0.004, 0.045, (length + 0.002, y, z)))
    mount_pad = mount_pad.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), angle_deg)

    if sign < 0.0:
        shaft_hub = shaft_hub.mirror("YZ")
        arm_body = arm_body.mirror("YZ")
        mount_pad = mount_pad.mirror("YZ")

    return shaft_hub, arm_body, mount_pad
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="branching_tree_study", assets=ASSETS)

    steel_dark = model.material("steel_dark", rgba=(0.26, 0.29, 0.32, 1.0))
    steel_mid = model.material("steel_mid", rgba=(0.47, 0.50, 0.54, 1.0))
    steel_light = model.material("steel_light", rgba=(0.72, 0.74, 0.77, 1.0))
    bearing_black = model.material("bearing_black", rgba=(0.12, 0.12, 0.13, 1.0))

    backbone = model.part("backbone_frame")
    backbone.visual(_mesh(_make_backbone(), "backbone_frame.obj"), material=steel_dark, name="frame_shell")
    backbone.inertial = Inertial.from_geometry(Box((0.44, 0.17, 0.78)), mass=18.0, origin=Origin(xyz=(0.0, 0.0, 0.39)))

    left_support = model.part("left_support")
    left_support.visual(_mesh(_make_support(-1.0, LEFT_AXIS), "left_support.obj"), material=steel_mid, name="support_body")
    left_support.inertial = Inertial.from_geometry(Box((0.11, 0.14, 0.19)), mass=2.8, origin=Origin(xyz=(-0.15, 0.0, LEFT_AXIS[2] - 0.01)))

    right_support = model.part("right_support")
    right_support.visual(_mesh(_make_support(1.0, RIGHT_AXIS), "right_support.obj"), material=steel_mid, name="support_body")
    right_support.inertial = Inertial.from_geometry(Box((0.11, 0.14, 0.19)), mass=2.9, origin=Origin(xyz=(0.16, 0.0, RIGHT_AXIS[2] - 0.01)))

    left_cap = model.part("left_cap")
    left_cap.visual(_mesh(_make_cap(LEFT_AXIS), "left_cap.obj"), material=steel_light, name="cap_body")
    left_cap.inertial = Inertial.from_geometry(Box((0.08, 0.12, 0.06)), mass=0.7, origin=Origin(xyz=LEFT_AXIS))

    right_cap = model.part("right_cap")
    right_cap.visual(_mesh(_make_cap(RIGHT_AXIS), "right_cap.obj"), material=steel_light, name="cap_body")
    right_cap.inertial = Inertial.from_geometry(Box((0.08, 0.12, 0.06)), mass=0.7, origin=Origin(xyz=RIGHT_AXIS))

    left_shaft_hub, left_arm_body, left_mount_pad = _make_branch_arm(length=0.225, angle_deg=31.0, sign=-1.0)
    left_branch = model.part("left_branch")
    left_branch.visual(_mesh(left_shaft_hub, "left_branch_shaft_hub.obj"), material=bearing_black, name="shaft_hub")
    left_branch.visual(_mesh(left_arm_body, "left_branch_body.obj"), material=steel_mid, name="arm_body")
    left_branch.visual(_mesh(left_mount_pad, "left_branch_mount_pad.obj"), material=steel_light, name="mount_pad")
    left_branch.inertial = Inertial.from_geometry(Box((0.28, 0.16, 0.20)), mass=2.4, origin=Origin(xyz=(-0.13, 0.0, 0.08)))

    right_shaft_hub, right_arm_body, right_mount_pad = _make_branch_arm(length=0.275, angle_deg=39.0, sign=1.0)
    right_branch = model.part("right_branch")
    right_branch.visual(_mesh(right_shaft_hub, "right_branch_shaft_hub.obj"), material=bearing_black, name="shaft_hub")
    right_branch.visual(_mesh(right_arm_body, "right_branch_body.obj"), material=steel_mid, name="arm_body")
    right_branch.visual(_mesh(right_mount_pad, "right_branch_mount_pad.obj"), material=steel_light, name="mount_pad")
    right_branch.inertial = Inertial.from_geometry(Box((0.33, 0.16, 0.23)), mass=2.8, origin=Origin(xyz=(0.16, 0.0, 0.11)))

    model.articulation("backbone_to_left_support", ArticulationType.FIXED, parent=backbone, child=left_support, origin=Origin())
    model.articulation("backbone_to_right_support", ArticulationType.FIXED, parent=backbone, child=right_support, origin=Origin())
    model.articulation("left_support_to_left_cap", ArticulationType.FIXED, parent=left_support, child=left_cap, origin=Origin())
    model.articulation("right_support_to_right_cap", ArticulationType.FIXED, parent=right_support, child=right_cap, origin=Origin())
    model.articulation(
        "left_support_to_left_branch",
        ArticulationType.REVOLUTE,
        parent=left_support,
        child=left_branch,
        origin=Origin(xyz=LEFT_AXIS),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=32.0, velocity=1.6, lower=-0.60, upper=0.95),
    )
    model.articulation(
        "right_support_to_right_branch",
        ArticulationType.REVOLUTE,
        parent=right_support,
        child=right_branch,
        origin=Origin(xyz=RIGHT_AXIS),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=36.0, velocity=1.5, lower=-0.85, upper=0.70),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
