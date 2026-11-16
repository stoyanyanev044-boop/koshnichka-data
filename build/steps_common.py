# Step format for the cooking mode.
# t = short headline, d = detailed instruction, tip = optional hint, timer = minutes (optional)
# In text: {2 л} / {1 ч.л.} / {8 тортили/тортила} are scaled to the household size (written for 4 portions);
# word@ing marks an ingredient and shows its scaled amount, word@ing*0.5 = half of it.
def S(t, d, tip=None, timer=None):
    x = {"t": t, "d": d}
    if tip:
        x["tip"] = tip
    if timer:
        x["timer"] = timer
    return x

STEPS = {}

def R(id, eq, *steps):
    STEPS[id] = {"eq": eq, "steps": list(steps)}
