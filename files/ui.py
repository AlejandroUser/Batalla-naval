import pygame

# Colores
AZUL_OSCURO  = (8,  20,  55)
CELESTE      = (80, 170, 230)
BLANCO       = (235, 245, 255)
GRIS         = (140, 150, 165)
GRIS_OSCURO  = (50,  60,  75)
VERDE        = (50, 200, 100)
ROJO         = (210, 60,  60)
AMARILLO     = (255, 210, 50)
NARANJA      = (255, 140, 30)
NEGRO        = (5,   10,  20)


def dibujar_fondo_mar(surface, ancho, alto):
    for y in range(alto):
        t = y / alto
        r = int(8  + t * 5)
        g = int(20 + t * 40)
        b = int(55 + t * 80)
        pygame.draw.line(surface, (r, g, b), (0, y), (ancho, y))
    font = pygame.font.SysFont("arial", 22)
    for x in range(0, ancho, 90):
        for y in range(0, alto, 130):
            ola = font.render("~", True, (30, 90, 160))
            surface.blit(ola, (x + (y // 30) % 50, y))


def dibujar_grid(surface, offset_x, offset_y, cols=10, rows=10,
                 celda_size=48, disparos_agua=None, disparos_impacto=None, titulo=""):
    disparos_agua    = disparos_agua    or set()
    disparos_impacto = disparos_impacto or set()
    C = celda_size

    fondo = pygame.Surface((cols * C, rows * C), pygame.SRCALPHA)
    fondo.fill((10, 40, 100, 180))
    surface.blit(fondo, (offset_x, offset_y))

    for c in range(cols):
        for r in range(rows):
            x = offset_x + c * C
            y = offset_y + r * C
            rect = pygame.Rect(x + 1, y + 1, C - 2, C - 2)
            if   (c, r) in disparos_impacto:
                pygame.draw.rect(surface, (160, 40, 40), rect, border_radius=4)
            elif (c, r) in disparos_agua:
                pygame.draw.rect(surface, (20, 80, 160), rect, border_radius=4)
            else:
                pygame.draw.rect(surface, (15, 55, 120), rect, border_radius=4)
            pygame.draw.rect(surface, (30, 90, 170), rect, 1, border_radius=4)

    font_label = pygame.font.SysFont("monospace", 14, bold=True)
    for c in range(cols):
        txt = font_label.render(chr(ord('A') + c), True, CELESTE)
        surface.blit(txt, (offset_x + c*C + C//2 - txt.get_width()//2, offset_y - 20))
    for r in range(rows):
        txt = font_label.render(str(r + 1), True, CELESTE)
        surface.blit(txt, (offset_x - 22, offset_y + r*C + C//2 - txt.get_height()//2))

    pygame.draw.rect(surface, CELESTE,
                     (offset_x, offset_y, cols*C, rows*C), 2, border_radius=4)

    if titulo:
        font_t = pygame.font.SysFont("monospace", 16, bold=True)
        txt_t  = font_t.render(titulo, True, BLANCO)
        surface.blit(txt_t, (offset_x + cols*C//2 - txt_t.get_width()//2, offset_y - 42))


def dibujar_marcadores(surface, offset_x, offset_y,
                       disparos_agua, disparos_impacto, celda_size=48):
    C = celda_size
    font = pygame.font.SysFont("monospace", 20, bold=True)
    for c, r in disparos_agua:
        x = offset_x + c*C + C//2
        y = offset_y + r*C + C//2
        txt = font.render("o", True, CELESTE)
        surface.blit(txt, (x - txt.get_width()//2, y - txt.get_height()//2))
    for c, r in disparos_impacto:
        x = offset_x + c*C + C//2
        y = offset_y + r*C + C//2
        pygame.draw.line(surface, AMARILLO, (x-10, y-10), (x+10, y+10), 3)
        pygame.draw.line(surface, AMARILLO, (x+10, y-10), (x-10, y+10), 3)
        pygame.draw.circle(surface, ROJO, (x, y), 6)


class PanelDisparo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo_str   = ""
        self.potencia_str = ""
        self.campo_activo = "angulo"
        self.mensaje      = ""
        self.mensaje_color = BLANCO
        self.font       = pygame.font.SysFont("monospace", 17, bold=True)
        self.font_big   = pygame.font.SysFont("monospace", 20, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 14)

    def manejar_evento(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.campo_activo = "potencia" if self.campo_activo == "angulo" else "angulo"
            elif event.key == pygame.K_BACKSPACE:
                if self.campo_activo == "angulo":
                    self.angulo_str = self.angulo_str[:-1]
                else:
                    self.potencia_str = self.potencia_str[:-1]
            elif event.unicode.isdigit() or event.unicode == '.':
                if self.campo_activo == "angulo" and len(self.angulo_str) < 5:
                    self.angulo_str += event.unicode
                elif self.campo_activo == "potencia" and len(self.potencia_str) < 5:
                    self.potencia_str += event.unicode

    def obtener_valores(self):
        try:
            a = float(self.angulo_str)
            p = float(self.potencia_str)
            if not (1 <= a <= 89):
                self.mensaje = "Angulo: 1–89 grados"
                self.mensaje_color = ROJO
                return None
            if not (10 <= p <= 120):
                self.mensaje = "Potencia: 10–120 m/s"
                self.mensaje_color = ROJO
                return None
            self.mensaje = ""
            return a, p
        except:
            self.mensaje = "Ingresa valores validos"
            self.mensaje_color = ROJO
            return None

    def draw(self, surface, turno_activo=True, barco_nombre=None):
        ancho, alto = 370, 175
        panel = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        panel.fill((10, 30, 80, 215))
        surface.blit(panel, (self.x, self.y))
        pygame.draw.rect(surface, CELESTE, (self.x, self.y, ancho, alto), 2, border_radius=8)

        # Título
        surface.blit(self.font_big.render("DISPARO", True, AMARILLO),
                     (self.x + 12, self.y + 10))

        # Barco seleccionado
        if barco_nombre:
            b_surf = self.font_small.render(f"Canon: {barco_nombre}", True, VERDE)
        else:
            b_surf = self.font_small.render("Clic en tu barco para seleccionar", True, ROJO)
        surface.blit(b_surf, (self.x + 130, self.y + 14))

        if not turno_activo:
            surface.blit(self.font.render("Esperando rival...", True, GRIS),
                         (self.x + 12, self.y + 60))
            return

        # Ángulo
        ca = AMARILLO if self.campo_activo == "angulo" else GRIS
        surface.blit(self.font_small.render("Angulo (1-89°):", True, ca),
                     (self.x + 12, self.y + 42))
        ra = pygame.Rect(self.x + 12, self.y + 62, 130, 32)
        pygame.draw.rect(surface, GRIS_OSCURO, ra, border_radius=5)
        pygame.draw.rect(surface, ca, ra, 2, border_radius=5)
        surface.blit(self.font.render(
            self.angulo_str + ("_" if self.campo_activo == "angulo" else ""), True, BLANCO),
            (ra.x + 6, ra.y + 5))

        # Potencia
        cp = AMARILLO if self.campo_activo == "potencia" else GRIS
        surface.blit(self.font_small.render("Potencia (10-120 m/s):", True, cp),
                     (self.x + 160, self.y + 42))
        rp = pygame.Rect(self.x + 160, self.y + 62, 130, 32)
        pygame.draw.rect(surface, GRIS_OSCURO, rp, border_radius=5)
        pygame.draw.rect(surface, cp, rp, 2, border_radius=5)
        surface.blit(self.font.render(
            self.potencia_str + ("_" if self.campo_activo == "potencia" else ""), True, BLANCO),
            (rp.x + 6, rp.y + 5))

        # Botón FUEGO
        btn = pygame.Rect(self.x + 305, self.y + 58, 55, 38)
        pygame.draw.rect(surface, (150, 50, 50), btn, border_radius=7)
        pygame.draw.rect(surface, ROJO, btn, 2, border_radius=7)
        surface.blit(self.font_small.render("FUEGO", True, BLANCO),
                     (btn.x + btn.w//2 - 22, btn.y + 10))

        # Hints
        surface.blit(self.font_small.render(
            "TAB = cambiar campo   |   ENTER = disparar", True, GRIS),
            (self.x + 12, self.y + 104))
        surface.blit(self.font_small.render(
            "Rango util: angulo 20-70°   potencia 30-85 m/s", True, (80, 140, 200)),
            (self.x + 12, self.y + 122))
        if self.mensaje:
            surface.blit(self.font_small.render(self.mensaje[:50], True, self.mensaje_color),
                         (self.x + 12, self.y + 148))


class PanelInfo:
    def __init__(self, x, y, ancho=330):
        self.x     = x
        self.y     = y
        self.ancho = ancho
        self.font       = pygame.font.SysFont("monospace", 16, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 13)

    def draw(self, surface, turno, jugador_id, flota_propia, flota_enemiga, log):
        alto = 195
        panel = pygame.Surface((self.ancho, alto), pygame.SRCALPHA)
        panel.fill((10, 30, 80, 215))
        surface.blit(panel, (self.x, self.y))
        pygame.draw.rect(surface, CELESTE, (self.x, self.y, self.ancho, alto), 2, border_radius=8)

        color_turno = VERDE if turno == jugador_id else ROJO
        txt_turno   = "TU TURNO" if turno == jugador_id else "TURNO RIVAL"
        surface.blit(self.font.render(f"▶  {txt_turno}", True, color_turno),
                     (self.x + 10, self.y + 10))

        vivos_p = sum(1 for s in flota_propia  if not s.hundido)
        vivos_e = sum(1 for s in flota_enemiga if not s.hundido)
        surface.blit(self.font.render(f"Tus barcos : {vivos_p}/{len(flota_propia)}", True, BLANCO),
                     (self.x + 10, self.y + 36))
        surface.blit(self.font.render(f"Rival      : {vivos_e}/{len(flota_enemiga)}", True, BLANCO),
                     (self.x + 10, self.y + 58))

        pygame.draw.line(surface, GRIS,
                         (self.x+10, self.y+82), (self.x+self.ancho-10, self.y+82))
        surface.blit(self.font_small.render("── BITÁCORA ──", True, GRIS),
                     (self.x + 10, self.y + 88))

        for i, entrada in enumerate(log[-7:]):
            color = AMARILLO if any(k in entrada.lower() for k in ["impacto","golpe","golpeo"]) else BLANCO
            color = ROJO     if "hundido" in entrada.lower() else color
            surface.blit(self.font_small.render(entrada[:42], True, color),
                         (self.x + 10, self.y + 104 + i * 14))


def dibujar_trayectoria(surface, puntos, color=(255, 200, 50)):
    for i, (x, y) in enumerate(puntos):
        r = max(2, 4 - i // 10)
        pygame.draw.circle(surface, color, (int(x), int(y)), r)


def pantalla_ganador(surface, ancho, alto, texto):
    overlay = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    surface.blit(overlay, (0, 0))
    font_big = pygame.font.SysFont("monospace", 64, bold=True)
    font_sub = pygame.font.SysFont("monospace", 26)
    txt = font_big.render(texto, True, AMARILLO)
    sub = font_sub.render("R = reiniciar   |   ESC = menú", True, BLANCO)
    surface.blit(txt, (ancho//2 - txt.get_width()//2, alto//2 - 70))
    surface.blit(sub, (ancho//2 - sub.get_width()//2, alto//2 + 30))
