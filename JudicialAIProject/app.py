import streamlit as st
import datetime
from app.clients.rama_judicial_client import (
    consultar_procesos_por_nombre,
    consultar_detalle_proceso,
    consultar_actuaciones_proceso,
    consultar_procesos_por_numero_radicacion, # Added
    consultar_documentos_actuacion, # Added
    descargar_documento_actuacion # Added
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

search_method = st.sidebar.radio(
    "Método de Búsqueda:",
    ("Nombre o Razón Social", "Número de Radicación")
)

nombre_razon_social = ""
numero_radicacion = ""

if search_method == "Nombre o Razón Social":
    nombre_razon_social = st.sidebar.text_input("Nombre o Razón Social", "")
    cod_despacho = st.sidebar.text_input("Código Despacho (Opcional)", "", help="Ej: 05001 para Medellín")
else: # Número de Radicación
    numero_radicacion = st.sidebar.text_input("Número de Radicación Completo", "", help="Ej: 05001418900820250032700")


if st.sidebar.button("🔍 Buscar Procesos"):
    st.session_state.search_results = []
    st.session_state.selected_proceso_id = None # Reset selected process
    api_procesos_raw = None

    if search_method == "Nombre o Razón Social":
        if not nombre_razon_social:
            st.sidebar.error("Por favor, ingrese un nombre o razón social.")
        else:
            with st.spinner(f"Buscando procesos para '{nombre_razon_social}'..."):
                api_procesos_raw = consultar_procesos_por_nombre(
                    nombre=nombre_razon_social,
                    codificacion_despacho=cod_despacho if cod_despacho else None
                )
    elif search_method == "Número de Radicación":
        if not numero_radicacion:
            st.sidebar.error("Por favor, ingrese el número de radicación.")
        else:
            with st.spinner(f"Buscando proceso por radicado '{numero_radicacion}'..."):
                # solo_activos for numero_radicacion is False by default in client
                api_procesos_raw = consultar_procesos_por_numero_radicacion(
                    numero_radicacion=numero_radicacion 
                )
    
    if api_procesos_raw:
        if api_procesos_raw.get("procesos"):
            st.session_state.search_results = api_procesos_raw.get("procesos")
            st.sidebar.success(f"{len(st.session_state.search_results)} proceso(s) encontrado(s).")
        elif search_method == "Número de Radicación" and isinstance(api_procesos_raw, dict) and "idProceso" in api_procesos_raw:
            # If search by numero_radicacion returns a single process directly (not in a "procesos" list)
            # This depends on the actual API response structure for this endpoint.
            # Assuming it might return a list with one item or the item directly.
            # For now, the client function for numero_radicacion is expected to return a dict with "procesos" key.
            # If it can return a single process, the client should normalize it or this part needs adjustment.
            # Based on current client, this branch might not be hit if client always wraps in {"procesos": [...]}
            st.session_state.search_results = [api_procesos_raw] 
            st.sidebar.success("1 proceso encontrado.")
        else:
            st.sidebar.warning("No se encontraron procesos o la respuesta no tuvo el formato esperado.")
            st.json(api_procesos_raw) # Show raw response for debugging
    elif (search_method == "Nombre o Razón Social" and nombre_razon_social) or \
         (search_method == "Número de Radicación" and numero_radicacion):
        st.sidebar.error("Error al consultar la API de la Rama Judicial.")

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
            
            # Store the original search term if it was by name for later use
            if search_method == "Nombre o Razón Social":
                st.session_state.nombre_busqueda_cache = nombre_razon_social
            else:
                st.session_state.nombre_busqueda_cache = None # Clear if search was by numero


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
                demandante=detalle_data.get("demandanteNombre") or detalle_data.get("sujetosProcesales", [{}])[0].get("nombre") if isinstance(detalle_data.get("sujetosProcesales"), list) and detalle_data.get("sujetosProcesales") else "N/A",
                demandado=detalle_data.get("demandadoNombre") or detalle_data.get("sujetosProcesales", [{}, {}])[1].get("nombre") if isinstance(detalle_data.get("sujetosProcesales"), list) and len(detalle_data.get("sujetosProcesales")) > 1 else "N/A",
                nombre_busqueda=st.session_state.get("nombre_busqueda_cache") # Use cached search name
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
                    
                    col1_act, col2_act, col3_act, col4_act = st.columns(4)
                    col1_act.text_input("Fecha Registro", act.fechaRegistro or "N/A", disabled=True, key=f"freg_{act.id}")
                    col2_act.text_input("Inicia Término", act.fechaIniciaTermino or "N/A", disabled=True, key=f"ftermini_{act.id}")
                    col3_act.text_input("Finaliza Término", act.fechaFinalizaTermino or "N/A", disabled=True, key=f"fterminf_{act.id}")
                    
                    doc_status = "Sí" if act.conDocumentos else "No"
                    if act.conDocumentos and act.idRegActuacion:
                        if col4_act.button(f"Ver Documentos ({doc_status})", key=f"docs_btn_{act.idRegActuacion}"):
                            st.session_state.actuacion_docs_id_to_show = str(act.idRegActuacion)
                            st.session_state.documentos_list = None # Reset
                    else:
                        col4_act.text_input("¿Documentos?", doc_status, disabled=True, key=f"fdoc_{act.id}")
                    
                    st.caption(f"ID Actuación (API): {act.idRegActuacion} | ID Actuación (BD): {act.id}")

                    # Display documents for the selected actuacion
                    if st.session_state.get("actuacion_docs_id_to_show") == str(act.idRegActuacion):
                        if st.session_state.get("documentos_list") is None: # Fetch only once or if reset
                            with st.spinner(f"Consultando documentos para actuación {act.idRegActuacion}..."):
                                docs = consultar_documentos_actuacion(str(act.idRegActuacion))
                                if docs and isinstance(docs, list):
                                    st.session_state.documentos_list = docs
                                elif docs: # API returned something but not a list
                                    st.warning("Respuesta inesperada al consultar documentos.")
                                    st.json(docs)
                                    st.session_state.documentos_list = []
                                else:
                                    st.error("No se pudieron obtener los documentos o no hay documentos asociados.")
                                    st.session_state.documentos_list = []
                        
                        if st.session_state.get("documentos_list"):
                            st.markdown("##### Documentos Asociados:")
                            for doc_item in st.session_state.documentos_list:
                                doc_id_reg = doc_item.get("idRegDocumento")
                                doc_nombre = doc_item.get("nombre", f"Documento ID {doc_id_reg}")
                                doc_checksum = doc_item.get("checksum")
                                
                                doc_col1, doc_col2 = st.columns([3,1])
                                doc_col1.markdown(f"- **{doc_nombre}** (ID: {doc_id_reg}, Checksum: {doc_checksum or 'N/A'})")
                                
                                if doc_id_reg:
                                    # Generate a unique key for the download button
                                    download_button_key = f"download_{act.idRegActuacion}_{doc_id_reg}"
                                    if doc_col2.button(f"📥 Descargar", key=download_button_key):
                                        with st.spinner(f"Descargando {doc_nombre}..."):
                                            contenido_doc = descargar_documento_actuacion(str(doc_id_reg))
                                            if contenido_doc:
                                                # Determine file extension (this is a guess, API might provide it)
                                                # For now, defaulting to .pdf if name suggests it, else .bin
                                                file_extension = ".pdf" if ".pdf" in doc_nombre.lower() else ".zip" if ".zip" in doc_nombre.lower() else ".docx" if ".docx" in doc_nombre.lower() else ".bin"
                                                
                                                st.download_button(
                                                    label=f"Descarga '{doc_nombre}' lista (click de nuevo si no inicia)",
                                                    data=contenido_doc,
                                                    file_name=f"{doc_nombre}{file_extension}" if not doc_nombre.endswith(file_extension) else doc_nombre,
                                                    mime="application/octet-stream" # Generic, or try to infer
                                                )
                                                st.success(f"'{doc_nombre}' listo para descargar.")
                                            else:
                                                st.error(f"No se pudo descargar el documento {doc_nombre}.")
                        elif not st.session_state.get("documentos_list") and st.session_state.get("actuacion_docs_id_to_show"):
                             st.info("No hay documentos asociados a esta actuación o no se pudieron cargar.")


        else:
            st.info("No hay actuaciones registradas en la base de datos para este proceso.")

else:
    st.info("Realice una búsqueda para ver los procesos y sus detalles.")

st.sidebar.markdown("---_---")
st.sidebar.caption("GitHub Copilot Demo")

# To run: streamlit run app.py (from JudicialAIProject directory)
