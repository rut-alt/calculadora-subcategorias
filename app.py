import pandas as pd
import streamlit as st
from scoring import generate_scale, xmin_by_weight

st.set_page_config(page_title="Scoring Calculator", layout="centered")

st.title("Calculadora de subcategorías (scoring 0–1)")
st.caption("Genera valores normalizados, aportación por categoría y saltos entre categorías.")

col1, col2 = st.columns(2)
with col1:
    peso_pct = st.number_input("Peso de la variable (%)", min_value=0.0, max_value=100.0, value=7.5, step=0.5)
with col2:
    k = st.number_input("Número de categorías (k)", min_value=2, max_value=20, value=4, step=1)

w = peso_pct / 100.0
xmin_auto = xmin_by_weight(w)

st.markdown("### Rango (premio/castigo)")
use_custom = st.toggle("Definir x_min manualmente", value=False)

if use_custom:
    xmin = st.slider("x_min", min_value=0.0, max_value=1.0, value=float(min(xmin_auto, 1.0)), step=0.05)
else:
    xmin = None
    st.info(f"x_min automático recomendado: **{xmin_auto}** (según peso)")

res = generate_scale(peso_pct=peso_pct, k=int(k), xmin=xmin)

cats = res["categories"]
df = pd.DataFrame([{
    "Categoría": c.j,
    "x (normalizado)": c.x,
    "Aportación (%)": c.contribution_pct,
    "Salto vs anterior (%)": c.delta_from_prev_pct,
} for c in cats])

st.markdown("### Resultados")
st.dataframe(df, use_container_width=True)

st.markdown("### Resumen")
c1, c2, c3 = st.columns(3)
c1.metric("Peso variable (w)", f"{res['peso_pct']}%")
c2.metric("x_min → x_max", f"{res['x_min_effective']} → {res['x_max_effective']}")
c3.metric("Δ máximo variable", f"{res['delta_max_pct']}%")

st.markdown("### Gráficas")
st.line_chart(df.set_index("Categoría")[["Aportación (%)"]])
st.bar_chart(df.set_index("Categoría")[["Salto vs anterior (%)"]])

st.markdown("### Fórmulas")
st.latex(r"x(j)=x_{min} + (j-1)\cdot\frac{1-x_{min}}{k-1}")
st.latex(r"Score(j)=w\cdot x(j)")
st.latex(r"\Delta = w\cdot (x_{max}-x_{min})")
