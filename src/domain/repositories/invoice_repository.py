"""
Interfaces para el repositorio de facturas.
"""
from abc import ABC, abstractmethod
from src.domain.entities.invoice import Invoice

class InvoiceRepository(ABC):
    """Interfaz para el repositorio de facturas."""
    
    @abstractmethod
    def save_invoice(self, invoice: Invoice) -> None:
        """Guarda una factura."""
        pass
    
    @abstractmethod
    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """Obtiene una factura por su ID."""
        pass
