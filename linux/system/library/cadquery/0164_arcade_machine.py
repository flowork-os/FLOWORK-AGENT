# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, arcade_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: arcade_machine

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
TABLE_LENGTH = 0.92
TABLE_WIDTH = 0.66
TOP_HEIGHT = 0.73
BASE_LENGTH = 0.84
BASE_WIDTH = 0.58
BASE_HEIGHT = 0.12
PEDESTAL_LENGTH = 0.78
PEDESTAL_WIDTH = 0.52
PEDESTAL_HEIGHT = 0.42
PEDESTAL_Z0 = BASE_HEIGHT
PEDESTAL_Z1 = PEDESTAL_Z0 + PEDESTAL_HEIGHT
UPPER_HEIGHT = TOP_HEIGHT - PEDESTAL_Z1
UPPER_WALL_THICK = 0.022
SCREEN_FRAME_LENGTH = 0.66
SCREEN_FRAME_WIDTH = 0.42
GLASS_LENGTH = 0.63
GLASS_WIDTH = 0.39
GLASS_THICK = 0.006
WELL_HEIGHT = 0.11
WELL_OUTER_LENGTH = 0.63
WELL_OUTER_WIDTH = 0.39
WELL_INNER_LENGTH = 0.56
WELL_INNER_WIDTH = 0.30
SCREEN_BEZEL_LENGTH = 0.60
SCREEN_BEZEL_WIDTH = 0.34
SCREEN_LENGTH = 0.50
SCREEN_WIDTH = 0.27
SERVICE_OPENING_WIDTH = 0.336
SERVICE_OPENING_HEIGHT = 0.31
SERVICE_OPENING_Z0 = PEDESTAL_Z0 + 0.055
SERVICE_FRAME_X = -(PEDESTAL_LENGTH / 2.0) + (UPPER_WALL_THICK / 2.0)
SERVICE_JAMB_WIDTH = (PEDESTAL_WIDTH - 2.0 * UPPER_WALL_THICK - SERVICE_OPENING_WIDTH) / 2.0
SERVICE_RAIL_HEIGHT = (PEDESTAL_HEIGHT - SERVICE_OPENING_HEIGHT) / 2.0
DOOR_THICK = 0.018
DOOR_WIDTH = 0.332
DOOR_HEIGHT = 0.304
DOOR_BOTTOM = SERVICE_OPENING_Z0 + 0.003
DOOR_HINGE_X = -(PEDESTAL_LENGTH / 2.0) + (DOOR_THICK / 2.0)
DOOR_HINGE_Y = -(DOOR_WIDTH / 2.0)
DOOR_MAX_SWING = 1.55
CONTROL_PANEL_LENGTH = 0.38
CONTROL_PANEL_DEPTH = 0.13
CONTROL_PANEL_THICK = 0.022
CONTROL_RISER_DEPTH = 0.05
CONTROL_RISER_HEIGHT = 0.04
CONTROL_RISER_Y = TABLE_WIDTH / 2.0 + 0.015
CONTROL_PANEL_Y = TABLE_WIDTH / 2.0 + 0.04
CONTROL_PANEL_TOP = TOP_HEIGHT + CONTROL_RISER_HEIGHT + CONTROL_PANEL_THICK
BUTTON_RADIUS = 0.017
BUTTON_CAP_LENGTH = 0.008
BUTTON_REST_OFFSET = 0.008
BUTTON_TRAVEL = 0.0035
BUTTON_XS = (-0.09, 0.0, 0.09)
BUTTON_HOLE_RADIUS = 0.0105
BUTTON_STEM_RADIUS = 0.0085
BUTTON_STEM_LENGTH = 0.026
BUTTON_STEM_CENTER_Z = -0.009
BUTTON_FLANGE_RADIUS = 0.0125
BUTTON_FLANGE_LENGTH = 0.004
BUTTON_FLANGE_CENTER_Z = -0.024
def add_visual(part, geometry, xyz, *, material, name):
    part.visual(geometry, origin=Origin(xyz=xyz), material=material, name=name)
def make_control_shelf():
    shelf = cq.Workplane("XY").box(CONTROL_PANEL_LENGTH, CONTROL_PANEL_DEPTH, CONTROL_PANEL_THICK)
    shelf = (
        shelf.faces(">Z")
        .workplane()
        .pushPoints([(button_x, 0.0) for button_x in BUTTON_XS])
        .circle(BUTTON_HOLE_RADIUS)
        .cutThruAll()
    )
    return shelf
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="cocktail_table_arcade")

    cabinet_black = model.material("cabinet_black", rgba=(0.14, 0.13, 0.12, 1.0))
    cabinet_trim = model.material("cabinet_trim", rgba=(0.22, 0.20, 0.18, 1.0))
    smoked_glass = model.material("smoked_glass", rgba=(0.45, 0.52, 0.56, 0.35))
    screen_black = model.material("screen_black", rgba=(0.03, 0.03, 0.04, 1.0))
    screen_glow = model.material("screen_glow", rgba=(0.09, 0.20, 0.32, 1.0))
    metal = model.material("metal", rgba=(0.62, 0.62, 0.60, 1.0))
    button_red = model.material("button_red", rgba=(0.76, 0.12, 0.14, 1.0))
    button_yellow = model.material("button_yellow", rgba=(0.90, 0.73, 0.14, 1.0))
    button_blue = model.material("button_blue", rgba=(0.13, 0.34, 0.72, 1.0))

    body = model.part("body")

    add_visual(
        body,
        Box((BASE_LENGTH, BASE_WIDTH, BASE_HEIGHT)),
        (0.0, 0.0, BASE_HEIGHT / 2.0),
        material=cabinet_black,
        name="base_plinth",
    )
    add_visual(
        body,
        Box((PEDESTAL_LENGTH, PEDESTAL_WIDTH, 0.02)),
        (0.0, 0.0, PEDESTAL_Z0 + 0.01),
        material=cabinet_trim,
        name="pedestal_floor",
    )
    add_visual(
        body,
        Box((PEDESTAL_LENGTH, UPPER_WALL_THICK, PEDESTAL_HEIGHT)),
        (0.0, PEDESTAL_WIDTH / 2.0 - UPPER_WALL_THICK / 2.0, PEDESTAL_Z0 + PEDESTAL_HEIGHT / 2.0),
        material=cabinet_black,
        name="pedestal_side_0",
    )
    add_visual(
        body,
        Box((PEDESTAL_LENGTH, UPPER_WALL_THICK, PEDESTAL_HEIGHT)),
        (0.0, -(PEDESTAL_WIDTH / 2.0 - UPPER_WALL_THICK / 2.0), PEDESTAL_Z0 + PEDESTAL_HEIGHT / 2.0),
        material=cabinet_black,
        name="pedestal_side_1",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, PEDESTAL_WIDTH - 2.0 * UPPER_WALL_THICK, PEDESTAL_HEIGHT)),
        (PEDESTAL_LENGTH / 2.0 - UPPER_WALL_THICK / 2.0, 0.0, PEDESTAL_Z0 + PEDESTAL_HEIGHT / 2.0),
        material=cabinet_black,
        name="pedestal_end",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, PEDESTAL_WIDTH - 2.0 * UPPER_WALL_THICK, SERVICE_RAIL_HEIGHT)),
        (SERVICE_FRAME_X, 0.0, PEDESTAL_Z1 - SERVICE_RAIL_HEIGHT / 2.0),
        material=cabinet_black,
        name="service_top_rail",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, PEDESTAL_WIDTH - 2.0 * UPPER_WALL_THICK, SERVICE_RAIL_HEIGHT)),
        (SERVICE_FRAME_X, 0.0, PEDESTAL_Z0 + SERVICE_RAIL_HEIGHT / 2.0),
        material=cabinet_black,
        name="service_bottom_rail",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, SERVICE_JAMB_WIDTH, SERVICE_OPENING_HEIGHT)),
        (
            SERVICE_FRAME_X,
            -(SERVICE_OPENING_WIDTH / 2.0 + SERVICE_JAMB_WIDTH / 2.0),
            SERVICE_OPENING_Z0 + SERVICE_OPENING_HEIGHT / 2.0,
        ),
        material=cabinet_black,
        name="service_jamb_0",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, SERVICE_JAMB_WIDTH, SERVICE_OPENING_HEIGHT)),
        (
            SERVICE_FRAME_X,
            SERVICE_OPENING_WIDTH / 2.0 + SERVICE_JAMB_WIDTH / 2.0,
            SERVICE_OPENING_Z0 + SERVICE_OPENING_HEIGHT / 2.0,
        ),
        material=cabinet_black,
        name="service_jamb_1",
    )
    add_visual(
        body,
        Box((TABLE_LENGTH, TABLE_WIDTH, 0.02)),
        (0.0, 0.0, PEDESTAL_Z1 + 0.01),
        material=cabinet_trim,
        name="upper_floor",
    )
    add_visual(
        body,
        Box((TABLE_LENGTH, UPPER_WALL_THICK, UPPER_HEIGHT)),
        (0.0, TABLE_WIDTH / 2.0 - UPPER_WALL_THICK / 2.0, PEDESTAL_Z1 + UPPER_HEIGHT / 2.0),
        material=cabinet_black,
        name="upper_side_0",
    )
    add_visual(
        body,
        Box((TABLE_LENGTH, UPPER_WALL_THICK, UPPER_HEIGHT)),
        (0.0, -(TABLE_WIDTH / 2.0 - UPPER_WALL_THICK / 2.0), PEDESTAL_Z1 + UPPER_HEIGHT / 2.0),
        material=cabinet_black,
        name="upper_side_1",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, TABLE_WIDTH - 2.0 * UPPER_WALL_THICK, UPPER_HEIGHT)),
        (TABLE_LENGTH / 2.0 - UPPER_WALL_THICK / 2.0, 0.0, PEDESTAL_Z1 + UPPER_HEIGHT / 2.0),
        material=cabinet_black,
        name="upper_end_0",
    )
    add_visual(
        body,
        Box((UPPER_WALL_THICK, TABLE_WIDTH - 2.0 * UPPER_WALL_THICK, UPPER_HEIGHT)),
        (-(TABLE_LENGTH / 2.0 - UPPER_WALL_THICK / 2.0), 0.0, PEDESTAL_Z1 + UPPER_HEIGHT / 2.0),
        material=cabinet_black,
        name="upper_end_1",
    )
    add_visual(
        body,
        Box((TABLE_LENGTH - SCREEN_FRAME_LENGTH, TABLE_WIDTH, 0.022)),
        (SCREEN_FRAME_LENGTH / 2.0 + (TABLE_LENGTH - SCREEN_FRAME_LENGTH) / 4.0, 0.0, TOP_HEIGHT - 0.011),
        material=cabinet_trim,
        name="top_rim_0",
    )
    add_visual(
        body,
        Box((TABLE_LENGTH - SCREEN_FRAME_LENGTH, TABLE_WIDTH, 0.022)),
        (-(SCREEN_FRAME_LENGTH / 2.0 + (TABLE_LENGTH - SCREEN_FRAME_LENGTH) / 4.0), 0.0, TOP_HEIGHT - 0.011),
        material=cabinet_trim,
        name="top_rim_1",
    )
    add_visual(
        body,
        Box((SCREEN_FRAME_LENGTH, TABLE_WIDTH - SCREEN_FRAME_WIDTH, 0.022)),
        (0.0, SCREEN_FRAME_WIDTH / 2.0 + (TABLE_WIDTH - SCREEN_FRAME_WIDTH) / 4.0, TOP_HEIGHT - 0.011),
        material=cabinet_trim,
        name="top_rim_2",
    )
    add_visual(
        body,
        Box((SCREEN_FRAME_LENGTH, TABLE_WIDTH - SCREEN_FRAME_WIDTH, 0.022)),
        (0.0, -(SCREEN_FRAME_WIDTH / 2.0 + (TABLE_WIDTH - SCREEN_FRAME_WIDTH) / 4.0), TOP_HEIGHT - 0.011),
        material=cabinet_trim,
        name="top_rim_3",
    )
    add_visual(
        body,
        Box((GLASS_LENGTH, GLASS_WIDTH, GLASS_THICK)),
        (0.0, 0.0, TOP_HEIGHT - GLASS_THICK / 2.0),
        material=smoked_glass,
        name="glass_top",
    )
    add_visual(
        body,
        Box((WELL_OUTER_LENGTH, WELL_OUTER_WIDTH - WELL_INNER_WIDTH, WELL_HEIGHT)),
        (0.0, WELL_INNER_WIDTH / 2.0 + (WELL_OUTER_WIDTH - WELL_INNER_WIDTH) / 4.0, TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT / 2.0),
        material=cabinet_trim,
        name="well_wall_0",
    )
    add_visual(
        body,
        Box((WELL_OUTER_LENGTH, WELL_OUTER_WIDTH - WELL_INNER_WIDTH, WELL_HEIGHT)),
        (0.0, -(WELL_INNER_WIDTH / 2.0 + (WELL_OUTER_WIDTH - WELL_INNER_WIDTH) / 4.0), TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT / 2.0),
        material=cabinet_trim,
        name="well_wall_1",
    )
    add_visual(
        body,
        Box((WELL_OUTER_LENGTH - WELL_INNER_LENGTH, WELL_INNER_WIDTH, WELL_HEIGHT)),
        (WELL_INNER_LENGTH / 2.0 + (WELL_OUTER_LENGTH - WELL_INNER_LENGTH) / 4.0, 0.0, TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT / 2.0),
        material=cabinet_trim,
        name="well_wall_2",
    )
    add_visual(
        body,
        Box((WELL_OUTER_LENGTH - WELL_INNER_LENGTH, WELL_INNER_WIDTH, WELL_HEIGHT)),
        (-(WELL_INNER_LENGTH / 2.0 + (WELL_OUTER_LENGTH - WELL_INNER_LENGTH) / 4.0), 0.0, TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT / 2.0),
        material=cabinet_trim,
        name="well_wall_3",
    )
    add_visual(
        body,
        Box((SCREEN_BEZEL_LENGTH, SCREEN_BEZEL_WIDTH, 0.012)),
        (0.0, 0.0, TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT - 0.006),
        material=screen_black,
        name="screen_bezel",
    )
    add_visual(
        body,
        Box((SCREEN_LENGTH, SCREEN_WIDTH, 0.004)),
        (0.0, 0.0, TOP_HEIGHT - GLASS_THICK - WELL_HEIGHT - 0.001),
        material=screen_glow,
        name="screen_surface",
    )
    add_visual(
        body,
        Box((0.012, 0.008, 0.07)),
        (DOOR_HINGE_X - 0.003, DOOR_HINGE_Y - 0.004, DOOR_BOTTOM + 0.06),
        material=metal,
        name="hinge_leaf_0",
    )
    add_visual(
        body,
        Box((0.012, 0.008, 0.07)),
        (DOOR_HINGE_X - 0.003, DOOR_HINGE_Y - 0.004, DOOR_BOTTOM + DOOR_HEIGHT - 0.06),
        material=metal,
        name="hinge_leaf_1",
    )
    add_visual(
        body,
        Box((CONTROL_PANEL_LENGTH, CONTROL_RISER_DEPTH, CONTROL_RISER_HEIGHT)),
        (0.0, CONTROL_RISER_Y, TOP_HEIGHT + CONTROL_RISER_HEIGHT / 2.0),
        material=cabinet_black,
        name="control_riser",
    )
    add_visual(
        body,
        mesh_from_cadquery(make_control_shelf(), "control_shelf"),
        (0.0, CONTROL_PANEL_Y, TOP_HEIGHT + CONTROL_RISER_HEIGHT + CONTROL_PANEL_THICK / 2.0),
        material=cabinet_trim,
        name="control_shelf",
    )
    add_visual(
        body,
        Box((CONTROL_PANEL_LENGTH, 0.018, 0.07)),
        (0.0, CONTROL_PANEL_Y + CONTROL_PANEL_DEPTH / 2.0 - 0.009, TOP_HEIGHT + 0.035),
        material=cabinet_black,
        name="control_fascia",
    )

    door = model.part("service_door")
    add_visual(
        door,
        Box((DOOR_THICK, DOOR_WIDTH, DOOR_HEIGHT)),
        (0.0, DOOR_WIDTH / 2.0, DOOR_HEIGHT / 2.0),
        material=cabinet_trim,
        name="door_panel",
    )
    add_visual(
        door,
        Box((0.028, 0.014, 0.07)),
        (-0.018, DOOR_WIDTH - 0.05, DOOR_HEIGHT * 0.55),
        material=metal,
        name="door_pull",
    )

    model.articulation(
        "door_hinge",
        ArticulationType.REVOLUTE,
        parent=body,
        child=door,
        origin=Origin(xyz=(DOOR_HINGE_X, DOOR_HINGE_Y, DOOR_BOTTOM)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(
            effort=12.0,
            velocity=1.5,
            lower=0.0,
            upper=DOOR_MAX_SWING,
        ),
    )

    button_materials = (button_red, button_yellow, button_blue)
    for index, (button_x, button_material) in enumerate(zip(BUTTON_XS, button_materials)):
        button = model.part(f"button_{index}")
        add_visual(
            button,
            Cylinder(radius=BUTTON_RADIUS, length=BUTTON_CAP_LENGTH),
            (0.0, 0.0, BUTTON_REST_OFFSET),
            material=button_material,
            name="button_cap",
        )
        add_visual(
            button,
            Cylinder(radius=BUTTON_STEM_RADIUS, length=BUTTON_STEM_LENGTH),
            (0.0, 0.0, BUTTON_STEM_CENTER_Z),
            material=metal,
            name="button_stem",
        )
        add_visual(
            button,
            Cylinder(radius=BUTTON_FLANGE_RADIUS, length=BUTTON_FLANGE_LENGTH),
            (0.0, 0.0, BUTTON_FLANGE_CENTER_Z),
            material=metal,
            name="button_flange",
        )
        model.articulation(
            f"button_{index}_slide",
            ArticulationType.PRISMATIC,
            parent=body,
            child=button,
            origin=Origin(xyz=(button_x, CONTROL_PANEL_Y, CONTROL_PANEL_TOP)),
            axis=(0.0, 0.0, -1.0),
            motion_limits=MotionLimits(
                effort=8.0,
                velocity=0.08,
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
