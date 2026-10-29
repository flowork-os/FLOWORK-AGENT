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
CHASSIS_W = 0.380
CHASSIS_D = 0.360
CHASSIS_H = 0.270
LID_W = 0.304
LID_D = 0.236
LID_T = 0.020
TRAY_W = 0.286
TRAY_D = 0.140
TRAY_H = 0.032
DOOR_W = 0.266
DOOR_H = 0.056
DOOR_T = 0.006
PANEL_W = 0.182
PANEL_H = 0.068
PANEL_T = 0.008
def _cq_box(size: tuple[float, float, float], center: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(center)
def _build_chassis_shell() -> cq.Workplane:
    shell = cq.Workplane("XY").box(CHASSIS_W, CHASSIS_D, CHASSIS_H).translate((0.0, 0.0, CHASSIS_H / 2.0))
    shell = shell.edges("|Z").fillet(0.012)
    shell = shell.edges(">Z").fillet(0.006)

    scanner_pocket = _cq_box((0.286, 0.214, 0.018), (0.0, 0.010, CHASSIS_H - 0.009))
    tray_tunnel = _cq_box((0.324, 0.252, 0.056), (0.0, -0.054, 0.043))
    output_cavity = _cq_box((0.274, 0.036, 0.056), (0.0, -(CHASSIS_D / 2.0) + 0.018, 0.118))
    control_recess = _cq_box((0.182, 0.010, 0.068), (0.0, -(CHASSIS_D / 2.0) + 0.005, 0.192))
    bottom_relief = _cq_box((0.220, 0.140, 0.010), (0.0, 0.006, 0.005))

    shell = shell.cut(scanner_pocket)
    shell = shell.cut(tray_tunnel)
    shell = shell.cut(output_cavity)
    shell = shell.cut(control_recess)
    shell = shell.cut(bottom_relief)

    return shell
def _build_lid_shell() -> cq.Workplane:
    lid = _cq_box((LID_W, LID_D, LID_T), (0.0, -LID_D / 2.0, LID_T / 2.0))
    lid = lid.edges("|X and >Z").fillet(0.004)

    inner_pocket = _cq_box((LID_W - 0.016, LID_D - 0.020, LID_T - 0.003), (0.0, -LID_D / 2.0, (LID_T - 0.003) / 2.0))
    cable_notch = _cq_box((0.070, 0.014, 0.010), (0.0, -0.010, 0.005))

    lid = lid.cut(inner_pocket)
    lid = lid.cut(cable_notch)
    return lid
def _build_tray_shell() -> cq.Workplane:
    tray = _cq_box((TRAY_W, TRAY_D, TRAY_H), (0.0, (TRAY_D / 2.0) - 0.004, TRAY_H / 2.0))
    cavity = _cq_box(
        (TRAY_W - 0.014, TRAY_D - 0.022, TRAY_H - 0.004),
        (0.0, 0.074, (TRAY_H - 0.004) / 2.0 + 0.004),
    )
    finger_scoop = (
        cq.Workplane("XZ")
        .center(0.0, 0.018)
        .circle(0.036)
        .extrude(0.012)
        .translate((0.0, -0.012, 0.0))
    )

    tray = tray.cut(cavity)
    tray = tray.cut(finger_scoop)
    tray = tray.union(_cq_box((0.010, 0.094, 0.003), (-(TRAY_W / 2.0) + 0.015, 0.060, -0.0015)))
    tray = tray.union(_cq_box((0.010, 0.094, 0.003), ((TRAY_W / 2.0) - 0.015, 0.060, -0.0015)))
    return tray
def _build_output_door() -> cq.Workplane:
    panel = _cq_box((DOOR_W, DOOR_T, DOOR_H), (0.0, -DOOR_T / 2.0, DOOR_H / 2.0))
    lip = _cq_box((0.110, 0.010, 0.010), (0.0, -0.003, DOOR_H - 0.010))
    inner_relief = _cq_box((DOOR_W - 0.018, 0.003, DOOR_H - 0.016), (0.0, -DOOR_T + 0.0015, DOOR_H / 2.0 + 0.001))
    return panel.union(lip).cut(inner_relief)
def _build_control_panel() -> cq.Workplane:
    panel = cq.Workplane("XY").box(PANEL_W, PANEL_T, PANEL_H)
    button_slot = lambda x: _cq_box((0.016, PANEL_T + 0.002, 0.010), (x, 0.0, -0.010))
    panel = panel.cut(button_slot(0.028))
    panel = panel.cut(button_slot(0.054))
    panel = panel.cut(button_slot(0.080))
    return panel
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="compact_all_in_one_printer")

    body_finish = model.material("body_graphite", rgba=(0.21, 0.22, 0.24, 1.0))
    lid_finish = model.material("lid_dark", rgba=(0.30, 0.31, 0.33, 1.0))
    tray_finish = model.material("tray_black", rgba=(0.16, 0.17, 0.18, 1.0))
    door_finish = model.material("door_smoke", rgba=(0.24, 0.25, 0.27, 1.0))
    panel_finish = model.material("panel_black", rgba=(0.10, 0.11, 0.12, 1.0))
    knob_finish = model.material("knob_black", rgba=(0.08, 0.08, 0.09, 1.0))
    button_finish = model.material("button_grey", rgba=(0.62, 0.64, 0.67, 1.0))
    glass_finish = model.material("scanner_glass", rgba=(0.43, 0.56, 0.61, 0.35))

    chassis = model.part("chassis")
    chassis.visual(
        mesh_from_cadquery(_build_chassis_shell(), "printer_chassis"),
        material=body_finish,
        name="shell",
    )

    lid = model.part("lid")
    lid.visual(
        mesh_from_cadquery(_build_lid_shell(), "printer_lid"),
        material=lid_finish,
        name="shell",
    )

    tray = model.part("tray")
    tray.visual(
        mesh_from_cadquery(_build_tray_shell(), "printer_tray"),
        material=tray_finish,
        name="drawer",
    )

    output_door = model.part("output_door")
    output_door.visual(
        mesh_from_cadquery(_build_output_door(), "printer_output_door"),
        material=door_finish,
        name="panel",
    )

    control_panel = model.part("control_panel")
    control_panel.visual(
        mesh_from_cadquery(_build_control_panel(), "printer_control_panel"),
        material=panel_finish,
        name="panel",
    )

    scanner_bed = model.part("scanner_bed")
    scanner_bed.visual(
        Box((0.272, 0.200, 0.003)),
        origin=Origin(xyz=(0.0, 0.0, 0.0015)),
        material=glass_finish,
        name="glass",
    )

    selector_knob = model.part("selector_knob")
    selector_knob.visual(
        Cylinder(radius=0.017, length=0.008),
        origin=Origin(xyz=(0.0, -0.008, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_finish,
        name="skirt",
    )
    selector_knob.visual(
        Cylinder(radius=0.013, length=0.012),
        origin=Origin(xyz=(0.0, -0.013, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=knob_finish,
        name="cap",
    )
    selector_knob.visual(
        Box((0.003, 0.0015, 0.010)),
        origin=Origin(xyz=(0.010, -0.019, 0.0)),
        material=button_finish,
        name="pointer",
    )

    for index, local_x in enumerate((0.028, 0.054, 0.080)):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.016, 0.004, 0.010)),
            origin=Origin(xyz=(0.0, -0.002, 0.0)),
            material=button_finish,
            name="cap",
        )

    model.articulation(
        "lid_hinge",
        ArticulationType.REVOLUTE,
        parent=chassis,
        child=lid,
        origin=Origin(xyz=(0.0, 0.128, CHASSIS_H)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=10.0, velocity=1.6, lower=0.0, upper=1.30),
    )
    model.articulation(
        "tray_slide",
        ArticulationType.PRISMATIC,
        parent=chassis,
        child=tray,
        origin=Origin(xyz=(0.0, -(CHASSIS_D / 2.0), 0.018)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=30.0, velocity=0.30, lower=0.0, upper=0.108),
    )
    model.articulation(
        "output_door_hinge",
        ArticulationType.REVOLUTE,
        parent=chassis,
        child=output_door,
        origin=Origin(xyz=(0.0, -(CHASSIS_D / 2.0), 0.090)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.0, lower=0.0, upper=1.45),
    )
    model.articulation(
        "chassis_to_control_panel",
        ArticulationType.FIXED,
        parent=chassis,
        child=control_panel,
        origin=Origin(xyz=(0.0, -0.176, 0.192)),
    )
    model.articulation(
        "chassis_to_scanner_bed",
        ArticulationType.FIXED,
        parent=chassis,
        child=scanner_bed,
        origin=Origin(xyz=(0.0, 0.010, 0.252)),
    )
    model.articulation(
        "selector_knob_spin",
        ArticulationType.CONTINUOUS,
        parent=control_panel,
        child=selector_knob,
        origin=Origin(xyz=(-0.040, 0.0, 0.010)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=0.12, velocity=6.0),
    )
    for index, local_x in enumerate((0.028, 0.054, 0.080)):
        model.articulation(
            f"button_{index}_push",
            ArticulationType.PRISMATIC,
            parent=control_panel,
            child=model.get_part(f"button_{index}"),
            origin=Origin(xyz=(local_x, 0.0, -0.010)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=6.0, velocity=0.08, lower=0.0, upper=0.003),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
