"""Pruebas del núcleo sin entrada/salida: descarga IMAP simulada y generación de Excel."""
import sys
import zipfile
from email.message import EmailMessage
from pathlib import Path

from openpyxl import load_workbook

MAIN_DIR = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(MAIN_DIR))

from bussines import tcEmail  # noqa: E402
from bussines.reporter import Reporter  # noqa: E402
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion  # noqa: E402

XML_MUESTRA = MAIN_DIR / "test" / "peajes" / "ad0900470252000250081eac8.xml"


class EventosReporter(Reporter):
    def __init__(self):
        self.eventos = []

    def info(self, mensaje):
        self.eventos.append(("info", mensaje))

    def error(self, mensaje):
        self.eventos.append(("error", mensaje))

    def progress(self, actual, total, mensaje=""):
        self.eventos.append(("progress", actual, total))


class FakeMail:
    """IMAP mínimo: un correo con un ZIP adjunto."""

    def __init__(self, zip_bytes, nombre="facturas.zip"):
        msg = EmailMessage()
        msg["Subject"] = "Facturas del mes"
        msg.set_content("adjunto")
        msg.add_attachment(zip_bytes, maintype="application", subtype="zip", filename=nombre)
        self.raw = msg.as_bytes()
        self.logout_llamado = False

    def search(self, *_):
        return "OK", [b"1"]

    def fetch(self, *_):
        return "OK", [(b"1", self.raw)]

    def logout(self):
        self.logout_llamado = True


def _zip_con_xml(destino: Path) -> bytes:
    with zipfile.ZipFile(destino, "w") as z:
        z.write(XML_MUESTRA, XML_MUESTRA.name)
    return destino.read_bytes()


def test_descarga_guarda_zip_y_reporta(tmp_path, monkeypatch):
    fake = FakeMail(_zip_con_xml(tmp_path / "origen.zip"))
    monkeypatch.setattr(tcEmail, "conectar_imap", lambda _cfg: fake)
    reporter = EventosReporter()

    res = tcEmail.conectar_y_descargar(3, 2025, str(tmp_path / "zip"), str(tmp_path / "closed"), {}, reporter)

    assert (res.correos, res.descargados, res.total_zips) == (1, 1, 1)
    assert (tmp_path / "zip" / "facturas.zip").exists()
    assert fake.logout_llamado
    assert ("progress", 1, 1) in reporter.eventos


def test_no_conecta_si_ya_hay_zips_y_no_se_verifica(tmp_path, monkeypatch):
    (tmp_path / "zip").mkdir()
    (tmp_path / "zip" / "viejo.zip").write_bytes(b"x")

    def no_debe_conectar(_cfg):
        raise AssertionError("no debería conectarse")

    monkeypatch.setattr(tcEmail, "conectar_imap", no_debe_conectar)
    res = tcEmail.conectar_y_descargar(3, 2025, str(tmp_path / "zip"), str(tmp_path / "closed"), {}, verificar=False)

    assert res.total_zips == 1 and res.descargados == 0


def test_extraccion_genera_excel_con_filas(tmp_path):
    zips = tmp_path / "test" / "zip" / "3_2025"
    zips.mkdir(parents=True)
    _zip_con_xml(zips / "facturas.zip")

    res = do_on_start_extract_facturacion("3_2025", "test", Reporter(), output_dir=tmp_path)

    assert (res.zips, res.facturas) == (1, 1)
    assert not (zips / "facturas.zip").exists()  # movido a closedZip
    libro = load_workbook(res.excel)
    filas_de_datos = sum(hoja.max_row - 1 for hoja in libro.worksheets)  # sin la cabecera
    assert filas_de_datos == 1
