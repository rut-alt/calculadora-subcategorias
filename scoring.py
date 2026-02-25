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
    Regla automática para fijar x_min según el peso w (en proporción).
    Ejemplo: 7,5% => w=0.075
    """
    if w <= 0:
        return 0.0
    if w >= 0.045:
        return 0.0
    if w >= 0.02:
        return 0.2
    if w >= 0.01:
        return 0.3
    return 0.4


def generate_scale(peso_pct: float, k: int, xmin: Optional[float] = None) -> Dict:
    """
    Genera escala lógica de k categorías para una variable con peso 'peso_pct' (%).

    Devuelve:
    - x(j) equiespaciado en [xmin, 1]
    - contribution(j) = w * x(j)
    - delta(j) = contribution(j) - contribution(j-1)
    - x_min_effective / x_max_effective (para el resumen en Streamlit)
    """
    if k < 2:
        raise ValueError("k debe ser >= 2 (mínimo 2 categorías).")

    w = peso_pct / 100.0

    if xmin is None:
        xmin = xmin_by_weight(w)

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

    # Para el resumen en app.py
    x_min_effective = results[0].x if results else 0.0
    x_max_effective = results[-1].x if results else 0.0

    # Impacto máximo de la variable (en el score total)
    delta_max = w * (x_max_effective - x_min_effective)

    return {
        "peso_pct": float(peso_pct),
        "w": w,
        "k": int(k),
        "xmin": xmin,
        "x_min_effective": x_min_effective,
        "x_max_effective": x_max_effective,
        "delta_max": round(delta_max, 6),
        "delta_max_pct": round(delta_max * 100.0, 4),
        "categories": results,
    }