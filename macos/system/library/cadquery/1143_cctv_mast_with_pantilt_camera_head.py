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
def _tube_shape(
    length: float,
    outer_radius: float,
    inner_radius: float,
    *,
    collar_radius: float | None = None,
    collar_height: float = 0.0,
) -> cq.Workplane:
    """Open telescoping tube, extruded from local z=0 to z=length."""
    tube = cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(length)
    if collar_radius is not None and collar_height > 0.0:
        collar = (
            cq.Workplane("XY")
            .circle(collar_radius)
            .circle(inner_radius)
            .extrude(collar_height)
            .translate((0.0, 0.0, length - collar_height))
        )
        tube = tube.union(collar)
    return tube
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="telescoping_cctv_mast")

    dark_metal = model.material("dark_galvanized_metal", rgba=(0.12, 0.13, 0.13, 1.0))
    brushed = model.material("brushed_aluminum", rgba=(0.62, 0.64, 0.62, 1.0))
    ballast_gray = model.material("rubberized_ballast_gray", rgba=(0.18, 0.19, 0.20, 1.0))
    black = model.material("matte_black", rgba=(0.01, 0.01, 0.012, 1.0))
    camera_white = model.material("powder_coated_camera_white", rgba=(0.88, 0.88, 0.84, 1.0))
    glass = model.material("dark_lens_glass", rgba=(0.03, 0.05, 0.08, 0.82))

    # Root: heavy ballast slab, fixed lower sleeve, welded flange, and a clamp knob.
    base = model.part("ballast_base")
    base.visual(
        Box((0.82, 0.56, 0.12)),
        origin=Origin(xyz=(0.0, 0.0, 0.06)),
        material=ballast_gray,
        name="ballast_slab",
    )
    base.visual(
        Cylinder(radius=0.13, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.125)),
        material=dark_metal,
        name="welded_flange",
    )
    base.visual(
        mesh_from_cadquery(
            _tube_shape(0.83, 0.065, 0.048, collar_radius=0.079, collar_height=0.07),
            "outer_sleeve",
            tolerance=0.0008,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.12)),
        material=dark_metal,
        name="outer_sleeve",
    )
    # Rubber feet are slightly embedded in the slab so they read as bolted-on pads.
    for idx, (x, y) in enumerate(
        ((-0.32, -0.20), (-0.32, 0.20), (0.32, -0.20), (0.32, 0.20))
    ):
        base.visual(
            Cylinder(radius=0.055, length=0.026),
            origin=Origin(xyz=(x, y, 0.004)),
            material=black,
            name=f"rubber_foot_{idx}",
        )
    base.visual(
        Box((0.070, 0.030, 0.045)),
        origin=Origin(xyz=(0.0, -0.070, 0.905)),
        material=dark_metal,
        name="clamp_boss",
    )
    base.visual(
        Cylinder(radius=0.010, length=0.040),
        origin=Origin(xyz=(0.0, -0.090, 0.905), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="clamp_screw",
    )
    base.visual(
        Cylinder(radius=0.020, length=0.045),
        origin=Origin(xyz=(0.0, -0.115, 0.905), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=black,
        name="clamp_knob",
    )

    # First moving stage: a hollow middle tube with a locking collar at its top.
    middle_stage = model.part("middle_stage")
    middle_stage.visual(
        mesh_from_cadquery(
            _tube_shape(1.40, 0.040, 0.030, collar_radius=0.050, collar_height=0.065),
            "middle_tube",
            tolerance=0.0008,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, -0.65)),
        material=brushed,
        name="middle_tube",
    )
    middle_stage.visual(
        mesh_from_cadquery(
            _tube_shape(0.040, 0.072, 0.038),
            "middle_stop_collar",
            tolerance=0.0008,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=dark_metal,
        name="middle_stop_collar",
    )

    # Second moving stage: slender upper pole with a pan-bearing cap at the top.
    upper_stage = model.part("upper_stage")
    upper_stage.visual(
        Cylinder(radius=0.024, length=1.05),
        origin=Origin(xyz=(0.0, 0.0, -0.025)),
        material=brushed,
        name="upper_pole",
    )
    upper_stage.visual(
        mesh_from_cadquery(
            _tube_shape(0.035, 0.045, 0.022),
            "upper_stop_collar",
            tolerance=0.0008,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=dark_metal,
        name="upper_stop_collar",
    )
    upper_stage.visual(
        Cylinder(radius=0.044, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.515)),
        material=dark_metal,
        name="pan_cap",
    )

    # Pan part: turntable plus U-yoke side plates that carry the tilt trunnions.
    pan_yoke = model.part("pan_yoke")
    pan_yoke.visual(
        Cylinder(radius=0.070, length=0.035),
        origin=Origin(xyz=(0.0, 0.0, 0.0175)),
        material=dark_metal,
        name="turntable",
    )
    pan_yoke.visual(
        Cylinder(radius=0.030, length=0.080),
        origin=Origin(xyz=(0.0, 0.0, 0.075)),
        material=dark_metal,
        name="yoke_stem",
    )
    pan_yoke.visual(
        Box((0.085, 0.205, 0.030)),
        origin=Origin(xyz=(0.0, 0.0, 0.105)),
        material=dark_metal,
        name="yoke_bridge",
    )
    pan_yoke.visual(
        Box((0.055, 0.018, 0.120)),
        origin=Origin(xyz=(0.0, -0.085, 0.170)),
        material=dark_metal,
        name="yoke_cheek_0",
    )
    pan_yoke.visual(
        Box((0.055, 0.018, 0.120)),
        origin=Origin(xyz=(0.0, 0.085, 0.170)),
        material=dark_metal,
        name="yoke_cheek_1",
    )

    # Box camera head carried by the tilt axis.  The child frame is the trunnion axis.
    camera = model.part("camera_head")
    camera.visual(
        Box((0.240, 0.130, 0.100)),
        origin=Origin(xyz=(0.080, 0.0, 0.0)),
        material=camera_white,
        name="camera_body",
    )
    camera.visual(
        Box((0.285, 0.165, 0.014)),
        origin=Origin(xyz=(0.080, 0.0, 0.057)),
        material=camera_white,
        name="sun_hood",
    )
    camera.visual(
        Cylinder(radius=0.018, length=0.152),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=dark_metal,
        name="tilt_trunnion",
    )
    camera.visual(
        Cylinder(radius=0.036, length=0.060),
        origin=Origin(xyz=(0.230, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=black,
        name="lens_barrel",
    )
    camera.visual(
        Cylinder(radius=0.029, length=0.010),
        origin=Origin(xyz=(0.265, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="front_glass",
    )

    model.articulation(
        "base_to_middle",
        ArticulationType.PRISMATIC,
        parent=base,
        child=middle_stage,
        origin=Origin(xyz=(0.0, 0.0, 0.95)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=120.0, velocity=0.18, lower=0.0, upper=0.55),
    )
    model.articulation(
        "middle_to_upper",
        ArticulationType.PRISMATIC,
        parent=middle_stage,
        child=upper_stage,
        origin=Origin(xyz=(0.0, 0.0, 0.75)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=80.0, velocity=0.16, lower=0.0, upper=0.45),
    )
    model.articulation(
        "upper_to_pan",
        ArticulationType.REVOLUTE,
        parent=upper_stage,
        child=pan_yoke,
        origin=Origin(xyz=(0.0, 0.0, 0.535)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.2, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "pan_to_camera",
        ArticulationType.REVOLUTE,
        parent=pan_yoke,
        child=camera,
        origin=Origin(xyz=(0.0, 0.0, 0.200)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.0, lower=-0.45, upper=0.80),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
