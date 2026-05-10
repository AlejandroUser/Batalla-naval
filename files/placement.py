"""
Pantalla de colocación de barcos con drag & drop.
- Arrastra cada barco a su posición en el grid
- R para rotar mientras arrastras
- 60 segundos para colocar todos los barcos
- Solapamiento rechazado con feedback visual
"""

import pygame
import math
from ships import Ship, TIPOS_BARCOS, flota_hundida
from physics import (GRID_DER_X, GRID_DER_Y, CELDA_G, GRID_W, GRID_H)

# ── Colores ────────────────────────────────────────────────────────
CELESTE   = (80, 170, 230)
BLANCO    = (235, 245, 255)
GRIS      = (140, 150, 165)
GRIS_OSC  = (50,  60,  75)
VERDE     = (50, 200, 100)
ROJO      = (210,  60,  60)
AMARILLO  = (255, 210,  50)
NARANJA   = (255, 140,  30)
NEGRO     = (5,   10,   20)
AZUL_GRID = (15,  55, 120)

ANCHO, ALTO = 1400, 900
TIEMPO_COLOCACION = 60   # segundos

# Grid de colocación = grid propio (derecho)
GX = GRID_DER_X
GY = GRID_DER_Y
C  = CELDA_G

# Zona de espera: barcos no colocados aparecen aquí (izquierda)
DOCK_X = 60
DOCK_Y = 80


class PantallaColocacion:
    """
    Gestiona la pantalla de colocación.
    Retorna la flota colocada o None si se agotó el tiempo / salió.
    """

    def __init__(self, screen, clock, jugador_id=1):
        self.screen     = screen
        self.clock      = clock
        self.jugador_id = jugador_id

        # Fuentes
        self.f_big   = pygame.font.SysFont("monospace", 22, bold=True)
        self.f_med   = pygame.font.SysFont("monospace", 16, bold=True)
        self.f_small = pygame.font.SysFont("monospace", 13)
        self.f_huge  = pygame.font.SysFont("monospace", 48, bold=True)

        self._inicializar()

    # ── Setup ──────────────────────────────────────────────────────

    def _inicializar(self):
        self.tiempo_restante = float(TIEMPO_COLOCACION)

        # Crear barcos en la zona de espera (dock)
        # Cada barco comienza SIN posición en el grid (col=None)
        self.barcos = []
        for i, (nombre, largo, color) in enumerate(TIPOS_BARCOS):
            b = Ship(nombre, largo, color, 0, i, horizontal=True)
            b.colocado = False          # atributo extra
            self.barcos.append(b)

        # Estado drag & drop
        self.arrastrando      = None    # barco que se está moviendo
        self.arrastre_offset  = (0, 0)  # offset del clic dentro del barco
        self.arrastre_col     = 0       # col fantasma actual
        self.arrastre_row     = 0       # row fantasma actual
        self.arrastre_horiz   = True    # orientación mientras se arrastra
        self.arrastre_valido  = True    # si la posición es válida

        # Feedback error
        self.error_timer  = 0.0
        self.error_msg    = ""

        # Posiciones en el dock (píxeles del centro de cada barco)
        self._recalcular_dock()

    def _recalcular_dock(self):
        """Calcula la posición en píxeles de cada barco no colocado en el dock."""
        self.dock_posiciones = {}
        y = DOCK_Y + 30
        for b in self.barcos:
            if not b.colocado:
                self.dock_posiciones[id(b)] = (DOCK_X, y)
                y += C + 18

    # ── Helpers ────────────────────────────────────────────────────

    def _celdas_ocupadas(self, excluir=None):
        """Retorna el set de (col,row) ocupadas por barcos ya colocados."""
        ocupadas = set()
        for b in self.barcos:
            if b.colocado and b is not excluir:
                for celda in b.celdas():
                    ocupadas.add(celda)
        return ocupadas

    def _fantasma_celdas(self):
        """Celdas que ocuparía el barco arrastrado en la posición actual."""
        b = self.arrastrando
        if b is None:
            return []
        celdas = []
        for i in range(b.largo):
            if self.arrastre_horiz:
                celdas.append((self.arrastre_col + i, self.arrastre_row))
            else:
                celdas.append((self.arrastre_col, self.arrastre_row + i))
        return celdas

    def _fantasma_valido(self):
        """True si el fantasma cabe en el grid y no se solapa."""
        celdas = self._fantasma_celdas()
        if not celdas:
            return False
        ocupadas = self._celdas_ocupadas(excluir=self.arrastrando)
        for col, row in celdas:
            if not (0 <= col < 10 and 0 <= row < 10):
                return False
            if (col, row) in ocupadas:
                return False
        return True

    def _px_a_celda(self, mx, my):
        """Convierte píxeles a (col, row) del grid de colocación."""
        col = int((mx - GX) // C)
        row = int((my - GY) // C)
        return col, row

    def _barco_en_dock_px(self, b):
        """Retorna el rect del barco en el dock."""
        if id(b) not in self.dock_posiciones:
            return None
        x, y = self.dock_posiciones[id(b)]
        w = b.largo * C if b.horizontal else C
        h = C if b.horizontal else b.largo * C
        return pygame.Rect(x, y, w, h)

    def _barco_en_grid_px(self, b):
        """Retorna el rect del barco ya colocado en el grid."""
        if not b.colocado:
            return None
        col0, row0 = b.col, b.row
        x = GX + col0 * C
        y = GY + row0 * C
        w = b.largo * C if b.horizontal else C
        h = C if b.horizontal else b.largo * C
        return pygame.Rect(x, y, w, h)

    def _todos_colocados(self):
        return all(b.colocado for b in self.barcos)

    # ── Eventos ────────────────────────────────────────────────────

    def _on_mousedown(self, mx, my):
        # ¿Hizo clic en un barco ya colocado en el grid?
        for b in self.barcos:
            if not b.colocado:
                continue
            rect = self._barco_en_grid_px(b)
            if rect and rect.collidepoint(mx, my):
                # Levantar el barco del grid
                b.colocado = False
                self.arrastrando     = b
                self.arrastre_horiz  = b.horizontal
                self.arrastre_col    = b.col
                self.arrastre_row    = b.row
                self.arrastre_offset = (mx - rect.x, my - rect.y)
                self._recalcular_dock()
                return

        # ¿Hizo clic en un barco del dock?
        for b in self.barcos:
            if b.colocado:
                continue
            rect = self._barco_en_dock_px(b)
            if rect and rect.collidepoint(mx, my):
                self.arrastrando     = b
                self.arrastre_horiz  = b.horizontal
                self.arrastre_offset = (mx - rect.x, my - rect.y)
                col, row = self._px_a_celda(mx, my)
                self.arrastre_col = max(0, col)
                self.arrastre_row = max(0, row)
                self._recalcular_dock()
                return

    def _on_mousemove(self, mx, my):
        if self.arrastrando is None:
            return
        # Calcular celda fantasma bajo el cursor
        off_x, off_y = self.arrastre_offset
        bx = mx - off_x
        by = my - off_y
        col = int((bx - GX) // C)
        row = int((by - GY) // C)
        self.arrastre_col   = col
        self.arrastre_row   = row
        self.arrastre_valido = self._fantasma_valido()

    def _on_mouseup(self, mx, my):
        if self.arrastrando is None:
            return
        b = self.arrastrando

        # ¿Está sobre el grid?
        if (0 <= self.arrastre_col < 10 and 0 <= self.arrastre_row < 10
                and self.arrastre_valido):
            # Verificar que todas las celdas caben dentro del grid
            celdas = self._fantasma_celdas()
            todas_dentro = all(0 <= c < 10 and 0 <= r < 10 for c, r in celdas)
            if todas_dentro:
                b.col        = self.arrastre_col
                b.row        = self.arrastre_row
                b.horizontal = self.arrastre_horiz
                b.colocado   = True
            else:
                self.error_msg   = f"¡{b.nombre} no cabe en esa posición!"
                self.error_timer = 2.0
        else:
            # Soltar fuera del grid → vuelve al dock
            if not self.arrastre_valido and (0 <= self.arrastre_col < 10
                                              and 0 <= self.arrastre_row < 10):
                self.error_msg   = "¡Posición ocupada o fuera del grid!"
                self.error_timer = 2.0

        self.arrastrando = None
        self._recalcular_dock()

    def _on_keydown(self, key):
        if key == pygame.K_r and self.arrastrando is not None:
            self.arrastre_horiz  = not self.arrastre_horiz
            self.arrastre_valido = self._fantasma_valido()
        if key == pygame.K_SPACE and self._todos_colocados():
            return "listo"
        return None

    # ── Dibujo ─────────────────────────────────────────────────────

    def _draw_fondo(self):
        for y in range(ALTO):
            t = y / ALTO
            r = int(8  + t * 5)
            g = int(20 + t * 40)
            b = int(55 + t * 80)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (ANCHO, y))

    def _draw_grid(self):
        # Fondo semitransparente
        fondo = pygame.Surface((GRID_W, GRID_H), pygame.SRCALPHA)
        fondo.fill((10, 40, 100, 180))
        self.screen.blit(fondo, (GX, GY))

        for col in range(10):
            for row in range(10):
                x = GX + col * C
                y = GY + row * C
                rect = pygame.Rect(x+1, y+1, C-2, C-2)
                pygame.draw.rect(self.screen, AZUL_GRID, rect, border_radius=3)
                pygame.draw.rect(self.screen, (30,90,170), rect, 1, border_radius=3)

        # Etiquetas
        for col in range(10):
            t = self.f_small.render(chr(65+col), True, CELESTE)
            self.screen.blit(t, (GX + col*C + C//2 - t.get_width()//2, GY-20))
        for row in range(10):
            t = self.f_small.render(str(row+1), True, CELESTE)
            self.screen.blit(t, (GX-22, GY + row*C + C//2 - t.get_height()//2))

        pygame.draw.rect(self.screen, CELESTE, (GX, GY, GRID_W, GRID_H), 2, border_radius=4)

    def _draw_barco_en_grid(self, b):
        for i, (col, row) in enumerate(b.celdas()):
            x = GX + col * C
            y = GY + row * C
            rect = pygame.Rect(x+1, y+1, C-2, C-2)
            pygame.draw.rect(self.screen, b.color, rect, border_radius=4)
            pygame.draw.rect(self.screen, (180,190,200), rect, 1, border_radius=4)
            if i == 0:
                t = self.f_small.render(b.nombre[0], True, BLANCO)
                self.screen.blit(t, (x + C//2 - t.get_width()//2,
                                     y + C//2 - t.get_height()//2))

    def _draw_fantasma(self):
        if self.arrastrando is None:
            return
        celdas = self._fantasma_celdas()
        color = (50, 200, 80, 140) if self.arrastre_valido else (210, 50, 50, 140)
        borde = VERDE if self.arrastre_valido else ROJO
        for col, row in celdas:
            if 0 <= col < 10 and 0 <= row < 10:
                x = GX + col * C
                y = GY + row * C
                s = pygame.Surface((C-2, C-2), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, (x+1, y+1))
                pygame.draw.rect(self.screen, borde,
                                 (x+1, y+1, C-2, C-2), 2, border_radius=3)

    def _draw_dock(self):
        # Panel del dock
        dock_w = 300
        dock_h = ALTO - DOCK_Y - 20
        dock_s = pygame.Surface((dock_w, dock_h), pygame.SRCALPHA)
        dock_s.fill((10, 30, 80, 180))
        self.screen.blit(dock_s, (DOCK_X - 15, DOCK_Y - 10))
        pygame.draw.rect(self.screen, CELESTE,
                         (DOCK_X-15, DOCK_Y-10, dock_w, dock_h), 2, border_radius=6)

        t = self.f_med.render("FLOTA — arrastra al grid", True, AMARILLO)
        self.screen.blit(t, (DOCK_X, DOCK_Y - 5))

        for b in self.barcos:
            if b.colocado or b is self.arrastrando:
                continue
            pos = self.dock_posiciones.get(id(b))
            if not pos:
                continue
            x, y = pos
            for i in range(b.largo):
                rx = x + i * C if b.horizontal else x
                ry = y if b.horizontal else y + i * C
                rect = pygame.Rect(rx+1, ry+1, C-2, C-2)
                pygame.draw.rect(self.screen, b.color, rect, border_radius=4)
                pygame.draw.rect(self.screen, (180,190,200), rect, 1, border_radius=4)
                if i == 0:
                    lt = self.f_small.render(b.nombre[0], True, BLANCO)
                    self.screen.blit(lt, (rx + C//2 - lt.get_width()//2,
                                          ry + C//2 - lt.get_height()//2))
            # Nombre del barco
            nt = self.f_small.render(f"{b.nombre} ({b.largo})", True, GRIS)
            ex = x + (b.largo * C if b.horizontal else C) + 8
            self.screen.blit(nt, (ex, y + C//2 - nt.get_height()//2))

    def _draw_arrastrado(self, mx, my):
        """Dibuja el barco siguiendo al cursor mientras se arrastra."""
        b = self.arrastrando
        if b is None:
            return
        off_x, off_y = self.arrastre_offset
        bx = mx - off_x
        by = my - off_y
        color_arr = (*b.color[:3], 200)
        for i in range(b.largo):
            rx = bx + i * C if self.arrastre_horiz else bx
            ry = by if self.arrastre_horiz else by + i * C
            s = pygame.Surface((C-2, C-2), pygame.SRCALPHA)
            s.fill(color_arr)
            self.screen.blit(s, (rx+1, ry+1))
            pygame.draw.rect(self.screen, AMARILLO,
                             (rx+1, ry+1, C-2, C-2), 2, border_radius=4)
            if i == 0:
                lt = self.f_small.render(b.nombre[0], True, BLANCO)
                self.screen.blit(lt, (rx + C//2 - lt.get_width()//2,
                                      ry + C//2 - lt.get_height()//2))

    def _draw_hud(self):
        # Título
        t = self.f_big.render(f"JUGADOR {self.jugador_id}  —  Coloca tu flota", True, CELESTE)
        self.screen.blit(t, (ANCHO//2 - t.get_width()//2, 18))

        # Cuenta regresiva
        secs = int(math.ceil(self.tiempo_restante))
        color_cr = VERDE if secs > 20 else (NARANJA if secs > 10 else ROJO)
        cr = self.f_huge.render(f"{secs:02d}", True, color_cr)
        self.screen.blit(cr, (ANCHO - 130, 60))
        lbl = self.f_small.render("segundos", True, GRIS)
        self.screen.blit(lbl, (ANCHO - 128, 120))

        # Instrucciones
        instrucciones = [
            "Arrastra los barcos al grid",
            "R = rotar mientras arrastras",
            "Clic en barco colocado para moverlo",
            "ESPACIO = confirmar (todos colocados)",
        ]
        panel = pygame.Surface((360, 115), pygame.SRCALPHA)
        panel.fill((10, 30, 80, 180))
        self.screen.blit(panel, (ANCHO - 390, 170))
        pygame.draw.rect(self.screen, CELESTE, (ANCHO-390, 170, 360, 115), 1, border_radius=6)
        for i, txt in enumerate(instrucciones):
            t = self.f_small.render(txt, True, BLANCO)
            self.screen.blit(t, (ANCHO - 382, 178 + i * 26))

        # Estado barcos
        panel2 = pygame.Surface((360, 175), pygame.SRCALPHA)
        panel2.fill((10, 30, 80, 180))
        self.screen.blit(panel2, (ANCHO - 390, 305))
        pygame.draw.rect(self.screen, CELESTE, (ANCHO-390, 305, 360, 175), 1, border_radius=6)
        lbl2 = self.f_med.render("Estado de la flota:", True, AMARILLO)
        self.screen.blit(lbl2, (ANCHO-382, 312))
        for i, b in enumerate(self.barcos):
            estado_color = VERDE if b.colocado else GRIS
            estado_txt   = f"✓ {b.nombre} ({b.largo})" if b.colocado else f"○ {b.nombre} ({b.largo})"
            t = self.f_small.render(estado_txt, True, estado_color)
            self.screen.blit(t, (ANCHO-382, 334 + i * 26))

        # Botón confirmar
        if self._todos_colocados():
            btn = pygame.Rect(ANCHO-390, 500, 360, 50)
            pygame.draw.rect(self.screen, (30, 120, 40), btn, border_radius=8)
            pygame.draw.rect(self.screen, VERDE, btn, 2, border_radius=8)
            bt = self.f_med.render("CONFIRMAR — ESPACIO", True, BLANCO)
            self.screen.blit(bt, (btn.x + btn.w//2 - bt.get_width()//2,
                                  btn.y + btn.h//2 - bt.get_height()//2))
        else:
            faltan = sum(1 for b in self.barcos if not b.colocado)
            ft = self.f_small.render(f"Faltan {faltan} barco(s) por colocar", True, NARANJA)
            self.screen.blit(ft, (ANCHO-382, 508))

        # Mensaje de error
        if self.error_timer > 0:
            alpha = min(255, int(255 * self.error_timer))
            err_s = pygame.Surface((600, 40), pygame.SRCALPHA)
            err_s.fill((180, 30, 30, min(180, alpha)))
            self.screen.blit(err_s, (ANCHO//2 - 300, ALTO - 70))
            et = self.f_med.render(self.error_msg, True, BLANCO)
            self.screen.blit(et, (ANCHO//2 - et.get_width()//2, ALTO - 62))

    def _draw_tiempo_agotado(self):
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        t1 = self.f_huge.render("¡TIEMPO AGOTADO!", True, ROJO)
        t2 = self.f_med.render("Los barcos restantes se colocan automáticamente", True, BLANCO)
        t3 = self.f_med.render("ESPACIO = continuar", True, AMARILLO)
        self.screen.blit(t1, (ANCHO//2 - t1.get_width()//2, ALTO//2 - 80))
        self.screen.blit(t2, (ANCHO//2 - t2.get_width()//2, ALTO//2 + 10))
        self.screen.blit(t3, (ANCHO//2 - t3.get_width()//2, ALTO//2 + 50))

    # ── Colocación automática de barcos restantes ──────────────────

    def _colocar_automatico(self):
        """Coloca los barcos no colocados en posiciones libres."""
        import random
        ocupadas = self._celdas_ocupadas()
        for b in self.barcos:
            if b.colocado:
                continue
            colocado = False
            intentos = 0
            while not colocado and intentos < 500:
                horiz = random.choice([True, False])
                col   = random.randint(0, 9)
                row   = random.randint(0, 9)
                if horiz:
                    celdas = [(col+i, row) for i in range(b.largo)]
                else:
                    celdas = [(col, row+i) for i in range(b.largo)]
                valido = all(0 <= c < 10 and 0 <= r < 10 and (c,r) not in ocupadas
                             for c, r in celdas)
                if valido:
                    b.col        = col
                    b.row        = row
                    b.horizontal = horiz
                    b.colocado   = True
                    for celda in celdas:
                        ocupadas.add(celda)
                    colocado = True
                intentos += 1

    # ── Loop principal ─────────────────────────────────────────────

    def run(self):
        tiempo_agotado   = False
        esperando_enter  = False   # True después de que se agota el tiempo

        while True:
            dt = self.clock.tick(60) / 1000.0
            mx, my = pygame.mouse.get_pos()

            # Actualizar cuenta regresiva
            if not tiempo_agotado:
                self.tiempo_restante -= dt
                if self.tiempo_restante <= 0:
                    self.tiempo_restante = 0
                    tiempo_agotado = True
                    self._colocar_automatico()
                    esperando_enter = True

            if self.error_timer > 0:
                self.error_timer -= dt

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return None
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return None
                    if esperando_enter and ev.key == pygame.K_SPACE:
                        return self.barcos
                    if not tiempo_agotado:
                        resultado = self._on_keydown(ev.key)
                        if resultado == "listo":
                            return self.barcos
                if not tiempo_agotado:
                    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                        self._on_mousedown(mx, my)
                    if ev.type == pygame.MOUSEMOTION:
                        self._on_mousemove(mx, my)
                    if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                        self._on_mouseup(mx, my)

            # Actualizar posición del fantasma con el mouse actual
            if self.arrastrando is not None:
                self._on_mousemove(mx, my)

            # ── Dibujo ─────────────────────────────────────────────
            self._draw_fondo()
            self._draw_grid()

            # Barcos colocados
            for b in self.barcos:
                if b.colocado and b is not self.arrastrando:
                    self._draw_barco_en_grid(b)

            self._draw_fantasma()
            self._draw_dock()
            self._draw_arrastrado(mx, my)
            self._draw_hud()

            if tiempo_agotado:
                self._draw_tiempo_agotado()

            pygame.display.flip()
