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
def _rounded_base_body() -> cq.Workplane:
    """Wide appliance base with softly radiused vertical corners."""
    return (
        cq.Workplane("XY")
        .box(0.380, 0.280, 0.135, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.024)
    )
def _jar_shell() -> cq.Workplane:
    """Transparent hollow rectangular jar shell with an open wide mouth."""
    outer_x, outer_y, height = 0.230, 0.190, 0.385
    wall, bottom = 0.012, 0.035
    shell = (
        cq.Workplane("XY")
        .box(outer_x, outer_y, height, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.018)
    )
    shell = (
        shell.faces(">Z")
        .workplane(centerOption="CenterOfMass")
        .rect(outer_x - 2.0 * wall, outer_y - 2.0 * wall)
        .cutBlind(-(height - bottom))
    )
    shaft_clearance = cq.Workplane("XY").circle(0.036).extrude(bottom + 0.012)
    return shell.cut(shaft_clearance)
def _annular_ring(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(height)
def _fill_cap() -> cq.Workplane:
    """Screw cap with a top disk, down-skirt, external thread bands, and a grip boss."""
    cap = cq.Workplane("XY").circle(0.113).extrude(0.026)
    skirt = (
        cq.Workplane("XY")
        .workplane(offset=-0.028)
        .circle(0.113)
        .circle(0.106)
        .extrude(0.028)
    )
    cap = cap.union(skirt)
    for z in (-0.022, -0.014, -0.006):
        band = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .circle(0.117)
            .circle(0.106)
            .extrude(0.003)
        )
        cap = cap.union(band)
    grip = cq.Workplane("XY").workplane(offset=0.026).circle(0.046).extrude(0.010)
    return cap.union(grip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cold_press_smoothie_blender")

    matte_black = model.material("matte_black", rgba=(0.015, 0.017, 0.020, 1.0))
    charcoal = model.material("charcoal_panel", rgba=(0.055, 0.060, 0.067, 1.0))
    brushed_steel = model.material("brushed_steel", rgba=(0.68, 0.70, 0.69, 1.0))
    rubber = model.material("black_rubber", rgba=(0.005, 0.005, 0.006, 1.0))
    polycarbonate = model.material("clear_polycarbonate", rgba=(0.72, 0.92, 1.00, 0.34))
    smoky_poly = model.material("smoky_polycarbonate", rgba=(0.40, 0.55, 0.62, 0.42))
    white_marking = model.material("etched_white", rgba=(0.92, 0.96, 1.00, 0.78))
    blade_steel = model.material("sharpened_steel", rgba=(0.86, 0.88, 0.86, 1.0))
    red_mark = model.material("red_index", rgba=(0.85, 0.06, 0.035, 1.0))

    base = model.part("base")
    base.visual(
        mesh_from_cadquery(_rounded_base_body(), "base_body", tolerance=0.0015),
        material=matte_black,
        name="base_body",
    )
    base.visual(
        Box((0.260, 0.010, 0.072)),
        origin=Origin(xyz=(0.0, -0.143, 0.074)),
        material=charcoal,
        name="front_panel",
    )
    base.visual(
        Cylinder(radius=0.088, length=0.022),
        origin=Origin(xyz=(0.0, 0.0, 0.146)),
        material=brushed_steel,
        name="bayonet_plate",
    )
    base.visual(
        Cylinder(radius=0.058, length=0.026),
        origin=Origin(xyz=(0.0, 0.0, 0.170)),
        material=brushed_steel,
        name="drive_socket",
    )
    for i, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        base.visual(
            Box((0.042, 0.014, 0.010)),
            origin=Origin(
                xyz=(0.079 * math.cos(angle), 0.079 * math.sin(angle), 0.162),
                rpy=(0.0, 0.0, angle + math.pi / 2.0),
            ),
            material=brushed_steel,
            name=f"bayonet_lug_{i}",
        )
    for i, (x, y) in enumerate(((-0.145, -0.095), (0.145, -0.095), (-0.145, 0.095), (0.145, 0.095))):
        base.visual(
            Cylinder(radius=0.024, length=0.012),
            origin=Origin(xyz=(x, y, 0.006)),
            material=rubber,
            name=f"foot_{i}",
        )

    jar = model.part("jar")
    jar.visual(
        Cylinder(radius=0.080, length=0.026),
        origin=Origin(xyz=(0.0, 0.0, 0.013)),
        material=brushed_steel,
        name="bayonet_skirt",
    )
    jar.visual(
        mesh_from_cadquery(_annular_ring(0.069, 0.018, 0.020), "lower_collar", tolerance=0.001),
        origin=Origin(xyz=(0.0, 0.0, 0.026)),
        material=charcoal,
        name="lower_collar",
    )
    jar.visual(
        mesh_from_cadquery(_jar_shell(), "jar_shell", tolerance=0.0012),
        origin=Origin(xyz=(0.0, 0.0, 0.045)),
        material=polycarbonate,
        name="jar_shell",
    )
    jar.visual(
        mesh_from_cadquery(_annular_ring(0.045, 0.014, 0.024), "blade_seal", tolerance=0.001),
        origin=Origin(xyz=(0.0, 0.0, 0.057)),
        material=charcoal,
        name="blade_seal",
    )
    jar.visual(
        mesh_from_cadquery(_annular_ring(0.103, 0.078, 0.032), "threaded_neck", tolerance=0.001),
        origin=Origin(xyz=(0.0, 0.0, 0.430)),
        material=polycarbonate,
        name="threaded_neck",
    )
    for i, z in enumerate((0.170, 0.220, 0.270, 0.320, 0.370)):
        tick_width = 0.052 if i % 2 == 0 else 0.034
        jar.visual(
            Box((tick_width, 0.0025, 0.004)),
            origin=Origin(xyz=(-0.063, -0.09625, z)),
            material=white_marking,
            name=f"measure_tick_{i}",
        )
    jar.visual(
        Box((0.066, 0.058, 0.022)),
        origin=Origin(xyz=(0.0, 0.116, 0.320)),
        material=smoky_poly,
        name="handle_upper_mount",
    )
    jar.visual(
        Box((0.066, 0.058, 0.022)),
        origin=Origin(xyz=(0.0, 0.116, 0.145)),
        material=smoky_poly,
        name="handle_lower_mount",
    )
    jar.visual(
        Box((0.046, 0.034, 0.202)),
        origin=Origin(xyz=(0.0, 0.149, 0.232)),
        material=smoky_poly,
        name="rear_handle",
    )

    blade = model.part("blade")
    blade.visual(
        Cylinder(radius=0.022, length=0.024),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=blade_steel,
        name="hub",
    )
    blade.visual(
        Cylinder(radius=0.008, length=0.070),
        origin=Origin(xyz=(0.0, 0.0, -0.035)),
        material=blade_steel,
        name="drive_shaft",
    )
    for i in range(6):
        angle = i * math.pi / 3.0
        blade.visual(
            Box((0.066, 0.017, 0.0036)),
            origin=Origin(
                xyz=(0.041 * math.cos(angle), 0.041 * math.sin(angle), 0.002 * (-1) ** i),
                rpy=(0.30 * (-1) ** i, 0.0, angle),
            ),
            material=blade_steel,
            name=f"blade_{i}",
        )

    fill_cap = model.part("fill_cap")
    fill_cap.visual(
        mesh_from_cadquery(_fill_cap(), "fill_cap_body", tolerance=0.001),
        material=matte_black,
        name="cap_body",
    )
    fill_cap.visual(
        Box((0.040, 0.006, 0.003)),
        origin=Origin(xyz=(0.042, 0.0, 0.0365)),
        material=red_mark,
        name="cap_index_mark",
    )

    speed_dial = model.part("speed_dial")
    speed_dial.visual(
        Cylinder(radius=0.032, length=0.018),
        origin=Origin(xyz=(0.0, -0.009, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=brushed_steel,
        name="dial_cap",
    )
    speed_dial.visual(
        Box((0.005, 0.0025, 0.021)),
        origin=Origin(xyz=(0.0, -0.019, 0.012)),
        material=red_mark,
        name="dial_pointer",
    )

    model.articulation(
        "base_to_jar",
        ArticulationType.REVOLUTE,
        parent=base,
        child=jar,
        origin=Origin(xyz=(0.0, 0.0, 0.183)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.0, lower=0.0, upper=0.42),
        motion_properties=MotionProperties(damping=0.25, friction=0.08),
    )
    model.articulation(
        "jar_to_blade",
        ArticulationType.CONTINUOUS,
        parent=jar,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.096)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=3.0, velocity=80.0),
        motion_properties=MotionProperties(damping=0.02, friction=0.01),
    )
    model.articulation(
        "jar_to_fill_cap",
        ArticulationType.REVOLUTE,
        parent=jar,
        child=fill_cap,
        origin=Origin(xyz=(0.0, 0.0, 0.462)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.5, velocity=2.0, lower=0.0, upper=2.0 * math.pi),
        motion_properties=MotionProperties(damping=0.12, friction=0.25),
    )
    model.articulation(
        "base_to_speed_dial",
        ArticulationType.REVOLUTE,
        parent=base,
        child=speed_dial,
        origin=Origin(xyz=(-0.070, -0.148, 0.084)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=0.8, velocity=4.0, lower=-2.25, upper=2.25),
        motion_properties=MotionProperties(damping=0.05, friction=0.18),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
