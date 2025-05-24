import streamlit as st
import datetime
from app.clients.rama_judicial_client import (
    consultar_procesos_por_nombre,
    consultar_detalle_proceso,
    consultar_actuaciones_proceso
)
from app.services.ai_services import (
    generar_resumen_actuacion,
    clasificar_urgencia_actuacion
)
from app.db.database import engine, create_db_and_tables, proceso_table, actuacion_table
from app.models.models import Proceso, Actuacion
from app.db import crud # We will create this file next

# Ensure database and tables are created
create_db_and_tables()

st.set_page_config(layout="wide", page_title="Judicial AI Process Explorer")

st.title("🤖 Judicial AI Process Explorer")
st.caption(f"Reto 1 Celerix - {datetime.date.today().strftime('%B %d, %Y')}")

# --- Search Section ---
st.sidebar.header("Buscar Procesos")
nombre_razon_social = st.sidebar.text_input("Nombre o Razón Social", "")
# tipo_persona = st.sidebar.selectbox("Tipo Persona", ["jur", "nat"], index=0) # Default to juridica
cod_despacho = st.sidebar.text_input("Código Despacho (Opcional)", "", help="Ej: 05001 para Medellín")

if st.sidebar.button("🔍 Buscar Procesos"):
    if not nombre_razon_social:
        st.sidebar.error("Por favor, ingrese un nombre o razón social.")
    else:
        with st.spinner(f"Buscando procesos para '{nombre_razon_social}'..."):
            api_procesos_raw = consultar_procesos_por_nombre(
                nombre=nombre_razon_social,
                codificacion_despacho=cod_despacho if cod_despacho else None
            )
            
            if api_procesos_raw and api_procesos_raw.get("procesos"):
                st.session_state.search_results = api_procesos_raw.get("procesos")
                st.session_state.selected_proceso_id = None # Reset selected process
                st.sidebar.success(f"{len(st.session_state.search_results)} procesos encontrados.")
            elif api_procesos_raw:
                 st.sidebar.warning("No se encontraron procesos o la respuesta no tuvo el formato esperado.")
                 st.json(api_procesos_raw) # Show raw response for debugging
                 st.session_state.search_results = []
            else:
                st.sidebar.error("Error al consultar la API de la Rama Judicial.")
                st.session_state.search_results = []

# --- Display Search Results ---
if 'search_results' in st.session_state and st.session_state.search_results:
    st.subheader("Resultados de la Búsqueda")
    
    # Create a list of strings for selectbox, including more info
    # Example: "ID: 123 - Demandante: X vs Demandado: Y (Despacho: Z)"
    # This requires fetching details or having enough info in the initial search result
    
    # For now, using idProceso for selection
    options = [f"{p.get('demandante', 'N/A')} vs {p.get('demandado', 'N/A')} (ID: {p.get('idProceso')})" for p in st.session_state.search_results]
    
    if not options:
        st.write("No hay procesos para mostrar con la información disponible en la búsqueda inicial.")
    else:
        selected_proceso_display = st.selectbox(
            "Seleccione un proceso para ver detalles y actuaciones:",
            options,
            index=0 # Select the first one by default
        )
        
        if selected_proceso_display:
            # Extract idProceso from the selected_proceso_display string
            try:
                st.session_state.selected_proceso_id = selected_proceso_display.split("ID: ")[-1].split(")")[0]
            except Exception as e:
                st.error(f"Error al parsear el ID del proceso seleccionado: {e}")
                st.session_state.selected_proceso_id = None


# --- Display Process Details and Actuaciones ---
if 'selected_proceso_id' in st.session_state and st.session_state.selected_proceso_id:
    proceso_id_str = str(st.session_state.selected_proceso_id)
    st.header(f"Detalles del Proceso ID: {proceso_id_str}")

    # 1. Check if process is in DB, if not, fetch, process, and store
    proceso_db = crud.get_proceso_by_idrama(engine, proceso_id_str)

    if not proceso_db:
        with st.spinner(f"Obteniendo detalles y actuaciones para el proceso {proceso_id_str} por primera vez..."):
            # Fetch details
            detalle_raw = consultar_detalle_proceso(proceso_id_str)
            if not detalle_raw or not detalle_raw.get("idProceso"): # API might return list for detail
                st.error(f"No se pudieron obtener los detalles para el proceso {proceso_id_str}.")
                st.stop()

            # The detail endpoint might return a list with one element
            if isinstance(detalle_raw, list) and detalle_raw:
                detalle_data = detalle_raw[0]
            elif isinstance(detalle_raw, dict) and detalle_raw.get("idProceso"):
                 detalle_data = detalle_raw
            else:
                st.error(f"Formato inesperado para detalles del proceso {proceso_id_str}.")
                st.json(detalle_raw)
                st.stop()


            # Create Proceso Pydantic model from API data
            proceso_data_for_db = Proceso(
                idProceso=str(detalle_data.get("idProceso")),
                numeroRadicacion=detalle_data.get("numero"), # Assuming 'numero' is numeroRadicacion
                despacho=detalle_data.get("despacho"),
                ponente=detalle_data.get("ponente"),
                sujetos=str(detalle_data.get("sujetosProcesales")), # Convert list/dict to str if necessary
                fechaRadicacion=detalle_data.get("fechaProceso") or detalle_data.get("fechaRadicacion"),
                tipoProceso=detalle_data.get("tipoProceso"),
                claseProceso=detalle_data.get("claseProceso"),
                ubicacionExpediente=detalle_data.get("ubicacionExpediente") or detalle_data.get("ubicacion"),
                demandante=detalle_data.get("demandanteNombre") or "N/A", # Adjust based on actual API field
                demandado=detalle_data.get("demandadoNombre") or "N/A",   # Adjust based on actual API field
                nombre_busqueda=nombre_razon_social # Store the search term
            )
            proceso_db_id = crud.create_proceso(engine, proceso_data_for_db)
            if not proceso_db_id:
                st.error("Error al guardar el proceso en la base de datos.")
                st.stop()
            
            proceso_db = crud.get_proceso_by_idrama(engine, proceso_id_str) # Fetch again to get the full object

            # Fetch actuaciones
            actuaciones_raw = consultar_actuaciones_proceso(proceso_id_str)
            actuaciones_list = []
            if actuaciones_raw:
                # Determine if 'actuaciones_raw' is a list directly or a dict containing a list
                if isinstance(actuaciones_raw, list):
                    actuaciones_list = actuaciones_raw
                elif isinstance(actuaciones_raw, dict) and 'actuaciones' in actuaciones_raw and isinstance(actuaciones_raw['actuaciones'], list):
                    actuaciones_list = actuaciones_raw['actuaciones']
                elif isinstance(actuaciones_raw, dict) and 'listaActuaciones' in actuaciones_raw and isinstance(actuaciones_raw['listaActuaciones'], list):
                    actuaciones_list = actuaciones_raw['listaActuaciones']    
                else:
                    st.warning(f"Formato inesperado para actuaciones del proceso {proceso_id_str}. Se intentará procesar si es una lista.")
                    if isinstance(actuaciones_raw, list): # If it's a list at the top level
                         actuaciones_list = actuaciones_raw
                    else: # Log or display the unexpected structure
                        st.json(actuaciones_raw)


            if actuaciones_list:
                st.write(f"Procesando {len(actuaciones_list)} actuaciones...")
                progress_bar = st.progress(0)
                for i, act_raw in enumerate(actuaciones_list):
                    anotacion = act_raw.get("anotacion", "")
                    resumen = generar_resumen_actuacion(anotacion)
                    clasificacion = clasificar_urgencia_actuacion(act_raw.get("actuacion"), anotacion)

                    actuacion_data_for_db = Actuacion(
                        idRegActuacion=str(act_raw.get("idRegActuacion")),
                        proceso_db_id=proceso_db.id, # Use the DB id of the parent proceso
                        fechaActuacion=act_raw.get("fechaActuacion"),
                        actuacion=act_raw.get("actuacion"),
                        anotacion=anotacion,
                        fechaIniciaTermino=act_raw.get("fechaIniciaTermino"),
                        fechaFinalizaTermino=act_raw.get("fechaFinalizaTermino"),
                        fechaRegistro=act_raw.get("fechaRegistro"),
                        conDocumentos=act_raw.get("conDocumentos", False),
                        resumen_ia=resumen,
                        clasificacion_urgencia_ia=clasificacion
                    )
                    crud.create_actuacion(engine, actuacion_data_for_db)
                    progress_bar.progress((i + 1) / len(actuaciones_list))
                st.success("Actuaciones procesadas y guardadas.")
            else:
                st.info("No se encontraron actuaciones para este proceso o el formato fue inesperado.")
    
    # Display Proceso Details from DB
    if proceso_db:
        st.subheader("Información General del Proceso (Desde BD)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tipo Proceso", proceso_db.tipoProceso or "N/A")
            st.metric("Clase Proceso", proceso_db.claseProceso or "N/A")
            st.text_input("Despacho", proceso_db.despacho or "N/A", disabled=True)
        with col2:
            st.text_input("Ponente", proceso_db.ponente or "N/A", disabled=True)
            st.text_input("Ubicación Expediente", proceso_db.ubicacionExpediente or "N/A", disabled=True)
            st.text_input("Fecha Radicación", proceso_db.fechaRadicacion or "N/A", disabled=True)

        st.text_area("Sujetos Procesales", proceso_db.sujetos or "N/A", height=100, disabled=True)
        st.caption(f"ID Rama Judicial: {proceso_db.idProceso} | ID Base de Datos: {proceso_db.id}")
        st.caption(f"Consultado via API por: '{proceso_db.nombre_busqueda}' el {proceso_db.fecha_consulta_api}")
        st.caption(f"Registro en BD creado: {proceso_db.fecha_creacion_db}, actualizado: {proceso_db.fecha_actualizacion_db}")

        # Display Actuaciones from DB
        st.subheader("Actuaciones del Proceso (Desde BD)")
        actuaciones_db = crud.get_actuaciones_by_proceso_db_id(engine, proceso_db.id)
        if actuaciones_db:
            for idx, act in enumerate(actuaciones_db):
                urgency_color = {
                    "ALTA": "red",
                    "MEDIA": "orange",
                    "BAJA": "green"
                }.get(act.clasificacion_urgencia_ia, "blue")

                with st.expander(f"{act.fechaActuacion} - {act.actuacion} - Urgencia: :{urgency_color}[{act.clasificacion_urgencia_ia or 'N/A'}]", expanded=idx==0):
                    st.markdown(f"**Anotación:**")
                    st.text_area(f"anotacion_{act.id}", act.anotacion or "N/A", height=150, disabled=True, key=f"anot_orig_{act.id}")
                    st.markdown(f"**Resumen IA:**")
                    st.text_area(f"resumen_ia_{act.id}", act.resumen_ia or "No disponible.", height=100, disabled=True, key=f"anot_ia_{act.id}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.text_input("Fecha Registro", act.fechaRegistro or "N/A", disabled=True, key=f"freg_{act.id}")
                    col2.text_input("Inicia Término", act.fechaIniciaTermino or "N/A", disabled=True, key=f"ftermini_{act.id}")
                    col3.text_input("Finaliza Término", act.fechaFinalizaTermino or "N/A", disabled=True, key=f"fterminf_{act.id}")
                    col4.text_input("¿Documentos?", "Sí" if act.conDocumentos else "No", disabled=True, key=f"fdoc_{act.id}")
                    st.caption(f"ID Actuación (API): {act.idRegActuacion} | ID Actuación (BD): {act.id}")
        else:
            st.info("No hay actuaciones registradas en la base de datos para este proceso.")

else:
    st.info("Realice una búsqueda para ver los procesos y sus detalles.")

st.sidebar.markdown("---_---")
st.sidebar.caption("GitHub Copilot Demo")

# To run: streamlit run app.py (from JudicialAIProject directory)
