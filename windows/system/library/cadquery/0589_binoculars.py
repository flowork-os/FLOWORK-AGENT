# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, binoculars, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: binoculars

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
import cadquery as cq
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="stabilized_binoculars")

    black_rubber = model.material("black_rubber", rgba=(0.15, 0.15, 0.15, 1.0))
    dark_gray = model.material("dark_gray", rgba=(0.25, 0.25, 0.25, 1.0))
    glass = model.material("glass", rgba=(0.1, 0.1, 0.3, 0.8))

    # Dimensions
    hinge_length = 0.08
    hinge_radius = 0.008
    prism_box_width = 0.04
    prism_box_length = 0.07
    prism_box_height = 0.035
    objective_length = 0.06
    objective_radius = 0.022
    eyepiece_length = 0.04
    eyepiece_radius = 0.016
    barrel_offset_x = 0.035
    barrel_offset_z = -0.01

    def make_half(is_left: bool):
        sign = -1 if is_left else 1
        
        # Hinge barrels (interleaved)
        hinge = cq.Workplane("XZ").workplane(offset=-hinge_length/2)
        if is_left:
            # Left gets front and back hinge segments
            hinge = hinge.center(0, 0).circle(hinge_radius).extrude(hinge_length * 0.3)
            hinge = hinge.faces(">Y").workplane().center(0, 0).circle(hinge_radius).extrude(hinge_length * 0.4).cut(hinge) # wait, just add another cylinder
            # Let's do it simpler
            h1 = cq.Workplane("XZ").workplane(offset=hinge_length/2 - hinge_length*0.3).circle(hinge_radius).extrude(hinge_length*0.3)
            h2 = cq.Workplane("XZ").workplane(offset=-hinge_length/2).circle(hinge_radius).extrude(hinge_length*0.3)
            hinge_parts = h1.union(h2)
        else:
            # Right gets middle hinge segment
            hinge_parts = cq.Workplane("XZ").workplane(offset=-hinge_length/2 + hinge_length*0.3).circle(hinge_radius).extrude(hinge_length*0.4)

        # Prism block (the "stabilizing prism block" half)
        # We want it to connect from the hinge to the barrel
        prism_center_x = sign * (prism_box_width / 2 + 0.005)
        prism = cq.Workplane("XY").workplane(offset=barrel_offset_z).center(prism_center_x, 0).box(prism_box_width, prism_box_length, prism_box_height)
        
        # Bridge arm connecting hinge to prism block
        arm = cq.Workplane("XY").workplane(offset=0).center(sign * 0.015, 0).box(0.03, prism_box_length * 0.8, hinge_radius * 2)
        
        # Objective barrel
        obj_barrel = cq.Workplane("XZ").workplane(offset=prism_box_length/2).center(sign * barrel_offset_x, barrel_offset_z).circle(objective_radius).extrude(objective_length)
        
        # Eyepiece
        eyepiece = cq.Workplane("XZ").workplane(offset=-prism_box_length/2 - eyepiece_length).center(sign * barrel_offset_x, barrel_offset_z).circle(eyepiece_radius).extrude(eyepiece_length)
        
        # Combine
        body = hinge_parts.union(prism).union(arm).union(obj_barrel).union(eyepiece)
        
        # Fillet some edges to make it look organic
        # body = body.edges("|Y").fillet(0.005) # might fail, skip for now
        
        # Lenses
        obj_lens = cq.Workplane("XZ").workplane(offset=prism_box_length/2 + objective_length - 0.002).center(sign * barrel_offset_x, barrel_offset_z).circle(objective_radius - 0.002).extrude(0.002)
        eye_lens = cq.Workplane("XZ").workplane(offset=-prism_box_length/2 - eyepiece_length).center(sign * barrel_offset_x, barrel_offset_z).circle(eyepiece_radius - 0.002).extrude(0.002)
        
        return body, obj_lens, eye_lens

    left_body, left_obj, left_eye = make_half(True)
    right_body, right_obj, right_eye = make_half(False)

    # Focus wheel with a shaft extending into the hinge barrel
    wheel_radius = 0.012
    wheel_length = 0.015
    shaft_radius = 0.004
    shaft_length = 0.01
    
    wheel_body = cq.Workplane("XZ").workplane(offset=-hinge_length/2 - wheel_length).circle(wheel_radius).extrude(wheel_length)
    shaft = cq.Workplane("XZ").workplane(offset=-hinge_length/2).circle(shaft_radius).extrude(shaft_length)
    wheel = wheel_body.union(shaft)

    left_side = model.part("left_side")
    left_side.visual(mesh_from_cadquery(left_body, "left_body"), material=black_rubber)
    left_side.visual(mesh_from_cadquery(left_obj, "left_obj"), material=glass)
    left_side.visual(mesh_from_cadquery(left_eye, "left_eye"), material=glass)

    right_side = model.part("right_side")
    right_side.visual(mesh_from_cadquery(right_body, "right_body"), material=black_rubber)
    right_side.visual(mesh_from_cadquery(right_obj, "right_obj"), material=glass)
    right_side.visual(mesh_from_cadquery(right_eye, "right_eye"), material=glass)

    focus_knob = model.part("focus_wheel")
    focus_knob.visual(mesh_from_cadquery(wheel, "wheel"), material=dark_gray)

    # Articulations
    # The bridge hinge adjusts IPD. 
    # Left side is root. Right side hinges around Y axis (X=0, Z=0).
    model.articulation(
        "bridge_hinge",
        ArticulationType.REVOLUTE,
        parent=left_side,
        child=right_side,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(lower=-0.2, upper=0.4, effort=5.0, velocity=1.0)
    )

    # Focus wheel rotates continuously
    model.articulation(
        "focus_joint",
        ArticulationType.CONTINUOUS,
        parent=left_side,
        child=focus_knob,
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=5.0)
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
