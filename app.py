import streamlit as st
import pandas as pd
from scoring import generate_scale, xmin_by_weight

st.set_page_config(page_title="Calculadora Subcategorías", layout="centered")

st.title("🔢 Calculadora de Subcategorías - Modelo de Scoring")

st.markdown("""
Esta herramienta genera automáticamente los valores de cada subcategoría
según el peso de la variable dentro del modelo de scoring.
""")

col1, col2 = st.columns(2)

with col1:
    peso_pct = st.number_input("Peso de la variable (%)", 0.0, 100.0, 7.5, step=0.5)

with col2:
    k = st.number_input("Número de categorías (k)", 2, 10, 4)

w = peso_pct / 100
xmin_auto = xmin_by_weight(w)

st.markdown("### Configuración del rango")

use_custom = st.toggle("Definir x_min manualmente")

if use_custom:
    xmin = st.slider("x_min", 0.0, 1.0, float(xmin_auto), step=0.05)
else:
    xmin = None
    st.info(f"x_min recomendado automáticamente según el peso: {xmin_auto}")

res = generate_scale(peso_pct=peso_pct, k=int(k), xmin=xmin)

cats = res["categories"]

df = pd.DataFrame([{
    "Categoría": c.j,
    "Valor normalizado (x)": c.x,
    "Aportación al Score (%)": c.contribution_pct,
    "Incremento vs anterior (%)": c.delta_from_prev_pct,
} for c in cats])

st.markdown("### 📊 Resultados")
st.dataframe(df, use_container_width=True)

st.markdown("### 🧠 Impacto máximo de la variable")
st.metric("Impacto máximo posible en el Score (%)", res["delta_max_pct"])

st.markdown("---")
st.markdown("## 📐 Fórmulas del modelo y significado")

st.latex(r"x(j)=x_{min} + \frac{(j-1)(1-x_{min})}{k-1}")

st.markdown("""
**¿Qué significa esta fórmula?**

Calcula el valor normalizado de cada categoría.

- `j` → número de la categoría (1 es la peor, k es la mejor)
- `x_min` → valor mínimo permitido según el peso de la variable
- `k` → número total de categorías

La fórmula reparte los valores de forma equidistante entre `x_min` y 1.
""")

st.latex(r"Score(j)=w\cdot x(j)")

st.markdown("""
**¿Qué significa esta fórmula?**

Calcula cuánto aporta esa categoría al score total del cliente.

- `w` → peso de la variable (por ejemplo 7,5% = 0,075)
- `x(j)` → valor normalizado de la categoría

El resultado es el porcentaje real que esa categoría suma al scoring total.
""")

st.latex(r"\Delta = w \cdot (x_{max}-x_{min})")

st.markdown("""
**¿Qué significa esta fórmula?**

Indica el impacto máximo que puede tener la variable dentro del modelo.

- `x_max` normalmente es 1
- `x_min` depende del peso
- `w` es el peso de la variable

Cuanto mayor sea este valor, mayor capacidad tiene la variable para
premiar o castigar dentro del modelo.
""")
