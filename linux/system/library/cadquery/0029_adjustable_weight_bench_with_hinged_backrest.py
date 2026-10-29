# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, adjustable_weight_bench_with_hinged_backrest, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: adjustable_weight_bench_with_hinged_backrest

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
import math
import cadquery as cq
def _pad_mesh(
    name: str,
    *,
    length: float,
    width: float,
    thickness: float,
    center_x: float,
    center_z: float,
    edge_radius: float,
):
    shape = (
        cq.Workplane("XY")
        .box(length, width, thickness)
        .edges()
        .fillet(edge_radius)
        .translate((center_x, 0.0, center_z))
    )
    return mesh_from_cadquery(shape, name)
def _add_roller_visuals(part, *, foam, steel) -> None:
    spin_origin = Origin(rpy=(math.pi / 2.0, 0.0, 0.0))
    part.visual(
        Cylinder(radius=0.055, length=0.320),
        origin=spin_origin,
        material=foam,
        name="foam",
    )
    part.visual(
        Cylinder(radius=0.041, length=0.010),
        origin=Origin(xyz=(0.0, 0.165, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="end_cap_0",
    )
    part.visual(
        Cylinder(radius=0.041, length=0.010),
        origin=Origin(xyz=(0.0, -0.165, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="end_cap_1",
    )
def _add_wheel_visuals(part, *, rubber, steel) -> None:
    spin_origin = Origin(rpy=(math.pi / 2.0, 0.0, 0.0))
    part.visual(
        Cylinder(radius=0.060, length=0.040),
        origin=spin_origin,
        material=rubber,
        name="tire",
    )
    part.visual(
        Cylinder(radius=0.038, length=0.024),
        origin=spin_origin,
        material=steel,
        name="hub",
    )
    part.visual(
        Cylinder(radius=0.047, length=0.006),
        origin=Origin(xyz=(0.0, 0.009, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="hub_cap_0",
    )
    part.visual(
        Cylinder(radius=0.047, length=0.006),
        origin=Origin(xyz=(0.0, -0.009, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=steel,
        name="hub_cap_1",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="decline_bench")

    powder_coat = model.material("powder_coat", rgba=(0.18, 0.19, 0.20, 1.0))
    upholstery = model.material("upholstery", rgba=(0.10, 0.10, 0.11, 1.0))
    backer = model.material("backer", rgba=(0.08, 0.08, 0.09, 1.0))
    steel = model.material("steel", rgba=(0.70, 0.72, 0.75, 1.0))
    rubber = model.material("rubber", rgba=(0.05, 0.05, 0.05, 1.0))
    foam = model.material("foam", rgba=(0.13, 0.13, 0.14, 1.0))

    frame = model.part("frame")
    frame.visual(
        Box((0.16, 0.52, 0.14)),
        origin=Origin(xyz=(-0.56, 0.0, 0.07)),
        material=powder_coat,
        name="rear_foot",
    )
    frame.visual(
        Box((0.10, 0.05, 0.12)),
        origin=Origin(xyz=(-0.50, 0.18, 0.12)),
        material=powder_coat,
        name="rear_riser_0",
    )
    frame.visual(
        Box((0.10, 0.05, 0.12)),
        origin=Origin(xyz=(-0.50, -0.18, 0.12)),
        material=powder_coat,
        name="rear_riser_1",
    )
    frame.visual(
        Box((1.02, 0.05, 0.05)),
        origin=Origin(xyz=(-0.05, 0.18, 0.16), rpy=(0.0, 0.12, 0.0)),
        material=powder_coat,
        name="rail_0",
    )
    frame.visual(
        Box((1.02, 0.05, 0.05)),
        origin=Origin(xyz=(-0.05, -0.18, 0.16), rpy=(0.0, 0.12, 0.0)),
        material=powder_coat,
        name="rail_1",
    )
    frame.visual(
        Box((0.22, 0.05, 0.05)),
        origin=Origin(xyz=(-0.43, 0.18, 0.155), rpy=(0.0, 0.12, 0.0)),
        material=powder_coat,
        name="rear_brace_0",
    )
    frame.visual(
        Box((0.22, 0.05, 0.05)),
        origin=Origin(xyz=(-0.43, -0.18, 0.155), rpy=(0.0, 0.12, 0.0)),
        material=powder_coat,
        name="rear_brace_1",
    )
    frame.visual(
        Box((0.12, 0.05, 0.10)),
        origin=Origin(xyz=(-0.40, 0.18, 0.17)),
        material=powder_coat,
        name="rear_gusset_0",
    )
    frame.visual(
        Box((0.12, 0.05, 0.10)),
        origin=Origin(xyz=(-0.40, -0.18, 0.17)),
        material=powder_coat,
        name="rear_gusset_1",
    )
    frame.visual(
        Box((0.16, 0.42, 0.06)),
        origin=Origin(xyz=(0.03, 0.0, 0.215)),
        material=powder_coat,
        name="back_bridge",
    )
    frame.visual(
        Box((0.08, 0.14, 0.12)),
        origin=Origin(xyz=(0.03, 0.0, 0.29)),
        material=powder_coat,
        name="back_support",
    )
    frame.visual(
        Box((0.14, 0.40, 0.06)),
        origin=Origin(xyz=(0.18, 0.0, 0.235)),
        material=powder_coat,
        name="seat_bridge",
    )
    frame.visual(
        Box((0.08, 0.14, 0.12)),
        origin=Origin(xyz=(0.18, 0.0, 0.32)),
        material=powder_coat,
        name="seat_support",
    )
    frame.visual(
        Box((0.18, 0.38, 0.06)),
        origin=Origin(xyz=(0.47, 0.0, 0.07)),
        material=powder_coat,
        name="front_base",
    )
    frame.visual(
        Box((0.08, 0.05, 0.44)),
        origin=Origin(xyz=(0.40, 0.18, 0.26)),
        material=powder_coat,
        name="upright_0",
    )
    frame.visual(
        Box((0.08, 0.05, 0.44)),
        origin=Origin(xyz=(0.40, -0.18, 0.26)),
        material=powder_coat,
        name="upright_1",
    )
    frame.visual(
        Box((0.10, 0.36, 0.06)),
        origin=Origin(xyz=(0.45, 0.0, 0.64)),
        material=powder_coat,
        name="roller_yoke",
    )
    frame.visual(
        Box((0.10, 0.02, 0.34)),
        origin=Origin(xyz=(0.49, 0.18, 0.49)),
        material=powder_coat,
        name="roller_cheek_0",
    )
    frame.visual(
        Box((0.10, 0.02, 0.34)),
        origin=Origin(xyz=(0.49, -0.18, 0.49)),
        material=powder_coat,
        name="roller_cheek_1",
    )
    frame.visual(
        Box((0.16, 0.03, 0.03)),
        origin=Origin(xyz=(0.60, 0.06, 0.115)),
        material=powder_coat,
        name="handle_stem_0",
    )
    frame.visual(
        Box((0.16, 0.03, 0.03)),
        origin=Origin(xyz=(0.60, -0.06, 0.115)),
        material=powder_coat,
        name="handle_stem_1",
    )
    frame.visual(
        Cylinder(radius=0.017, length=0.16),
        origin=Origin(xyz=(0.68, 0.0, 0.12), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=powder_coat,
        name="handle_grip",
    )
    frame.visual(
        Box((0.06, 0.03, 0.08)),
        origin=Origin(xyz=(0.50, 0.195, 0.09)),
        material=powder_coat,
        name="wheel_bracket_0",
    )
    frame.visual(
        Box((0.06, 0.03, 0.08)),
        origin=Origin(xyz=(0.50, -0.195, 0.09)),
        material=powder_coat,
        name="wheel_bracket_1",
    )

    back_pad = model.part("back_pad")
    back_pad.visual(
        _pad_mesh(
            "back_pad_shell",
            length=0.98,
            width=0.30,
            thickness=0.065,
            center_x=-0.39,
            center_z=0.046,
            edge_radius=0.012,
        ),
        material=upholstery,
        name="pad_shell",
    )
    back_pad.visual(
        Box((0.78, 0.24, 0.012)),
        origin=Origin(xyz=(-0.43, 0.0, 0.0075)),
        material=backer,
        name="backer_plate",
    )
    back_pad.visual(
        Box((0.08, 0.12, 0.018)),
        origin=Origin(xyz=(-0.08, 0.0, -0.006)),
        material=backer,
        name="mount_block",
    )

    seat = model.part("seat")
    seat.visual(
        _pad_mesh(
            "seat_pad_shell",
            length=0.34,
            width=0.30,
            thickness=0.065,
            center_x=0.14,
            center_z=0.046,
            edge_radius=0.012,
        ),
        material=upholstery,
        name="pad_shell",
    )
    seat.visual(
        Box((0.12, 0.24, 0.012)),
        origin=Origin(xyz=(0.20, 0.0, 0.0075)),
        material=backer,
        name="backer_plate",
    )
    seat.visual(
        Box((0.09, 0.12, 0.018)),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=backer,
        name="mount_block",
    )

    leg_roller_0 = model.part("leg_roller_0")
    _add_roller_visuals(leg_roller_0, foam=foam, steel=steel)

    leg_roller_1 = model.part("leg_roller_1")
    _add_roller_visuals(leg_roller_1, foam=foam, steel=steel)

    front_wheel_0 = model.part("front_wheel_0")
    _add_wheel_visuals(front_wheel_0, rubber=rubber, steel=steel)

    front_wheel_1 = model.part("front_wheel_1")
    _add_wheel_visuals(front_wheel_1, rubber=rubber, steel=steel)

    model.articulation(
        "frame_to_back_pad",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=back_pad,
        origin=Origin(xyz=(0.03, 0.0, 0.35), rpy=(0.0, -math.radians(10.0), 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=40.0,
            velocity=1.0,
            lower=-0.25,
            upper=0.85,
        ),
    )
    model.articulation(
        "frame_to_seat",
        ArticulationType.REVOLUTE,
        parent=frame,
        child=seat,
        origin=Origin(xyz=(0.18, 0.0, 0.375), rpy=(0.0, math.radians(9.0), 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=25.0,
            velocity=1.0,
            lower=-0.20,
            upper=0.45,
        ),
    )
    model.articulation(
        "frame_to_leg_roller_0",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=leg_roller_0,
        origin=Origin(xyz=(0.50, 0.0, 0.55)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=6.0, velocity=12.0),
    )
    model.articulation(
        "frame_to_leg_roller_1",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=leg_roller_1,
        origin=Origin(xyz=(0.58, 0.0, 0.34)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=6.0, velocity=12.0),
    )
    model.articulation(
        "frame_to_front_wheel_0",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=front_wheel_0,
        origin=Origin(xyz=(0.53, 0.23, 0.07)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0),
    )
    model.articulation(
        "frame_to_front_wheel_1",
        ArticulationType.CONTINUOUS,
        parent=frame,
        child=front_wheel_1,
        origin=Origin(xyz=(0.53, -0.23, 0.07)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=12.0, velocity=20.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
