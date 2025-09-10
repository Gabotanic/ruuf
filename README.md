# Tarea Dev Junior - Ruuf

## 🎯 Objetivo

El objetivo de este ejercicio es poder entender tus habilidades como programador/a, la forma en que planteas un problema, cómo los resuelves y finalmente cómo comunicas tu forma de razonar y resultados.

## 🛠️ Problema

El problema a resolver consiste en encontrar la máxima cantidad de rectángulos de dimensiones "a" y "b" (paneles solares) que caben dentro de un rectángulo de dimensiones "x" e "y" (techo).

## 🚀 Cómo Empezar

### Opción 1: Solución en TypeScript
```bash
cd typescript
npm install
npm start
```

### Opción 2: Solución en Python
```bash
cd python
python3 main.py
```

> **Tips útiles (CLI):**
> - Correr tests del JSON: `python3 main.py --test`
> - Caso rectangular único: `python3 main.py <a> <b> <x> <y>`  
>   Ejemplo: `python3 main.py 1 2 3 5`
> - **Bonus triangular** (base=x, altura=y): `python3 main.py <a> <b> <x> <y> --triangle`  
>   Ejemplo: `python3 main.py 1 2 7 6 --triangle`
> - **Bonus rectángulos superpuestos**: `python3 main.py <a> <b> <x> <y> --overlap <dx> <dy>`  
>   (Se modela la unión de dos rectángulos iguales x*y; el segundo está desplazado dx, dy respecto del primero)  
>   Ejemplo: `python3 main.py 1 2 6 4 --overlap 3 0`

## ✅ Casos de Prueba

Tu solución debe pasar los siguientes casos de prueba:
- Paneles 1x2 y techo 2x4 ⇒ Caben 4
- Paneles 1x2 y techo 3x5 ⇒ Caben 7
- Paneles 2x2 y techo 1x10 ⇒ Caben 0

---

## 📝 Tu Solución

**Resumen del enfoque (una sola función `calculate_panels(a, b, x, y)`):**

1) **Reducción exacta por MCD + búsqueda con memo**  
   - Escalo todas las dimensiones por g = gcd(a, b, x, y) para trabajar en una rejilla entera de tamaño W = x/g por H = y/g celdas (cada celda representa un bloque de g por g).  
   - Si W*H es menor o igual a 64, resuelvo de forma **exacta** con backtracking y **memoización** (`@lru_cache`) sobre un **bitmask**:
     - `dfs(mask)` devuelve el máximo de paneles que puedo seguir colocando desde el estado `mask` (bit=1 celda ocupada, bit=0 celda libre).
     - Tomo la **primera celda libre** y pruebo tres alternativas:  
       (a) colocar un panel de a1*b1, (b) colocar uno girado de b1*a1, (c) **dejar la celda vacía** si conviene.  
       Tomo el **máximo** de las tres.  
     - `lru_cache` evita recomputar estados repetidos (mismo `mask`) y acelera de forma sustancial.
     - `puede(w, h)`: verifica si el bloque w*h cabe en la posición y no pisa celdas ocupadas.  
       `coloca(w, h)`: devuelve la nueva máscara con esas celdas marcadas como ocupadas.
   - Resultado: óptimo **garantizado** en techos “pequeños” (tras la reducción por MCD).

2) **Fallback rápido por franjas (tipo “knapsack” de 2 tipos)**  
   - Si W*H es mayor a 64, uso un método lineal que **mezcla franjas** de ambas orientaciones:
     - **Por columnas (ancho)**:  
       Si uso columnas de ancho a (panel a*b), caben A = y//b paneles por columna.  
       Si uso columnas de ancho b (panel girado b*a), caben B = y//a.  
       Recorro i = 0..(x//a) columnas-`a` y completo el resto con columnas-`b`:  
       `valor(i) = i*A + ((x - i*a)//b)*B`  
       Tomo el máximo.
     - **Por filas (alto)**: misma idea, mezclando filas de alto b y de alto a.  
     - Tomo el **máximo global** considerando también el intercambio a↔b (ambas orientaciones del panel).
   - Este método capta bien la **mezcla de orientaciones 0°/90°** y escala en tiempo proporcional a (x//a + x//b + y//a + y//b).

**Características clave**
- **Mezcla de orientaciones** (0°/90°) permitida dentro del mismo techo.  
- **Sin cortes ni solapes**; **se permiten huecos** si eso habilita colocar más paneles en otras zonas.  
- Todo se trabaja en **enteros** (si hubiera decimales, se puede escalar la unidad para volver a enteros).

**Complejidad**
- Exacto (con memo): exponencial en W*H, pero acotado a ≤ 64 celdas → muy rápido en la práctica.  
- Franjas (fallback): lineal en los cocientes enteros (x//a, x//b, y//a, y//b).

---

## 💰 Bonus (Opcional)

### Bonus Implementado
- **Opción 1 – Techo triangular isósceles (`--triangle`)**  
  - **Supuesto**: triángulo con base horizontal de largo x y altura y (ápice arriba, centrado).  
  - **Reducción por MCD**: g = gcd(a, b, x, y). Trabajo con a1, b1, X, H en celdas.  
  - **Ancho por altura**: el ancho útil decrece linealmente con la altura. En altura t (0..H), uso `width_at(t) = (X*(H - t)) // H`.  
  - **DP por franjas horizontales**: `dp[t]` = máximo desde altura t. Transiciones:  
    - Usar franja de alto b1 (panel a*b): `count = width_at(t + b1) // a1; dp[t] = max(dp[t], count + dp[t + b1])`  
    - Usar franja de alto a1 (panel b*a): `count = width_at(t + a1) // b1; dp[t] = max(dp[t], count + dp[t + a1])`  
    - O **saltar** a `t+1`.  
  - **Complejidad**: O(H).

- **Opción 2 – Dos rectángulos iguales superpuestos (`--overlap dx dy`)**  
  - **Modelo**: unión de dos rectángulos iguales de tamaño x*y; el segundo está corrido un desplazamiento (dx, dy) respecto del primero.  
    Rect A: [0,x]×[0,y]; Rect B: [dx,dx+x]×[dy,dy+y].  
  - **Reducción por MCD**: g = gcd(a, b, x, y, |dx|, |dy|). Tras dividir, todos los bordes coinciden con la rejilla.  
  - **Exacto (casos chicos)**: si el área de la unión en celdas ≤ límite (por ejemplo, 80), hago backtracking con bitmask sobre la **unión** (celdas fuera de la unión se marcan ocupadas en el estado inicial).  
  - **Fallback por franjas**:  
    1) **Segmentación en Y**: parto el plano en segmentos horizontales entre alturas clave (0, y, dy, dy+y recortadas al bounding box). En cada segmento la sección horizontal es constante (uno o dos intervalos).  
       - Capacidad por fila:  
         `capAB = sum(L // a1)` para intervalos con panel a*b, y `capBA = sum(L // b1)` para panel b*a.  
       - **Knapsack 1D** por segmento (dos ítems ilimitados): peso = alto de la fila (b1 o a1), valor = capacidad (capAB o capBA). O(Hseg).  
    2) **Simetría en X (opcional)**: repito el mismo procedimiento “de pie” (segmentación vertical) e intercambio a1↔b1; me quedo con el máximo entre horizontal y vertical.  
  - **Complejidad**: lineal en la altura (o el ancho) segmentada; muy rápida en práctica.

### Explicación del Bonus
- Ambos bonus conservan la idea central: **discretizar con MCD**, **optimizar por franjas** cuando la geometría lo permite y, si el estado es pequeño, caer en un **exacto con memo** para garantizar optimalidad.  
- El caso de superposición se resuelve por **segmentos donde el corte es constante**, lo que permite tratar cada segmento de forma independiente con una **DP 1D** simple y sumar resultados.

---

## 🤔 Supuestos y Decisiones

- **Unidades y dominios**: a, b, x, y son **enteros positivos** en la **misma unidad**. La salida es **cantidad de paneles** (entero).  
- **Orientación**: se permiten **rotaciones 0°/90°** y **mezcla** de orientaciones dentro del mismo techo.  
- **Geometría**: paneles **no se cortan** ni **se superponen**; se **pueden dejar huecos** si mejora el total.  
- **Reducción por MCD**: uso g = gcd(a, b, x, y) (y en el bonus de superposición, también |dx| y |dy|) para **discretizar y reducir** el tamaño del estado sin cambiar la respuesta.  
- **Criterio de conmutación**: si la rejilla reducida (o el área de la unión) es pequeña, uso el método **exacto** con bitmask; si no, uso **franjas + knapsack 1D** (trade-off entre optimalidad garantizada y tiempo).  
- **Orden de exploración**: en el exacto, siempre coloco desde la **primera celda libre** (consistente y con buen pruning) y uso `@lru_cache` para **evitar recomputación**.  
- **CLI**:  
  - Rectangular: `python3 main.py a b x y`  
  - Triangular: `python3 main.py a b base height --triangle`  
  - Superpuestos: `python3 main.py a b x y --overlap dx dy`
