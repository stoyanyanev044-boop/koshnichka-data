# Quantities for 4 servings. g for kg-items, ml for l-items, count for pcs.
# Only products that exist in the KZP price data; spices/salt/water are assumed at home (pantry).
# tags: veg | fish | pork | chicken (main protein), oven, quick (<=35 min)
R = []

def M(id, name, cuisine, min, tags, ing, pan, steps, meal="main"):
    R.append(dict(id=id, name=name, cuisine=cuisine, min=min, tags=tags, ing=ing, pan=pan, steps=steps, meal=meal, un=[]))

from recipes_main import add_main
from recipes_breakfast import add_breakfast
add_main(M)
add_breakfast(M)
from recipes_more import add_more, add_more_breakfast
add_more(M)
add_more_breakfast(M)

import steps_bg1, steps_bg1b, steps_bg2, steps_intl, steps_breakfast
from steps_common import STEPS
for _r in R:
    if _r["id"] in STEPS:
        _r["steps"] = STEPS[_r["id"]]["steps"]
        _r["eq"] = STEPS[_r["id"]]["eq"]
