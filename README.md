# Scoring Calculator (0–1) – Subcategorías por peso

Calculadora para diseñar subcategorías de variables de scoring:
- Devuelve valores normalizados `x(j)` en `[x_min, 1]`
- Devuelve aportación por categoría `Score(j)=w*x(j)`
- Devuelve saltos entre categorías `ΔScore(j)=Score(j)-Score(j-1)`

## Fórmulas
- `x(j)=x_min + (j-1)*(1-x_min)/(k-1)`
- `Score(j)=w*x(j)`
- `Δ = w*(x_max-x_min)`

## Regla automática de x_min (por peso)
- ≥ 4.5% → x_min=0.0
- 2%–4.49% → x_min=0.2
- 1%–1.99% → x_min=0.3
- < 1% → x_min=0.4

## Ejecutar la app
```bash
pip install -r requirements.txt
streamlit run app.py