from typing import List, Tuple, Dict
from functools import lru_cache
import json, math, argparse


def calculate_panels(panel_width: int, panel_height: int, 
                     roof_width: int, roof_height: int) -> int:
    a, b, x, y = panel_width, panel_height, roof_width, roof_height
    if min(a, b, x, y) <= 0:
        return 0

    # Intento exacto en techos chicos (después de escalar por MCD)
    def _exact(a: int, b: int, x: int, y: int, limit_cells: int = 64):
        g = math.gcd(math.gcd(a, b), math.gcd(x, y))
        a1, b1, x1, y1 = a // g, b // g, x // g, y // g
        W, H = x1, y1
        total = W * H
        if total > limit_cells:
            return None

        @lru_cache(maxsize=None)
        def dfs(mask: int) -> int:
            if mask == (1 << (W * H)) - 1:
                return 0
            # primera celda libre
            k = 0
            while (mask >> k) & 1:
                k += 1
            i, j = k % W, k // W

            def puede(w: int, h: int) -> bool:
                if i + w > W or j + h > H:
                    return False
                for dy in range(h):
                    row = (j + dy) * W
                    for dx in range(w):
                        if (mask >> (row + i + dx)) & 1:
                            return False
                return True

            def coloca(w: int, h: int) -> int:
                m = mask
                for dy in range(h):
                    row = (j + dy) * W
                    for dx in range(w):
                        m |= 1 << (row + i + dx)
                return m

            best = 0
            if puede(a1, b1):
                best = max(best, 1 + dfs(coloca(a1, b1)))
            if (a1, b1) != (b1, a1) and puede(b1, a1):
                best = max(best, 1 + dfs(coloca(b1, a1)))
            # opción: dejar vacía esta celda
            best = max(best, dfs(mask | (1 << k)))
            return best

        return dfs(0)

    exact = _exact(a, b, x, y, limit_cells=64)
    if exact is not None:
        return exact

    # Fallback rápido: mezcla óptima por columnas (ancho) y por filas (alto)
    def by_width(a: int, b: int, x: int, y: int) -> int:
        best = 0
        ab = y // b   # paneles por columna si uso a×b
        ba = y // a   # paneles por columna si uso b×a (girado)
        for i in range(x // a + 1):
            rem = x - i * a
            val = i * ab + (rem // b) * ba
            best = max(best, val)
        return best

    def by_height(a: int, b: int, x: int, y: int) -> int:
        best = 0
        ab = x // a
        ba = x // b
        for j in range(y // b + 1):
            rem = y - j * b
            val = j * ab + (rem // a) * ba
            best = max(best, val)
        return best

    return max(
        by_width(a, b, x, y),
        by_width(b, a, x, y),
        by_height(a, b, x, y),
        by_height(b, a, x, y),
    )


def calculate_panels_triangle(panel_width: int, panel_height: int,
                              base_x: int, height_h: int) -> int:
    """
    Máximo de paneles a×b dentro de un triángulo isósceles con base = x y altura = h.
    Supuestos: rectángulos enteros, sin cortes ni solapes, giros 0°/90°, mezcla permitida.
    """
    a, b, x, h = panel_width, panel_height, base_x, height_h
    if min(a, b, x, h) <= 0:
        return 0

    # 1) Reducir por MCD para discretizar y achicar el estado
    g = math.gcd(math.gcd(a, b), math.gcd(x, h))
    a1, b1, X, H = a // g, b // g, x // g, h // g

    if H == 0 or X == 0:
        return 0

    # 2) Ancho disponible a altura t (conservador en el tope de la franja)
    #    t=0: base (ancho X) ... t=H: ápice (ancho 0)
    def width_at(t: int) -> int:
        # floor( X * (H - t) / H )
        if t < 0:
            t = 0
        if t > H:
            t = H
        return (X * (H - t)) // H

    # 3) DP 1D: dp[t] = máximo desde altura t hasta H
    dp = [0] * (H + 1)  # dp[H] = 0

    for t in range(H - 1, -1, -1):
        best = dp[t + 1]  # opción: saltar esta altura (dejar hueco)

        # Usar franja de alto b1 con panel a1×b1
        nt = t + b1
        if nt <= H:
            row_count = width_at(nt) // a1  # ancho "tope" de la franja
            cand = row_count + dp[nt]
            if cand > best:
                best = cand

        # Usar franja de alto a1 con panel girado b1×a1
        nt = t + a1
        if nt <= H:
            row_count = width_at(nt) // b1
            cand = row_count + dp[nt]
            if cand > best:
                best = cand

        dp[t] = best

    return dp[0]

def calculate_panels_overlap(panel_width: int, panel_height: int,
                             rect_w: int, rect_h: int,
                             dx: int, dy: int) -> int:
    """
    Dos rectángulos iguales de tamaño rect_w x rect_h, el segundo desplazado (dx, dy)
    respecto del primero. Devuelve el máximo de paneles a×b.
    - Sin cortes ni solapes entre paneles.
    - Rotaciones 0°/90° permitidas y mezcla dentro del mismo techo.
    - Exacto con bitmask si el área escalada es pequeña; si no, fallback por franjas.
    """
    a, b, x, y = panel_width, panel_height, rect_w, rect_h
    if min(a, b, x, y) <= 0:
        return 0

    # ---------- 1) Reducir por MCD ----------
    g = math.gcd(math.gcd(a, b), math.gcd(math.gcd(x, y), math.gcd(abs(dx), abs(dy))))
    if g <= 0:
        g = 1
    a1, b1 = a // g, b // g
    X, Y = x // g, y // g
    DX, DY = dx // g, dy // g

    # Normalizar a bounding box no negativa
    shiftX = -min(0, DX)
    shiftY = -min(0, DY)
    # Rect A
    Ax0, Ay0 = shiftX + 0,        shiftY + 0
    Ax1, Ay1 = Ax0 + X,           Ay0 + Y
    # Rect B
    Bx0, By0 = shiftX + DX,       shiftY + DY
    Bx1, By1 = Bx0 + X,           By0 + Y

    W = max(Ax1, Bx1)
    H = max(Ay1, By1)
    if W <= 0 or H <= 0:
        return 0

    # ---------- 2) Exacto con bitmask sobre la UNIÓN si el área es pequeña ----------
    # Construimos una máscara inicial con celdas inválidas = 1 (ocupadas), válidas = 0 (libres)
    # Para contar el área válida en celdas:
    valid_cells = 0
    init_mask = 0
    for yy in range(H):
        row = yy * W
        for xx in range(W):
            insideA = (Ax0 <= xx < Ax1) and (Ay0 <= yy < Ay1)
            insideB = (Bx0 <= xx < Bx1) and (By0 <= yy < By1)
            if insideA or insideB:
                valid_cells += 1
            else:
                k = row + xx
                init_mask |= (1 << k)  # celdas fuera de la unión: marcarlas ocupadas

    LIMIT_CELLS = 80  # puedes ajustar (64~100). Solo afecta el umbral del exacto
    if valid_cells <= LIMIT_CELLS:
        @lru_cache(maxsize=None)
        def dfs_union(mask: int) -> int:
            if mask == (1 << (W * H)) - 1:
                return 0
            # primera celda libre (válida y no ocupada)
            k = 0
            while (mask >> k) & 1:
                k += 1
            i, j = k % W, k // W

            def puede(w: int, h: int) -> bool:
                if i + w > W or j + h > H:
                    return False
                base = j * W
                for dy_ in range(h):
                    row = base + dy_ * W
                    for dx_ in range(w):
                        kk = row + (i + dx_)
                        if (mask >> kk) & 1:
                            return False
                return True

            def coloca(w: int, h: int) -> int:
                m = mask
                base = j * W
                for dy_ in range(h):
                    row = base + dy_ * W
                    for dx_ in range(w):
                        kk = row + (i + dx_)
                        m |= (1 << kk)
                return m

            best = 0
            if puede(a1, b1):
                best = max(best, 1 + dfs_union(coloca(a1, b1)))
            if (a1, b1) != (b1, a1) and puede(b1, a1):
                best = max(best, 1 + dfs_union(coloca(b1, a1)))
            # dejar vacía
            best = max(best, dfs_union(mask | (1 << k)))
            return best

        return dfs_union(init_mask)

    # ---------- 3) Fallback por franjas (segmentación en Y + knapsack por segmento) ----------
    def merge_intervals(iv):
        if not iv:
            return []
        iv.sort()
        out = [list(iv[0])]
        for s, e in iv[1:]:
            if s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out

    def segs_by_Y(rects, a_cell, b_cell):
        """
        rects: lista de rects [(x0,x1,y0,y1), (x0,x1,y0,y1)]
        a_cell, b_cell: dimensiones del panel en celdas (a1,b1) para filas de alto b_cell y filas rotadas de alto a_cell
        """
        # cortes Y donde cambia la sección horizontal
        cuts = {0, H}
        for (x0, x1, y0, y1) in rects:
            cuts.add(max(0, min(H, y0)))
            cuts.add(max(0, min(H, y1)))
        ys = sorted(cuts)

        total = 0
        for i in range(len(ys) - 1):
            yl, yh = ys[i], ys[i + 1]
            hseg = yh - yl
            if hseg <= 0:
                continue
            # ¿qué rects están activos en este segmento?
            intervals = []
            for (x0, x1, y0, y1) in rects:
                if y0 <= yl and yh <= y1:
                    intervals.append((max(0, x0), min(W, x1)))
            intervals = [(s, e) for (s, e) in intervals if e > s]
            if not intervals:
                continue
            merged = merge_intervals(intervals)  # 1 o 2 intervalos
            lengths = [e - s for (s, e) in merged]

            # capacidad por FILA
            capAB = sum(L // a_cell for L in lengths)  # filas de alto b_cell, ancho a_cell por panel
            capBA = sum(L // b_cell for L in lengths)  # filas de alto a_cell, ancho b_cell por panel

            # knapsack 1D ilimitado: peso = alto de la fila, valor = capacidad de esa fila
            # dp[t] = mejor valor ocupando exactamente t de altura; respuesta = max_{t<=hseg} dp[t]
            dp = [0] * (hseg + 1)
            for t in range(hseg + 1):
                # usar una fila de alto b_cell (panel a×b)
                nt = t + b_cell
                if nt <= hseg:
                    dp[nt] = max(dp[nt], dp[t] + capAB)
                # usar una fila de alto a_cell (panel b×a)
                nt = t + a_cell
                if nt <= hseg:
                    dp[nt] = max(dp[nt], dp[t] + capBA)
            total += max(dp)  # podemos dejar resto sin llenar
        return total

    rectsY = [(Ax0, Ax1, Ay0, Ay1), (Bx0, Bx1, By0, By1)]
    # Horizontal (segmentando por Y)
    by_y = segs_by_Y(rectsY, a1, b1)

    # Vertical (simetría: rotamos el problema 90° -> intercambiamos ejes)
    # Para reutilizar segs_by_Y, intercambiamos x<->y en rects y W/H y también a1<->b1
    # Construimos "rects" en el espacio transpuesto
    rectsX = [(Ay0, Ay1, Ax0, Ax1), (By0, By1, Bx0, Bx1)]
    # Ajuste: en el espacio transpuesto, la "altura total" es W (antes era H)
    H_backup, W_backup = H, W
    H, W = W_backup, H_backup  # swap para que segs_by_Y use los límites correctos
    by_x = segs_by_Y(rectsX, b1, a1)
    # restaurar por si acaso (no se usa después)
    H, W = H_backup, W_backup

    return max(by_y, by_x)


def run_tests() -> None:
    with open('test_cases.json', 'r') as f:
        data = json.load(f)
        test_cases: List[Dict[str, int]] = [
            {
                "panel_w": test["panelW"],
                "panel_h": test["panelH"],
                "roof_w": test["roofW"],
                "roof_h": test["roofH"],
                "expected": test["expected"]
            }
            for test in data["testCases"]
        ]
    
    print("Corriendo tests:")
    print("-------------------")
    
    for i, test in enumerate(test_cases, 1):
        result = calculate_panels(
            test["panel_w"], test["panel_h"], 
            test["roof_w"], test["roof_h"]
        )
        passed = result == test["expected"]
        
        print(f"Test {i}:")
        print(f"  Panels: {test['panel_w']}x{test['panel_h']}, "
              f"Roof: {test['roof_w']}x{test['roof_h']}")
        print(f"  Expected: {test['expected']}, Got: {result}")
        print(f"  Status: {'✅ PASSED' if passed else '❌ FAILED'}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula cuántos paneles caben o corre los tests."
    )
    parser.add_argument("panel_w", type=int, nargs="?", help="Ancho panel (a)")
    parser.add_argument("panel_h", type=int, nargs="?", help="Alto panel (b)")
    parser.add_argument("roof_w",  type=int, nargs="?", help="Ancho techo (x)")
    parser.add_argument("roof_h",  type=int, nargs="?", help="Alto techo (y)")
    parser.add_argument("--test", action="store_true",
                        help="Corre los tests de test_cases.json")
    parser.add_argument("--triangle", action="store_true",
                    help="Interpreta roof_w como base y roof_h como altura para un techo triangular isósceles")
    parser.add_argument("--overlap", nargs=2, type=int, metavar=("dx", "dy"),
                    help="Dos rectángulos iguales: el segundo desplazado (dx, dy). Usa roof_w, roof_h como tamaño de cada rectángulo.")


    args = parser.parse_args()

    print("🐕 Wuuf wuuf wuuf 🐕")
    print("================================\n")

    # Si se pasa --test o no diste los 4 números, corre los tests
    if args.test or None in (args.panel_w, args.panel_h, args.roof_w, args.roof_h):
        run_tests()
        return

    a, b, x, y = args.panel_w, args.panel_h, args.roof_w, args.roof_h

    if args.overlap:
        odx, ody = args.overlap
        result = calculate_panels_overlap(a, b, x, y, odx, ody)
        print("Caso único (dos rectángulos superpuestos):")
        print(f"  Panel: {a}x{b}, Rectángulos: {x}x{y}, Desplazamiento: dx={odx}, dy={ody}")
        print(f"  Máximo que caben: {result}")
    elif args.triangle:
        result = calculate_panels_triangle(a, b, x, y)  # x=base, y=altura
        print(f"Caso único (triángulo isósceles):")
        print(f"  Panel: {a}x{b}, Base: {x}, Altura: {y}")
        print(f"  Máximo que caben: {result}")
    else:
        result = calculate_panels(a, b, x, y)  # rectangular
        print(f"Caso único (rectangular):")
        print(f"  Panel: {a}x{b}, Techo: {x}x{y}")
        print(f"  Máximo que caben: {result}")


if __name__ == "__main__":
    main()

