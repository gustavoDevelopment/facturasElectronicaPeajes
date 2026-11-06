"""Pruebas de extracción de datos de facturas de peajes (main/bussines)."""
import sys
from pathlib import Path

import pytest

MAIN_DIR = Path(__file__).parent.parent / "main"
sys.path.insert(0, str(MAIN_DIR))

from bussines.tcProcesFacturacion import extraer_datos_factura  # noqa: E402

PEAJES = MAIN_DIR / "test" / "peajes"


@pytest.mark.parametrize(
    "xml, peaje, placa",
    [
        ("ad0900470252000250081eac8.xml", "PEAJE TEBAIDA", "TLZ455"),
        ("ad090047025200025008b3ae8.xml", "PEAJE ALBARRACIN", "VAK142"),
        ("ad090047025200025008b3bb8.xml", "PEAJE ROBLE", "SPX932"),
        ("ad090047025200025008b3f11.xml", "PEAJE ANDES", "VAK142"),
    ],
)
def test_extrae_peaje_y_placa(xml, peaje, placa):
    _, fila = extraer_datos_factura(str(PEAJES / xml))
    assert fila["NombrePeaje"] == peaje
    assert fila["NumeroPlaca"] == placa


def test_items_sin_duplicar():
    _, fila = extraer_datos_factura(str(PEAJES / "ad0900470252000250081eac8.xml"))
    assert len(fila["Items"]) == 1
