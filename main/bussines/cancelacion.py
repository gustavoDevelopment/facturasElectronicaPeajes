"""Cancelación cooperativa: el núcleo revisa la señal en puntos seguros."""


class ProcesoCancelado(Exception):
    """El usuario detuvo el proceso."""


def comprobar(cancelar) -> None:
    """Lanza ProcesoCancelado si `cancelar` (un threading.Event) está activado."""
    if cancelar is not None and cancelar.is_set():
        raise ProcesoCancelado("Proceso detenido por el usuario.")
