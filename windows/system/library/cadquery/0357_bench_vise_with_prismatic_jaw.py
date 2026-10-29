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
def _x_cylinder_origin(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(0.0, math.pi / 2.0, 0.0))
def _y_cylinder_origin(x: float, y: float, z: float) -> Origin:
    return Origin(xyz=(x, y, z), rpy=(math.pi / 2.0, 0.0, 0.0))
def _rear_body_shape():
    body = cq.Workplane("XY").box(0.118, 0.160, 0.180).translate((-0.060, 0.0, 0.0))
    back_plate = cq.Workplane("XY").box(0.028, 0.142, 0.168).translate((-0.118, 0.0, -0.004))
    mounting_flange = cq.Workplane("XY").box(0.108, 0.130, 0.028).translate((-0.074, 0.0, -0.098))
    screw_box = cq.Workplane("YZ").workplane(offset=-0.040).circle(0.050).extrude(0.035, both=True)
    upper_boss = cq.Workplane("YZ").workplane(offset=-0.034).center(0.0, 0.050).circle(0.026).extrude(0.028, both=True)
    lower_boss = cq.Workplane("YZ").workplane(offset=-0.034).center(0.0, -0.050).circle(0.026).extrude(0.028, both=True)
    return body.union(back_plate).union(mounting_flange).union(screw_box).union(upper_boss).union(lower_boss)
def _front_carriage_shape():
    carriage = cq.Workplane("XY").box(0.126, 0.160, 0.188).translate((0.091, 0.0, 0.0))
    screw_hub = cq.Workplane("YZ").workplane(offset=0.154).circle(0.042).extrude(0.018, both=True)
    lever_boss = cq.Workplane("XZ").workplane(offset=0.091).center(0.118, 0.040).circle(0.015).extrude(0.012, both=True)
    shape = carriage.union(screw_hub).union(lever_boss)

    for bore_radius, bore_z in ((0.0130, 0.050), (0.0130, -0.050), (0.0190, 0.0)):
        cutter = (
            cq.Workplane("YZ")
            .workplane(offset=0.091)
            .center(0.0, bore_z)
            .circle(bore_radius)
            .extrude(0.230, both=True)
        )
        shape = shape.cut(cutter)

    return shape
def _handle_collar_shape():
    return (
        cq.Workplane("YZ")
        .workplane(offset=0.015)
        .circle(0.020)
        .circle(0.016)
        .extrude(0.015, both=True)
    )
def _front_chop_shape():
    chop = (
        cq.Workplane("YZ")
        .workplane(offset=0.019)
        .rect(0.360, 0.160)
        .extrude(0.019, both=True)
    )
    for hole_radius, hole_z in ((0.018, 0.050), (0.018, -0.050), (0.032, 0.0)):
        cutter = (
            cq.Workplane("YZ")
            .workplane(offset=0.019)
            .center(0.0, hole_z)
            .circle(hole_radius)
            .extrude(0.030, both=True)
        )
        chop = chop.cut(cutter)
    return chop
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="woodworking_quick_release_vise")

    cast_iron = model.material("cast_iron", rgba=(0.25, 0.28, 0.30, 1.0))
    steel = model.material("steel", rgba=(0.65, 0.67, 0.70, 1.0))
    blackened_steel = model.material("blackened_steel", rgba=(0.17, 0.18, 0.19, 1.0))
    oak = model.material("oak", rgba=(0.73, 0.58, 0.39, 1.0))
    walnut = model.material("walnut", rgba=(0.35, 0.23, 0.14, 1.0))

    rear_jaw = model.part("rear_jaw")
    rear_jaw.visual(
        mesh_from_cadquery(_rear_body_shape(), "rear_body"),
        material=cast_iron,
        name="rear_body",
    )
    rear_jaw.visual(
        Box((0.045, 0.360, 0.160)),
        origin=Origin(xyz=(-0.0225, 0.0, 0.0)),
        material=oak,
        name="rear_chop",
    )
    rear_jaw.visual(
        Cylinder(radius=0.012, length=0.440),
        origin=_x_cylinder_origin(0.215, 0.0, 0.050),
        material=steel,
        name="guide_rod_upper",
    )
    rear_jaw.visual(
        Cylinder(radius=0.012, length=0.440),
        origin=_x_cylinder_origin(0.215, 0.0, -0.050),
        material=steel,
        name="guide_rod_lower",
    )
    rear_jaw.visual(
        Cylinder(radius=0.014, length=0.175),
        origin=_x_cylinder_origin(0.0825, 0.0, 0.0),
        material=blackened_steel,
        name="lead_screw",
    )
    rear_jaw.visual(
        Cylinder(radius=0.028, length=0.038),
        origin=_x_cylinder_origin(-0.018, 0.0, 0.0),
        material=steel,
        name="thrust_collar",
    )

    front_jaw = model.part("front_jaw")
    front_jaw.visual(
        mesh_from_cadquery(_front_carriage_shape(), "guide_carriage"),
        material=cast_iron,
        name="guide_carriage",
    )
    front_jaw.visual(
        mesh_from_cadquery(_front_chop_shape(), "front_chop"),
        material=oak,
        name="front_chop",
    )
    front_jaw.visual(
        Cylinder(radius=0.010, length=0.026),
        origin=_y_cylinder_origin(0.118, 0.093, 0.040),
        material=steel,
        name="lever_mount",
    )

    handle = model.part("handle")
    handle.visual(
        Cylinder(radius=0.006, length=0.320),
        origin=_y_cylinder_origin(0.012, 0.0, 0.0),
        material=steel,
        name="handle_bar",
    )
    handle.visual(
        mesh_from_cadquery(_handle_collar_shape(), "handle_collar"),
        material=steel,
        name="handle_collar",
    )
    handle.visual(
        Cylinder(radius=0.012, length=0.060),
        origin=_y_cylinder_origin(0.012, 0.130, 0.0),
        material=walnut,
        name="grip_0",
    )
    handle.visual(
        Cylinder(radius=0.012, length=0.060),
        origin=_y_cylinder_origin(0.012, -0.130, 0.0),
        material=walnut,
        name="grip_1",
    )

    release_lever = model.part("release_lever")
    release_lever.visual(
        Cylinder(radius=0.008, length=0.018),
        origin=_y_cylinder_origin(0.0, 0.009, 0.0),
        material=steel,
        name="lever_hub",
    )
    release_lever.visual(
        Box((0.072, 0.014, 0.018)),
        origin=Origin(xyz=(0.036, 0.009, -0.012)),
        material=blackened_steel,
        name="lever_arm",
    )
    release_lever.visual(
        Cylinder(radius=0.008, length=0.026),
        origin=_y_cylinder_origin(0.072, 0.009, -0.012),
        material=walnut,
        name="lever_tip",
    )

    model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=rear_jaw,
        child=front_jaw,
        origin=Origin(),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=280.0, velocity=0.16, lower=0.0, upper=0.260),
    )
    model.articulation(
        "handle_spin",
        ArticulationType.CONTINUOUS,
        parent=front_jaw,
        child=handle,
        origin=Origin(xyz=(0.172, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=12.0),
    )
    model.articulation(
        "lever_pivot",
        ArticulationType.REVOLUTE,
        parent=front_jaw,
        child=release_lever,
        origin=Origin(xyz=(0.118, 0.106, 0.040)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=3.0, velocity=3.0, lower=-0.60, upper=0.70),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
