# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_conditioning_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_conditioning_machine

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
import cadquery as cq
PANEL_SIZE = 0.95
PANEL_THICKNESS = 0.028
CHASSIS_SIZE = 0.68
CHASSIS_HEIGHT = 0.27
INTAKE_OPENING = 0.488
INTAKE_GRILLE_OUTER = 0.492
INTAKE_GRILLE_THICKNESS = 0.006
INTAKE_GRILLE_FRAME = 0.024
INTAKE_BAR_WIDTH = 0.012
INTAKE_BAR_COUNT = 5
OUTLET_LENGTH = 0.50
OUTLET_DEPTH = 0.105
OUTLET_GAP = 0.015
OUTLET_CENTER_OFFSET = INTAKE_GRILLE_OUTER / 2.0 + OUTLET_GAP + OUTLET_DEPTH / 2.0
FLAP_THICKNESS = 0.01
FLAP_LENGTH = OUTLET_LENGTH - 0.012
FLAP_DEPTH = OUTLET_DEPTH - 0.012
FLAP_SWING = 1.1
BUTTON_CAP_SIZE = (0.018, 0.012, 0.003)
BUTTON_STEM_HEIGHT = 0.009
BUTTON_SLOT = (0.021, 0.015)
BUTTON_TRAVEL = 0.0035
BUTTON_Y = -0.432
BUTTON_XS = (0.334, 0.366)
def _cut_box(size: tuple[float, float, float], xyz: tuple[float, float, float]) -> cq.Workplane:
    return cq.Workplane("XY").box(*size).translate(xyz)
def _build_panel_shell() -> cq.Workplane:
    shell = cq.Workplane("XY").box(PANEL_SIZE, PANEL_SIZE, PANEL_THICKNESS).translate(
        (0.0, 0.0, PANEL_THICKNESS / 2.0)
    )

    full_cut_height = PANEL_THICKNESS + 0.02
    shell = shell.cut(_cut_box((INTAKE_OPENING, INTAKE_OPENING, full_cut_height), (0.0, 0.0, PANEL_THICKNESS / 2.0)))
    shell = shell.cut(
        _cut_box(
            (OUTLET_LENGTH, OUTLET_DEPTH, full_cut_height),
            (0.0, -OUTLET_CENTER_OFFSET, PANEL_THICKNESS / 2.0),
        )
    )
    shell = shell.cut(
        _cut_box(
            (OUTLET_LENGTH, OUTLET_DEPTH, full_cut_height),
            (0.0, OUTLET_CENTER_OFFSET, PANEL_THICKNESS / 2.0),
        )
    )
    shell = shell.cut(
        _cut_box(
            (OUTLET_DEPTH, OUTLET_LENGTH, full_cut_height),
            (-OUTLET_CENTER_OFFSET, 0.0, PANEL_THICKNESS / 2.0),
        )
    )
    shell = shell.cut(
        _cut_box(
            (OUTLET_DEPTH, OUTLET_LENGTH, full_cut_height),
            (OUTLET_CENTER_OFFSET, 0.0, PANEL_THICKNESS / 2.0),
        )
    )

    for button_x in BUTTON_XS:
        shell = shell.cut(
            _cut_box(
                (BUTTON_SLOT[0], BUTTON_SLOT[1], full_cut_height),
                (button_x, BUTTON_Y, PANEL_THICKNESS / 2.0),
            )
        )

    return shell
def _build_intake_grille() -> cq.Workplane:
    grille = cq.Workplane("XY").box(
        INTAKE_GRILLE_OUTER,
        INTAKE_GRILLE_OUTER,
        INTAKE_GRILLE_THICKNESS,
    ).translate((0.0, 0.0, INTAKE_GRILLE_THICKNESS / 2.0))

    clear = INTAKE_GRILLE_OUTER - 2.0 * INTAKE_GRILLE_FRAME
    grille = grille.cut(
        _cut_box(
            (clear, clear, INTAKE_GRILLE_THICKNESS + 0.004),
            (0.0, 0.0, INTAKE_GRILLE_THICKNESS / 2.0),
        )
    )

    pitch = clear / (INTAKE_BAR_COUNT + 1)
    bar_span = clear + 0.002
    for i in range(INTAKE_BAR_COUNT):
        pos = -clear / 2.0 + (i + 1) * pitch
        grille = grille.union(
            cq.Workplane("XY")
            .box(INTAKE_BAR_WIDTH, bar_span, INTAKE_GRILLE_THICKNESS)
            .translate((pos, 0.0, INTAKE_GRILLE_THICKNESS / 2.0))
        )
        grille = grille.union(
            cq.Workplane("XY")
            .box(bar_span, INTAKE_BAR_WIDTH, INTAKE_GRILLE_THICKNESS)
            .translate((0.0, pos, INTAKE_GRILLE_THICKNESS / 2.0))
        )

    return grille
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="ceiling_cassette_air_conditioner")

    panel_white = model.material("panel_white", color=(0.94, 0.95, 0.93))
    chassis_gray = model.material("chassis_gray", color=(0.80, 0.82, 0.82))
    grille_gray = model.material("grille_gray", color=(0.72, 0.75, 0.76))
    flap_white = model.material("flap_white", color=(0.92, 0.93, 0.91))
    button_gray = model.material("button_gray", color=(0.58, 0.60, 0.62))

    cassette = model.part("cassette")
    cassette.visual(
        mesh_from_cadquery(_build_panel_shell(), "cassette_panel_shell"),
        material=panel_white,
        name="panel_shell",
    )
    cassette.visual(
        mesh_from_cadquery(_build_intake_grille(), "cassette_intake_grille"),
        material=grille_gray,
        name="intake_grille",
    )
    cassette.visual(
        Box((CHASSIS_SIZE, CHASSIS_SIZE, CHASSIS_HEIGHT)),
        origin=Origin(xyz=(0.0, 0.0, PANEL_THICKNESS + CHASSIS_HEIGHT / 2.0)),
        material=chassis_gray,
        name="upper_body",
    )

    front_flap = model.part("front_flap")
    front_flap.visual(
        Box((FLAP_LENGTH, FLAP_DEPTH, FLAP_THICKNESS)),
        origin=Origin(xyz=(0.0, FLAP_DEPTH / 2.0, -FLAP_THICKNESS / 2.0)),
        material=flap_white,
        name="flap_panel",
    )

    rear_flap = model.part("rear_flap")
    rear_flap.visual(
        Box((FLAP_LENGTH, FLAP_DEPTH, FLAP_THICKNESS)),
        origin=Origin(xyz=(0.0, -FLAP_DEPTH / 2.0, -FLAP_THICKNESS / 2.0)),
        material=flap_white,
        name="flap_panel",
    )

    left_flap = model.part("left_flap")
    left_flap.visual(
        Box((FLAP_DEPTH, FLAP_LENGTH, FLAP_THICKNESS)),
        origin=Origin(xyz=(FLAP_DEPTH / 2.0, 0.0, -FLAP_THICKNESS / 2.0)),
        material=flap_white,
        name="flap_panel",
    )

    right_flap = model.part("right_flap")
    right_flap.visual(
        Box((FLAP_DEPTH, FLAP_LENGTH, FLAP_THICKNESS)),
        origin=Origin(xyz=(-FLAP_DEPTH / 2.0, 0.0, -FLAP_THICKNESS / 2.0)),
        material=flap_white,
        name="flap_panel",
    )

    for index, button_x in enumerate(BUTTON_XS):
        button = model.part(f"front_button_{index}")
        button.visual(
            Box(BUTTON_CAP_SIZE),
            material=button_gray,
            name="button_cap",
        )
        button.visual(
            Box((BUTTON_SLOT[0], BUTTON_SLOT[1], BUTTON_STEM_HEIGHT)),
            origin=Origin(xyz=(0.0, 0.0, BUTTON_CAP_SIZE[2] / 2.0 + BUTTON_STEM_HEIGHT / 2.0)),
            material=button_gray,
            name="button_stem",
        )
        model.articulation(
            f"front_button_{index}_press",
            ArticulationType.PRISMATIC,
            parent=cassette,
            child=button,
            origin=Origin(xyz=(button_x, BUTTON_Y, BUTTON_CAP_SIZE[2] / 2.0)),
            axis=(0.0, 0.0, 1.0),
            motion_limits=MotionLimits(
                effort=3.0,
                velocity=0.05,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    model.articulation(
        "front_flap_hinge",
        ArticulationType.REVOLUTE,
        parent=cassette,
        child=front_flap,
        origin=Origin(xyz=(0.0, -OUTLET_CENTER_OFFSET - OUTLET_DEPTH / 2.0, 0.0)),
        axis=(-1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=0.0, upper=FLAP_SWING),
    )
    model.articulation(
        "rear_flap_hinge",
        ArticulationType.REVOLUTE,
        parent=cassette,
        child=rear_flap,
        origin=Origin(xyz=(0.0, OUTLET_CENTER_OFFSET + OUTLET_DEPTH / 2.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=0.0, upper=FLAP_SWING),
    )
    model.articulation(
        "left_flap_hinge",
        ArticulationType.REVOLUTE,
        parent=cassette,
        child=left_flap,
        origin=Origin(xyz=(-OUTLET_CENTER_OFFSET - OUTLET_DEPTH / 2.0, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=0.0, upper=FLAP_SWING),
    )
    model.articulation(
        "right_flap_hinge",
        ArticulationType.REVOLUTE,
        parent=cassette,
        child=right_flap,
        origin=Origin(xyz=(OUTLET_CENTER_OFFSET + OUTLET_DEPTH / 2.0, 0.0, 0.0)),
        axis=(0.0, -1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=1.5, lower=0.0, upper=FLAP_SWING),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
