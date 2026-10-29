# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, cctv_mast_with_pantilt_camera_head, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: cctv_mast_with_pantilt_camera_head

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="site_security_tripod_mast")

    powder_black = model.material("powder_black", rgba=(0.16, 0.16, 0.17, 1.0))
    charcoal = model.material("charcoal", rgba=(0.24, 0.25, 0.27, 1.0))
    anodized_aluminum = model.material(
        "anodized_aluminum", rgba=(0.56, 0.58, 0.60, 1.0)
    )
    rubber = model.material("rubber", rgba=(0.10, 0.10, 0.11, 1.0))
    camera_grey = model.material("camera_grey", rgba=(0.31, 0.33, 0.35, 1.0))
    glass = model.material("glass", rgba=(0.18, 0.24, 0.28, 0.45))

    leg_angles = {
        "front": 0.0,
        "left": 2.0 * math.pi / 3.0,
        "right": 4.0 * math.pi / 3.0,
    }
    hub = model.part("hub")
    hub.visual(
        Cylinder(radius=0.080, length=0.140),
        origin=Origin(xyz=(0.0, 0.0, 0.530)),
        material=powder_black,
        name="hub_lower_collar",
    )
    hub.visual(
        Cylinder(radius=0.060, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.585)),
        material=powder_black,
        name="hub_top_cap",
    )
    for clamp_angle in leg_angles.values():
        c = math.cos(clamp_angle)
        s = math.sin(clamp_angle)
        hub.visual(
            Box((0.018, 0.024, 0.180)),
            origin=Origin(
                xyz=(0.070 * c, 0.070 * s, 0.690),
                rpy=(0.0, 0.0, clamp_angle),
            ),
            material=charcoal,
            name=f"mast_clamp_{int(round(clamp_angle * 1000.0))}",
        )

    hinge_radius = 0.098
    bracket_offset = 0.026

    def add_leg_brackets(
        angle: float,
        *,
        left_name: str,
        right_name: str,
        left_rib_name: str,
        right_rib_name: str,
    ) -> None:
        c = math.cos(angle)
        s = math.sin(angle)
        rib_radius = 0.084
        rib_size_x = 0.016
        hub.visual(
            Box((0.020, 0.012, 0.042)),
            origin=Origin(
                xyz=(
                    hinge_radius * c - bracket_offset * s,
                    hinge_radius * s + bracket_offset * c,
                    0.530,
                ),
                rpy=(0.0, 0.0, angle),
            ),
            material=powder_black,
            name=left_name,
        )
        hub.visual(
            Box((0.020, 0.012, 0.042)),
            origin=Origin(
                xyz=(
                    hinge_radius * c + bracket_offset * s,
                    hinge_radius * s - bracket_offset * c,
                    0.530,
                ),
                rpy=(0.0, 0.0, angle),
            ),
            material=powder_black,
            name=right_name,
        )
        hub.visual(
            Box((rib_size_x, 0.008, 0.042)),
            origin=Origin(
                xyz=(
                    rib_radius * c - bracket_offset * s,
                    rib_radius * s + bracket_offset * c,
                    0.530,
                ),
                rpy=(0.0, 0.0, angle),
            ),
            material=powder_black,
            name=left_rib_name,
        )
        hub.visual(
            Box((rib_size_x, 0.008, 0.042)),
            origin=Origin(
                xyz=(
                    rib_radius * c + bracket_offset * s,
                    rib_radius * s - bracket_offset * c,
                    0.530,
                ),
                rpy=(0.0, 0.0, angle),
            ),
            material=powder_black,
            name=right_rib_name,
        )

    add_leg_brackets(
        leg_angles["front"],
        left_name="front_bracket_left",
        right_name="front_bracket_right",
        left_rib_name="front_bracket_left_rib",
        right_rib_name="front_bracket_right_rib",
    )
    add_leg_brackets(
        leg_angles["left"],
        left_name="left_bracket_left",
        right_name="left_bracket_right",
        left_rib_name="left_bracket_left_rib",
        right_rib_name="left_bracket_right_rib",
    )
    add_leg_brackets(
        leg_angles["right"],
        left_name="right_bracket_left",
        right_name="right_bracket_right",
        left_rib_name="right_bracket_left_rib",
        right_rib_name="right_bracket_right_rib",
    )

    hub.inertial = Inertial.from_geometry(
        Box((0.240, 0.240, 0.430)),
        mass=4.2,
        origin=Origin(xyz=(0.0, 0.0, 0.665)),
    )

    leg_length = 0.880
    leg_connector_length = 0.065
    leg_main_tube_length = leg_length - leg_connector_length
    leg_drop_angle = 0.620
    leg_tube_radius = 0.019
    leg_foot_radius = 0.022
    leg_beta = math.pi / 2.0 + leg_drop_angle
    leg_connector_midpoint = (
        0.5 * leg_connector_length * math.cos(leg_drop_angle),
        0.0,
        -0.5 * leg_connector_length * math.sin(leg_drop_angle),
    )
    leg_midpoint = (
        0.5 * (leg_connector_length + leg_length) * math.cos(leg_drop_angle),
        0.0,
        -0.5 * (leg_connector_length + leg_length) * math.sin(leg_drop_angle),
    )
    leg_tip = (
        leg_length * math.cos(leg_drop_angle),
        0.0,
        -leg_length * math.sin(leg_drop_angle),
    )

    for leg_name in leg_angles:
        leg = model.part(f"leg_{leg_name}")
        leg.visual(
            Cylinder(radius=0.015, length=0.040),
            origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
            material=charcoal,
            name="hinge_barrel",
        )
        leg.visual(
            Box((leg_connector_length, 0.014, 0.024)),
            origin=Origin(xyz=leg_connector_midpoint, rpy=(0.0, leg_drop_angle, 0.0)),
            material=charcoal,
            name="leg_root_arm",
        )
        leg.visual(
            Cylinder(radius=leg_tube_radius, length=leg_main_tube_length),
            origin=Origin(xyz=leg_midpoint, rpy=(0.0, leg_beta, 0.0)),
            material=anodized_aluminum,
            name="leg_tube",
        )
        leg.visual(
            Sphere(radius=leg_foot_radius),
            origin=Origin(xyz=leg_tip),
            material=rubber,
            name="foot_pad",
        )
        leg.inertial = Inertial.from_geometry(
            Box((0.760, 0.060, 0.560)),
            mass=1.0,
            origin=Origin(xyz=(0.360, 0.0, -0.210)),
        )

    mast = model.part("mast")
    mast.visual(
        Cylinder(radius=0.050, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, 0.011)),
        material=charcoal,
        name="mast_base_collar",
    )
    mast.visual(
        Cylinder(radius=0.028, length=0.980),
        origin=Origin(xyz=(0.0, 0.0, 0.512)),
        material=anodized_aluminum,
        name="mast_tube",
    )
    mast.visual(
        Cylinder(radius=0.034, length=0.045),
        origin=Origin(xyz=(0.0, 0.0, 0.970)),
        material=charcoal,
        name="mast_top_collar",
    )
    mast.visual(
        Cylinder(radius=0.046, length=0.048),
        origin=Origin(xyz=(0.0, 0.0, 1.016)),
        material=powder_black,
        name="mast_head_plate",
    )
    mast.inertial = Inertial.from_geometry(
        Box((0.110, 0.110, 1.060)),
        mass=2.6,
        origin=Origin(xyz=(0.0, 0.0, 0.520)),
    )

    pan_head = model.part("pan_head")
    pan_head.visual(
        Cylinder(radius=0.060, length=0.028),
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        material=powder_black,
        name="pan_turntable",
    )
    pan_head.visual(
        Box((0.055, 0.100, 0.070)),
        origin=Origin(xyz=(0.0, 0.0, 0.055)),
        material=charcoal,
        name="pan_pedestal",
    )
    pan_head.visual(
        Box((0.030, 0.012, 0.120)),
        origin=Origin(xyz=(0.0, 0.049, 0.100)),
        material=powder_black,
        name="yoke_left",
    )
    pan_head.visual(
        Box((0.030, 0.012, 0.120)),
        origin=Origin(xyz=(0.0, -0.049, 0.100)),
        material=powder_black,
        name="yoke_right",
    )
    pan_head.inertial = Inertial.from_geometry(
        Box((0.140, 0.120, 0.180)),
        mass=0.9,
        origin=Origin(xyz=(0.0, 0.0, 0.090)),
    )

    camera = model.part("camera")
    camera.visual(
        Cylinder(radius=0.009, length=0.086),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=charcoal,
        name="trunnion_pin",
    )
    camera.visual(
        Box((0.050, 0.060, 0.024)),
        origin=Origin(xyz=(0.025, 0.0, 0.0)),
        material=charcoal,
        name="trunnion_mount",
    )
    camera.visual(
        Box((0.150, 0.080, 0.086)),
        origin=Origin(xyz=(0.115, 0.0, 0.0)),
        material=camera_grey,
        name="body_shell",
    )
    camera.visual(
        Box((0.030, 0.070, 0.070)),
        origin=Origin(xyz=(0.045, 0.0, 0.0)),
        material=charcoal,
        name="rear_housing",
    )
    camera.visual(
        Cylinder(radius=0.026, length=0.065),
        origin=Origin(xyz=(0.198, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=charcoal,
        name="lens_housing",
    )
    camera.visual(
        Cylinder(radius=0.018, length=0.012),
        origin=Origin(xyz=(0.228, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="lens_glass",
    )
    camera.visual(
        Box((0.060, 0.082, 0.012)),
        origin=Origin(xyz=(0.188, 0.0, 0.048)),
        material=charcoal,
        name="sunshield",
    )
    camera.inertial = Inertial.from_geometry(
        Box((0.210, 0.090, 0.110)),
        mass=1.4,
        origin=Origin(xyz=(0.120, 0.0, 0.0)),
    )

    for leg_name, angle in leg_angles.items():
        c = math.cos(angle)
        s = math.sin(angle)
        model.articulation(
            f"hub_to_leg_{leg_name}",
            ArticulationType.REVOLUTE,
            parent=hub,
            child=f"leg_{leg_name}",
            origin=Origin(xyz=(hinge_radius * c, hinge_radius * s, 0.530), rpy=(0.0, 0.0, angle)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=30.0,
                velocity=1.2,
                lower=0.0,
                upper=1.70,
            ),
        )

    model.articulation(
        "hub_to_mast",
        ArticulationType.PRISMATIC,
        parent=hub,
        child=mast,
        origin=Origin(xyz=(0.0, 0.0, 0.600)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=90.0,
            velocity=0.20,
            lower=0.0,
            upper=0.240,
        ),
    )
    model.articulation(
        "mast_to_pan_head",
        ArticulationType.CONTINUOUS,
        parent=mast,
        child=pan_head,
        origin=Origin(xyz=(0.0, 0.0, 1.040)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=2.2),
    )
    model.articulation(
        "pan_head_to_camera",
        ArticulationType.REVOLUTE,
        parent=pan_head,
        child=camera,
        origin=Origin(xyz=(0.0, 0.0, 0.110)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=10.0,
            velocity=1.4,
            lower=-0.70,
            upper=0.95,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
