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
BASE_LENGTH = 0.34
BASE_WIDTH = 0.24
BASE_HEIGHT = 0.03
POST_RADIUS = 0.035
POST_HEIGHT = 0.86
SUPPORT_PAD_RADIUS = 0.04
SUPPORT_PAD_THICKNESS = 0.02
SUPPORT_PAD_CENTER_X = 0.165
SHOULDER_JOINT_X = SUPPORT_PAD_CENTER_X + SUPPORT_PAD_RADIUS
SUPPORT_PAD_TOP_Z = 0.76
LINK_PAD_THICKNESS = 0.02
JOINT_STANDOFF_HEIGHT = 0.04
JOINT_STANDOFF_RADIUS = 0.022
SHOULDER_END_RADIUS = 0.05
FORELINK_ROOT_RADIUS = 0.046
FORELINK_END_RADIUS = 0.048
WRIST_ROOT_RADIUS = 0.043
SHOULDER_LENGTH = 0.38
FORELINK_LENGTH = 0.32
def _rounded_prism(length: float, width: float, height: float, fillet: float) -> cq.Workplane:
    prism = cq.Workplane("XY").rect(length, width).extrude(height)
    if fillet > 0.0:
        prism = prism.edges("|Z").fillet(fillet)
    return prism
def _make_support_shape() -> cq.Workplane:
    base = _rounded_prism(BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT, 0.012)

    post = (
        cq.Workplane("XY")
        .circle(POST_RADIUS)
        .extrude(POST_HEIGHT)
        .translate((0.0, 0.0, BASE_HEIGHT))
    )

    shoulder_arm = _rounded_prism(0.16, 0.06, 0.028, 0.008).translate((0.09, 0.0, 0.69))

    shoulder_riser = _rounded_prism(0.056, 0.062, 0.05, 0.006).translate((0.137, 0.0, 0.715))

    gusset = (
        cq.Workplane("XZ")
        .polyline(
            [
                (POST_RADIUS * 0.8, 0.585),
                (0.102, 0.585),
                (0.152, 0.725),
                (POST_RADIUS * 0.8, 0.725),
            ]
        )
        .close()
        .extrude(0.052)
        .translate((0.0, -0.026, 0.0))
    )

    support_pad = (
        cq.Workplane("XY")
        .circle(SUPPORT_PAD_RADIUS)
        .extrude(SUPPORT_PAD_THICKNESS)
        .translate(
            (
                SUPPORT_PAD_CENTER_X,
                0.0,
                SUPPORT_PAD_TOP_Z - SUPPORT_PAD_THICKNESS,
            )
        )
    )

    shoulder_mount = _rounded_prism(0.02, 0.078, 0.02, 0.004).translate(
        (SHOULDER_JOINT_X - 0.01, 0.0, SUPPORT_PAD_TOP_Z - 0.01)
    )

    cap = (
        cq.Workplane("XY")
        .circle(POST_RADIUS * 1.08)
        .extrude(0.012)
        .translate((0.0, 0.0, BASE_HEIGHT + POST_HEIGHT - 0.012))
    )

    return (
        base.union(post)
        .union(shoulder_arm)
        .union(shoulder_riser)
        .union(gusset)
        .union(support_pad)
        .union(shoulder_mount)
        .union(cap)
    )
def _make_shoulder_shape() -> cq.Workplane:
    root_plate = _rounded_prism(0.08, 0.078, LINK_PAD_THICKNESS, 0.006).translate((0.04, 0.0, 0.0))

    root_housing = (
        cq.Workplane("XY")
        .circle(0.03)
        .extrude(0.028)
        .translate((0.03, 0.0, 0.0))
    )

    beam = _rounded_prism(0.27, 0.07, 0.04, 0.007).translate((0.195, 0.0, 0.008))

    spine = _rounded_prism(0.22, 0.046, 0.014, 0.004).translate((0.205, 0.0, 0.028))

    end_disk = (
        cq.Workplane("XY")
        .circle(SHOULDER_END_RADIUS)
        .extrude(LINK_PAD_THICKNESS)
        .translate((SHOULDER_LENGTH, 0.0, 0.0))
    )

    end_web = _rounded_prism(0.05, 0.056, 0.024, 0.004).translate((0.355, 0.0, 0.012))

    end_boss = (
        cq.Workplane("XY")
        .circle(JOINT_STANDOFF_RADIUS)
        .extrude(JOINT_STANDOFF_HEIGHT)
        .translate((SHOULDER_LENGTH, 0.0, LINK_PAD_THICKNESS))
    )

    return root_plate.union(root_housing).union(beam).union(spine).union(end_disk).union(end_web).union(end_boss)
def _make_link_shape(
    *,
    length: float,
    beam_width: float,
    beam_height: float,
    root_radius: float,
    end_radius: float,
    root_hole_radius: float = 0.0,
) -> cq.Workplane:
    root_disk = cq.Workplane("XY").circle(root_radius).extrude(LINK_PAD_THICKNESS)
    if root_hole_radius > 0.0:
        root_disk = root_disk.cut(
            cq.Workplane("XY").circle(root_hole_radius).extrude(LINK_PAD_THICKNESS)
        )
    end_disk = (
        cq.Workplane("XY")
        .circle(end_radius)
        .extrude(LINK_PAD_THICKNESS)
        .translate((length, 0.0, 0.0))
    )

    beam_length = length - 0.45 * (root_radius + end_radius)
    beam = (
        _rounded_prism(beam_length, beam_width, beam_height, 0.007)
        .translate((length * 0.5, 0.0, 0.008))
    )

    top_cap = (
        _rounded_prism(beam_length * 0.88, beam_width * 0.72, 0.012, 0.004)
        .translate((length * 0.5, 0.0, LINK_PAD_THICKNESS + 0.016))
    )

    end_boss = (
        cq.Workplane("XY")
        .circle(JOINT_STANDOFF_RADIUS)
        .extrude(JOINT_STANDOFF_HEIGHT)
        .translate((length, 0.0, LINK_PAD_THICKNESS))
    )

    return root_disk.union(end_disk).union(beam).union(top_cap).union(end_boss)
def _make_wrist_face_shape() -> cq.Workplane:
    pad = cq.Workplane("XY").circle(WRIST_ROOT_RADIUS).extrude(LINK_PAD_THICKNESS)

    neck = (
        _rounded_prism(0.08, 0.05, 0.034, 0.005)
        .translate((0.048, 0.0, 0.01))
    )

    rib = (
        cq.Workplane("XZ")
        .polyline([(0.018, 0.0), (0.065, 0.0), (0.082, 0.042), (0.03, 0.042)])
        .close()
        .extrude(0.028)
        .translate((0.0, -0.014, LINK_PAD_THICKNESS))
    )

    plate = (
        cq.Workplane("YZ")
        .rect(0.14, 0.18)
        .extrude(0.016)
        .edges("|X")
        .fillet(0.01)
        .faces(">X")
        .workplane(centerOption="CenterOfMass")
        .pushPoints([(-0.04, -0.05), (0.04, -0.05), (-0.04, 0.05), (0.04, 0.05)])
        .hole(0.012)
        .translate((0.078, 0.0, 0.028))
    )

    return pad.union(neck).union(rib).union(plate)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="side_post_cantilever_arm")

    model.material("support_dark", rgba=(0.19, 0.2, 0.23, 1.0))
    model.material("arm_silver", rgba=(0.73, 0.75, 0.77, 1.0))
    model.material("wrist_gray", rgba=(0.57, 0.59, 0.62, 1.0))

    support = model.part("support")
    support.visual(
        mesh_from_cadquery(_make_support_shape(), "support_body"),
        material="support_dark",
        name="support_body",
    )

    shoulder = model.part("shoulder_link")
    shoulder.visual(
        mesh_from_cadquery(_make_shoulder_shape(), "shoulder_link_body"),
        material="arm_silver",
        name="shoulder_body",
    )

    forelink = model.part("forelink")
    forelink.visual(
        mesh_from_cadquery(
            _make_link_shape(
                length=FORELINK_LENGTH,
                beam_width=0.066,
                beam_height=0.038,
                root_radius=FORELINK_ROOT_RADIUS,
                end_radius=FORELINK_END_RADIUS,
            ),
            "forelink_body",
        ),
        material="arm_silver",
        name="forelink_body",
    )

    wrist_face = model.part("wrist_face")
    wrist_face.visual(
        mesh_from_cadquery(_make_wrist_face_shape(), "wrist_face_body"),
        material="wrist_gray",
        name="wrist_body",
    )

    model.articulation(
        "support_to_shoulder",
        ArticulationType.REVOLUTE,
        parent=support,
        child=shoulder,
        origin=Origin(xyz=(SHOULDER_JOINT_X, 0.0, SUPPORT_PAD_TOP_Z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=30.0, velocity=1.5, lower=-1.0, upper=1.0),
    )

    model.articulation(
        "shoulder_to_forelink",
        ArticulationType.REVOLUTE,
        parent=shoulder,
        child=forelink,
        origin=Origin(xyz=(SHOULDER_LENGTH, 0.0, LINK_PAD_THICKNESS + JOINT_STANDOFF_HEIGHT)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=20.0, velocity=1.7, lower=-1.0, upper=1.0),
    )

    model.articulation(
        "forelink_to_wrist",
        ArticulationType.REVOLUTE,
        parent=forelink,
        child=wrist_face,
        origin=Origin(xyz=(FORELINK_LENGTH, 0.0, LINK_PAD_THICKNESS + JOINT_STANDOFF_HEIGHT)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=12.0, velocity=2.0, lower=-1.0, upper=1.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
