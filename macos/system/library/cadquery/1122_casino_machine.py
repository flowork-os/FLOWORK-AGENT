# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, casino_machine, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: casino_machine

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
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="slant_top_casino_machine")

    # 1. Base Cabinet Shell
    # Profile in YZ plane. X is right, Y is forward, Z is up.
    # Player is at -Y, looking at +Y.
    profile = (
        cq.Workplane("YZ")
        .moveTo(-0.3, 0.0)
        .lineTo(0.4, 0.0)
        .lineTo(0.4, 1.4)
        .lineTo(0.3, 1.4)
        .lineTo(0.0, 0.65)
        .lineTo(-0.3, 0.5)
        .close()
    )
    # Extrude along X (width 0.6). Center on X=0.
    cabinet_shape = profile.extrude(0.6).translate((-0.3, 0, 0)).shell(-0.02)

    # Cut belly opening
    belly_cut = cq.Workplane("XY").box(0.5, 0.2, 0.4).translate((0, -0.3, 0.25))
    cabinet_shape = cabinet_shape.cut(belly_cut)

    # Deck angle and normal
    deck_angle = math.atan2(0.15, 0.3) # ~26.56 deg
    deck_center = (0, -0.15, 0.575)

    # Cut button hole in deck
    button_hole = (
        cq.Workplane("XY")
        .circle(0.03)
        .extrude(0.1)
        .translate((0, 0, -0.05))
        .rotate((0,0,0), (1,0,0), math.degrees(deck_angle))
        .translate(deck_center)
    )
    cabinet_shape = cabinet_shape.cut(button_hole)

    # Screen angle and normal
    screen_angle = math.atan2(0.75, 0.3) # ~68.2 deg
    knob_center = (0.2, 0.05, 0.775)

    # Cut volume knob hole
    knob_hole = (
        cq.Workplane("XY")
        .circle(0.006)
        .extrude(0.1)
        .translate((0, 0, -0.05))
        .rotate((0,0,0), (1,0,0), math.degrees(screen_angle))
        .translate(knob_center)
    )
    cabinet_shape = cabinet_shape.cut(knob_hole)

    base = model.part("base_cabinet")
    base.visual(mesh_from_cadquery(cabinet_shape, "cabinet_shell"), name="cabinet_shell")

    # Add Screen Visual
    screen_geom = cq.Workplane("XY").box(0.5, 0.6, 0.01).translate((0, 0, 0.005))
    base.visual(
        mesh_from_cadquery(screen_geom, "screen_panel"),
        origin=Origin(xyz=(0, 0.15, 1.025), rpy=(screen_angle, 0, 0)),
        name="screen_panel"
    )

    # Add Sleeve Visual to Base
    sleeve_geom = (
        cq.Workplane("XY")
        .circle(0.04).circle(0.03).extrude(0.02)
    )
    deck_origin = Origin(xyz=deck_center, rpy=(deck_angle, 0, 0))
    base.visual(mesh_from_cadquery(sleeve_geom, "spin_button_sleeve"), origin=deck_origin, name="spin_button_sleeve")

    # 2. Belly Door
    belly_door = model.part("belly_door")
    # Hinge at X=0.25, Y=-0.3, Z=0.25
    door_geom = cq.Workplane("XY").box(0.488, 0.018, 0.39).translate((-0.244, 0.01, 0))
    belly_door.visual(mesh_from_cadquery(door_geom, "door_panel"), name="door_panel")
    
    lock_geom = cq.Workplane("XY").circle(0.01).extrude(0.005)
    belly_door.visual(
        mesh_from_cadquery(lock_geom, "door_lock"),
        origin=Origin(xyz=(-0.45, 0.0, 0.1), rpy=(-math.pi/2, 0, 0)),
        name="door_lock"
    )

    model.articulation(
        "belly_door_hinge",
        ArticulationType.REVOLUTE,
        parent=base,
        child=belly_door,
        origin=Origin(xyz=(0.25, -0.3, 0.25)),
        axis=(0, 0, 1),
        motion_limits=MotionLimits(effort=5.0, velocity=1.0, lower=0.0, upper=math.pi/2)
    )

    # 3. Spin Button
    spin_button = model.part("spin_button")
    button_geom = (
        cq.Workplane("XY").circle(0.028).extrude(0.02)
        .add(cq.Workplane("XY").circle(0.03).extrude(-0.05))
    )
    spin_button.visual(
        mesh_from_cadquery(button_geom, "button_cap"),
        origin=Origin(xyz=(0, 0, 0.005)),
        name="button_cap"
    )

    model.articulation(
        "spin_button_press",
        ArticulationType.PRISMATIC,
        parent=base,
        child=spin_button,
        origin=deck_origin,
        axis=(0, 0, 1),
        motion_limits=MotionLimits(effort=1.0, velocity=1.0, lower=-0.005, upper=0.0)
    )

    # 4. Volume Knob
    volume_knob = model.part("volume_knob")
    knob_geom = (
        cq.Workplane("XY")
        .circle(0.015).extrude(0.015)
        .faces(">Z").workplane().circle(0.01).extrude(0.005)
    ).translate((0, 0, 0.01))
    shaft_geom = cq.Workplane("XY").circle(0.005).extrude(0.035).translate((0, 0, -0.025))
    
    volume_knob.visual(mesh_from_cadquery(knob_geom, "knob_cap"), name="knob_cap")
    volume_knob.visual(mesh_from_cadquery(shaft_geom, "knob_shaft"), name="knob_shaft")

    knob_origin = Origin(xyz=knob_center, rpy=(screen_angle, 0, 0))
    model.articulation(
        "volume_turn",
        ArticulationType.CONTINUOUS,
        parent=base,
        child=volume_knob,
        origin=knob_origin,
        axis=(0, 0, 1),
        motion_limits=MotionLimits(effort=0.5, velocity=5.0)
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
