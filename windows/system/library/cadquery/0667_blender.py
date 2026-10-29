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
def _bowl_shell() -> cq.Workplane:
    """Open, hollow processor bowl with a thick rim and solid lower floor."""
    wall = cq.Workplane("XY").circle(0.165).circle(0.145).extrude(0.300).translate(
        (0.0, 0.0, 0.040)
    )
    floor = cq.Workplane("XY").circle(0.145).extrude(0.022).translate(
        (0.0, 0.0, 0.018)
    )
    rim = cq.Workplane("XY").circle(0.173).circle(0.142).extrude(0.018).translate(
        (0.0, 0.0, 0.330)
    )
    return wall.union(floor).union(rim)
def _feed_tube() -> cq.Workplane:
    """Hollow cylindrical feed tube rising from the lid."""
    return cq.Workplane("XY").circle(0.038).circle(0.027).extrude(0.105)
def _blade_swept() -> cq.Workplane:
    """Two broad, flattened cutting wings joined at the central hub."""
    left = (
        cq.Workplane("XY")
        .polyline([(0.018, -0.018), (0.126, -0.032), (0.108, 0.020), (0.020, 0.026)])
        .close()
        .extrude(0.006)
        .translate((0.0, 0.0, 0.008))
    )
    right = (
        cq.Workplane("XY")
        .polyline([(-0.018, 0.018), (-0.126, 0.032), (-0.108, -0.020), (-0.020, -0.026)])
        .close()
        .extrude(0.006)
        .translate((0.0, 0.0, 0.018))
    )
    bridge = cq.Workplane("XY").circle(0.034).extrude(0.030)
    return bridge.union(left).union(right)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="food_processor")

    warm_white = model.material("warm_white_plastic", rgba=(0.86, 0.84, 0.78, 1.0))
    dark = model.material("charcoal_trim", rgba=(0.07, 0.08, 0.09, 1.0))
    rubber = model.material("matte_black_rubber", rgba=(0.015, 0.014, 0.013, 1.0))
    glass = model.material("clear_smoky_bowl", rgba=(0.62, 0.82, 0.95, 0.34))
    lid_plastic = model.material("smoky_lid", rgba=(0.55, 0.72, 0.86, 0.42))
    steel = model.material("brushed_steel", rgba=(0.72, 0.74, 0.72, 1.0))
    accent = model.material("red_lock_marks", rgba=(0.80, 0.08, 0.05, 1.0))

    bowl_mesh = mesh_from_cadquery(_bowl_shell(), "hollow_processor_bowl", tolerance=0.001)
    feed_tube_mesh = mesh_from_cadquery(_feed_tube(), "hollow_feed_tube", tolerance=0.001)
    blade_mesh = mesh_from_cadquery(_blade_swept(), "processor_blade_swept", tolerance=0.0005)

    base = model.part("base")
    base.visual(
        Box((0.58, 0.38, 0.140)),
        origin=Origin(xyz=(0.0, 0.0, 0.070)),
        material=warm_white,
        name="base_body",
    )
    base.visual(
        Box((0.52, 0.30, 0.020)),
        origin=Origin(xyz=(0.0, 0.010, 0.150)),
        material=warm_white,
        name="raised_top",
    )
    base.visual(
        Cylinder(radius=0.205, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.156)),
        material=dark,
        name="socket_plate",
    )
    base.visual(
        Cylinder(radius=0.126, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.158)),
        material=dark,
        name="drive_well",
    )
    base.visual(
        Box((0.30, 0.018, 0.070)),
        origin=Origin(xyz=(0.0, -0.199, 0.078)),
        material=dark,
        name="front_panel",
    )
    base.visual(
        Cylinder(radius=0.052, length=0.010),
        origin=Origin(xyz=(0.0, -0.205, 0.078), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=dark,
        name="dial_collar",
    )
    for x in (-0.210, 0.210):
        for y in (-0.130, 0.130):
            base.visual(
                Box((0.080, 0.055, 0.014)),
                origin=Origin(xyz=(x, y, -0.007)),
                material=rubber,
                name=f"rubber_foot_{x}_{y}",
            )

    bowl = model.part("bowl")
    bowl.visual(bowl_mesh, origin=Origin(), material=glass, name="bowl_shell")
    bowl.visual(
        Cylinder(radius=0.184, length=0.024),
        origin=Origin(xyz=(0.0, 0.0, 0.012)),
        material=dark,
        name="bayonet_collar",
    )
    for i, angle in enumerate((0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)):
        bowl.visual(
            Box((0.072, 0.024, 0.014)),
            origin=Origin(
                xyz=(0.187 * math.cos(angle), 0.187 * math.sin(angle), 0.029),
                rpy=(0.0, 0.0, angle + math.pi / 2.0),
            ),
            material=dark,
            name=f"bayonet_tab_{i}",
        )
    bowl.visual(
        Box((0.028, 0.058, 0.205)),
        origin=Origin(xyz=(0.232, 0.0, 0.205)),
        material=glass,
        name="handle_grip",
    )
    bowl.visual(
        Box((0.082, 0.052, 0.030)),
        origin=Origin(xyz=(0.197, 0.0, 0.122)),
        material=glass,
        name="lower_handle_root",
    )
    bowl.visual(
        Box((0.082, 0.052, 0.030)),
        origin=Origin(xyz=(0.197, 0.0, 0.290)),
        material=glass,
        name="upper_handle_root",
    )
    bowl.visual(
        Cylinder(radius=0.030, length=0.036),
        origin=Origin(xyz=(0.0, 0.0, 0.058)),
        material=dark,
        name="center_boss",
    )
    for z in (0.120, 0.170, 0.220, 0.270):
        bowl.visual(
            Box((0.010, 0.045, 0.004)),
            origin=Origin(xyz=(-0.162, -0.018, z)),
            material=dark,
            name=f"measure_mark_{int(z * 1000)}",
        )
    for side, x in (("hinge_a", -0.070), ("hinge_b", 0.070)):
        bowl.visual(
            Box((0.030, 0.042, 0.024)),
            origin=Origin(xyz=(x, 0.184, 0.329)),
            material=dark,
            name=f"{side}_base",
        )
        bowl.visual(
            Box((0.030, 0.022, 0.052)),
            origin=Origin(xyz=(x, 0.190, 0.360)),
            material=dark,
            name=f"{side}_cheek",
        )

    lid = model.part("lid")
    lid.visual(
        Cylinder(radius=0.168, length=0.018),
        origin=Origin(xyz=(0.0, -0.165, 0.009)),
        material=lid_plastic,
        name="lid_disc",
    )
    lid.visual(
        feed_tube_mesh,
        origin=Origin(xyz=(0.060, -0.165, 0.018)),
        material=lid_plastic,
        name="feed_tube",
    )
    lid.visual(
        Cylinder(radius=0.009, length=0.086),
        origin=Origin(xyz=(0.0, 0.008, 0.010), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark,
        name="hinge_barrel",
    )
    lid.visual(
        Box((0.050, 0.018, 0.020)),
        origin=Origin(xyz=(0.0, -0.322, 0.014)),
        material=dark,
        name="front_latch",
    )

    blade = model.part("blade")
    blade.visual(blade_mesh, origin=Origin(), material=steel, name="blade_swept")
    blade.visual(
        Cylinder(radius=0.040, length=0.052),
        origin=Origin(xyz=(0.0, 0.0, 0.026)),
        material=dark,
        name="blade_hub",
    )
    blade.visual(
        Cylinder(radius=0.020, length=0.038),
        origin=Origin(xyz=(0.0, 0.0, 0.071)),
        material=dark,
        name="hub_cap",
    )

    dial = model.part("dial")
    dial.visual(
        Cylinder(radius=0.041, length=0.026),
        origin=Origin(xyz=(0.0, -0.013, 0.0), rpy=(-math.pi / 2.0, 0.0, 0.0)),
        material=warm_white,
        name="dial_cap",
    )
    dial.visual(
        Box((0.007, 0.004, 0.035)),
        origin=Origin(xyz=(0.0, -0.028, 0.010)),
        material=accent,
        name="dial_pointer",
    )

    model.articulation(
        "bowl_bayonet",
        ArticulationType.REVOLUTE,
        parent=base,
        child=bowl,
        origin=Origin(xyz=(0.0, 0.0, 0.162)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=15.0, velocity=1.0, lower=0.0, upper=0.45),
    )
    model.articulation(
        "lid_hinge",
        ArticulationType.REVOLUTE,
        parent=bowl,
        child=lid,
        origin=Origin(xyz=(0.0, 0.165, 0.348)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=0.0, upper=1.75),
    )
    model.articulation(
        "blade_spin",
        ArticulationType.CONTINUOUS,
        parent=bowl,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.076)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=3.0, velocity=30.0),
    )
    model.articulation(
        "dial_turn",
        ArticulationType.REVOLUTE,
        parent=base,
        child=dial,
        origin=Origin(xyz=(0.0, -0.210, 0.078)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=4.0, lower=-2.2, upper=2.2),
    )
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
