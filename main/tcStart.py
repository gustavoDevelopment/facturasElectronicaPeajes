from bussines.tcEmail import do_on_start
from bussines.tcExtracFacturacion import do_on_start_extract_facturacion

month = input("Ingrese el MES: ")
year = input("Ingrese el YEAR : ")
subFolderDate= str(month)+str("_")+str(year)
do_on_start(subFolderDate,int(month),int(year))
do_on_start_extract_facturacion(subFolderDate)