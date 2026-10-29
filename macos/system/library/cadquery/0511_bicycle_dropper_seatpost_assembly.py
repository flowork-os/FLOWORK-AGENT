# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, bicycle_dropper_seatpost_assembly, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: bicycle_dropper_seatpost_assembly

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
def _annular_tube(outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """A watertight hollow cylinder running from z=0 to z=length."""
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(length)
def _rounded_box(size: tuple[float, float, float], radius: float) -> cq.Workplane:
    """Low-profile rounded rectangular clamp pieces."""
    x, y, z = size
    return cq.Workplane("XY").box(x, y, z).edges("|Z").fillet(radius)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="carbon_fibre_dropper_seatpost")

    carbon = model.material("satin_carbon", rgba=(0.015, 0.016, 0.017, 1.0))
    weave_dark = model.material("subtle_black_weave", rgba=(0.004, 0.004, 0.005, 1.0))
    weave_sheen = model.material("graphite_weave_sheen", rgba=(0.105, 0.115, 0.12, 1.0))
    anodized = model.material("black_anodized_alloy", rgba=(0.01, 0.011, 0.012, 1.0))
    stanchion = model.material("polished_black_stanchion", rgba=(0.025, 0.027, 0.030, 1.0))
    titanium = model.material("brushed_titanium", rgba=(0.62, 0.60, 0.55, 1.0))
    rubber = model.material("matte_black_seal", rgba=(0.002, 0.002, 0.002, 1.0))

    outer_radius = 0.0160
    outer_bore_radius = 0.0136
    outer_length = 0.430
    collar_outer_radius = 0.0200
    collar_bore_radius = 0.0142
    collar_length = 0.038
    collar_z = outer_length - 0.025

    outer_tube = model.part("outer_tube")
    outer_tube.visual(
        mesh_from_cadquery(
            _annular_tube(outer_radius, outer_bore_radius, outer_length),
            "outer_tube_shell",
            tolerance=0.00045,
            angular_tolerance=0.06,
        ),
        material=carbon,
        name="outer_shell",
    )
    outer_tube.visual(
        mesh_from_cadquery(
            _annular_tube(collar_outer_radius, collar_bore_radius, collar_length),
            "upper_seal_collar",
            tolerance=0.0004,
            angular_tolerance=0.06,
        ),
        origin=Origin(xyz=(0.0, 0.0, collar_z)),
        material=anodized,
        name="seal_collar",
    )
    outer_tube.visual(
        mesh_from_cadquery(
            _annular_tube(0.0165, outer_bore_radius, 0.010),
            "lower_reinforced_lip",
            tolerance=0.00045,
            angular_tolerance=0.06,
        ),
        material=anodized,
        name="lower_lip",
    )
    outer_tube.visual(
        mesh_from_cadquery(
            _annular_tube(0.0158, 0.0130, 0.010),
            "rubber_wiper",
            tolerance=0.00035,
            angular_tolerance=0.06,
        ),
        origin=Origin(xyz=(0.0, 0.0, outer_length + 0.004)),
        material=rubber,
        name="wiper_seal",
    )

    # Raised, shallow tangent strips give the dark tube a woven carbon-fibre read
    # without turning the post into a heavy patterned mesh.
    strip_radius = outer_radius + 0.00012
    for i in range(18):
        theta = i * (2.0 * math.pi / 18.0)
        z = 0.060 + (i % 6) * 0.055
        pitch = math.radians(23.0 if i % 2 == 0 else -23.0)
        material = weave_sheen if i % 3 == 0 else weave_dark
        outer_tube.visual(
            Box((0.0009, 0.0038, 0.112)),
            origin=Origin(
                xyz=(strip_radius * math.cos(theta), strip_radius * math.sin(theta), z),
                rpy=(pitch, 0.0, theta),
            ),
            material=material,
            name=f"weave_strip_{i}",
        )

    inner_post = model.part("inner_post")
    inner_radius = 0.0122
    inner_length = 0.530
    inner_center_z = -0.125
    inner_post.visual(
        Cylinder(radius=inner_radius, length=inner_length),
        origin=Origin(xyz=(0.0, 0.0, inner_center_z)),
        material=stanchion,
        name="sliding_shaft",
    )
    for name, z, length in (
        ("upper_guide_bushing", -0.020, 0.020),
        ("lower_guide_bushing", -0.310, 0.016),
    ):
        inner_post.visual(
            Cylinder(radius=0.01372, length=length),
            origin=Origin(xyz=(0.0, 0.0, z)),
            material=anodized,
            name=name,
        )
    inner_post.visual(
        Cylinder(radius=0.0142, length=0.030),
        origin=Origin(xyz=(0.0, 0.0, 0.145)),
        material=anodized,
        name="head_socket",
    )
    inner_post.visual(
        mesh_from_cadquery(
            _rounded_box((0.095, 0.046, 0.018), 0.006),
            "inline_clamp_base",
            tolerance=0.00035,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.162)),
        material=anodized,
        name="clamp_base",
    )
    inner_post.visual(
        mesh_from_cadquery(
            _rounded_box((0.084, 0.044, 0.008), 0.004),
            "low_profile_top_plate",
            tolerance=0.00035,
            angular_tolerance=0.08,
        ),
        origin=Origin(xyz=(0.0, 0.0, 0.189)),
        material=anodized,
        name="top_plate",
    )
    for y in (-0.0175, 0.0175):
        inner_post.visual(
            Box((0.086, 0.0085, 0.012)),
            origin=Origin(xyz=(0.0, y, 0.176)),
            material=anodized,
            name=f"rail_cradle_{'neg' if y < 0.0 else 'pos'}",
        )
        inner_post.visual(
            Cylinder(radius=0.0032, length=0.112),
            origin=Origin(xyz=(0.0, y, 0.183), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=titanium,
            name=f"saddle_rail_{'neg' if y < 0.0 else 'pos'}",
        )

    for x in (-0.030, 0.030):
        inner_post.visual(
            Cylinder(radius=0.0060, length=0.006),
            origin=Origin(xyz=(x, 0.0, 0.1959)),
            material=titanium,
            name=f"bolt_head_{'front' if x > 0.0 else 'rear'}",
        )
        inner_post.visual(
            Cylinder(radius=0.0032, length=0.0015),
            origin=Origin(xyz=(x, 0.0, 0.1995)),
            material=weave_dark,
            name=f"hex_recess_{'front' if x > 0.0 else 'rear'}",
        )

    for i, z in enumerate((-0.020, 0.020, 0.060, 0.100)):
        inner_post.visual(
            Box((0.0008, 0.009, 0.0018)),
            origin=Origin(xyz=(inner_radius + 0.00015, 0.0, z), rpy=(0.0, 0.0, 0.0)),
            material=weave_sheen,
            name=f"height_mark_{i}",
        )

    model.articulation(
        "tube_to_post",
        ArticulationType.PRISMATIC,
        parent=outer_tube,
        child=inner_post,
        origin=Origin(xyz=(0.0, 0.0, outer_length)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=180.0, velocity=0.35, lower=0.0, upper=0.160),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
