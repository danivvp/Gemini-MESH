import json
import datetime
import os

# MODULO 5: REGISTRO DE ERRORES ---
# Clase para los nodos de la lista de errores (Log cronologico)
class NodoError:
    def __init__(self, codigo, descripcion):
        self.fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.codigo = codigo
        self.descripcion = descripcion
        self.siguiente = None

class ListaErrores:
    def __init__(self):
        self.cabeza = None

    def registrar(self, codigo, descripcion):
        nuevo = NodoError(codigo, descripcion)
        if not self.cabeza:
            self.cabeza = nuevo
        else:
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo

    def mostrar(self):
        actual = self.cabeza
        if not actual:
            print("No hay errores en el registro.")
            return
        print("\n--- LOG DE ERRORES ---")
        while actual:
            print(f"[{actual.fecha_hora}] {actual.codigo}: {actual.descripcion}")
            actual = actual.siguiente

# --- MODULO 3: GESTION DE RESTAURACION (PILAS) ---
# Guardamos estados previos para el comando "undo"
class NodoEstado:
    def __init__(self, sys_inst, temp):
        self.systemInstruction = sys_inst
        self.temperatura = temp
        self.siguiente = None

class PilaRestauracion:
    def __init__(self):
        self.tope = None

    def push(self, sys_inst, temp):
        nuevo = NodoEstado(sys_inst, temp)
        nuevo.siguiente = self.tope
        self.tope = nuevo

    def pop(self):
        if not self.tope:
            return None
        estado = (self.tope.systemInstruction, self.tope.temperatura)
        self.tope = self.tope.siguiente
        return estado

# MODULO 2: TDA CONTEXTO (COLAS) ---
# Mantiene los ultimos N mensajes en memoria dinamica
class NodoMensaje:
    def __init__(self, msj):
        self.contenido = msj
        self.siguiente = None

class ColaContexto:
    def __init__(self, n):
        self.frente = None
        self.final = None
        self.max_mensajes = n
        self.cantidad_actual = 0

    def encolar(self, msj):
        nuevo = NodoMensaje(msj)
        if not self.frente:
            self.frente = self.final = nuevo
        else:
            self.final.siguiente = nuevo
            self.final = nuevo
        self.cantidad_actual += 1
        # Si superamos el limite N, sacamos el mas viejo (FIFO)
        if self.cantidad_actual > self.max_mensajes:
            self.desencolar()

    def desencolar(self):
        if not self.frente:
            return
        self.frente = self.frente.siguiente
        if not self.frente:
            self.final = None
        self.cantidad_actual -= 1

    def mostrar(self):
        actual = self.frente
        if not actual:
            print("  (Historial vacio)")
        while actual:
            print(f"  > {actual.contenido}")
            actual = actual.siguiente

# MODULO 1: CONFIGURACION (LISTA ENLAZADA DOBLE) ---
# El nodo principal que organiza el sistema
class BotNode:
    def __init__(self, id_u, nombre, mod, key, sys, n_mensajes):
        self.idUnico = id_u
        self.nombreBot = nombre
        self.modelo = mod
        self.apiKey = key
        self.systemInstruction = sys
        self.temperatura = 0.7
        # Punteros a las estructuras hijas
        self.pilaEstados = PilaRestauracion()
        self.colaMensajes = ColaContexto(n_mensajes)
        self.anterior = None
        self.siguiente = None

class GeminiMesh:
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self.errores = ListaErrores()
        self.bot_actual = None

    def crear_bot(self, id_u, nom, mod, key, sys, n):
        nuevo = BotNode(id_u, nom, mod, key, sys, n)
        if not self.cabeza:
            self.cabeza = self.cola = nuevo
        else:
            self.cola.siguiente = nuevo
            nuevo.anterior = self.cola
            self.cola = nuevo

    def listar_bots(self):
        actual = self.cabeza
        if not actual:
            print("No hay bots en el sistema.")
            return
        while actual:
            print(f"ID: {actual.idUnico} | Nombre: {actual.nombreBot} | Modelo: {actual.modelo}")
            actual = actual.siguiente

    def seleccionar_bot(self, id_u):
        actual = self.cabeza
        while actual:
            if str(actual.idUnico) == str(id_u):
                self.bot_actual = actual
                return True
            actual = actual.siguiente
        self.errores.registrar("ERR_404", f"ID {id_u} no encontrado")
        return False

    def guardar_datos(self, ruta):
        datos = []
        actual = self.cabeza
        while actual:
            datos.append({
                "id": actual.idUnico, "nombre": actual.nombreBot,
                "modelo": actual.modelo, "key": actual.apiKey,
                "sys_inst": actual.systemInstruction, "temp": actual.temperatura
            })
            actual = actual.siguiente
        try:
            with open(ruta, 'w') as f:
                json.dump(datos, f, indent=4)
        except Exception as e:
            self.errores.registrar("ERR_SAVE", str(e))

    def cargar_datos(self, ruta):
        try:
            if os.path.exists(ruta):
                with open(ruta, 'r') as f:
                    datos = json.load(f)
                    for d in datos:
                        # Usamos las llaves completas para coincidir con el JSON profesional
                        self.crear_bot(d["id"], d["nombre"], d["modelo"], d["key"], d["sys_inst"], 10)
        except Exception as e:
            self.errores.registrar("ERR_LOAD", str(e))

# MODULO 6: INTERFAZ (CLI) ---
class CLI:
    def __init__(self):
        self.mesh = GeminiMesh()
        self.comandos = {
            "list": self.cmd_list,
            "select": self.cmd_select,
            "chat": self.cmd_chat,
            "edit": self.cmd_edit,
            "undo": self.cmd_undo,
            "log": self.cmd_log,
            "current": self.cmd_current,
            "exit-chatbot": self.cmd_exit_bot
        }

    def cmd_list(self, args): self.mesh.listar_bots()

    def cmd_select(self, args):
        if args and self.mesh.seleccionar_bot(args[0]):
            print(f"Bot '{self.mesh.bot_actual.nombreBot}' seleccionado.")
        else: print("Error: Indica un ID valido.")

    def cmd_chat(self, args):
        if not self.mesh.bot_actual:
            print("Error: Selecciona un bot primero.")
            return
        msj = " ".join(args)
        self.mesh.bot_actual.colaMensajes.encolar(msj)
        print("Mensaje encolado con exito.")

    def cmd_edit(self, args):
        if not self.mesh.bot_actual or len(args) < 2:
            print("Uso: edit sys <nuevo_prompt>")
            return
        if args[0] == "sys":
            # Guardamos snapshot en la pila antes de modificar
            self.mesh.bot_actual.pilaEstados.push(self.mesh.bot_actual.systemInstruction, self.mesh.bot_actual.temperatura)
            self.mesh.bot_actual.systemInstruction = " ".join(args[1:])
            print("Prompt actualizado y respaldado en la Pila.")

    def cmd_undo(self, args):
        if not self.mesh.bot_actual: return
        estado = self.mesh.bot_actual.pilaEstados.pop()
        if estado:
            self.mesh.bot_actual.systemInstruction, self.mesh.bot_actual.temperatura = estado
            print("Restauracion exitosa (Pop de la Pila).")
        else: print("La pila de estados esta vacia.")

    def cmd_log(self, args): self.mesh.errores.mostrar()

    def cmd_current(self, args):
        if not self.mesh.bot_actual: return
        print(f"\n--- ESTADO DEL BOT: {self.mesh.bot_actual.nombreBot} ---")
        print(f"System Instruction: {self.mesh.bot_actual.systemInstruction}")
        print("Cola de Mensajes (Contexto):")
        self.mesh.bot_actual.colaMensajes.mostrar()

    def cmd_exit_bot(self, args):
        self.mesh.bot_actual = None
        print("Volviendo al menu principal...")

    def iniciar(self):
        # Módulo 4: Leer ruta desde archivo de configuracion
        try:
            with open("config.txt", "r") as f:
                ruta_datos = f.read().strip()
        except:
            ruta_datos = "bots.json"

        self.mesh.cargar_datos(ruta_datos)
        
        print("****************************************")
        print("* BIENVENIDA A GEMINI MESH - UJAP   *")
        print("****************************************")
        
        while True:
            entrada = input("\nMenu> ").strip().split()
            if not entrada: continue
            
            cmd = entrada[0].lower()
            if cmd == "exit":
                self.mesh.guardar_datos(ruta_datos)
                print("Saliendo y guardando datos... ¡Exito!")
                break
            
            if cmd in self.comandos:
                self.comandos[cmd](entrada[1:])
            else:
                self.mesh.errores.registrar("ERR_CMD", f"Comando invalido: {cmd}")
                print("Comando no reconocido. Revisa el log.")

if __name__ == "__main__":
    app = CLI()
    app.iniciar()