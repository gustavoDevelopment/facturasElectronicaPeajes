"""Procesamiento de varios meses a la vez."""
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "main"))

from interfaz import services  # noqa: E402
from interfaz.services import ResumenProceso, ejecutar_varios, rango_meses  # noqa: E402


def test_rango_cruza_de_anio():
    assert rango_meses((11, 2025), (2, 2026)) == [(11, 2025), (12, 2025), (1, 2026), (2, 2026)]


def test_rango_de_un_solo_mes():
    assert rango_meses((3, 2026), (3, 2026)) == [(3, 2026)]


@pytest.mark.parametrize("desde, hasta, texto", [
    ((5, 2026), (4, 2026), "anterior"),
    ((13, 2026), (13, 2026), "entre 1 y 12"),
    ((1, 2024), (1, 2026), "Máximo"),
])
def test_rango_invalido(desde, hasta, texto):
    with pytest.raises(ValueError, match=texto):
        rango_meses(desde, hasta)


@pytest.fixture
def sin_correo(monkeypatch):
    monkeypatch.setattr(services, "cargar_email", lambda t: {})
    monkeypatch.setattr(services, "plantilla_path", lambda t: None)


def test_los_meses_corren_a_la_vez(sin_correo, monkeypatch):
    # La barrera solo se abre si 3 meses están ejecutándose al mismo tiempo
    barrera = threading.Barrier(3, timeout=5)

    def falso(tenant, mes, anio, reporter, reverificar):
        barrera.wait()
        return ResumenProceso(facturas=mes)

    monkeypatch.setattr(services, "ejecutar_proceso", falso)
    resultados = ejecutar_varios("t", [(1, 2026), (2, 2026), (3, 2026)], lambda c: None, simultaneos=3)

    assert [r.ok for r in resultados] == [True, True, True]
    assert [r.resultado.facturas for r in resultados] == [1, 2, 3]  # en el orden pedido


def test_un_mes_con_error_no_detiene_a_los_demas(sin_correo, monkeypatch):
    def falso(tenant, mes, anio, reporter, reverificar):
        if mes == 2:
            raise RuntimeError("sin correos")
        return ResumenProceso(facturas=10)

    monkeypatch.setattr(services, "ejecutar_proceso", falso)
    terminados = []
    resultados = ejecutar_varios("t", [(1, 2026), (2, 2026), (3, 2026)], lambda c: None,
                                 simultaneos=1, al_terminar=terminados.append)

    assert [r.ok for r in resultados] == [True, False, True]
    assert resultados[1].error == "sin correos"
    assert len(terminados) == 3


def test_cada_mes_recibe_su_propio_reporter(sin_correo, monkeypatch):
    usados = {}
    monkeypatch.setattr(services, "ejecutar_proceso",
                        lambda t, m, a, rep, rv: usados.setdefault(f"{m:02d}/{a}", rep) and ResumenProceso())
    ejecutar_varios("t", [(1, 2026), (12, 2025)], lambda clave: f"reporter-{clave}", simultaneos=2)

    assert usados == {"01/2026": "reporter-01/2026", "12/2025": "reporter-12/2025"}


def test_sin_correo_configurado_falla_antes_de_empezar(monkeypatch):
    monkeypatch.setattr(services, "cargar_email", lambda t: (_ for _ in ()).throw(services.ConfiguracionIncompleta("falta")))
    with pytest.raises(services.ConfiguracionIncompleta):
        ejecutar_varios("t", [(1, 2026)], lambda c: None)
