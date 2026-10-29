# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, air_purifier_with_filter_door, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: air_purifier_with_filter_door

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

class Inertia:
    def __init__(self, ixx=0.0, ixy=0.0, ixz=0.0, iyy=0.0, iyz=0.0, izz=0.0):
        self.ixx, self.ixy, self.ixz = ixx, ixy, ixz
        self.iyy, self.iyz, self.izz = iyy, iyz, izz

class Inertial:
    def __init__(self, mass=1.0, inertia=None, origin=None):
        self.mass = float(mass)
        self.inertia = inertia
        self.origin = origin or Origin()

    @staticmethod
    def from_geometry(geometry, mass, *, origin=None):
        return Inertial(mass=mass, inertia=Inertia(), origin=origin or Origin())

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
import math
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="portable_bedside_air_purifier")

    shell_white = model.material("shell_white", rgba=(0.95, 0.96, 0.94, 1.0))
    grille_grey = model.material("grille_grey", rgba=(0.84, 0.86, 0.86, 1.0))
    interior_charcoal = model.material("interior_charcoal", rgba=(0.16, 0.18, 0.19, 1.0))
    tray_grey = model.material("tray_grey", rgba=(0.82, 0.84, 0.85, 1.0))
    filter_green = model.material("filter_green", rgba=(0.72, 0.80, 0.72, 1.0))
    filter_shadow = model.material("filter_shadow", rgba=(0.56, 0.63, 0.56, 1.0))

    housing_width = 0.230
    housing_depth = 0.225
    housing_height = 0.305
    shell_wall = 0.006
    shell_radius = 0.024
    top_cap_thickness = 0.006

    grille_width = 0.176
    grille_height = 0.180
    grille_bottom = 0.072
    tray_slot_width = 0.194
    tray_slot_height = 0.042
    tray_slot_bottom = 0.000

    tray_width = 0.198
    tray_depth = 0.168
    tray_wall = 0.003
    tray_front_lip_width = 0.188
    tray_front_lip_thickness = 0.004
    tray_front_lip_height = 0.038
    tray_travel = 0.125

    housing = model.part("housing")
    shell_body_height = housing_height - top_cap_thickness
    front_plane_y = housing_depth * 0.5 - shell_wall * 0.5
    side_panel_depth = housing_depth - shell_wall
    front_post_width = 0.018
    housing.visual(
        Box((shell_wall, side_panel_depth, shell_body_height)),
        origin=Origin(
            xyz=(
                -(housing_width * 0.5 - shell_wall * 0.5),
                -shell_wall * 0.5,
                shell_body_height * 0.5,
            )
        ),
        material=shell_white,
        name="left_shell_wall",
    )
    housing.visual(
        Box((shell_wall, side_panel_depth, shell_body_height)),
        origin=Origin(
            xyz=(
                housing_width * 0.5 - shell_wall * 0.5,
                -shell_wall * 0.5,
                shell_body_height * 0.5,
            )
        ),
        material=shell_white,
        name="right_shell_wall",
    )
    housing.visual(
        Box((housing_width - 2.0 * shell_wall, shell_wall, shell_body_height)),
        origin=Origin(
            xyz=(
                0.0,
                -(housing_depth * 0.5 - shell_wall * 0.5),
                shell_body_height * 0.5,
            )
        ),
        material=shell_white,
        name="back_shell_wall",
    )
    housing.visual(
        Box((housing_width, housing_depth, top_cap_thickness)),
        origin=Origin(xyz=(0.0, 0.0, housing_height - top_cap_thickness * 0.5)),
        material=shell_white,
        name="top_cap",
    )
    housing.visual(
        Box((front_post_width, shell_wall, shell_body_height)),
        origin=Origin(
            xyz=(
                -(housing_width * 0.5 - front_post_width * 0.5),
                front_plane_y,
                shell_body_height * 0.5,
            )
        ),
        material=shell_white,
        name="front_left_post",
    )
    housing.visual(
        Box((front_post_width, shell_wall, shell_body_height)),
        origin=Origin(
            xyz=(
                housing_width * 0.5 - front_post_width * 0.5,
                front_plane_y,
                shell_body_height * 0.5,
            )
        ),
        material=shell_white,
        name="front_right_post",
    )
    housing.visual(
        Box((0.194, shell_wall, tray_slot_bottom + tray_slot_height)),
        origin=Origin(
            xyz=(
                0.0,
                front_plane_y,
                (tray_slot_bottom + tray_slot_height) * 0.5,
            )
        ),
        material=shell_white,
        name="front_lower_band",
    )
    mid_rail_height = grille_bottom - (tray_slot_bottom + tray_slot_height)
    housing.visual(
        Box((0.194, shell_wall, mid_rail_height)),
        origin=Origin(
            xyz=(
                0.0,
                front_plane_y,
                tray_slot_bottom + tray_slot_height + mid_rail_height * 0.5,
            )
        ),
        material=shell_white,
        name="front_mid_rail",
    )
    top_rail_height = shell_body_height - (grille_bottom + grille_height)
    housing.visual(
        Box((0.194, shell_wall, top_rail_height)),
        origin=Origin(
            xyz=(
                0.0,
                front_plane_y,
                grille_bottom + grille_height + top_rail_height * 0.5,
            )
        ),
        material=shell_white,
        name="front_top_rail",
    )

    left_runner_center_x = -(housing_width * 0.5 - shell_wall - 0.015)
    right_runner_center_x = -left_runner_center_x
    housing.visual(
        Box((0.030, 0.180, 0.008)),
        origin=Origin(xyz=(left_runner_center_x, 0.011, 0.004)),
        material=interior_charcoal,
        name="left_tray_runner",
    )
    housing.visual(
        Box((0.030, 0.180, 0.008)),
        origin=Origin(xyz=(right_runner_center_x, 0.011, 0.004)),
        material=interior_charcoal,
        name="right_tray_runner",
    )
    housing.visual(
        Box((0.206, 0.048, 0.006)),
        origin=Origin(xyz=(0.0, -0.0885, 0.003)),
        material=interior_charcoal,
        name="rear_floor",
    )
    grille_depth = 0.004
    grille_outer_width = 0.194
    grille_side_rail_width = 0.010
    grille_frame_height = 0.010
    housing.visual(
        Box((grille_side_rail_width, grille_depth, grille_height)),
        origin=Origin(
            xyz=(
                -(grille_outer_width * 0.5 - grille_side_rail_width * 0.5),
                housing_depth * 0.5 - grille_depth * 0.5,
                grille_bottom + grille_height * 0.5,
            )
        ),
        material=grille_grey,
        name="grille_left_rail",
    )
    housing.visual(
        Box((grille_side_rail_width, grille_depth, grille_height)),
        origin=Origin(
            xyz=(
                grille_outer_width * 0.5 - grille_side_rail_width * 0.5,
                housing_depth * 0.5 - grille_depth * 0.5,
                grille_bottom + grille_height * 0.5,
            )
        ),
        material=grille_grey,
        name="grille_right_rail",
    )
    housing.visual(
        Box((grille_outer_width, grille_depth, grille_frame_height)),
        origin=Origin(
            xyz=(
                0.0,
                housing_depth * 0.5 - grille_depth * 0.5,
                grille_bottom + grille_frame_height * 0.5,
            )
        ),
        material=grille_grey,
        name="grille_lower_rail",
    )
    housing.visual(
        Box((grille_outer_width, grille_depth, grille_frame_height)),
        origin=Origin(
            xyz=(
                0.0,
                housing_depth * 0.5 - grille_depth * 0.5,
                grille_bottom + grille_height - grille_frame_height * 0.5,
            )
        ),
        material=grille_grey,
        name="grille_upper_rail",
    )
    slat_count = 9
    slat_height = 0.006
    slat_width = grille_outer_width - 2.0 * grille_side_rail_width
    slat_gap = (grille_height - 2.0 * grille_frame_height - slat_count * slat_height) / (
        slat_count - 1
    )
    for slat_index in range(slat_count):
        z_center = (
            grille_bottom
            + grille_frame_height
            + slat_height * 0.5
            + slat_index * (slat_height + slat_gap)
        )
        housing.visual(
            Box((slat_width, grille_depth, slat_height)),
            origin=Origin(
                xyz=(
                    0.0,
                    housing_depth * 0.5 - grille_depth * 0.5,
                    z_center,
                )
            ),
            material=grille_grey,
            name=f"grille_slat_{slat_index}",
        )
    housing.visual(
        Box((0.168, 0.014, 0.172)),
        origin=Origin(
            xyz=(
                0.0,
                housing_depth * 0.5 - 0.0105,
                grille_bottom + grille_height * 0.5,
            )
        ),
        material=interior_charcoal,
        name="intake_shadow",
    )
    housing.inertial = Inertial.from_geometry(
        Box((housing_width, housing_depth, housing_height)),
        mass=2.3,
        origin=Origin(xyz=(0.0, 0.0, housing_height * 0.5)),
    )

    filter_tray = model.part("filter_tray")
    filter_tray.visual(
        Box((tray_width, tray_depth, tray_wall)),
        origin=Origin(xyz=(0.0, 0.0, tray_wall * 0.5)),
        material=tray_grey,
        name="tray_base",
    )
    filter_tray.visual(
        Box((tray_wall, tray_depth, 0.024)),
        origin=Origin(xyz=(-(tray_width - tray_wall) * 0.5, 0.0, 0.012)),
        material=tray_grey,
        name="tray_left_wall",
    )
    filter_tray.visual(
        Box((tray_wall, tray_depth, 0.024)),
        origin=Origin(xyz=(((tray_width - tray_wall) * 0.5), 0.0, 0.012)),
        material=tray_grey,
        name="tray_right_wall",
    )
    filter_tray.visual(
        Box((tray_width, tray_wall, 0.024)),
        origin=Origin(xyz=(0.0, -(tray_depth - tray_wall) * 0.5, 0.012)),
        material=tray_grey,
        name="tray_rear_wall",
    )
    filter_tray.visual(
        Box((tray_front_lip_width, tray_front_lip_thickness, tray_front_lip_height)),
        origin=Origin(
            xyz=(
                0.0,
                tray_depth * 0.5 - tray_front_lip_thickness * 0.5,
                tray_front_lip_height * 0.5,
            )
        ),
        material=tray_grey,
        name="tray_front_lip",
    )
    filter_tray.visual(
        Box((0.060, 0.008, 0.006)),
        origin=Origin(
            xyz=(
                0.0,
                tray_depth * 0.5 - tray_front_lip_thickness - 0.003,
                tray_front_lip_height - 0.006,
            )
        ),
        material=tray_grey,
        name="tray_pull_ridge",
    )
    filter_tray.visual(
        Box((0.184, 0.142, 0.032)),
        origin=Origin(xyz=(0.0, -0.002, 0.019)),
        material=filter_green,
        name="filter_block",
    )
    for pleat_index, x_pos in enumerate(
        (-0.074, -0.053, -0.032, -0.011, 0.011, 0.032, 0.053, 0.074)
    ):
        filter_tray.visual(
            Box((0.004, 0.142, 0.007)),
            origin=Origin(xyz=(x_pos, -0.002, 0.0325)),
            material=filter_shadow,
            name=f"filter_pleat_{pleat_index}",
        )
    filter_tray.inertial = Inertial.from_geometry(
        Box((tray_width, tray_depth, 0.041)),
        mass=0.45,
        origin=Origin(xyz=(0.0, 0.0, 0.0205)),
    )

    model.articulation(
        "housing_to_filter_tray",
        ArticulationType.PRISMATIC,
        parent=housing,
        child=filter_tray,
        origin=Origin(
            xyz=(
                0.0,
                housing_depth * 0.5 - tray_depth * 0.5,
                0.008,
            )
        ),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(
            effort=20.0,
            velocity=0.20,
            lower=0.0,
            upper=tray_travel,
        ),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
