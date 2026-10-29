# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bench_vise_with_prismatic_jaw, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bench_vise_with_prismatic_jaw

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
def _tube_mesh(name: str, *, outer_radius: float, inner_radius: float, length: float):
    """Hollow cylinder mesh centered on local X, used for guide/nut bushings."""
    tube = (
        cq.Workplane("YZ")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
        .translate((-length / 2.0, 0.0, 0.0))
    )
    return mesh_from_cadquery(tube, name, tolerance=0.0008, angular_tolerance=0.08)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cast_iron_woodworking_vise")

    cast_iron = Material("dark_cast_iron", rgba=(0.08, 0.085, 0.09, 1.0))
    worn_edge = Material("worn_cast_edges", rgba=(0.16, 0.16, 0.15, 1.0))
    oiled_steel = Material("oiled_steel", rgba=(0.55, 0.57, 0.58, 1.0))
    dark_steel = Material("darkened_steel", rgba=(0.18, 0.18, 0.17, 1.0))
    bench_wood = Material("aged_bench_wood", rgba=(0.50, 0.32, 0.17, 1.0))
    jaw_wood = Material("maple_jaw_liners", rgba=(0.70, 0.50, 0.27, 1.0))

    guide_sleeve_mesh = _tube_mesh(
        "fixed_guide_sleeve", outer_radius=0.042, inner_radius=0.024, length=0.12
    )
    screw_nut_mesh = _tube_mesh(
        "fixed_screw_nut", outer_radius=0.047, inner_radius=0.027, length=0.13
    )
    sliding_screw_boss_mesh = _tube_mesh(
        "sliding_screw_boss", outer_radius=0.047, inner_radius=0.0138, length=0.080
    )
    bench_mount = model.part("bench_mount")

    # Bench edge and apron that the fixed vise casting is bolted to.
    bench_mount.visual(
        Box((0.70, 0.55, 0.065)),
        origin=Origin(xyz=(-0.285, 0.0, 0.795)),
        material=bench_wood,
        name="bench_top",
    )
    bench_mount.visual(
        Box((0.085, 0.55, 0.13)),
        origin=Origin(xyz=(-0.030, 0.0, 0.490)),
        material=bench_wood,
        name="lower_apron",
    )
    for index, y in enumerate((-0.250, 0.250)):
        bench_mount.visual(
            Box((0.085, 0.055, 0.36)),
            origin=Origin(xyz=(-0.030, y, 0.600)),
            material=bench_wood,
            name=f"side_apron_{index}",
        )

    # Fixed jaw casting, guide-bushing yoke, and bolted back plate.
    bench_mount.visual(
        Box((0.070, 0.405, 0.205)),
        origin=Origin(xyz=(0.020, 0.0, 0.835)),
        material=cast_iron,
        name="fixed_backplate",
    )
    bench_mount.visual(
        Box((0.025, 0.350, 0.155)),
        origin=Origin(xyz=(0.0675, 0.0, 0.850)),
        material=jaw_wood,
        name="fixed_pad",
    )
    bench_mount.visual(
        Box((0.078, 0.370, 0.038)),
        origin=Origin(xyz=(0.000, 0.0, 0.565)),
        material=cast_iron,
        name="lower_yoke",
    )
    for index, y in enumerate((-0.115, 0.115)):
        bench_mount.visual(
            guide_sleeve_mesh,
            origin=Origin(xyz=(0.0, y, 0.620)),
            material=cast_iron,
            name=f"guide_sleeve_{index}",
        )
        bench_mount.visual(
            Box((0.070, 0.075, 0.135)),
            origin=Origin(xyz=(0.010, y, 0.7225)),
            material=cast_iron,
            name=f"sleeve_web_{index}",
        )

    bench_mount.visual(
        screw_nut_mesh,
        origin=Origin(xyz=(0.0, 0.0, 0.700)),
        material=cast_iron,
        name="screw_nut",
    )
    bench_mount.visual(
        Box((0.082, 0.080, 0.060)),
        origin=Origin(xyz=(0.010, 0.0, 0.770)),
        material=cast_iron,
        name="nut_web",
    )

    # Bolt heads through the fixed casting into the bench apron.
    for index, (y, z) in enumerate(((-0.160, 0.895), (0.160, 0.895), (-0.160, 0.772), (0.160, 0.772))):
        bench_mount.visual(
            Cylinder(radius=0.018, length=0.012),
            origin=Origin(xyz=(0.084, y, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_steel,
            name=f"bolt_head_{index}",
        )

    # Subtle horizontal grain/groove lines on the fixed wooden jaw liner.
    for index, z in enumerate((0.812, 0.850, 0.888)):
        bench_mount.visual(
            Box((0.004, 0.330, 0.005)),
            origin=Origin(xyz=(0.082, 0.0, z)),
            material=bench_wood,
            name=f"fixed_grain_{index}",
        )

    sliding_jaw = model.part("sliding_jaw")
    sliding_jaw.visual(
        Box((0.078, 0.395, 0.205)),
        origin=Origin(xyz=(0.164, 0.0, 0.835)),
        material=cast_iron,
        name="sliding_casting",
    )
    sliding_jaw.visual(
        Box((0.025, 0.350, 0.155)),
        origin=Origin(xyz=(0.1175, 0.0, 0.850)),
        material=jaw_wood,
        name="sliding_pad",
    )
    sliding_jaw.visual(
        Box((0.060, 0.310, 0.030)),
        origin=Origin(xyz=(0.156, 0.0, 0.745)),
        material=cast_iron,
        name="jaw_throat_rib",
    )

    for index, y in enumerate((-0.115, 0.115)):
        sliding_jaw.visual(
            Cylinder(radius=0.039, length=0.085),
            origin=Origin(xyz=(0.158, y, 0.620), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=cast_iron,
            name=f"rod_boss_{index}",
        )
        sliding_jaw.visual(
            Box((0.072, 0.072, 0.110)),
            origin=Origin(xyz=(0.158, y, 0.700)),
            material=cast_iron,
            name=f"rod_lug_{index}",
        )

    sliding_jaw.visual(
        sliding_screw_boss_mesh,
        origin=Origin(xyz=(0.158, 0.0, 0.700)),
        material=cast_iron,
        name="screw_boss",
    )

    for index, z in enumerate((0.812, 0.850, 0.888)):
        sliding_jaw.visual(
            Box((0.004, 0.330, 0.005)),
            origin=Origin(xyz=(0.104, 0.0, z)),
            material=bench_wood,
            name=f"sliding_grain_{index}",
        )

    guide_rod_0 = model.part("guide_rod_0")
    guide_rod_0.visual(
        Cylinder(radius=0.0244, length=0.330),
        origin=Origin(xyz=(-0.035, -0.115, 0.620), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=oiled_steel,
        name="rod",
    )
    guide_rod_1 = model.part("guide_rod_1")
    guide_rod_1.visual(
        Cylinder(radius=0.0244, length=0.330),
        origin=Origin(xyz=(-0.035, 0.115, 0.620), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=oiled_steel,
        name="rod",
    )

    screw_spindle = model.part("screw_spindle")
    screw_spindle.visual(
        Cylinder(radius=0.014, length=0.580),
        origin=Origin(xyz=(0.110, 0.0, 0.700), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=oiled_steel,
        name="spindle",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.024, length=0.060),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="handle_hub",
    )
    handle.visual(
        Cylinder(radius=0.008, length=0.330),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=oiled_steel,
        name="tommy_bar",
    )
    for index, y in enumerate((-0.175, 0.175)):
        handle.visual(
            Sphere(radius=0.022),
            origin=Origin(xyz=(0.0, y, 0.0)),
            material=dark_steel,
            name=f"bar_knob_{index}",
        )

    model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=bench_mount,
        child=sliding_jaw,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=900.0, velocity=0.08, lower=0.0, upper=0.20),
    )
    model.articulation(
        "jaw_to_guide_0",
        ArticulationType.FIXED,
        parent=sliding_jaw,
        child=guide_rod_0,
        origin=Origin(),
    )
    model.articulation(
        "jaw_to_guide_1",
        ArticulationType.FIXED,
        parent=sliding_jaw,
        child=guide_rod_1,
        origin=Origin(),
    )
    model.articulation(
        "jaw_to_screw",
        ArticulationType.FIXED,
        parent=sliding_jaw,
        child=screw_spindle,
        origin=Origin(),
    )
    model.articulation(
        "handle_spin",
        ArticulationType.CONTINUOUS,
        parent=screw_spindle,
        child=handle,
        origin=Origin(xyz=(0.430, 0.0, 0.700)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=20.0, velocity=4.0),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
