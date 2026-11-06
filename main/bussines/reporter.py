"""
Canal de salida del núcleo de procesamiento.

La lógica de negocio no imprime ni pregunta: reporta eventos a un Reporter.
La consola usa ConsoleReporter; una interfaz gráfica puede heredar de Reporter
y mostrar los mensajes y el progreso donde corresponda.
"""


# Peso de cada fase en el avance total (0 a 1): descarga de correos y proceso de ZIP.
PESO_FASES = {"descarga": 0.5, "proceso": 0.5}


def fraccion_global(fase: str, actual: int, total: int) -> float:
    """Avance total (0 a 1) a partir del avance dentro de una fase."""
    previo = PESO_FASES["descarga"] if fase == "proceso" else 0.0
    peso = PESO_FASES.get(fase, 1.0)
    return min(1.0, previo + peso * (actual / total if total else 1.0))


class Reporter:
    """Reporter nulo: ignora todo. Base para otros reporters."""

    def info(self, mensaje: str) -> None:
        pass

    def warn(self, mensaje: str) -> None:
        pass

    def error(self, mensaje: str) -> None:
        pass

    def progress(self, actual: int, total: int, mensaje: str = "", fase: str = "") -> None:
        pass


class ConsoleReporter(Reporter):
    """Imprime los eventos en la consola."""

    def info(self, mensaje: str) -> None:
        print(mensaje)

    def warn(self, mensaje: str) -> None:
        print(f"⚠️  {mensaje}")

    def error(self, mensaje: str) -> None:
        print(f"❌ {mensaje}")

    def progress(self, actual: int, total: int, mensaje: str = "", fase: str = "") -> None:
        print(f"[{actual}/{total}] {mensaje}".rstrip())
