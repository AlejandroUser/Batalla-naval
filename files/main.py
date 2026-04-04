import pygame
import sys
import time

pygame.init()

ANCHO, ALTO = 1400, 900
screen = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("⚓ Batalla Naval — Disparo Parabólico")
clock = pygame.time.Clock()

# Colores
AZUL_OSCURO  = (8,  20,  55)
AZUL_MAR     = (15, 70, 140)
CELESTE      = (80, 170, 230)
BLANCO       = (235, 245, 255)
GRIS         = (140, 150, 165)
AMARILLO     = (255, 210, 50)
ROJO         = (210, 60,  60)
VERDE        = (50, 200, 100)
NEGRO        = (5,   10,  20)
NARANJA      = (255, 140, 30)


def dibujar_fondo_menu(surface, t):
    """Fondo animado para el menú."""
    for y in range(ALTO):
        ratio = y / ALTO
        r = int(5  + ratio * 10)
        g = int(15 + ratio * 50)
        b = int(50 + ratio * 100)
        pygame.draw.line(surface, (r, g, b), (0, y), (ANCHO, y))

    # Olas animadas
    font = pygame.font.SysFont("segoe ui emoji", 22)
    for x in range(-80, ANCHO + 80, 90):
        for y in range(100, ALTO, 140):
            offset = int(20 * pygame.math.Vector2(1, 0).rotate(t * 30 + x * 0.5).y)
            ola = font.render("〜", True, (25, 80, 160))
            surface.blit(ola, (x, y + offset))


def boton(surface, texto, x, y, ancho, alto, color_fondo, color_borde, color_txt, hover=False):
    factor = 1.05 if hover else 1.0
    ax = int(x - (ancho * factor - ancho) / 2)
    ay = int(y - (alto * factor - alto) / 2)
    aw = int(ancho * factor)
    ah = int(alto * factor)

    fondo = pygame.Surface((aw, ah), pygame.SRCALPHA)
    fondo.fill((*color_fondo, 200))
    surface.blit(fondo, (ax, ay))
    pygame.draw.rect(surface, color_borde, (ax, ay, aw, ah), 2, border_radius=10)

    font = pygame.font.SysFont("monospace", 20, bold=True)
    txt = font.render(texto, True, color_txt)
    surface.blit(txt, (ax + aw // 2 - txt.get_width() // 2,
                       ay + ah // 2 - txt.get_height() // 2))
    return pygame.Rect(ax, ay, aw, ah)


def pantalla_menu():
    t = 0.0
    font_titulo = pygame.font.SysFont("monospace", 64, bold=True)
    font_sub    = pygame.font.SysFont("monospace", 22)
    font_hint   = pygame.font.SysFont("monospace", 15)

    btns = {
        "cpu":     pygame.Rect(500, 310, 400, 58),
        "host":    pygame.Rect(500, 390, 400, 58),
        "cliente": pygame.Rect(500, 470, 400, 58),
        "salir":   pygame.Rect(500, 555, 400, 48),
    }

    while True:
        dt = clock.tick(60) / 1000.0
        t += dt
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "salir"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btns["cpu"].collidepoint(mx, my):
                    return "cpu"
                if btns["host"].collidepoint(mx, my):
                    return "host"
                if btns["cliente"].collidepoint(mx, my):
                    return "cliente"
                if btns["salir"].collidepoint(mx, my):
                    return "salir"

        dibujar_fondo_menu(screen, t)

        # Título
        titulo = font_titulo.render("⚓ BATALLA NAVAL", True, CELESTE)
        sombra  = font_titulo.render("⚓ BATALLA NAVAL", True, NEGRO)
        screen.blit(sombra, (ANCHO // 2 - titulo.get_width() // 2 + 3, 103))
        screen.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 100))

        sub = font_sub.render("Disparo Parabólico — Física Realista", True, AMARILLO)
        screen.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 175))

        # Decoración
        for i in range(5):
            pygame.draw.circle(screen, (30, 90, 170),
                               (200 + i * 50, 220), 4)
            pygame.draw.circle(screen, (30, 90, 170),
                               (ANCHO - 200 - i * 50, 220), 4)

        # Botones
        boton(screen, "🤖  Jugar vs CPU",
              btns["cpu"].x, btns["cpu"].y, btns["cpu"].w, btns["cpu"].h,
              (20, 60, 120), CELESTE, BLANCO,
              hover=btns["cpu"].collidepoint(mx, my))

        boton(screen, "🌐  Crear Partida LAN (Host)",
              btns["host"].x, btns["host"].y, btns["host"].w, btns["host"].h,
              (20, 80, 40), VERDE, BLANCO,
              hover=btns["host"].collidepoint(mx, my))

        boton(screen, "🔗  Unirse a Partida LAN",
              btns["cliente"].x, btns["cliente"].y, btns["cliente"].w, btns["cliente"].h,
              (80, 40, 20), NARANJA, BLANCO,
              hover=btns["cliente"].collidepoint(mx, my))

        boton(screen, "✕  Salir",
              btns["salir"].x, btns["salir"].y, btns["salir"].w, btns["salir"].h,
              (60, 20, 20), ROJO, BLANCO,
              hover=btns["salir"].collidepoint(mx, my))

        hint = font_hint.render("ESC en partida = volver al menú  |  R = reiniciar tras victoria", True, GRIS)
        screen.blit(hint, (ANCHO // 2 - hint.get_width() // 2, ALTO - 30))

        pygame.display.flip()


def pantalla_host():
    """Espera conexión del cliente y muestra la IP."""
    from network import ServidorLAN
    servidor = ServidorLAN()
    ip = servidor.iniciar()

    font_big  = pygame.font.SysFont("monospace", 30, bold=True)
    font_med  = pygame.font.SysFont("monospace", 22)
    font_hint = pygame.font.SysFont("monospace", 15)
    t = 0.0

    while True:
        dt = clock.tick(60) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                servidor.cerrar()
                return None, None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                servidor.cerrar()
                return None, None

        dibujar_fondo_menu(screen, t)

        txt1 = font_big.render("🌐 MODO HOST — Esperando jugador...", True, VERDE)
        screen.blit(txt1, (ANCHO // 2 - txt1.get_width() // 2, 240))

        txt2 = font_med.render(f"Tu IP local: {ip}:{5555}", True, AMARILLO)
        screen.blit(txt2, (ANCHO // 2 - txt2.get_width() // 2, 330))

        txt3 = font_med.render("Comparte esta IP con tu rival.", True, BLANCO)
        screen.blit(txt3, (ANCHO // 2 - txt3.get_width() // 2, 390))

        dots = "." * (int(t * 2) % 4)
        espera = font_med.render(f"Esperando conexión{dots}", True, CELESTE)
        screen.blit(espera, (ANCHO // 2 - espera.get_width() // 2, 470))

        hint = font_hint.render("ESC = cancelar", True, GRIS)
        screen.blit(hint, (ANCHO // 2 - hint.get_width() // 2, ALTO - 30))

        pygame.display.flip()

        if servidor.hay_cliente_conectado():
            return servidor, 1  # jugador 1 = host


def pantalla_cliente():
    """Permite ingresar la IP del host."""
    from network import ClienteLAN
    font_big  = pygame.font.SysFont("monospace", 28, bold=True)
    font_med  = pygame.font.SysFont("monospace", 22)
    font_hint = pygame.font.SysFont("monospace", 15)

    ip_str = ""
    mensaje = ""
    color_msg = BLANCO
    t = 0.0

    while True:
        dt = clock.tick(60) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None
                elif event.key == pygame.K_BACKSPACE:
                    ip_str = ip_str[:-1]
                elif event.key == pygame.K_RETURN:
                    mensaje = f"Conectando a {ip_str}..."
                    color_msg = CELESTE
                    cliente = ClienteLAN()
                    if cliente.conectar(ip_str):
                        return cliente, 2  # jugador 2 = cliente
                    else:
                        mensaje = "❌ No se pudo conectar. Verifica la IP."
                        color_msg = ROJO
                elif len(ip_str) < 20 and (event.unicode.isdigit() or event.unicode == '.'):
                    ip_str += event.unicode

        dibujar_fondo_menu(screen, t)

        txt1 = font_big.render("🔗 UNIRSE A PARTIDA LAN", True, NARANJA)
        screen.blit(txt1, (ANCHO // 2 - txt1.get_width() // 2, 240))

        txt2 = font_med.render("Ingresa la IP del host:", True, BLANCO)
        screen.blit(txt2, (ANCHO // 2 - txt2.get_width() // 2, 340))

        # Campo de IP
        rect_ip = pygame.Rect(ANCHO // 2 - 180, 390, 360, 50)
        pygame.draw.rect(screen, (20, 50, 100), rect_ip, border_radius=8)
        pygame.draw.rect(screen, CELESTE, rect_ip, 2, border_radius=8)
        ip_txt = font_big.render(ip_str + "_", True, AMARILLO)
        screen.blit(ip_txt, (rect_ip.x + 12, rect_ip.y + 8))

        # Botón conectar
        btn = pygame.Rect(ANCHO // 2 - 110, 460, 220, 50)
        mx, my = pygame.mouse.get_pos()
        hover = btn.collidepoint(mx, my)
        boton(screen, "CONECTAR", btn.x, btn.y, btn.w, btn.h,
              (20, 80, 40), VERDE, BLANCO, hover=hover)

        if mensaje:
            msg_txt = font_med.render(mensaje, True, color_msg)
            screen.blit(msg_txt, (ANCHO // 2 - msg_txt.get_width() // 2, 530))

        hint = font_hint.render("ESC = cancelar  |  ENTER = conectar", True, GRIS)
        screen.blit(hint, (ANCHO // 2 - hint.get_width() // 2, ALTO - 30))

        pygame.display.flip()


# ─── Loop principal ───────────────────────────
def main():
    while True:
        resultado = pantalla_menu()

        if resultado == "salir":
            break

        elif resultado == "cpu":
            from game import JuegoCPU
            juego = JuegoCPU(screen)
            r = juego.run()
            if r == "salir":
                break

        elif resultado == "host":
            red, jugador_id = pantalla_host()
            if red is not None:
                from game import JuegoLAN
                juego = JuegoLAN(screen, red, jugador_id)
                r = juego.run()
                red.cerrar()
                if r == "salir":
                    break

        elif resultado == "cliente":
            red, jugador_id = pantalla_cliente()
            if red is not None:
                from game import JuegoLAN
                juego = JuegoLAN(screen, red, jugador_id)
                r = juego.run()
                red.cerrar()
                if r == "salir":
                    break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
