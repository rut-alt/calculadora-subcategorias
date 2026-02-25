import argparse
from scoring import generate_scale

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--peso", type=float, required=True, help="Peso en % (ej: 7.5)")
    p.add_argument("--k", type=int, required=True, help="Número de categorías (>=2)")
    p.add_argument("--xmin", type=float, default=None, help="x_min manual (opcional)")
    args = p.parse_args()

    res = generate_scale(args.peso, args.k, args.xmin)

    print(f"Peso: {res['peso_pct']}% | k={res['k']} | xmin={res['xmin']}")
    print(f"Δ máximo variable: {res['delta_max_pct']}%")
    print("-" * 60)
    for c in res["categories"]:
        print(
            f"Cat {c.j}: x={c.x:.4f} | aport={c.contribution_pct:.4f}% | "
            f"salto={c.delta_from_prev_pct:.4f}%"
        )

if __name__ == "__main__":
    main()