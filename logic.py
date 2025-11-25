from collections import defaultdict
from constants import CONVERSION

def normalize(amount, unit):
    if unit in CONVERSION:
        target_unit, factor = CONVERSION[unit]
        return amount * factor, target_unit
    return amount, unit

def aggregate(selected):
    """
    selected: list of tuples (ingredients_of_recipe, factor)
    ingredients_of_recipe: list of (name, unit, amount)
    """
    agg = defaultdict(float)  # key = (name, unit)
    for items, factor in selected:
        for name, unit, amount in items:
            a, u = normalize(float(amount) * factor, unit)
            agg[(name, u)] += a
    return sorted(((k[0], round(v, 2), k[1]) for k, v in agg.items()),
                  key=lambda x: x[0].lower())
