import app.services.ai_services as ais
import app.clients.rama_judicial_client as rjc
import fitz
import io
from app.db import crud # We will create this file next
import streamlit as st
from app.db.database import engine, create_db_and_tables, proceso_table, actuacion_table
import datetime
from app.models.models import Proceso, Actuacion

def main():
    # Example usage of the AI service
    test_id_proceso_static = "198167821" 

    print(f"\n--- Test: Consultar Detalle del Proceso ({test_id_proceso_static}) ---")
    detalle = rjc.consultar_detalle_proceso(test_id_proceso_static)
    if detalle:
        # print("Detalle del proceso:", detalle) # Full detail can be verbose
        print(f"  Tipo de Proceso: {detalle.get('tipoProceso')}")
        print(f"  Clase de Proceso: {detalle.get('claseProceso')}")
        print(f"  Ubicación Expediente: {detalle.get('ubicacion')}")
    else:
        print(f"No details found for process {test_id_proceso_static} or error occurred.")

    print(f"\n--- Test: Consultar Actuaciones del Proceso ({test_id_proceso_static}) ---")
    actuaciones_data = rjc.consultar_actuaciones_proceso(test_id_proceso_static)
    if actuaciones_data:
        # The structure of actuaciones_data needs to be inspected from an actual API call.
        # Assuming it's a list of actuaciones directly or a dict with a key like 'actuaciones'
        if isinstance(actuaciones_data, list):
            actuaciones_list = actuaciones_data
        elif isinstance(actuaciones_data, dict) and 'actuaciones' in actuaciones_data:
            actuaciones_list = actuaciones_data['actuaciones']
        else:
            actuaciones_list = [] # Or handle as an unexpected format
            rjc.logging.warning(f"Unexpected format for actuaciones: {type(actuaciones_data)}")

        if actuaciones_list:
            print(f"Found {len(actuaciones_list)} actuaciones.")
            for actuacion in actuaciones_list[:3]: # Print first 3 actuaciones
                print(f"  Fecha: {actuacion.get('fechaActuacion')}, Actuación: {actuacion.get('actuacion')}, Anotación: {actuacion.get('anotacion', '')[:50]}...")
        else:
            print("No actuaciones found in the response or unexpected format.")
    else:
        print(f"No actuaciones found for process {test_id_proceso_static} or error occurred.")

    # Test new functions
    test_numero_radicacion = "05001418900820250032700" # Example from prompt
    print(f"\\n--- Test: Consultar Procesos por Número de Radicación ({test_numero_radicacion}) ---")
    proceso_rad = rjc.consultar_procesos_por_numero_radicacion(test_numero_radicacion)
    if proceso_rad and proceso_rad.get("procesos"):
        print(f"Found {len(proceso_rad['procesos'])} process(es).")
        for p in proceso_rad["procesos"][:1]:
             print(f"  ID Proceso: {p.get('idProceso')}, Demandante: {p.get('demandante')}, Demandado: {p.get('demandado')}")
    elif proceso_rad:
        print("Proceso por radicado response:", proceso_rad)
    else:
        print(f"No proceso found for radicado {test_numero_radicacion} or error occurred.")

    test_id_reg_actuacion_docs = "1715845581" # Example from prompt
    print(f"\\n--- Test: Consultar Documentos de Actuación ({test_id_reg_actuacion_docs}) ---")
    documentos_actuacion = rjc.consultar_documentos_actuacion(test_id_reg_actuacion_docs)
    test_id_reg_documento_descarga = None
    if documentos_actuacion and isinstance(documentos_actuacion, list) and documentos_actuacion:
        print(f"Found {len(documentos_actuacion)} documento(s) for actuación {test_id_reg_actuacion_docs}.")
        for doc in documentos_actuacion[:1]: # Print first document info
            print(f"  Nombre: {doc.get('nombre')}, ID Reg Documento: {doc.get('idRegDocumento')}, Checksum: {doc.get('checksum')}")
            if 'idRegDocumento' in doc and not test_id_reg_documento_descarga:
                test_id_reg_documento_descarga = str(doc.get('idRegDocumento'))
    elif documentos_actuacion:
         print("Documentos actuación response:", documentos_actuacion) # Print raw response
    else:
        print(f"No documents found for actuación {test_id_reg_actuacion_docs} or error occurred.")

    if test_id_reg_documento_descarga:
        print(f"\\n--- Test: Descargar Documento ({test_id_reg_documento_descarga}) ---")
        documento_contenido = rjc.descargar_documento_actuacion(test_id_reg_documento_descarga)
        if documento_contenido:
            print(f"Documento descargado. Tamaño: {len(documento_contenido)} bytes.")
            # Example: Save the document
            # try:
            #     with open(f"documento_{test_id_reg_documento_descarga}.pdf", "wb") as f: # Assuming PDF
            #         f.write(documento_contenido)
            #     print(f"Documento guardado como documento_{test_id_reg_documento_descarga}.pdf")
            # except IOError as e:
            #     print(f"Error al guardar el documento: {e}")
        else:
            print(f"No se pudo descargar el documento {test_id_reg_documento_descarga} or error occurred.")
    else:
        print("\\nSkipping Test: Descargar Documento - No idRegDocumento available from previous step.")
    
    rjc.logging.info("Finished testing Rama Judicial API client.")

    pdfstream = io.BytesIO(documento_contenido)

    with fitz.open(stream=pdfstream, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
         text = page.get_text()

    responseLLM = ais.generar_resumen_actuacion(texto_actuacion=text)
    urgenciaLLM = ais.clasificar_urgencia_actuacion(texto_actuacion=text)


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
                api_procesos_raw = rjc.consultar_procesos_por_nombre(
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
                detalle_raw = rjc.consultar_detalle_proceso(proceso_id_str)
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
                actuaciones_raw = rjc.consultar_actuaciones_proceso(proceso_id_str)
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
                        resumen = responseLLM
                        clasificacion = urgenciaLLM

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

     
    a = 1

if __name__ == "__main__":
    main()