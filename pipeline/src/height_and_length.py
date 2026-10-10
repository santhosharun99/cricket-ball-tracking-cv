import numpy as np

print("=== Height (Z) using the same stump ruler, near-stumps point only ===")

# C4: use fitted height/base_y models extended to frame105
height_data_c4 = {93:107, 94:112, 95:118, 96:142, 97:115, 98:137, 99:150, 100:148, 101:148, 102:165, 103:160}
base_y_data_c4 = {93:462, 94:470, 95:478, 96:500, 97:517, 98:535, 99:565, 100:600, 101:618, 102:648, 103:657}

def fit(d):
    fr = np.array(sorted(d.keys()))
    val = np.array([d[f] for f in fr])
    p = np.polyfit(fr, val, 1)
    return np.poly1d(p)

h_fit_c4 = fit(height_data_c4)
by_fit_c4 = fit(base_y_data_c4)

f = 105
ball_y = 693
h = h_fit_c4(f); by = by_fit_c4(f)
scale = h/0.7112
real_z_c4 = (by - ball_y)/scale
print(f"C4 frame{f}: base_y_fit={by:.1f} ball_y={ball_y} scale={scale:.1f} -> real_z={real_z_c4:.3f} (ground truth impact_z=0.187)")

# C5: frame42->60 zoom rate
f0,h0 = 42,95
f1,h1 = 60,112
rate = (h1-h0)/(f1-f0)
base0 = 366
f = 91
ball_y = 382
h = h0 + rate*(f-f0)
by = base0 + rate*(f-f0)
scale = h/0.7112
real_z_c5 = (by-ball_y)/scale
print(f"C5 frame{f}: base_y_fit={by:.1f} ball_y={ball_y} scale={scale:.1f} -> real_z={real_z_c5:.3f} (ground truth stump_z=0.292)")

print()
print("=== Pitch length classification (using official bounce_x answer key) ===")
import json
ex = json.load(open('data/examples.json'))
names = ['C1','C2','C3','C4','C5']
def classify(bx):
    if bx <= 2.0:
        return "Yorker / very full"
    elif bx <= 4.0:
        return "Full length"
    elif bx <= 8.0:
        return "Good length"
    else:
        return "Short of a length / short"

for name, e in zip(names, ex):
    p = e['prediction']
    bx = p['bounce_x']
    print(name, 'bounce_x=', bx, '->', classify(bx), ' kph=', p['kph'])
