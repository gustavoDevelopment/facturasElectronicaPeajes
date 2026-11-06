"""Lanzar procesos independientes (uno por tenant y mes) mientras otros siguen corriendo."""
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "main"))

from interfaz import services  # noqa: E402
from interfaz.services import DemasiadosProcesos, Lanzador, ProcesoDuplicado, ResumenProceso  # noqa: E402


class Recolector:
    """Guarda los resultados y permite esperar a que lleguen n."""

    def __init__(self):
        self.resultados, self._n, self._evento = [], 0, threading.Event()

    def esperar(self, n, timeout=5):
        self._n = n
        self._evento.clear()
        if len(self.resultados) >= n:
            self._evento.set()
        assert self._evento.wait(timeout), f"solo terminaron {len(self.resultados)} de {n}"

    def __call__(self, resultado):
        self.resultados.append(resultado)
        if self._n and len(self.resultados) >= self._n:
            self._evento.set()


def test_se_puede_lanzar_otro_mes_mientras_el_primero_corre(monkeypatch):
    primero_corriendo, soltar = threading.Event(), threading.Event()

    def falso(tenant, mes, anio, reporter, reverificar):
        if mes == 1:
            primero_corriendo.set()
            assert soltar.wait(5)       # el mes 1 sigue "corriendo"
        return ResumenProceso(facturas=mes)

    monkeypatch.setattr(services, "ejecutar_proceso", falso)
    lanzador, fin = Lanzador(), Recolector()

    lanzador.lanzar("t", 1, 2026, None, fin)
    assert primero_corriendo.wait(5)
    lanzador.lanzar("t", 2, 2026, None, fin)      # se lanza con el primero aún en curso
    fin.esperar(1)                                 # el mes 2 termina primero...
    assert fin.resultados[0].mes == 2
    assert lanzador.en_curso == 1                  # ...mientras el mes 1 sigue corriendo
    soltar.set()
    fin.esperar(2)

    assert sorted(r.resultado.facturas for r in fin.resultados) == [1, 2]
    assert lanzador.en_curso == 0


def test_no_deja_lanzar_el_mismo_tenant_y_mes_dos_veces(monkeypatch):
    soltar = threading.Event()
    monkeypatch.setattr(services, "ejecutar_proceso", lambda *a: soltar.wait(5) and ResumenProceso())
    lanzador, fin = Lanzador(), Recolector()

    lanzador.lanzar("t", 1, 2026, None, fin)
    with pytest.raises(ProcesoDuplicado):
        lanzador.lanzar("t", 1, 2026, None, fin)
    lanzador.lanzar("otro", 1, 2026, None, fin)    # otro tenant, mismo mes: permitido
    soltar.set()
    fin.esperar(2)


def test_limite_de_procesos_simultaneos(monkeypatch):
    soltar = threading.Event()
    monkeypatch.setattr(services, "ejecutar_proceso", lambda *a: soltar.wait(5) and ResumenProceso())
    lanzador, fin = Lanzador(max_simultaneos=2), Recolector()

    lanzador.lanzar("t", 1, 2026, None, fin)
    lanzador.lanzar("t", 2, 2026, None, fin)
    with pytest.raises(DemasiadosProcesos):
        lanzador.lanzar("t", 3, 2026, None, fin)
    soltar.set()
    fin.esperar(2)


def test_un_proceso_con_error_no_afecta_a_otro_y_se_puede_relanzar(monkeypatch):
    def falso(tenant, mes, anio, reporter, reverificar):
        if mes == 2:
            raise RuntimeError("sin correos")
        return ResumenProceso(facturas=10)

    monkeypatch.setattr(services, "ejecutar_proceso", falso)
    lanzador, fin = Lanzador(), Recolector()

    lanzador.lanzar("t", 1, 2026, None, fin)
    lanzador.lanzar("t", 2, 2026, None, fin)
    fin.esperar(2)
    por_mes = {r.mes: r for r in fin.resultados}

    assert por_mes[1].ok and not por_mes[2].ok and por_mes[2].error == "sin correos"
    assert por_mes[2].tenant == "t"
    lanzador.lanzar("t", 2, 2026, None, fin)       # tras terminar, el mismo mes se puede relanzar
    fin.esperar(3)
