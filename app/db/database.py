'''
Database setup and table creation using SQLAlchemy Core for SQLite.
'''
import sqlalchemy
from sqlalchemy import (Table, Column, Integer, String, Boolean, DateTime, ForeignKey, MetaData, create_engine, Text)
from datetime import datetime
import os

# Define the database URL. Creates a file named `judicial_data.sqlite` in the data directory.
# Construct the path to the data directory relative to this file's location
# This file is in JudicialAIProject/app/db/database.py
# Data directory is JudicialAIProject/data/
APP_DIR = os.path.dirname(os.path.dirname(__file__)) # JudicialAIProject/app/
PROJECT_ROOT = os.path.dirname(APP_DIR) # JudicialAIProject/
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Ensure the data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'judicial_data.sqlite')}"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite

# Metadata container
metadata = MetaData()

# Table definition for Proceso
proceso_table = Table(
    "proceso",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("idProceso", String, unique=True, index=True, nullable=False), # From Rama Judicial API
    Column("numeroRadicacion", String, index=True, nullable=True),
    Column("despacho", String, nullable=True),
    Column("ponente", String, nullable=True),
    Column("sujetos", Text, nullable=True), # Can be long
    Column("fechaRadicacion", String, nullable=True),
    Column("tipoProceso", String, nullable=True),
    Column("claseProceso", String, nullable=True),
    Column("ubicacionExpediente", String, nullable=True),
    Column("demandante", String, nullable=True),
    Column("demandado", String, nullable=True),
    Column("nombre_busqueda", String, nullable=True, index=True), # Name/NIT used for search
    Column("fecha_consulta_api", DateTime, default=datetime.utcnow),
    Column("fecha_creacion_db", DateTime, default=datetime.utcnow),
    Column("fecha_actualizacion_db", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

# Table definition for Actuacion
actuacion_table = Table(
    "actuacion",
    metadata,
    Column("id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("idRegActuacion", String, index=True, nullable=True), # From Rama Judicial API
    Column("proceso_db_id", Integer, ForeignKey("proceso.id"), nullable=False, index=True),
    Column("fechaActuacion", String, nullable=True),
    Column("actuacion", String, nullable=True), # Tipo de actuación
    Column("anotacion", Text, nullable=True), # Can be very long
    Column("fechaIniciaTermino", String, nullable=True),
    Column("fechaFinalizaTermino", String, nullable=True),
    Column("fechaRegistro", String, nullable=True),
    Column("conDocumentos", Boolean, default=False),
    Column("resumen_ia", Text, nullable=True),
    Column("clasificacion_urgencia_ia", String, nullable=True),
    Column("fecha_creacion_db", DateTime, default=datetime.utcnow),
    Column("fecha_actualizacion_db", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

def create_db_and_tables():
    '''
    Creates the database and all defined tables if they don't already exist.
    '''
    try:
        # Check if the SQLite file exists. If not, create_all will create it.
        # For other DBs, this would connect to an existing server and create tables.
        db_file_path = engine.url.database
        if db_file_path and not os.path.exists(db_file_path):
            print(f"Database file {db_file_path} not found, will be created.")
        
        metadata.create_all(bind=engine)
        print("Database and tables created successfully (if they didn't exist).")
        if db_file_path:
            print(f"Database file is at: {os.path.abspath(db_file_path)}")

    except sqlalchemy.exc.SQLAlchemyError as e:
        print(f"An error occurred during database/table creation: {e}")
    except Exception as e:
        print(f"A general error occurred: {e}")

# Example of how to run the table creation:
if __name__ == "__main__":
    print("Initializing database setup...")
    create_db_and_tables()
