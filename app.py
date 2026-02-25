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
