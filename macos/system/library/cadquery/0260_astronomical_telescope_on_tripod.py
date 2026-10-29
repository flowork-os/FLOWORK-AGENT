# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, astronomical_telescope_on_tripod, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: astronomical_telescope_on_tripod

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
def _annular_cylinder(axis: str, outer_radius: float, inner_radius: float, length: float) -> cq.Workplane:
    """Return a CadQuery annular sleeve centered on the origin and aligned to an axis."""
    plane = {"x": "YZ", "y": "XZ", "z": "XY"}[axis]
    return (
        cq.Workplane(plane)
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length / 2.0, both=True)
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="goto_single_arm_newtonian_reflector")

    mount_black = model.material("matte_black", rgba=(0.015, 0.017, 0.020, 1.0))
    mount_blue = model.material("deep_blue_mount", rgba=(0.03, 0.06, 0.13, 1.0))
    tube_white = model.material("warm_white_tube", rgba=(0.88, 0.86, 0.78, 1.0))
    dark_graphite = model.material("dark_graphite", rgba=(0.05, 0.055, 0.060, 1.0))
    machined = model.material("machined_aluminum", rgba=(0.55, 0.57, 0.58, 1.0))
    glass = model.material("faint_mirror_glass", rgba=(0.50, 0.62, 0.68, 0.75))

    # A compact flat tripod head with three radial socket pads and a fixed lower
    # half of the azimuth bearing.
    tripod_head = model.part("tripod_head")
    tripod_head.visual(
        Cylinder(radius=0.30, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 0.025)),
        material=mount_black,
        name="flat_plate",
    )
    tripod_head.visual(
        Cylinder(radius=0.18, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 0.075)),
        material=machined,
        name="fixed_bearing_race",
    )
    for i, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        tripod_head.visual(
            Box((0.22, 0.075, 0.038)),
            origin=Origin(
                xyz=(0.32 * math.cos(angle), 0.32 * math.sin(angle), 0.026),
                rpy=(0.0, 0.0, angle),
            ),
            material=mount_black,
            name=f"tripod_socket_{i}",
        )

    # Rotating computerized single-arm fork mount.  Its child frame is on the
    # azimuth axis at the top of the tripod head, so z=0 is the bearing plane.
    fork_arm = model.part("fork_arm")
    fork_arm.visual(
        Cylinder(radius=0.215, length=0.070),
        origin=Origin(xyz=(0.0, 0.0, 0.035)),
        material=mount_blue,
        name="azimuth_motor_housing",
    )
    fork_arm.visual(
        Cylinder(radius=0.150, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.079)),
        material=machined,
        name="rotating_bearing_race",
    )

    arm_shell = (
        cq.Workplane("XY")
        .box(0.16, 0.14, 0.68)
        .edges("|Z")
        .fillet(0.025)
        .translate((0.0, -0.265, 0.405))
    )
    fork_arm.visual(
        mesh_from_cadquery(arm_shell, "fork_arm_shell", tolerance=0.0015),
        material=mount_blue,
        name="fork_arm_shell",
    )
    fork_arm.visual(
        Box((0.25, 0.12, 0.12)),
        origin=Origin(xyz=(0.0, -0.235, 0.105)),
        material=mount_blue,
        name="arm_foot_fillet",
    )
    fork_arm.visual(
        Box((0.105, 0.020, 0.22)),
        origin=Origin(xyz=(0.055, -0.342, 0.395), rpy=(0.0, 0.0, -0.10)),
        material=dark_graphite,
        name="electronics_panel",
    )

    altitude_bearing = _annular_cylinder("y", outer_radius=0.108, inner_radius=0.055, length=0.080)
    fork_arm.visual(
        mesh_from_cadquery(altitude_bearing, "altitude_bearing_ring", tolerance=0.001),
        origin=Origin(xyz=(0.0, -0.190, 0.740)),
        material=machined,
        name="altitude_bearing_ring",
    )
    fork_arm.visual(
        Cylinder(radius=0.048, length=0.030),
        origin=Origin(xyz=(0.0, -0.236, 0.740), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark_graphite,
        name="altitude_motor_cap",
    )

    # Tube, cradle rings, focuser, and the visible altitude axle rotate together.
    # The part frame is at the altitude axis on the inside face of the fork arm.
    tube_cradle = model.part("tube_cradle")

    tube_shell = _annular_cylinder("x", outer_radius=0.115, inner_radius=0.104, length=1.10).translate(
        (0.0, 0.190, 0.0)
    )
    tube_cradle.visual(
        mesh_from_cadquery(tube_shell, "open_newtonian_tube", tolerance=0.0012),
        material=tube_white,
        name="open_tube",
    )
    tube_cradle.visual(
        mesh_from_cadquery(
            _annular_cylinder("x", outer_radius=0.124, inner_radius=0.102, length=0.026).translate(
                (0.555, 0.190, 0.0)
            ),
            "front_black_rim",
            tolerance=0.001,
        ),
        material=dark_graphite,
        name="front_rim",
    )
    tube_cradle.visual(
        Cylinder(radius=0.116, length=0.026),
        origin=Origin(xyz=(-0.552, 0.190, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_graphite,
        name="rear_cell",
    )
    tube_cradle.visual(
        Cylinder(radius=0.074, length=0.006),
        origin=Origin(xyz=(-0.568, 0.190, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=glass,
        name="primary_mirror",
    )

    for x in (-0.285, 0.285):
        tube_cradle.visual(
            mesh_from_cadquery(
                _annular_cylinder("x", outer_radius=0.148, inner_radius=0.112, length=0.045).translate(
                    (x, 0.190, 0.0)
                ),
                f"cradle_ring_{'front' if x > 0 else 'rear'}",
                tolerance=0.001,
            ),
            material=mount_black,
            name=f"cradle_ring_{'front' if x > 0 else 'rear'}",
        )
    tube_cradle.visual(
        Box((0.76, 0.045, 0.030)),
        origin=Origin(xyz=(0.0, 0.190, -0.135)),
        material=mount_black,
        name="dovetail_rail",
    )
    tube_cradle.visual(
        Box((0.32, 0.120, 0.090)),
        origin=Origin(xyz=(0.0, 0.102, 0.0)),
        material=mount_black,
        name="side_saddle",
    )
    tube_cradle.visual(
        Cylinder(radius=0.040, length=0.205),
        origin=Origin(xyz=(0.0, 0.1025, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=machined,
        name="altitude_axle",
    )
    tube_cradle.visual(
        Cylinder(radius=0.061, length=0.026),
        origin=Origin(xyz=(0.0, 0.053, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=machined,
        name="axle_collar",
    )

    # Newtonian side focuser near the open end: a raised base, drawtube, and
    # eyepiece identify the optical tube as a reflector rather than a refractor.
    tube_cradle.visual(
        Box((0.120, 0.070, 0.035)),
        origin=Origin(xyz=(0.330, 0.190, 0.116)),
        material=dark_graphite,
        name="focuser_base",
    )
    tube_cradle.visual(
        Cylinder(radius=0.034, length=0.110),
        origin=Origin(xyz=(0.330, 0.190, 0.180)),
        material=mount_black,
        name="focuser_drawtube",
    )
    tube_cradle.visual(
        Cylinder(radius=0.026, length=0.070),
        origin=Origin(xyz=(0.330, 0.190, 0.270)),
        material=machined,
        name="eyepiece",
    )

    model.articulation(
        "azimuth_bearing",
        ArticulationType.CONTINUOUS,
        parent=tripod_head,
        child=fork_arm,
        origin=Origin(xyz=(0.0, 0.0, 0.100)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=80.0, velocity=0.65),
    )
    model.articulation(
        "altitude_axis",
        ArticulationType.REVOLUTE,
        parent=fork_arm,
        child=tube_cradle,
        origin=Origin(xyz=(0.0, -0.190, 0.740)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=45.0, velocity=0.45, lower=0.0, upper=1.45),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
