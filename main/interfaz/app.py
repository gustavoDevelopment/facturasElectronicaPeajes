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
from interfaz import empresas, services
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
        self._tab_empresas(self.tabs.add("Empresas"))
        self._tab_correo(self.tabs.add("Correo"))
        self._tab_ayuda(self.tabs.add("Ayuda"))
        self._refrescar_empresas()
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
        self.tenant = ctk.CTkComboBox(tab, values=[""], state="readonly")
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
                    self._refrescar_empresas()
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


    # ---------- Empresas ----------
    def _tab_empresas(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)
        self.empresa_sel = ctk.StringVar()
        acciones = ctk.CTkFrame(tab, fg_color="transparent")
        acciones.grid(row=0, column=0, sticky="w", pady=(0, 8))
        for texto, comando in (("Agregar", lambda: self._dialogo_empresa()),
                               ("Editar", self._editar_empresa),
                               ("Eliminar", self._eliminar_empresa),
                               ("Configurar correo", self._configurar_correo)):
            ctk.CTkButton(acciones, text=texto, width=120, command=comando).pack(side="left", padx=(0, 8))
        self.lista = ctk.CTkScrollableFrame(tab, label_text="Empresas")
        self.lista.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(tab, text="El nombre identifica a la empresa (carpetas, correo y plantilla), por eso no se puede cambiar.",
                     text_color="gray").grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _refrescar_empresas(self):
        lista = empresas.listar_empresas()
        for w in self.lista.winfo_children():
            w.destroy()
        for c, texto in enumerate(("Empresa", "Almacenamiento", "Correo", "Plantilla")):
            ctk.CTkLabel(self.lista, text=texto, font=ctk.CTkFont(weight="bold")).grid(row=0, column=c, padx=10, sticky="w")
        for r, e in enumerate(lista, start=1):
            ctk.CTkRadioButton(self.lista, text=e["name"], variable=self.empresa_sel, value=e["name"]).grid(row=r, column=0, padx=10, pady=3, sticky="w")
            ctk.CTkLabel(self.lista, text=empresas.ALMACENAMIENTOS.get(e["storage"], "—")).grid(row=r, column=1, padx=10, sticky="w")
            ctk.CTkLabel(self.lista, text="✅ Configurado" if e["tiene_correo"] else "— Pendiente").grid(row=r, column=2, padx=10, sticky="w")
            ctk.CTkLabel(self.lista, text="✅ Lista" if e["tiene_plantilla"] else "— Falta").grid(row=r, column=3, padx=10, sticky="w")
        nombres = [e["name"] for e in lista]
        self.tenant.configure(values=nombres or [""])
        if self.tenant.get() not in nombres:
            self.tenant.set(nombres[0] if nombres else "")
        if self.empresa_sel.get() not in nombres:
            self.empresa_sel.set("")

    def _seleccionada(self):
        nombre = self.empresa_sel.get()
        if not nombre:
            messagebox.showinfo("Elige una empresa", "Selecciona una empresa de la lista.")
        return nombre

    def _editar_empresa(self):
        nombre = self._seleccionada()
        if nombre:
            self._dialogo_empresa(next(e for e in empresas.listar_empresas() if e["name"] == nombre))

    def _eliminar_empresa(self):
        nombre = self._seleccionada()
        if not nombre or not messagebox.askyesno(
                "Eliminar empresa",
                f"¿Eliminar '{nombre}'?\n\nSe quita de la lista y se borra su plantilla. Los ZIP, vouchers y Excel "
                "ya generados no se tocan."):
            return
        borrar = messagebox.askyesno("Credenciales de correo",
                                     f"¿Borrar también las credenciales de correo de '{nombre}' (email y token)?")
        empresas.eliminar_empresa(nombre, borrar_credenciales=borrar)
        self._refrescar_empresas()

    def _configurar_correo(self):
        nombre = self._seleccionada()
        if not nombre:
            return
        self.c_tenant.delete(0, "end")
        self.c_tenant.insert(0, nombre)
        try:  # rellena servidor y usuario si ya estaban guardados (nunca la contraseña)
            actual = services.cargar_email(nombre)
            for campo, clave in ((self.c_imap, "imap_server"), (self.c_user, "user")):
                if actual.get(clave):
                    campo.delete(0, "end")
                    campo.insert(0, actual[clave])
        except services.ConfiguracionIncompleta:
            pass
        self.tabs.set("Correo")

    def _dialogo_empresa(self, existente=None):
        d = ctk.CTkToplevel(self)
        d.title("Editar empresa" if existente else "Agregar empresa")
        d.geometry("470x430")
        d.transient(self)
        d.after(200, d.grab_set)
        d.columnconfigure(1, weight=1)

        ctk.CTkLabel(d, text="Nombre").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        nombre = ctk.CTkEntry(d)
        nombre.grid(row=0, column=1, padx=12, sticky="ew")
        ctk.CTkLabel(d, text="Almacenamiento").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        sin_definir = "(sin definir)"
        almacen = ctk.CTkComboBox(d, values=[sin_definir, *empresas.ALMACENAMIENTOS.values()], state="readonly")
        almacen.grid(row=1, column=1, padx=12, sticky="ew")
        ctk.CTkLabel(d, text="Correo de la empresa").grid(row=2, column=0, padx=12, pady=8, sticky="w")
        correo = ctk.CTkEntry(d, placeholder_text="opcional")
        correo.grid(row=2, column=1, padx=12, sticky="ew")

        modo, archivo = ctk.StringVar(value="luego"), {"ruta": ""}
        origen = ctk.CTkComboBox(d, values=[e["name"] for e in empresas.listar_empresas() if e["tiene_plantilla"]] or [""],
                                 state="readonly")
        etiqueta_archivo = ctk.CTkLabel(d, text="", text_color="gray", wraplength=300, justify="left")

        def elegir_archivo():
            ruta = filedialog.askopenfilename(parent=d, filetypes=[("JSON", "*.json")])
            if ruta:
                archivo["ruta"] = ruta
                etiqueta_archivo.configure(text=ruta)
                modo.set("archivo")

        if existente:
            nombre.insert(0, existente["name"])
            nombre.configure(state="disabled")
            almacen.set(empresas.ALMACENAMIENTOS.get(existente["storage"], sin_definir))
            correo.insert(0, existente["email_template"])
        else:
            ctk.CTkLabel(d, text="Plantilla de Excel", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, columnspan=2, padx=12, pady=(16, 4), sticky="w")
            ctk.CTkRadioButton(d, text="Copiar de otra empresa", variable=modo, value="copiar").grid(row=4, column=0, padx=12, pady=4, sticky="w")
            origen.grid(row=4, column=1, padx=12, sticky="ew")
            ctk.CTkRadioButton(d, text="Importar archivo", variable=modo, value="archivo").grid(row=5, column=0, padx=12, pady=4, sticky="w")
            ctk.CTkButton(d, text="Elegir archivo…", command=elegir_archivo).grid(row=5, column=1, padx=12, sticky="w")
            etiqueta_archivo.grid(row=6, column=1, padx=12, sticky="w")
            ctk.CTkRadioButton(d, text="Más tarde", variable=modo, value="luego").grid(row=7, column=0, padx=12, pady=4, sticky="w")

        def guardar():
            clave = next((k for k, v in empresas.ALMACENAMIENTOS.items() if v == almacen.get()), "")
            try:
                if existente:
                    empresas.editar_empresa(existente["name"], clave, correo.get())
                else:
                    copiar = origen.get() if modo.get() == "copiar" else None
                    importar = archivo["ruta"] if modo.get() == "archivo" else None
                    if modo.get() == "copiar" and not copiar:
                        raise empresas.EmpresaError("No hay otra empresa con plantilla para copiar.")
                    if modo.get() == "archivo" and not importar:
                        raise empresas.EmpresaError("Elige el archivo de plantilla.")
                    empresas.crear_empresa(nombre.get(), clave, correo.get(), copiar, importar)
            except empresas.EmpresaError as e:
                return messagebox.showerror("No se pudo guardar", str(e), parent=d)
            d.destroy()
            self._refrescar_empresas()

        ctk.CTkButton(d, text="Guardar", command=guardar).grid(row=8, column=1, padx=12, pady=20, sticky="e")

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
