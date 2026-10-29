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

# ===== model =====
import cadquery as cq
BACKPLATE_W = 0.160
BACKPLATE_H = 0.320
BACKPLATE_T = 0.010
MOUNT_SLOT_LEN = 0.040
MOUNT_SLOT_DIA = 0.010
MOUNT_SLOT_Z = 0.110
SPINE_W = 0.040
SPINE_D = 0.024
SPINE_H = 0.250
SPINE_Y = 0.022
POD_SUPPORT_W = 0.054
POD_SUPPORT_D = 0.018
POD_SUPPORT_H = 0.034
POD_SUPPORT_Y = 0.036
PIVOT_Y = 0.045
POD_Z_OFFSET = 0.085
HINGE_TAB_LEN = 0.028
HINGE_TAB_D = 0.008
HINGE_TAB_T = 0.024
ROOT_BLOCK_LEN = 0.042
ROOT_BLOCK_D = 0.018
ROOT_BLOCK_T = 0.018
ROOT_BLOCK_X = 0.034
ROOT_BLOCK_Y = 0.016
ARM_BEAM_LEN = 0.090
ARM_BEAM_D = 0.014
ARM_BEAM_T = 0.010
ARM_BEAM_X = 0.090
ARM_BEAM_Y = 0.027
TIP_NECK_LEN = 0.018
TIP_NECK_D = 0.018
TIP_NECK_T = 0.010
TIP_NECK_X = 0.137
TIP_NECK_Y = 0.036
END_PLATE_T = 0.008
END_PLATE_W = 0.040
END_PLATE_H = 0.078
END_PLATE_X = 0.146
END_PLATE_Y = 0.042
END_PLATE_HOLE_R = 0.005
END_PLATE_HOLE_Z = 0.021
TONGUE_LEN = 0.030
TONGUE_D = 0.014
TONGUE_T = 0.004
TONGUE_X = 0.018
TONGUE_Y = 0.006
def _pod_mount_shape(z_center: float) -> cq.Workplane:
    pod_block = cq.Workplane("XY").box(POD_SUPPORT_W, POD_SUPPORT_D, POD_SUPPORT_H).translate(
        (0.0, POD_SUPPORT_Y, z_center)
    )
    face_pad = cq.Workplane("XY").box(0.034, 0.004, 0.028).translate((0.0, PIVOT_Y - 0.002, z_center))
    return pod_block.union(face_pad)
def _backplate_shape() -> cq.Workplane:
    backplate = (
        cq.Workplane("XY")
        .box(BACKPLATE_W, BACKPLATE_T, BACKPLATE_H)
        .translate((0.0, BACKPLATE_T / 2.0, 0.0))
        .edges("|Y")
        .fillet(0.012)
    )
    slot_cutters = (
        cq.Workplane("XZ")
        .pushPoints([(0.0, MOUNT_SLOT_Z), (0.0, -MOUNT_SLOT_Z)])
        .slot2D(MOUNT_SLOT_LEN, MOUNT_SLOT_DIA, 90)
        .extrude(BACKPLATE_T + 0.004, both=True)
        .translate((0.0, BACKPLATE_T / 2.0, 0.0))
    )
    backplate = backplate.cut(slot_cutters)

    spine = cq.Workplane("XY").box(SPINE_W, SPINE_D, SPINE_H).translate((0.0, SPINE_Y, 0.0))
    web_right = cq.Workplane("XY").box(0.012, 0.016, 0.220).translate((0.019, 0.015, 0.0))
    web_left = cq.Workplane("XY").box(0.012, 0.016, 0.220).translate((-0.019, 0.015, 0.0))

    upper_pod = _pod_mount_shape(POD_Z_OFFSET)
    lower_pod = _pod_mount_shape(-POD_Z_OFFSET)

    return backplate.union(spine).union(web_right).union(web_left).union(upper_pod).union(lower_pod)
def _branch_shape(hand: float) -> cq.Workplane:
    hinge_tab = cq.Workplane("XY").box(HINGE_TAB_LEN, HINGE_TAB_D, HINGE_TAB_T).translate(
        (hand * (HINGE_TAB_LEN / 2.0), HINGE_TAB_D / 2.0, 0.0)
    )
    tongue = cq.Workplane("XY").box(TONGUE_LEN, TONGUE_D, TONGUE_T).translate(
        (hand * TONGUE_X, TONGUE_Y, 0.0)
    )
    root_block = cq.Workplane("XY").box(ROOT_BLOCK_LEN, ROOT_BLOCK_D, ROOT_BLOCK_T).translate(
        (hand * ROOT_BLOCK_X, ROOT_BLOCK_Y, 0.0)
    )
    beam = cq.Workplane("XY").box(ARM_BEAM_LEN, ARM_BEAM_D, ARM_BEAM_T).translate(
        (hand * ARM_BEAM_X, ARM_BEAM_Y, 0.0)
    )
    tip_neck = cq.Workplane("XY").box(TIP_NECK_LEN, TIP_NECK_D, TIP_NECK_T).translate(
        (hand * TIP_NECK_X, TIP_NECK_Y, 0.0)
    )
    end_plate = cq.Workplane("XY").box(END_PLATE_T, END_PLATE_W, END_PLATE_H).translate(
        (hand * END_PLATE_X, END_PLATE_Y, 0.0)
    )

    plate_holes = (
        cq.Workplane("YZ")
        .pushPoints([(0.0, END_PLATE_HOLE_Z), (0.0, -END_PLATE_HOLE_Z)])
        .circle(END_PLATE_HOLE_R)
        .extrude(END_PLATE_T + 0.006, both=True)
        .translate((hand * END_PLATE_X, END_PLATE_Y, 0.0))
    )

    return (
        hinge_tab.union(tongue)
        .union(root_block)
        .union(beam)
        .union(tip_neck)
        .union(end_plate)
        .cut(plate_holes)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="service_panel_two_branch_bracket")

    model.material("powder_coat_dark", rgba=(0.24, 0.26, 0.29, 1.0))
    model.material("cast_aluminum", rgba=(0.71, 0.73, 0.76, 1.0))

    backplate = model.part("backplate")
    backplate.visual(
        mesh_from_cadquery(_backplate_shape(), "backplate"),
        material="powder_coat_dark",
        name="backplate_shell",
    )
    backplate.inertial = Inertial.from_geometry(
        Box((BACKPLATE_W, 0.084, BACKPLATE_H)),
        mass=3.4,
        origin=Origin(xyz=(0.0, 0.042, 0.0)),
    )

    upper_branch = model.part("upper_branch")
    upper_branch.visual(
        mesh_from_cadquery(_branch_shape(1.0), "upper_branch"),
        material="cast_aluminum",
        name="upper_branch_shell",
    )
    upper_branch.inertial = Inertial.from_geometry(
        Box((0.160, 0.052, END_PLATE_H)),
        mass=0.95,
        origin=Origin(xyz=(0.078, 0.008, 0.0)),
    )

    lower_branch = model.part("lower_branch")
    lower_branch.visual(
        mesh_from_cadquery(_branch_shape(-1.0), "lower_branch"),
        material="cast_aluminum",
        name="lower_branch_shell",
    )
    lower_branch.inertial = Inertial.from_geometry(
        Box((0.160, 0.052, END_PLATE_H)),
        mass=0.95,
        origin=Origin(xyz=(-0.078, 0.008, 0.0)),
    )

    model.articulation(
        "upper_branch_hinge",
        ArticulationType.REVOLUTE,
        parent=backplate,
        child=upper_branch,
        origin=Origin(xyz=(0.0, PIVOT_Y, POD_Z_OFFSET)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.25, effort=18.0, velocity=1.5),
    )
    model.articulation(
        "lower_branch_hinge",
        ArticulationType.REVOLUTE,
        parent=backplate,
        child=lower_branch,
        origin=Origin(xyz=(0.0, PIVOT_Y, -POD_Z_OFFSET)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.25, effort=18.0, velocity=1.5),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
