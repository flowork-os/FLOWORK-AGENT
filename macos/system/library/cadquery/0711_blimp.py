# [FL_INDEX: keywords="cadquery, open_cascade, python_cad, blimp, parametric_solid" | COT="Parametric CadQuery Python solid from 3DCodeverse"]
# Component: blimp

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

class Sphere:
    __slots__ = ("radius",)

    def __init__(self, radius):
        self.radius = float(radius)

    def _cq(self):
        return cq.Solid.makeSphere(self.radius, angleDegrees1=-90, angleDegrees2=90,
                                   angleDegrees3=360)

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
HULL_LENGTH = 14.0
def _envelope_shape() -> cq.Workplane:
    sections = [
        (0.0, 0.03),
        (0.7, 0.30),
        (1.6, 0.78),
        (3.0, 1.23),
        (5.0, 1.52),
        (7.0, 1.60),
        (9.0, 1.50),
        (11.0, 1.18),
        (12.5, 0.66),
        (13.5, 0.20),
        (14.0, 0.03),
    ]

    body = cq.Workplane("YZ").circle(sections[0][1])
    previous_x = sections[0][0]
    for x_pos, radius in sections[1:]:
        body = body.workplane(offset=x_pos - previous_x).circle(radius)
        previous_x = x_pos

    return body.loft(combine=True, clean=True).translate((-HULL_LENGTH / 2.0, 0.0, 0.0))
def _gondola_shape() -> cq.Workplane:
    cabin = (
        cq.Workplane("XY")
        .box(3.1, 1.05, 0.92)
        .edges("|Z")
        .fillet(0.08)
        .translate((0.0, 0.0, -0.46))
    )
    nose_cap = (
        cq.Workplane("YZ")
        .circle(0.34)
        .workplane(offset=0.34)
        .circle(0.20)
        .loft(combine=True, clean=True)
        .translate((1.38, 0.0, -0.43))
    )
    return cabin.union(nose_cap)
def _top_fin_shape() -> cq.Workplane:
    profile = [
        (0.05, 0.00),
        (-0.20, 1.18),
        (-0.62, 1.02),
        (-0.62, 0.22),
        (-0.12, 0.00),
    ]
    return cq.Workplane("XZ").polyline(profile).close().extrude(0.10, both=True)
def _bottom_fin_shape() -> cq.Workplane:
    profile = [
        (0.05, 0.00),
        (-0.12, 0.00),
        (-0.62, -0.22),
        (-0.62, -1.02),
        (-0.20, -1.18),
    ]
    return cq.Workplane("XZ").polyline(profile).close().extrude(0.10, both=True)
def _horizontal_fin_shape(side_sign: float) -> cq.Workplane:
    profile = [
        (0.05, 0.00),
        (-0.12, 0.00),
        (-0.60, 0.20 * side_sign),
        (-0.60, 0.92 * side_sign),
        (-0.16, 1.18 * side_sign),
    ]
    return cq.Workplane("XY").polyline(profile).close().extrude(0.10, both=True)
def _rudder_shape() -> cq.Workplane:
    profile = [
        (0.00, -0.40),
        (-0.34, -0.48),
        (-0.40, 0.40),
        (0.00, 0.40),
    ]
    return cq.Workplane("XZ").polyline(profile).close().extrude(0.08, both=True)
def _elevator_shape() -> cq.Workplane:
    profile = [
        (0.00, -0.38),
        (-0.42, -0.46),
        (-0.36, 0.46),
        (0.00, 0.38),
    ]
    return cq.Workplane("XY").polyline(profile).close().extrude(0.08, both=True)
def _pod_shape(side_sign: float) -> cq.Workplane:
    pylon = cq.Workplane("XY").box(0.32, 0.44, 0.18).translate((0.00, 0.22 * side_sign, 0.00))
    nacelle = (
        cq.Workplane("YZ").cylinder(0.46, 0.10).translate((0.00, 0.53 * side_sign, 0.00))
        .union(cq.Workplane("XY").sphere(0.10).translate((0.23, 0.53 * side_sign, 0.00)))
        .union(cq.Workplane("XY").sphere(0.07).translate((-0.23, 0.53 * side_sign, 0.00)))
    )
    return pylon.union(nacelle)
def _add_propeller(part, material) -> None:
    part.visual(
        Cylinder(radius=0.04, length=0.10),
        origin=Origin(rpy=(0.0, math.pi / 2.0, 0.0)),
        material=material,
        name="hub",
    )
    part.visual(
        Sphere(radius=0.045),
        origin=Origin(xyz=(0.055, 0.0, 0.0)),
        material=material,
        name="spinner",
    )
    part.visual(
        Box((0.028, 0.62, 0.10)),
        origin=Origin(rpy=(0.0, 0.24, 0.0)),
        material=material,
        name="blade_y",
    )
    part.visual(
        Box((0.028, 0.10, 0.56)),
        origin=Origin(rpy=(0.0, -0.18, 0.0)),
        material=material,
        name="blade_z",
    )
def build_object_model() -> ArticulatedObject:
    model = ArticulatedObject(name="communications_blimp")

    envelope_mat = model.material("envelope_fabric", rgba=(0.91, 0.93, 0.95, 1.0))
    frame_mat = model.material("frame_grey", rgba=(0.46, 0.50, 0.54, 1.0))
    cabin_mat = model.material("cabin_grey", rgba=(0.32, 0.36, 0.40, 1.0))
    tail_mat = model.material("tail_orange", rgba=(0.88, 0.49, 0.20, 1.0))
    control_mat = model.material("control_red", rgba=(0.74, 0.25, 0.18, 1.0))
    glass_mat = model.material("window_tint", rgba=(0.16, 0.23, 0.28, 1.0))
    tire_mat = model.material("tire_black", rgba=(0.10, 0.10, 0.11, 1.0))
    metal_mat = model.material("metal_dark", rgba=(0.18, 0.19, 0.20, 1.0))

    envelope = model.part("envelope")
    envelope.visual(
        mesh_from_cadquery(_envelope_shape(), "blimp_hull"),
        material=envelope_mat,
        name="hull",
    )
    envelope.visual(
        Box((2.4, 0.56, 0.18)),
        origin=Origin(xyz=(0.0, 0.0, -1.48)),
        material=frame_mat,
        name="keel",
    )
    for index, (x_pos, y_pos) in enumerate(((-0.80, -0.28), (-0.80, 0.28), (0.80, -0.28), (0.80, 0.28))):
        envelope.visual(
            Cylinder(radius=0.045, length=0.33),
            origin=Origin(xyz=(x_pos, y_pos, -1.735)),
            material=frame_mat,
            name=f"suspension_{index}",
        )
    envelope.visual(
        Box((0.55, 0.16, 0.36)),
        origin=Origin(xyz=(-5.65, 0.0, 0.83)),
        material=frame_mat,
        name="top_mount",
    )
    envelope.visual(
        Box((0.55, 0.16, 0.36)),
        origin=Origin(xyz=(-5.65, 0.0, -0.83)),
        material=frame_mat,
        name="bottom_mount",
    )
    envelope.visual(
        Box((0.55, 0.36, 0.16)),
        origin=Origin(xyz=(-5.65, -0.83, 0.0)),
        material=frame_mat,
        name="port_mount",
    )
    envelope.visual(
        Box((0.55, 0.36, 0.16)),
        origin=Origin(xyz=(-5.65, 0.83, 0.0)),
        material=frame_mat,
        name="starboard_mount",
    )

    gondola = model.part("gondola")
    gondola.visual(
        mesh_from_cadquery(_gondola_shape(), "equipment_gondola"),
        material=cabin_mat,
        name="cabin",
    )
    gondola.visual(
        Box((0.04, 0.62, 0.22)),
        origin=Origin(xyz=(1.55, 0.0, -0.22)),
        material=glass_mat,
        name="front_window",
    )
    gondola.visual(
        Box((0.12, 0.05, 0.24)),
        origin=Origin(xyz=(-1.12, -0.10, -1.04)),
        material=frame_mat,
        name="fork_port",
    )
    gondola.visual(
        Box((0.12, 0.05, 0.24)),
        origin=Origin(xyz=(-1.12, 0.10, -1.04)),
        material=frame_mat,
        name="fork_starboard",
    )
    gondola.visual(
        Box((0.16, 0.28, 0.06)),
        origin=Origin(xyz=(-1.12, 0.0, -0.90)),
        material=frame_mat,
        name="fork_bridge",
    )
    gondola.visual(
        Cylinder(radius=0.015, length=0.06),
        origin=Origin(xyz=(-1.12, -0.09, -1.11), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal_mat,
        name="axle_port",
    )
    gondola.visual(
        Cylinder(radius=0.015, length=0.06),
        origin=Origin(xyz=(-1.12, 0.09, -1.11), rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal_mat,
        name="axle_starboard",
    )

    model.articulation(
        "envelope_to_gondola",
        ArticulationType.FIXED,
        parent=envelope,
        child=gondola,
        origin=Origin(xyz=(0.0, 0.0, -1.90)),
    )

    port_pod = model.part("port_pod")
    port_pod.visual(
        mesh_from_cadquery(_pod_shape(-1.0), "port_pod"),
        material=metal_mat,
        name="nacelle",
    )
    port_pod.visual(
        Cylinder(radius=0.024, length=0.10),
        origin=Origin(xyz=(0.36, -0.53, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal_mat,
        name="shaft",
    )

    starboard_pod = model.part("starboard_pod")
    starboard_pod.visual(
        mesh_from_cadquery(_pod_shape(1.0), "starboard_pod"),
        material=metal_mat,
        name="nacelle",
    )
    starboard_pod.visual(
        Cylinder(radius=0.024, length=0.10),
        origin=Origin(xyz=(0.36, 0.53, 0.0), rpy=(0.0, math.pi / 2.0, 0.0)),
        material=metal_mat,
        name="shaft",
    )

    model.articulation(
        "gondola_to_port_pod",
        ArticulationType.FIXED,
        parent=gondola,
        child=port_pod,
        origin=Origin(xyz=(-0.25, -0.525, -0.28)),
    )
    model.articulation(
        "gondola_to_starboard_pod",
        ArticulationType.FIXED,
        parent=gondola,
        child=starboard_pod,
        origin=Origin(xyz=(-0.25, 0.525, -0.28)),
    )

    port_propeller = model.part("port_propeller")
    _add_propeller(port_propeller, material=metal_mat)
    starboard_propeller = model.part("starboard_propeller")
    _add_propeller(starboard_propeller, material=metal_mat)

    model.articulation(
        "port_pod_to_port_propeller",
        ArticulationType.CONTINUOUS,
        parent=port_pod,
        child=port_propeller,
        origin=Origin(xyz=(0.46, -0.53, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=50.0),
    )
    model.articulation(
        "starboard_pod_to_starboard_propeller",
        ArticulationType.CONTINUOUS,
        parent=starboard_pod,
        child=starboard_propeller,
        origin=Origin(xyz=(0.46, 0.53, 0.0)),
        axis=(1.0, 0.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=50.0),
    )

    top_fin = model.part("top_fin")
    top_fin.visual(
        mesh_from_cadquery(_top_fin_shape(), "top_fin"),
        material=tail_mat,
        name="fin",
    )
    top_fin.visual(
        Box((0.18, 0.12, 0.18)),
        origin=Origin(xyz=(-0.05, 0.0, 0.09)),
        material=tail_mat,
        name="root",
    )
    bottom_fin = model.part("bottom_fin")
    bottom_fin.visual(
        mesh_from_cadquery(_bottom_fin_shape(), "bottom_fin"),
        material=tail_mat,
        name="fin",
    )
    bottom_fin.visual(
        Box((0.18, 0.12, 0.18)),
        origin=Origin(xyz=(-0.05, 0.0, -0.09)),
        material=tail_mat,
        name="root",
    )
    port_fin = model.part("port_fin")
    port_fin.visual(
        mesh_from_cadquery(_horizontal_fin_shape(-1.0), "port_fin"),
        material=tail_mat,
        name="fin",
    )
    port_fin.visual(
        Box((0.18, 0.18, 0.12)),
        origin=Origin(xyz=(-0.05, -0.09, 0.0)),
        material=tail_mat,
        name="root",
    )
    starboard_fin = model.part("starboard_fin")
    starboard_fin.visual(
        mesh_from_cadquery(_horizontal_fin_shape(1.0), "starboard_fin"),
        material=tail_mat,
        name="fin",
    )
    starboard_fin.visual(
        Box((0.18, 0.18, 0.12)),
        origin=Origin(xyz=(-0.05, 0.09, 0.0)),
        material=tail_mat,
        name="root",
    )

    model.articulation(
        "envelope_to_top_fin",
        ArticulationType.FIXED,
        parent=envelope,
        child=top_fin,
        origin=Origin(xyz=(-5.65, 0.0, 1.01)),
    )
    model.articulation(
        "envelope_to_bottom_fin",
        ArticulationType.FIXED,
        parent=envelope,
        child=bottom_fin,
        origin=Origin(xyz=(-5.65, 0.0, -1.01)),
    )
    model.articulation(
        "envelope_to_port_fin",
        ArticulationType.FIXED,
        parent=envelope,
        child=port_fin,
        origin=Origin(xyz=(-5.65, -1.01, 0.0)),
    )
    model.articulation(
        "envelope_to_starboard_fin",
        ArticulationType.FIXED,
        parent=envelope,
        child=starboard_fin,
        origin=Origin(xyz=(-5.65, 1.01, 0.0)),
    )

    rudder = model.part("rudder")
    rudder.visual(
        mesh_from_cadquery(_rudder_shape(), "rudder"),
        material=control_mat,
        name="surface",
    )
    port_elevator = model.part("port_elevator")
    port_elevator.visual(
        mesh_from_cadquery(_elevator_shape(), "port_elevator"),
        material=control_mat,
        name="surface",
    )
    starboard_elevator = model.part("starboard_elevator")
    starboard_elevator.visual(
        mesh_from_cadquery(_elevator_shape(), "starboard_elevator"),
        material=control_mat,
        name="surface",
    )

    model.articulation(
        "top_fin_to_rudder",
        ArticulationType.REVOLUTE,
        parent=top_fin,
        child=rudder,
        origin=Origin(xyz=(-0.62, 0.0, 0.62)),
        axis=(0.0, 0.0, 1.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.55, upper=0.55),
    )
    model.articulation(
        "port_fin_to_port_elevator",
        ArticulationType.REVOLUTE,
        parent=port_fin,
        child=port_elevator,
        origin=Origin(xyz=(-0.60, -0.58, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.45, upper=0.45),
    )
    model.articulation(
        "starboard_fin_to_starboard_elevator",
        ArticulationType.REVOLUTE,
        parent=starboard_fin,
        child=starboard_elevator,
        origin=Origin(xyz=(-0.60, 0.58, 0.0)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=8.0, velocity=2.0, lower=-0.45, upper=0.45),
    )

    wheel = model.part("wheel")
    wheel.visual(
        Cylinder(radius=0.17, length=0.08),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=tire_mat,
        name="tire",
    )
    wheel.visual(
        Cylinder(radius=0.07, length=0.12),
        origin=Origin(rpy=(math.pi / 2.0, 0.0, 0.0)),
        material=metal_mat,
        name="hub",
    )

    model.articulation(
        "gondola_to_wheel",
        ArticulationType.CONTINUOUS,
        parent=gondola,
        child=wheel,
        origin=Origin(xyz=(-1.12, 0.0, -1.11)),
        axis=(0.0, 1.0, 0.0),
        motion_limits=MotionLimits(effort=1.0, velocity=20.0),
    )

    return model


# ---- self-contained REST-pose assembly ----
try:
    object_model
except NameError:
    object_model = build_object_model()
result = object_model.to_cq()
