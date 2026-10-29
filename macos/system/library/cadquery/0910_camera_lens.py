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
def _tube(z0: float, z1: float, outer_radius: float, inner_radius: float) -> cq.Workplane:
    """Annular tube section on the optical Z axis."""
    height = z1 - z0
    outer = cq.Workplane("XY").circle(outer_radius).extrude(height)
    bore = cq.Workplane("XY").circle(inner_radius).extrude(height + 0.004).translate(
        (0.0, 0.0, -0.002)
    )
    return outer.cut(bore).translate((0.0, 0.0, z0))
def _trapezoid_prism_x(length: float, points_yz: list[tuple[float, float]]) -> cq.Workplane:
    """Extrude a Y/Z dovetail section along X and center it on the origin."""
    return (
        cq.Workplane("YZ")
        .polyline(points_yz)
        .close()
        .extrude(length)
        .translate((-length / 2.0, 0.0, 0.0))
    )
def _barrel_body() -> cq.Workplane:
    body = _tube(0.011, 0.023, 0.058, 0.046)
    body = body.union(_tube(0.020, 0.116, 0.052, 0.040))
    body = body.union(_tube(0.108, 0.128, 0.055, 0.035))

    # Raised longitudinal grip ribs on the fixed round barrel.
    for i in range(24):
        angle = 360.0 * i / 24.0
        rib = (
            cq.Workplane("XY")
            .box(0.006, 0.009, 0.040)
            .translate((0.052, 0.0, 0.066))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        body = body.union(rib)
    return body
def _camera_mount() -> cq.Workplane:
    mount = _tube(-0.024, -0.015, 0.060, 0.034)
    for i in range(3):
        angle = 120.0 * i + 18.0
        lug = (
            cq.Workplane("XY")
            .box(0.014, 0.006, 0.005)
            .translate((0.048, 0.0, -0.024))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        mount = mount.union(lug)
    return mount
def _rotation_ring() -> cq.Workplane:
    ring = _tube(-0.008, 0.004, 0.052, 0.034)

    # Two overhanging rails bridge the aperture and form the fixed dovetail guide.
    rail_len = 0.078
    upper = _trapezoid_prism_x(
        rail_len,
        [
            (0.026, 0.004),
            (0.035, 0.004),
            (0.035, 0.011),
            (0.022, 0.011),
        ],
    )
    lower = _trapezoid_prism_x(
        rail_len,
        [
            (-0.035, 0.004),
            (-0.026, 0.004),
            (-0.022, 0.011),
            (-0.035, 0.011),
        ],
    )
    ring = ring.union(upper).union(lower)

    # Small stop blocks at the ends of the guide show the usable shift travel.
    for x in (-0.046, 0.046):
        stop = cq.Workplane("XY").box(0.006, 0.036, 0.007).translate((x, 0.0, 0.0075))
        ring = ring.union(stop)
    return ring
def _optical_carriage() -> cq.Workplane:
    # Matching sliding dovetail tongue, captive under the guide lips.
    tongue = _trapezoid_prism_x(
        0.068,
        [
            (-0.026, 0.011),
            (0.026, 0.011),
            (0.022, 0.0178),
            (-0.022, 0.0178),
        ],
    )

    plate = (
        cq.Workplane("XY")
        .rect(0.058, 0.040)
        .extrude(0.008)
        .faces(">Z")
        .workplane()
        .circle(0.020)
        .cutThruAll()
        .translate((0.0, 0.0, 0.0178))
    )

    lens_cell = _tube(0.025, 0.096, 0.0265, 0.020)
    front_bezel = _tube(0.088, 0.100, 0.028, 0.018)
    rear_retainer = _tube(0.025, 0.034, 0.024, 0.018)
    return tongue.union(plate).union(lens_cell).union(front_bezel).union(rear_retainer)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="perspective_control_shift_lens")

    matte_black = model.material("matte_black", rgba=(0.005, 0.005, 0.006, 1.0))
    graphite = model.material("graphite", rgba=(0.09, 0.085, 0.08, 1.0))
    anodized_gray = model.material("anodized_gray", rgba=(0.42, 0.42, 0.40, 1.0))
    glass_blue = model.material("coated_glass", rgba=(0.18, 0.42, 0.72, 0.42))
    red = model.material("red_index", rgba=(0.9, 0.04, 0.02, 1.0))
    white = model.material("white_engraving", rgba=(0.9, 0.9, 0.82, 1.0))

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_barrel_body(), "barrel_body", tolerance=0.0008),
        material=matte_black,
        name="barrel_body",
    )
    barrel.visual(
        mesh_from_cadquery(_camera_mount(), "camera_mount", tolerance=0.0008),
        material=anodized_gray,
        name="camera_mount",
    )
    for i in range(3):
        angle = 2.0 * math.pi * i / 3.0 + math.pi / 6.0
        barrel.visual(
            Box((0.006, 0.012, 0.027)),
            origin=Origin(
                xyz=(0.057 * math.cos(angle), 0.057 * math.sin(angle), -0.002),
                rpy=(0.0, 0.0, angle),
            ),
            material=matte_black,
            name=f"bridge_pier_{i}",
        )
    barrel.visual(
        Cylinder(radius=0.0022, length=0.0015),
        origin=Origin(xyz=(0.0, -0.0570, 0.001), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=red,
        name="fixed_index_dot",
    )

    rotation_ring = model.part("rotation_ring")
    rotation_ring.visual(
        mesh_from_cadquery(_rotation_ring(), "rotation_ring", tolerance=0.0007),
        material=graphite,
        name="rotating_face",
    )
    rotation_ring.visual(
        Cylinder(radius=0.0016, length=0.0012),
        origin=Origin(xyz=(0.0, -0.0520, 0.0005), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=white,
        name="ring_index_dot",
    )

    optical_block = model.part("optical_block")
    optical_block.visual(
        mesh_from_cadquery(_optical_carriage(), "optical_carriage", tolerance=0.0007),
        material=anodized_gray,
        name="optical_carriage",
    )
    optical_block.visual(
        Cylinder(radius=0.0208, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.093), rpy=(0.0, 0.0, 0.0)),
        material=glass_blue,
        name="front_element",
    )

    model.articulation(
        "barrel_to_rotation_ring",
        ArticulationType.REVOLUTE,
        parent=barrel,
        child=rotation_ring,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=1.5, lower=-math.pi, upper=math.pi),
    )
    model.articulation(
        "ring_to_optical_block",
        ArticulationType.PRISMATIC,
        parent=rotation_ring,
        child=optical_block,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=0.08, lower=-0.012, upper=0.012),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
