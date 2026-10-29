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
BARREL_RADIUS = 0.0260
MOUNT_RADIUS = 0.0310
FRONT_BARREL_RADIUS = 0.0285
FILTER_RING_RADIUS = 0.0304
APERTURE_START = 0.0052
APERTURE_LENGTH = 0.0098
APERTURE_INNER_RADIUS = 0.0266
APERTURE_OUTER_RADIUS = 0.0292
APERTURE_RIB_RADIUS = 0.0298
FOCUS_START = 0.0180
FOCUS_LENGTH = 0.0255
FOCUS_INNER_RADIUS = 0.0274
FOCUS_OUTER_RADIUS = 0.0312
FOCUS_RIB_RADIUS = 0.0319
def _annular_ring(
    *,
    start_z: float,
    length: float,
    inner_radius: float,
    outer_radius: float,
    rib_radius: float,
    rib_count: int,
) -> cq.Workplane:
    ring = (
        cq.Workplane("XY")
        .workplane(offset=start_z)
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(length)
    )
    pitch = length / rib_count
    rib_length = min(0.0024, pitch * 0.62)
    for index in range(rib_count):
        rib_z = start_z + (index + 0.5) * pitch - (0.5 * rib_length)
        ring = ring.union(
            cq.Workplane("XY")
            .workplane(offset=rib_z)
            .circle(rib_radius)
            .circle(inner_radius)
            .extrude(rib_length)
        )
    return ring
def _barrel_shell() -> cq.Workplane:
    shell = cq.Workplane("XY").circle(BARREL_RADIUS).extrude(0.046)
    shell = shell.union(cq.Workplane("XY").circle(MOUNT_RADIUS).extrude(0.0028))
    shell = shell.union(
        cq.Workplane("XY").workplane(offset=0.046).circle(FRONT_BARREL_RADIUS).extrude(0.009)
    )
    shell = shell.union(
        cq.Workplane("XY").workplane(offset=0.055).circle(FILTER_RING_RADIUS).extrude(0.003)
    )
    shell = shell.cut(cq.Workplane("XY").workplane(offset=-0.001).circle(0.0204).extrude(0.060))
    shell = shell.cut(cq.Workplane("XY").workplane(offset=0.047).circle(0.0220).extrude(0.009))
    return shell
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="mirrorless_prime_lens")

    barrel_black = model.material("barrel_black", rgba=(0.09, 0.09, 0.10, 1.0))
    rubber_black = model.material("rubber_black", rgba=(0.13, 0.13, 0.14, 1.0))
    mount_metal = model.material("mount_metal", rgba=(0.73, 0.75, 0.78, 1.0))
    index_white = model.material("index_white", rgba=(0.93, 0.94, 0.96, 1.0))
    glass_blue = model.material("glass_blue", rgba=(0.12, 0.19, 0.26, 0.72))
    coating_blue = model.material("coating_blue", rgba=(0.18, 0.28, 0.38, 0.55))
    seam_gray = model.material("seam_gray", rgba=(0.30, 0.30, 0.31, 1.0))

    barrel = model.part("barrel")
    barrel.visual(
        mesh_from_cadquery(_barrel_shell(), "barrel_shell"),
        material=barrel_black,
        name="barrel_shell",
    )
    barrel.visual(
        Cylinder(radius=APERTURE_INNER_RADIUS, length=APERTURE_LENGTH),
        origin=Origin(xyz=(0.0, 0.0, APERTURE_START + (0.5 * APERTURE_LENGTH))),
        material=barrel_black,
        name="aperture_track",
    )
    barrel.visual(
        Cylinder(radius=FOCUS_INNER_RADIUS, length=FOCUS_LENGTH),
        origin=Origin(xyz=(0.0, 0.0, FOCUS_START + (0.5 * FOCUS_LENGTH))),
        material=barrel_black,
        name="focus_track",
    )
    barrel.visual(
        Cylinder(radius=0.0309, length=0.0021),
        origin=Origin(xyz=(0.0, 0.0, 0.00105)),
        material=mount_metal,
        name="mount_flange",
    )
    barrel.visual(
        Box((0.0010, 0.0034, 0.0016)),
        origin=Origin(xyz=(APERTURE_INNER_RADIUS - 0.0002, 0.0, APERTURE_START + APERTURE_LENGTH + 0.0005)),
        material=index_white,
        name="index_line",
    )

    front_glass = model.part("front_glass")
    front_glass.visual(
        Cylinder(radius=0.0220, length=0.0032),
        origin=Origin(xyz=(0.0, 0.0, 0.0526)),
        material=glass_blue,
        name="front_glass",
    )
    front_glass.visual(
        Cylinder(radius=0.0172, length=0.0012),
        origin=Origin(xyz=(0.0, 0.0, 0.0540)),
        material=coating_blue,
        name="front_coating",
    )

    focus_ring = model.part("focus_ring")
    focus_ring.visual(
        mesh_from_cadquery(
            _annular_ring(
                start_z=FOCUS_START,
                length=FOCUS_LENGTH,
                inner_radius=FOCUS_INNER_RADIUS,
                outer_radius=FOCUS_OUTER_RADIUS,
                rib_radius=FOCUS_RIB_RADIUS,
                rib_count=7,
            ),
            "focus_ring",
        ),
        material=rubber_black,
        name="focus_band",
    )
    focus_ring.visual(
        Box((0.0012, 0.0024, 0.0052)),
        origin=Origin(xyz=(FOCUS_RIB_RADIUS - 0.0004, 0.0, FOCUS_START + (0.5 * FOCUS_LENGTH))),
        material=seam_gray,
        name="focus_mark",
    )

    aperture_ring = model.part("aperture_ring")
    aperture_ring.visual(
        mesh_from_cadquery(
            _annular_ring(
                start_z=APERTURE_START,
                length=APERTURE_LENGTH,
                inner_radius=APERTURE_INNER_RADIUS,
                outer_radius=APERTURE_OUTER_RADIUS,
                rib_radius=APERTURE_RIB_RADIUS,
                rib_count=5,
            ),
            "aperture_ring",
        ),
        material=rubber_black,
        name="aperture_band",
    )
    aperture_ring.visual(
        Box((0.0012, 0.0022, 0.0034)),
        origin=Origin(
            xyz=(APERTURE_RIB_RADIUS - 0.0004, 0.0, APERTURE_START + (0.5 * APERTURE_LENGTH))
        ),
        material=index_white,
        name="aperture_mark",
    )

    model.articulation(
        "front_mount",
        ArticulationType.FIXED,
        parent=barrel,
        child=front_glass,
        origin=Origin(),
    )
    model.articulation(
        "focus_rotation",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=focus_ring,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.25, velocity=8.0),
    )
    model.articulation(
        "aperture_rotation",
        ArticulationType.CONTINUOUS,
        parent=barrel,
        child=aperture_ring,
        origin=Origin(),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.18, velocity=6.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
