from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from app.db.database import proceso_table, actuacion_table, engine
from app.models.models import Proceso as ProcesoPydantic, Actuacion as ActuacionPydantic
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_proceso(db_engine, proceso: ProcesoPydantic) -> Optional[int]:
    """
    Creates a new proceso in the database.
    Returns the ID of the newly created proceso, or None if an error occurs.
    """
    try:
        with db_engine.connect() as connection:
            # Check if idProceso already exists
            stmt_select = select(proceso_table).where(proceso_table.c.idProceso == proceso.idProceso)
            existing_proceso = connection.execute(stmt_select).first()
            if existing_proceso:
                logger.info(f"Proceso with idProceso {proceso.idProceso} already exists. Updating.")
                # Update existing proceso
                stmt_update = (
                    update(proceso_table)
                    .where(proceso_table.c.idProceso == proceso.idProceso)
                    .values(**proceso.model_dump(exclude_unset=True, exclude_none=True, exclude={"id", "fecha_creacion_db"})) # Exclude id and creation timestamp
                )
                result = connection.execute(stmt_update)
                connection.commit()
                return existing_proceso.id # Return existing DB ID
            
            # Insert new proceso
            stmt_insert = proceso_table.insert().values(**proceso.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}))
            result = connection.execute(stmt_insert)
            connection.commit()
            logger.info(f"Proceso {proceso.idProceso} created with DB ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        logger.error(f"Error creating/updating proceso {proceso.idProceso}: {e}")
        return None

def get_proceso_by_idrama(db_engine, id_proceso_rama: str) -> Optional[ProcesoPydantic]:
    """Retrieves a proceso by its Rama Judicial ID (idProceso)."""
    try:
        with db_engine.connect() as connection:
            stmt = select(proceso_table).where(proceso_table.c.idProceso == id_proceso_rama)
            result = connection.execute(stmt).first()
            if result:
                return ProcesoPydantic(**result._asdict())
            return None
    except Exception as e:
        logger.error(f"Error getting proceso by id_proceso_rama {id_proceso_rama}: {e}")
        return None

def get_proceso_by_db_id(db_engine, proceso_db_id: int) -> Optional[ProcesoPydantic]:
    """Retrieves a proceso by its database ID."""
    try:
        with db_engine.connect() as connection:
            stmt = select(proceso_table).where(proceso_table.c.id == proceso_db_id)
            result = connection.execute(stmt).first()
            if result:
                return ProcesoPydantic(**result._asdict())
            return None
    except Exception as e:
        logger.error(f"Error getting proceso by db_id {proceso_db_id}: {e}")
        return None

def create_actuacion(db_engine, actuacion: ActuacionPydantic) -> Optional[int]:
    """
    Creates a new actuacion in the database.
    Returns the ID of the newly created actuacion, or None if an error occurs.
    """
    try:
        with db_engine.connect() as connection:
            # Check if idRegActuacion already exists for this proceso_db_id
            if actuacion.idRegActuacion: # Only check if idRegActuacion is present
                stmt_select = select(actuacion_table).where(
                    actuacion_table.c.idRegActuacion == actuacion.idRegActuacion,
                    actuacion_table.c.proceso_db_id == actuacion.proceso_db_id
                )
                existing_actuacion = connection.execute(stmt_select).first()
                if existing_actuacion:
                    logger.info(f"Actuacion with idRegActuacion {actuacion.idRegActuacion} for proceso_db_id {actuacion.proceso_db_id} already exists. Updating.")
                    stmt_update = (
                        update(actuacion_table)
                        .where(actuacion_table.c.id == existing_actuacion.id) # Update by its own DB ID
                        .values(**actuacion.model_dump(exclude_unset=True, exclude_none=True, exclude={"id", "fecha_creacion_db"}))
                    )
                    connection.execute(stmt_update)
                    connection.commit()
                    return existing_actuacion.id # Return existing DB ID

            # Insert new actuacion
            stmt_insert = actuacion_table.insert().values(**actuacion.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}))
            result = connection.execute(stmt_insert)
            connection.commit()
            logger.info(f"Actuacion for proceso_db_id {actuacion.proceso_db_id} created with DB ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        logger.error(f"Error creating/updating actuacion for proceso_db_id {actuacion.proceso_db_id}: {e}")
        return None

def get_actuaciones_by_proceso_db_id(db_engine, proceso_db_id: int) -> List[ActuacionPydantic]:
    """Retrieves all actuaciones for a given proceso_db_id, ordered by fechaActuacion descending."""
    try:
        with db_engine.connect() as connection:
            stmt = (
                select(actuacion_table)
                .where(actuacion_table.c.proceso_db_id == proceso_db_id)
                .order_by(actuacion_table.c.fechaActuacion.desc()) # Or .asc() if preferred
            )
            results = connection.execute(stmt).fetchall()
            return [ActuacionPydantic(**row._asdict()) for row in results]
    except Exception as e:
        logger.error(f"Error getting actuaciones for proceso_db_id {proceso_db_id}: {e}")
        return []

# Potentially add update/delete functions if needed later
