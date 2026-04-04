import math

GRAVEDAD = 9.8
DT       = 0.02

# ── Layout del campo ───────────────────────────────────────────────
CELDA_G    = 48
GRID_W     = 10 * CELDA_G   # 480
GRID_H     = 10 * CELDA_G   # 480

GRID_IZQ_X = 60
GRID_IZQ_Y = 65
GRID_DER_X = 620             # 80px de mar entre grids
GRID_DER_Y = 65
# ───────────────────────────────────────────────────────────────────


def calcular_trayectoria(x0, y0, angulo_deg, potencia, _=None):
    """
    Parámetros
    ----------
    angulo_deg : negativo → izquierda (jugador→grid IZQ)
                 positivo → derecha   (CPU→grid DER)
    potencia   : m/s  (rango útil 30-90)

    Retorna (lista_puntos, (px_imp, py_imp))
    """
    angulo_rad = math.radians(abs(angulo_deg))
    direccion  = 1 if angulo_deg >= 0 else -1

    vx =  direccion * potencia * math.cos(angulo_rad)
    vy = -potencia  * math.sin(angulo_rad)

    if direccion < 0:
        gx1, gx2 = GRID_IZQ_X, GRID_IZQ_X + GRID_W
    else:
        gx1, gx2 = GRID_DER_X, GRID_DER_X + GRID_W
    gy1, gy2 = GRID_IZQ_Y, GRID_IZQ_Y + GRID_H

    puntos           = [(x0, y0)]
    t                = DT
    px_prev, py_prev = x0, y0
    subiendo         = True

    while t < 120.0:
        px = x0 + vx * t
        py = y0 + vy * t + 0.5 * GRAVEDAD * t * t

        if py > py_prev:
            subiendo = False

        if not subiendo:
            borde = gx2 if direccion < 0 else gx1
            cruzo = (px_prev >= borde > px) if direccion < 0 else (px_prev <= borde < px)
            if cruzo:
                frac  = (borde - px_prev) / (px - px_prev)
                y_c   = py_prev + frac * (py - py_prev)
                if gy1 <= y_c <= gy2:
                    px_imp = borde - (1 if direccion < 0 else -1)
                    puntos.append((px_imp, y_c))
                    return puntos, (px_imp, y_c)

            if gx1 <= px <= gx2 and py >= gy2:
                frac   = (gy2 - py_prev) / (py - py_prev) if py != py_prev else 1.0
                px_imp = max(gx1, min(px_prev + frac * (px - px_prev), gx2 - 1))
                puntos.append((px_imp, gy2 - 1))
                return puntos, (px_imp, gy2 - 1)

            if gx1 <= px <= gx2 and gy1 <= py <= gy2:
                puntos.append((px, py))
                return puntos, (px, py)

            if abs(px - x0) > 2000:
                break

        puntos.append((px, py))
        px_prev, py_prev = px, py
        t += DT

    return puntos, (px_prev, py_prev)


def pixel_a_celda(px, py, offset_x, offset_y, celda=None):
    if celda is None:
        celda = CELDA_G
    col = max(0, min(int((px - offset_x) // celda), 9))
    row = max(0, min(int((py - offset_y) // celda), 9))
    return col, row


def celda_valida_px(px, py, offset_x, offset_y, celda=None):
    if celda is None:
        celda = CELDA_G
    return (offset_x <= px <= offset_x + 10 * celda and
            offset_y <= py <= offset_y + 10 * celda)


def celda_valida(col, row, cols=10, rows=10):
    return 0 <= col < cols and 0 <= row < rows


def angulo_para_alcanzar(x0, y0, x_obj, y_obj, potencia):
    R  = abs(x_obj - x0)
    g  = GRAVEDAD
    v2 = potencia ** 2
    arg = g * R / v2
    if arg > 1.0:
        return None
    return round(math.degrees(0.5 * math.asin(arg)), 1)
