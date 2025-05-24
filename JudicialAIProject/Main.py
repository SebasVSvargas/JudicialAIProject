import app.services.ai_services as ais
import app.clients.rama_judicial_client as rjc
import fitz
import io

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
    

    a = 1
if __name__ == "__main__":
    main()