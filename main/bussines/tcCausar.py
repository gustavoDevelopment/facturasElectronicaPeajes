import json
from openpyxl import Workbook, load_workbook
from datetime import datetime
import os
from ..plantilla.cabecera import Cabecera
from ..plantilla.constants import Constants

def crear_archivo_excel_con_cabecera(subFolder):
    fecha_hora_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"documento_{fecha_hora_actual}.xlsx"
    # Establecer la ruta del archivo Excel
    path_excel = os.path.join(os.getcwd(), "output",subFolder, nombre_archivo)  # Aquí creas el directorio "file"
    # Verifica que la carpeta "file" exista, si no, créala
    if not os.path.exists(os.path.dirname(path_excel)):
        os.makedirs(os.path.dirname(path_excel))

    wb = Workbook()
    ws = wb.active
    ws.title = "Encabezado"

    # Escribimos la cabecera en la fila 1 con los nombres del Enum
    for columna in Cabecera:
        ws.cell(row=1, column=columna.value[1], value=columna.value[0])

    wb.save(path_excel)
    print(f"✅ Archivo creado: {path_excel}")
    return path_excel


def agregar_filas_al_excel(path_excel: str, datos: list[dict]):
    if not os.path.exists(path_excel):
        raise FileNotFoundError("El archivo no existe. Primero crea el archivo con cabeceras.")

    wb = load_workbook(path_excel)
    ws = wb.active
    next_row = 2

    for item in datos:
        ws.cell(row=next_row, column=Constants.ENCAB_EMPRESA.value[1], value=Constants.ENCAB_EMPRESA.value[0])
        ws.cell(row=next_row, column=Constants.ENCAB_TERCERO_INTERNO.value[1], value=Constants.ENCAB_TERCERO_INTERNO.value[0])
        ws.cell(row=next_row, column=Constants.ENCAB_TERCERO_EXTERNO.value[1], value=Constants.ENCAB_TERCERO_EXTERNO.value[0])
        ws.cell(row=next_row, column=Constants.ENCAB_FORMA_PAGO.value[1], value=Constants.ENCAB_FORMA_PAGO.value[0])
        ws.cell(row=next_row, column=Constants.ENCAB_VERIFICADO.value[1], value=Constants.ENCAB_VERIFICADO.value[0])
        ws.cell(row=next_row, column=Constants.ENCAB_ANULADO.value[1], value=Constants.ENCAB_ANULADO.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_PRODUCTO.value[1], value=Constants.DETALLE_PRODUCTO.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_BODEGA.value[1], value=Constants.DETALLE_BODEGA.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_UNIDAD_MEDIDA.value[1], value=Constants.DETALLE_UNIDAD_MEDIDA.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_CANTIDAD.value[1], value=Constants.DETALLE_CANTIDAD.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_IVA.value[1], value=Constants.DETALLE_IVA.value[0])
        ws.cell(row=next_row, column=Constants.DETALLE_DESCUENTO.value[1], value=Constants.DETALLE_DESCUENTO.value[0])
        
        ws.cell(row=next_row, column=Cabecera.ENCAB_FECHA.value[1], value=item["FechaEmision"])
        ws.cell(row=next_row, column=Cabecera.ENCAB_PREF_DTO_EXT.value[1], value=item["FacturaCabecera"])
        ws.cell(row=next_row, column=Cabecera.ENCAB_NO_DTO_EXT.value[1], value=item["FacturaNumero"])
        ws.cell(row=next_row, column=Cabecera.ENCAB_NOTA.value[1], value=item["NombrePeaje"])
        ws.cell(row=next_row, column=Cabecera.ENCAB_FECHA_EMISION.value[1], value=item["FechaEmision"])

        ws.cell(row=next_row, column=Cabecera.DETALLE_VALOR_UNITARIO.value[1], value=item["ValorTotal"])
        ws.cell(row=next_row, column=Cabecera.DETALLE_VENCIMIENTO.value[1], value=item["FechaEmision"])
        ws.cell(row=next_row, column=Cabecera.DETALLE_CENTRO_COSTOS.value[1], value=item["NumeroPlaca"])
        next_row += 1

    wb.save(path_excel)
    print(f"Se agregaron {len(datos)} filas al archivo.")

