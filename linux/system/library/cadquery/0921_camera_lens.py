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
IRIS_CENTER_Z = 0.040
ZOOM_CENTER_Z = 0.106
FOCUS_CENTER_Z = 0.1835
IRIS_SUPPORT_RADIUS = 0.041
ZOOM_SUPPORT_RADIUS = 0.046
FOCUS_SUPPORT_RADIUS = 0.049
def build_front_barrel_shell() -> cq.Workplane:
    outer = cq.Workplane("XY").workplane(offset=0.226).circle(0.071).extrude(0.060)
    front_cell = cq.Workplane("XY").workplane(offset=0.226).circle(0.052).extrude(0.022)
    front_opening = cq.Workplane("XY").workplane(offset=0.248).circle(0.0555).extrude(0.038)
    return outer.cut(front_cell).cut(front_opening)
def build_geared_ring(
    *,
    inner_radius: float,
    width: float,
    wall: float,
    tooth_height: float,
    tooth_count: int,
    tooth_fill: float = 0.58,
) -> cq.Workplane:
    base_outer_radius = inner_radius + wall
    bore = cq.Workplane("XY").circle(inner_radius).extrude((width + 0.004) / 2.0, both=True)
    ring = cq.Workplane("XY").circle(base_outer_radius).extrude(width / 2.0, both=True).cut(bore)

    tooth_band_width = width * 0.82
    tooth_pitch = 2.0 * math.pi * (base_outer_radius + tooth_height * 0.5) / tooth_count
    tooth_width = tooth_pitch * tooth_fill
    tooth = (
        cq.Workplane("XY")
        .rect(tooth_height, tooth_width)
        .extrude(tooth_band_width / 2.0, both=True)
        .translate((base_outer_radius + tooth_height / 2.0, 0.0, 0.0))
    )
    for idx in range(tooth_count):
        ring = ring.union(tooth.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 360.0 * idx / tooth_count))

    return ring.cut(bore)
def add_rotating_ring(
    model: ArticulatedObject,
    *,
    name: str,
    band_name: str,
    mesh_name: str,
    center_z: float,
    inner_radius: float,
    width: float,
    wall: float,
    tooth_height: float,
    tooth_count: int,
    material: str,
) -> None:
    ring = model.part(name)
    ring.visual(
        mesh_from_cadquery(
            build_geared_ring(
                inner_radius=inner_radius,
                width=width,
                wall=wall,
                tooth_height=tooth_height,
                tooth_count=tooth_count,
            ),
            mesh_name,
        ),
        material=material,
        name=band_name,
    )
    model.articulation(
        f"body_to_{name}",
        ArticulationType.CONTINUOUS,
        parent="body",
        child=ring,
        origin=Origin(xyz=(0.0, 0.0, center_z)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=1.5, velocity=4.0),
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cinema_zoom_lens")

    body_black = model.material("body_black", rgba=(0.08, 0.08, 0.09, 1.0))
    ring_black = model.material("ring_black", rgba=(0.12, 0.12, 0.13, 1.0))

    body = model.part("body")
    body.visual(
        Cylinder(radius=0.039, length=0.030),
        material=body_black,
        origin=Origin(xyz=(0.0, 0.0, 0.015)),
        name="rear_body",
    )
    body.visual(
        Cylinder(radius=IRIS_SUPPORT_RADIUS, length=0.026),
        material=body_black,
        origin=Origin(xyz=(0.0, 0.0, 0.041)),
        name="iris_support",
    )
    body.visual(
        Cylinder(radius=ZOOM_SUPPORT_RADIUS, length=0.080),
        material=body_black,
        origin=Origin(xyz=(0.0, 0.0, 0.092)),
        name="zoom_body",
    )
    body.visual(
        Cylinder(radius=FOCUS_SUPPORT_RADIUS, length=0.083),
        material=body_black,
        origin=Origin(xyz=(0.0, 0.0, 0.1715)),
        name="focus_body",
    )
    body.visual(
        Cylinder(radius=0.054, length=0.017),
        material=body_black,
        origin=Origin(xyz=(0.0, 0.0, 0.2195)),
        name="front_collar",
    )
    body.visual(
        mesh_from_cadquery(build_front_barrel_shell(), "front_barrel_shell"),
        material=body_black,
        name="front_barrel",
    )

    add_rotating_ring(
        model,
        name="iris_ring",
        band_name="iris_ring_band",
        mesh_name="iris_ring",
        center_z=IRIS_CENTER_Z,
        inner_radius=IRIS_SUPPORT_RADIUS,
        width=0.020,
        wall=0.0032,
        tooth_height=0.0028,
        tooth_count=52,
        material=ring_black,
    )
    add_rotating_ring(
        model,
        name="zoom_ring",
        band_name="zoom_ring_band",
        mesh_name="zoom_ring",
        center_z=ZOOM_CENTER_Z,
        inner_radius=ZOOM_SUPPORT_RADIUS,
        width=0.044,
        wall=0.0036,
        tooth_height=0.0031,
        tooth_count=60,
        material=ring_black,
    )
    add_rotating_ring(
        model,
        name="focus_ring",
        band_name="focus_ring_band",
        mesh_name="focus_ring",
        center_z=FOCUS_CENTER_Z,
        inner_radius=FOCUS_SUPPORT_RADIUS,
        width=0.050,
        wall=0.0038,
        tooth_height=0.0035,
        tooth_count=68,
        material=ring_black,
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
