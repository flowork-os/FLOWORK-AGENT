# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, binoculars, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: binoculars

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

class MotionProperties:
    def __init__(self, damping=None, friction=None):
        self.damping = damping
        self.friction = friction

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
MAT_ARMOR = Material("matte_black_rubber", rgba=(0.005, 0.006, 0.006, 1.0))
MAT_PANEL = Material("pebbled_charcoal_grip", rgba=(0.025, 0.026, 0.025, 1.0))
MAT_METAL = Material("satin_black_anodized_metal", rgba=(0.015, 0.015, 0.014, 1.0))
MAT_EDGE = Material("dry_graphite_edges", rgba=(0.080, 0.082, 0.078, 1.0))
MAT_GLASS = Material("green_blue_coated_glass", rgba=(0.04, 0.22, 0.25, 0.62))
MAT_MARK = Material("engraved_white_mark", rgba=(0.82, 0.84, 0.78, 1.0))
def _tube_x(outer_radius: float, inner_radius: float, length: float):
    """Hollow optical tube whose local extrusion axis is +X."""
    return cq.Workplane("YZ").circle(outer_radius).circle(inner_radius).extrude(length)
def _add_barrel_module(
    part,
    *,
    side: int,
    barrel_y: float,
    main_mesh_name: str,
    objective_mesh_name: str,
    eyecup_mesh_name: str,
) -> None:
    """Add one precision optical barrel with armor, lenses, and rubber grip."""
    # Main hollow rubber-armored barrel, open through the optical axis.
    part.visual(
        mesh_from_cadquery(_tube_x(0.029, 0.020, 0.122), main_mesh_name, tolerance=0.0007),
        origin=Origin(xyz=(-0.061, barrel_y, 0.0)),
        material=MAT_ARMOR,
        name="main_tube",
    )

    # Front objective bell with a larger annular retaining ring.
    part.visual(
        mesh_from_cadquery(_tube_x(0.036, 0.024, 0.033), objective_mesh_name, tolerance=0.0007),
        origin=Origin(xyz=(0.058, barrel_y, 0.0)),
        material=MAT_METAL,
        name="objective_ring",
    )
    part.visual(
        Cylinder(radius=0.0248, length=0.0026),
        origin=Origin(xyz=(0.0922, barrel_y, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=MAT_GLASS,
        name="objective_glass",
    )
    part.visual(
        Cylinder(radius=0.034, length=0.004),
        origin=Origin(xyz=(0.0545, barrel_y, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=MAT_EDGE,
        name="objective_shoulder",
    )

    # Rear eyepiece cup and ocular glass.
    part.visual(
        mesh_from_cadquery(_tube_x(0.026, 0.016, 0.030), eyecup_mesh_name, tolerance=0.0007),
        origin=Origin(xyz=(-0.090, barrel_y, 0.0)),
        material=MAT_ARMOR,
        name="eyecup",
    )
    part.visual(
        Cylinder(radius=0.0168, length=0.0022),
        origin=Origin(xyz=(-0.0908, barrel_y, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=MAT_GLASS,
        name="ocular_glass",
    )

    # Raised side grip pad and individual ribs.  They are slightly buried into
    # the tube/pad so the molded rubber reads as one connected armored shell.
    outer_y = barrel_y + side * 0.0310
    part.visual(
        Box((0.066, 0.0055, 0.030)),
        origin=Origin(xyz=(-0.002, outer_y, 0.0)),
        material=MAT_PANEL,
        name="grip_panel",
    )
    for i, x in enumerate((-0.031, -0.020, -0.009, 0.002, 0.013, 0.024)):
        part.visual(
            Box((0.0035, 0.0080, 0.032)),
            origin=Origin(xyz=(x, outer_y + side * 0.0020, 0.0)),
            material=MAT_EDGE,
            name=f"grip_rib_{i}",
        )

    # Fine protective lip rings at the two ends of the body tube.
    for i, x in enumerate((-0.055, 0.049)):
        part.visual(
            Cylinder(radius=0.0305, length=0.006),
            origin=Origin(xyz=(x, barrel_y, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=MAT_EDGE,
            name=f"armor_lip_{i}",
        )
def _add_focus_wheel(part) -> None:
    part.visual(
        Cylinder(radius=0.0140, length=0.032),
        origin=Origin(rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=MAT_EDGE,
        name="wheel_body",
    )
    for i in range(18):
        theta = 2.0 * math.pi * i / 18.0
        part.visual(
            Box((0.0028, 0.0340, 0.0042)),
            origin=Origin(
                xyz=(0.0142 * math.cos(theta), 0.0, 0.0142 * math.sin(theta)),
                rpy=(0.0, -theta, 0.0),
            ),
            material=MAT_PANEL,
            name=f"wheel_knurl_{i}",
        )
    part.visual(
        Box((0.004, 0.030, 0.0015)),
        origin=Origin(xyz=(0.0, 0.0, 0.0155)),
        material=MAT_MARK,
        name="index_mark",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="field_binoculars")

    left_barrel = model.part("left_barrel")
    right_barrel = model.part("right_barrel")
    focus_wheel = model.part("focus_wheel")

    # The part frames for both optical halves lie on the longitudinal hinge
    # axis.  The optical axes are parallel to +X and offset laterally in +/-Y.
    _add_barrel_module(
        left_barrel,
        side=-1,
        barrel_y=-0.044,
        main_mesh_name="left_hollow_barrel",
        objective_mesh_name="left_objective_annulus",
        eyecup_mesh_name="left_eyecup_annulus",
    )
    _add_barrel_module(
        right_barrel,
        side=1,
        barrel_y=0.044,
        main_mesh_name="right_hollow_barrel",
        objective_mesh_name="right_objective_annulus",
        eyecup_mesh_name="right_eyecup_annulus",
    )

    # Alternating exposed hinge knuckles on the shared IPD hinge axis.  The left
    # half carries the front/rear knuckles; the right half carries the center
    # knuckle, so the joint reads as a real interleaved hinge without broad
    # current-pose overlap.
    for i, x in enumerate((-0.052, 0.052)):
        left_barrel.visual(
            Cylinder(radius=0.0110, length=0.038),
            origin=Origin(xyz=(x, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=MAT_METAL,
            name=f"hinge_knuckle_{i}",
        )
        left_barrel.visual(
            Box((0.050, 0.016, 0.011)),
            origin=Origin(xyz=(x, -0.013, 0.0)),
            material=MAT_METAL,
            name=f"bridge_web_{i}",
        )
        left_barrel.visual(
            Box((0.032, 0.010, 0.007)),
            origin=Origin(xyz=(x, -0.024, 0.020)),
            material=MAT_EDGE,
            name=f"upper_bridge_rib_{i}",
        )
    right_barrel.visual(
        Cylinder(radius=0.0106, length=0.040),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=MAT_METAL,
        name="hinge_knuckle",
    )
    right_barrel.visual(
        Box((0.056, 0.016, 0.011)),
        origin=Origin(xyz=(0.0, 0.013, 0.0)),
        material=MAT_METAL,
        name="bridge_web",
    )
    right_barrel.visual(
        Box((0.034, 0.010, 0.007)),
        origin=Origin(xyz=(0.0, 0.024, 0.020)),
        material=MAT_EDGE,
        name="upper_bridge_rib",
    )

    # Small fixed saddle plates that visually cradle the focusing wheel above
    # the central bridge without intersecting the rotating wheel.
    left_barrel.visual(
        Box((0.014, 0.004, 0.024)),
        origin=Origin(xyz=(-0.013, -0.019, 0.023)),
        material=MAT_METAL,
        name="focus_yoke",
    )

    _add_focus_wheel(focus_wheel)

    model.articulation(
        "interpupillary_hinge",
        ArticulationType.REVOLUTE,
        parent=left_barrel,
        child=right_barrel,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=1.2, lower=-0.28, upper=0.28),
        motion_properties=MotionProperties(damping=0.08, friction=0.04),
    )
    model.articulation(
        "focus_axis",
        ArticulationType.CONTINUOUS,
        parent=left_barrel,
        child=focus_wheel,
        origin=Origin(xyz=(-0.013, 0.0, 0.045)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.25, velocity=5.0),
        motion_properties=MotionProperties(damping=0.02, friction=0.01),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
