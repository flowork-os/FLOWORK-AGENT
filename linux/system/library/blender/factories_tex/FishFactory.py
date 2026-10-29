# [FL_INDEX: keywords="blender_factory, procedural_3d, FishFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FishFactory | Category: factories_tex
# Prompt: A fish rendered as a textured 3D model. The creature has a classic oval, laterally compressed body shape with a smooth, matte periwinkle blue-gray surface coloring with subtle cloud-like variation. Multiple fins are prominent: a large fan-shaped dorsal fin and caudal (tail) fin with golden-brown ribbed fin rays, paired pectoral and pelvic fins, and a small anal fin — all with the characteristic golden-brown striped ray pattern contrasting against the blue-gray body. A small black circular eye is visible on the rounded head, and a small pointed mouth opens at the tip of the snout.

import os
import math
import bmesh
import bpy
import numpy as np
from mathutils import Euler as BEuler
from mathutils import Matrix, Vector
from scipy.interpolate import BSpline


def _load_templates():
    """Load all 6 fish body NURBS templates, each shape (9, 8, 3)."""

    templates = {}

    templates["body_fish_bluefish"] = np.array([
        3.71000767e-02, 1.93054475e-05,-1.77929327e-02, 3.71024609e-02, 1.93054475e-05,-1.77483000e-02, 3.71047258e-02, 1.93054475e-05,-1.77036636e-02, 3.71047258e-02, 1.03878342e-07,-1.77036636e-02, 3.71047258e-02,-1.90976953e-05,-1.77036636e-02, 3.71024609e-02,-1.90976953e-05,-1.77483000e-02, 3.71000767e-02,-1.90976953e-05,-1.77929327e-02, 3.71000767e-02, 1.03878378e-07,-1.77929327e-02,
        3.32365036e-02, 2.50130575e-02,-5.86516298e-02, 3.71024609e-02, 3.84033285e-02,-1.77483186e-02, 4.18156385e-02, 1.86112225e-02, 3.34436074e-02, 4.18156385e-02, 1.21951476e-07, 7.15177506e-02, 4.18156385e-02,-1.86110102e-02, 3.34436074e-02, 3.71024609e-02,-3.84031013e-02,-1.77483335e-02, 3.32365036e-02,-2.50128228e-02,-5.86516298e-02, 3.32365036e-02, 1.21951476e-07,-9.09675509e-02,
        4.44417655e-01, 5.49747497e-02,-1.24393225e-01, 4.38329518e-01, 8.44045058e-02,-7.43677318e-02, 4.47070599e-01, 4.09045033e-02, 9.05237976e-02, 4.47070599e-01, 8.52048397e-08, 1.41270205e-01, 4.47070599e-01,-4.09043133e-02, 9.05237976e-02, 4.38329577e-01,-8.44043344e-02,-7.43677169e-02, 4.44417596e-01,-5.49745187e-02,-1.24393225e-01, 4.55885053e-01, 1.04308128e-07,-1.93103746e-01,
        7.59379208e-01, 6.05770275e-02,-1.92256719e-01, 7.50482798e-01, 9.30058882e-02,-7.73598701e-02, 7.59379208e-01, 3.73214707e-02, 1.54069200e-01, 7.59379208e-01, 8.03172588e-08, 2.48082638e-01, 7.59379208e-01,-3.73213105e-02, 1.54069200e-01, 7.50482798e-01,-9.30057541e-02,-7.73598701e-02, 7.59379208e-01,-6.05768375e-02,-1.92256719e-01, 7.59379208e-01, 8.03172588e-08,-2.98536539e-01,
        1.17731130e+00, 9.87295657e-02,-1.71696946e-01, 1.17731130e+00, 1.27242103e-01,-2.92101800e-02, 1.17731130e+00, 7.97584355e-02, 1.55281499e-01, 1.17731130e+00, 8.87513161e-08, 2.47278094e-01, 1.17731130e+00,-7.97582567e-02, 1.55281499e-01, 1.17731130e+00,-1.27241880e-01,-2.92100869e-02, 1.17731130e+00,-9.87294093e-02,-1.71696946e-01, 1.17731130e+00, 7.62939453e-08,-2.64743954e-01,
        1.38404822e+00, 1.00305736e-01,-1.64997101e-01, 1.38404822e+00, 1.29273459e-01,-2.41131373e-02, 1.38404822e+00, 5.78281507e-02, 1.29120216e-01, 1.38404822e+00, 1.04308128e-07, 2.21116811e-01, 1.38404822e+00,-5.78279495e-02, 1.29120216e-01, 1.38404822e+00,-1.29273161e-01,-2.41131559e-02, 1.38404822e+00,-1.00305520e-01,-1.64997101e-01, 1.38404822e+00, 1.04308128e-07,-2.54413307e-01,
        1.62378681e+00, 9.79986638e-02,-1.33716837e-01, 1.62378681e+00, 9.39294770e-02,-2.22482085e-02, 1.62378681e+00, 5.32889031e-02, 8.81245732e-02, 1.62378681e+00, 1.04308128e-07, 1.67973071e-01, 1.62378681e+00,-5.32886386e-02, 8.81245732e-02, 1.62378681e+00,-9.39292982e-02,-2.22482085e-02, 1.62378681e+00,-9.79984775e-02,-1.33716866e-01, 1.62378681e+00, 1.04308128e-07,-2.06181496e-01,
        1.94139814e+00, 2.26888359e-02,-2.68203951e-02, 1.94139814e+00, 2.93813832e-02, 1.05916699e-02, 1.94139814e+00, 1.65814385e-02, 4.31793891e-02, 1.94139814e+00, 5.60283661e-06, 5.59160300e-02, 1.94139814e+00,-1.65806878e-02, 4.31793891e-02, 1.94139814e+00,-2.93802656e-02, 1.05916699e-02, 1.94139814e+00,-2.26879809e-02,-2.68203951e-02, 1.94139814e+00, 5.60283661e-06,-3.47316191e-02,
        1.94139814e+00, 1.42812170e-04, 8.43491033e-03, 1.94139814e+00, 1.42812170e-04, 8.65517929e-03, 1.94139814e+00, 1.42812170e-04, 8.87544826e-03, 1.94139814e+00, 1.78813934e-08, 8.87544826e-03, 1.94139814e+00,-1.42762437e-04, 8.87544826e-03, 1.94139814e+00,-1.42762437e-04, 8.65517929e-03, 1.94139814e+00,-1.42762437e-04, 8.43491033e-03, 1.94139814e+00, 1.78813934e-08, 8.43491033e-03,
    ]).reshape(9, 8, 3)

    templates["body_fish_crappie"] = np.array([
        -1.12690032e-03, 1.93054475e-05,-3.37159634e-04,-1.12483930e-03, 1.93054475e-05,-2.92530656e-04,-1.12288049e-03, 1.93054475e-05,-2.47888640e-04,-1.12288049e-03, 1.07437372e-07,-2.47888640e-04,-1.12288049e-03,-1.90976953e-05,-2.47888640e-04,-1.12483930e-03,-1.90976953e-05,-2.92530656e-04,-1.12690032e-03,-1.90976953e-05,-3.37159634e-04,-1.12690032e-03, 1.07437372e-07,-3.37159634e-04,
        -4.46929038e-03, 1.74986105e-02,-5.32675683e-02,-1.12483930e-03, 3.84033285e-02,-2.92551145e-04, 2.95256451e-03, 1.74986105e-02, 6.44369125e-02, 2.95256451e-03, 1.21951476e-07, 8.89735222e-02, 2.95256451e-03,-1.74984410e-02, 6.44369125e-02,-1.12483930e-03,-3.84031013e-02,-2.92551145e-04,-4.46929038e-03,-1.74984410e-02,-5.32675683e-02,-4.46929038e-03, 1.21951476e-07,-7.35117793e-02,
        3.23606938e-01, 2.78978776e-02,-8.92594308e-02, 3.19786400e-01, 6.12261221e-02,-2.74386909e-02, 3.25271755e-01, 3.31869461e-02, 1.06381141e-01, 3.25271755e-01, 1.10268593e-07, 1.46731049e-01, 3.25271755e-01,-3.31867449e-02, 1.06381141e-01, 3.19786429e-01,-6.12258874e-02,-2.74386834e-02, 3.23606879e-01,-2.78976876e-02,-8.92594308e-02, 3.30803126e-01, 1.34110451e-07,-1.23341218e-01,
        6.19482279e-01, 4.89516668e-02,-1.87488854e-01, 6.11785948e-01, 1.05619021e-01,-1.16035640e-02, 6.16657197e-01, 3.40733044e-02, 2.28796884e-01, 6.16657197e-01, 9.08970833e-08, 3.22826058e-01, 6.16657197e-01,-3.40731703e-02, 2.28796884e-01, 6.11785948e-01,-1.05618924e-01,-1.16035640e-02, 6.19482279e-01,-4.89515029e-02,-1.87488854e-01, 6.19482279e-01, 1.14440918e-07,-2.66955584e-01,
        9.05269146e-01, 7.97823220e-02,-1.98831066e-01, 9.05269146e-01, 1.90241292e-01, 2.74816714e-03, 8.82668316e-01, 1.31550357e-01, 2.65437335e-01, 8.82668316e-01, 9.68575478e-08, 3.74524713e-01, 8.82668316e-01,-1.31550089e-01, 2.65437335e-01, 9.05269146e-01,-1.90240964e-01, 2.74828076e-03, 9.05269146e-01,-7.97821954e-02,-1.98831066e-01, 9.05269146e-01, 1.04308128e-07,-2.80545115e-01,
        1.16412377e+00, 8.10560137e-02,-1.68309495e-01, 1.16412377e+00, 1.93268329e-01, 2.44810339e-02, 1.14717317e+00, 9.53793973e-02, 2.21129894e-01, 1.14717317e+00, 1.04308128e-07, 3.12008142e-01, 1.14717317e+00,-9.53791291e-02, 2.21129894e-01, 1.16412377e+00,-1.93267897e-01, 2.44809985e-02, 1.16412377e+00,-8.10558200e-02,-1.68309495e-01, 1.16412377e+00, 1.19209290e-07,-2.37480029e-01,
        1.30317569e+00, 6.65707514e-02,-1.19203724e-01, 1.30317569e+00, 9.39294770e-02, 4.41631973e-02, 1.31023848e+00, 7.11367428e-02, 1.40758544e-01, 1.31023848e+00, 1.04308128e-07, 1.98606402e-01, 1.31023848e+00,-7.11364448e-02, 1.40758544e-01, 1.30317569e+00,-9.39292908e-02, 4.41631973e-02, 1.30317569e+00,-6.65706247e-02,-1.19203746e-01, 1.30317569e+00, 1.04308128e-07,-1.68193176e-01,
        1.54440629e+00, 2.93813888e-02,-4.48383763e-04, 1.53635108e+00, 2.93813888e-02, 6.98706061e-02, 1.52829576e+00, 2.14724839e-02, 1.40191242e-01, 1.52829564e+00, 5.66244125e-06, 1.40191242e-01, 1.52829564e+00,-2.14714929e-02, 1.40191242e-01, 1.53635108e+00,-2.93802600e-02, 6.98706061e-02, 1.54440629e+00,-2.93802600e-02,-4.48383763e-04, 1.54440629e+00, 5.66244125e-06,-4.48383763e-04,
        1.53673446e+00, 1.42821670e-04, 6.65244162e-02, 1.53669524e+00, 1.42821670e-04, 6.68661371e-02, 1.53665602e+00, 1.42821670e-04, 6.72078654e-02, 1.53665602e+00, 2.98023224e-08, 6.72078654e-02, 1.53665602e+00,-1.42762437e-04, 6.72078654e-02, 1.53669524e+00,-1.42762437e-04, 6.68661371e-02, 1.53673446e+00,-1.42762437e-04, 6.65244162e-02, 1.53673446e+00, 2.98023224e-08, 6.65244162e-02,
    ]).reshape(9, 8, 3)

    templates["body_fish_eel"] = np.array([
        -1.51607013e+00, 1.93054475e-05, 1.20516727e-02,-1.51606679e+00, 1.93054475e-05, 1.20828003e-02,-1.51606333e+00, 1.93054475e-05, 1.21139269e-02,-1.51606297e+00, 1.07437372e-07, 1.21139493e-02,-1.51606250e+00,-1.90929790e-05, 1.21139716e-02,-1.51606584e+00,-1.90929790e-05, 1.20828394e-02,-1.51606917e+00,-1.90929790e-05, 1.20517164e-02,-1.51606965e+00, 1.07437372e-07, 1.20516922e-02,
        -1.52186060e+00, 2.39744484e-02,-3.86217125e-02,-1.51685762e+00, 3.84033285e-02, 1.20467320e-02,-1.51106167e+00, 2.39744484e-02, 7.37763196e-02,-1.51116467e+00, 1.21951476e-07, 7.42523074e-02,-1.51106060e+00,-2.39742137e-02, 7.37763718e-02,-1.51685655e+00,-3.84031013e-02, 1.20467842e-02,-1.52185905e+00,-2.39742137e-02,-3.86216380e-02,-1.52128565e+00, 1.21951476e-07,-3.89654860e-02,
        -9.97655332e-01, 2.77164169e-02,-6.79720119e-02,-9.94429827e-01, 5.19167371e-02, 1.44815892e-02,-9.89130616e-01, 2.81454213e-02, 1.04923092e-01,-9.89111125e-01, 3.99947166e-05, 1.20630383e-01,-9.89130616e-01,-2.80977860e-02, 1.04923092e-01,-9.94429708e-01,-5.19638024e-02, 1.44815892e-02,-9.97655332e-01,-2.76701245e-02,-6.79720119e-02,-9.83649194e-01, 1.70469284e-05,-8.51858035e-02,
        -5.06315827e-01, 4.11026590e-02,-6.99963719e-02,-5.10212779e-01, 7.25849345e-02, 1.42117590e-02,-5.01554191e-01, 3.55590023e-02, 1.24903269e-01,-5.01167357e-01,-3.08942795e-03, 1.63814500e-01,-5.01547158e-01,-4.11662087e-02, 1.24902435e-01,-5.10197103e-01,-7.87659585e-02, 1.42169595e-02,-5.06257117e-01,-4.57078889e-02,-6.99643865e-02,-5.06791055e-01,-3.08808312e-03,-8.80113244e-02,
        5.44715703e-01, 5.58757894e-02,-7.59482458e-02, 5.42643964e-01, 7.33061507e-02, 9.72673669e-03, 5.48981011e-01, 5.41456267e-02, 1.09124109e-01, 5.49366832e-01,-4.98964079e-03, 1.47562385e-01, 5.48981011e-01,-6.32465817e-02, 1.09124109e-01, 5.42643964e-01,-8.34978223e-02, 9.72677767e-03, 5.44715703e-01,-6.18387498e-02,-7.59482458e-02, 5.44715703e-01,-5.00482321e-03,-9.07617882e-02,
        1.12251794e+00, 6.53799623e-02,-8.08493048e-02, 1.12322628e+00, 8.11860859e-02, 9.81053337e-03, 1.12656713e+00, 4.54806611e-02, 9.48402658e-02, 1.12696397e+00,-3.32011096e-03, 1.31755680e-01, 1.12656713e+00,-5.15142381e-02, 9.48402658e-02, 1.12322628e+00,-8.78565013e-02, 9.81052034e-03, 1.12251794e+00,-6.88424036e-02,-8.08493122e-02, 1.12251794e+00,-3.30924429e-03,-9.60670337e-02,
        1.58868670e+00, 8.05266425e-02,-1.32189572e-01, 1.59185529e+00, 9.56453085e-02,-3.88176888e-02, 1.59499586e+00, 5.86516112e-02, 4.01972979e-02, 1.59808815e+00,-4.47249785e-04, 7.76412711e-02, 1.59499586e+00,-5.94198778e-02, 4.01972979e-02, 1.59185529e+00,-9.65725929e-02,-3.88176888e-02, 1.58868670e+00,-8.06468874e-02,-1.32189602e-01, 1.58582830e+00,-4.34160233e-04,-1.51426941e-01,
        1.93168294e+00, 2.04673763e-02,-5.73762506e-02, 1.93285942e+00, 2.04673763e-02,-3.53952870e-02, 1.93403566e+00, 1.49579719e-02,-1.34138167e-02, 1.93403566e+00, 4.61339951e-06,-1.34138167e-02, 1.93403566e+00,-1.49571598e-02,-1.34138167e-02, 1.93285942e+00,-2.04664692e-02,-3.53952870e-02, 1.93168294e+00,-2.04664692e-02,-5.73762506e-02, 1.93168294e+00, 4.61339951e-06,-5.73762506e-02,
        1.93280351e+00, 9.95472074e-05,-3.64413038e-02, 1.93280852e+00, 9.95472074e-05,-3.63344029e-02, 1.93281460e+00, 9.95472074e-05,-3.62276137e-02, 1.93281460e+00, 8.94069672e-09,-3.62276137e-02, 1.93281460e+00,-9.93795693e-05,-3.62276137e-02, 1.93280852e+00,-9.93795693e-05,-3.63344029e-02, 1.93280351e+00,-9.93795693e-05,-3.64413038e-02, 1.93280351e+00, 8.94069672e-09,-3.64413038e-02,
    ]).reshape(9, 8, 3)

    templates["body_fish_pickerel"] = np.array([
        -1.44144684e-01, 1.93054475e-05, 1.35787204e-03,-1.44141346e-01, 1.93054475e-05, 1.38900103e-03,-1.44137889e-01, 1.93054475e-05, 1.42012909e-03,-1.44137532e-01, 1.07437372e-07, 1.42015144e-03,-1.44137055e-01,-1.90976953e-05, 1.42017169e-03,-1.44140393e-01,-1.90976953e-05, 1.38904431e-03,-1.44143730e-01,-1.90976953e-05, 1.35791532e-03,-1.44144207e-01, 1.07437372e-07, 1.35789439e-03,
        -1.49935156e-01, 2.39744484e-02,-4.93155085e-02,-1.44932181e-01, 3.84033285e-02, 1.35293417e-03,-1.39136225e-01, 2.39744484e-02, 6.30825236e-02,-1.39239222e-01, 1.21951476e-07, 6.35585114e-02,-1.39135152e-01,-2.39742175e-02, 6.30825683e-02,-1.44931108e-01,-3.84031013e-02, 1.35297747e-03,-1.49933606e-01,-2.39742175e-02,-4.93154377e-02,-1.49360210e-01, 1.21951476e-07,-4.96592894e-02,
        1.11472219e-01, 2.37023775e-02,-7.71420673e-02, 1.14230424e-01, 4.43962477e-02,-6.63542748e-03, 1.18761748e-01, 2.40692235e-02, 7.07017183e-02, 1.18778437e-01, 3.60697508e-05, 8.41331333e-02, 1.18761748e-01,-2.40247324e-02, 7.07017183e-02, 1.14230543e-01,-4.44327183e-02,-6.63542748e-03, 1.11472219e-01,-2.36590281e-02,-7.71420673e-02, 1.23448938e-01, 1.64583325e-05,-9.18617025e-02,
        4.02713358e-01, 5.81631809e-02,-1.28593519e-01, 3.97302747e-01, 1.01873457e-01,-1.16781462e-02, 4.09324408e-01, 5.04663102e-02, 1.42006993e-01, 4.09861624e-01,-3.19354981e-03, 1.96031719e-01, 4.09334183e-01,-5.60597144e-02, 1.42005831e-01, 3.97324622e-01,-1.08263560e-01,-1.16709322e-02, 4.02794838e-01,-6.23654202e-02,-1.28549114e-01, 4.02053535e-01,-3.19166854e-03,-1.53605655e-01,
        1.13765919e+00, 8.58720616e-02,-1.22610010e-01, 1.13455653e+00, 1.11975752e-01, 5.69676049e-03, 1.14404690e+00, 8.32809880e-02, 1.54554129e-01, 1.14462471e+00,-5.27993403e-03, 2.12119237e-01, 1.14404690e+00,-9.25254300e-02, 1.54554129e-01, 1.13455653e+00,-1.22853674e-01, 5.69682103e-03, 1.13765919e+00,-9.04170722e-02,-1.22610010e-01, 1.13765919e+00,-5.30266389e-03,-1.44794732e-01,
        1.46125221e+00, 9.64227170e-02,-1.22370690e-01, 1.46228290e+00, 1.19420260e-01, 9.53720696e-03, 1.46714377e+00, 6.74697235e-02, 1.33253470e-01, 1.46772122e+00,-3.53424065e-03, 1.86964512e-01, 1.46714377e+00,-7.36555606e-02, 1.33253470e-01, 1.46228290e+00,-1.26532689e-01, 9.53720044e-03, 1.46125221e+00,-9.88676101e-02,-1.22370713e-01, 1.46125221e+00,-3.51843098e-03,-1.44512117e-01,
        1.74057841e+00, 8.05266500e-02,-1.07487708e-01, 1.72998977e+00, 9.56453159e-02,-1.46640465e-02, 1.72148347e+00, 5.86516187e-02, 6.39544874e-02, 1.71903908e+00,-4.47243452e-04, 1.01446338e-01, 1.72148347e+00,-5.94198741e-02, 6.39544874e-02, 1.72998977e+00,-9.65725705e-02,-1.46640465e-02, 1.74057841e+00,-8.06468725e-02,-1.07487731e-01, 1.74057841e+00,-4.34149802e-04,-1.26936272e-01,
        2.06885481e+00, 2.04673875e-02, 1.69232413e-02, 2.06678796e+00, 2.04673875e-02, 3.88384089e-02, 2.06472087e+00, 1.49579793e-02, 6.07540682e-02, 2.06472087e+00, 4.61339951e-06, 6.07540682e-02, 2.06472087e+00,-1.49571523e-02, 6.07540682e-02, 2.06678796e+00,-2.04664618e-02, 3.88384089e-02, 2.06885481e+00,-2.04664618e-02, 1.69232413e-02, 2.06885481e+00, 4.61339951e-06, 1.69232413e-02,
        2.06688643e+00, 9.95561480e-05, 3.77955511e-02, 2.06687570e+00, 9.95561480e-05, 3.79020348e-02, 2.06686592e+00, 9.95561480e-05, 3.80085371e-02, 2.06686592e+00, 8.94069672e-09, 3.80085371e-02, 2.06686592e+00,-9.93795693e-05, 3.80085371e-02, 2.06687570e+00,-9.93795693e-05, 3.79020348e-02, 2.06688643e+00,-9.93795693e-05, 3.77955511e-02, 2.06688643e+00, 8.94069672e-09, 3.77955511e-02,
    ]).reshape(9, 8, 3)

    templates["body_fish_pufferfish"] = np.array([
        -1.06593187e-03, 1.17346644e-05, 7.52858445e-04,-1.06476061e-03, 1.17346644e-05, 7.78168812e-04,-1.06364489e-03, 1.17346644e-05, 8.03476572e-04,-1.06364489e-03, 8.94069672e-09, 8.03476572e-04,-1.06364489e-03,-1.15483999e-05, 8.03476572e-04,-1.06476061e-03,-1.15483999e-05, 7.78168812e-04,-1.06593187e-03,-1.15483999e-05, 7.52858445e-04,-1.06593187e-03, 8.94069672e-09, 7.52858445e-04,
        -2.96100229e-03, 1.05970018e-02,-2.92576067e-02,-1.06476061e-03, 2.34177131e-02, 7.78160617e-04, 1.24704046e-03, 1.07706077e-02, 3.74784470e-02, 1.24704046e-03, 9.89437103e-08, 5.13902232e-02, 1.24704046e-03,-1.07704587e-02, 3.74784470e-02,-1.06476061e-03,-2.34175231e-02, 7.78160617e-04,-2.96100229e-03,-1.05968490e-02,-2.92576067e-02,-2.96100229e-03, 9.89437103e-08,-4.07356694e-02,
        1.76236153e-01, 2.70260572e-02,-6.68170080e-02, 1.73444808e-01, 5.95305115e-02,-2.16499828e-02, 1.77452490e-01, 3.25114205e-02, 7.61205107e-02, 1.77452490e-01, 1.39698386e-07, 1.05600670e-01, 1.77452490e-01,-3.25111598e-02, 7.61205107e-02, 1.73444837e-01,-5.95302321e-02,-2.16499828e-02, 1.76236108e-01,-2.70258188e-02,-6.68170080e-02, 1.81493774e-01, 1.49011612e-07,-9.17175964e-02,
        3.80391479e-01, 1.64557844e-01,-3.20270508e-01, 3.72695208e-01, 2.19414502e-01,-8.69555771e-02, 3.77566457e-01, 6.96000457e-02, 2.04390436e-01, 3.77566457e-01, 3.27825546e-08, 2.75448441e-01, 3.77566457e-01,-6.96000606e-02, 2.04390436e-01, 3.72695208e-01,-2.19414562e-01,-8.69555771e-02, 3.80391479e-01,-1.64557815e-01,-3.20270508e-01, 3.80391479e-01, 8.34465027e-08,-4.07698631e-01,
        6.66178346e-01, 2.84099340e-01,-3.34461987e-01, 6.66178346e-01, 4.14719909e-01,-6.88938275e-02, 6.43577576e-01, 2.87552506e-01, 2.32079685e-01, 6.43577576e-01, 5.96046448e-08, 3.14517170e-01, 6.43577576e-01,-2.87552237e-01, 2.32079685e-01, 6.66178346e-01,-4.14719522e-01,-6.88936985e-02, 6.66178346e-01,-2.84099460e-01,-3.34461987e-01, 6.66178346e-01, 5.96046448e-08,-4.23353612e-01,
        9.25032973e-01, 2.62995303e-01,-2.96273053e-01, 9.30381536e-01, 3.87578756e-01,-4.17014398e-02, 9.08767939e-01, 1.93468750e-01, 1.98596477e-01, 9.08082366e-01, 5.96046448e-08, 2.67273307e-01, 9.08767939e-01,-1.93468481e-01, 1.98596477e-01, 9.30381596e-01,-3.87578279e-01,-4.17014696e-02, 9.25032973e-01,-2.62995213e-01,-2.96273053e-01, 9.25032973e-01, 1.04308128e-07,-3.69470060e-01,
        1.02993584e+00, 2.27447137e-01,-2.21061721e-01, 1.07025099e+00, 2.50135988e-01, 2.32950114e-02, 1.04654169e+00, 1.60277754e-01, 1.59942076e-01, 1.03699863e+00, 8.34465027e-08, 2.41753876e-01, 1.04654169e+00,-1.60277292e-01, 1.59942076e-01, 1.07025099e+00,-2.50135869e-01, 2.32950114e-02, 1.02993584e+00,-2.27447107e-01,-2.21061736e-01, 1.02993584e+00, 1.04308128e-07,-2.76997387e-01,
        1.20875597e+00, 4.59948368e-02,-7.17158318e-02, 1.20070076e+00, 4.62229997e-02, 1.62680671e-02, 1.19264543e+00, 3.29032615e-02, 1.04254037e-01, 1.19264531e+00, 7.62939453e-06, 1.04254037e-01, 1.19264531e+00,-3.29019167e-02, 1.04254037e-01, 1.20070076e+00,-4.62213904e-02, 1.62680671e-02, 1.20875597e+00,-4.59932722e-02,-7.17158318e-02, 1.20875597e+00, 7.67707825e-06,-7.17158318e-02,
        1.20108414e+00, 2.19729543e-04, 1.20812878e-02, 1.20104492e+00, 2.19702348e-04, 1.25088468e-02, 1.20100570e+00, 2.19672173e-04, 1.29364282e-02, 1.20100570e+00,-4.76837158e-08, 1.29364282e-02, 1.20100570e+00,-2.19771639e-04, 1.29364282e-02, 1.20104492e+00,-2.19799206e-04, 1.25088468e-02, 1.20108414e+00,-2.19827145e-04, 1.20812878e-02, 1.20108414e+00,-4.76837158e-08, 1.20812878e-02,
    ]).reshape(9, 8, 3)

    templates["body_fish_spadefish"] = np.array([
        -8.37474596e-04, 1.93054475e-05,-2.31362879e-04,-8.30277987e-04, 1.93054475e-05,-1.87292788e-04,-8.23146594e-04, 1.93054475e-05,-1.43200159e-04,-8.23146594e-04, 1.07437372e-07,-1.43200159e-04,-8.23146594e-04,-1.90976953e-05,-1.43200159e-04,-8.30277987e-04,-1.90976953e-05,-1.87292788e-04,-8.37474596e-04,-1.90976953e-05,-2.31362879e-04,-8.37474596e-04, 1.07437372e-07,-2.31362879e-04,
        -1.25365509e-02, 2.39744484e-02,-7.19659925e-02,-8.30277987e-04, 3.84033285e-02,-1.87313557e-04, 1.34360697e-02, 2.39744484e-02, 5.97435273e-02, 1.35248201e-02, 1.21951476e-07, 8.79645944e-02, 1.34360697e-02,-2.39742137e-02, 5.97435199e-02,-8.30277987e-04,-3.84031013e-02,-1.87313557e-04,-1.25365509e-02,-2.39742137e-02,-7.19659925e-02,-1.26048578e-02, 1.21951476e-07,-7.24926516e-02,
        2.05219120e-01, 3.82222570e-02,-1.83451608e-01, 2.00940609e-01, 6.12261221e-02, 2.42497027e-02, 2.01982036e-01, 4.54686768e-02, 1.59583367e-01, 2.01965868e-01, 1.21951476e-07, 2.15377942e-01, 2.01982036e-01,-4.54683863e-02, 1.59583367e-01, 2.00940624e-01,-6.12258837e-02, 2.42497344e-02, 2.05219075e-01,-3.82219851e-02,-1.83451638e-01, 2.10349232e-01, 1.34110451e-07,-2.48459414e-01,
        4.14377540e-01, 4.93875742e-02,-2.64224738e-01, 4.11633462e-01, 1.05619036e-01, 2.18600687e-02, 4.18696970e-01, 4.80764881e-02, 3.41576993e-01, 4.18696970e-01, 1.01327896e-07, 4.27322060e-01, 4.18696970e-01,-4.80762795e-02, 3.41576993e-01, 4.11633462e-01,-1.05618902e-01, 2.18600687e-02, 4.14377540e-01,-3.98088209e-02,-2.64224738e-01, 4.14351523e-01, 1.19209290e-07,-3.94666880e-01,
        6.42465472e-01, 7.37472773e-02,-2.58420169e-01, 6.57577276e-01, 1.19710460e-01, 8.73168930e-03, 6.74955904e-01, 6.79166913e-02, 3.43623281e-01, 6.74955904e-01, 1.19209290e-07, 4.29368347e-01, 6.74955904e-01,-6.79163188e-02, 3.43623281e-01, 6.57577336e-01,-1.24499403e-01, 8.73179734e-03, 6.42465472e-01,-7.37470835e-02,-2.58420169e-01, 6.42465472e-01, 1.19209290e-07,-3.72660339e-01,
        8.05282593e-01, 7.49246329e-02,-2.32784018e-01, 8.22675765e-01, 1.21659830e-01,-6.82246685e-03, 8.43541205e-01, 9.17142182e-02, 2.41336733e-01, 8.43541205e-01, 1.19209290e-07, 3.27081800e-01, 8.43541205e-01,-9.17137861e-02, 2.41336733e-01, 8.22675705e-01,-1.26448661e-01,-6.82249293e-03, 8.05282593e-01,-7.49243572e-02,-2.32784018e-01, 8.05282593e-01, 1.39698386e-07,-3.41076940e-01,
        9.65303659e-01, 4.93858680e-02,-1.68695956e-01, 9.76115942e-01, 9.39295068e-02,-2.68732607e-02, 9.49067116e-01, 4.28583920e-02, 8.90070498e-02, 9.88991618e-01, 1.19209290e-07, 1.27114072e-01, 9.49067116e-01,-4.28581908e-02, 8.90070498e-02, 9.76115942e-01,-9.39292684e-02,-2.68732607e-02, 9.65303719e-01,-4.93856966e-02,-1.68695986e-01, 9.65303719e-01, 1.34110451e-07,-2.38954201e-01,
        1.08825457e+00, 2.93814093e-02,-1.41601235e-01, 1.09162295e+00, 2.93814093e-02,-7.11301416e-02, 1.09499156e+00, 2.14725006e-02,-6.57392666e-04, 1.09499145e+00, 5.85913658e-06,-6.57382607e-04, 1.09499145e+00,-2.14714706e-02,-6.57382607e-04, 1.09162295e+00,-2.93802433e-02,-7.11301416e-02, 1.08825457e+00,-2.93802433e-02,-1.41601235e-01, 1.08825457e+00, 5.85913658e-06,-1.41601235e-01,
        1.09146273e+00, 1.42827630e-04,-7.44835511e-02, 1.09147894e+00, 1.42827630e-04,-7.41410926e-02, 1.09149539e+00, 1.42827630e-04,-7.37986341e-02, 1.09149539e+00, 4.76837158e-08,-7.37986341e-02, 1.09149539e+00,-1.42738968e-04,-7.37986341e-02, 1.09147894e+00,-1.42738968e-04,-7.41410926e-02, 1.09146273e+00,-1.42738968e-04,-7.44835511e-02, 1.09146273e+00, 4.76837158e-08,-7.44835511e-02,
    ]).reshape(9, 8, 3)

    return templates

FISH_TEMPLATES = _load_templates()

# defaultdict(lambda: 0.1, {"body_fish_eel": 0.01, "body_fish_puffer": 0.001})
FISH_TEMPLATE_TEMPS = {
    "body_fish_bluefish": 0.1,
    "body_fish_crappie": 0.1,
    "body_fish_eel": 0.01,
    "body_fish_pickerel": 0.1,
    "body_fish_pufferfish": 0.001,
    "body_fish_spadefish": 0.1,
}


def skeleton_to_tangents(skeleton):
    axes = np.empty_like(skeleton, dtype=np.float32)
    axes[-1] = skeleton[-1] - skeleton[-2]
    axes[:-1] = skeleton[1:] - skeleton[:-1]
    axes[1:-1] = (axes[1:-1] + axes[:-2]) / 2
    norm = np.linalg.norm(axes, axis=-1)
    axes[norm > 0] /= norm[norm > 0, None]
    return axes

def rodrigues(angles, axes):
    axes = axes / np.linalg.norm(axes, axis=-1, keepdims=True)
    K = np.zeros((*axes.shape[:-1], 3, 3))
    K[..., 0, 1] = -axes[..., 2]
    K[..., 0, 2] = axes[..., 1]
    K[..., 1, 0] = axes[..., 2]
    K[..., 1, 2] = -axes[..., 0]
    K[..., 2, 0] = -axes[..., 1]
    K[..., 2, 1] = axes[..., 0]
    I = np.eye(3)
    s = np.sin(angles)[..., None, None]
    c = np.cos(angles)[..., None, None]
    return I + s * K + (1 - c) * (K @ K)

def rotate_match_directions(a, b):
    norm = np.linalg.norm
    axes = np.cross(a, b, axis=-1)
    m = np.linalg.norm(axes, axis=-1) > 1e-4
    rots = np.empty((len(a), 3, 3))
    rots[~m] = np.eye(3)[None]
    if np.all(~m):
        return rots
    dots = (a[m] * b[m]).sum(axis=-1)
    dots /= norm(a[m], axis=-1) * norm(b[m], axis=-1)
    dots = np.clip(dots, -1, 1)
    rots[m] = rodrigues(np.arccos(dots), axes[m])
    return rots

def lerp_sample(arr, indices):
    """Linear interpolation sample from array at fractional indices."""

    n = len(arr)
    idx_floor = np.floor(indices).astype(int)
    idx_ceil = np.ceil(indices).astype(int)
    idx_floor = np.clip(idx_floor, 0, n - 1)
    idx_ceil = np.clip(idx_ceil, 0, n - 1)
    t = indices - idx_floor
    return arr[idx_floor] * (1 - t)[..., None] + arr[idx_ceil] * t[..., None]

def factorize_nurbs_handles(handles):
    """Decompose (9,8,3) handles into skeleton, radii, normalized profiles."""

    skeleton = handles.mean(axis=1)
    tangents = skeleton_to_tangents(skeleton)

    forward = np.zeros_like(tangents)
    forward[:, 0] = 1
    rot_mats = rotate_match_directions(tangents, forward)

    profiles = handles - skeleton[:, None]
    profiles = np.einsum("bij,bvj->bvi", rot_mats, profiles)

    ts = np.linspace(0, 1, handles.shape[0])

    rads = np.linalg.norm(profiles, axis=2, keepdims=True).mean(axis=1, keepdims=True)
    rads = np.clip(rads, 1e-3, 1e5)
    profiles_norm = profiles / rads

    skeleton_root = skeleton[[0]]
    dirs = np.diff(skeleton, axis=0)

    lens = np.linalg.norm(dirs, axis=-1)
    length = lens.sum()
    proportions = lens / length

    thetas = np.arctan2(dirs[:, 2], dirs[:, 0])
    thetas = np.rad2deg(thetas)
    skeleton_yoffs = dirs[:, 1] / np.clip(lens, 1e-8, None)

    return {
        "ts": ts,
        "rads": rads,
        "skeleton_root": skeleton_root,
        "skeleton_yoffs": skeleton_yoffs,
        "length": length,
        "proportions": proportions,
        "thetas": thetas,
        "profiles_norm": profiles_norm,
    }

def recompose_nurbs_handles(params):
    """Recompose NURBS handles from decomposed parameters."""

    lens = params["length"] * params["proportions"]
    thetas = np.deg2rad(params["thetas"])
    skeleton_offs = np.stack(
        [lens * np.cos(thetas), lens * params["skeleton_yoffs"], lens * np.sin(thetas)],
        axis=-1,
    )
    skeleton = np.concatenate([params["skeleton_root"], skeleton_offs], axis=0)
    skeleton = np.cumsum(skeleton, axis=0)

    # compute_profile_verts with profile_as_points=True
    n = params["profiles_norm"].shape[0]
    k = len(skeleton)
    ts = params["ts"]
    profiles = params["profiles_norm"] * params["rads"]

    axes = skeleton_to_tangents(skeleton)
    forward = np.zeros_like(axes)
    forward[:, 0] = 1
    rot_mats = rotate_match_directions(forward, axes)

    axes_sampled = lerp_sample(axes, ts * (k - 1))
    pos_sampled = lerp_sample(skeleton, ts * (k - 1))

    forward_s = np.zeros_like(axes_sampled)
    forward_s[:, 0] = 1
    rot_mats_s = rotate_match_directions(forward_s, axes_sampled)

    handles = np.einsum("bij,bvj->bvi", rot_mats_s, profiles) + pos_sampled[:, None]
    return handles


def sample_body_params(var=1.0):
    """


    1. Dirichlet sampling over 6 fish templates with temperature weights
    2. Weighted blend of raw handle arrays
    3. Decompose into skeleton + profiles
    4. Add noise to decomposed parameters
    """

    fish_keys = sorted(FISH_TEMPLATES.keys())
    temp = np.array([FISH_TEMPLATE_TEMPS[k] for k in fish_keys])

    # Dirichlet sampling (low temperature = mostly picks one template)
    weights = np.random.dirichlet(temp)

    # Weighted blend of raw handle arrays
    handles = sum(weights[i] * FISH_TEMPLATES[k] for i, k in enumerate(fish_keys))

    # Decompose blended handles
    decomp = factorize_nurbs_handles(handles)

    # Apply noise (matching NurbsPart.sample_params exactly)
    def N(u, v, d=1):
        return np.random.normal(u, np.array(v) * var, d)

    sz = N(1, 0.1)
    decomp["length"] *= sz * N(1, 0.1)
    decomp["rads"] *= sz * N(1, 0.1) * N(1, 0.15, decomp["rads"].shape)
    decomp["proportions"] *= N(1, 0.15)

    ang_noise = N(0, 7, decomp["thetas"].shape)
    ang_noise -= ang_noise.mean()
    decomp["thetas"] += ang_noise

    n, m, d = decomp["profiles_norm"].shape
    profile_noise = N(1, 0.07, (1, m, 1)) * N(1, 0.15, (n, m, 1))
    profile_noise[:, :m // 2 - 1] = profile_noise[:, m // 2:-1][:, ::-1]  # symmetrize
    decomp["profiles_norm"] *= profile_noise

    return decomp


# ── Random parameter sampling ───────────────────────────────────────────────


SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys


def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_body_material(seed, name="FishBody_Material"):
    """Fish body shader: metallic with subsurface, wave-driven scale pattern,
    BSDF: Metallic=0.8, Specular=0.9, Roughness=0.3, IOR=1.69, SSS."""

    noise_w = float(np.random.uniform(-2, 2))
    wave_scale = float(np.exp(np.random.uniform(np.log(1), np.log(4))))
    wave_phase = float(np.random.uniform(0, 10))
    wave_dist = float(np.random.uniform(0, 3))
    # Body colors: warm-toned dorsal, lighter ventral
    body_hue = float(np.random.uniform(0.02, 0.12))
    body_color = _hsv2rgba(body_hue, np.random.uniform(0.4, 0.9), np.random.uniform(0.02, 0.2))
    belly_color = _hsv2rgba(body_hue, np.random.uniform(0.05, 0.15), np.random.uniform(0.6, 1.0))
    # Scale edge highlight color (from colorramp_7 / colorramp_15 in original)
    edge_color = _hsv2rgba(body_hue + np.random.uniform(-0.02, 0.02),
                           np.random.uniform(0.1, 0.3),
                           np.random.uniform(0.01, 0.03))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Noise for wave distortion (original: noise_dimensions=4D, Scale=50)
    noise0 = nt.nodes.new("ShaderNodeTexNoise"); noise0.noise_dimensions = "4D"
    ln(tc.outputs["Generated"], noise0.inputs["Vector"])
    noise0.inputs["W"].default_value = noise_w
    noise0.inputs["Scale"].default_value = 50.0

    # Mix noise with Generated coords (Fac=0.9042 in original)
    mix_v = nt.nodes.new("ShaderNodeMix"); mix_v.data_type = "RGBA"
    mix_v.inputs[0].default_value = 0.9042
    ln(noise0.outputs["Color"], mix_v.inputs[6])
    ln(tc.outputs["Generated"], mix_v.inputs[7])

    # Wave texture for stripe/scale pattern
    wave = nt.nodes.new("ShaderNodeTexWave")
    ln(mix_v.outputs[2], wave.inputs["Vector"])
    wave.inputs["Scale"].default_value = wave_scale
    wave.inputs["Distortion"].default_value = wave_dist
    wave.inputs["Detail"].default_value = 0.0
    wave.inputs["Detail Roughness"].default_value = 0.0
    wave.inputs["Phase Offset"].default_value = wave_phase

    # Wave color ramp (position randomized as in original)
    cr_wave = nt.nodes.new("ShaderNodeValToRGB")
    ln(wave.outputs["Color"], cr_wave.inputs["Fac"])
    cr_wave.color_ramp.elements[0].position = float(np.random.uniform(0.0, 0.2))
    cr_wave.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_wave.color_ramp.elements[1].position = 1.0
    cr_wave.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Dorsal-ventral gradient via Generated Z
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tc.outputs["Generated"], sep.inputs["Vector"])

    # Invert Z for belly brightness (matching invert node in original)
    invert_fac = float(np.random.uniform(0.5, 1.0))
    inv = nt.nodes.new("ShaderNodeInvert")
    inv.inputs["Fac"].default_value = invert_fac
    ln(sep.outputs["Z"], inv.inputs["Color"])

    # wave_contrib = (wave_ramp + (-0.5)) / 2.0
    add_half = nt.nodes.new("ShaderNodeMath"); add_half.operation = "ADD"
    ln(cr_wave.outputs["Color"], add_half.inputs[0])
    add_half.inputs[1].default_value = -0.5

    div2 = nt.nodes.new("ShaderNodeMath"); div2.operation = "DIVIDE"
    ln(add_half.outputs["Value"], div2.inputs[0])
    div2.inputs[1].default_value = 2.0

    # Combine wave with Z-invert
    add_wz = nt.nodes.new("ShaderNodeMath"); add_wz.operation = "ADD"
    ln(div2.outputs["Value"], add_wz.inputs[0])
    ln(inv.outputs["Color"], add_wz.inputs[1])

    # Body color ramp: 3-stop dark-to-warm-to-dark (from colorramp_9)
    cr_body = nt.nodes.new("ShaderNodeValToRGB")
    ln(add_wz.outputs["Value"], cr_body.inputs["Fac"])
    cr_body.color_ramp.elements.new(0)
    cr_body.color_ramp.elements[0].position = 0.0
    cr_body.color_ramp.elements[0].color = edge_color
    cr_body.color_ramp.elements[1].position = float(np.random.uniform(0.1, 0.9))
    # Warm mid-tone (original: ~0.197, 0.121, 0.015)
    mid_color = _hsv2rgba(body_hue, np.random.uniform(0.5, 0.9), np.random.uniform(0.05, 0.25))
    cr_body.color_ramp.elements[1].color = mid_color
    cr_body.color_ramp.elements[2].position = 1.0
    cr_body.color_ramp.elements[2].color = (0.0, 0.0, 0.0, 1.0)

    # Noise multiplier (original: noise Scale=3, multiply blend)
    noise_mul = nt.nodes.new("ShaderNodeTexNoise")
    noise_mul.inputs["Scale"].default_value = 3.0
    cr_nmul = nt.nodes.new("ShaderNodeValToRGB")
    _fac_out = noise_mul.outputs.get("Fac") or noise_mul.outputs.get("Factor") or noise_mul.outputs[0]
    ln(_fac_out, cr_nmul.inputs["Fac"])
    cr_nmul.color_ramp.elements[0].position = 0.2614
    cr_nmul.color_ramp.elements[0].color = (0.006, 0.003, 0.0002, 1.0)
    cr_nmul.color_ramp.elements[1].position = 0.58
    cr_nmul.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Multiply body color with noise
    mix_mul = nt.nodes.new("ShaderNodeMix"); mix_mul.data_type = "RGBA"
    mix_mul.blend_type = "MULTIPLY"
    mix_mul.inputs[0].default_value = 1.0
    ln(cr_body.outputs["Color"], mix_mul.inputs[6])
    ln(cr_nmul.outputs["Color"], mix_mul.inputs[7])

    # Belly mix: white belly blended with patterned dorsal
    cr_belly = nt.nodes.new("ShaderNodeValToRGB")
    # Normal Z + 0.5 offset (original: add.inputs[1] = sample_range(0.45, 0.6))
    belly_off = nt.nodes.new("ShaderNodeMath"); belly_off.operation = "ADD"
    ln(tc.outputs["Normal"], sep.inputs["Vector"])  # reuse sep
    sep2 = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tc.outputs["Normal"], sep2.inputs["Vector"])
    add_belly = nt.nodes.new("ShaderNodeMath"); add_belly.operation = "ADD"
    ln(sep2.outputs["Z"], add_belly.inputs[0])
    add_belly.inputs[1].default_value = float(np.random.uniform(0.45, 0.6))

    ln(add_belly.outputs["Value"], cr_belly.inputs["Fac"])
    cr_belly.color_ramp.elements[0].position = 0.0
    cr_belly.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_belly.color_ramp.elements[1].position = 0.234
    cr_belly.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Mix belly white with body pattern
    mix_belly = nt.nodes.new("ShaderNodeMix"); mix_belly.data_type = "RGBA"
    ln(cr_belly.outputs["Color"], mix_belly.inputs[0])
    mix_belly.inputs[6].default_value = belly_color
    ln(mix_mul.outputs[2], mix_belly.inputs[7])

    # Principled BSDF (faithful to shader_fish_body_regular)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_belly.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 0.8
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.3
    bsdf.inputs["IOR"].default_value = 1.69
    bsdf.inputs["Subsurface Weight"].default_value = 0.02
    bsdf.inputs["Subsurface Radius"].default_value = (0.36, 0.46, 0.6)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_fin_material(seed, name="FishFin_Material"):
    """Fish fin shader: dark semi-translucent with noise color variation.
    BSDF: default Principled with dark base color from two noise textures."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    noise_w1 = float(np.random.uniform(-2, 2))
    noise_w2 = float(np.random.uniform(-2, 2))

    # Noise texture 1 (Scale=20, 4D) -> 3-stop dark color ramp
    noise1 = nt.nodes.new("ShaderNodeTexNoise"); noise1.noise_dimensions = "4D"
    noise1.inputs["Scale"].default_value = 20.0
    noise1.inputs["W"].default_value = noise_w1
    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    _fac1 = noise1.outputs.get("Fac") or noise1.outputs.get("Factor") or noise1.outputs[0]
    ln(_fac1, cr1.inputs["Fac"])
    cr1.color_ramp.elements.new(0)
    # 3 stops: all dark, randomized
    for i in range(3):
        cr1.color_ramp.elements[i].color = (
            float(np.random.uniform(0, 0.15)),
            float(np.random.uniform(0, 0.15)),
            float(np.random.uniform(0, 0.15)), 1.0)
    cr1.color_ramp.elements[0].position = 0.0
    cr1.color_ramp.elements[1].position = 0.673
    cr1.color_ramp.elements[2].position = 1.0

    # Noise texture 2 (Scale=10, 4D) -> 2-stop dark color ramp
    noise2 = nt.nodes.new("ShaderNodeTexNoise"); noise2.noise_dimensions = "4D"
    noise2.inputs["Scale"].default_value = 10.0
    noise2.inputs["W"].default_value = noise_w2
    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    _fac2 = noise2.outputs.get("Fac") or noise2.outputs.get("Factor") or noise2.outputs[0]
    ln(_fac2, cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.005
    cr2.color_ramp.elements[0].color = (
        float(np.random.uniform(0, 0.15)),
        float(np.random.uniform(0, 0.15)),
        float(np.random.uniform(0, 0.15)), 1.0)
    cr2.color_ramp.elements[1].position = 0.536
    cr2.color_ramp.elements[1].color = (
        float(np.random.uniform(0, 0.15)),
        float(np.random.uniform(0, 0.15)),
        float(np.random.uniform(0, 0.15)), 1.0)

    # Mix the two noise colors (using a simple constant Fac=0.5 to blend)
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    mix_c.inputs[0].default_value = 0.5
    ln(cr1.outputs["Color"], mix_c.inputs[6])
    ln(cr2.outputs["Color"], mix_c.inputs[7])

    # Principled BSDF with dark base (matching shader_fin_regular)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_eye_material(seed, name="FishEye_Material"):
    """Fish eye shader: iris pattern with Voronoi texture, glossy mix.
    Topology: PrincipledBSDF(Specular=0, Roughness=0) + GlossyBSDF -> MixShader(0.02)."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    voronoi_w = float(np.random.uniform(-10, 10))
    iris_scale1 = float(np.random.uniform(0.65, 1.2))
    iris_scale2 = float(np.random.uniform(0.6, 0.8))

    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Object coords -> SeparateXYZ for iris ring pattern
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(tc.outputs["Object"], sep.inputs["Vector"])

    # Pupil circle: Y^2 * 0.8^2 + Z^2 * 0.3^2 + 0.63
    mul_z = nt.nodes.new("ShaderNodeMath"); mul_z.operation = "MULTIPLY"
    ln(sep.outputs["Z"], mul_z.inputs[0]); mul_z.inputs[1].default_value = 0.3
    sq_z = nt.nodes.new("ShaderNodeMath"); sq_z.operation = "MULTIPLY"
    ln(mul_z.outputs["Value"], sq_z.inputs[0]); ln(mul_z.outputs["Value"], sq_z.inputs[1])

    mul_y = nt.nodes.new("ShaderNodeMath"); mul_y.operation = "MULTIPLY"
    ln(sep.outputs["Y"], mul_y.inputs[0]); mul_y.inputs[1].default_value = 0.8
    sq_y = nt.nodes.new("ShaderNodeMath"); sq_y.operation = "MULTIPLY"
    ln(mul_y.outputs["Value"], sq_y.inputs[0]); ln(mul_y.outputs["Value"], sq_y.inputs[1])

    add_yz = nt.nodes.new("ShaderNodeMath"); add_yz.operation = "ADD"
    ln(sq_z.outputs["Value"], add_yz.inputs[0]); ln(sq_y.outputs["Value"], add_yz.inputs[1])
    add_off = nt.nodes.new("ShaderNodeMath"); add_off.operation = "ADD"
    ln(add_yz.outputs["Value"], add_off.inputs[0]); add_off.inputs[1].default_value = 0.63

    # Pupil color ramp: white center -> black edge at 0.64-0.66
    cr_pupil = nt.nodes.new("ShaderNodeValToRGB")
    ln(add_off.outputs["Value"], cr_pupil.inputs["Fac"])
    cr_pupil.color_ramp.elements[0].position = 0.64
    cr_pupil.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    cr_pupil.color_ramp.elements[1].position = 0.659
    cr_pupil.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    # Iris ring 1: bigger radius -> iris boundary
    mul_z2 = nt.nodes.new("ShaderNodeMath"); mul_z2.operation = "MULTIPLY"
    ln(sep.outputs["Z"], mul_z2.inputs[0]); mul_z2.inputs[1].default_value = iris_scale1
    sq_z2 = nt.nodes.new("ShaderNodeMath"); sq_z2.operation = "MULTIPLY"
    ln(mul_z2.outputs["Value"], sq_z2.inputs[0]); ln(mul_z2.outputs["Value"], sq_z2.inputs[1])

    mul_y2 = nt.nodes.new("ShaderNodeMath"); mul_y2.operation = "MULTIPLY"
    ln(sep.outputs["Y"], mul_y2.inputs[0]); mul_y2.inputs[1].default_value = iris_scale1
    sq_y2 = nt.nodes.new("ShaderNodeMath"); sq_y2.operation = "MULTIPLY"
    ln(mul_y2.outputs["Value"], sq_y2.inputs[0]); ln(mul_y2.outputs["Value"], sq_y2.inputs[1])

    add_yz2 = nt.nodes.new("ShaderNodeMath"); add_yz2.operation = "ADD"
    ln(sq_z2.outputs["Value"], add_yz2.inputs[0]); ln(sq_y2.outputs["Value"], add_yz2.inputs[1])
    add_off2 = nt.nodes.new("ShaderNodeMath"); add_off2.operation = "ADD"
    ln(add_yz2.outputs["Value"], add_off2.inputs[0]); add_off2.inputs[1].default_value = 0.0

    cr_iris1 = nt.nodes.new("ShaderNodeValToRGB")
    ln(add_off2.outputs["Value"], cr_iris1.inputs["Fac"])
    cr_iris1.color_ramp.elements[0].position = 0.616
    cr_iris1.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    cr_iris1.color_ramp.elements[1].position = 0.659
    cr_iris1.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    # Iris color ramp from iris1 -> thin dark ring border
    cr_iris_border = nt.nodes.new("ShaderNodeValToRGB")
    ln(cr_iris1.outputs["Color"], cr_iris_border.inputs["Fac"])
    cr_iris_border.color_ramp.elements[0].position = 0.03
    cr_iris_border.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_iris_border.color_ramp.elements[1].position = 0.052
    cr_iris_border.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # Iris color: noise-driven yellow-orange (from colorramp_4 in original)
    noise_iris = nt.nodes.new("ShaderNodeTexNoise"); noise_iris.noise_dimensions = "4D"
    ln(tc.outputs["Object"], noise_iris.inputs["Vector"])
    noise_iris.inputs["W"].default_value = float(np.random.uniform(-10, 10))
    noise_iris.inputs["Scale"].default_value = 0.5
    cr_iris_col = nt.nodes.new("ShaderNodeValToRGB")
    ln(noise_iris.outputs["Color"], cr_iris_col.inputs["Fac"])
    cr_iris_col.color_ramp.interpolation = "CARDINAL"
    cr_iris_col.color_ramp.elements[0].position = 0.37
    # Yellow-ish iris color
    iris_h1 = float(np.random.uniform(0.08, 0.18))
    iris_h2 = float(np.random.uniform(0.03, 0.10))
    cr_iris_col.color_ramp.elements[0].color = _hsv2rgba(iris_h1, 0.7, 0.9)
    cr_iris_col.color_ramp.elements[1].position = 0.545
    cr_iris_col.color_ramp.elements[1].color = _hsv2rgba(iris_h2, 0.5, 0.8)

    # Outer ring (scale2): separates iris from white sclera
    mul_z3 = nt.nodes.new("ShaderNodeMath"); mul_z3.operation = "MULTIPLY"
    ln(sep.outputs["Z"], mul_z3.inputs[0]); mul_z3.inputs[1].default_value = iris_scale2
    sq_z3 = nt.nodes.new("ShaderNodeMath"); sq_z3.operation = "MULTIPLY"
    ln(mul_z3.outputs["Value"], sq_z3.inputs[0]); ln(mul_z3.outputs["Value"], sq_z3.inputs[1])

    mul_y3 = nt.nodes.new("ShaderNodeMath"); mul_y3.operation = "MULTIPLY"
    ln(sep.outputs["Y"], mul_y3.inputs[0]); mul_y3.inputs[1].default_value = iris_scale2
    sq_y3 = nt.nodes.new("ShaderNodeMath"); sq_y3.operation = "MULTIPLY"
    ln(mul_y3.outputs["Value"], sq_y3.inputs[0]); ln(mul_y3.outputs["Value"], sq_y3.inputs[1])

    add_yz3 = nt.nodes.new("ShaderNodeMath"); add_yz3.operation = "ADD"
    ln(sq_z3.outputs["Value"], add_yz3.inputs[0]); ln(sq_y3.outputs["Value"], add_yz3.inputs[1])
    add_off3 = nt.nodes.new("ShaderNodeMath"); add_off3.operation = "ADD"
    ln(add_yz3.outputs["Value"], add_off3.inputs[0]); add_off3.inputs[1].default_value = 0.18

    cr_outer = nt.nodes.new("ShaderNodeValToRGB")
    ln(add_off3.outputs["Value"], cr_outer.inputs["Fac"])
    cr_outer.color_ramp.elements[0].position = 0.477
    cr_outer.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    cr_outer.color_ramp.elements[1].position = 0.666
    cr_outer.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)

    # Mix iris color with sclera brown (original: (0.738, 0.524, 0.270, 1))
    sclera_color = _hsv2rgba(0.08, 0.63, 0.74)
    mix_sclera = nt.nodes.new("ShaderNodeMix"); mix_sclera.data_type = "RGBA"
    ln(cr_outer.outputs["Color"], mix_sclera.inputs[0])
    mix_sclera.inputs[6].default_value = sclera_color
    ln(cr_iris_col.outputs["Color"], mix_sclera.inputs[7])

    # Mix with black for iris ring (iris1 fac)
    mix_ring = nt.nodes.new("ShaderNodeMix"); mix_ring.data_type = "RGBA"
    ln(cr_iris1.outputs["Color"], mix_ring.inputs[0])
    ln(mix_sclera.outputs[2], mix_ring.inputs[6])
    mix_ring.inputs[7].default_value = (0.0, 0.0, 0.0, 1.0)

    # Combine with pupil (black center)
    mix_pupil = nt.nodes.new("ShaderNodeMix"); mix_pupil.data_type = "RGBA"
    ln(cr_pupil.outputs["Color"], mix_pupil.inputs[0])
    mix_pupil.inputs[6].default_value = (0.0, 0.0, 0.0, 1.0)
    ln(mix_ring.outputs[2], mix_pupil.inputs[7])

    # PrincipledBSDF: Specular=0, Roughness=0 (glossy eye surface)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_pupil.outputs[2], bsdf.inputs["Base Color"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.0

    # Glossy BSDF for specular highlights
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")

    # MixShader: 0.02 fac between Principled and Glossy
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    mix_sh.inputs["Fac"].default_value = 0.02
    ln(bsdf.outputs["BSDF"], mix_sh.inputs[1])
    ln(glossy.outputs["BSDF"], mix_sh.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_sh.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_metal_body_material(seed, metal_type="MetalBasic", name="FishMetal_Material"):
    """

    Creates a Principled BSDF with high metallic, varied color, low roughness."""

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    # Silver/steel tones for metals
    if metal_type == "MetalBasic":
        h = float(np.random.uniform(0.0, 0.1))
        s = float(np.random.uniform(0.0, 0.15))
        v = float(np.random.uniform(0.4, 0.9))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.1, 0.4))
    elif metal_type == "BrushedMetal":
        h = float(np.random.uniform(0.0, 0.08))
        s = float(np.random.uniform(0.0, 0.1))
        v = float(np.random.uniform(0.5, 0.85))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.2, 0.5))
    elif metal_type == "GalvanizedMetal":
        h = float(np.random.uniform(0.55, 0.65))
        s = float(np.random.uniform(0.0, 0.15))
        v = float(np.random.uniform(0.4, 0.7))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.15, 0.35))
    elif metal_type == "GrainedMetal":
        h = float(np.random.uniform(0.05, 0.12))
        s = float(np.random.uniform(0.1, 0.4))
        v = float(np.random.uniform(0.3, 0.6))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.3, 0.5))
    elif metal_type == "HammeredMetal":
        h = float(np.random.uniform(0.05, 0.1))
        s = float(np.random.uniform(0.2, 0.5))
        v = float(np.random.uniform(0.3, 0.55))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.25, 0.45))
    elif metal_type == "BrushedBlackMetal":
        h = 0.0
        s = 0.0
        v = float(np.random.uniform(0.02, 0.1))
        bsdf.inputs["Roughness"].default_value = float(np.random.uniform(0.2, 0.4))
    else:
        h, s, v = 0.0, 0.0, 0.5
        bsdf.inputs["Roughness"].default_value = 0.3
    bsdf.inputs["Base Color"].default_value = _hsv2rgba(h, s, v)
    bsdf.inputs["Metallic"].default_value = float(np.random.uniform(0.8, 1.0))
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _pick_fish_body_material(seed, name="FishBody_Material"):
    """

    MetalBasic(3), BrushedMetal(2), GalvanizedMetal(1), GrainedMetal(1),
    HammeredMetal(0.7), BrushedBlackMetal(0.3), FishBody(7).
    Uses np.random.seed(seed) + np.random.choice to match FixedSeed + weighted_sample."""

    np.random.seed(seed); _random.seed(seed)
    classes = ['MetalBasic', 'BrushedMetal', 'GalvanizedMetal', 'GrainedMetal',
               'HammeredMetal', 'BrushedBlackMetal', 'FishBody']
    weights = np.array([3.0, 2.0, 1.0, 1.0, 0.7, 0.3, 7.0])
    chosen = classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]
    if chosen == 'FishBody':
        return make_body_material(seed, name)
    else:
        return make_metal_body_material(seed, metal_type=chosen, name=name)


# ── Create all 3 materials ──────────────────────────────────────────────────
BODY_MAT = _pick_fish_body_material(SEED, "FishBody_Material")
FIN_MAT = make_fin_material(SEED, "FishFin_Material")
EYE_MAT = make_eye_material(SEED, "FishEye_Material")
np.random.seed(SEED)


# Body shape: sample using NURBS pipeline
body_params = sample_body_params(var=np.random.uniform(0.3, 1.0))

# Fin presence (matching fish_genome() probabilities)
has_dorsal = np.random.uniform() < 0.9
has_pectoral = np.random.uniform() < 0.8
has_pelvic = np.random.uniform() < 0.8
has_hind = np.random.uniform() < 0.8

# Fin placement (matching fish_genome() ranges)
dorsal_u = np.random.uniform(0.30, 0.45)
pectoral_u = np.random.uniform(0.65, 0.80)
pelvic_u = np.random.uniform(0.50, 0.65)
hind_u = np.random.uniform(0.20, 0.30)
pectoral_v_raw = np.random.uniform(55, 65)  # degrees, converted to [0,1] fraction of 180
hind_v_raw = np.random.normal(36, 5)        # degrees

# Dorsal fin params (matching fin_params(scale, dorsal=True))
dorsal_scale_noise = np.array([
    np.clip(np.random.normal(1, 0.1), 0.8, 1.2),
    1.0,
    0.8 * np.clip(np.random.normal(1, 0.1), 0.8, 1.2)
])
dorsal_base_scale = np.array([np.random.uniform(0.4, 0.6), 0.5, 0.2])
dorsal_scale = (dorsal_base_scale * dorsal_scale_noise).astype(np.float32)
dorsal_round = np.random.uniform(0.8, 1.0)
dorsal_rounding_weight = 1.0
dorsal_affine_z = np.random.uniform(0.0, 0.1)
dorsal_offset_z = np.random.uniform(0.6, 1.0)
dorsal_offset_y = 1.0
dorsal_freq = np.random.uniform(100, 150)

# Paired fin params (matching fin_params(scale, dorsal=False))
def sample_fin_params_paired():
    noise = np.array([
        np.clip(np.random.normal(1, 0.1), 0.8, 1.2),
        1.0,
        0.8 * np.clip(np.random.normal(1, 0.1), 0.8, 1.2)
    ])
    return {
        "round_weight": 1.0,
        "rounding_weight": np.random.uniform(0.02, 0.07),
        "affine_z": np.random.uniform(0.8, 1.2),
        "offset_z": np.random.uniform(0.05, 0.2),
        "offset_y": np.random.uniform(0.2, 1.0),
        "freq": np.random.uniform(60, 80),
        "noise": noise,
    }

pectoral_fin_p = sample_fin_params_paired()
pelvic_fin_p = sample_fin_params_paired()
hind_fin_p = sample_fin_params_paired()
tail_fin_p = sample_fin_params_paired()

# Tail
tail_angle = np.random.uniform(140, 170)

# Eyes
eye_radius = max(0.012, np.random.normal(0.036, 0.01))
eye_u = 0.9

_joint_noise = lambda: np.random.normal(0, 7, 3)

# ── helpers ──────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_tf(obj):
    select_only(obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object

# ── NURBS evaluation using scipy BSpline ─────────────────────────────────────

def generate_knotvector_clamped(degree, n):
    middle = np.linspace(0, n, n - degree + 1)[1:-1]
    knot = np.concatenate([np.zeros(degree + 1), middle, np.full(degree + 1, float(n))])
    knot /= knot.max()
    return knot

def generate_knotvector_uniform(degree, n):
    knot = np.arange(0, n + degree + 1, dtype=float)
    knot /= knot.max()
    return knot

def compute_cylinder_topology(n, m, cyclic=True):
    loop = np.arange(m)
    h_neighbors = np.stack([loop, np.roll(loop, -1)], axis=-1)
    ring_start_offsets = np.arange(0, n * m, m)
    ring_edges = ring_start_offsets[:, None, None] + h_neighbors[None]
    if not cyclic:
        ring_edges = ring_edges[:, :-1, :]
    ring_edges = ring_edges.reshape(-1, 2)
    v_neighbors = np.stack([loop, loop + m], axis=-1)
    bridge_offsets = np.arange(0, (n - 1) * m, m)
    bridge_edges = bridge_offsets[:, None, None] + v_neighbors[None]
    bridge_edges = bridge_edges.reshape(-1, 2)
    edges = np.concatenate([ring_edges, bridge_edges])
    face_neighbors = np.concatenate([h_neighbors, h_neighbors[:, ::-1] + m], axis=-1)
    faces = bridge_offsets[:, None, None] + face_neighbors[None]
    if not cyclic:
        faces = faces[:, :-1, :]
    faces = faces.reshape(-1, 4)
    return edges, faces

def eval_nurbs_surface(ctrl_pts, face_size=0.02):
    """Evaluate degree-3 NURBS surface: clamped u, cyclic v."""

    n, m, _ = ctrl_pts.shape
    degree = 3
    ctrl_wrapped = np.concatenate([ctrl_pts, ctrl_pts[:, :degree, :]], axis=1)
    m_wrapped = m + degree
    knots_u = generate_knotvector_clamped(degree, n)
    kv_v_base = generate_knotvector_uniform(degree, m)
    knots_v = np.append(kv_v_base,
                        kv_v_base[1:degree + 1] + kv_v_base[-1] - kv_v_base[0])
    ulength = np.linalg.norm(np.diff(ctrl_pts, axis=0), axis=-1).sum(axis=0).max()
    vlength = np.linalg.norm(np.diff(ctrl_pts, axis=1), axis=-1).sum(axis=1).max()
    delta = face_size / max(ulength, vlength)
    num_eval = max(20, int(1 / delta) + 1)
    u_params = np.linspace(0, 1, num_eval)
    u_params[-1] = 1.0 - 1e-10
    v_start = knots_v[degree]
    v_end = knots_v[m_wrapped]
    nv = num_eval
    v_params = np.linspace(v_start, v_end, nv, endpoint=False)
    bspl_u = BSpline(knots_u, ctrl_wrapped, degree)
    intermediate = bspl_u(u_params)
    inter_t = intermediate.transpose(1, 0, 2)
    bspl_v = BSpline(knots_v, inter_t, degree)
    result = bspl_v(v_params)
    points = result.transpose(1, 0, 2)
    return points, num_eval, nv

# ── body surface helpers ─────────────────────────────────────────────────────

def body_surface_point(surface_pts, nu, nv, u, v_att, radius=1.0, side=1):
    """Find point on body using direction-based lookup."""

    u_idx = min(int(u * (nu - 1) + 0.5), nu - 1)
    angle = math.pi * v_att
    dy = math.sin(angle) * side
    dz = -math.cos(angle)
    direction = np.array([0.0, dy, dz])
    center = surface_pts[u_idx].mean(axis=0)
    offsets = surface_pts[u_idx] - center
    projections = offsets @ direction
    v_idx = int(np.argmax(projections))
    surface_pt = surface_pts[u_idx, v_idx]
    return center + radius * (surface_pt - center)

def body_surface_normal(surface_pts, nu, nv, u, v_att, side=1):
    """Compute approximate outward surface normal at (u, v_att)."""

    u_idx = min(int(u * (nu - 1) + 0.5), nu - 1)
    angle = math.pi * v_att
    dy = math.sin(angle) * side
    dz = -math.cos(angle)
    direction = np.array([0.0, dy, dz])
    center = surface_pts[u_idx].mean(axis=0)
    offsets = surface_pts[u_idx] - center
    v_idx = int(np.argmax(offsets @ direction))
    u_next = min(u_idx + 1, nu - 1)
    u_prev = max(u_idx - 1, 0)
    v_next = (v_idx + 1) % nv
    v_prev = (v_idx - 1) % nv
    du = surface_pts[u_next, v_idx] - surface_pts[u_prev, v_idx]
    dv = surface_pts[u_idx, v_next] - surface_pts[u_idx, v_prev]
    normal = np.cross(du, dv)
    norm_val = np.linalg.norm(normal)
    if norm_val > 1e-8:
        normal /= norm_val
    if normal @ direction < 0:
        normal = -normal
    return normal


def get_body_handles():
    """Generate body handles using the NURBS decompose/recompose pipeline."""

    return recompose_nurbs_handles(body_params)


# ── fish fin builder (faithful replication of nodegroup_fish_fin) ────────────

def float_curve_fin_outline(t):
    """Piecewise linear interpolation of the original fin outline float curve."""

    xs = np.array([0.0068, 0.0455, 0.1091, 0.1955, 0.3205, 0.4955, 0.7545, 0.8705, 1.0])
    ys = np.array([0.0, 0.3812, 0.5419, 0.6437, 0.7300, 0.7719, 0.7350, 0.6562, 0.4413])
    return np.interp(t, xs, ys)

def build_fish_fin(fin_scale, round_weight, freq, offset_weight_z,
                   offset_weight_y=1.0, affine_z=0.0, affine_x=0.0,
                   rounding_weight=0.0,
                   pattern_rotation=(4.0, 0.0, 2.0),
                   noise_ratio_x=0.925, ridge_scale=10.0, n=100,
                   x_clip=0.12, name="fin"):
    """Build a ridged fin mesh faithfully replicating nodegroup_fish_fin."""

    gx = np.linspace(-0.5 + x_clip, 0.5, n)
    gz = np.linspace(-0.5, 0.5, n)
    orig_x_2d, orig_z_2d = np.meshgrid(gx, gz)
    orig_x = orig_x_2d.ravel()
    orig_z = orig_z_2d.ravel()

    x = orig_x.copy()
    z = orig_z.copy()

    shifted_x = orig_x + 0.5
    shifted_z = orig_z + 0.5

    outline = float_curve_fin_outline(shifted_x)
    z += round_weight * (outline - 0.7) + affine_x * (shifted_x + 0.5) * shifted_z
    x += affine_z * shifted_x * shifted_z

    dx = noise_ratio_x * orig_x + 10.0
    dx_term = dx * 0.9 + pattern_rotation[0]
    dz = orig_z + 1.0
    dz_term = (dz * 0.9 + pattern_rotation[2]) * 0.5
    dist = np.sqrt(dx_term**2 + dz_term**2)
    sine_val = np.sin(dist * freq)

    x += sine_val * (0.5 - orig_x) * offset_weight_z * (-0.02) * ridge_scale
    z += sine_val * offset_weight_z * 0.03 * ridge_scale

    power_val = np.abs(sine_val) ** 2.1
    bump_mask = np.clip(0.5 - orig_z, 0, 1)
    y = power_val * bump_mask * offset_weight_z * 0.006 * ridge_scale

    z += 0.4

    sx, sy, sz = fin_scale
    t2_x = sy * y
    t2_y = -sx * x
    t2_z = sz * z

    final_x = t2_z
    final_y = t2_x
    final_z = t2_y

    verts = np.stack([final_x, final_y, final_z], axis=1)

    faces = []
    for jz in range(n - 1):
        for jx in range(n - 1):
            i0 = jz * n + jx
            faces.append((i0, i0 + 1, i0 + n + 1, i0 + n))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    for p in obj.data.polygons:
        p.use_smooth = True

    return obj

# ── fin placement ────────────────────────────────────────────────────────────

def place_fin_on_body(fin_obj, surface_pts, nu, nv, u, v_att, radius, side,
                      joint_euler_deg):
    """Place fin at body surface with global rotation basis."""

    pos = body_surface_point(surface_pts, nu, nv, u, v_att, radius, side=1)

    jr = tuple(math.radians(a) for a in joint_euler_deg)
    rot_mat = BEuler(jr, 'XYZ').to_matrix().to_4x4()

    transform = Matrix.Translation(Vector(pos)) @ rot_mat

    for v in fin_obj.data.vertices:
        co = transform @ Vector((*v.co, 1.0))
        v.co = co.xyz

    if side == -1:
        for v in fin_obj.data.vertices:
            v.co.y = -v.co.y

    fin_obj.data.update()

def boolean_trim_fin(fin_obj, body_obj, margin=0.003):
    """Boolean DIFFERENCE to cleanly cut fin geometry inside the body."""

    select_only(body_obj)
    bpy.ops.object.duplicate()
    body_copy = bpy.context.active_object
    body_copy.name = "body_bool_cutter"

    if margin > 0:
        bm = bmesh.new()
        bm.from_mesh(body_copy.data)
        bm.normal_update()
        for v in bm.verts:
            v.co += Vector(v.normal) * margin
        bm.to_mesh(body_copy.data)
        bm.free()
        body_copy.data.update()

    select_only(fin_obj)
    bool_mod = fin_obj.modifiers.new("trim_body", "BOOLEAN")
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = body_copy
    bool_mod.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    n_remaining = len(fin_obj.data.vertices)
    bpy.data.objects.remove(body_copy, do_unlink=True)
    fin_obj.data.update()
    return 10000 - n_remaining

# ── eye builder ──────────────────────────────────────────────────────────────

def build_iris_cone(radius, name="iris"):
    """Small visible pupil: short flat cone at front of eye."""

    n_seg = 6
    n_ring = 16
    verts, faces = [], []
    seg_total = 0.6 * radius
    for j in range(n_seg + 1):
        t = j / n_seg
        x = 0.4 * radius + t * seg_total
        r = (0.7 * radius) * (1.0 - t * 0.4)
        for k in range(n_ring):
            ang = 2 * math.pi * k / n_ring
            verts.append((x, r * math.cos(ang), r * math.sin(ang) * 1.1))
    for j in range(n_seg):
        for k in range(n_ring):
            i0 = j * n_ring + k
            i1 = j * n_ring + (k + 1) % n_ring
            i2 = (j + 1) * n_ring + (k + 1) % n_ring
            i3 = (j + 1) * n_ring + k
            faces.append((i0, i1, i2, i3))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.rotation_euler = (0.0, 0.0, 0.34910)
    apply_tf(obj)
    return obj


def build_eye(radius=0.028):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, radius=radius,
                                         location=(0, 0, 0))
    eye = bpy.context.active_object
    eye.name = "eye"
    eye.scale = (1.0, 1.0, 0.7)
    apply_tf(eye)
    eye.rotation_euler = (0.0, math.pi / 2, 0.0)
    apply_tf(eye)
    eye.location = (0.1 * radius, 0.0, 0.0)
    apply_tf(eye)
    select_only(eye)
    bpy.ops.object.shade_smooth()

    iris = build_iris_cone(radius, name="iris")
    iris_join = join_objs([eye, iris])
    return iris_join

# ── body mesh builder ────────────────────────────────────────────────────────

def build_body_mesh(handles, face_size=0.02):
    points, nu, nv = eval_nurbs_surface(handles, face_size=face_size)
    verts = points.reshape(-1, 3)
    edges, faces = compute_cylinder_topology(nu, nv, cyclic=True)

    mesh = bpy.data.meshes.new("fish_body")
    mesh.from_pydata(verts.tolist(), edges.tolist(), faces.tolist())
    mesh.update()

    obj = bpy.data.objects.new("fish_body", mesh)
    bpy.context.scene.collection.objects.link(obj)
    select_only(obj)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()

    return obj, points, nu, nv

# ── main assembly ────────────────────────────────────────────────────────────

def build_fish():
    clear_scene()

    # ── 1. Build body ──
    handles = get_body_handles()
    body, surface_pts, nu, nv = build_body_mesh(handles, face_size=0.02)

    # Assign body material
    body.data.materials.append(BODY_MAT)

    # Track parts with their material role: 'body', 'fin', 'eye'
    parts = [body]
    part_roles = ['body']

    # ── 2. Dorsal fin ──
    if has_dorsal:
        dorsal = build_fish_fin(
            fin_scale=dorsal_scale, round_weight=dorsal_round,
            freq=dorsal_freq, offset_weight_z=dorsal_offset_z,
            offset_weight_y=dorsal_offset_y, affine_z=dorsal_affine_z,
            rounding_weight=dorsal_rounding_weight,
            affine_x=0.0, pattern_rotation=(4.0, 0.0, 2.0),
            x_clip=0.0, name="dorsal_fin")
        place_fin_on_body(dorsal, surface_pts, nu, nv,
                          u=dorsal_u, v_att=1.0, radius=0.7, side=1,
                          joint_euler_deg=(0, -100, 0))
        dorsal.data.materials.append(FIN_MAT)
        parts.append(dorsal); part_roles.append('fin')

    # ── 3. Pectoral fins ──
    if has_pectoral:
        pect_base_scale = np.array([0.1, 0.5, 0.3])
        pect_scale = (pect_base_scale * pectoral_fin_p["noise"]).astype(np.float32)
        pect_joint = np.array([20, -13, -205], dtype=float) + _joint_noise()
        pv = pectoral_v_raw / 180.0
        for side in [-1, 1]:
            pect = build_fish_fin(
                fin_scale=pect_scale, round_weight=pectoral_fin_p["round_weight"],
                freq=pectoral_fin_p["freq"],
                offset_weight_z=pectoral_fin_p["offset_z"],
                offset_weight_y=pectoral_fin_p["offset_y"],
                affine_z=pectoral_fin_p["affine_z"],
                rounding_weight=pectoral_fin_p["rounding_weight"],
                affine_x=0.0,
                pattern_rotation=(4.0, 0.0, 2.0), name="pectoral_fin")
            place_fin_on_body(pect, surface_pts, nu, nv,
                              u=pectoral_u, v_att=pv, radius=0.9, side=side,
                              joint_euler_deg=tuple(pect_joint))
            normal = body_surface_normal(surface_pts, nu, nv, u=pectoral_u, v_att=pv, side=side)
            n_vec = Vector(normal).normalized()
            attach = Vector(body_surface_point(surface_pts, nu, nv,
                                               u=pectoral_u, v_att=pv, radius=0.9, side=side))
            flatten_factor = 0.4
            for v in pect.data.vertices:
                offset = Vector(v.co) - attach
                depth = offset.dot(n_vec)
                v.co -= n_vec * depth * (1.0 - flatten_factor)
            pect.data.update()
            inward = -n_vec * 0.008
            for v in pect.data.vertices:
                v.co += inward
            pect.data.update()
            boolean_trim_fin(pect, body, margin=0.020)
            pect.data.materials.append(FIN_MAT)
            parts.append(pect); part_roles.append('fin')

    # ── 4. Pelvic fins ──
    if has_pelvic:
        pelv_base_scale = np.array([0.08, 0.5, 0.25])
        pelv_scale = (pelv_base_scale * pelvic_fin_p["noise"]).astype(np.float32)
        pelv_joint = np.array([20, 28, -205], dtype=float) + _joint_noise()
        pelv_v = np.random.uniform(8, 15) / 180.0
        for side in [-1, 1]:
            pelv = build_fish_fin(
                fin_scale=pelv_scale, round_weight=pelvic_fin_p["round_weight"],
                freq=pelvic_fin_p["freq"],
                offset_weight_z=pelvic_fin_p["offset_z"],
                offset_weight_y=pelvic_fin_p["offset_y"],
                affine_z=pelvic_fin_p["affine_z"],
                rounding_weight=pelvic_fin_p["rounding_weight"],
                affine_x=0.0,
                pattern_rotation=(4.0, 0.0, 2.0), name="pelvic_fin")
            place_fin_on_body(pelv, surface_pts, nu, nv,
                              u=pelvic_u, v_att=pelv_v, radius=0.8, side=side,
                              joint_euler_deg=tuple(pelv_joint))
            pelv.data.materials.append(FIN_MAT)
            parts.append(pelv); part_roles.append('fin')

    # ── 5. Hind/anal fins ──
    if has_hind:
        hind_base_scale = np.array([0.1, 0.5, 0.3])
        hind_scale = (hind_base_scale * hind_fin_p["noise"]).astype(np.float32)
        hind_joint = np.array([20, 28, -205], dtype=float) + _joint_noise()
        hv = hind_v_raw / 180.0
        for side in [-1, 1]:
            hind = build_fish_fin(
                fin_scale=hind_scale, round_weight=hind_fin_p["round_weight"],
                freq=hind_fin_p["freq"],
                offset_weight_z=hind_fin_p["offset_z"],
                offset_weight_y=hind_fin_p["offset_y"],
                affine_z=hind_fin_p["affine_z"],
                rounding_weight=hind_fin_p["rounding_weight"],
                affine_x=0.0,
                pattern_rotation=(4.0, 0.0, 2.0), name="hind_fin")
            place_fin_on_body(hind, surface_pts, nu, nv,
                              u=hind_u, v_att=hv, radius=0.9, side=side,
                              joint_euler_deg=tuple(hind_joint))
            hind.data.materials.append(FIN_MAT)
            parts.append(hind); part_roles.append('fin')

    # ── 6. Tail fins (V-fork) ──
    tail_base_scale = np.array([0.12, 0.5, 0.35])
    tail_scale = (tail_base_scale * tail_fin_p["noise"]).astype(np.float32)
    for vdir in [-1, 1]:
        tail = build_fish_fin(
            fin_scale=tail_scale, round_weight=tail_fin_p["round_weight"],
            freq=tail_fin_p["freq"],
            offset_weight_z=tail_fin_p["offset_z"],
            offset_weight_y=tail_fin_p["offset_y"],
            affine_z=tail_fin_p["affine_z"],
            rounding_weight=tail_fin_p["rounding_weight"],
            affine_x=0.0,
            pattern_rotation=(4.0, 0.0, 2.0), name="tail_fin")
        joint_angle = -tail_angle * vdir
        place_fin_on_body(tail, surface_pts, nu, nv,
                          u=0.05, v_att=0.0, radius=0.0, side=1,
                          joint_euler_deg=(0, joint_angle, 0))
        tail.data.materials.append(FIN_MAT)
        parts.append(tail); part_roles.append('fin')

    # ── 7. Eyes ──
    socket_radius = eye_radius * 1.10

    for side in [-1, 1]:
        eye_pos = body_surface_point(surface_pts, nu, nv,
                                     u=eye_u, v_att=0.6, radius=0.9, side=1)
        eye_normal = body_surface_normal(surface_pts, nu, nv,
                                         u=eye_u, v_att=0.6, side=1)
        if side == -1:
            eye_pos = eye_pos.copy()
            eye_pos[1] = -eye_pos[1]
            eye_normal = eye_normal.copy()
            eye_normal[1] = -eye_normal[1]

        # Carve eye socket in the body mesh using Boolean
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16, ring_count=12,
            radius=socket_radius,
            location=tuple(eye_pos))
        cutter = bpy.context.active_object
        cutter.name = f"eye_cutter_{side}"

        bool_mod = body.modifiers.new("eye_socket", "BOOLEAN")
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cutter
        select_only(body)
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        bpy.data.objects.remove(cutter, do_unlink=True)

        # Create the actual eye sphere in the socket
        eye = build_eye(radius=eye_radius)
        eye.location = tuple(eye_pos)
        apply_tf(eye)

        # Remove inward-facing hemisphere
        n_vec = Vector(eye_normal)
        center = Vector(eye_pos)
        bm = bmesh.new()
        bm.from_mesh(eye.data)
        to_del = [v for v in bm.verts
                  if (Vector(v.co) - center).dot(n_vec) < 0]
        if to_del:
            bmesh.ops.delete(bm, geom=to_del, context='VERTS')
        bm.to_mesh(eye.data)
        bm.free()
        eye.data.update()

        eye.data.materials.append(EYE_MAT)
        parts.append(eye); part_roles.append('eye')

    # Fix normals after Boolean operations
    select_only(body)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()

    # ── 8. Join all parts ──
    result = join_objs(parts)

    # ── 8b. Remove tiny disconnected mesh islands (Boolean edge artifacts) ──
    bm = bmesh.new()
    bm.from_mesh(result.data)
    visited = set()
    islands = []
    for v in bm.verts:
        if v.index in visited:
            continue
        island = []
        stack = [v]
        while stack:
            cur = stack.pop()
            if cur.index in visited:
                continue
            visited.add(cur.index)
            island.append(cur)
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in visited:
                    stack.append(other)
        islands.append(island)
    for island in islands:
        if len(island) < 200:
            bmesh.ops.delete(bm, geom=island, context='VERTS')
    bm.to_mesh(result.data)
    bm.free()
    result.data.update()

    # ── 9. Center (offset_center x=True, z=False) ──
    verts_arr = np.array([v.co for v in result.data.vertices])
    x_center = (verts_arr[:, 0].max() + verts_arr[:, 0].min()) / 2
    for v in result.data.vertices:
        v.co.x -= x_center
    result.data.update()

    return result

# ── run ──────────────────────────────────────────────────────────────────────

fish = build_fish()
fish.name = "FishFactory"
