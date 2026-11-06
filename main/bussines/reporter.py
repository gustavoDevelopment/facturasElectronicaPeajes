"""
Canal de salida del núcleo de procesamiento.

La lógica de negocio no imprime ni pregunta: reporta eventos a un Reporter.
La consola usa ConsoleReporter; una interfaz gráfica puede heredar de Reporter
y mostrar los mensajes y el progreso donde corresponda.
"""


class Reporter:
    """Reporter nulo: ignora todo. Base para otros reporters."""

    def info(self, mensaje: str) -> None:
        pass

    def warn(self, mensaje: str) -> None:
        pass

    def error(self, mensaje: str) -> None:
        pass

    def progress(self, actual: int, total: int, mensaje: str = "") -> None:
        pass


class ConsoleReporter(Reporter):
    """Imprime los eventos en la consola."""

    def info(self, mensaje: str) -> None:
        print(mensaje)

    def warn(self, mensaje: str) -> None:
        print(f"⚠️  {mensaje}")

    def error(self, mensaje: str) -> None:
        print(f"❌ {mensaje}")

    def progress(self, actual: int, total: int, mensaje: str = "") -> None:
        print(f"[{actual}/{total}] {mensaje}".rstrip())
