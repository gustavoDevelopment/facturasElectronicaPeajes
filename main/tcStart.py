from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion
import os

month = input("Ingrese el MES: ")
year = input("Ingrese el YEAR : ")
subFolderDate= str(month)+str("_")+str(year)
##do_on_start(4,2025)
do_on_start_extract_facturacion(subFolderDate)