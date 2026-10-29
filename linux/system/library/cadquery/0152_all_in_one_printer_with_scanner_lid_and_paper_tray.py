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
PRINTER_W = 0.48
PRINTER_D = 0.41
BODY_H = 0.185
SCANNER_X = -0.075
SCANNER_Y = -0.005
SCANNER_W = 0.290
SCANNER_D = 0.225
SCANNER_RECESS = 0.014
LID_W = 0.332
LID_D = 0.300
LID_H = 0.026
def _box_solid(
    width: float,
    depth: float,
    height: float,
    *,
    center_x: float = 0.0,
    center_y: float = 0.0,
    base_z: float = 0.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(width, depth, height, centered=(True, True, False))
        .translate((center_x, center_y, base_z))
    )
def _open_top_shell(
    width: float,
    depth: float,
    height: float,
    *,
    wall: float,
    bottom: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
    base_z: float = 0.0,
) -> cq.Workplane:
    outer = _box_solid(width, depth, height, center_x=center_x, center_y=center_y, base_z=base_z)
    inner = _box_solid(
        width - 2.0 * wall,
        depth - 2.0 * wall,
        height - bottom + 0.002,
        center_x=center_x,
        center_y=center_y,
        base_z=base_z + bottom,
    )
    return outer.cut(inner)
def _open_bottom_shell(
    width: float,
    depth: float,
    height: float,
    *,
    wall: float,
    top: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
    base_z: float = 0.0,
) -> cq.Workplane:
    outer = _box_solid(width, depth, height, center_x=center_x, center_y=center_y, base_z=base_z)
    inner = _box_solid(
        width - 2.0 * wall,
        depth - 2.0 * wall,
        height - top + 0.002,
        center_x=center_x,
        center_y=center_y,
        base_z=base_z - 0.001,
    )
    return outer.cut(inner)
def _make_body_shape() -> cq.Workplane:
    body = _box_solid(PRINTER_W, PRINTER_D, BODY_H)
    body = body.edges("|Z").fillet(0.010)
    body = body.edges(">Z").fillet(0.006)

    control_pod = _box_solid(0.088, 0.090, 0.020, center_x=0.184, center_y=-0.124, base_z=BODY_H)
    control_pod = control_pod.edges("|Z").fillet(0.004)
    body = body.union(control_pod)

    scanner_recess = _box_solid(
        SCANNER_W,
        SCANNER_D,
        SCANNER_RECESS + 0.002,
        center_x=SCANNER_X,
        center_y=SCANNER_Y,
        base_z=BODY_H - SCANNER_RECESS,
    )
    body = body.cut(scanner_recess)

    output_slot = _box_solid(
        0.248,
        0.070,
        0.012,
        center_x=-0.010,
        center_y=-PRINTER_D * 0.5 + 0.030,
        base_z=0.136,
    )
    body = body.cut(output_slot)

    tray_path = _box_solid(
        0.292,
        0.105,
        0.050,
        center_x=-0.010,
        center_y=-PRINTER_D * 0.5 + 0.0475,
        base_z=0.082,
    )
    body = body.cut(tray_path)

    cassette_cavity = _box_solid(
        0.398,
        0.300,
        0.062,
        center_x=0.000,
        center_y=-PRINTER_D * 0.5 + 0.145,
        base_z=0.010,
    )
    body = body.cut(cassette_cavity)

    handle_notch = _box_solid(
        0.100,
        0.022,
        0.016,
        center_x=0.000,
        center_y=-PRINTER_D * 0.5 + 0.006,
        base_z=0.030,
    )
    body = body.cut(handle_notch)
    return body
def _make_lid_shape() -> cq.Workplane:
    lid = _open_bottom_shell(LID_W, LID_D, LID_H, wall=0.010, top=0.004, center_y=-LID_D * 0.5)
    lower_adf = _open_top_shell(
        0.286,
        0.162,
        0.028,
        wall=0.006,
        bottom=0.004,
        center_x=0.000,
        center_y=-0.116,
        base_z=LID_H,
    )

    throat_front = _box_solid(
        0.210,
        0.024,
        0.013,
        center_x=0.000,
        center_y=-0.186,
        base_z=LID_H + 0.006,
    )
    throat_rear = _box_solid(
        0.188,
        0.018,
        0.010,
        center_x=0.000,
        center_y=-0.046,
        base_z=LID_H + 0.010,
    )
    lower_adf = lower_adf.cut(throat_front).cut(throat_rear)

    return lid.union(lower_adf)
def _make_adf_lid_shape() -> cq.Workplane:
    adf_lid = _open_bottom_shell(
        0.286,
        0.164,
        0.018,
        wall=0.006,
        top=0.0035,
        center_y=-0.082,
        base_z=0.000,
    )
    return adf_lid
def _make_cassette_shape() -> cq.Workplane:
    tray = _open_top_shell(0.386, 0.240, 0.056, wall=0.006, bottom=0.0035, center_y=0.120)
    fascia = _box_solid(0.404, 0.026, 0.066, center_y=0.008, base_z=0.000)
    notch = _box_solid(0.094, 0.014, 0.016, center_y=-0.002, base_z=0.028)
    return tray.union(fascia).cut(notch)
def _make_flap_shape() -> cq.Workplane:
    flap = _box_solid(0.286, 0.004, 0.056, center_y=-0.002, base_z=0.000)
    lip = _box_solid(0.248, 0.016, 0.006, center_y=-0.010, base_z=0.050)
    return flap.union(lip)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="office_all_in_one_printer")

    body_mat = model.material("body_light", rgba=(0.84, 0.85, 0.86, 1.0))
    panel_mat = model.material("panel_dark", rgba=(0.20, 0.22, 0.24, 1.0))
    trim_mat = model.material("trim_mid", rgba=(0.34, 0.37, 0.40, 1.0))
    glass_mat = model.material("glass_blue", rgba=(0.42, 0.58, 0.70, 0.35))
    button_mat = model.material("button_blue", rgba=(0.22, 0.31, 0.42, 1.0))

    body = model.part("body")
    body.visual(mesh_from_cadquery(_make_body_shape(), "printer_body"), material=body_mat, name="shell")

    scanner_glass = model.part("scanner_glass")
    scanner_glass.visual(
        Box((SCANNER_W - 0.010, SCANNER_D - 0.010, 0.003)),
        origin=Origin(xyz=(0.0, 0.0, 0.0015)),
        material=glass_mat,
        name="glass",
    )
    model.articulation(
        "body_to_scanner_glass",
        ArticulationType.FIXED,
        parent=body,
        child=scanner_glass,
        origin=Origin(xyz=(SCANNER_X, SCANNER_Y, BODY_H - SCANNER_RECESS)),
    )

    lid_mount = model.part("lid_mount")
    lid_mount.visual(
        Box((0.296, 0.018, 0.003)),
        origin=Origin(xyz=(0.0, 0.0, 0.0015)),
        material=trim_mat,
        name="hinge_pad",
    )
    model.articulation(
        "body_to_lid_mount",
        ArticulationType.FIXED,
        parent=body,
        child=lid_mount,
        origin=Origin(xyz=(SCANNER_X, SCANNER_Y + SCANNER_D * 0.5 - 0.009, BODY_H)),
    )

    lid = model.part("lid")
    lid.visual(mesh_from_cadquery(_make_lid_shape(), "printer_lid"), material=body_mat, name="lid_shell")
    lid_hinge_y = SCANNER_Y + SCANNER_D * 0.5
    lid_joint = model.articulation(
        "body_to_lid",
        ArticulationType.REVOLUTE,
        parent=body,
        child=lid,
        origin=Origin(xyz=(SCANNER_X, lid_hinge_y, BODY_H + 0.003)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=18.0, velocity=1.4, lower=0.0, upper=1.24),
    )

    adf_lid = model.part("adf_lid")
    adf_lid.visual(mesh_from_cadquery(_make_adf_lid_shape(), "printer_adf_lid"), material=panel_mat, name="adf_shell")
    adf_joint = model.articulation(
        "lid_to_adf_lid",
        ArticulationType.REVOLUTE,
        parent=lid,
        child=adf_lid,
        origin=Origin(xyz=(0.0, -0.035, LID_H + 0.028)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=0.0, upper=1.10),
    )

    cassette = model.part("cassette")
    cassette.visual(
        mesh_from_cadquery(_make_cassette_shape(), "printer_cassette"),
        material=panel_mat,
        name="tray_shell",
    )
    cassette_joint = model.articulation(
        "body_to_cassette",
        ArticulationType.PRISMATIC,
        parent=body,
        child=cassette,
        origin=Origin(xyz=(0.0, -PRINTER_D * 0.5 - 0.020, 0.012)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=70.0, velocity=0.18, lower=0.0, upper=0.130),
    )

    tray_flap = model.part("tray_flap")
    tray_flap.visual(
        mesh_from_cadquery(_make_flap_shape(), "printer_tray_flap"),
        material=trim_mat,
        name="flap_panel",
    )
    flap_joint = model.articulation(
        "body_to_tray_flap",
        ArticulationType.REVOLUTE,
        parent=body,
        child=tray_flap,
        origin=Origin(xyz=(-0.010, -PRINTER_D * 0.5, 0.078)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=4.0, velocity=2.2, lower=0.0, upper=1.28),
    )

    dial = model.part("dial")
    dial.visual(
        Cylinder(radius=0.017, length=0.012),
        origin=Origin(xyz=(0.0, 0.0, 0.006)),
        material=panel_mat,
        name="dial_knob",
    )
    model.articulation(
        "body_to_dial",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=dial,
        origin=Origin(xyz=(0.184, -0.112, BODY_H + 0.020)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.3, velocity=4.0),
    )

    button_positions = (
        (0.156, -0.149),
        (0.184, -0.149),
        (0.212, -0.149),
        (0.170, -0.085),
        (0.198, -0.085),
    )
    for index, (button_x, button_y) in enumerate(button_positions):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.018, 0.014, 0.005)),
            origin=Origin(xyz=(0.0, 0.0, 0.0025)),
            material=button_mat,
            name="button_cap",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(button_x, button_y, BODY_H + 0.020)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(effort=6.0, velocity=0.08, lower=0.0, upper=0.0025),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
