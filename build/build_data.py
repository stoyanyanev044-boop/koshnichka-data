import json, re, sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ingredients import ING, UNCOVERED, PANTRY
from recipes import R

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("KZP_SRC", "/tmp/sb/v1"))
OUT = Path(os.environ.get("OUT", ROOT / "docs" / "data.json"))
PHOTOS = ROOT / "docs" / "photos"
CHAINS = {"kaufland": "Kaufland", "lidl": "Lidl", "billa": "Billa", "fantastico": "Fantastico", "tmarket": "T Market"}
meta = json.load(open(SRC / "meta.json"))

def norm_unit(u):
    return u

out = {"date": meta["date"], "chains": {}, "ing": {}, "uncovered": UNCOVERED, "pantry": PANTRY}
report = []
for cid, cname in CHAINS.items():
    items = json.load(open(SRC / "products" / f"{cid}.json"))["items"]
    chain = {}
    for iid, d in ING.items():
        cands = []
        for code, v in items.items():
            name, cat, qty, unit, perkg, price, promo, day = v
            if cat not in d["cats"] or price is None or price <= 0:
                continue
            low = name.lower()
            if not re.search(d["inc"], low):
                continue
            if d["exc"] and re.search(d["exc"], low):
                continue
            assumed = False
            if qty is None or unit is None:
                qty, unit, assumed = d["default"], d["unit"], True
            if unit != d["unit"]:
                # kg vs l for canned tomatoes etc: treat as equivalent mass
                if {unit, d["unit"]} <= {"kg", "l"}:
                    pass
                else:
                    continue
            if d["unit"] == "pcs" and qty < 4:
                continue
            # deli tubs / wheels (8 kg cheese, 13 kg olives, "около 1,5 кг" ham) are sold loose: price is per kg
            if not perkg and d["unit"] in ("kg", "l") and (qty >= 2 or re.search(r"около|ок\.|~", low)):
                perkg, qty = 1, 1.0
            per = price / qty  # price per base unit (kg / l / pcs)
            # sanity: bulk 8kg cheese tubs etc. are per-kg loose, ok; drop absurdly tiny packs
            if d["unit"] in ("kg", "l") and not perkg and qty < 0.1:
                continue
            cands.append(dict(k=code, n=name, p=round(price, 2), q=qty, kg=bool(perkg), per=round(per, 3), pr=bool(promo), a=assumed))
        if not cands:
            continue
        # prefer real sizes over assumed
        cands.sort(key=lambda c: (c["a"], c["per"]))
        # drop outliers: cheapest must be >= 35% of median per-unit (avoids mis-parsed sizes)
        pers = sorted(c["per"] for c in cands)
        med = pers[len(pers) // 2]
        good = [c for c in cands if c["per"] >= 0.35 * med] or cands
        chain[iid] = good[:4]
    out["chains"][cid] = {"name": cname, "stores": meta["chains"][cid]["stores"], "items": chain}
    missing = [i for i in ING if i not in chain]
    report.append(f"{cname}: {len(chain)}/{len(ING)} matched; missing: {missing}")

# ---- city-level prices: median per (city, chain, product) across that chain's stores in the city ----
import statistics
stores = json.load(open(SRC / "stores.json"))
cities_meta = {c["e"]: c for c in json.load(open(SRC / "cities.json"))}
by_city = {}
for stx in stores:
    if stx["c"] in CHAINS:
        by_city.setdefault(stx["e"], {}).setdefault(stx["c"], []).append(stx["id"])
city_out = {}
for e, chains in by_city.items():
    cm = cities_meta.get(e)
    if not cm:
        continue
    cdata = {}
    for cid, sids in chains.items():
        want = {c["k"] for lst in out["chains"][cid]["items"].values() for c in lst}
        vals = {}
        for sid in sids:
            fp = SRC / "prices" / f"{sid}.json"
            if not fp.exists():
                continue
            p = json.load(open(fp))["p"]
            for k in want:
                if k in p and p[k][0]:
                    vals.setdefault(k, []).append((p[k][0], p[k][2]))
        items = {}
        for iid, lst in out["chains"][cid]["items"].items():
            best = None
            for ci, c in enumerate(lst):
                if c["k"] not in vals:
                    continue
                pr = statistics.median(v[0] for v in vals[c["k"]])
                promo = sum(v[1] for v in vals[c["k"]]) * 2 > len(vals[c["k"]])
                per = pr / c["q"]
                cand = (c["a"], per, ci, round(pr, 2), 1 if promo else 0)
                if best is None or cand < best:
                    best = cand
            if best:
                items[iid] = [best[2], best[3], best[4]]
        if items:
            cdata[cid] = {"n": len(sids), "i": items}
    if cdata:
        city_out[e] = {"name": cm["n"], "t": cm.get("t", ""), "obl": cm.get("o", ""), "c": cdata}
out["cities"] = dict(sorted(city_out.items(), key=lambda kv: -sum(v["n"] for v in kv[1]["c"].values())))
report.append(f"cities with our chains: {len(city_out)}")

for iid, d in ING.items():
    out["ing"][iid] = {"bg": d["bg"], "unit": d["unit"], "aisle": d["aisle"], "nut": d["nut"]}
out["recipes"] = R
import os
out["photos"] = sorted(f[:-4] for f in os.listdir(PHOTOS) if f.endswith(".jpg")) if PHOTOS.is_dir() else []
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print("\n".join(report))
print("size", len(json.dumps(out, ensure_ascii=False)))
