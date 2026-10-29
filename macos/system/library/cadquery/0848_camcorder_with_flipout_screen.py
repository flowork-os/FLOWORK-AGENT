# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, camcorder_with_flipout_screen, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: camcorder_with_flipout_screen

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
import cadquery as cq
BODY_LENGTH = 0.086
BODY_WIDTH = 0.046
BODY_HEIGHT = 0.054
BODY_HALF_WIDTH = BODY_WIDTH * 0.5
SCREEN_LENGTH = 0.062
SCREEN_HEIGHT = 0.040
SCREEN_THICKNESS = 0.0048
HINGE_RADIUS = 0.0014
HINGE_X = -0.030
HINGE_Y = BODY_HALF_WIDTH + HINGE_RADIUS
BUTTON_WIDTH = 0.0064
BUTTON_DEPTH = 0.0024
BUTTON_HEIGHT = 0.0058
BUTTON_TRAVEL = 0.0020
def _body_shell_mesh():
    body = cq.Workplane("XY").box(BODY_LENGTH, BODY_WIDTH, BODY_HEIGHT)
    body = body.edges("|Z").fillet(0.0055)

    rear_bulge = cq.Workplane("XY").box(0.018, 0.038, 0.038).translate((-0.034, 0.000, 0.001))
    top_hump = cq.Workplane("XY").box(0.030, 0.020, 0.008).translate((-0.008, 0.000, 0.031))
    nose_cheek = cq.Workplane("XY").box(0.012, 0.032, 0.034).translate((0.040, 0.000, -0.003))
    eyecup = cq.Workplane("XY").box(0.010, 0.022, 0.018).translate((-0.046, 0.000, 0.012))

    body = body.union(rear_bulge).union(top_hump).union(nose_cheek).union(eyecup)

    screen_recess = cq.Workplane("XY").box(0.060, 0.0034, 0.040).translate((0.004, 0.0213, 0.004))
    body = body.cut(screen_recess)

    for x_pos in (-0.004, 0.008, 0.020):
        button_pocket = (
            cq.Workplane("XY")
            .box(0.0074, 0.0052, 0.0068)
            .translate((x_pos, BODY_HALF_WIDTH - 0.0026, -0.015))
        )
        body = body.cut(button_pocket)

    return mesh_from_cadquery(body, "camcorder_body_shell")
def _lens_ring_mesh():
    ring = cq.Workplane("YZ").circle(0.0178).circle(0.0152).extrude(0.011)
    for x_pos in (0.0015, 0.0048, 0.0081):
        rib = (
            cq.Workplane("YZ")
            .workplane(offset=x_pos)
            .circle(0.0184)
            .circle(0.0178)
            .extrude(0.0008)
        )
        ring = ring.union(rib)
    return mesh_from_cadquery(ring, "camcorder_lens_ring")
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="home_video_camcorder")

    body_mat = model.material("body_mat", rgba=(0.14, 0.15, 0.16, 1.0))
    trim_mat = model.material("trim_mat", rgba=(0.25, 0.26, 0.28, 1.0))
    glass_mat = model.material("glass_mat", rgba=(0.16, 0.24, 0.30, 0.48))
    lens_mat = model.material("lens_mat", rgba=(0.08, 0.08, 0.09, 1.0))
    button_mat = model.material("button_mat", rgba=(0.58, 0.60, 0.63, 1.0))
    strap_mat = model.material("strap_mat", rgba=(0.18, 0.18, 0.19, 1.0))
    strap_pad_mat = model.material("strap_pad_mat", rgba=(0.10, 0.10, 0.11, 1.0))

    body = model.part("body")
    body.visual(_body_shell_mesh(), material=body_mat, name="body_shell")
    body.visual(
        Cylinder(radius=0.0146, length=0.0260),
        origin=Origin(xyz=(0.056, 0.000, 0.000), rpy=(0.000, 1.57079632679, 0.000)),
        material=trim_mat,
        name="lens_housing",
    )
    body.visual(
        Cylinder(radius=0.0118, length=0.0220),
        origin=Origin(xyz=(0.058, 0.000, 0.000), rpy=(0.000, 1.57079632679, 0.000)),
        material=lens_mat,
        name="lens_core",
    )
    body.visual(
        Cylinder(radius=0.0105, length=0.0018),
        origin=Origin(xyz=(0.0699, 0.000, 0.000), rpy=(0.000, 1.57079632679, 0.000)),
        material=glass_mat,
        name="front_glass",
    )
    body.visual(
        Cylinder(radius=0.0178, length=0.0010),
        origin=Origin(xyz=(0.0525, 0.000, 0.000), rpy=(0.000, 1.57079632679, 0.000)),
        material=trim_mat,
        name="lens_mount_face",
    )
    body.visual(
        Box((0.012, 0.010, 0.006)),
        origin=Origin(xyz=(0.006, 0.000, 0.030)),
        material=trim_mat,
        name="top_mic",
    )
    body.visual(
        Cylinder(radius=HINGE_RADIUS, length=0.011),
        origin=Origin(xyz=(HINGE_X, HINGE_Y, -0.0135)),
        material=trim_mat,
        name="hinge_barrel_lower",
    )
    body.visual(
        Cylinder(radius=HINGE_RADIUS, length=0.011),
        origin=Origin(xyz=(HINGE_X, HINGE_Y, 0.0135)),
        material=trim_mat,
        name="hinge_barrel_upper",
    )
    body.visual(
        Box((0.0045, HINGE_RADIUS * 2.0, 0.011)),
        origin=Origin(xyz=(HINGE_X + 0.0022, BODY_HALF_WIDTH + HINGE_RADIUS, -0.0135)),
        material=trim_mat,
        name="hinge_leaf_lower",
    )
    body.visual(
        Box((0.0045, HINGE_RADIUS * 2.0, 0.011)),
        origin=Origin(xyz=(HINGE_X + 0.0022, BODY_HALF_WIDTH + HINGE_RADIUS, 0.0135)),
        material=trim_mat,
        name="hinge_leaf_upper",
    )
    for index, x_pos in enumerate((-0.004, 0.008, 0.020)):
        body.visual(
            Box((0.0048, 0.0040, 0.0040)),
            origin=Origin(xyz=(x_pos, BODY_HALF_WIDTH - 0.0034, -0.015)),
            material=trim_mat,
            name=f"button_guide_{index}",
        )

    hand_strap = model.part("hand_strap")
    hand_strap.visual(
        Box((0.010, 0.002, 0.022)),
        origin=Origin(xyz=(-0.025, -0.001, 0.000)),
        material=strap_pad_mat,
        name="front_anchor",
    )
    hand_strap.visual(
        Box((0.010, 0.002, 0.022)),
        origin=Origin(xyz=(0.022, -0.001, 0.000)),
        material=strap_pad_mat,
        name="rear_anchor",
    )
    hand_strap.visual(
        Box((0.052, 0.002, 0.020)),
        origin=Origin(xyz=(-0.0015, -0.003, 0.000)),
        material=strap_mat,
        name="strap_band",
    )
    model.articulation(
        "body_to_hand_strap",
        ArticulationType.FIXED,
        parent=body,
        child=hand_strap,
        origin=Origin(xyz=(0.000, -BODY_HALF_WIDTH, 0.000)),
    )

    screen = model.part("screen")
    screen.visual(
        Cylinder(radius=0.0012, length=0.014),
        origin=Origin(),
        material=trim_mat,
        name="hinge_barrel",
    )
    screen.visual(
        Box((0.005, 0.0014, 0.030)),
        origin=Origin(xyz=(0.0025, 0.0007, 0.000)),
        material=trim_mat,
        name="hinge_leaf",
    )
    screen.visual(
        Box((SCREEN_LENGTH, SCREEN_THICKNESS, SCREEN_HEIGHT)),
        origin=Origin(xyz=(0.036, 0.0038, 0.000)),
        material=trim_mat,
        name="screen_panel",
    )
    screen.visual(
        Box((0.053, 0.0008, 0.032)),
        origin=Origin(xyz=(0.036, 0.0066, 0.000)),
        material=glass_mat,
        name="display",
    )
    model.articulation(
        "body_to_screen",
        ArticulationType.REVOLUTE,
        parent=body,
        child=screen,
        origin=Origin(xyz=(HINGE_X, HINGE_Y, 0.000)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=0.4,
            velocity=2.0,
            lower=0.0,
            upper=2.35,
        ),
    )

    lens_ring = model.part("lens_ring")
    lens_ring.visual(_lens_ring_mesh(), material=lens_mat, name="ring_shell")
    model.articulation(
        "body_to_lens_ring",
        ArticulationType.CONTINUOUS,
        parent=body,
        child=lens_ring,
        origin=Origin(xyz=(0.053, 0.000, 0.000)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=0.15,
            velocity=8.0,
        ),
    )

    for index, x_pos in enumerate((-0.004, 0.008, 0.020)):
        button = model.part(f"button_{index}")
        button.visual(
            Box((BUTTON_WIDTH, BUTTON_DEPTH, BUTTON_HEIGHT)),
            origin=Origin(xyz=(0.000, BUTTON_DEPTH * 0.5, 0.000)),
            material=button_mat,
            name="button_cap",
        )
        button.visual(
            Box((0.0042, 0.0030, 0.0036)),
            origin=Origin(xyz=(0.000, -0.0013, 0.000)),
            material=button_mat,
            name="button_stem",
        )
        model.articulation(
            f"body_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(x_pos, BODY_HALF_WIDTH, -0.015)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=4.0,
                velocity=0.03,
                lower=0.0,
                upper=BUTTON_TRAVEL,
            ),
        )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
