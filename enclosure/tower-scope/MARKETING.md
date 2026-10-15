# TOWER SCOPE — go-to-market notes

## Positioning
Not "a case for a gadget" — **a desk object with a story**: *the live airspace over your home, in an air-traffic
control tower, on a runway with your airport's name on it.* Appeals to aviation fans, spotters, pilots' gifts,
desk-gadget people. Hero shot = tower + windsock + ICAO code; second shot = the display tilted showing live traffic.

## Why it beats a generic case
- Silhouette is recognisable in a thumbnail (tower + windsock).
- Personalised per buyer (ICAO, runway number, coordinates) — a reason to buy from you rather than print it.
- Tool-less assembly, no hardware, zero extra BOM.
- Colourways: "Schiphol night" (dark base/white), "Tarmac" (grey/yellow), "Glass cab" (translucent head), "Hi-vis".

## Product tiers (suggestion, not validated)
1. **STL licence** (MakerWorld/Printables/Etsy): personal print licence; commercial-print licence tier.
2. **Printed enclosure kit** (assembled, painted inlays, windsock) — your cost is mostly print time (~14 h per set).
3. **Complete flashed unit** — highest margin, but see the data-licence caveat below.

## Things to settle BEFORE selling
- **adsb.fi data terms.** Third-party sources describe adsb.fi's public API as personal / non-commercial with
  1 req/s limit (I couldn't reach their official terms page — **confirm at opendata.adsb.fi**). Selling pre-flashed
  units that call it is commercial use. Options: sell enclosure-only (user supplies firmware), get written
  permission, or switch the firmware to a source that allows commercial use.
- **Firmware licence:** repo is MIT (© 2026 MatixYo) — fine to ship, keep the licence notice and credit the author.
- **Their MakerWorld case:** this design is independent; do not copy its STL or imagery. Don't call it
  "official"; credit the firmware as "compatible with the ESP32-Plane-Radar firmware".
- **Names/marks:** check "Tower Scope" for existing trademarks before you print it on packaging.
- **Fit:** validate on at least 3 different display-module batches; GC9A01 board sizes vary between suppliers
  — either source one module and sell the kit, or ship 2 bezel sizes.
- **Printing for sale:** PETG/ASA recommended (car-dashboard heat, matte finish); sand/prime the head if you want
  a retail look; inlay printing needs a multi-colour printer (AMS/MMU) or paint.

## Next steps I'd suggest
1. Print `fit_test.stl`, measure parts, update the 4 VERIFY numbers.
2. Prototype one full set; photograph with real traffic on the screen.
3. Airport configurator (pick ICAO → runway heading/designators) to automate personalisation.
