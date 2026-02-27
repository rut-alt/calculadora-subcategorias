# app.py
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st


# =========================
# Lógica scoring
# =========================

@dataclass(frozen=True)
class CategoryResult:
    j: int
    x: float
    contribution_pct: float
    delta_from_prev_pct: float


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def generate_scale_fixed_weight_manual_x(
    peso_pct: float,   # peso fijo en %
    k: int,
    x_values: List[float],
) -> Dict:
    if k < 2:
        raise ValueError("k debe ser >= 2.")

    xs = list(x_values or [])
    if len(xs) < k:
        xs += [0.0] * (k - len(xs))
    if len(xs) > k:
        xs = xs[:k]
    xs = [clamp01(x) for x in xs]

    results: List[CategoryResult] = []
    prev = 0.0
    for j in range(1, k + 1):
        x = xs[j - 1]
        contrib = float(peso_pct) * x
        delta = contrib - prev if j > 1 else 0.0
        results.append(
            CategoryResult(
                j=j,
                x=round(x, 6),
                contribution_pct=round(contrib, 4),
                delta_from_prev_pct=round(delta, 4),
            )
        )
        prev = contrib

    delta_max_pct = float(peso_pct) * (results[-1].x - results[0].x) if results else 0.0

    return {
        "peso_pct": float(peso_pct),
        "k": int(k),
        "x_values": xs,
        "delta_max_pct": round(delta_max_pct, 4),
        "categories": results,
    }


def scale_to_df(scale: dict, labels: List[str]) -> pd.DataFrame:
    rows = []
    for idx, r in enumerate(scale["categories"]):
        label = labels[idx] if idx < len(labels) else ""
        rows.append(
            {
                "K (j)": r.j,
                "Etiqueta (texto libre)": label,
                "x(j) (normalizado)": r.x,
                "Aporta al score % (peso*x)": r.contribution_pct,
                "Δ vs prev %": r.delta_from_prev_pct,
            }
        )
    return pd.DataFrame(rows)


# =========================
# App (pesos fijos)
# =========================

st.set_page_config(page_title="Taller scoring por tarjetas", layout="wide")
st.title("Taller scoring — pesos fijos + x(j) manual + calculadora inversa")


def init_model():
    raw_pct = [
        ("Antigüedad 1ª contratación", 7.5),
        ("Vinculación: Nº de Ramos con nosotros", 7.5),
        ("Rentabilidad de la póliza actual", 7.5),
        ("Descuentos o Recargos aplicados sobre tarifa", 5.5),
        ("Morosidad: Históricos sin incidencia en devolución (Anotaciones de póliza)", 5.0),
        ("Engagement comercial / Uso de canales propios (App / Área cliente / Web privada)", 4.5),
        ("Frecuencia uso de coberturas complementarias que no emiten siniestralidad.", 4.5),
        ("Total de asegurados en el Total de sus pólizas - Media de asegurados por póliza", 4.5),
        ("Edad", 4.5),
        ("Rentabilidad de la póliza retrospectivo/histórica (LTV)", 4.5),
        ("Tipo de distribución", 4.5),
        ("Vinculación: Coberturas complementarias opcionales", 4.5),
        ("Contactabilidad: Más de X Campos de datos (Tiene App, Teléfono, Mail, etc.).", 4.0),
        ("Edad del asegurado más mayor", 4.0),
        ("Vinculación familiar", 3.0),
        ("Prescriptor", 3.0),
        ("Exposición a comunicaciones de marca (RRSS, mailing…)", 3.0),
        ("Descendencia", 3.0),
        ("Medio de pago", 2.5),
        ("Frecuencia de pago (Periodicidad)", 2.0),
        ("Probabilidad de desglose", 1.5),
        ("Tipo de producto", 1.5),
        ("NPS", 1.5),
        ("Mascotas", 1.5),
        ("Localización (enfocado a potencial de compra)", 1.5),
        ("Autónomo", 1.0),
        ("Siniestralidad (Salud)", 1.0),
        ("Grado de digitalización de la póliza", 0.5),
        ("Profesión", 0.5),
        ("Nivel educativo", 0.5),
        ("Sexo", 0.0),
    ]

    variables = []
    for idx, (name, peso_pct) in enumerate(raw_pct, start=1):
        preset_labels = ["", "", ""]
        preset_x = [0.0, 0.5, 1.0]

        if "Nº de Ramos con nosotros" in name:
            preset_labels = ["0 ramos", "1-2 ramos", "3 o más ramos"]
            preset_x = [0.0, 0.6, 1.0]

        variables.append(
            {
                "id": f"var_{idx:02d}",
                "name": name,
                "peso_pct": float(peso_pct),  # fijo
                "k": 3,
                "labels": preset_labels,
                "x_values": preset_x,
                "notes": "",
            }
        )

    return {
        "variables": variables,
        "settings": {
            "force_best_x1": True,
            "force_worst_x0": False,
            "enforce_monotone_default": True,
        },
    }


if "model" not in st.session_state:
    st.session_state.model = init_model()


def normalize_labels(var: dict):
    k = int(var["k"])
    labels = list(var.get("labels") or [])
    if len(labels) < k:
        labels += [""] * (k - len(labels))
    if len(labels) > k:
        labels = labels[:k]
    var["labels"] = labels


def normalize_x_values(var: dict):
    k = int(var["k"])
    xs = list(var.get("x_values") or [])
    if len(xs) < k:
        xs += [0.0] * (k - len(xs))
    if len(xs) > k:
        xs = xs[:k]
    var["x_values"] = [clamp01(x) for x in xs]


# =========================
# Sidebar
# =========================
with st.sidebar:
    st.image("LOGOTIPO-AES-05.png", use_container_width=True)

    st.subheader("Controles globales")

    st.session_state.model["settings"]["force_best_x1"] = st.toggle(
        "Forzar x(mejor) = 1 (recomendado)",
        value=bool(st.session_state.model["settings"].get("force_best_x1", True)),
    )

    st.session_state.model["settings"]["force_worst_x0"] = st.toggle(
        "Forzar x(peor) = 0 (opcional)",
        value=bool(st.session_state.model["settings"].get("force_worst_x0", False)),
    )

    st.divider()

    raw_sum = sum(float(v.get("peso_pct", 0.0)) for v in st.session_state.model["variables"])
    st.metric("Suma pesos fijos", f"{raw_sum:.2f}%")

    st.divider()

    st.caption("Exporta el estado del taller.")
    st.download_button(
        "⬇️ Descargar JSON del taller",
        data=pd.Series(st.session_state.model).to_json(force_ascii=False, indent=2).encode("utf-8"),
        file_name="taller_scoring.json",
        mime="application/json",
        use_container_width=True,
    )


# =========================
# Tarjetas
# =========================

vars_list = st.session_state.model["variables"]

col1, col2 = st.columns(2, gap="large")
cols = [col1, col2]

force_best = bool(st.session_state.model["settings"].get("force_best_x1", True))
force_worst = bool(st.session_state.model["settings"].get("force_worst_x0", False))
enforce_default = bool(st.session_state.model["settings"].get("enforce_monotone_default", True))

for i, var in enumerate(vars_list):
    normalize_labels(var)
    normalize_x_values(var)

    with cols[i % 2]:
        with st.container(border=True):
            st.subheader(var["name"])

            peso_pct = float(var.get("peso_pct", 0.0))
            st.metric("Peso fijo (%)", f"{peso_pct:.2f}")

            var["k"] = int(
                st.number_input(
                    "k (nº de subcategorías)",
                    min_value=2,
                    max_value=10,
                    value=int(var["k"]),
                    step=1,
                    key=f"k_{var['id']}",
                )
            )

            normalize_labels(var)
            normalize_x_values(var)

            st.markdown("**Etiquetas por categoría (texto libre)**")
            left, right = st.columns(2)
            for j in range(1, int(var["k"]) + 1):
                target = left if j % 2 == 1 else right
                var["labels"][j - 1] = target.text_input(
                    f"K = {j}",
                    value=var["labels"][j - 1],
                    key=f"lbl_{var['id']}_{j}",
                )

            # =========================
            # Edición normal: x(j) manual
            # =========================
            st.markdown("**x(j) manual (0 a 1)**")
            leftx, rightx = st.columns(2)

            enforce_monotone = st.checkbox(
                "Forzar x(j) no decreciente (opcional)",
                value=enforce_default,
                key=f"mono_{var['id']}",
            )

            for j in range(1, int(var["k"]) + 1):
                target = leftx if j % 2 == 1 else rightx
                current = float(var["x_values"][j - 1])

                new_x = target.number_input(
                    f"x para K = {j}",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(current),
                    step=0.01,
                    key=f"x_{var['id']}_{j}",
                )
                new_x = clamp01(new_x)

                if enforce_monotone and j > 1:
                    prev = float(var["x_values"][j - 2])
                    if new_x < prev:
                        new_x = prev

                var["x_values"][j - 1] = new_x

            # anclas (opcionales)
            if force_worst:
                var["x_values"][0] = 0.0
            if force_best:
                var["x_values"][-1] = 1.0

            st.divider()

            # =========================
            # NUEVO: Calculadora inversa
            # =========================
            st.markdown("### Calculadora inversa (de aporte % → x normalizado)")
            st.caption("Introduce cuánto quieres que aporte cada K al score total (%). Se calcula x = aporte / peso.")

            # si peso=0, no tiene sentido pedir aportes >0
            max_aporte = max(0.0, float(peso_pct))

            lc, rc = st.columns(2)

            contrib_targets = []
            for j in range(1, int(var["k"]) + 1):
                target_col = lc if j % 2 == 1 else rc

                # sugerimos el aporte actual como default
                current_x = float(var["x_values"][j - 1])
                suggested_aporte = peso_pct * current_x

                contrib = target_col.number_input(
                    f"Aporte deseado % para K = {j}",
                    min_value=0.0,
                    max_value=float(max_aporte),
                    value=float(suggested_aporte),
                    step=0.1,
                    key=f"ap_{var['id']}_{j}",
                    help=f"Rango: 0 a {max_aporte:.2f} (porque peso={peso_pct:.2f}%).",
                    disabled=(peso_pct <= 0.0),
                )
                contrib_targets.append(float(contrib))

            if st.button("Aplicar aportes → recalcular x(j)", key=f"apply_ap_{var['id']}"):
                if peso_pct <= 0.0:
                    # no aporta nada; dejamos todo a 0 (y mejor=1 no tiene sentido con peso 0, pero no afecta)
                    new_xs = [0.0] * int(var["k"])
                else:
                    new_xs = []
                    for c in contrib_targets:
                        # x = c / peso
                        x = float(c) / float(peso_pct)
                        new_xs.append(clamp01(x))

                # respetar anclas si están activas
                if force_worst:
                    new_xs[0] = 0.0
                if force_best:
                    new_xs[-1] = 1.0

                # si tenías monotonicidad marcada en esta variable, la respetamos
                if enforce_monotone and int(var["k"]) >= 2:
                    for idx in range(1, int(var["k"])):
                        if new_xs[idx] < new_xs[idx - 1]:
                            new_xs[idx] = new_xs[idx - 1]

                var["x_values"] = new_xs

                # limpiar los inputs x_... para que la UI refleje el cambio
                for j in range(1, int(var["k"]) + 1):
                    st.session_state.pop(f"x_{var['id']}_{j}", None)

                st.rerun()

            st.divider()

            var["notes"] = st.text_area(
                "Notas / criterio (opcional)",
                value=var.get("notes", ""),
                key=f"notes_{var['id']}",
            )

            scale = generate_scale_fixed_weight_manual_x(
                peso_pct=peso_pct,
                k=int(var["k"]),
                x_values=var["x_values"],
            )
            df = scale_to_df(scale, var["labels"])

            st.caption(f"Máximo de esta variable (si x=1): {peso_pct:.2f}% del score total")
            st.dataframe(df, use_container_width=True, hide_index=True)


st.divider()
st.subheader("Resumen del modelo")
summary = []
for v in st.session_state.model["variables"]:
    xs = [clamp01(x) for x in (v.get("x_values") or [])]
    summary.append(
        {
            "Variable": v["name"],
            "Peso fijo %": round(float(v.get("peso_pct", 0.0)), 2),
            "k": int(v["k"]),
            "x (preview)": " | ".join([f"{x:.2f}" for x in xs[:3]]) + (" ..." if len(xs) > 3 else ""),
        }
    )
st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
