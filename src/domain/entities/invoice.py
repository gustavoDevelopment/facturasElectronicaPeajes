"""
Entidad que representa una factura electrónica.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Invoice:
    """Representa una factura electrónica."""
    id: str
    prefix: str
    number: str
    issue_date: datetime
    currency: str
    total_amount: float
    items: List[dict]
    toll_name: Optional[str] = None
    plate_number: Optional[str] = None
    related_invoice: Optional[str] = None
