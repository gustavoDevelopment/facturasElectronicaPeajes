"""Ventana principal (CustomTkinter): procesar facturas y configurar el correo."""
import os
import queue
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk

from bussines.reporter import Reporter
from interfaz import services
from interfaz.ayuda import AYUDA, ENLACES
from settings import get_output_dir, ruta_recurso, set_output_dir

MESES = [str(m) for m in range(1, 13)]


class ReporterGui(Reporter):
    """Envía los eventos de un proceso a la ventana mediante una cola (con su etiqueta)."""

    def __init__(self, cola: queue.Queue, id_proceso: int, etiqueta: str):
        self.cola = cola
        self.id = id_proceso
        self.etiqueta = etiqueta

    def _linea(self, mensaje):
        return f"[{self.etiqueta}] {mensaje}"

    def info(self, mensaje):
        self.cola.put(("log", self._linea(mensaje)))

    def warn(self, mensaje):
        self.cola.put(("log", self._linea(f"⚠️ {mensaje}")))

    def error(self, mensaje):
        self.cola.put(("log", self._linea(f"❌ {mensaje}")))

    def progress(self, actual, total, mensaje=""):
        self.cola.put(("progress", (self.id, actual / total if total else 0)))
        if mensaje:
            self.cola.put(("log", self._linea(f"[{actual}/{total}] {mensaje}")))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Causa Peajes")
        self._icono()
        self.geometry("860x780")
        self.cola = queue.Queue()
        self.ultimo_excel = ""

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self._tab_procesar(self.tabs.add("Procesar"))
        self._tab_correo(self.tabs.add("Correo"))
        self._tab_ayuda(self.tabs.add("Ayuda"))
        self.after(100, self._leer_cola)

    def _icono(self):
        """Ícono de la ventana; si no se puede cargar, la aplicación sigue sin él."""
        try:
            if sys.platform == "win32":
                self.iconbitmap(str(ruta_recurso("assets/icon.ico")))
            else:
                self._img_icono = tk.PhotoImage(file=str(ruta_recurso("assets/icon.png")))
                self.iconphoto(True, self._img_icono)
        except Exception:
            pass

    # ---------- Procesar ----------
    COLUMNAS = ("Tenant", "Mes", "Estado", "Avance", "Correos", "ZIPs", "Facturas", "Excel")

    def _tab_procesar(self, tab):
        tab.columnconfigure(1, weight=1)
        mes, anio = services.mes_anterior()
        self.lanzador = services.Lanzador()
        self.filas = {}
        self.n_procesos = 0

        ctk.CTkLabel(tab, text="Tenant").grid(row=0, column=0, sticky="w", pady=4)
        self.tenant = ctk.CTkComboBox(tab, values=services.listar_tenants() or [""])
        self.tenant.grid(row=0, column=1, columnspan=2, sticky="ew", padx=8)

        ctk.CTkLabel(tab, text="Mes / Año").grid(row=1, column=0, sticky="w", pady=4)
        marco = ctk.CTkFrame(tab, fg_color="transparent")
        marco.grid(row=1, column=1, columnspan=2, sticky="w", padx=8)
        self.mes = ctk.CTkComboBox(marco, values=MESES, width=70)
        self.mes.set(str(mes))
        self.mes.pack(side="left")
        self.anio = ctk.CTkEntry(marco, width=80)
        self.anio.insert(0, str(anio))
        self.anio.pack(side="left", padx=8)
        self.reverificar = ctk.CTkCheckBox(marco, text="Verificar y descargar faltantes aunque ya haya ZIPs")
        self.reverificar.select()
        self.reverificar.pack(side="left", padx=16)

        ctk.CTkLabel(tab, text="Carpeta de salida").grid(row=2, column=0, sticky="w", pady=4)
        self.salida = ctk.CTkEntry(tab)
        self.salida.insert(0, str(get_output_dir()))
        self.salida.grid(row=2, column=1, sticky="ew", padx=8)
        ctk.CTkButton(tab, text="Elegir…", width=80, command=self._elegir_salida).grid(row=2, column=2)

        acciones = ctk.CTkFrame(tab, fg_color="transparent")
        acciones.grid(row=3, column=1, columnspan=2, sticky="w", padx=8, pady=8)
        ctk.CTkButton(acciones, text="Lanzar proceso", command=self._lanzar).pack(side="left")
        ctk.CTkLabel(acciones, text="Puedes lanzar otro mes mientras corre este.", text_color="gray").pack(side="left", padx=12)

        # Panel de procesos: una fila por proceso lanzado
        self.panel = ctk.CTkScrollableFrame(tab, height=170, label_text="Procesos")
        self.panel.grid(row=4, column=0, columnspan=3, sticky="ew", pady=6)
        self._encabezado_panel()

        barra = ctk.CTkFrame(tab, fg_color="transparent")
        barra.grid(row=5, column=0, columnspan=3, sticky="ew")
        self.total = ctk.CTkLabel(barra, text="", anchor="w")
        self.total.pack(side="left")
        ctk.CTkButton(barra, text="Limpiar terminados", width=140, fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), command=self._limpiar_terminados).pack(side="right")

        self.log = ctk.CTkTextbox(tab, height=150)
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=4)
        tab.rowconfigure(6, weight=1)

        botones = ctk.CTkFrame(tab, fg_color="transparent")
        botones.grid(row=7, column=0, columnspan=3, sticky="w")
        ctk.CTkButton(botones, text="Abrir último Excel", command=lambda: self._abrir(self.ultimo_excel)).pack(side="left")
        ctk.CTkButton(botones, text="Abrir carpeta de salida",
                      command=lambda: self._abrir(self.salida.get())).pack(side="left", padx=8)

    def _encabezado_panel(self):
        for c, texto in enumerate(self.COLUMNAS):
            ctk.CTkLabel(self.panel, text=texto, font=ctk.CTkFont(weight="bold")).grid(row=0, column=c, padx=8, sticky="w")

    def _agregar_fila(self, id_proceso, tenant, clave_mes):
        r = id_proceso + 1
        w = {"terminado": False, "widgets": []}
        textos = {"Tenant": tenant, "Mes": clave_mes, "Estado": "⏳ En curso", "Correos": "—", "ZIPs": "—", "Facturas": "—"}
        for c, nombre in enumerate(self.COLUMNAS):
            if nombre == "Avance":
                w[nombre] = ctk.CTkProgressBar(self.panel, width=90)
                w[nombre].set(0)
            elif nombre == "Excel":
                w[nombre] = ctk.CTkButton(self.panel, text="Abrir", width=60, state="disabled")
            else:
                w[nombre] = ctk.CTkLabel(self.panel, text=textos[nombre])
            w[nombre].grid(row=r, column=c, padx=8, pady=2, sticky="w")
            w["widgets"].append(w[nombre])
        self.filas[id_proceso] = w

    def _terminar_fila(self, id_proceso, res):
        fila = self.filas.get(id_proceso)
        if not fila:
            return
        fila["terminado"] = True
        if res.ok:
            r = res.resultado
            fila["Estado"].configure(text="✅ Listo", text_color="#2E9E5B")
            fila["Avance"].set(1)
            fila["Correos"].configure(text=str(r.correos))
            fila["ZIPs"].configure(text=str(r.zips))
            fila["Facturas"].configure(text=str(r.facturas))
            fila["Excel"].configure(state="normal", command=lambda x=r.excel: self._abrir(x))
        else:
            fila["Estado"].configure(text="❌ Error", text_color="#D64545")

    def _limpiar_terminados(self):
        for id_proceso in [i for i, f in self.filas.items() if f["terminado"]]:
            for w in self.filas.pop(id_proceso)["widgets"]:
                w.destroy()
        self._actualizar_total()

    def _actualizar_total(self):
        en_curso = self.lanzador.en_curso
        self.total.configure(text=f"En curso: {en_curso}" if en_curso else "")

    def _elegir_salida(self):
        carpeta = filedialog.askdirectory(initialdir=self.salida.get())
        if carpeta:
            self.salida.delete(0, "end")
            self.salida.insert(0, carpeta)

    def _lanzar(self):
        tenant = self.tenant.get().strip()
        try:
            mes, anio = int(self.mes.get()), int(self.anio.get())
            if not 1 <= mes <= 12:
                raise ValueError
        except ValueError:
            return messagebox.showerror("Datos inválidos", "El mes (1 a 12) y el año deben ser números.")
        if not tenant:
            return messagebox.showerror("Falta el tenant", "Elige o escribe el tenant.")
        set_output_dir(self.salida.get())

        id_proceso, clave_mes = self.n_procesos, f"{mes:02d}/{anio}"
        reporter = ReporterGui(self.cola, id_proceso, f"{tenant} {clave_mes}")
        try:
            self.lanzador.lanzar(tenant, mes, anio, reporter,
                                 al_terminar=lambda r, i=id_proceso: self.cola.put(("fin", (i, r))),
                                 reverificar=bool(self.reverificar.get()))
        except (services.ProcesoDuplicado, services.DemasiadosProcesos) as e:
            return messagebox.showinfo("No se puede lanzar", str(e))
        self.n_procesos += 1
        self._agregar_fila(id_proceso, tenant, clave_mes)
        self._actualizar_total()

    def _leer_cola(self):
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                if tipo == "log":
                    self.log.insert("end", dato + "\n")
                    self.log.see("end")
                elif tipo == "progress":
                    id_proceso, fraccion = dato
                    if id_proceso in self.filas:
                        self.filas[id_proceso]["Avance"].set(fraccion)
                elif tipo == "fin":
                    id_proceso, res = dato
                    self._terminar_fila(id_proceso, res)
                    if res.ok:
                        self.ultimo_excel = res.resultado.excel
                    else:
                        self.log.insert("end", f"[{res.tenant} {res.mes:02d}/{res.anio}] ❌ {res.error}\n")
                        messagebox.showerror(f"Falló {res.tenant} {res.mes:02d}/{res.anio}", res.error)
                    self._actualizar_total()
                elif tipo == "estado":
                    self.c_estado.configure(text=dato)
                    self.tenant.configure(values=services.listar_tenants() or [""])
        except queue.Empty:
            pass
        self.after(100, self._leer_cola)

    def _abrir(self, ruta):
        if ruta and os.path.exists(ruta):
            services.abrir_ruta(ruta)
        else:
            messagebox.showinfo("Aún no existe", "Todavía no hay nada que abrir en esa ruta.")

    # ---------- Correo ----------
    def _tab_correo(self, tab):
        tab.columnconfigure(1, weight=1)
        campos = [("Tenant", "c_tenant", ""), ("Servidor IMAP", "c_imap", "imap.gmail.com"),
                  ("Correo (usuario)", "c_user", "")]
        for i, (etiqueta, attr, valor) in enumerate(campos):
            ctk.CTkLabel(tab, text=etiqueta).grid(row=i, column=0, sticky="w", pady=6)
            e = ctk.CTkEntry(tab)
            e.insert(0, valor)
            e.grid(row=i, column=1, sticky="ew", padx=8)
            setattr(self, attr, e)

        self.modo = ctk.StringVar(value="oauth")
        modos = ctk.CTkFrame(tab, fg_color="transparent")
        modos.grid(row=3, column=1, sticky="w", padx=8, pady=6)
        ctk.CTkRadioButton(modos, text="Google (OAuth2, recomendado)", variable=self.modo, value="oauth").pack(side="left")
        ctk.CTkRadioButton(modos, text="Contraseña de aplicación", variable=self.modo, value="password").pack(side="left", padx=12)

        ctk.CTkLabel(tab, text="Contraseña").grid(row=4, column=0, sticky="w", pady=6)
        self.c_pass = ctk.CTkEntry(tab, show="•")
        self.c_pass.grid(row=4, column=1, sticky="ew", padx=8)

        ctk.CTkLabel(tab, text="client_secret.json").grid(row=5, column=0, sticky="w", pady=6)
        self.c_secret = ctk.CTkEntry(tab)
        self.c_secret.grid(row=5, column=1, sticky="ew", padx=8)
        ctk.CTkButton(tab, text="Elegir…", width=80, command=self._elegir_secret).grid(row=5, column=2)

        ctk.CTkButton(tab, text="Guardar / Vincular", command=self._guardar_correo).grid(row=6, column=1, sticky="w", padx=8, pady=12)
        ctk.CTkButton(tab, text="¿Cómo obtengo el client_secret.json?", fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90"), command=lambda: self.tabs.set("Ayuda")).grid(row=6, column=2, padx=8)
        self.c_estado = ctk.CTkLabel(tab, text="", wraplength=620, justify="left")
        self.c_estado.grid(row=7, column=0, columnspan=3, sticky="w")

    def _elegir_secret(self):
        ruta = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if ruta:
            self.c_secret.delete(0, "end")
            self.c_secret.insert(0, ruta)

    def _guardar_correo(self):
        tenant, imap, user = self.c_tenant.get().strip(), self.c_imap.get().strip(), self.c_user.get().strip()
        if not (tenant and imap and user):
            return messagebox.showerror("Faltan datos", "Tenant, servidor y correo son obligatorios.")
        oauth = self.modo.get() == "oauth"
        secreto, clave = self.c_secret.get().strip(), self.c_pass.get()
        if oauth and not secreto:
            return messagebox.showerror("Falta el archivo", "Elige el client_secret.json descargado de Google Cloud.")
        if not oauth and not clave:
            return messagebox.showerror("Falta la contraseña", "Escribe la contraseña de aplicación.")
        self.c_estado.configure(text="Abriendo el navegador para autorizar…" if oauth else "Guardando…")

        def trabajo():
            try:
                if oauth:
                    ruta = services.guardar_email_oauth(tenant, imap, user, secreto)
                else:
                    ruta = services.guardar_email_password(tenant, imap, user, clave)
                self.cola.put(("estado", f"✅ Guardado en {ruta}"))
            except Exception as e:
                self.cola.put(("estado", f"❌ {e}"))

        threading.Thread(target=trabajo, daemon=True).start()


    # ---------- Ayuda ----------
    def _tab_ayuda(self, tab):
        enlaces = ctk.CTkFrame(tab, fg_color="transparent")
        enlaces.pack(fill="x")
        for texto, url in ENLACES:
            ctk.CTkButton(enlaces, text=texto, command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=(0, 8), pady=(0, 8))
        texto = ctk.CTkTextbox(tab, wrap="word")
        texto.pack(fill="both", expand=True)
        texto.insert("1.0", AYUDA)
        texto.configure(state="disabled")


def autotest() -> str:
    """Comprueba que la ventana y los recursos incluidos funcionan (usado en CI)."""
    from bussines.paths import plantilla_path

    if not ruta_recurso("assets/icon.png").exists():
        raise RuntimeError("Falta el ícono incluido (assets/icon.png)")
    if not plantilla_path("test").exists():
        raise RuntimeError("Falta la plantilla incluida (build/tenant/test/plantilla.json)")
    app = App()
    app.update()
    app.destroy()
    return "OK"


def run():
    ctk.set_appearance_mode("system")
    App().mainloop()
