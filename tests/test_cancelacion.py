"""Detener un proceso no debe perder datos ni dejar ZIP a medias."""
import sys
import threading
import zipfile
from pathlib import Path

import pytest

MAIN_DIR = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(MAIN_DIR))

from bussines import tcEmail  # noqa: E402
from bussines.cancelacion import ProcesoCancelado, comprobar  # noqa: E402
from bussines.reporter import Reporter, fraccion_global  # noqa: E402
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion  # noqa: E402

PEAJES = MAIN_DIR / "test" / "peajes"


def _preparar(tmp_path, xmls):
    zips = tmp_path / "test" / "zip" / "3_2025"
    zips.mkdir(parents=True)
    for i, xml in enumerate(xmls):
        with zipfile.ZipFile(zips / f"f{i}.zip", "w") as z:
            z.write(PEAJES / xml, xml)
    return zips


class CancelaAlSegundoZip(Reporter):
    """Activa la señal de detención justo después de procesar el primer ZIP."""

    def __init__(self, evento):
        self.evento = evento

    def progress(self, actual, total, mensaje="", fase=""):
        if actual == 1:
            self.evento.set()


def test_comprobar():
    comprobar(None)
    comprobar(threading.Event())
    activa = threading.Event()
    activa.set()
    with pytest.raises(ProcesoCancelado):
        comprobar(activa)


def test_detener_en_medio_no_cierra_zips_ni_genera_excel(tmp_path):
    zips = _preparar(tmp_path, ["ad0900470252000250081eac8.xml", "ad090047025200025008b3ae8.xml"])
    evento = threading.Event()

    with pytest.raises(ProcesoCancelado):
        do_on_start_extract_facturacion("3_2025", "test", CancelaAlSegundoZip(evento), output_dir=tmp_path, cancelar=evento)

    assert sorted(p.name for p in zips.glob("*.zip")) == ["f0.zip", "f1.zip"]   # ninguno se movió
    assert not list((tmp_path / "test" / "closedZip").rglob("*.zip"))
    assert not (tmp_path / "test" / "output").exists()                          # sin Excel parcial


def test_al_relanzar_tras_detener_se_procesa_todo(tmp_path):
    zips = _preparar(tmp_path, ["ad0900470252000250081eac8.xml", "ad090047025200025008b3ae8.xml"])
    evento = threading.Event()
    with pytest.raises(ProcesoCancelado):
        do_on_start_extract_facturacion("3_2025", "test", CancelaAlSegundoZip(evento), output_dir=tmp_path, cancelar=evento)

    res = do_on_start_extract_facturacion("3_2025", "test", Reporter(), output_dir=tmp_path)

    assert (res.zips, res.facturas) == (2, 2)
    assert not list(zips.glob("*.zip"))                                         # ahora sí, cerrados
    assert len(list((tmp_path / "test" / "closedZip" / "3_2025").glob("*.zip"))) == 2


def test_detener_durante_la_descarga_no_deja_zip_a_medias(tmp_path, monkeypatch):
    from email.message import EmailMessage

    class Correo:
        def search(self, *_):
            return "OK", [b"1 2 3"]

        def fetch(self, *_):
            msg = EmailMessage()
            msg["Subject"] = "x"
            msg.set_content("a")
            msg.add_attachment(b"PK", maintype="application", subtype="zip", filename=f"z{self.n}.zip")
            self.n += 1
            return "OK", [(b"1", msg.as_bytes())]

        n = 0

        def logout(self):
            pass

    evento = threading.Event()
    correo = Correo()
    monkeypatch.setattr(tcEmail, "conectar_imap", lambda _c: correo)

    class Detiene(Reporter):
        def progress(self, actual, total, mensaje="", fase=""):
            evento.set()                      # se detiene tras el primer correo

    with pytest.raises(ProcesoCancelado):
        tcEmail.conectar_y_descargar(3, 2025, str(tmp_path / "zip"), str(tmp_path / "closed"), {}, Detiene(), True, evento)

    assert sorted(p.name for p in (tmp_path / "zip").glob("*.zip")) == ["z0.zip"]   # el 1.º completo, no hay más


@pytest.mark.parametrize("fase, actual, total, esperado", [
    ("descarga", 0, 10, 0.0), ("descarga", 10, 10, 0.5), ("descarga", 5, 10, 0.25),
    ("proceso", 0, 4, 0.5), ("proceso", 2, 4, 0.75), ("proceso", 4, 4, 1.0),
    ("proceso", 0, 0, 1.0),
])
def test_porcentaje_global(fase, actual, total, esperado):
    assert fraccion_global(fase, actual, total) == pytest.approx(esperado)
