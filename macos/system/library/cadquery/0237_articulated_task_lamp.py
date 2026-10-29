# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, articulated_task_lamp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: articulated_task_lamp

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
import cadquery as cq
def _cyl_x(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(0.0, math.pi / 2.0, 0.0))
def _cyl_y(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(-math.pi / 2.0, 0.0, 0.0))
def _cyl_z(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z))
def _annular_ring(outer_radius: float, inner_radius: float, thickness: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(thickness)
        .translate((0.0, 0.0, -thickness / 2.0))
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="ceiling_exam_lamp")

    painted = model.material("warm_white_painted_metal", rgba=(0.86, 0.84, 0.78, 1.0))
    satin = model.material("satin_stainless_steel", rgba=(0.62, 0.64, 0.64, 1.0))
    dark = model.material("black_rubber_cable", rgba=(0.02, 0.02, 0.018, 1.0))
    lens = model.material("warm_diffuser_lens", rgba=(1.0, 0.92, 0.48, 0.62))
    ceiling_mat = model.material("white_ceiling_panel", rgba=(0.95, 0.95, 0.92, 1.0))

    # Root: a ceiling escutcheon with a short fixed collar below it.
    ceiling_plate = model.part("ceiling_plate")
    ceiling_plate.visual(
        Box((0.46, 0.46, 0.012)),
        origin=Origin(xyz=(0.0, 0.0, 0.176)),
        material=ceiling_mat,
        name="ceiling_panel",
    )
    ceiling_plate.visual(
        Cylinder(radius=0.18, length=0.0375),
        origin=_cyl_z(0.0, 0.0, 0.15125),
        material=painted,
        name="round_plate",
    )
    ceiling_plate.visual(
        Cylinder(radius=0.105, length=0.085),
        origin=_cyl_z(0.0, 0.0, 0.09),
        material=painted,
        name="tapered_canopy",
    )
    ceiling_plate.visual(
        Cylinder(radius=0.066, length=0.0475),
        origin=_cyl_z(0.0, 0.0, 0.02375),
        material=satin,
        name="bottom_collar",
    )

    # Shoulder pan stage and the upper arm are one moving link.  The twin tubes
    # sit below the ceiling hub and terminate in a fork around the elbow joint.
    upper_arm = model.part("upper_arm")
    upper_arm.visual(
        Cylinder(radius=0.070, length=0.090),
        origin=_cyl_z(0.0, 0.0, -0.045),
        material=satin,
        name="shoulder_hub",
    )
    for idx, y in enumerate((-0.058, 0.058)):
        upper_arm.visual(
            Cylinder(radius=0.014, length=0.760),
            origin=_cyl_x(0.43, y, -0.060),
            material=painted,
            name=f"upper_tube_{idx}",
        )
    upper_arm.visual(
        Cylinder(radius=0.006, length=0.750),
        origin=_cyl_x(0.40, 0.0, -0.087),
        material=dark,
        name="upper_cable",
    )
    for name, y in (("elbow_fork_0", -0.0575), ("elbow_fork_1", 0.0575)):
        upper_arm.visual(
            Cylinder(radius=0.065, length=0.040),
            origin=_cyl_y(0.85, y, -0.060),
            material=satin,
            name=name,
        )

    forearm = model.part("forearm")
    forearm.visual(
        Cylinder(radius=0.052, length=0.075),
        origin=_cyl_y(0.0, 0.0, 0.0),
        material=satin,
        name="elbow_knuckle",
    )
    for idx, y in enumerate((-0.022, 0.022)):
        forearm.visual(
            Cylinder(radius=0.014, length=0.590),
            origin=_cyl_x(0.335, y, -0.025),
            material=painted,
            name=f"forearm_tube_{idx}",
        )
    forearm.visual(
        Cylinder(radius=0.006, length=0.520),
        origin=_cyl_x(0.33, 0.0, -0.058),
        material=dark,
        name="forearm_cable",
    )
    for name, x in (("forearm_clip_0", 0.18), ("forearm_clip_1", 0.50)):
        forearm.visual(
            Box((0.018, 0.060, 0.040)),
            origin=Origin(xyz=(x, 0.0, -0.043)),
            material=dark,
            name=name,
        )
    forearm.visual(
        Cylinder(radius=0.055, length=0.050),
        origin=_cyl_z(0.65, 0.0, -0.025),
        material=satin,
        name="pan_socket",
    )

    # The pan link is a U-yoke: a vertical spindle, crossbar, two side cheeks,
    # and round bosses where the lamp tilts.
    yoke = model.part("yoke")
    yoke.visual(
        Cylinder(radius=0.035, length=0.080),
        origin=_cyl_z(0.0, 0.0, -0.040),
        material=satin,
        name="pan_stem",
    )
    yoke.visual(
        Box((0.090, 0.450, 0.035)),
        origin=Origin(xyz=(0.0, 0.0, -0.090)),
        material=satin,
        name="yoke_crossbar",
    )
    for cheek_name, boss_name, y in (
        ("yoke_cheek_0", "tilt_boss_0", -0.205),
        ("yoke_cheek_1", "tilt_boss_1", 0.205),
    ):
        yoke.visual(
            Box((0.040, 0.035, 0.195)),
            origin=Origin(xyz=(0.0, y, -0.175)),
            material=satin,
            name=cheek_name,
        )
        yoke.visual(
            Cylinder(radius=0.045, length=0.035),
            origin=_cyl_y(0.0, y, -0.270),
            material=satin,
            name=boss_name,
        )

    lamp_head = model.part("lamp_head")
    lamp_head.visual(
        Cylinder(radius=0.025, length=0.375),
        origin=_cyl_y(0.0, 0.0, 0.0),
        material=satin,
        name="trunnion",
    )
    lamp_head.visual(
        Box((0.110, 0.300, 0.070)),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=painted,
        name="rear_saddle",
    )
    lamp_head.visual(
        Cylinder(radius=0.175, length=0.085),
        origin=_cyl_z(0.0, 0.0, -0.105),
        material=painted,
        name="round_shell",
    )
    lamp_head.visual(
        Cylinder(radius=0.125, length=0.035),
        origin=_cyl_z(0.0, 0.0, -0.050),
        material=satin,
        name="rear_cap",
    )
    lamp_head.visual(
        mesh_from_cadquery(_annular_ring(0.176, 0.135, 0.014), "front_bezel"),
        origin=Origin(xyz=(0.0, 0.0, -0.151)),
        material=satin,
        name="front_bezel",
    )
    lamp_head.visual(
        Cylinder(radius=0.132, length=0.006),
        origin=_cyl_z(0.0, 0.0, -0.1505),
        material=lens,
        name="diffuser_lens",
    )
    lamp_head.visual(
        Cylinder(radius=0.015, length=0.073),
        origin=_cyl_z(0.0, 0.0, -0.190),
        material=satin,
        name="sterile_handle_stem",
    )
    lamp_head.visual(
        Sphere(radius=0.030),
        origin=Origin(xyz=(0.0, 0.0, -0.232)),
        material=painted,
        name="sterile_handle",
    )

    model.articulation(
        "shoulder",
        ArticulationType.REVOLUTE,
        parent=ceiling_plate,
        child=upper_arm,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.5, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "elbow",
        ArticulationType.REVOLUTE,
        parent=upper_arm,
        child=forearm,
        origin=Origin(xyz=(0.85, 0.0, -0.060)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=14.0, velocity=1.2, lower=-1.15, upper=1.25),
    )
    model.articulation(
        "pan",
        ArticulationType.REVOLUTE,
        parent=forearm,
        child=yoke,
        origin=Origin(xyz=(0.65, 0.0, -0.050)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.4, lower=-2.60, upper=2.60),
    )
    model.articulation(
        "tilt",
        ArticulationType.REVOLUTE,
        parent=yoke,
        child=lamp_head,
        origin=Origin(xyz=(0.0, 0.0, -0.270)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=6.0, velocity=1.0, lower=-0.95, upper=0.95),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
