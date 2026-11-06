"""Ventana principal (CustomTkinter): procesar facturas y configurar el correo."""
import os
import queue
import threading
import webbrowser
from tkinter import filedialog, messagebox

import customtkinter as ctk

from bussines.reporter import Reporter
from interfaz import services
from interfaz.ayuda import AYUDA, ENLACES
from settings import get_output_dir, set_output_dir

MESES = [str(m) for m in range(1, 13)]


class ReporterGui(Reporter):
    """Envía los eventos de un mes a la ventana mediante una cola (con su etiqueta)."""

    def __init__(self, cola: queue.Queue, clave: str = ""):
        self.cola = cola
        self.clave = clave

    def _linea(self, mensaje):
        return f"[{self.clave}] {mensaje}" if self.clave else mensaje

    def info(self, mensaje):
        self.cola.put(("log", self._linea(mensaje)))

    def warn(self, mensaje):
        self.cola.put(("log", self._linea(f"⚠️ {mensaje}")))

    def error(self, mensaje):
        self.cola.put(("log", self._linea(f"❌ {mensaje}")))

    def progress(self, actual, total, mensaje=""):
        self.cola.put(("progress", (self.clave, actual / total if total else 0)))
        if mensaje:
            self.cola.put(("log", self._linea(f"[{actual}/{total}] {mensaje}")))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Facturae Optimus")
        self.geometry("860x780")
        self.cola = queue.Queue()
        self.ultimo_excel = ""

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=12)
        self._tab_procesar(self.tabs.add("Procesar"))
        self._tab_correo(self.tabs.add("Correo"))
        self._tab_ayuda(self.tabs.add("Ayuda"))
        self.after(100, self._leer_cola)

    # ---------- Procesar ----------
    def _tab_procesar(self, tab):
        tab.columnconfigure(1, weight=1)
        mes, anio = services.mes_anterior()

        ctk.CTkLabel(tab, text="Tenant").grid(row=0, column=0, sticky="w", pady=4)
        self.tenant = ctk.CTkComboBox(tab, values=services.listar_tenants() or [""])
        self.tenant.grid(row=0, column=1, columnspan=2, sticky="ew", padx=8)

        self.desde_mes, self.desde_anio = self._selector_mes(tab, 1, "Desde (mes / año)", mes, anio)
        self.hasta_mes, self.hasta_anio = self._selector_mes(tab, 2, "Hasta (mes / año)", mes, anio)

        ctk.CTkLabel(tab, text="Procesos simultáneos").grid(row=3, column=0, sticky="w", pady=4)
        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.grid(row=3, column=1, columnspan=2, sticky="w", padx=8)
        self.simultaneos = ctk.CTkComboBox(fila, values=["1", "2", "3", "4"], width=70)
        self.simultaneos.set("3")
        self.simultaneos.pack(side="left")
        self.reverificar = ctk.CTkCheckBox(fila, text="Verificar y descargar faltantes aunque ya haya ZIPs")
        self.reverificar.select()
        self.reverificar.pack(side="left", padx=16)

        ctk.CTkLabel(tab, text="Carpeta de salida").grid(row=4, column=0, sticky="w", pady=4)
        self.salida = ctk.CTkEntry(tab)
        self.salida.insert(0, str(get_output_dir()))
        self.salida.grid(row=4, column=1, sticky="ew", padx=8)
        ctk.CTkButton(tab, text="Elegir…", width=80, command=self._elegir_salida).grid(row=4, column=2)

        self.boton = ctk.CTkButton(tab, text="Descargar y procesar", command=self._procesar)
        self.boton.grid(row=5, column=1, sticky="w", padx=8, pady=8)

        self.barra = ctk.CTkProgressBar(tab)
        self.barra.set(0)
        self.barra.grid(row=6, column=0, columnspan=3, sticky="ew", pady=2)

        # Panel de resumen: una fila por mes
        self.panel = ctk.CTkScrollableFrame(tab, height=130, label_text="Resumen")
        self.panel.grid(row=7, column=0, columnspan=3, sticky="ew", pady=6)
        self.filas = {}
        self._encabezado_panel()
        self.total = ctk.CTkLabel(tab, text="", anchor="w")
        self.total.grid(row=8, column=0, columnspan=3, sticky="w")

        self.log = ctk.CTkTextbox(tab, height=170)
        self.log.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=4)
        tab.rowconfigure(9, weight=1)

        botones = ctk.CTkFrame(tab, fg_color="transparent")
        botones.grid(row=10, column=0, columnspan=3, sticky="w")
        ctk.CTkButton(botones, text="Abrir último Excel", command=lambda: self._abrir(self.ultimo_excel)).pack(side="left")
        ctk.CTkButton(botones, text="Abrir carpeta de salida",
                      command=lambda: self._abrir(self.salida.get())).pack(side="left", padx=8)

    def _selector_mes(self, tab, fila, etiqueta, mes, anio):
        ctk.CTkLabel(tab, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=4)
        marco = ctk.CTkFrame(tab, fg_color="transparent")
        marco.grid(row=fila, column=1, columnspan=2, sticky="w", padx=8)
        combo = ctk.CTkComboBox(marco, values=MESES, width=70)
        combo.set(str(mes))
        combo.pack(side="left")
        entrada = ctk.CTkEntry(marco, width=80)
        entrada.insert(0, str(anio))
        entrada.pack(side="left", padx=8)
        return combo, entrada

    COLUMNAS = ("Mes", "Estado", "Correos", "ZIPs", "Facturas", "Excel")

    def _encabezado_panel(self):
        for c, texto in enumerate(self.COLUMNAS):
            ctk.CTkLabel(self.panel, text=texto, font=ctk.CTkFont(weight="bold")).grid(row=0, column=c, padx=8, sticky="w")

    def _limpiar_panel(self):
        for w in self.panel.winfo_children():
            w.destroy()
        self.filas = {}
        self._encabezado_panel()
        self.total.configure(text="")

    def _agregar_fila(self, clave):
        r = len(self.filas) + 1
        etiquetas = {}
        for c, nombre in enumerate(self.COLUMNAS[:-1]):
            etiquetas[nombre] = ctk.CTkLabel(self.panel, text=clave if nombre == "Mes" else ("En cola" if nombre == "Estado" else "—"))
            etiquetas[nombre].grid(row=r, column=c, padx=8, sticky="w")
        etiquetas["Excel"] = ctk.CTkButton(self.panel, text="Abrir", width=60, state="disabled")
        etiquetas["Excel"].grid(row=r, column=5, padx=8)
        self.filas[clave] = etiquetas

    def _actualizar_fila(self, res):
        fila = self.filas.get(f"{res.mes:02d}/{res.anio}")
        if not fila:
            return
        if res.ok:
            r = res.resultado
            fila["Estado"].configure(text="✅ Listo", text_color="#2E9E5B")
            fila["Correos"].configure(text=str(r.correos))
            fila["ZIPs"].configure(text=str(r.zips))
            fila["Facturas"].configure(text=str(r.facturas))
            fila["Excel"].configure(state="normal", command=lambda x=r.excel: self._abrir(x))
        else:
            fila["Estado"].configure(text="❌ Error", text_color="#D64545")

    def _elegir_salida(self):
        carpeta = filedialog.askdirectory(initialdir=self.salida.get())
        if carpeta:
            self.salida.delete(0, "end")
            self.salida.insert(0, carpeta)

    def _procesar(self):
        try:
            tenant = self.tenant.get().strip()
            meses = services.rango_meses(
                (int(self.desde_mes.get()), int(self.desde_anio.get())),
                (int(self.hasta_mes.get()), int(self.hasta_anio.get())))
            simultaneos = int(self.simultaneos.get())
        except ValueError as e:
            return messagebox.showerror("Datos inválidos", str(e) if "mes" in str(e).lower() else "Mes, año y procesos deben ser números.")
        if not tenant:
            return messagebox.showerror("Falta el tenant", "Elige o escribe el tenant.")
        set_output_dir(self.salida.get())
        reverificar = bool(self.reverificar.get())
        self.boton.configure(state="disabled")
        self.barra.set(0)
        self.log.delete("1.0", "end")
        self._limpiar_panel()
        self.fracciones = {f"{m:02d}/{a}": 0.0 for m, a in meses}
        self.resultados = []
        for clave in self.fracciones:
            self._agregar_fila(clave)

        def crear_reporter(clave):
            self.cola.put(("inicio", clave))
            return ReporterGui(self.cola, clave)

        def trabajo():
            try:
                services.ejecutar_varios(tenant, meses, crear_reporter, reverificar, simultaneos,
                                         al_terminar=lambda r: self.cola.put(("mes_fin", r)))
                self.cola.put(("todo_fin", None))
            except Exception as e:  # se muestra en la ventana, no se pierde en la consola
                self.cola.put(("error", str(e)))

        threading.Thread(target=trabajo, daemon=True).start()

    def _leer_cola(self):
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                if tipo == "log":
                    self.log.insert("end", dato + "\n")
                    self.log.see("end")
                elif tipo == "inicio":
                    if dato in self.filas:
                        self.filas[dato]["Estado"].configure(text="⏳ En curso")
                elif tipo == "progress":
                    clave, fraccion = dato
                    self.fracciones[clave] = fraccion
                    self.barra.set(sum(self.fracciones.values()) / len(self.fracciones))
                elif tipo == "mes_fin":
                    self.resultados.append(dato)
                    self.fracciones[f"{dato.mes:02d}/{dato.anio}"] = 1.0
                    self.barra.set(sum(self.fracciones.values()) / len(self.fracciones))
                    self._actualizar_fila(dato)
                    if dato.ok:
                        self.ultimo_excel = dato.resultado.excel
                    else:
                        self.log.insert("end", f"[{dato.mes:02d}/{dato.anio}] ❌ {dato.error}\n")
                elif tipo == "todo_fin":
                    self.boton.configure(state="normal")
                    ok = [r for r in self.resultados if r.ok]
                    fallidos = [r for r in self.resultados if not r.ok]
                    facturas = sum(r.resultado.facturas for r in ok)
                    self.total.configure(text=f"Total: {facturas} facturas en {len(ok)} de {len(self.resultados)} meses")
                    if fallidos:
                        detalle = "\n".join(f"{r.mes:02d}/{r.anio}: {r.error}" for r in fallidos)
                        messagebox.showerror("Algunos meses fallaron", detalle)
                elif tipo == "estado":
                    self.c_estado.configure(text=dato)
                    self.tenant.configure(values=services.listar_tenants() or [""])
                elif tipo == "error":
                    self.boton.configure(state="normal")
                    self.log.insert("end", f"\n❌ {dato}\n")
                    messagebox.showerror("No se pudo completar", dato)
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

    if not plantilla_path("test").exists():
        raise RuntimeError("Falta la plantilla incluida (build/tenant/test/plantilla.json)")
    app = App()
    app.update()
    app.destroy()
    return "OK"


def run():
    ctk.set_appearance_mode("system")
    App().mainloop()
