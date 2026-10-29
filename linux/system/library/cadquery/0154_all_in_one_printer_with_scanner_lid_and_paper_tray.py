# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, all_in_one_printer_with_scanner_lid_and_paper_tray, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: all_in_one_printer_with_scanner_lid_and_paper_tray

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
BODY_DEPTH = 0.49
BODY_WIDTH = 0.47
SCANNER_HINGE_X = -0.18
SCANNER_HINGE_Z = 0.620
CASSETTE_ENTRY_X = 0.219
PANEL_PIVOT_X = 0.284
PANEL_PIVOT_Y = 0.080
PANEL_PIVOT_Z = 0.384
def _box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    sx, sy, sz = size
    cx, cy, cz = center
    return cq.Workplane("XY").box(sx, sy, sz).translate((cx, cy, cz))
def _body_shape() -> cq.Workplane:
    lower = _box((BODY_DEPTH, BODY_WIDTH, 0.41), (0.0, 0.0, 0.205))
    upper = _box((0.43, 0.45, 0.21), (-0.02, 0.0, 0.515))
    panel_pedestal = _box((0.085, 0.19, 0.075), (0.202, 0.0, 0.3825))
    panel_chin = _box((0.055, 0.20, 0.040), (0.220, 0.0, 0.315))
    panel_pivot_rail = _box((0.040, 0.176, 0.022), (0.252, 0.078, 0.396))
    body = lower.union(upper).union(panel_pedestal).union(panel_chin).union(panel_pivot_rail)

    cassette_cavity = _box((0.38, 0.392, 0.128), (0.055, 0.0, 0.089))
    output_cavity = _box((0.22, 0.320, 0.052), (0.135, 0.0, 0.262))
    scanner_well = _box((0.318, 0.316, 0.034), (-0.020, 0.0, 0.603))
    service_cavity = _box((0.212, 0.110, 0.192), (-0.005, 0.180, 0.292))
    internal_channel = _box((0.260, 0.180, 0.080), (0.055, 0.075, 0.252))
    body = body.cut(cassette_cavity)
    body = body.cut(output_cavity)
    body = body.cut(scanner_well)
    body = body.cut(service_cavity)
    body = body.cut(internal_channel)

    output_lip = _box((0.048, 0.320, 0.006), (0.226, 0.0, 0.232))
    return body.union(output_lip)
def _flatbed_lid_shape() -> cq.Workplane:
    lid_outer = _box((0.346, 0.366, 0.028), (0.173, 0.0, 0.014))
    lid_inner = _box((0.304, 0.324, 0.024), (0.173, 0.0, 0.012))
    lid_shell = lid_outer.cut(lid_inner)

    adf_base_outer = _box((0.182, 0.342, 0.060), (0.091, 0.0, 0.058))
    adf_tunnel = _box((0.142, 0.298, 0.036), (0.102, 0.0, 0.048))
    adf_front_slot = _box((0.060, 0.286, 0.020), (0.018, 0.0, 0.044))
    adf_base = adf_base_outer.cut(adf_tunnel).cut(adf_front_slot)

    front_grip = _box((0.015, 0.110, 0.010), (0.339, 0.0, 0.010))
    hinge_bar = (
        cq.Workplane("YZ")
        .center(0.0, 0.012)
        .circle(0.008)
        .extrude(0.330)
        .translate((0.004, -0.165, 0.0))
    )
    return lid_shell.union(adf_base).union(front_grip).union(hinge_bar)
def _adf_lid_shape() -> cq.Workplane:
    cover_outer = _box((0.172, 0.344, 0.021), (0.086, 0.0, 0.0105))
    cover_inner = _box((0.146, 0.312, 0.017), (0.090, 0.0, 0.0085))
    cover_shell = cover_outer.cut(cover_inner)
    front_lip = _box((0.018, 0.210, 0.010), (0.165, 0.0, 0.010))
    hinge_bar = (
        cq.Workplane("YZ")
        .center(0.0, 0.010)
        .circle(0.006)
        .extrude(0.330)
        .translate((0.003, -0.165, 0.0))
    )
    return cover_shell.union(front_lip).union(hinge_bar)
def _service_door_shape() -> cq.Workplane:
    outer = _box((0.206, 0.010, 0.194), (0.103, 0.005, 0.097))
    inner = _box((0.170, 0.008, 0.152), (0.112, 0.004, 0.098))
    latch = _box((0.016, 0.006, 0.034), (0.182, 0.011, 0.100))
    return outer.cut(inner).union(latch)
def _control_panel_shape() -> cq.Workplane:
    housing = _box((0.032, 0.168, 0.088), (0.016, 0.0, 0.044))

    screen_recess = _box((0.008, 0.094, 0.050), (0.028, -0.018, 0.056))
    housing = housing.cut(screen_recess)

    for y in (-0.048, -0.022, 0.004, 0.030):
        pocket = _box((0.004, 0.019, 0.012), (0.030, y, 0.018))
        housing = housing.cut(pocket)

    dial_hole = (
        cq.Workplane("YZ")
        .center(0.058, 0.026)
        .circle(0.009)
        .extrude(0.012)
        .translate((0.020, 0.0, 0.0))
    )
    left_trunnion = (
        cq.Workplane("XZ")
        .center(0.000, 0.012)
        .circle(0.008)
        .extrude(0.010)
        .translate((0.0, -0.079, 0.0))
    )
    right_trunnion = (
        cq.Workplane("XZ")
        .center(0.000, 0.012)
        .circle(0.008)
        .extrude(0.010)
        .translate((0.0, 0.069, 0.0))
    )
    pivot_spine = _box((0.004, 0.150, 0.010), (-0.002, -0.005, 0.012))
    return housing.cut(dial_hole).union(left_trunnion).union(right_trunnion).union(pivot_spine)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="office_printer")

    body_color = model.material("body_color", rgba=(0.81, 0.83, 0.85, 1.0))
    trim_color = model.material("trim_color", rgba=(0.38, 0.40, 0.44, 1.0))
    dark_trim = model.material("dark_trim", rgba=(0.18, 0.19, 0.21, 1.0))
    glass_color = model.material("glass_color", rgba=(0.10, 0.15, 0.18, 0.55))
    button_color = model.material("button_color", rgba=(0.30, 0.32, 0.35, 1.0))

    body = model.part("body")
    body.visual(
        mesh_from_cadquery(_body_shape(), "printer_body"),
        material=body_color,
        name="body_shell",
    )

    flatbed_lid = model.part("flatbed_lid")
    flatbed_lid.visual(
        mesh_from_cadquery(_flatbed_lid_shape(), "flatbed_lid"),
        material=body_color,
        name="lid_shell",
    )

    adf_lid = model.part("adf_lid")
    adf_lid.visual(
        mesh_from_cadquery(_adf_lid_shape(), "adf_lid"),
        material=trim_color,
        name="adf_cover",
    )

    cassette = model.part("cassette")
    cassette.visual(
        Box((0.320, 0.374, 0.006)),
        origin=Origin(xyz=(-0.160, 0.0, 0.003)),
        material=body_color,
        name="cassette_floor",
    )
    cassette.visual(
        Box((0.320, 0.008, 0.072)),
        origin=Origin(xyz=(-0.160, -0.183, 0.039)),
        material=body_color,
        name="cassette_wall_0",
    )
    cassette.visual(
        Box((0.320, 0.008, 0.072)),
        origin=Origin(xyz=(-0.160, 0.183, 0.039)),
        material=body_color,
        name="cassette_wall_1",
    )
    cassette.visual(
        Box((0.008, 0.374, 0.072)),
        origin=Origin(xyz=(-0.316, 0.0, 0.039)),
        material=body_color,
        name="cassette_back",
    )
    cassette.visual(
        Box((0.240, 0.010, 0.016)),
        origin=Origin(xyz=(-0.160, -0.191, 0.024)),
        material=body_color,
        name="cassette_runner_0",
    )
    cassette.visual(
        Box((0.240, 0.010, 0.016)),
        origin=Origin(xyz=(-0.160, 0.191, 0.024)),
        material=body_color,
        name="cassette_runner_1",
    )
    cassette.visual(
        Box((0.050, 0.300, 0.028)),
        origin=Origin(xyz=(0.007, 0.0, 0.017)),
        material=body_color,
        name="cassette_front",
    )
    cassette.visual(
        Box((0.012, 0.388, 0.108)),
        origin=Origin(xyz=(0.038, 0.0, 0.054)),
        material=body_color,
        name="cassette_fascia",
    )

    service_door = model.part("service_door")
    service_door.visual(
        mesh_from_cadquery(_service_door_shape(), "service_door"),
        material=trim_color,
        name="door_shell",
    )

    control_panel = model.part("control_panel")
    control_panel.visual(
        mesh_from_cadquery(_control_panel_shape(), "control_panel"),
        material=trim_color,
        name="panel_shell",
    )
    control_panel.visual(
        Box((0.002, 0.090, 0.046)),
        origin=Origin(xyz=(0.025, -0.018, 0.056)),
        material=glass_color,
        name="touchscreen",
    )

    selector_dial = model.part("selector_dial")
    selector_dial.visual(
        Cylinder(radius=0.012, length=0.016),
        origin=Origin(xyz=(0.010, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_trim,
        name="dial_knob",
    )
    selector_dial.visual(
        Cylinder(radius=0.008, length=0.012),
        origin=Origin(xyz=(0.001, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=dark_trim,
        name="dial_shaft",
    )

    key_positions = (-0.048, -0.022, 0.004, 0.030)
    for index, y in enumerate(key_positions):
        key = model.part(f"key_{index}")
        key.visual(
            Box((0.003, 0.017, 0.010)),
            origin=Origin(xyz=(0.0015, 0.0, 0.0)),
            material=button_color,
            name="key_cap",
        )
        key.visual(
            Box((0.004, 0.009, 0.006)),
            origin=Origin(xyz=(-0.001, 0.0, 0.0)),
            material=button_color,
            name="key_stem",
        )
        model.articulation(
            f"control_panel_to_key_{index}",
            ArticulationType.PRISMATIC,
            parent=control_panel,
            child=key,
            origin=Origin(xyz=(0.030, y, 0.018)),
            axis=(-1.0, 0.0, 0.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.05,
                lower=0.0,
                upper=0.0012,
            ),
        )

    model.articulation(
        "body_to_flatbed_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=flatbed_lid,
        origin=Origin(xyz=(SCANNER_HINGE_X, 0.0, SCANNER_HINGE_Z)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=18.0,
            velocity=1.2,
            lower=0.0,
            upper=1.28,
        ),
    )
    model.articulation(
        "flatbed_lid_to_adf_lid",
        ArticulationType.REVOLUTE,
        parent=flatbed_lid,
        child=adf_lid,
        origin=Origin(xyz=(0.010, 0.0, 0.088)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.2,
            lower=0.0,
            upper=1.22,
        ),
    )
    model.articulation(
        "body_to_cassette",
        ArticulationType.PRISMATIC,
        parent=body,
        child=cassette,
        origin=Origin(xyz=(CASSETTE_ENTRY_X, 0.0, 0.033)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=45.0,
            velocity=0.30,
            lower=0.0,
            upper=0.19,
        ),
    )
    model.articulation(
        "body_to_service_door",
        ArticulationType.REVOLUTE,
        parent=body,
        child=service_door,
        origin=Origin(xyz=(-0.108, 0.235, 0.195)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=6.0,
            velocity=1.8,
            lower=0.0,
            upper=1.55,
        ),
    )
    model.articulation(
        "body_to_control_panel",
        ArticulationType.REVOLUTE,
        parent=body,
        child=control_panel,
        origin=Origin(
            xyz=(PANEL_PIVOT_X, PANEL_PIVOT_Y, PANEL_PIVOT_Z),
            rpy=(0.0, -0.35, 0.0),
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=5.0,
            velocity=1.6,
            lower=0.0,
            upper=0.45,
        ),
    )
    model.articulation(
        "control_panel_to_selector_dial",
        ArticulationType.CONTINUOUS,
        parent=control_panel,
        child=selector_dial,
        origin=Origin(xyz=(0.031, 0.058, 0.026)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=0.3, velocity=7.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
