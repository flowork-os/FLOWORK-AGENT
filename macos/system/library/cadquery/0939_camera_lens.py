# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camera_lens, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camera_lens

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
def _annular_cylinder(outer_radius: float, inner_radius: float, length: float):
    """A centered, open-ended tube with its optical axis on local Z."""
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length / 2.0, both=True)
    )
def _flared_tube(
    rear_outer: float,
    front_outer: float,
    rear_inner: float,
    front_inner: float,
    length: float,
):
    """A front lens shade/hood tube that runs from local z=0 to z=length."""
    outer = (
        cq.Workplane("XY")
        .circle(rear_outer)
        .workplane(offset=length)
        .circle(front_outer)
        .loft(combine=True)
    )
    inner = (
        cq.Workplane("XY")
        .circle(rear_inner)
        .workplane(offset=length)
        .circle(front_inner)
        .loft(combine=True)
    )
    return outer.cut(inner)
def _radial_box_origin(radius: float, angle: float, z: float) -> Origin:
    """Place a box with local +X radial and local +Y tangential."""
    return Origin(
        xyz=(radius * math.cos(angle), radius * math.sin(angle), z),
        rpy=(0.0, 0.0, angle),
    )
def _add_radial_box(
    part,
    *,
    name: str,
    radius: float,
    angle: float,
    z: float,
    size: tuple[float, float, float],
    material: Material,
):
    part.visual(
        Box(size),
        origin=_radial_box_origin(radius, angle, z),
        material=material,
        name=name,
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cinema_prime_lens")

    matte_black = model.material("matte_black", rgba=(0.005, 0.005, 0.004, 1.0))
    satin_black = model.material("satin_black", rgba=(0.018, 0.017, 0.015, 1.0))
    rubber = model.material("knurled_rubber", rgba=(0.002, 0.002, 0.002, 1.0))
    dark_metal = model.material("dark_anodized_metal", rgba=(0.035, 0.035, 0.033, 1.0))
    bare_metal = model.material("brushed_mount_metal", rgba=(0.55, 0.52, 0.46, 1.0))
    engraving = model.material("filled_engraving", rgba=(0.82, 0.82, 0.76, 1.0))
    glass = model.material("coated_glass", rgba=(0.10, 0.24, 0.32, 0.72))
    amber = model.material("amber_index_dot", rgba=(1.0, 0.48, 0.08, 1.0))

    barrel = model.part("barrel")

    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.052, 0.034, 0.150), "control_sleeve"),
        origin=Origin(xyz=(0.0, 0.0, -0.005)),
        material=matte_black,
        name="control_sleeve",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.050, 0.034, 0.082), "rear_barrel"),
        origin=Origin(xyz=(0.0, 0.0, -0.102)),
        material=satin_black,
        name="rear_barrel",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.060, 0.036, 0.012), "rear_shoulder"),
        origin=Origin(xyz=(0.0, 0.0, -0.081)),
        material=dark_metal,
        name="rear_shoulder",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.061, 0.052, 0.006), "iris_rear_stop"),
        origin=Origin(xyz=(0.0, 0.0, -0.073)),
        material=dark_metal,
        name="iris_rear_stop",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.061, 0.052, 0.006), "iris_front_stop"),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=dark_metal,
        name="iris_front_stop",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.068, 0.052, 0.006), "focus_rear_stop"),
        origin=Origin(xyz=(0.0, 0.0, -0.028)),
        material=dark_metal,
        name="focus_rear_stop",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.068, 0.052, 0.006), "focus_front_stop"),
        origin=Origin(xyz=(0.0, 0.0, 0.056)),
        material=dark_metal,
        name="focus_front_stop",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.063, 0.038, 0.012), "front_shoulder"),
        origin=Origin(xyz=(0.0, 0.0, 0.072)),
        material=dark_metal,
        name="front_shoulder",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.075, 0.045, 0.054), "front_housing"),
        origin=Origin(xyz=(0.0, 0.0, 0.105)),
        material=matte_black,
        name="front_housing",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.083, 0.052, 0.014), "front_flange"),
        origin=Origin(xyz=(0.0, 0.0, 0.139)),
        material=dark_metal,
        name="front_flange",
    )
    barrel.visual(
        Cylinder(radius=0.043, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.137)),
        material=glass,
        name="front_element",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.053, 0.041, 0.006), "front_retainer"),
        origin=Origin(xyz=(0.0, 0.0, 0.137)),
        material=dark_metal,
        name="front_retainer",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.058, 0.035, 0.018), "rear_mount"),
        origin=Origin(xyz=(0.0, 0.0, -0.151)),
        material=bare_metal,
        name="rear_mount",
    )
    barrel.visual(
        Cylinder(radius=0.033, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, -0.162)),
        material=glass,
        name="rear_element",
    )
    barrel.visual(
        mesh_from_cadquery(_annular_cylinder(0.037, 0.031, 0.004), "rear_retainer"),
        origin=Origin(xyz=(0.0, 0.0, -0.162)),
        material=dark_metal,
        name="rear_retainer",
    )

    for i, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        _add_radial_box(
            barrel,
            name=f"front_bayonet_lug_{i}",
            radius=0.083,
            angle=angle,
            z=0.142,
            size=(0.008, 0.026, 0.006),
            material=dark_metal,
        )
        _add_radial_box(
            barrel,
            name=f"rear_mount_tab_{i}",
            radius=0.057,
            angle=angle + math.pi / 8.0,
            z=-0.161,
            size=(0.010, 0.020, 0.005),
            material=bare_metal,
        )

    # Fixed witness marks between the moving focus and iris bands.
    _add_radial_box(
        barrel,
        name="witness_line",
        radius=0.0528,
        angle=math.pi / 2.0,
        z=-0.029,
        size=(0.004, 0.005, 0.020),
        material=engraving,
    )
    _add_radial_box(
        barrel,
        name="witness_dot",
        radius=0.0528,
        angle=math.pi / 2.0,
        z=-0.012,
        size=(0.004, 0.006, 0.006),
        material=amber,
    )

    lever_angle = -0.42
    pivot_radius = 0.070
    pivot_xyz = (
        pivot_radius * math.cos(lever_angle),
        pivot_radius * math.sin(lever_angle),
        -0.151,
    )
    _add_radial_box(
        barrel,
        name="lever_bridge",
        radius=0.064,
        angle=lever_angle,
        z=-0.151,
        size=(0.020, 0.014, 0.012),
        material=dark_metal,
    )
    barrel.visual(
        Cylinder(radius=0.005, length=0.010),
        origin=Origin(xyz=pivot_xyz),
        material=bare_metal,
        name="lever_pivot",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(_annular_cylinder(0.068, 0.056, 0.078), "focus_band"),
        material=rubber,
        name="focus_band",
    )
    for i in range(48):
        angle = 2.0 * math.pi * i / 48.0
        _add_radial_box(
            focus_ring,
            name=f"focus_grip_{i}",
            radius=0.0684,
            angle=angle,
            z=0.0,
            size=(0.0032, 0.0038, 0.070),
            material=rubber,
        )
    for i in range(12):
        angle = 2.0 * math.pi * i / 12.0
        tick_len = 0.018 if i % 3 == 0 else 0.010
        _add_radial_box(
            focus_ring,
            name=f"focus_scale_tick_{i}",
            radius=0.0701,
            angle=angle,
            z=0.030,
            size=(0.0014, 0.0030, tick_len),
            material=engraving,
        )

    iris_ring = model.part("iris_ring")
    iris_ring.visual(
        mesh_from_cadquery(_annular_cylinder(0.061, 0.055, 0.032), "iris_band"),
        material=satin_black,
        name="iris_band",
    )
    for i in range(9):
        angle = 2.0 * math.pi * i / 9.0 + 0.10
        _add_radial_box(
            iris_ring,
            name=f"iris_mark_{i}",
            radius=0.0616,
            angle=angle,
            z=0.006,
            size=(0.0012, 0.0030, 0.012),
            material=engraving,
        )
    _add_radial_box(
        iris_ring,
        name="iris_index_dot",
        radius=0.0610,
        angle=math.pi / 2.0,
        z=-0.010,
        size=(0.0020, 0.005, 0.005),
        material=amber,
    )

    lens_shade = model.part("lens_shade")
    lens_shade.visual(
        mesh_from_cadquery(
            _flared_tube(0.067, 0.091, 0.057, 0.080, 0.084),
            "shade_body",
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=matte_black,
        name="shade_body",
    )
    lens_shade.visual(
        mesh_from_cadquery(_annular_cylinder(0.071, 0.057, 0.012), "shade_collar"),
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        material=dark_metal,
        name="shade_collar",
    )
    for i, angle in enumerate((0.12, 2.0 * math.pi / 3.0 + 0.12, 4.0 * math.pi / 3.0 + 0.12)):
        _add_radial_box(
            lens_shade,
            name=f"shade_bayonet_key_{i}",
            radius=0.070,
            angle=angle,
            z=0.009,
            size=(0.008, 0.025, 0.007),
            material=dark_metal,
        )
    _add_radial_box(
        lens_shade,
        name="shade_alignment_dot",
        radius=0.0710,
        angle=math.pi / 2.0,
        z=0.013,
        size=(0.0020, 0.006, 0.006),
        material=engraving,
    )

    lock_lever = model.part("lock_lever")
    lock_lever.visual(
        Box((0.008, 0.045, 0.005)),
        origin=Origin(xyz=(0.006, 0.023, 0.008)),
        material=bare_metal,
        name="lever_blade",
    )
    lock_lever.visual(
        Box((0.010, 0.012, 0.005)),
        origin=Origin(xyz=(0.006, 0.002, 0.008)),
        material=dark_metal,
        name="lever_root",
    )

    model.articulation(
        "barrel_to_focus",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=focus_ring,
        origin=Origin(xyz=(0.0, 0.0, 0.014)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=1.5, lower=-2.1, upper=2.1),
    )
    model.articulation(
        "barrel_to_iris",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=iris_ring,
        origin=Origin(xyz=(0.0, 0.0, -0.054)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.0, velocity=1.2, lower=0.0, upper=1.45),
    )
    model.articulation(
        "barrel_to_shade",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=lens_shade,
        origin=Origin(xyz=(0.0, 0.0, 0.142)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=3.0, velocity=1.0, lower=0.0, upper=0.35),
    )
    model.articulation(
        "barrel_to_lever",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=lock_lever,
        origin=Origin(xyz=pivot_xyz, rpy=(0.0, 0.0, lever_angle)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.5, velocity=2.0, lower=-0.45, upper=0.45),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
