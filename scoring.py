from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CategoryResult:
    j: int
    x: float                 # valor normalizado en [xmin, 1]
    contribution: float      # w * x (proporción)
    contribution_pct: float  # w * x en %
    delta_from_prev: float   # incremento vs categoría anterior (proporción)
    delta_from_prev_pct: float


def xmin_by_weight(w: float) -> float:
    """
    Asignación exacta de x_min según los pesos definidos en vuestro modelo.
    w está en proporción (7,5% = 0.075)
    """
    peso_pct = round(w * 100, 1)

    if peso_pct <= 0:
        return 0.0

    mapping = {
        7.5: 0.00,
        5.5: 0.05,
        5.0: 0.10,
        4.5: 0.15,
        4.0: 0.20,
        3.0: 0.25,
        2.5: 0.30,
        2.0: 0.35,
        1.5: 0.40,
        1.0: 0.45,
        0.5: 0.50,
        0.0: 0.0,   # si entra, no aporta
    }

    # Si llega un peso no contemplado (por ejemplo 6,0), devolvemos una regla por defecto razonable
    return mapping.get(peso_pct, 0.20)


def generate_scale(
    peso_pct: float,
    k: int,
    xmin: Optional[float] = None,
    xmin_floor: float = 0.01,  # 👈 suelo mínimo para que la peor categoría sume algo
) -> Dict:
    """
    Genera escala lógica de k categorías para una variable con peso 'peso_pct' (%).

    Devuelve:
    - x(j) equiespaciado en [xmin, 1]
    - contribution(j) = w * x(j)
    - delta(j) = contribution(j) - contribution(j-1)
    - x_min_effective / x_max_effective
    """
    if k < 2:
        raise ValueError("k debe ser >= 2 (mínimo 2 categorías).")

    w = peso_pct / 100.0

    if xmin is None:
        xmin = xmin_by_weight(w)

    # 👇 aplica el suelo mínimo
    xmin = max(float(xmin_floor), float(xmin))
    xmin = max(0.0, min(1.0, float(xmin)))

    results: List[CategoryResult] = []
    prev_contrib = 0.0

    for j in range(1, k + 1):
        if w == 0:
            x = 0.0
        else:
            x = xmin + (j - 1) * (1.0 - xmin) / (k - 1)

        contrib = w * x
        delta = contrib - prev_contrib if j > 1 else 0.0

        results.append(
            CategoryResult(
                j=j,
                x=round(x, 6),
                contribution=round(contrib, 6),
                contribution_pct=round(contrib * 100.0, 4),
                delta_from_prev=round(delta, 6),
                delta_from_prev_pct=round(delta * 100.0, 4),
            )
        )
        prev_contrib = contrib

    x_min_effective = results[0].x if results else 0.0
    x_max_effective = results[-1].x if results else 0.0
    delta_max = w * (x_max_effective - x_min_effective)

    return {
        "peso_pct": float(peso_pct),
        "w": float(w),
        "k": int(k),
        "xmin": float(xmin),
        "x_min_effective": float(x_min_effective),
        "x_max_effective": float(x_max_effective),
        "delta_max": round(float(delta_max), 6),
        "delta_max_pct": round(float(delta_max) * 100.0, 4),
        "categories": results,
    }


def x_value_for_choice(
    peso_pct: float,
    k: int,
    choice_index: int,
    invert: bool = False,
    xmin_floor: float = 0.01,
    xmin: Optional[float] = None,
) -> float:
    """
    Devuelve x(j) para una elección 0..k-1 (según el orden de labels que mostráis).
    invert=True si "más es peor" (invierte el orden).
    """
    if not (0 <= choice_index < k):
        raise ValueError(f"choice_index debe estar en [0, {k-1}]")

    res = generate_scale(peso_pct=peso_pct, k=k, xmin=xmin, xmin_floor=xmin_floor)
    xs = [c.x for c in res["categories"]]  # j=1..k (peor -> mejor)
    if invert:
        xs = list(reversed(xs))
    return float(xs[choice_index])


def contribution_pct_for_choice(
    peso_pct: float,
    k: int,
    choice_index: int,
    invert: bool = False,
    xmin_floor: float = 0.01,
    xmin: Optional[float] = None,
) -> float:
    """
    Devuelve cuánto suma al score total (en %) para choice_index 0..k-1.
    """
    if not (0 <= choice_index < k):
        raise ValueError(f"choice_index debe estar en [0, {k-1}]")

    res = generate_scale(peso_pct=peso_pct, k=k, xmin=xmin, xmin_floor=xmin_floor)
    contribs = [c.contribution_pct for c in res["categories"]]  # peor -> mejor
    if invert:
        contribs = list(reversed(contribs))
    return float(contribs[choice_index])
