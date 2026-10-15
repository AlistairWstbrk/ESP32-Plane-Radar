#!/usr/bin/env python3
"""
SIMPLE DESK CASE - ESP32 Plane Radar (ESP32-C3 Super Mini + 1.28" GC9A01 + USB-C cable)
Three printed bodies + a button: BODY (round puck), BEZEL (snap-on front ring), STAND (weighted
wedge the puck rests in), plus PLUNGER + CAP for the BOOT/range button on the back.
No screws or glue.  Run: python3 simple_case.py   (needs: pip install cadquery)

VERIFY items (measure your parts): DISP_D, WINDOW_D, PCB size, BOOT_X/BOOT_Y, PLUG_W/PLUG_T.
"""
import math, os
import cadquery as cq

# ---- electronics (VERIFY with calipers) ----
DISP_D, DISP_CLR, WINDOW_D = 40.0, 0.8, 33.6
PCB_W, PCB_L, PCB_T = 18.0, 22.6, 1.2
BOOT_X, BOOT_Y = -5.0, 4.5      # +X = viewer's right looking at the screen; Y up from the USB-C end
PLUG_W, PLUG_T = 15.0, 8.0

# ---- body: chunkier than a minimal case ----
R_OUT, R_BORE = 30.0, 22.5      # 60 mm puck, 7.5 mm side walls
ZW, D_IN = 4.0, 13.7            # 4 mm rear wall
H = ZW + D_IN
FACE_T, SKIRT_L = 4.0, 6.0
PCB_FRONT_DEPTH = 9.0
# ---- stand ----
TILT = 20.0                     # screen leans back this many degrees
BASE_X, BASE_Y, BASE_T = 100.0, 72.0, 12.0

def cyl(r, z0, h, x=0, y=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(h)
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))
def rot_z(w, a):
    return w.rotate((0,0,0), (0,0,1), a)

PCB_FRONT = H - PCB_FRONT_DEPTH
PCB_REAR  = PCB_FRONT - PCB_T
PCB_Y0    = -20.0               # USB-C end of the board, local y
USB_ZC    = PCB_REAR - 1.63
BTN_XY    = (BOOT_X, PCB_Y0 + BOOT_Y)

def make_body():
    b = cyl(R_OUT, 0, H).faces("<Z").edges().fillet(4.0)
    b = b.faces(">Z").edges().chamfer(0.5)
    b = b.cut(cyl(R_BORE, ZW, H))
    # snap groove for the bezel
    b = b.cut(cyl(23.3, H-5.2, 1.6).cut(cyl(R_BORE-0.1, H-6, 4)))
    # pry nick on the rim (top)
    b = b.cut(box(-5, 5, R_OUT-2.0, R_OUT+1, H-1.2, H+1))
    # USB-C plug opening, bottom
    b = b.cut(box(-PLUG_W/2, PLUG_W/2, -R_OUT-1, -R_BORE+3, USB_ZC-PLUG_T/2, USB_ZC+PLUG_T/2))
    # board clips (snap in from the front)
    hw, yc = PCB_W/2+0.2, PCB_Y0 + PCB_L/2
    for sx in (-1, 1):
        for dy in (-7, 7):
            y = yc+dy
            s = lambda a, c: sorted((sx*a, sx*c))
            b = b.union(box(*s(hw, hw+1.6), y-1.8, y+1.8, ZW-0.5, PCB_FRONT+1.0))
            b = b.union(box(*s(hw-1.2, hw),  y-1.8, y+1.8, ZW-0.5, PCB_REAR))
            b = b.union(box(*s(hw-0.6, hw),  y-1.8, y+1.8, PCB_FRONT+0.1, PCB_FRONT+1.0))
    # posts that keep the display from rattling
    for a in (45, 135, 225, 315):
        b = b.union(cyl(2.0, ZW-0.5, (H-SKIRT_L-0.25)-(ZW-0.5), 17.8*math.cos(math.radians(a)), 17.8*math.sin(math.radians(a))))
    b = b.cut(cyl(2.0, -1, ZW+2, *BTN_XY))          # button hole
    return b

def make_plunger():
    return cyl(2.5, 0, 1.2).union(cyl(1.7, -(ZW+3.0), ZW+3.0))
def make_cap():
    return cyl(4.6, 0, 2.6).faces(">Z").edges().fillet(1.0).cut(cyl(1.6, -0.1, 2.1))

def make_bezel():
    b = cyl(R_OUT, H, FACE_T).faces(">Z").edges().chamfer(0.6)
    b = b.union(cyl(22.2, H-SKIRT_L, SKIRT_L))
    b = b.cut(cyl(DISP_D/2+DISP_CLR/2, H-SKIRT_L-0.1, SKIRT_L+0.1))
    b = b.cut(cyl(WINDOW_D/2, H-1, FACE_T+2))
    cone = (cq.Workplane("XY").workplane(offset=H+FACE_T-1.0).circle(WINDOW_D/2)
            .workplane(offset=1.0).circle(WINDOW_D/2+1.0).loft())
    b = b.cut(cone)
    for a in (45, 135, 225, 315):                   # snap bumps
        n = 8
        pts = [(23.1*math.cos(math.radians(a-15+30*i/n)), 23.1*math.sin(math.radians(a-15+30*i/n))) for i in range(n+1)]
        pts += [(21.9*math.cos(math.radians(a+15-30*i/n)), 21.9*math.sin(math.radians(a+15-30*i/n))) for i in range(n+1)]
        b = b.union(cq.Workplane("XY").workplane(offset=H-4.9).polyline(pts).close().extrude(1.4))
    b = b.cut(box(-9, 9, -23, -17.5, H-SKIRT_L-0.1, H+0.01))        # wire notch (pin header side)
    # N marker
    b = b.cut(cq.Workplane("XY").workplane(offset=H+FACE_T-0.5)
              .polyline([(-2.0, 27.0), (2.0, 27.0), (0, 24.0)]).close().extrude(0.6))
    return b

def to_world(w):
    """body frame -> assembled frame (rear centre at origin, screen leaning back)"""
    return w.rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(1,0,0),-TILT)

def place():
    """returns (dy, dz) that sits the body in the stand"""
    bb = to_world(make_body()).val().BoundingBox()
    dz = BASE_T + 5.0 - bb.zmin
    dy = -(bb.ymin+bb.ymax)/2
    return dy, dz

def make_stand():
    dy, dz = place()
    T = lambda w: to_world(w).translate((0, dy, dz))
    slab = (cq.Workplane("XY").box(BASE_X, BASE_Y, BASE_T, centered=(True,True,False))
            .edges("|Z").fillet(8.0).faces(">Z").edges().chamfer(1.5).faces("<Z").edges().chamfer(0.6))
    c = T(cq.Workplane("XY").workplane().circle(1).extrude(0.001)).val().Center()  # rear-centre (world)
    saddle = box(-R_OUT*0.85, R_OUT*0.85, c.y-25, c.y+8, BASE_T-0.5, c.z)
    st = slab.union(saddle)
    st = st.cut(T(cyl(R_OUT+0.25, -0.4, 60)))                 # trough the puck rests in
    st = st.cut(T(cyl(6.5, -9, 9.0, *BTN_XY)))                # clearance for the button cap
    # cable: vertical hole under the plug opening + open underside groove out the back
    uc = T(box(-1, 1, -R_OUT-0.5, -R_OUT+0.5, USB_ZC-0.5, USB_ZC+0.5)).val().Center()
    st = st.cut(box(-8.5, 8.5, uc.y-9, uc.y+9, -1, c.z))
    st = st.cut(box(-8.5, 8.5, uc.y-9, BASE_Y/2+1, -1, 9.0))
    for sx in (-1, 1):                                         # bumper recesses
        for sy in (-1, 1):
            st = st.cut(cyl(5.2, -0.1, 0.9, sx*40, sy*26))
    return st

def build():
    return {"body": make_body(), "bezel": make_bezel(), "stand": make_stand(),
            "plunger": make_plunger(), "cap": make_cap()}

def print_orient(n, w):
    if n == "bezel": w = w.rotate((0,0,0),(1,0,0),180)
    bb = w.val().BoundingBox()
    return w.translate((0, 0, -bb.zmin))

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl"); os.makedirs(out, exist_ok=True)
    for n, w in build().items():
        cq.exporters.export(print_orient(n, w), os.path.join(out, n+".stl"), tolerance=0.01, angularTolerance=0.1)
        print("wrote", n)
