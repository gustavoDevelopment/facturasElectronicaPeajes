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
    """Envía los eventos del hilo de trabajo a la ventana mediante una cola."""

    def __init__(self, cola: queue.Queue):
        self.cola = cola

    def info(self, mensaje):
        self.cola.put(("log", mensaje))

    def warn(self, mensaje):
        self.cola.put(("log", f"⚠️ {mensaje}"))

    def error(self, mensaje):
        self.cola.put(("log", f"❌ {mensaje}"))

    def progress(self, actual, total, mensaje=""):
        self.cola.put(("progress", actual / total if total else 0))
        if mensaje:
            self.cola.put(("log", f"[{actual}/{total}] {mensaje}"))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Facturae Optimus")
        self.geometry("760x640")
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

        ctk.CTkLabel(tab, text="Tenant").grid(row=0, column=0, sticky="w", pady=6)
        self.tenant = ctk.CTkComboBox(tab, values=services.listar_tenants() or [""])
        self.tenant.grid(row=0, column=1, sticky="ew", padx=8)

        ctk.CTkLabel(tab, text="Mes / Año").grid(row=1, column=0, sticky="w", pady=6)
        fila = ctk.CTkFrame(tab, fg_color="transparent")
        fila.grid(row=1, column=1, sticky="w", padx=8)
        self.mes = ctk.CTkComboBox(fila, values=MESES, width=70)
        self.mes.set(str(mes))
        self.mes.pack(side="left")
        self.anio = ctk.CTkEntry(fila, width=80)
        self.anio.insert(0, str(anio))
        self.anio.pack(side="left", padx=8)

        ctk.CTkLabel(tab, text="Carpeta de salida").grid(row=2, column=0, sticky="w", pady=6)
        self.salida = ctk.CTkEntry(tab)
        self.salida.insert(0, str(get_output_dir()))
        self.salida.grid(row=2, column=1, sticky="ew", padx=8)
        ctk.CTkButton(tab, text="Elegir…", width=80, command=self._elegir_salida).grid(row=2, column=2)

        self.reverificar = ctk.CTkCheckBox(tab, text="Verificar y descargar faltantes aunque ya haya ZIPs")
        self.reverificar.select()
        self.reverificar.grid(row=3, column=1, sticky="w", padx=8, pady=6)

        self.boton = ctk.CTkButton(tab, text="Descargar y procesar", command=self._procesar)
        self.boton.grid(row=4, column=1, sticky="w", padx=8, pady=8)

        self.barra = ctk.CTkProgressBar(tab)
        self.barra.set(0)
        self.barra.grid(row=5, column=0, columnspan=3, sticky="ew", pady=4)

        self.log = ctk.CTkTextbox(tab, height=260)
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=4)
        tab.rowconfigure(6, weight=1)

        botones = ctk.CTkFrame(tab, fg_color="transparent")
        botones.grid(row=7, column=0, columnspan=3, sticky="w")
        ctk.CTkButton(botones, text="Abrir Excel", command=lambda: self._abrir(self.ultimo_excel)).pack(side="left")
        ctk.CTkButton(botones, text="Abrir carpeta de salida",
                      command=lambda: self._abrir(self.salida.get())).pack(side="left", padx=8)

    def _elegir_salida(self):
        carpeta = filedialog.askdirectory(initialdir=self.salida.get())
        if carpeta:
            self.salida.delete(0, "end")
            self.salida.insert(0, carpeta)

    def _procesar(self):
        try:
            tenant, mes, anio = self.tenant.get().strip(), int(self.mes.get()), int(self.anio.get())
        except ValueError:
            return messagebox.showerror("Datos inválidos", "El mes y el año deben ser números.")
        if not tenant:
            return messagebox.showerror("Falta el tenant", "Elige o escribe el tenant.")
        set_output_dir(self.salida.get())
        reverificar = bool(self.reverificar.get())
        self.boton.configure(state="disabled")
        self.barra.set(0)
        self.log.delete("1.0", "end")

        def trabajo():
            try:
                res = services.ejecutar_proceso(tenant, mes, anio, ReporterGui(self.cola), reverificar)
                self.cola.put(("fin", res))
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
                elif tipo == "progress":
                    self.barra.set(dato)
                elif tipo == "fin":
                    self.ultimo_excel = dato.excel
                    self.barra.set(1)
                    self.boton.configure(state="normal")
                    self.log.insert("end", f"\n✅ Listo: {dato.facturas} facturas en {dato.zips} ZIP.\n{dato.excel}\n")
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
