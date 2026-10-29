# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_fryer_with_pullout_basket, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_fryer_with_pullout_basket

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
BODY_D = 0.340
BODY_W = 0.285
BODY_H = 0.388
BODY_Z0 = 0.012
BODY_FRONT_X = BODY_D * 0.5
DRAWER_D = 0.228
DRAWER_W = 0.236
DRAWER_H = 0.178
DRAWER_FRONT_T = 0.016
DRAWER_WALL = 0.005
DRAWER_Z0 = 0.060
DRAWER_TRAVEL = 0.145
BASKET_D = 0.206
BASKET_W = 0.214
BASKET_H = 0.147
BASKET_WALL = 0.004
BASKET_FRONT_GAP = 0.026
def _build_housing_shell():
    shell = (
        cq.Workplane("XY")
        .box(BODY_D, BODY_W, BODY_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(0.020)
        .translate((0.0, 0.0, BODY_Z0))
    )

    cavity = (
        cq.Workplane("XY")
        .box(0.252, 0.244, 0.192, centered=(True, True, False))
        .translate((0.044, 0.0, 0.056))
    )

    return shell.cut(cavity)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="glass_window_air_fryer")

    body_finish = model.material("body_finish", rgba=(0.13, 0.14, 0.15, 1.0))
    trim_finish = model.material("trim_finish", rgba=(0.19, 0.20, 0.22, 1.0))
    handle_finish = model.material("handle_finish", rgba=(0.17, 0.18, 0.19, 1.0))
    basket_finish = model.material("basket_finish", rgba=(0.23, 0.24, 0.25, 1.0))
    glass_tint = model.material("glass_tint", rgba=(0.34, 0.41, 0.46, 0.28))
    foot_finish = model.material("foot_finish", rgba=(0.07, 0.07, 0.08, 1.0))
    accent_finish = model.material("accent_finish", rgba=(0.56, 0.58, 0.61, 1.0))
    control_finish = model.material("control_finish", rgba=(0.10, 0.11, 0.12, 1.0))

    housing = model.part("housing")
    housing.visual(
        mesh_from_cadquery(_build_housing_shell(), "housing_shell"),
        material=body_finish,
        name="body_shell",
    )
    housing.visual(
        Box((0.220, 0.180, 0.010)),
        origin=Origin(xyz=(0.000, 0.000, BODY_Z0 + BODY_H - 0.005)),
        material=trim_finish,
        name="top_cap",
    )
    housing.visual(
        Box((0.146, 0.010, 0.248)),
        origin=Origin(xyz=(0.046, BODY_W * 0.5 + 0.005, 0.208)),
        material=trim_finish,
        name="control_panel",
    )
    for x_pos, z_pos, name in (
        (0.018, 0.272, "dial_ring_0"),
        (0.018, 0.190, "dial_ring_1"),
    ):
        housing.visual(
            Cylinder(radius=0.031, length=0.004),
            origin=Origin(xyz=(x_pos, BODY_W * 0.5 + 0.012, z_pos), rpy=(1.57079632679, 0.0, 0.0)),
            material=accent_finish,
            name=name,
        )
    for x_pos, z_pos, name in (
        (0.088, 0.274, "button_bezel_0"),
        (0.088, 0.224, "button_bezel_1"),
        (0.088, 0.174, "button_bezel_2"),
    ):
        housing.visual(
            Box((0.026, 0.006, 0.022)),
            origin=Origin(xyz=(x_pos, BODY_W * 0.5 + 0.008, z_pos)),
            material=accent_finish,
            name=name,
        )
    for y_pos, name in ((-0.122, "guide_rail_0"), (0.122, "guide_rail_1")):
        housing.visual(
            Box((0.248, 0.010, 0.012)),
            origin=Origin(xyz=(0.044, y_pos, DRAWER_Z0 + 0.016)),
            material=trim_finish,
            name=name,
        )
    for x_pos in (-0.120, 0.120):
        for y_pos in (-0.092, 0.092):
            housing.visual(
                Cylinder(radius=0.014, length=0.012),
                origin=Origin(xyz=(x_pos, y_pos, 0.006)),
                material=foot_finish,
                name=f"foot_{int((x_pos > 0.0))}_{int((y_pos > 0.0))}",
            )

    drawer = model.part("drawer")
    drawer.visual(
        Box((DRAWER_D - DRAWER_FRONT_T, DRAWER_W, DRAWER_WALL)),
        origin=Origin(xyz=(-(DRAWER_D + DRAWER_FRONT_T) * 0.5, 0.000, DRAWER_WALL * 0.5)),
        material=trim_finish,
        name="drawer_bottom",
    )
    drawer.visual(
        Box((DRAWER_D - DRAWER_FRONT_T, DRAWER_WALL, DRAWER_H)),
        origin=Origin(
            xyz=(
                -(DRAWER_D + DRAWER_FRONT_T) * 0.5,
                -(DRAWER_W - DRAWER_WALL) * 0.5,
                DRAWER_H * 0.5,
            )
        ),
        material=trim_finish,
        name="drawer_side_0",
    )
    drawer.visual(
        Box((DRAWER_D - DRAWER_FRONT_T, DRAWER_WALL, DRAWER_H)),
        origin=Origin(
            xyz=(
                -(DRAWER_D + DRAWER_FRONT_T) * 0.5,
                (DRAWER_W - DRAWER_WALL) * 0.5,
                DRAWER_H * 0.5,
            )
        ),
        material=trim_finish,
        name="drawer_side_1",
    )
    drawer.visual(
        Box((DRAWER_WALL, DRAWER_W - 2.0 * DRAWER_WALL, DRAWER_H)),
        origin=Origin(xyz=(-DRAWER_D + DRAWER_WALL * 0.5, 0.000, DRAWER_H * 0.5)),
        material=trim_finish,
        name="drawer_back",
    )
    drawer.visual(
        Box((DRAWER_FRONT_T, DRAWER_W, 0.094)),
        origin=Origin(xyz=(-DRAWER_FRONT_T * 0.5, 0.000, 0.047)),
        material=body_finish,
        name="front_lower",
    )
    drawer.visual(
        Box((DRAWER_FRONT_T, DRAWER_W, DRAWER_H - 0.148)),
        origin=Origin(xyz=(-DRAWER_FRONT_T * 0.5, 0.000, 0.163)),
        material=body_finish,
        name="front_upper",
    )
    for y_pos, name in ((-0.091, "front_jamb_0"), (0.091, "front_jamb_1")):
        drawer.visual(
            Box((DRAWER_FRONT_T, 0.054, 0.054)),
            origin=Origin(xyz=(-DRAWER_FRONT_T * 0.5, y_pos, 0.121)),
            material=body_finish,
            name=name,
        )
    for y_pos, name in ((-0.114, "slider_shoe_0"), (0.114, "slider_shoe_1")):
        drawer.visual(
            Box((0.206, 0.006, 0.010)),
            origin=Origin(xyz=(-0.122, y_pos, 0.016)),
            material=trim_finish,
            name=name,
        )
    drawer.visual(
        Box((0.046, 0.014, 0.050)),
        origin=Origin(xyz=(0.021, -0.060, 0.055)),
        material=handle_finish,
        name="handle_cheek_0",
    )
    drawer.visual(
        Box((0.046, 0.014, 0.050)),
        origin=Origin(xyz=(0.021, 0.060, 0.055)),
        material=handle_finish,
        name="handle_cheek_1",
    )
    drawer.visual(
        Box((0.028, 0.140, 0.030)),
        origin=Origin(xyz=(0.030, 0.000, 0.056)),
        material=handle_finish,
        name="handle_grip",
    )
    drawer.visual(
        Box((0.018, 0.042, 0.010)),
        origin=Origin(xyz=(0.008, -0.049, 0.080)),
        material=handle_finish,
        name="handle_top_0",
    )
    drawer.visual(
        Box((0.018, 0.042, 0.010)),
        origin=Origin(xyz=(0.008, 0.049, 0.080)),
        material=handle_finish,
        name="handle_top_1",
    )
    drawer.visual(
        Box((0.003, 0.136, 0.062)),
        origin=Origin(xyz=(-0.009, 0.000, 0.121)),
        material=glass_tint,
        name="window_glass",
    )

    basket = model.part("basket")
    basket.visual(
        Box((BASKET_D, BASKET_W, BASKET_WALL)),
        origin=Origin(xyz=(-BASKET_D * 0.5, 0.000, BASKET_WALL * 0.5)),
        material=basket_finish,
        name="basket_bottom",
    )
    basket.visual(
        Box((BASKET_D, BASKET_WALL, BASKET_H)),
        origin=Origin(xyz=(-BASKET_D * 0.5, -(BASKET_W - BASKET_WALL) * 0.5, BASKET_H * 0.5)),
        material=basket_finish,
        name="basket_side_0",
    )
    basket.visual(
        Box((BASKET_D, BASKET_WALL, BASKET_H)),
        origin=Origin(xyz=(-BASKET_D * 0.5, (BASKET_W - BASKET_WALL) * 0.5, BASKET_H * 0.5)),
        material=basket_finish,
        name="basket_side_1",
    )
    basket.visual(
        Box((BASKET_WALL, BASKET_W - 2.0 * BASKET_WALL, BASKET_H)),
        origin=Origin(xyz=(-BASKET_D + BASKET_WALL * 0.5, 0.000, BASKET_H * 0.5)),
        material=basket_finish,
        name="basket_back",
    )
    basket.visual(
        Box((BASKET_WALL, 0.050, 0.064)),
        origin=Origin(xyz=(-BASKET_WALL * 0.5, -0.078, 0.032)),
        material=basket_finish,
        name="basket_front_0",
    )
    basket.visual(
        Box((BASKET_WALL, 0.050, 0.064)),
        origin=Origin(xyz=(-BASKET_WALL * 0.5, 0.078, 0.032)),
        material=basket_finish,
        name="basket_front_1",
    )
    basket.visual(
        Box((BASKET_WALL, BASKET_W, 0.032)),
        origin=Origin(xyz=(-BASKET_WALL * 0.5, 0.000, 0.016)),
        material=basket_finish,
        name="basket_front_lower",
    )
    basket.visual(
        Box((BASKET_WALL, BASKET_W, 0.035)),
        origin=Origin(xyz=(-BASKET_WALL * 0.5, 0.000, 0.1295)),
        material=basket_finish,
        name="basket_front_upper",
    )

    release_button = model.part("release_button")
    release_button.visual(
        Box((0.018, 0.046, 0.006)),
        origin=Origin(xyz=(0.000, 0.000, 0.000)),
        material=accent_finish,
        name="release_cap",
    )
    release_button.visual(
        Box((0.012, 0.028, 0.010)),
        origin=Origin(xyz=(0.000, 0.000, -0.008)),
        material=accent_finish,
        name="release_stem",
    )

    for part_name, x_pos, z_pos in (
        ("dial_0", 0.018, 0.272),
        ("dial_1", 0.018, 0.190),
    ):
        dial = model.part(part_name)
        dial.visual(
            Cylinder(radius=0.028, length=0.008),
            origin=Origin(xyz=(0.000, 0.004, 0.000), rpy=(1.57079632679, 0.0, 0.0)),
            material=control_finish,
            name="dial_skirt",
        )
        dial.visual(
            Cylinder(radius=0.021, length=0.018),
            origin=Origin(xyz=(0.000, 0.017, 0.000), rpy=(1.57079632679, 0.0, 0.0)),
            material=control_finish,
            name="dial_cap",
        )
        dial.visual(
            Box((0.004, 0.004, 0.010)),
            origin=Origin(xyz=(0.000, 0.028, 0.013)),
            material=accent_finish,
            name="dial_marker",
        )
        model.articulation(
            f"housing_to_{part_name}",
            ArticulationType.CONTINUOUS,
            parent=housing,
            child=dial,
            origin=Origin(xyz=(x_pos, BODY_W * 0.5 + 0.010, z_pos)),
            axis=(0.0, 1.0, 0.0),
            motion_limits=MotionLimits(effort=0.35, velocity=8.0),
        )

    for index, x_pos, z_pos in (
        (0, 0.088, 0.274),
        (1, 0.088, 0.224),
        (2, 0.088, 0.174),
    ):
        button = model.part(f"button_{index}")
        button.visual(
            Box((0.020, 0.010, 0.016)),
            origin=Origin(xyz=(0.000, 0.009, 0.000)),
            material=accent_finish,
            name="button_cap",
        )
        button.visual(
            Box((0.010, 0.004, 0.010)),
            origin=Origin(xyz=(0.000, 0.002, 0.000)),
            material=accent_finish,
            name="button_stem",
        )
        model.articulation(
            f"housing_to_button_{index}",
            ArticulationType.PRISMATIC,
            parent=housing,
            child=button,
            origin=Origin(xyz=(x_pos, BODY_W * 0.5 + 0.011, z_pos)),
            axis=(0.0, -1.0, 0.0),
            motion_limits=MotionLimits(
                effort=6.0,
                velocity=0.08,
                lower=0.0,
                upper=0.004,
            ),
        )

    model.articulation(
        "housing_to_drawer",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=drawer,
        origin=Origin(xyz=(BODY_FRONT_X, 0.000, DRAWER_Z0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(
            effort=55.0,
            velocity=0.28,
            lower=0.0,
            upper=DRAWER_TRAVEL,
        ),
    )
    model.articulation(
        "drawer_to_basket",
        ArticulationType.FIXED,
        parent=drawer,
        child=basket,
        origin=Origin(xyz=(-BASKET_FRONT_GAP, 0.000, 0.012)),
    )
    model.articulation(
        "drawer_to_release_button",
        ArticulationType.PRISMATIC,
        parent=drawer,
        child=release_button,
        origin=Origin(xyz=(0.022, 0.000, 0.084)),
        axis=(0.0, 0.0, -1.0),
        motion_limits=MotionLimits(
            effort=8.0,
            velocity=0.08,
            lower=0.0,
            upper=0.004,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
