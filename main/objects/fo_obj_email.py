import json

class ConfiguracionEmail:
    def __init__(self, path_file=None):
        """Constructor de la clase para inicializar valores de configuración"""
        self.path_file = path_file

    def cargar_configuracion(self):
        """Carga el archivo de configuración desde el path dado"""
        if self.path_file:
            try:
                with open(self.path_file, "r") as file:
                    self.config = json.load(file)
                print(f"Configuración cargada correctamente desde {self.path_file}.")
                self.find=True
                return self.config
            except FileNotFoundError:
                print(f"Error: El archivo de configuración {self.path_file} no se encuentra.")
                self.find=False
                return 
            except json.JSONDecodeError:
                print(f"Error: El archivo {self.path_file} tiene un formato incorrecto.")
                self.find=False
                return None
        else:
            print("Error: No se proporcionó un path para el archivo de configuración.")
            self.find=False
            return None

    def obtener_config_email(self):
        """Devuelve la configuración de email"""
        if hasattr(self, 'config') and self.config:  # Verifica que 'config' exista y no esté vacío
            if "email" in self.config:
                return self.config["email"]
            else:
                print("Error: No se encontró la configuración de email en el archivo cargado.")
                return None
        else:
            print("Error: 'config' no está inicializado o está vacío.")
            return None
        

    def actualizar_config_email(self, imap_server, user, password):
        """Actualiza la configuración de email"""
        if "email" not in self.config:
            self.config["email"] = {}

        self.config["email"]["imap_server"] = imap_server
        self.config["email"]["user"] = user
        self.config["email"]["password"] = password
        print("Configuración de email actualizada.")

    def guardar_configuracion(self):
        """Guarda la configuración actual en el archivo JSON"""
        if not self.path_file:
            print("Error: No se ha proporcionado un path de archivo para guardar la configuración.")
            return

        try:
            with open(self.path_file, "w") as file:
                json.dump(self.config, file, indent=4)
            print(f"Configuración guardada correctamente en {self.path_file}.")
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")