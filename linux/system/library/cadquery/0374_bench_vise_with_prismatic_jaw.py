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
def _x_cylinder(
    radius: float,
    length: float,
    *,
    center_x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
) -> cq.Workplane:
    """CadQuery cylinder whose axis is the model's horizontal X screw/rod axis."""
    return (
        cq.Workplane("YZ")
        .center(y, z)
        .circle(radius)
        .extrude(length)
        .translate((center_x - 0.5 * length, 0.0, 0.0))
    )
def _annular_x_bushing(
    *,
    outer_radius: float,
    inner_radius: float,
    length: float,
    center_x: float,
    y: float,
    z: float,
) -> cq.Workplane:
    outer = _x_cylinder(outer_radius, length, center_x=center_x, y=y, z=z)
    inner = _x_cylinder(inner_radius, length + 0.006, center_x=center_x, y=y, z=z)
    return outer.cut(inner)
def _box_with_x_holes(
    *,
    x_min: float,
    x_max: float,
    y_size: float,
    z_size: float,
    holes: tuple[tuple[float, float, float], ...],
) -> cq.Workplane:
    """Box in global axes, with circular through-holes bored along X."""
    x_size = x_max - x_min
    center_x = 0.5 * (x_min + x_max)
    body = cq.Workplane("XY").box(x_size, y_size, z_size).translate((center_x, 0.0, 0.0))
    for y, z, radius in holes:
        cutter = _x_cylinder(radius, x_size + 0.030, center_x=center_x, y=y, z=z)
        body = body.cut(cutter)
    return body
def _threaded_screw_mesh() -> cq.Workplane:
    """A ridged lead-screw: a slim shaft with repeated crest bands."""
    shaft = _x_cylinder(0.0165, 0.440, center_x=-0.080)
    pitch = 0.010
    for i in range(34):
        x = -0.245 + i * pitch
        crest = _x_cylinder(0.0205, 0.0045, center_x=x)
        shaft = shaft.union(crest)
    return shaft
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="woodworking_front_vise")

    jaw_wood = model.material("oiled_maple", rgba=(0.72, 0.48, 0.25, 1.0))
    bench_wood = model.material("dark_bench_wood", rgba=(0.38, 0.22, 0.11, 1.0))
    end_grain = model.material("end_grain", rgba=(0.56, 0.34, 0.17, 1.0))
    steel = model.material("brushed_steel", rgba=(0.48, 0.50, 0.50, 1.0))
    dark_steel = model.material("darkened_thread", rgba=(0.18, 0.19, 0.19, 1.0))
    handle_wood = model.material("handle_wood", rgba=(0.67, 0.39, 0.18, 1.0))

    screw_hole = (0.0, 0.0, 0.029)
    guide_holes = ((-0.225, -0.055, 0.021), (0.225, -0.055, 0.021))
    all_holes = (screw_hole, *guide_holes)

    bench_front = model.part("bench_front")
    bench_front.visual(
        mesh_from_cadquery(
            _box_with_x_holes(
                x_min=-0.122,
                x_max=-0.052,
                y_size=0.800,
                z_size=0.320,
                holes=all_holes,
            ),
            "bench_apron",
        ),
        material=bench_wood,
        name="bench_apron",
    )
    bench_front.visual(
        Box((0.320, 0.820, 0.050)),
        origin=Origin(xyz=(-0.175, 0.0, 0.185)),
        material=bench_wood,
        name="bench_top",
    )
    bench_front.visual(
        mesh_from_cadquery(
            _box_with_x_holes(
                x_min=-0.055,
                x_max=0.0,
                y_size=0.680,
                z_size=0.180,
                holes=all_holes,
            ),
            "fixed_jaw",
        ),
        material=jaw_wood,
        name="fixed_jaw",
    )
    bench_front.visual(
        Box((0.006, 0.680, 0.020)),
        origin=Origin(xyz=(0.003, 0.0, 0.080)),
        material=end_grain,
        name="fixed_top_edge",
    )

    bench_front.visual(
        mesh_from_cadquery(
            _annular_x_bushing(
                outer_radius=0.047,
                inner_radius=0.026,
                length=0.026,
                center_x=0.013,
                y=0.0,
                z=0.0,
            ),
            "screw_nut",
        ),
        material=steel,
        name="screw_nut",
    )
    bench_front.visual(
        mesh_from_cadquery(
            _annular_x_bushing(
                outer_radius=0.032,
                inner_radius=0.0135,
                length=0.022,
                center_x=0.011,
                y=-0.225,
                z=-0.055,
            ),
            "guide_bushing_0",
        ),
        material=steel,
        name="guide_bushing_0",
    )
    bench_front.visual(
        mesh_from_cadquery(
            _annular_x_bushing(
                outer_radius=0.032,
                inner_radius=0.0135,
                length=0.022,
                center_x=0.011,
                y=0.225,
                z=-0.055,
            ),
            "guide_bushing_1",
        ),
        material=steel,
        name="guide_bushing_1",
    )

    bolt_locations = (
        (-0.285, 0.055),
        (0.285, 0.055),
        (-0.285, -0.055),
        (0.285, -0.055),
    )
    for idx, (y, z) in enumerate(bolt_locations):
        bench_front.visual(
            Cylinder(radius=0.018, length=0.009),
            origin=Origin(xyz=(0.0045, y, z), rpy=(0.0, math.pi / 2.0, 0.0)),
            material=dark_steel,
            name=f"bolt_head_{idx}",
        )

    moving_jaw = model.part("moving_jaw")
    moving_jaw.visual(
        mesh_from_cadquery(
            _box_with_x_holes(
                x_min=0.0,
                x_max=0.072,
                y_size=0.660,
                z_size=0.205,
                holes=((0.0, 0.0, 0.028),),
            ),
            "moving_jaw_face",
        ),
        material=jaw_wood,
        name="jaw_face",
    )
    moving_jaw.visual(
        Box((0.008, 0.660, 0.018)),
        origin=Origin(xyz=(0.076, 0.0, 0.090)),
        material=end_grain,
        name="moving_top_edge",
    )
    moving_jaw.visual(
        mesh_from_cadquery(
            _annular_x_bushing(
                outer_radius=0.038,
                inner_radius=0.024,
                length=0.022,
                center_x=0.083,
                y=0.0,
                z=0.0,
            ),
            "moving_screw_collar",
        ),
        material=steel,
        name="screw_collar",
    )

    moving_jaw.visual(
        Cylinder(radius=0.014, length=0.380),
        origin=Origin(xyz=(-0.155, -0.225, -0.055), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="guide_rod_0",
    )
    moving_jaw.visual(
        Cylinder(radius=0.026, length=0.030),
        origin=Origin(xyz=(0.015, -0.225, -0.055), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="rod_socket_0",
    )
    moving_jaw.visual(
        Cylinder(radius=0.014, length=0.380),
        origin=Origin(xyz=(-0.155, 0.225, -0.055), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="guide_rod_1",
    )
    moving_jaw.visual(
        Cylinder(radius=0.026, length=0.030),
        origin=Origin(xyz=(0.015, 0.225, -0.055), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_steel,
        name="rod_socket_1",
    )

    model.articulation(
        "jaw_slide",
        ArticulationType.PRISMATIC,
        parent=bench_front,
        child=moving_jaw,
        origin=Origin(xyz=(0.035, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=750.0, velocity=0.18, lower=0.0, upper=0.180),
    )

    lead_screw = model.part("lead_screw")
    lead_screw.visual(
        mesh_from_cadquery(_threaded_screw_mesh(), "threaded_screw"),
        material=dark_steel,
        name="threaded_shaft",
    )
    lead_screw.visual(
        Cylinder(radius=0.032, length=0.064),
        origin=Origin(xyz=(0.124, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=steel,
        name="handle_hub",
    )
    lead_screw.visual(
        Cylinder(radius=0.017, length=0.390),
        origin=Origin(xyz=(0.145, 0.0, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=handle_wood,
        name="round_handle",
    )
    for idx, y in enumerate((-0.210, 0.210)):
        lead_screw.visual(
            Sphere(radius=0.033),
            origin=Origin(xyz=(0.145, y, 0.0)),
            material=handle_wood,
            name=f"handle_knob_{idx}",
        )

    model.articulation(
        "handle_spin",
        ArticulationType.CONTINUOUS,
        parent=moving_jaw,
        child=lead_screw,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=8.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
