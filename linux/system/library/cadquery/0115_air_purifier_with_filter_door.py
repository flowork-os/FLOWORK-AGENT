# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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
BODY_W = 0.24
BODY_D = 0.18
BODY_H = 0.42
WALL = 0.0045
DOOR_W = 0.212
DOOR_H = 0.332
DOOR_T = 0.010
DOOR_Z = -0.005
FILTER_W = 0.188
FILTER_H = 0.156
FILTER_D = 0.104
FILTER_Z = -0.082
FILTER_TRAVEL = 0.076
HANDLE_RECESS_W = 0.190
HANDLE_RECESS_D = 0.062
HANDLE_RECESS_H = 0.034
HANDLE_BAR_W = 0.148
HANDLE_BAR_D = 0.032
HANDLE_BAR_T = 0.012
HANDLE_DROP = 0.016
HANDLE_PIVOT_SPAN = 0.174
HANDLE_PIVOT_LEN = 0.016
HANDLE_PIVOT_R = 0.005
def _build_shell_shape() -> cq.Workplane:
    def panel(size_x: float, size_y: float, size_z: float, xyz: tuple[float, float, float]) -> cq.Workplane:
        return cq.Workplane("XY").box(size_x, size_y, size_z).translate(xyz)

    front_y = BODY_D / 2.0 - WALL / 2.0
    back_y = -BODY_D / 2.0 + WALL / 2.0
    side_x = BODY_W / 2.0 - WALL / 2.0
    bottom_t = 0.012
    top_t = 0.008
    bottom_z = -BODY_H / 2.0 + bottom_t / 2.0
    top_z = BODY_H / 2.0 - top_t / 2.0

    open_w = DOOR_W - 0.016
    open_h = DOOR_H - 0.016
    side_frame_w = (BODY_W - open_w) / 2.0
    top_frame_h = BODY_H / 2.0 - (DOOR_Z + open_h / 2.0)
    bottom_frame_h = (DOOR_Z - open_h / 2.0) + BODY_H / 2.0

    shell = panel(BODY_W, WALL, BODY_H, (0.0, back_y, 0.0))
    shell = shell.union(panel(WALL, BODY_D, BODY_H, (-side_x, 0.0, 0.0)))
    shell = shell.union(panel(WALL, BODY_D, BODY_H, (side_x, 0.0, 0.0)))
    shell = shell.union(panel(BODY_W, BODY_D, bottom_t, (0.0, 0.0, bottom_z)))

    top_panel = panel(BODY_W, BODY_D, top_t, (0.0, 0.0, top_z))
    handle_pocket = panel(HANDLE_RECESS_W, HANDLE_RECESS_D, HANDLE_RECESS_H, (0.0, 0.0, BODY_H / 2.0 - HANDLE_RECESS_H / 2.0 + 0.002))
    shell = shell.union(top_panel.cut(handle_pocket))

    shell = shell.union(panel(side_frame_w, WALL, open_h, (-(open_w / 2.0 + side_frame_w / 2.0), front_y, DOOR_Z)))
    shell = shell.union(panel(side_frame_w, WALL, open_h, (open_w / 2.0 + side_frame_w / 2.0, front_y, DOOR_Z)))
    shell = shell.union(panel(BODY_W, WALL, top_frame_h, (0.0, front_y, (BODY_H / 2.0 + DOOR_Z + open_h / 2.0) / 2.0)))
    shell = shell.union(panel(BODY_W, WALL, bottom_frame_h, (0.0, front_y, (-BODY_H / 2.0 + DOOR_Z - open_h / 2.0) / 2.0)))

    guide_rail = panel(0.024, 0.096, 0.010, (0.0, 0.0, 0.0))
    rail_y = 0.018
    rail_z = FILTER_Z - FILTER_H / 2.0 + 0.006
    shell = shell.union(guide_rail.translate((0.106, rail_y, rail_z)))
    shell = shell.union(guide_rail.translate((-0.106, rail_y, rail_z)))

    return shell.combine()
def _build_door_shape() -> cq.Workplane:
    panel = cq.Workplane("XY").box(DOOR_W, DOOR_T, DOOR_H, centered=(False, True, True))

    inset = cq.Workplane("XY").box(DOOR_W - 0.030, 0.0035, DOOR_H - 0.060, centered=(False, True, True))
    inset = inset.translate((0.015, DOOR_T / 2.0 - 0.00175, 0.0))
    door = panel.cut(inset)

    finger_pull = cq.Workplane("XY").box(0.016, DOOR_T * 0.75, 0.074)
    finger_pull = finger_pull.translate((DOOR_W - 0.009, DOOR_T * 0.12, 0.0))
    door = door.cut(finger_pull)

    hinge_barrel = cq.Workplane("XY").circle(0.0045).extrude(0.060)
    upper_barrel = hinge_barrel.translate((0.0, DOOR_T / 2.0 + 0.003, 0.094))
    lower_barrel = hinge_barrel.translate((0.0, DOOR_T / 2.0 + 0.003, -0.154))
    return door.union(upper_barrel).union(lower_barrel).combine()
def _build_filter_shape() -> cq.Workplane:
    front_frame = cq.Workplane("XY").box(FILTER_W, 0.012, FILTER_H)
    media = cq.Workplane("XY").box(FILTER_W - 0.018, FILTER_D, FILTER_H - 0.020)
    media = media.translate((0.0, -FILTER_D / 2.0 - 0.004, 0.0))

    pull_tab = cq.Workplane("XY").box(0.060, 0.012, 0.024)
    pull_tab = pull_tab.translate((0.0, 0.011, 0.0))

    return front_frame.union(media).union(pull_tab).combine()
def _build_handle_shape() -> cq.Workplane:
    grip = cq.Workplane("XY").box(HANDLE_BAR_W, HANDLE_BAR_D, HANDLE_BAR_T)
    grip = grip.translate((0.0, 0.0, -HANDLE_DROP))

    end_lobe = cq.Workplane("XY").box(0.032, HANDLE_BAR_D + 0.006, 0.020)
    left_lobe = end_lobe.translate((-0.068, 0.0, -HANDLE_DROP / 2.0))
    right_lobe = end_lobe.translate((0.068, 0.0, -HANDLE_DROP / 2.0))

    pivot = cq.Workplane("YZ").circle(HANDLE_PIVOT_R).extrude(HANDLE_PIVOT_LEN)
    left_pivot = pivot.translate((-HANDLE_PIVOT_SPAN / 2.0 - HANDLE_PIVOT_LEN / 2.0, 0.0, 0.0))
    right_pivot = pivot.translate((HANDLE_PIVOT_SPAN / 2.0 - HANDLE_PIVOT_LEN / 2.0, 0.0, 0.0))

    return grip.union(left_lobe).union(right_lobe).union(left_pivot).union(right_pivot).combine()
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_purifier")

    shell_white = model.material("shell_white", rgba=(0.92, 0.93, 0.94, 1.0))
    shell_dark = model.material("shell_dark", rgba=(0.20, 0.22, 0.24, 1.0))
    filter_gray = model.material("filter_gray", rgba=(0.76, 0.79, 0.76, 1.0))

    shell = model.part("shell")
    shell.visual(
        mesh_from_cadquery(_build_shell_shape(), "shell"),
        material=shell_white,
        name="housing",
    )

    door = model.part("door")
    door.visual(
        mesh_from_cadquery(_build_door_shape(), "door"),
        material=shell_white,
        name="panel",
    )

    filter_cartridge = model.part("filter_cartridge")
    filter_cartridge.visual(
        mesh_from_cadquery(_build_filter_shape(), "filter_cartridge"),
        material=filter_gray,
        name="cartridge",
    )

    handle = model.part("handle")
    handle.visual(
        mesh_from_cadquery(_build_handle_shape(), "handle"),
        material=shell_dark,
        name="grip",
    )

    model.articulation(
        "door_hinge",
        ArticulationType.REVOLUTE,
        parent=shell,
        child=door,
        origin=Origin(xyz=(-DOOR_W / 2.0, BODY_D / 2.0 + DOOR_T / 2.0, DOOR_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(lower=0.0, upper=1.55, effort=8.0, velocity=1.6),
    )

    model.articulation(
        "filter_slide",
        ArticulationType.PRISMATIC,
        parent=shell,
        child=filter_cartridge,
        origin=Origin(xyz=(0.0, BODY_D / 2.0 - WALL - 0.020, FILTER_Z)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=FILTER_TRAVEL, effort=25.0, velocity=0.20),
    )

    model.articulation(
        "handle_pivot",
        ArticulationType.REVOLUTE,
        parent=shell,
        child=handle,
        origin=Origin(xyz=(0.0, 0.0, BODY_H / 2.0 - WALL - 0.003)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(lower=0.0, upper=2.85, effort=6.0, velocity=2.2),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
