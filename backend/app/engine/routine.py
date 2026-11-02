"""AM/PM routine ordering and conflict rules (spec 9.2 step 8).

- Sunscreen is the last AM step and never appears at night.
- Vitamin C is AM only; retinoids and AHA/BHA exfoliants are PM only and never on the same night.
- Exfoliants are 2-3x weekly.
"""

from __future__ import annotations

from app.models import Product, Routine, Step

_AM_ORDER = {"cleanser": 0, "serum": 2, "eye": 3, "moisturiser": 4, "sunscreen": 9}
_PM_ORDER = {"cleanser": 0, "toner_exfoliant": 1, "serum": 2, "eye": 3, "moisturiser": 4}
_SERUM_ORDER_AM = {"vitc": 0, "niacinamide": 1}
_SERUM_ORDER_PM = {"retinoid": 0, "niacinamide": 1}
ALTERNATE_NIGHTS_NOTE = "Alternate nights: never use retinol and the exfoliating toner on the same night."


def _serum_rank(p: Product, order: dict[str, int]) -> int:
    return min((order[a] for a in p.actives if a in order), default=5)


def build_routine(products: tuple[Product, ...]) -> tuple[Routine, list[str]]:
    notes: list[str] = []
    has_retinoid = any("retinoid" in p.actives for p in products)
    has_acid = any(a in ("aha", "bha") for p in products if p.category == "toner_exfoliant" for a in p.actives)
    if has_retinoid and has_acid:
        notes.append(ALTERNATE_NIGHTS_NOTE + " Start retinol on 2 evenings a week.")

    am = [p for p in products if "am" in p.time_of_day and p.category in _AM_ORDER]
    am = [p for p in am if not ({"retinoid", "aha"} & set(p.actives))]  # defensive: never at AM
    am.sort(key=lambda p: (_AM_ORDER[p.category], _serum_rank(p, _SERUM_ORDER_AM), p.id))

    pm = [p for p in products if "pm" in p.time_of_day and p.category in _PM_ORDER]
    pm = [p for p in pm if "vitc" not in p.actives]
    pm.sort(key=lambda p: (_PM_ORDER[p.category], _serum_rank(p, _SERUM_ORDER_PM), p.id))

    def steps(items: list[Product]) -> list[Step]:
        out = []
        for i, p in enumerate(items, start=1):
            note = None
            if (p.category == "toner_exfoliant" or "retinoid" in p.actives) and has_retinoid and has_acid:
                note = ALTERNATE_NIGHTS_NOTE
            elif "retinoid" in p.actives:
                note = "Start on 2 evenings a week and build up slowly."
            elif p.category == "toner_exfoliant":
                note = "Use 2-3 evenings a week, not every night."
            elif p.category == "sunscreen":
                note = "Always the last step. Reapply every 2 hours outdoors."
            out.append(Step(order=i, product_id=p.id, instruction=p.usage, frequency=p.frequency, note=note))
        return out

    return Routine(am=steps(am), pm=steps(pm)), notes
