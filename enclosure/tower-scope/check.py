import math, cadquery as cq, tower_scope as t
P = t.build()
for n,w in P.items():
    v=w.val(); bb=v.BoundingBox()
    print(f"{n:12s} valid={v.isValid()} solids={len(w.solids().vals())} vol={v.Volume()/1000:.1f}cm3 bbox={bb.xlen:.1f}x{bb.ylen:.1f}x{bb.zlen:.1f}")

def inter(a,b):
    try: return a.intersect(b).val().Volume()
    except Exception as e: return 0.0

# head -> world: local z -> -Y (front faces viewer at -Y), then tilt back about X at pivot
def head_world(w, tilt):
    w = w.translate((0,0,-t.Z_PIVOT))                     # pivot to origin
    w = w.rotate((0,0,0),(1,0,0),90)                      # local z -> -y
    w = w.rotate((0,0,0),(1,0,0),-tilt)                   # tilt back
    return w.translate((0,t.PED_YC,t.Z_PIVOT_W))
ped = P["pedestal"].translate((0,t.PED_YC,0))
for tilt in (-25,0,10,20,25):
    parts = [P["head"], P["bezel"]]
    tot=0
    for p in parts:
        tot+=inter(head_world(p,tilt), ped)
    print(f"tilt {tilt:4d}: head/bezel vs pedestal interference = {tot:.2f} mm3")
# front-face normal check
h=head_world(P["bezel"],20).val().BoundingBox()
print("bezel world bbox y",round(h.ymin,1),round(h.ymax,1),"z",round(h.zmin,1),round(h.zmax,1))
# bezel vs head (assembled, no rotation): should be ~0 volume
print("bezel/head overlap", inter(P["bezel"],P["head"]))
print("plunger/head overlap", inter(P["plunger"].translate((t.BOOT_X,-20+t.BOOT_Y,t.ZW)),P["head"]))
# pedestal vs base
print("ped/base overlap", inter(ped,P["base"]))
print("plate/base overlap", inter(P["plate"],P["base"]))

t.YOKE_GAP=59.0
Q=t.make_pedestal().translate((0,t.PED_YC,0))
print("loose-yoke interference (expect 0):", sum(inter(head_world(p,0),Q) for p in (P["head"],P["bezel"])))
