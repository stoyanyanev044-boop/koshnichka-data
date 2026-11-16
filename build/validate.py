"""Проверка преди публикуване: ако данните изглеждат счупени, работният процес спира
и старият data.json остава. GitHub праща имейл при провал."""
import json, sys
from datetime import date
from pathlib import Path

new = json.load(open(sys.argv[1]))
old_p = Path(sys.argv[2]) if len(sys.argv) > 2 else None
old = json.load(open(old_p)) if old_p and old_p.exists() else None
errors = []

n_ing = len(new["ing"])
for cid, c in new["chains"].items():
    cov = len(c["items"]) / n_ing
    if cov < 0.7:
        errors.append(f"{c['name']}: само {cov:.0%} от продуктите имат цена")
if len(new["chains"]) < 4:
    errors.append(f"само {len(new['chains'])} вериги")
if len(new.get("cities", {})) < 50:
    errors.append(f"само {len(new.get('cities', {}))} града")
age = (date.today() - date.fromisoformat(new["date"])).days
if age > 7:
    errors.append(f"данните са от {new['date']} ({age} дни назад) — изворът е спрял да се обновява")
if old:
    if new["date"] < old["date"]:
        errors.append(f"новите данни ({new['date']}) са по-стари от публикуваните ({old['date']})")
    # рязка промяна в цените = вероятно счупено разпознаване на продукт
    for cid, c in new["chains"].items():
        for ing, lst in c["items"].items():
            o = old["chains"].get(cid, {}).get("items", {}).get(ing)
            if o and lst and o[0]["per"] and not (0.4 < lst[0]["per"] / o[0]["per"] < 2.5):
                print(f"внимание: {c['name']} {ing}: {o[0]['per']} → {lst[0]['per']} за единица")

if errors:
    print("СПИРАМ, не публикувам:\n- " + "\n- ".join(errors))
    sys.exit(1)
print(f"OK: {new['date']}, {len(new['chains'])} вериги, {len(new['cities'])} града, {len(new['recipes'])} рецепти")
