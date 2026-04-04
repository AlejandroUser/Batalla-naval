import socket
import threading
import json
import time

PUERTO = 5555
BUFFER = 4096


class ServidorLAN:
    """Servidor para el modo multijugador LAN (host)."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clientes = []
        self.mensajes_recibidos = []
        self.lock = threading.Lock()
        self.corriendo = False
        self.ip_local = self._obtener_ip()

    def _obtener_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def iniciar(self):
        self.socket.bind(("", PUERTO))
        self.socket.listen(1)
        self.corriendo = True
        t = threading.Thread(target=self._aceptar_conexiones, daemon=True)
        t.start()
        return self.ip_local

    def _aceptar_conexiones(self):
        while self.corriendo:
            try:
                self.socket.settimeout(1.0)
                conn, addr = self.socket.accept()
                self.clientes.append(conn)
                t = threading.Thread(target=self._recibir, args=(conn,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except:
                break

    def _recibir(self, conn):
        while self.corriendo:
            try:
                data = conn.recv(BUFFER)
                if not data:
                    break
                msg = json.loads(data.decode())
                with self.lock:
                    self.mensajes_recibidos.append(msg)
            except:
                break

    def enviar(self, msg):
        data = json.dumps(msg).encode()
        for c in self.clientes:
            try:
                c.sendall(data)
            except:
                pass

    def hay_mensaje(self):
        with self.lock:
            return len(self.mensajes_recibidos) > 0

    def obtener_mensaje(self):
        with self.lock:
            if self.mensajes_recibidos:
                return self.mensajes_recibidos.pop(0)
        return None

    def hay_cliente_conectado(self):
        return len(self.clientes) > 0

    def cerrar(self):
        self.corriendo = False
        self.socket.close()


class ClienteLAN:
    """Cliente para el modo multijugador LAN."""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mensajes_recibidos = []
        self.lock = threading.Lock()
        self.conectado = False

    def conectar(self, ip):
        try:
            self.socket.settimeout(5.0)
            self.socket.connect((ip, PUERTO))
            self.socket.settimeout(None)
            self.conectado = True
            t = threading.Thread(target=self._recibir, daemon=True)
            t.start()
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            return False

    def _recibir(self):
        while self.conectado:
            try:
                data = self.socket.recv(BUFFER)
                if not data:
                    break
                msg = json.loads(data.decode())
                with self.lock:
                    self.mensajes_recibidos.append(msg)
            except:
                break

    def enviar(self, msg):
        if self.conectado:
            try:
                data = json.dumps(msg).encode()
                self.socket.sendall(data)
            except:
                self.conectado = False

    def hay_mensaje(self):
        with self.lock:
            return len(self.mensajes_recibidos) > 0

    def obtener_mensaje(self):
        with self.lock:
            if self.mensajes_recibidos:
                return self.mensajes_recibidos.pop(0)
        return None

    def cerrar(self):
        self.conectado = False
        self.socket.close()
