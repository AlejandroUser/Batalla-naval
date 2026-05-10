import pygame
import math

# Colores
AZUL_OSCURO = (10, 25, 60)
AZUL_MAR = (20, 80, 150)
GRIS_BARCO = (120, 130, 140)
GRIS_CLARO = (180, 190, 200)
ROJO_DANIO = (200, 50, 50)
AMARILLO = (255, 210, 50)
BLANCO = (240, 245, 255)
NEGRO = (10, 10, 20)
NARANJA = (255, 140, 0)

# Definición de tipos de barcos: (nombre, celdas_de_largo, color)
TIPOS_BARCOS = [
    ("Portaaviones", 5, (80, 90, 100)),
    ("Acorazado",    4, (100, 110, 120)),
    ("Crucero",      3, (110, 120, 130)),
    ("Destructor",   3, (90, 100, 110)),
    ("Submarino",    2, (60, 80, 90)),
]

CELDA = 40  # tamaño de cada celda en píxeles


class Ship:
    def __init__(self, nombre, largo, color, col, row, horizontal=True):
        self.nombre = nombre
        self.largo = largo
        self.color = color
        self.col = col       # columna inicial en el grid
        self.row = row       # fila inicial en el grid
        self.horizontal = horizontal
        self.hits = set()    # celdas golpeadas (offset 0..largo-1)
        self.hundido = False

    def celdas(self):
        """Retorna lista de (col, row) que ocupa el barco."""
        celdas = []
        for i in range(self.largo):
            if self.horizontal:
                celdas.append((self.col + i, self.row))
            else:
                celdas.append((self.col, self.row + i))
        return celdas

    def canon_origen_px(self, offset_x, offset_y):
        """
        Devuelve las coordenadas en píxeles del cañón del barco
        (celda central, borde superior de la celda).
        """
        celdas = self.celdas()
        mid = len(celdas) // 2
        c, r = celdas[mid]
        cx = offset_x + c * CELDA + CELDA // 2
        cy = offset_y + r * CELDA + 4  # borde superior de la celda
        return (cx, cy)

    def draw_seleccionado(self, surface, offset_x, offset_y):
        """Resalta el barco seleccionado para disparar."""
        for c, r in self.celdas():
            rect = pygame.Rect(offset_x + c * CELDA + 1,
                               offset_y + r * CELDA + 1,
                               CELDA - 2, CELDA - 2)
            pygame.draw.rect(surface, AMARILLO, rect, 3, border_radius=4)
        # Dibuja el icono del cañón en el origen
        cx, cy = self.canon_origen_px(offset_x, offset_y)
        pygame.draw.circle(surface, AMARILLO, (cx, cy), 6)
        pygame.draw.circle(surface, NEGRO,    (cx, cy), 3)

    def recibir_impacto(self, col, row):
        """Devuelve True si (col,row) golpea este barco."""
        for i, (c, r) in enumerate(self.celdas()):
            if c == col and r == row:
                self.hits.add(i)
                if len(self.hits) == self.largo:
                    self.hundido = True
                return True
        return False

    def draw(self, surface, offset_x, offset_y, revelar=True):
        """Dibuja el barco en el grid. revelar=False oculta barcos enemigos."""
        if not revelar:
            return
        celdas = self.celdas()
        # Sombra
        for (c, r) in celdas:
            x = offset_x + c * CELDA + 3
            y = offset_y + r * CELDA + 3
            pygame.draw.rect(surface, (0, 0, 0, 80), (x, y, CELDA - 2, CELDA - 2), border_radius=4)

        for i, (c, r) in enumerate(celdas):
            x = offset_x + c * CELDA
            y = offset_y + r * CELDA
            rect = pygame.Rect(x + 1, y + 1, CELDA - 2, CELDA - 2)

            if i in self.hits:
                color = ROJO_DANIO
            elif self.hundido:
                color = (60, 20, 20)
            else:
                color = self.color

            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, GRIS_CLARO, rect, 1, border_radius=4)

            # Símbolo en la primera celda
            if i == 0:
                font = pygame.font.SysFont("monospace", 11, bold=True)
                letra = self.nombre[0]
                txt = font.render(letra, True, BLANCO)
                surface.blit(txt, (x + CELDA // 2 - txt.get_width() // 2,
                                   y + CELDA // 2 - txt.get_height() // 2))

            # Llama/explosión en celda golpeada
            if i in self.hits:
                font2 = pygame.font.SysFont("segoe ui emoji", 14)
                fuego = font2.render("💥", True, AMARILLO)
                surface.blit(fuego, (x + 4, y + 4))


def crear_flota_defecto(jugador):
    """Crea la flota inicial para el jugador con posiciones predefinidas."""
    flota = []
    # Posiciones distintas para P1 y P2
    posiciones = [
        (0, 0, True),
        (0, 2, True),
        (0, 4, True),
        (4, 4, False),
        (6, 3, True),
    ]
    for i, (nombre, largo, color) in enumerate(TIPOS_BARCOS):
        col, row, horiz = posiciones[i]
        flota.append(Ship(nombre, largo, color, col, row, horiz))
    return flota


def crear_flota_desde_colocacion(barcos_colocados):
    """
    Crea una flota limpia a partir de los barcos de la pantalla de placement.
    """
    flota = []
    for b in barcos_colocados:
        nuevo = Ship(b.nombre, b.largo, b.color, b.col, b.row, b.horizontal)
        flota.append(nuevo)
    return flota


def flota_hundida(flota):
    return all(s.hundido for s in flota)
