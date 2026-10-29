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
BASE_WIDTH = 0.235
BASE_DEPTH = 0.255
BASE_HEIGHT = 0.142
BASE_TOP_WIDTH = 0.168
BASE_TOP_DEPTH = 0.192
BASE_TOP_SHIFT_Y = 0.018
PANEL_WIDTH = 0.164
PANEL_HEIGHT = 0.094
PANEL_THICKNESS = 0.006
PANEL_TILT = math.radians(55.0)
PANEL_CENTER = (0.0, -0.097, 0.074)
KNOB_POS = (0.0, 0.023, 0.0)
BUTTON_Y = -0.023
BUTTON_XS = (-0.041, 0.0, 0.041)
JUG_ORIGIN = (0.0, 0.014, 0.150)
JUG_HEIGHT = 0.230
def _base_shape() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .rect(BASE_WIDTH, BASE_DEPTH)
        .workplane(offset=BASE_HEIGHT)
        .center(0.0, BASE_TOP_SHIFT_Y)
        .rect(BASE_TOP_WIDTH, BASE_TOP_DEPTH)
        .loft(combine=True)
    )

    panel_cavity = cq.Workplane("XY").transformed(
        offset=PANEL_CENTER,
        rotate=(math.degrees(PANEL_TILT), 0.0, 0.0),
    ).box(
        PANEL_WIDTH + 0.018,
        PANEL_HEIGHT + 0.010,
        0.050,
        centered=(True, True, True),
    )

    return body.cut(panel_cavity)
def _panel_shape() -> cq.Workplane:
    panel = cq.Workplane("XY").transformed(offset=(0.0, 0.0, -PANEL_THICKNESS)).box(
        PANEL_WIDTH,
        PANEL_HEIGHT,
        PANEL_THICKNESS,
        centered=(True, True, False),
    )
    left_tab = cq.Workplane("XY").transformed(offset=(-0.068, 0.0, -0.020)).box(
        0.014,
        0.026,
        0.014,
        centered=(True, True, False),
    )
    right_tab = cq.Workplane("XY").transformed(offset=(0.068, 0.0, -0.020)).box(
        0.014,
        0.026,
        0.014,
        centered=(True, True, False),
    )
    panel = panel.union(left_tab).union(right_tab)

    knob_cut = cq.Workplane("XY").center(KNOB_POS[0], KNOB_POS[1]).circle(0.0065).extrude(0.025, both=True)
    panel = panel.cut(knob_cut)

    for button_x in BUTTON_XS:
        button_cut = (
            cq.Workplane("XY")
            .center(button_x, BUTTON_Y)
            .rect(0.016, 0.010)
            .extrude(0.025, both=True)
        )
        panel = panel.cut(button_cut)

    return panel
def _jug_shell_shape() -> cq.Workplane:
    outer = (
        cq.Workplane("XY")
        .rect(0.100, 0.100)
        .workplane(offset=0.090)
        .rect(0.128, 0.128)
        .workplane(offset=0.140)
        .rect(0.160, 0.160)
        .loft(combine=True)
    )

    inner = (
        cq.Workplane("XY")
        .workplane(offset=0.016)
        .rect(0.078, 0.078)
        .workplane(offset=0.070)
        .rect(0.112, 0.112)
        .workplane(offset=0.159)
        .rect(0.152, 0.152)
        .loft(combine=True)
    )

    return outer.cut(inner)
def _jug_handle_shape() -> cq.Workplane:
    loop = (
        cq.Workplane("XZ")
        .center(0.102, 0.145)
        .rect(0.038, 0.148)
        .rect(0.018, 0.104)
        .extrude(0.020, both=True)
    )

    top_bridge = cq.Workplane("XY").transformed(offset=(0.078, 0.0, 0.191)).box(
        0.022,
        0.022,
        0.022,
        centered=(True, True, True),
    )
    bottom_bridge = cq.Workplane("XY").transformed(offset=(0.073, 0.0, 0.091)).box(
        0.024,
        0.022,
        0.028,
        centered=(True, True, True),
    )
    grip_pad = cq.Workplane("XY").transformed(offset=(0.108, 0.0, 0.145)).box(
        0.016,
        0.024,
        0.090,
        centered=(True, True, True),
    )

    return loop.union(top_bridge).union(bottom_bridge).union(grip_pad)
def _jug_collar_shape() -> cq.Workplane:
    outer = cq.Workplane("XY").box(0.104, 0.104, 0.026, centered=(True, True, False))
    inner = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.004)).box(
        0.076,
        0.076,
        0.024,
        centered=(True, True, False),
    )
    return outer.cut(inner)
def _knob_shape() -> cq.Workplane:
    skirt = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.0)).circle(0.028).extrude(0.004)
    body = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.004)).circle(0.024).extrude(0.014)
    crown = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.018)).circle(0.018).extrude(0.004)
    pointer = cq.Workplane("XY").transformed(offset=(0.0, 0.015, 0.0225)).box(
        0.004,
        0.010,
        0.001,
        centered=(True, True, True),
    )
    return skirt.union(body).union(crown).union(pointer)
def _lid_shape() -> cq.Workplane:
    plug = cq.Workplane("XY").transformed(offset=(0.0, 0.0, -0.013)).box(
        0.148,
        0.148,
        0.021,
        centered=(True, True, False),
    )
    flange = cq.Workplane("XY").box(0.170, 0.170, 0.010, centered=(True, True, False))
    crown = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.010)).box(
        0.154,
        0.154,
        0.008,
        centered=(True, True, False),
    )
    port_boss = cq.Workplane("XY").transformed(offset=(0.0, 0.0, 0.018)).circle(0.022).extrude(0.010)
    hinge_pedestal = cq.Workplane("XY").transformed(offset=(0.0, -0.019, 0.028)).box(
        0.034,
        0.010,
        0.014,
        centered=(True, True, True),
    )
    hinge_bridge = cq.Workplane("XY").transformed(offset=(0.0, -0.019, 0.033)).box(
        0.034,
        0.008,
        0.008,
        centered=(True, True, True),
    )
    left_barrel = cq.Workplane("XY").transformed(
        offset=(-0.011, -0.019, 0.033),
        rotate=(0.0, 90.0, 0.0),
    ).circle(0.004).extrude(0.008, both=True)
    right_barrel = cq.Workplane("XY").transformed(
        offset=(0.011, -0.019, 0.033),
        rotate=(0.0, 90.0, 0.0),
    ).circle(0.004).extrude(0.008, both=True)
    port_hole = cq.Workplane("XY").circle(0.0105).extrude(0.050, both=True)

    return (
        plug.union(flange)
        .union(crown)
        .union(port_boss)
        .union(hinge_pedestal)
        .union(hinge_bridge)
        .union(left_barrel)
        .union(right_barrel)
        .cut(port_hole)
    )
def _flap_shape() -> cq.Workplane:
    cap = cq.Workplane("XY").transformed(offset=(0.0, 0.019, 0.017)).box(
        0.038,
        0.032,
        0.004,
        centered=(True, True, True),
    )
    bridge = cq.Workplane("XY").transformed(offset=(0.0, 0.008, 0.008)).box(
        0.020,
        0.012,
        0.014,
        centered=(True, True, True),
    )
    barrel = cq.Workplane("XY").transformed(
        offset=(0.0, 0.0, 0.0),
        rotate=(0.0, 90.0, 0.0),
    ).circle(0.0038).extrude(0.010, both=True)
    tab = cq.Workplane("XY").transformed(offset=(0.0, 0.034, 0.018)).box(
        0.014,
        0.006,
        0.003,
        centered=(True, True, True),
    )
    return cap.union(bridge).union(barrel).union(tab)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="vacuum_blender")

    base_silver = model.material("base_silver", rgba=(0.73, 0.76, 0.80, 1.0))
    base_charcoal = model.material("base_charcoal", rgba=(0.16, 0.17, 0.18, 1.0))
    panel_glass = model.material("panel_glass", rgba=(0.09, 0.11, 0.13, 0.82))
    knob_black = model.material("knob_black", rgba=(0.10, 0.10, 0.11, 1.0))
    button_metal = model.material("button_metal", rgba=(0.70, 0.72, 0.75, 1.0))
    jug_clear = model.material("jug_clear", rgba=(0.78, 0.90, 0.98, 0.30))
    jug_trim = model.material("jug_trim", rgba=(0.12, 0.12, 0.13, 1.0))
    lid_black = model.material("lid_black", rgba=(0.14, 0.15, 0.16, 1.0))
    steel = model.material("steel", rgba=(0.80, 0.82, 0.84, 1.0))

    base = model.part("base")
    base.visual(mesh_from_cadquery(_base_shape(), "base_shell"), material=base_silver, name="shell")
    base.visual(
        Box((0.108, 0.108, 0.008)),
        origin=Origin(xyz=(0.0, 0.014, 0.146)),
        material=base_charcoal,
        name="seat",
    )

    panel = model.part("panel")
    panel.visual(mesh_from_cadquery(_panel_shape(), "front_panel"), material=panel_glass, name="plate")
    model.articulation(
        "base_to_panel",
        ArticulationType.FIXED,
        parent=base,
        child=panel,
        origin=Origin(
            xyz=(
                PANEL_CENTER[0],
                PANEL_CENTER[1] + 0.005 * math.sin(PANEL_TILT),
                PANEL_CENTER[2] - 0.005 * math.cos(PANEL_TILT),
            ),
            rpy=(PANEL_TILT, 0.0, 0.0),
        ),
    )

    knob = model.part("knob")
    knob.visual(
        mesh_from_cadquery(_knob_shape(), "control_knob"),
        material=knob_black,
        name="cap",
    )
    knob.visual(
        Cylinder(radius=0.006, length=0.014),
        origin=Origin(xyz=(0.0, 0.0, -0.007)),
        material=knob_black,
        name="shaft",
    )
    knob.visual(
        Cylinder(radius=0.009, length=0.002),
        origin=Origin(xyz=(0.0, 0.0, -0.009)),
        material=knob_black,
        name="retainer",
    )
    model.articulation(
        "panel_to_knob",
        ArticulationType.CONTINUOUS,
        parent=panel,
        child=knob,
        origin=Origin(xyz=(KNOB_POS[0], KNOB_POS[1], 0.0002)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=0.6, velocity=8.0),
    )

    for index, button_x in enumerate(BUTTON_XS):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.022, 0.014, 0.008)),
            origin=Origin(xyz=(0.0, 0.0, 0.004)),
            material=button_metal,
            name="cap",
        )
        button.visual(
            Box((0.014, 0.008, 0.011)),
            origin=Origin(xyz=(0.0, 0.0, -0.0045)),
            material=button_metal,
            name="stem",
        )
        button.visual(
            Box((0.018, 0.012, 0.002)),
            origin=Origin(xyz=(0.0, 0.0, -0.0102)),
            material=button_metal,
            name="retainer",
        )
        model.articulation(
            f"panel_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=panel,
            child=button,
            origin=Origin(xyz=(button_x, BUTTON_Y, 0.001)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.08,
                lower=0.0,
                upper=0.001,
            ),
        )

    jug = model.part("jug")
    jug.visual(mesh_from_cadquery(_jug_shell_shape(), "jug_shell"), material=jug_clear, name="shell")
    jug.visual(mesh_from_cadquery(_jug_handle_shape(), "jug_handle"), material=jug_trim, name="handle")
    jug.visual(mesh_from_cadquery(_jug_collar_shape(), "jug_collar"), material=jug_trim, name="collar")
    model.articulation(
        "base_to_jug",
        ArticulationType.FIXED,
        parent=base,
        child=jug,
        origin=Origin(xyz=JUG_ORIGIN),
    )

    lid = model.part("lid")
    lid.visual(mesh_from_cadquery(_lid_shape(), "lid_shell"), material=lid_black, name="shell")
    model.articulation(
        "jug_to_lid",
        ArticulationType.FIXED,
        parent=jug,
        child=lid,
        origin=Origin(xyz=(0.0, 0.0, JUG_HEIGHT + 0.0114)),
    )

    flap = model.part("flap")
    flap.visual(mesh_from_cadquery(_flap_shape(), "lid_flap"), material=lid_black, name="cap")
    model.articulation(
        "lid_to_flap",
        ArticulationType.REVOLUTE,
        parent=lid,
        child=flap,
        origin=Origin(xyz=(0.0, -0.019, 0.033)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=1.0,
            velocity=2.0,
            lower=0.0,
            upper=1.25,
        ),
    )

    socket = model.part("socket")
    socket.visual(
        Cylinder(radius=0.010, length=0.010),
        origin=Origin(xyz=(0.0, 0.0, 0.005)),
        material=jug_trim,
        name="body",
    )
    model.articulation(
        "jug_to_socket",
        ArticulationType.FIXED,
        parent=jug,
        child=socket,
        origin=Origin(xyz=(0.0, 0.0, 0.016)),
    )

    blade = model.part("blade")
    blade.visual(
        Cylinder(radius=0.011, length=0.006),
        origin=Origin(xyz=(0.0, 0.0, 0.003)),
        material=steel,
        name="hub",
    )
    for index, (yaw_deg, pitch_deg) in enumerate(((35.0, 20.0), (145.0, -20.0), (215.0, 20.0), (325.0, -20.0))):
        blade.visual(
            Box((0.030, 0.007, 0.002)),
            origin=Origin(
                xyz=(0.017, 0.0, 0.005),
                rpy=(0.0, math.radians(pitch_deg), math.radians(yaw_deg)),
            ),
            material=steel,
            name=f"wing_{index}",
        )
    model.articulation(
        "socket_to_blade",
        ArticulationType.CONTINUOUS,
        parent=socket,
        child=blade,
        origin=Origin(xyz=(0.0, 0.0, 0.010)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=15.0, velocity=40.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
