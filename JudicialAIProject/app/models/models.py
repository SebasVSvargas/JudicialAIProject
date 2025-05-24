'''
Pydantic models for representing judicial processes and actions.
'''
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Actuacion(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Database ID
    idRegActuacion: Optional[str] = None # ID from Rama Judicial API, e.g., for linking to documents
    proceso_db_id: Optional[int] = Field(default=None, foreign_key="proceso.id") # Foreign key to local Proceso table

    fechaActuacion: Optional[str] = None # From API: "fechaActuacion"
    actuacion: Optional[str] = None      # From API: "actuacion" (tipo de actuación)
    anotacion: Optional[str] = None       # From API: "anotacion"
    fechaIniciaTermino: Optional[str] = None # From API: "fechaIniciaTermino"
    fechaFinalizaTermino: Optional[str] = None # From API: "fechaFinalizaTermino"
    fechaRegistro: Optional[str] = None   # From API: "fechaRegistro"
    conDocumentos: Optional[bool] = False # From API: "conDocumentos"
    
    # Fields to be populated by GenAI
    resumen_ia: Optional[str] = None
    clasificacion_urgencia_ia: Optional[str] = None # e.g., "Alta", "Media", "Baja"

    # Timestamps for local record
    fecha_creacion_db: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion_db: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True # For SQLAlchemy compatibility if we use its ORM later
        anystr_strip_whitespace = True

class Proceso(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True) # Database ID
    idProceso: str # From API: "idProceso" - This is the main ID from Rama Judicial

    # Fields from "Consulta por nombre" or "Consulta directa por número de radicado"
    numeroRadicacion: Optional[str] = None # From API: "numero"
    despacho: Optional[str] = None         # From API: "despacho"
    ponente: Optional[str] = None          # From API: "ponente" (often in details)
    sujetos: Optional[str] = None # From API: "sujetosProcesales" (can be a list, simplify to string for now or parse later)
    # Fields from "Detalle del proceso"
    fechaRadicacion: Optional[str] = None  # From API: "fechaProceso" or "fechaRadicacion"
    tipoProceso: Optional[str] = None      # From API: "tipoProceso"
    claseProceso: Optional[str] = None     # From API: "claseProceso"
    ubicacionExpediente: Optional[str] = None # From API: "ubicacion" or "ubicacionExpediente"
    # Add more fields from API response as needed, e.g., demandante, demandado
    demandante: Optional[str] = None
    demandado: Optional[str] = None

    # Metadata for our system
    nombre_busqueda: Optional[str] = None # The name/NIT used to find this process
    fecha_consulta_api: datetime = Field(default_factory=datetime.utcnow)
    
    # Timestamps for local record
    fecha_creacion_db: datetime = Field(default_factory=datetime.utcnow)
    fecha_actualizacion_db: datetime = Field(default_factory=datetime.utcnow)

    # Relationship (though Pydantic doesn't enforce it like an ORM)
    # actuaciones: List[Actuacion] = [] # This would be populated by our application logic

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

# Example of how you might receive data from the API for an Actuacion
# This is based on the Reto1.txt and typical API structures
# actuacion_api_example = {
#     "idRegActuacion": 1715845581, # Example ID
#     "fechaActuacion": "2024-05-20T00:00:00",
#     "actuacion": "AUTO FIJA FECHA PARA AUDIENCIA",
#     "anotacion": "SE FIJA FECHA PARA AUDIENCIA INICIAL EL DÍA 20 DE JUNIO DE 2024 A LAS 09:00 AM",
#     "fechaIniciaTermino": None,
#     "fechaFinalizaTermino": None,
#     "fechaRegistro": "2024-05-20T10:30:00",
#     "conDocumentos": True
# }

# Example of how you might receive data from the API for a Proceso (summary from search)
# proceso_api_search_example = {
#     "idProceso": 198167821,
#     "numero": "05001418900820250032700",
#     "despacho": "JUZGADO 008 CIVIL MUNICIPAL DE EJECUCIÓN DE SENTENCIAS DE MEDELLÍN",
#     "sujetosProcesales": "DEMANDANTE: BANCOLOMBIA S.A. | DEMANDADO: JUAN PEREZ", # Example, actual structure may vary
#     "fechaProceso": "2025-01-15T00:00:00", # Or similar field
# }

# Example of how you might receive data from the API for Proceso Detail
# proceso_api_detail_example = {
#     "idProceso": 198167821,
#     "tipoProceso": "SINGULAR",
#     "claseProceso": "EJECUTIVO HIPOTECARIO",
#     "ubicacion": "ESTANTE 3",
#     "fechaProceso": "2025-01-15T00:00:00",
#     "ponente": "MARIA LOPEZ",
#     # ... other fields from detail endpoint
# }
