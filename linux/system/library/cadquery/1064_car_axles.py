# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, car_axles, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: car_axles

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
def _hub_shell_mesh(name: str):
    """One wheel-hub shell, authored with its mounting face at local x=0."""

    gap = 0.0

    def annular_x(x0: float, length: float, outer_radius: float, bore_radius: float):
        return (
            cq.Workplane("YZ", origin=(x0, 0.0, 0.0))
            .circle(outer_radius)
            .circle(bore_radius)
            .extrude(length)
        )

    # Rear bearing sleeve and broad wheel-mounting flange share the same bore.
    hub = annular_x(gap, 0.108, 0.055, 0.033)
    hub = hub.union(annular_x(gap, 0.045, 0.118, 0.033))

    # A closed grease cap sits beyond the hidden spindle nose, leaving the rear
    # half of the hub as a true clearance bore rather than a solid placeholder.
    hub = hub.union(
        cq.Workplane("YZ", origin=(0.087, 0.0, 0.0)).circle(0.041).extrude(0.028)
    )

    # Five protruding wheel studs make hub spin visually legible.
    stud_radius = 0.008
    stud_circle = 0.079
    for index in range(5):
        angle = 2.0 * math.pi * index / 5.0 + math.radians(18.0)
        y = stud_circle * math.cos(angle)
        z = stud_circle * math.sin(angle)
        stud = (
            cq.Workplane("YZ", origin=(0.040, y, z))
            .circle(stud_radius)
            .extrude(0.041)
        )
        hub = hub.union(stud)

    # A shallow pilot ring at the center of the flange gives the hub a machined
    # bearing-seat silhouette while preserving the spindle bore behind it.
    hub = hub.union(
        cq.Workplane("YZ", origin=(0.045, 0.0, 0.0))
        .circle(0.065)
        .circle(0.035)
        .extrude(0.026)
    )

    return mesh_from_cadquery(hub, name, tolerance=0.0008, angular_tolerance=0.08)
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="de_dion_rear_axle")

    tube_paint = model.material("satin_black_tube", color=(0.02, 0.022, 0.024, 1.0))
    dark_block = model.material("dark_forged_block", color=(0.07, 0.075, 0.078, 1.0))
    machined = model.material("machined_steel", color=(0.62, 0.60, 0.56, 1.0))
    pin_steel = model.material("polished_pin_steel", color=(0.78, 0.76, 0.70, 1.0))

    axle_beam = model.part("axle_beam")

    # Two visible tube halves terminate in the center universal-coupling block,
    # just like a de Dion tube with the center section clamped/welded in place.
    axle_beam.visual(
        Cylinder(radius=0.055, length=0.84),
        origin=Origin(xyz=(-0.51, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=tube_paint,
        name="left_tube",
    )
    axle_beam.visual(
        Cylinder(radius=0.055, length=0.84),
        origin=Origin(xyz=(0.51, 0.0, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=tube_paint,
        name="right_tube",
    )

    axle_beam.visual(
        Box((0.235, 0.185, 0.150)),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=dark_block,
        name="coupling_block",
    )
    axle_beam.visual(
        Box((0.075, 0.290, 0.052)),
        origin=Origin(xyz=(0.0, 0.0, 0.060)),
        material=dark_block,
        name="upper_yoke",
    )
    axle_beam.visual(
        Box((0.075, 0.290, 0.052)),
        origin=Origin(xyz=(0.0, 0.0, -0.060)),
        material=dark_block,
        name="lower_yoke",
    )
    axle_beam.visual(
        Cylinder(radius=0.018, length=0.330),
        origin=Origin(xyz=(0.0, 0.0, 0.0), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=pin_steel,
        name="cross_pin_y",
    )
    axle_beam.visual(
        Cylinder(radius=0.015, length=0.185),
        origin=Origin(xyz=(0.0, 0.0, 0.0)),
        material=pin_steel,
        name="cross_pin_z",
    )

    # Outer forged end flanges and hidden stub spindles.  The thin shafts pass
    # through the hub bores; the hub joint origins sit on the flange faces.
    flange_face_x = 0.940
    flange_thickness = 0.055
    axle_beam.visual(
        Cylinder(radius=0.080, length=flange_thickness),
        origin=Origin(
            xyz=(flange_face_x - flange_thickness / 2.0, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=machined,
        name="right_spindle_flange",
    )
    axle_beam.visual(
        Cylinder(radius=0.044, length=0.075),
        origin=Origin(
            xyz=(flange_face_x - flange_thickness - 0.030, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=machined,
        name="right_neck",
    )
    axle_beam.visual(
        Cylinder(radius=0.024, length=0.074),
        origin=Origin(
            xyz=(flange_face_x + 0.074 / 2.0, 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=pin_steel,
        name="right_spindle_shaft",
    )
    axle_beam.visual(
        Cylinder(radius=0.080, length=flange_thickness),
        origin=Origin(
            xyz=(-(flange_face_x - flange_thickness / 2.0), 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=machined,
        name="left_spindle_flange",
    )
    axle_beam.visual(
        Cylinder(radius=0.044, length=0.075),
        origin=Origin(
            xyz=(-(flange_face_x - flange_thickness - 0.030), 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=machined,
        name="left_neck",
    )
    axle_beam.visual(
        Cylinder(radius=0.024, length=0.074),
        origin=Origin(
            xyz=(-(flange_face_x + 0.074 / 2.0), 0.0, 0.0),
            rpy=(0.0, math.pi / 2.0, 0.0),
        ),
        material=pin_steel,
        name="left_spindle_shaft",
    )

    right_hub = model.part("right_hub")
    right_hub.visual(
        _hub_shell_mesh("right_hub_shell"),
        origin=Origin(),
        material=machined,
        name="hub_shell",
    )

    left_hub = model.part("left_hub")
    left_hub.visual(
        _hub_shell_mesh("left_hub_shell"),
        origin=Origin(),
        material=machined,
        name="hub_shell",
    )

    model.articulation(
        "right_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=axle_beam,
        child=right_hub,
        origin=Origin(xyz=(flange_face_x, 0.0, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=180.0, velocity=55.0),
    )
    model.articulation(
        "left_hub_spin",
        ArticulationType.CONTINUOUS,
        parent=axle_beam,
        child=left_hub,
        # Rotate the joint frame so the same local hub mesh projects outward.
        origin=Origin(xyz=(-flange_face_x, 0.0, 0.0), rpy=(0.0, 0.0, math.pi)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=180.0, velocity=55.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
