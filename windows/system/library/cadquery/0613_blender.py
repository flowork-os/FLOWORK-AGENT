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
def _annular_cylinder(outer_radius: float, inner_radius: float, height: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(outer_radius).circle(inner_radius).extrude(height)
def _cup_shell() -> cq.Workplane:
    """Open stainless chamber cup with a thick bottom, rolled rim, and bayonet lugs."""
    inner_radius = 0.072
    outer_radius = 0.080
    bottom = cq.Workplane("XY").circle(inner_radius).extrude(0.030)
    wall = _annular_cylinder(outer_radius, inner_radius, 0.232).translate((0.0, 0.0, 0.020))
    rolled_rim = _annular_cylinder(0.084, 0.070, 0.010).translate((0.0, 0.0, 0.250))
    lower_flange = _annular_cylinder(0.088, 0.056, 0.014)

    cup = bottom.union(wall).union(rolled_rim).union(lower_flange)
    for angle_deg in (0.0, 120.0, 240.0):
        lug = (
            cq.Workplane("XY")
            .box(0.018, 0.040, 0.010)
            .translate((0.092, 0.0, 0.012))
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_deg)
        )
        cup = cup.union(lug)
    return cup
def _rounded_housing() -> cq.Workplane:
    return cq.Workplane("XY").box(0.280, 0.320, 0.550).edges("|Z").fillet(0.018)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="laboratory_homogenizer_blender")

    powder_coat = model.material("warm_gray_powder_coat", rgba=(0.72, 0.74, 0.73, 1.0))
    dark_panel = model.material("dark_control_panel", rgba=(0.015, 0.018, 0.022, 1.0))
    stainless = model.material("brushed_stainless", rgba=(0.68, 0.70, 0.69, 1.0))
    black_rubber = model.material("black_rubber", rgba=(0.005, 0.005, 0.006, 1.0))
    clear_lid = model.material("clear_polycarbonate", rgba=(0.58, 0.82, 0.95, 0.46))
    yellow_mark = model.material("yellow_lock_mark", rgba=(1.0, 0.76, 0.08, 1.0))
    red_indicator = model.material("red_indicator", rgba=(0.80, 0.04, 0.03, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_rounded_housing(), "rounded_housing", tolerance=0.0012),
        origin=Origin(xyz=(0.0, 0.0, 0.275)),
        material=powder_coat,
        name="housing_shell",
    )
    housing.visual(
        Box((0.205, 0.006, 0.255)),
        origin=Origin(xyz=(0.0, -0.163, 0.330)),
        material=dark_panel,
        name="control_panel",
    )
    housing.visual(
        mesh_from_cadquery(_annular_cylinder(0.105, 0.080, 0.015), "bayonet_socket"),
        origin=Origin(xyz=(0.0, -0.020, 0.550)),
        material=stainless,
        name="bayonet_socket",
    )
    for idx, angle in enumerate((0.0, 120.0, 240.0)):
        radius = 0.094
        x = radius * math.cos(math.radians(angle))
        y = -0.020 + radius * math.sin(math.radians(angle))
        housing.visual(
            Box((0.014, 0.050, 0.001)),
            origin=Origin(xyz=(x, y, 0.5645), rpy=(0.0, 0.0, math.radians(angle))),
            material=dark_panel,
            name=f"bayonet_slot_{idx}",
        )
    housing.visual(
        Cylinder(radius=0.018, length=0.020),
        origin=Origin(xyz=(0.0, -0.020, 0.555)),
        material=stainless,
        name="drive_coupler",
    )
    housing.visual(
        Box((0.004, 0.028, 0.018)),
        origin=Origin(xyz=(0.085, -0.168, 0.444)),
        material=yellow_mark,
        name="lock_tick",
    )

    chamber_cup = model.part("chamber_cup")
    chamber_cup.visual(
        mesh_from_cadquery(_cup_shell(), "stainless_chamber_cup", tolerance=0.0008),
        material=stainless,
        name="cup_shell",
    )
    chamber_cup.visual(
        Box((0.020, 0.008, 0.045)),
        origin=Origin(xyz=(0.0, -0.083, 0.125)),
        material=black_rubber,
        name="grip_strip",
    )

    lid_hinge = model.part("lid_hinge")
    lid_hinge.visual(
        Box((0.150, 0.012, 0.018)),
        origin=Origin(xyz=(0.0, 0.089, 0.248)),
        material=stainless,
        name="hinge_bridge",
    )
    lid_hinge.visual(
        Box((0.025, 0.012, 0.034)),
        origin=Origin(xyz=(-0.060, 0.089, 0.267)),
        material=stainless,
        name="hinge_ear_0",
    )
    lid_hinge.visual(
        Box((0.025, 0.012, 0.034)),
        origin=Origin(xyz=(0.060, 0.089, 0.267)),
        material=stainless,
        name="hinge_ear_1",
    )

    chamber_lid = model.part("chamber_lid")
    chamber_lid.visual(
        Cylinder(radius=0.080, length=0.012),
        origin=Origin(xyz=(0.0, -0.088, -0.002)),
        material=clear_lid,
        name="lid_disk",
    )
    chamber_lid.visual(
        mesh_from_cadquery(_annular_cylinder(0.080, 0.066, 0.004), "lid_gasket"),
        origin=Origin(xyz=(0.0, -0.088, -0.008)),
        material=black_rubber,
        name="lid_gasket",
    )
    chamber_lid.visual(
        Cylinder(radius=0.008, length=0.070),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=stainless,
        name="hinge_barrel",
    )
    chamber_lid.visual(
        Box((0.070, 0.034, 0.010)),
        origin=Origin(xyz=(0.0, -0.022, -0.001)),
        material=clear_lid,
        name="hinge_leaf",
    )
    chamber_lid.visual(
        Cylinder(radius=0.018, length=0.016),
        origin=Origin(xyz=(0.0, -0.088, 0.011)),
        material=black_rubber,
        name="lid_knob",
    )

    blade_drive = model.part("blade_drive")
    blade_drive.visual(
        Cylinder(radius=0.005, length=0.044),
        material=stainless,
        name="drive_shaft",
    )
    blade_drive.visual(
        Cylinder(radius=0.016, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=stainless,
        name="blade_hub",
    )
    for idx, yaw in enumerate((0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0)):
        blade_drive.visual(
            Box((0.052, 0.014, 0.004)),
            origin=Origin(xyz=(0.033 * math.cos(yaw), 0.033 * math.sin(yaw), 0.012), rpy=(0.0, 0.0, yaw)),
            material=stainless,
            name=f"blade_leaf_{idx}",
        )

    speed_dial = model.part("speed_dial")
    speed_dial.visual(
        Cylinder(radius=0.029, length=0.018),
        origin=Origin(xyz=(0.0, 0.0, 0.009)),
        material=black_rubber,
        name="dial_cap",
    )
    speed_dial.visual(
        Box((0.004, 0.023, 0.002)),
        origin=Origin(xyz=(0.0, 0.020, 0.019)),
        material=yellow_mark,
        name="dial_pointer",
    )

    status_light = model.part("status_light")
    status_light.visual(
        Cylinder(radius=0.014, length=0.008),
        origin=Origin(xyz=(0.0, 0.0, 0.004)),
        material=red_indicator,
        name="indicator_lens",
    )

    cup_twist = model.articulation(
        "housing_to_chamber_cup",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=chamber_cup,
        origin=Origin(xyz=(0.0, -0.020, 0.565)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.2, lower=0.0, upper=0.42),
    )
    model.articulation(
        "cup_to_lid_hinge",
        ArticulationType.FIXED,
        parent=chamber_cup,
        child=lid_hinge,
    )
    model.articulation(
        "hinge_to_lid",
        ArticulationType.REVOLUTE,
        parent=lid_hinge,
        child=chamber_lid,
        origin=Origin(xyz=(0.0, 0.088, 0.268)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=1.4, lower=0.0, upper=1.25),
    )
    model.articulation(
        "cup_to_blade",
        ArticulationType.CONTINUOUS,
        parent=chamber_cup,
        child=blade_drive,
        origin=Origin(xyz=(0.0, 0.0, 0.052)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=2.0, velocity=80.0),
    )
    model.articulation(
        "housing_to_speed_dial",
        ArticulationType.REVOLUTE,
        parent=housing,
        child=speed_dial,
        origin=Origin(xyz=(0.0, -0.166, 0.325), rpy=(math.pi / 2.0, 0.0, 0.0)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.25, velocity=4.0, lower=0.0, upper=4.7),
    )
    model.articulation(
        "housing_to_status_light",
        ArticulationType.FIXED,
        parent=housing,
        child=status_light,
        origin=Origin(xyz=(-0.065, -0.166, 0.405), rpy=(math.pi / 2.0, 0.0, 0.0)),
    )

    cup_twist.meta["description"] = "Limited revolute bayonet twist lock for the removable stainless chamber cup."
    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
