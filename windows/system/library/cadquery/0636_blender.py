# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blender, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blender

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
def _rounded_rect_sketch(width: float, depth: float, radius: float) -> cq.Sketch:
    return cq.Sketch().rect(width, depth).vertices().fillet(radius)
def _build_base_shape() -> cq.Workplane:
    lower = _rounded_rect_sketch(0.260, 0.220, 0.034)
    mid = _rounded_rect_sketch(0.246, 0.206, 0.031).moved(z=0.034)
    upper = _rounded_rect_sketch(0.206, 0.170, 0.027).moved(z=0.070)

    housing = cq.Workplane("XY").placeSketch(lower, mid, upper).loft()
    top_pad = (
        cq.Workplane("XY")
        .transformed(offset=(0.0, 0.0, 0.070))
        .placeSketch(_rounded_rect_sketch(0.154, 0.126, 0.020))
        .extrude(0.008)
    )
    return housing.union(top_pad)
def _build_pitcher_shell() -> cq.Workplane:
    outer = cq.Workplane("XY").placeSketch(
        _rounded_rect_sketch(0.112, 0.110, 0.018),
        _rounded_rect_sketch(0.128, 0.126, 0.020).moved(z=0.170),
        _rounded_rect_sketch(0.148, 0.142, 0.022).moved(z=0.300),
    ).loft()

    inner = cq.Workplane("XY").placeSketch(
        _rounded_rect_sketch(0.090, 0.088, 0.013).moved(z=0.012),
        _rounded_rect_sketch(0.116, 0.114, 0.015).moved(z=0.180),
        _rounded_rect_sketch(0.132, 0.128, 0.018).moved(z=0.330),
    ).loft()

    return outer.cut(inner)
def _build_cap_cover() -> cq.Workplane:
    cover = (
        cq.Workplane("XY")
        .transformed(offset=(0.075, 0.0, -0.006))
        .placeSketch(_rounded_rect_sketch(0.146, 0.136, 0.018))
        .extrude(0.012)
    )
    dome = (
        cq.Workplane("XY")
        .transformed(offset=(0.075, 0.0, 0.006))
        .circle(0.028)
        .extrude(0.008)
    )
    button_bore = (
        cq.Workplane("XY")
        .transformed(offset=(0.075, 0.0, -0.012))
        .circle(0.0115)
        .extrude(0.032)
    )
    return cover.union(dome).cut(button_bore)
def _build_cap_plug() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .transformed(offset=(0.075, 0.0, -0.018))
        .placeSketch(_rounded_rect_sketch(0.122, 0.116, 0.015))
        .extrude(0.012)
    )
def _build_blade_shape() -> cq.Workplane:
    assembly = (
        cq.Workplane("XY").circle(0.016).extrude(0.006).union(
            cq.Workplane("XY").circle(0.005).extrude(0.014)
        )
    )

    base_blade = (
        cq.Workplane("XY")
        .box(0.050, 0.011, 0.0018, centered=(True, True, False))
        .translate((0.018, 0.0, 0.0035))
    )
    blade_specs = (
        (0.0, 18.0),
        (90.0, -16.0),
        (180.0, 12.0),
        (270.0, -14.0),
    )
    for yaw_deg, pitch_deg in blade_specs:
        blade = base_blade.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), pitch_deg).rotate(
            (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), yaw_deg
        )
        assembly = assembly.union(blade)
    return assembly
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="vacuum_blender")

    body_graphite = model.material("body_graphite", rgba=(0.16, 0.17, 0.19, 1.0))
    gloss_black = model.material("gloss_black", rgba=(0.08, 0.09, 0.10, 1.0))
    soft_black = model.material("soft_black", rgba=(0.12, 0.12, 0.13, 1.0))
    brushed_metal = model.material("brushed_metal", rgba=(0.74, 0.76, 0.78, 1.0))
    smoky_tritan = model.material("smoky_tritan", rgba=(0.76, 0.84, 0.90, 0.34))
    seal_black = model.material("seal_black", rgba=(0.10, 0.11, 0.11, 1.0))
    blade_steel = model.material("blade_steel", rgba=(0.80, 0.82, 0.84, 1.0))
    button_metal = model.material("button_metal", rgba=(0.88, 0.89, 0.90, 1.0))

    base_shell_mesh = mesh_from_cadquery(_build_base_shape(), "vacuum_blender_base_shell")
    pitcher_shell_mesh = mesh_from_cadquery(_build_pitcher_shell(), "vacuum_blender_pitcher_shell")
    cap_cover_mesh = mesh_from_cadquery(_build_cap_cover(), "vacuum_blender_cap_cover")
    cap_plug_mesh = mesh_from_cadquery(_build_cap_plug(), "vacuum_blender_cap_plug")
    blade_mesh = mesh_from_cadquery(_build_blade_shape(), "vacuum_blender_blade")

    base = model.part("base")
    base.visual(base_shell_mesh, material=body_graphite, name="base_shell")
    base.visual(
        Box((0.118, 0.118, 0.005)),
        origin=Origin(xyz=(0.0, 0.0, 0.0755)),
        material=brushed_metal,
        name="deck_plate",
    )
    base.visual(
        Box((0.004, 0.096, 0.032)),
        origin=Origin(xyz=(0.119, 0.0, 0.038)),
        material=gloss_black,
        name="status_panel",
    )
    base.inertial = Inertial.from_geometry(
        Box((0.260, 0.220, 0.083)),
        mass=4.8,
        origin=Origin(xyz=(0.0, 0.0, 0.0415)),
    )

    pitcher = model.part("pitcher")
    pitcher.visual(pitcher_shell_mesh, material=smoky_tritan, name="jar_shell")
    pitcher.visual(
        Box((0.040, 0.040, 0.022)),
        origin=Origin(xyz=(0.012, 0.084, 0.236)),
        material=soft_black,
        name="handle_upper_bridge",
    )
    pitcher.visual(
        Box((0.034, 0.040, 0.024)),
        origin=Origin(xyz=(0.020, 0.084, 0.102)),
        material=soft_black,
        name="handle_lower_bridge",
    )
    pitcher.visual(
        Box((0.026, 0.020, 0.170)),
        origin=Origin(xyz=(0.012, 0.101, 0.164)),
        material=soft_black,
        name="handle_grip",
    )
    pitcher.visual(
        Cylinder(radius=0.034, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=seal_black,
        name="blade_seat",
    )
    for index, y_pos in enumerate((-0.038, 0.038)):
        pitcher.visual(
            Box((0.020, 0.016, 0.012)),
            origin=Origin(xyz=(-0.070, y_pos, 0.292)),
            material=soft_black,
            name=f"hinge_support_{index}",
        )
        pitcher.visual(
            Box((0.010, 0.016, 0.024)),
            origin=Origin(xyz=(-0.082, y_pos, 0.296)),
            material=soft_black,
            name=f"hinge_post_{index}",
        )
        pitcher.visual(
            Cylinder(radius=0.0055, length=0.020),
            origin=Origin(
                xyz=(-0.082, y_pos, 0.308),
                rpy=(math.pi / 2.0, 0.0, 0.0),
            ),
            material=soft_black,
            name=f"hinge_barrel_{index}",
        )
    pitcher.inertial = Inertial.from_geometry(
        Box((0.160, 0.120, 0.312)),
        mass=1.2,
        origin=Origin(xyz=(0.0, 0.0, 0.156)),
    )

    cap = model.part("cap")
    cap.visual(cap_cover_mesh, material=gloss_black, name="cap_cover")
    cap.visual(cap_plug_mesh, material=seal_black, name="seal_plug")
    cap.visual(
        Box((0.024, 0.074, 0.010)),
        origin=Origin(xyz=(0.010, 0.0, -0.001)),
        material=gloss_black,
        name="hinge_bridge",
    )
    cap.visual(
        Cylinder(radius=0.0053, length=0.050),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=soft_black,
        name="hinge_barrel",
    )
    cap.inertial = Inertial.from_geometry(
        Box((0.150, 0.140, 0.040)),
        mass=0.22,
        origin=Origin(xyz=(0.075, 0.0, 0.0)),
    )

    button = model.part("release_button")
    button.visual(
        Cylinder(radius=0.0105, length=0.004),
        origin=Origin(xyz=(0.0, 0.0, 0.002)),
        material=button_metal,
        name="button_cap",
    )
    button.visual(
        Cylinder(radius=0.0065, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -0.006)),
        material=button_metal,
        name="button_stem",
    )
    button.visual(
        Cylinder(radius=0.0125, length=0.003),
        origin=Origin(xyz=(0.0, 0.0, -0.0145)),
        material=button_metal,
        name="button_retainer",
    )
    button.inertial = Inertial.from_geometry(
        Cylinder(radius=0.011, length=0.020),
        mass=0.02,
        origin=Origin(),
    )

    blade = model.part("blade")
    blade.visual(blade_mesh, material=blade_steel, name="blade_assembly")
    blade.visual(
        Cylinder(radius=0.0045, length=0.020),
        origin=Origin(xyz=(0.0, 0.0, -0.008)),
        material=blade_steel,
        name="blade_spindle",
    )
    blade.inertial = Inertial.from_geometry(
        Cylinder(radius=0.045, length=0.018),
        mass=0.08,
        origin=Origin(xyz=(0.0, 0.0, 0.007)),
    )

    model.articulation(
        "base_to_pitcher",
        ArticulationType.FIXED,
        parent=base,
        child=pitcher,
        origin=Origin(xyz=(0.0, 0.0, 0.078)),
    )
    model.articulation(
        "pitcher_to_cap",
        ArticulationType.REVOLUTE,
        parent=pitcher,
        child=cap,
        origin=Origin(xyz=(-0.076, 0.0, 0.308)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=2.0,
            lower=0.0,
            upper=math.radians(110.0),
        ),
    )
    model.articulation(
        "cap_to_release_button",
        ArticulationType.PRISMATIC,
        parent=cap,
        child=button,
        origin=Origin(xyz=(0.075, 0.0, 0.010)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=0.08,
            lower=0.0,
            upper=0.005,
        ),
    )
    model.articulation(
        "pitcher_to_blade",
        ArticulationType.CONTINUOUS,
        parent=pitcher,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.022)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=30.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
