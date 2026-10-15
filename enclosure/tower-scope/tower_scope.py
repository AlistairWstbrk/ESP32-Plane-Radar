#!/usr/bin/env python3
"""
TOWER SCOPE - desk enclosure for the ESP32 Plane Radar
=======================================================
Parametric CadQuery source.  Run:  python3 tower_scope.py [--icao EHAM] [--rwy 09]

Parts list (unchanged from the stock build):
  * ESP32-C3 Super Mini (22.5 x 18 mm)      * 1.28" round GC9A01 module (240x240)
  * USB-C data cable
No screws, no glue: bayonet bezel, snap-in board clips, friction-pivot yoke,
bayonet pedestal.

Concept: an air-traffic-control tower standing beside a runway.  The radar scope
is the tower cab; the base is the airfield apron with runway markings (multi-colour
inlays), and the owner's airport ICAO code is engraved on the apron.

!! Dimensions marked VERIFY are assumptions about generic modules - measure your
!! parts with calipers and edit the numbers (or print fit_test.stl first).
"""
import argparse, math, os
import cadquery as cq

# ----------------------------------------------------------------- parameters
# --- electronics (VERIFY) ---
DISP_D      = 40.0   # round display PCB outer diameter
DISP_CLR    = 0.8    # total diametral clearance in bezel pocket
WINDOW_D    = 33.6   # visible window (active area is 32.4)
PCB_W, PCB_L, PCB_T = 18.0, 22.6, 1.2   # ESP32-C3 Super Mini
PCB_COMP_H  = 3.5    # tallest part on rear face (USB-C receptacle)
BTN_H       = 1.5    # BOOT tact switch height above PCB
# BOOT button position. X: +ve = viewer's right when looking at the SCREEN from
# the front (so it is on the LEFT as you look at the back). Y: distance up from
# the USB-C end of the PCB.  VERIFY on your board; use fit_test.stl.
BOOT_X, BOOT_Y = -5.0, 4.5
PLUG_W, PLUG_T = 15.0, 8.0   # USB-C plug overmould opening in the head

# --- head ---
R_OUT   = 29.0       # head outer radius (58 mm puck)
R_BORE  = 22.5
ZW      = 3.4        # rear wall thickness
D_IN    = 13.7       # interior depth rim -> rear inner wall
H_HEAD  = ZW + D_IN  # rim height (17.1)
FACE_T  = 3.0        # bezel face thickness
SKIRT_L = 6.0
PCB_FRONT_DEPTH = 9.0
Z_PIVOT = 10.0       # pivot height on head axis

# --- bayonet ---
LUG_ARC, NOTCH_ARC, TRAVEL = 22.0, 30.0, 30.0

# --- pedestal / base ---
BASE_X, BASE_Y, BASE_T, BASE_R = 104.0, 76.0, 12.0, 8.0
SKIN_T, COUNTERBORE = 3.0, 1.2
PED_YC   = 12.0      # pedestal centre on base (towards the rear)
Z_TOP    = 62.0      # top of the tower cab plate above base top
Z_PIVOT_W = Z_TOP + 34.0
YOKE_GAP = 57.7      # inner distance between yoke arms (head is 58.0 -> preload)
TILT_DEG = 20.0

TOL = 0.2
WIND_XY = (40.0, 27.0)   # windsock pole position on the base

# ------------------------------------------------------------------ helpers
def rrect(w, d, r, z0, h):
    return (cq.Workplane("XY").workplane(offset=z0).rect(w, d).extrude(h)
            .edges("|Z").fillet(r))

def cyl(r, z0, h, x=0, y=0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(h)

def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False)
            .translate((x0, y0, z0)))

def sector(r0, r1, a0, a1, z0, h, cx=0, cy=0):
    """annular sector, angles in degrees, extruded from z0 by h"""
    n = max(2, int(abs(a1-a0)/3)+1)
    pts_o = [(cx+r1*math.cos(math.radians(a0+(a1-a0)*i/n)),
              cy+r1*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)]
    pts_i = [(cx+r0*math.cos(math.radians(a1-(a1-a0)*i/n)),
              cy+r0*math.sin(math.radians(a1-(a1-a0)*i/n))) for i in range(n+1)]
    return (cq.Workplane("XY").workplane(offset=z0)
            .polyline(pts_o+pts_i).close().extrude(h))

def rot_z(w, a, cx=0, cy=0):
    return w.rotate((cx, cy, 0), (cx, cy, 1), a)

def text(s, size, depth, x, y, z, rot=0.0, bold=False):
    t = (cq.Workplane("XY").workplane(offset=z)
         .text(s, size, depth, combine=False, halign="center", valign="center",
               kind="bold" if bold else "regular"))
    t = t.rotate((0, 0, 0), (0, 0, 1), rot).translate((x, y, 0))
    return t

# =================================================================== HEAD
def make_head():
    h = H_HEAD
    body = cyl(R_OUT, 0, h)
    body = body.faces("<Z").edges().fillet(3.5)
    body = body.faces(">Z").edges().chamfer(0.4)
    body = body.cut(cyl(R_BORE, ZW, h))                      # interior bore

    # bayonet receiver (groove + entry notches) for the bezel lugs
    zg0 = h - 5.6 - 0.2
    gh  = 2.6 + 0.4
    for k in range(3):
        a = 90 + 120*k            # locked lug centre (none at 270 = wire notch)
        body = body.cut(sector(R_BORE-0.1, 23.9, a-LUG_ARC/2-3, a+LUG_ARC/2+3, zg0, gh))
        n = a - TRAVEL            # entry notch centre
        body = body.cut(sector(R_BORE-0.1, 23.9, n-NOTCH_ARC/2, n+NOTCH_ARC/2, zg0, h-zg0+1))
        # travel groove between notch and locked position
        body = body.cut(sector(R_BORE-0.1, 23.9, n, a+LUG_ARC/2+3, zg0, gh))

    # USB-C plug opening, bottom of the head
    zc = ZW + D_IN - PCB_FRONT_DEPTH + PCB_T          # pcb rear face z ... see below
    pcb_rear = h - PCB_FRONT_DEPTH - 0.0              # z of pcb FRONT face
    pcb_rear = pcb_rear - PCB_T                        # z of pcb REAR face
    usb_zc = pcb_rear - 1.63
    body = body.cut(box(-PLUG_W/2, PLUG_W/2, -R_OUT-1, -R_BORE+3,
                        usb_zc-PLUG_T/2, usb_zc+PLUG_T/2))

    # PCB clips: y of PCB bottom edge
    pcb_y0 = -20.0
    pcb_yc = pcb_y0 + PCB_L/2
    pcb_front = h - PCB_FRONT_DEPTH
    hw = PCB_W/2 + 0.2
    for sx in (-1, 1):
        for dy in (-7, 7):
            yy = pcb_yc + dy
            x0, x1 = sorted((sx*hw, sx*(hw+1.4)))
            body = body.union(box(x0, x1, yy-1.6, yy+1.6, ZW-0.5, pcb_front+1.0))       # finger
            xs0, xs1 = sorted((sx*(hw-1.2), sx*hw))
            body = body.union(box(xs0, xs1, yy-1.6, yy+1.6, ZW-0.5, pcb_rear))          # shoulder
            xl0, xl1 = sorted((sx*(hw-0.6), sx*hw))
            lip = box(xl0, xl1, yy-1.6, yy+1.6, pcb_front+0.1, pcb_front+1.0)
            body = body.union(lip)
    # display back-pressure posts (stop display rattling)
    disp_back = h - SKIRT_L
    for a in (45, 135, 225, 315):
        px, py = 17.8*math.cos(math.radians(a)), 17.8*math.sin(math.radians(a))
        body = body.union(cyl(2.0, ZW-0.5, disp_back-0.25-(ZW-0.5), px, py))

    # BOOT plunger hole (rear)
    bx = BOOT_X
    by = pcb_y0 + BOOT_Y
    body = body.cut(cyl(2.0, -1, ZW+2, bx, by))

    # pivot blind holes
    for sx in (-1, 1):
        hole = (cq.Workplane("YZ").workplane(offset=sx*(R_OUT-3.0) if sx > 0 else -R_OUT)
                .center(0, Z_PIVOT).circle(2.2).extrude(3.0))
        body = body.cut(hole)

    # radar engraving on the rear: range rings + sweep + blips
    for r in (8.0, 15.0, 22.0):
        ring = cyl(r+0.4, -0.5, 1.1).cut(cyl(r-0.4, -1, 3))
        body = body.cut(ring.cut(cyl(2.9, -2, 5, bx, by)))   # leave plunger area clean
    sweep = box(0.0, 24.0, -0.4, 0.4, -0.5, 0.6)
    sweep = rot_z(sweep, 38)
    body = body.cut(sweep)
    for (r, a) in ((12.0, 70), (19.0, 20), (16.0, 100)):
        body = body.cut(cyl(1.3, -0.5, 1.1, r*math.cos(math.radians(a)), r*math.sin(math.radians(a))))
    return body

def make_plunger():
    """z=0 is the flange underside (rests on the inner rear wall). Stem runs to -z
    through the wall and protrudes 3.0 mm; the cap presses on the tip."""
    return cyl(2.5, 0, 1.2).union(cyl(1.7, -(ZW+3.0), ZW+3.0))

def make_cap():
    """beacon-dome button cap; the blind hole presses onto the stem tip"""
    cap = cyl(4.6, 0, 2.6).faces(">Z").edges().fillet(1.0)
    return cap.cut(cyl(1.6, -0.1, 2.1))

# ================================================================== BEZEL
def make_bezel():
    h0 = H_HEAD
    face = cyl(R_OUT, h0, FACE_T)
    face = face.faces(">Z").edges().chamfer(0.5)
    skirt = cyl(22.2, h0-SKIRT_L, SKIRT_L)
    b = face.union(skirt)
    b = b.cut(cyl(DISP_D/2+DISP_CLR/2, h0-SKIRT_L-0.1, SKIRT_L+0.1))   # display pocket
    # window with a chamfered view-cone
    win = cyl(WINDOW_D/2, h0-1, FACE_T+2)
    b = b.cut(win)
    cone = (cq.Workplane("XY").workplane(offset=h0+FACE_T-0.9).circle(WINDOW_D/2)
            .workplane(offset=0.9).circle(WINDOW_D/2+0.9).loft())
    b = b.cut(cone)
    # bayonet lugs
    zl = h0 - 5.6
    for k in range(3):
        a = 90 + 120*k
        b = b.union(sector(21.9, 23.4, a-LUG_ARC/2, a+LUG_ARC/2, zl, 2.6))
    # wire notch at the bottom (pin header side)
    b = b.cut(box(-9, 9, -23, -17.5, h0-SKIRT_L-0.1, h0+0.01))
    # engraved bezel: ticks, cardinal letters
    top = h0 + FACE_T
    depth = 0.5
    for i in range(36):
        ang = i*10
        major = (ang % 30 == 0)
        r0, r1 = (22.0, 26.0) if major else (24.2, 26.0)
        wdt = 0.7 if major else 0.45
        t = box(r0, r1, -wdt/2, wdt/2, top-depth, top+0.1)
        b = b.cut(rot_z(t, 90 - ang))
    for lbl, ang, size in (("N", 90, 4.4), ("E", 0, 3.4), ("S", -90, 3.4), ("W", 180, 3.4)):
        r = 19.6 if lbl != "N" else 19.6
        x, y = r*math.cos(math.radians(ang)), r*math.sin(math.radians(ang))
        b = b.cut(text(lbl, size, depth+0.1, x, y, top-depth, 0, True))
    # alignment arrow (N) already marked by the larger N; add lock arrow on rim
    tri = (cq.Workplane("XY").workplane(offset=top-depth)
           .polyline([(-1.6, 27.2), (1.6, 27.2), (0, 24.8)]).close().extrude(depth+0.1))
    b = b.cut(tri)
    return b

# ================================================================ PEDESTAL
def make_pedestal():
    zc = -COUNTERBORE
    collar = rrect(50.0, 44.0, 7.0, zc, 4.2)
    collar = collar.faces(">Z").edges().chamfer(1.0)
    # bayonet spigot (below collar)
    spig = cyl(19.0, -6.1, 6.1+zc*-1 - 1.0 + 0.0)  # r19 from -6.1 up to collar bottom
    spig = cyl(19.0, -6.1, 6.1 + zc + 0.1)
    for k in range(3):
        a = 30 + 120*k
        spig = spig.union(sector(18.8, 20.8, a-LUG_ARC/2, a+LUG_ARC/2, -6.1, 2.95))
    lower = collar.union(spig)
    # ATC-tower silhouette: slim shaft, 45-degree flare, flat cab band with a window groove
    z_sh, z_fl, z_cab = Z_TOP-22.0, Z_TOP-8.0, Z_TOP
    shaft = (cq.Workplane("XY").workplane(offset=3.0).slot2D(46, 40)
             .workplane(offset=z_sh-3.0).slot2D(40, 36).loft(combine=True))
    flare = (cq.Workplane("XY").workplane(offset=z_sh).slot2D(40, 36)
             .workplane(offset=z_fl-z_sh).slot2D(68, 36).loft(combine=True))
    cab = cq.Workplane("XY").workplane(offset=z_fl).slot2D(68, 36).extrude(z_cab-z_fl)
    cab = cab.faces(">Z").edges().chamfer(0.8)
    # window band: shallow recess round the cab
    win = (cq.Workplane("XY").workplane(offset=z_fl+2.0).slot2D(70, 38).extrude(3.4)
           .cut(cq.Workplane("XY").workplane(offset=z_fl+1.0).slot2D(66.8, 34.8).extrude(5.4)))
    balcony = cq.Workplane("XY").workplane(offset=z_fl-1.2).slot2D(71, 39).extrude(1.2)
    ped = lower.union(shaft).union(flare).union(cab).union(balcony).cut(win)
    # yoke arms + pivot pins
    for sx in (-1, 1):
        xi = sx*YOKE_GAP/2
        xo = sx*(YOKE_GAP/2 + 3.0)
        x0, x1 = sorted((xi, xo))
        arm = box(x0, x1, -8.0, 8.0, Z_TOP-2, Z_PIVOT_W)
        knob = (cq.Workplane("YZ").workplane(offset=x0).center(0, Z_PIVOT_W)
                .circle(8.0).extrude(x1-x0))
        arm = arm.union(knob)
        # pin
        pin = (cq.Workplane("YZ").workplane(offset=min(xi, xi - sx*2.6))
               .center(0, Z_PIVOT_W).circle(2.0).extrude(2.6))
        ped = ped.union(arm).union(pin)
    # chamfer pin tips
    # cable bore through everything
    bore = (cq.Workplane("XY").workplane(offset=-8).rect(16, 28).extrude(Z_TOP+10)
            .edges("|Z").fillet(6.0))
    ped = ped.cut(bore)
    # decorative: engraved window bands on the stem (tower look)
    for zz in (10.0, 15.0, 20.0, 25.0):            # floor lines on the shaft
        f = (zz-3.0)/(z_sh-3.0)
        L, W = 46-6*f, 40-4*f
        slab = box(-40, 40, -30, 30, zz, zz+0.9)
        keep = cq.Workplane("XY").workplane(offset=zz-1).slot2D(L-1.6, W-1.6).extrude(3)
        ped = ped.cut(slab.cut(keep))
    return ped.translate((0, 0, 0))

# ==================================================================== BASE
def make_base(icao="EHAM", rwy="09", coords=None):
    T = BASE_T
    body = rrect(BASE_X, BASE_Y, BASE_R, -T, T)
    body = body.faces(">Z").edges().chamfer(1.5)
    body = body.faces("<Z").edges().chamfer(0.6)
    cav = rrect(BASE_X-4.8, BASE_Y-4.8, BASE_R-2.4, -T-0.1, T-SKIN_T+0.1)
    body = body.cut(cav)
    # counterbore + bayonet hole in skin
    cb = rrect(50.4, 44.4, 7.2, -COUNTERBORE, COUNTERBORE+0.1).translate((0, PED_YC, 0))
    body = body.cut(cb)
    body = body.cut(cyl(19.35, -SKIN_T-0.1, SKIN_T+0.2, 0, PED_YC))
    for k in range(3):
        a = 30 + 120*k - TRAVEL
        body = body.cut(sector(18.0, 21.3, a-NOTCH_ARC/2, a+NOTCH_ARC/2, -SKIN_T-0.1, SKIN_T+0.2, 0, PED_YC))
        a2 = 30 + 120*k + LUG_ARC/2 + 1.0
        body = body.union(sector(19.5, 21.6, a2, a2+4.0, -SKIN_T-3.6, 3.7, 0, PED_YC))  # stop
    # cable lane ribs + exit notch (rear), plate cutout handled in plate
    for sx in (-1, 1):
        body = body.union(box(sx*10.2 - 0.8, sx*10.2 + 0.8, PED_YC+19.6, BASE_Y/2-2.4, -T, -SKIN_T+0.1))
    body = body.cut(box(-8.5, 8.5, BASE_Y/2-3.0, BASE_Y/2+1, -T-0.1, -3.4))
    # windsock pole socket (boss under the skin, hole open on the top face)
    body = body.union(cyl(5.0, -SKIN_T-6.6, 6.7, *WIND_XY))
    body = body.cut(cyl(2.1, -9.0, 9.1, *WIND_XY))
    return body

def make_markings(icao="EHAM", rwy="09", coords=""):
    """returns (white, yellow) inlay solids, 0.8 thick, flush with base top (z 0)"""
    d = 0.8
    z0 = -d
    hx = BASE_X/2 - 5.0
    white, yellow = None, None
    def add(a, b):
        return b if a is None else a.union(b)
    # runway edge lines
    for yy in (-35.2, -18.8):
        white = add(white, box(-hx, hx, yy-0.4, yy+0.4, z0, 0))
    # centreline dashes
    for i in range(-2, 3):
        white = add(white, box(i*12.0-3.5, i*12.0+3.5, -27.0-0.6, -27.0+0.6, z0, 0))
    # thresholds (6 bars each end)
    for end in (-1, 1):
        for j in range(6):
            yy = -33.2 + j*2.8
            xa, xb = sorted((end*(hx-1.0), end*(hx-7.0)))
            white = add(white, box(xa, xb, yy-0.5, yy+0.5, z0, 0))
    # designators
    r2 = rwy
    other = f"{(int(rwy)+18) % 36 or 36:02d}"
    white = add(white, text(r2, 6.5, d, -33.0, -27.0, z0, -90, True))
    white = add(white, text(other, 6.5, d, 33.0, -27.0, z0, 90, True))
    # apron text: ICAO left; coords right
    white = add(white, text(icao.upper(), 8.0, d, -38.0, 12.0, z0, 90, True))
    if coords:
        white = add(white, text(coords, 2.6, d, 40.0, 4.0, z0, 90))
    # hold-short lines (yellow): solid pair + dashed pair
    for yy in (-15.6, -14.3):
        yellow = add(yellow, box(-hx, hx, yy-0.45, yy+0.45, z0, 0))
    n = int(2*hx // 4.0)
    for yy in (-12.6, -11.3):
        for i in range(0, n, 2):
            xs = -hx + i*4.0
            yellow = add(yellow, box(xs, xs+2.6, yy-0.45, yy+0.45, z0, 0))
    return white, yellow

def make_plate():
    T = BASE_T
    w, d = BASE_X-4.8-0.3, BASE_Y-4.8-0.3
    plate = rrect(w, d, BASE_R-2.7, -T, 2.5)
    # crush ribs
    for sx in (-1, 1):
        for yy in (-20, 0, 20):
            plate = plate.union(box(sx*w/2 - (0.35 if sx < 0 else 0), sx*w/2 + (0.35 if sx > 0 else 0)*1 + (0 if sx > 0 else -0.0) - (0 if sx>0 else 0),
                                    yy-3, yy+3, -T, -T+2.5))
    for sy in (-1, 1):
        for xx in (-30, 30):
            plate = plate.union(box(xx-3, xx+3, sy*d/2 - (0.35 if sy < 0 else 0),
                                    sy*d/2 + (0.35 if sy > 0 else 0), -T, -T+2.5))
    # cable lane cutout (open to desk), thumb notch
    plate = plate.cut(box(-8.5, 8.5, PED_YC+12, BASE_Y/2, -T-1, 0))
    plate = plate.cut(cyl(5.0, -T-1, 6, 0, -d/2))
    # feet recesses
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate = plate.cut(cyl(5.2, -T-0.1, 0.9, sx*38, sy*24))
    # anti-rotation pegs for pedestal bayonet
    for k in range(3):
        a = 30 + 120*k - LUG_ARC/2 - 6.0
        plate = plate.union(sector(19.0, 21.4, a, a+3.5, -T+2.5-0.1, 4.3, 0, PED_YC))
    return plate

# =============================================================== WINDSOCK
def make_pole():
    """pole: bottom end sits in the base socket, ball tip stops the windsock"""
    return cyl(2.0, 0, 50.0).union(cyl(3.2, 50.0, 3.0).faces(">Z").edges().fillet(1.2))

def make_windsock():
    """free-spinning windsock; slides onto the pole from below (before inserting
    the pole in the base).  Cone axis = +X, pole axis = Z through the origin."""
    sleeve = cyl(3.6, -4.0, 8.0).cut(cyl(2.4, -5, 10))
    cone_o = (cq.Workplane("YZ").workplane(offset=5.0).circle(5.6)
              .workplane(offset=26.0).circle(2.4).loft(combine=True))
    cone_i = (cq.Workplane("YZ").workplane(offset=4.9).circle(4.7)
              .workplane(offset=26.2).circle(1.6).loft(combine=True))
    cone = cone_o.cut(cone_i)
    bridge = box(2.5, 6.0, -1.1, 1.1, 0.0, 5.2)
    return sleeve.union(cone).union(bridge).cut(cyl(2.4, -5, 10))

# ================================================================ FIT TEST
def make_fit_test():
    """Quick-print coupon: display pocket ring + PCB cradle + BOOT/USB locator."""
    ring = cyl(24, 0, 4).cut(cyl(DISP_D/2+DISP_CLR/2, 1.2, 4)).cut(cyl(WINDOW_D/2, -1, 3))
    ring = ring.cut(box(-9, 9, -30, -17.5, 1.2, 5))
    pad = box(-14, 14, 26, 56, 0, 1.6)
    # PCB-shaped pocket and a BOOT marker hole
    pad = pad.cut(box(-PCB_W/2-0.2, PCB_W/2+0.2, 28, 28+PCB_L+0.4, 0.6, 3))
    pad = pad.cut(box(-8, 8, 20, 29, 0.6, 3))     # USB end opening
    pad = pad.cut(cyl(2.0, -1, 4, BOOT_X, 28+0.2+BOOT_Y))
    return ring.union(pad).union(box(-3, 3, 22, 30, 0, 1.6))

# ==================================================================== EXPORT
def build(icao="EHAM", rwy="09", coords=""):
    parts = {}
    parts["head"] = make_head()
    parts["bezel"] = make_bezel()
    parts["plunger"] = make_plunger()
    parts["cap"] = make_cap()
    parts["pedestal"] = make_pedestal()
    white, yellow = make_markings(icao, rwy, coords)
    base = make_base()
    base = base.cut(white).cut(yellow)
    parts["base"] = base
    parts["inlay_white"] = white
    parts["inlay_yellow"] = yellow
    parts["plate"] = make_plate()
    parts["pole"] = make_pole()
    parts["windsock"] = make_windsock()
    parts["fit_test"] = make_fit_test()
    return parts

def print_orientation(name, w):
    """put each part in its recommended print orientation, bed at z=0"""
    if name == "head":      pass                              # rear on bed already
    elif name == "bezel":   w = w.rotate((0,0,0),(1,0,0),180)  # front face on bed
    elif name == "plunger": pass
    elif name == "cap":     pass
    elif name == "pedestal":w = w.translate((0,0,6.1))
    elif name in ("base", "inlay_white", "inlay_yellow"):
        w = w.rotate((0,0,0),(1,0,0),180)                     # top face on bed
    elif name == "pole":    w = w.rotate((0,0,0),(0,1,0),90)         # lie flat
    elif name == "windsock":w = w.rotate((0,0,0),(0,1,0),-90)        # big end of cone on bed
    elif name == "plate":   w = w.translate((0,0,12.0))
    bb = w.val().BoundingBox()
    return w.translate((0, 0, -bb.zmin))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--icao", default="EHAM")
    ap.add_argument("--rwy", default="09")
    ap.add_argument("--coords", default="52.37N 004.90E")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, w in build(a.icao, a.rwy, a.coords).items():
        pw = print_orientation(name, w)
        cq.exporters.export(pw, os.path.join(a.out, f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print("wrote", name)
