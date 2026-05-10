import pygame
import math
import random
from ships import crear_flota_defecto, flota_hundida
from physics import (calcular_trayectoria, pixel_a_celda,
                     celda_valida, celda_valida_px,
                     angulo_para_alcanzar,
                     GRID_IZQ_X, GRID_IZQ_Y,
                     GRID_DER_X, GRID_DER_Y,
                     CELDA_G, GRID_W, GRID_H, GRAVEDAD)
from ui import (dibujar_fondo_mar, dibujar_grid, dibujar_marcadores,
                PanelDisparo, PanelInfo, dibujar_trayectoria, pantalla_ganador,
                BLANCO, NEGRO, AMARILLO, CELESTE, ROJO, VERDE, GRIS, NARANJA)

import ships
ships.CELDA = CELDA_G

ANCHO, ALTO = 1400, 900
FPS = 60
CANON_Y = GRID_DER_Y + GRID_H   # base del grid propio = 545


def _canon_jugador(barco):
    celdas = barco.celdas()
    col, _ = celdas[len(celdas) // 2]
    return GRID_DER_X + col * CELDA_G + CELDA_G // 2, CANON_Y


def _canon_cpu(barco):
    celdas = barco.celdas()
    col, _ = celdas[len(celdas) // 2]
    return GRID_IZQ_X + col * CELDA_G + CELDA_G // 2, GRID_IZQ_Y + GRID_H


# ══════════════════════════════════════════════════════
#  vs CPU
# ══════════════════════════════════════════════════════
class JuegoCPU:
    def __init__(self, screen, flota_jugador=None):
        self.screen = screen
        self.clock  = pygame.time.Clock()
        self._flota_jugador_inicial = flota_jugador
        self.reiniciar()

    def reiniciar(self):
        from ships import crear_flota_defecto
        if self._flota_jugador_inicial:
            # Clonar la flota para que reiniciar funcione
            from ships import crear_flota_desde_colocacion
            self.flota_j = crear_flota_desde_colocacion(self._flota_jugador_inicial)
        else:
            self.flota_j = crear_flota_defecto(1)
        self.flota_c = crear_flota_defecto(2)
        self.dj_ag = set(); self.dj_im = set()
        self.dc_ag = set(); self.dc_im = set()
        self.turno       = "jugador"
        self.barco_sel   = None
        self.panel_d     = PanelDisparo(60, 590)
        self.panel_i     = PanelInfo(850, 585)
        self.log         = ["¡Batalla iniciada!", "Clic en tu barco para disparar"]
        self.proy_activo = False
        self.puntos      = []
        self.idx         = 0
        self.pos_proy    = (0, 0)
        self.dest_px     = (0, 0)
        self.es_jugador  = True
        self.fase        = "input"
        self.ganador     = None
        self.cpu_timer   = 0.0

    def _vivos(self, f): return [b for b in f if not b.hundido]

    def _click(self, mx, my):
        if self.turno != "jugador" or self.proy_activo: return
        for b in self._vivos(self.flota_j):
            for col, row in b.celdas():
                x = GRID_DER_X + col*CELDA_G; y = GRID_DER_Y + row*CELDA_G
                if x <= mx < x+CELDA_G and y <= my < y+CELDA_G:
                    self.barco_sel = b
                    self.panel_d.mensaje = f"Cañón listo: {b.nombre}"
                    self.panel_d.mensaje_color = VERDE
                    return

    def _disparar_j(self):
        if not self.barco_sel:
            self.panel_d.mensaje = "Primero clic en un barco de tu flota"
            self.panel_d.mensaje_color = ROJO; return
        vals = self.panel_d.obtener_valores()
        if not vals: return
        a, p = vals
        cx, cy = _canon_jugador(self.barco_sel)
        pts, imp = calcular_trayectoria(cx, cy, -a, p)
        self._anim(pts, imp, True)

    def _disparar_cpu(self):
        vc = self._vivos(self.flota_c); vj = self._vivos(self.flota_j)
        if not vc or not vj: return
        b = random.choice(vc)
        cx, cy = _canon_cpu(b)
        cands = [(c,r) for c in range(10) for r in range(10)
                 if (c,r) not in self.dc_ag and (c,r) not in self.dc_im]
        adj = [(c,r) for ci,ri in self.dc_im
               for c,r in [(ci-1,ri),(ci+1,ri),(ci,ri-1),(ci,ri+1)] if (c,r) in cands]
        tc, tr = random.choice(adj if adj else cands)
        ox = GRID_DER_X + tc*CELDA_G + CELDA_G//2
        oy = GRID_DER_Y + tr*CELDA_G + CELDA_G//2
        pot = 65.0
        ai = angulo_para_alcanzar(cx, cy, ox, oy, pot)
        if ai is None: pot=80.0; ai=angulo_para_alcanzar(cx,cy,ox,oy,pot)
        if ai is None: ai=random.uniform(30,60)
        af = max(5, min(85, ai + random.uniform(-8,8)))
        pot += random.uniform(-8,8)
        pts, imp = calcular_trayectoria(cx, cy, af, pot)
        self._anim(pts, imp, False)

    def _anim(self, pts, imp, jug):
        self.puntos=pts; self.idx=0
        self.pos_proy=pts[0] if pts else (0,0)
        self.dest_px=imp; self.es_jugador=jug
        self.proy_activo=True; self.fase="animacion"

    def _procesar(self):
        px, py = self.dest_px
        if self.es_jugador:
            en = celda_valida_px(px, py, GRID_IZQ_X, GRID_IZQ_Y)
            if not en:
                self.log.append(f"¡Tiro al mar! (x={px:.0f})")
            else:
                col, row = pixel_a_celda(px, py, GRID_IZQ_X, GRID_IZQ_Y)
                hit = False
                for b in self.flota_c:
                    if b.recibir_impacto(col, row):
                        hit=True; self.dj_im.add((col,row))
                        self.log.append(f"¡Impacto! {chr(65+col)}{row+1}")
                        if b.hundido: self.log.append(f"¡{b.nombre} hundido!")
                        break
                if not hit: self.dj_ag.add((col,row)); self.log.append(f"Agua en {chr(65+col)}{row+1}")
            if flota_hundida(self.flota_c): self.ganador="¡GANASTE!"
            else: self.turno="cpu"; self.log.append("Turno CPU...")
        else:
            en = celda_valida_px(px, py, GRID_DER_X, GRID_DER_Y)
            if not en:
                self.log.append("CPU falló — tiro al mar")
            else:
                col, row = pixel_a_celda(px, py, GRID_DER_X, GRID_DER_Y)
                hit = False
                for b in self.flota_j:
                    if b.recibir_impacto(col, row):
                        hit=True; self.dc_im.add((col,row))
                        self.log.append(f"CPU te golpeó en {chr(65+col)}{row+1}!")
                        if b.hundido: self.log.append(f"¡{b.nombre} hundido!")
                        break
                if not hit: self.dc_ag.add((col,row)); self.log.append(f"CPU falló en {chr(65+col)}{row+1}")
            if flota_hundida(self.flota_j): self.ganador="¡CPU GANÓ!"
            else: self.turno="jugador"; self.barco_sel=None; self.log.append("Tu turno")
        self.proy_activo=False; self.fase="resultado"

    def _draw_referencia(self):
        if not self.barco_sel or self.proy_activo: return
        cx, cy = _canon_jugador(self.barco_sel)
        borde = GRID_IZQ_X + GRID_W
        for x in range(borde, cx, 14):
            pygame.draw.circle(self.screen, (50,100,160), (x, cy), 1)
        pygame.draw.circle(self.screen, AMARILLO, (cx, cy), 8)
        pygame.draw.circle(self.screen, NEGRO,    (cx, cy), 4)
        # Pistas de ángulo para el centro del grid enemigo
        font = pygame.font.SysFont("monospace", 12)
        y_c = GRID_IZQ_Y + GRID_H // 2
        for i, pot in enumerate([50, 65, 80]):
            a = angulo_para_alcanzar(cx, cy, GRID_IZQ_X + 5*CELDA_G, y_c, pot)
            if a:
                t = font.render(f"p={pot} → a≈{a:.0f}°", True, (100,170,230))
                self.screen.blit(t, (cx - t.get_width() - 10, cy - 42 + i*14))
        dist = cx - borde
        info = font.render(f"Dist cañón→grid: {dist}px  |  g=9.8 m/s²", True, GRIS)
        self.screen.blit(info, (ANCHO//2 - info.get_width()//2, ALTO - 16))

    def _draw_mar(self):
        mx = GRID_IZQ_X + GRID_W + 2
        mw = GRID_DER_X - mx - 2
        ms = pygame.Surface((mw, GRID_H), pygame.SRCALPHA)
        ms.fill((10, 60, 130, 100))
        self.screen.blit(ms, (mx, GRID_IZQ_Y))
        font = pygame.font.SysFont("monospace", 15)
        t = font.render("~ MAR ~", True, (60, 130, 200))
        self.screen.blit(t, (mx + mw//2 - t.get_width()//2,
                             GRID_IZQ_Y + GRID_H//2 - t.get_height()//2))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: return "salir"
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE: return "menu"
                    if ev.key == pygame.K_r and self.ganador: self.reiniciar(); continue
                    if self.turno == "jugador" and not self.proy_activo:
                        self.panel_d.manejar_evento(ev)
                        if ev.key == pygame.K_RETURN: self._disparar_j()
                if ev.type == pygame.MOUSEBUTTONDOWN: self._click(*ev.pos)

            if self.turno == "cpu" and not self.proy_activo and not self.ganador:
                self.cpu_timer += dt
                if self.cpu_timer >= 1.3: self.cpu_timer=0.0; self._disparar_cpu()

            if self.fase == "resultado" and not self.ganador: self.fase = "input"

            if self.proy_activo and self.fase == "animacion":
                self.idx += 3
                if self.idx >= len(self.puntos): self._procesar()
                else: self.pos_proy = self.puntos[self.idx]

            # ── dibujo ──────────────────────────────────────────────
            dibujar_fondo_mar(self.screen, ANCHO, ALTO)
            dibujar_grid(self.screen, GRID_IZQ_X, GRID_IZQ_Y, celda_size=CELDA_G,
                         disparos_agua=self.dj_ag, disparos_impacto=self.dj_im,
                         titulo="FLOTA ENEMIGA")
            dibujar_grid(self.screen, GRID_DER_X, GRID_DER_Y, celda_size=CELDA_G,
                         disparos_agua=self.dc_ag, disparos_impacto=self.dc_im,
                         titulo="TU FLOTA")
            self._draw_mar()

            for b in self.flota_c: b.draw(self.screen, GRID_IZQ_X, GRID_IZQ_Y, revelar=b.hundido)
            for b in self.flota_j: b.draw(self.screen, GRID_DER_X, GRID_DER_Y, revelar=True)

            if self.barco_sel and not self.proy_activo:
                self.barco_sel.draw_seleccionado(self.screen, GRID_DER_X, GRID_DER_Y)

            dibujar_marcadores(self.screen, GRID_IZQ_X, GRID_IZQ_Y,
                               self.dj_ag, self.dj_im, CELDA_G)
            dibujar_marcadores(self.screen, GRID_DER_X, GRID_DER_Y,
                               self.dc_ag, self.dc_im, CELDA_G)

            if self.proy_activo:
                trail = self.puntos[max(0, self.idx-40):self.idx]
                dibujar_trayectoria(self.screen, trail)
                px, py = self.pos_proy
                pygame.draw.circle(self.screen, AMARILLO, (int(px),int(py)), 9)
                pygame.draw.circle(self.screen, BLANCO,   (int(px),int(py)), 4)

            self._draw_referencia()
            self.panel_d.draw(self.screen,
                              turno_activo=(self.turno=="jugador" and not self.proy_activo),
                              barco_nombre=self.barco_sel.nombre if self.barco_sel else None)
            self.panel_i.draw(self.screen, self.turno, "jugador",
                              self.flota_j, self.flota_c, self.log)

            font = pygame.font.SysFont("monospace", 22, bold=True)
            t = font.render("BATALLA NAVAL  |  vs CPU  |  Física Parabólica", True, CELESTE)
            self.screen.blit(t, (ANCHO//2 - t.get_width()//2, 18))

            if self.ganador: pantalla_ganador(self.screen, ANCHO, ALTO, self.ganador)
            pygame.display.flip()


# ══════════════════════════════════════════════════════
#  LAN
# ══════════════════════════════════════════════════════
class JuegoLAN:
    def __init__(self, screen, red, jugador_id, flota_propia=None):
        self.screen=screen; self.clock=pygame.time.Clock()
        self.red=red; self.jugador_id=jugador_id
        self._flota_propia_inicial = flota_propia
        self.reiniciar()

    def reiniciar(self):
        from ships import crear_flota_defecto, crear_flota_desde_colocacion
        if self._flota_propia_inicial:
            self.flota_p = crear_flota_desde_colocacion(self._flota_propia_inicial)
        else:
            self.flota_p  = crear_flota_defecto(self.jugador_id)
        self.flota_e  = crear_flota_defecto(3-self.jugador_id)
        self.dp_ag=set(); self.dp_im=set()
        self.de_ag=set(); self.de_im=set()
        self.turno_actual=1; self.barco_sel=None
        self.panel_d=PanelDisparo(60,590); self.panel_i=PanelInfo(850,585)
        self.log=[f"Jugador {self.jugador_id}","Turno J1"]
        self.proy_activo=False; self.puntos=[]; self.idx=0
        self.pos_proy=(0,0); self.dest_px=(0,0)
        self.propio=True; self.ganador=None; self.fase="input"

    def es_mi_turno(self): return self.turno_actual==self.jugador_id

    def _click(self,mx,my):
        if not self.es_mi_turno() or self.proy_activo: return
        for b in [b for b in self.flota_p if not b.hundido]:
            for col,row in b.celdas():
                x=GRID_DER_X+col*CELDA_G; y=GRID_DER_Y+row*CELDA_G
                if x<=mx<x+CELDA_G and y<=my<y+CELDA_G:
                    self.barco_sel=b
                    self.panel_d.mensaje=f"Cañón: {b.nombre}"
                    self.panel_d.mensaje_color=VERDE; return

    def _lanzar(self):
        if not self.barco_sel:
            self.panel_d.mensaje="Selecciona un barco"
            self.panel_d.mensaje_color=ROJO; return
        vals=self.panel_d.obtener_valores()
        if not vals: return
        a,p=vals; cx,cy=_canon_jugador(self.barco_sel)
        self.red.enviar({"tipo":"disparo","angulo":-a,"potencia":p,"ox":cx,"oy":cy})
        pts,imp=calcular_trayectoria(cx,cy,-a,p)
        self.puntos=pts; self.idx=0
        self.pos_proy=pts[0] if pts else (0,0)
        self.dest_px=imp; self.propio=True
        self.proy_activo=True; self.fase="animacion"
        self.barco_sel=None

    def _imp(self, propio):
        px,py=self.dest_px
        if propio:
            en=celda_valida_px(px,py,GRID_IZQ_X,GRID_IZQ_Y)
            if not en: self.log.append("Tiro al mar")
            else:
                col,row=pixel_a_celda(px,py,GRID_IZQ_X,GRID_IZQ_Y)
                hit=False
                for b in self.flota_e:
                    if b.recibir_impacto(col,row):
                        hit=True; self.dp_im.add((col,row))
                        self.log.append(f"Impacto {chr(65+col)}{row+1}!")
                        if b.hundido: self.log.append(f"{b.nombre} hundido!"); break
                if not hit: self.dp_ag.add((col,row)); self.log.append(f"Agua {chr(65+col)}{row+1}")
            if flota_hundida(self.flota_e):
                self.ganador=f"J{self.jugador_id} GANA!"
                self.red.enviar({"tipo":"ganador","ganador":self.jugador_id})
            else:
                self.turno_actual=3-self.jugador_id
                self.log.append(f"Turno J{self.turno_actual}")
        else:
            en=celda_valida_px(px,py,GRID_DER_X,GRID_DER_Y)
            if not en: self.log.append("Rival al mar")
            else:
                col,row=pixel_a_celda(px,py,GRID_DER_X,GRID_DER_Y)
                hit=False
                for b in self.flota_p:
                    if b.recibir_impacto(col,row):
                        hit=True; self.de_im.add((col,row))
                        self.log.append(f"Rival golpea {chr(65+col)}{row+1}!")
                        if b.hundido: self.log.append(f"{b.nombre} hundido!"); break
                if not hit: self.de_ag.add((col,row)); self.log.append(f"Rival falla {chr(65+col)}{row+1}")
            if flota_hundida(self.flota_p): self.ganador=f"J{3-self.jugador_id} GANA!"
            else: self.turno_actual=self.jugador_id; self.log.append("Tu turno")
        self.proy_activo=False; self.fase="input"

    def run(self):
        while True:
            self.clock.tick(FPS)
            while self.red.hay_mensaje():
                msg=self.red.obtener_mensaje()
                if msg["tipo"]=="disparo" and not self.es_mi_turno():
                    pts,imp=calcular_trayectoria(msg["ox"],msg["oy"],-msg["angulo"],msg["potencia"])
                    self.puntos=pts; self.idx=0
                    self.pos_proy=pts[0] if pts else (0,0)
                    self.dest_px=imp; self.propio=False
                    self.proy_activo=True; self.fase="animacion"
                elif msg["tipo"]=="ganador":
                    self.ganador=f"J{msg['ganador']} GANA!"
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: return "salir"
                if ev.type==pygame.KEYDOWN:
                    if ev.key==pygame.K_ESCAPE: return "menu"
                    if ev.key==pygame.K_r and self.ganador: self.reiniciar(); continue
                    if self.es_mi_turno() and not self.proy_activo:
                        self.panel_d.manejar_evento(ev)
                        if ev.key==pygame.K_RETURN: self._lanzar()
                if ev.type==pygame.MOUSEBUTTONDOWN: self._click(*ev.pos)
            if self.proy_activo and self.fase=="animacion":
                self.idx+=3
                if self.idx>=len(self.puntos): self._imp(self.propio)
                else: self.pos_proy=self.puntos[self.idx]

            dibujar_fondo_mar(self.screen,ANCHO,ALTO)
            dibujar_grid(self.screen,GRID_IZQ_X,GRID_IZQ_Y,celda_size=CELDA_G,
                         disparos_agua=self.dp_ag,disparos_impacto=self.dp_im,titulo="FLOTA ENEMIGA")
            dibujar_grid(self.screen,GRID_DER_X,GRID_DER_Y,celda_size=CELDA_G,
                         disparos_agua=self.de_ag,disparos_impacto=self.de_im,titulo="TU FLOTA")
            mx=GRID_IZQ_X+GRID_W+2; mw=GRID_DER_X-mx-2
            ms=pygame.Surface((mw,GRID_H),pygame.SRCALPHA); ms.fill((10,60,130,100))
            self.screen.blit(ms,(mx,GRID_IZQ_Y))
            for b in self.flota_e: b.draw(self.screen,GRID_IZQ_X,GRID_IZQ_Y,revelar=b.hundido)
            for b in self.flota_p: b.draw(self.screen,GRID_DER_X,GRID_DER_Y,revelar=True)
            if self.barco_sel and not self.proy_activo:
                self.barco_sel.draw_seleccionado(self.screen,GRID_DER_X,GRID_DER_Y)
            dibujar_marcadores(self.screen,GRID_IZQ_X,GRID_IZQ_Y,self.dp_ag,self.dp_im,CELDA_G)
            dibujar_marcadores(self.screen,GRID_DER_X,GRID_DER_Y,self.de_ag,self.de_im,CELDA_G)
            if self.proy_activo:
                trail=self.puntos[max(0,self.idx-40):self.idx]
                dibujar_trayectoria(self.screen,trail)
                px,py=self.pos_proy
                pygame.draw.circle(self.screen,AMARILLO,(int(px),int(py)),9)
                pygame.draw.circle(self.screen,BLANCO,(int(px),int(py)),4)
            self.panel_d.draw(self.screen,
                turno_activo=(self.es_mi_turno() and not self.proy_activo),
                barco_nombre=self.barco_sel.nombre if self.barco_sel else None)
            self.panel_i.draw(self.screen,self.turno_actual,self.jugador_id,
                              self.flota_p,self.flota_e,self.log)
            f=pygame.font.SysFont("monospace",22,bold=True)
            t=f.render(f"BATALLA NAVAL LAN  |  Jugador {self.jugador_id}",True,CELESTE)
            self.screen.blit(t,(ANCHO//2-t.get_width()//2,18))
            if self.ganador: pantalla_ganador(self.screen,ANCHO,ALTO,self.ganador)
            pygame.display.flip()
