'''
Client for interacting with the Rama Judicial API.
'''
import requests
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"

def consultar_procesos_por_nombre(
    nombre: str,
    tipo_persona: str = "jur",
    solo_activos: bool = True,
    codificacion_despacho: str | None = None, # e.g., "05001" for Medellín, Antioquia
    pagina: int = 1
) -> dict | None:
    '''
    Consults processes by company name (razón social) or individual name.

    Args:
        nombre: The name of the company or person.
        tipo_persona: "jur" for legal entity, "nat" for natural person.
        solo_activos: True to search only for active processes.
        codificacion_despacho: Optional. Judicial office codification (department/city).
        pagina: Page number for results.

    Returns:
        A dictionary with the API response or None if an error occurs.
    '''
    endpoint = f"{BASE_URL}/Procesos/Consulta/NombreRazonSocial"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    params = {
        "nombre": nombre,
        "tipoPersona": tipo_persona,
        "SoloActivos": str(solo_activos).lower(), # API expects "true" or "false"
        "pagina": pagina
    }
    if codificacion_despacho:
        params["codificacionDespacho"] = codificacion_despacho

    try:
        response = requests.get(endpoint, params=params, timeout=30, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"An error occurred during the request: {req_err}")
    return None

def consultar_detalle_proceso(id_proceso: str) -> dict | None:
    '''
    Retrieves the details of a specific process using its ID.

    Args:
        id_proceso: The unique identifier of the process.

    Returns:
        A dictionary with the process details or None if an error occurs.
    '''
    endpoint = f"{BASE_URL}/Proceso/Detalle/{id_proceso}"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(endpoint, timeout=30,headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching process details for {id_proceso}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error fetching process details for {id_proceso}: {req_err}")
    return None

def consultar_actuaciones_proceso(id_proceso: str) -> dict | None:
    '''
    Retrieves the actions (actuaciones) of a specific process using its ID.

    Args:
        id_proceso: The unique identifier of the process.

    Returns:
        A dictionary with the process actions or None if an error occurs.
    '''
    endpoint = f"{BASE_URL}/Proceso/Actuaciones/{id_proceso}"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(endpoint, timeout=30, headers=headers)
        response.raise_for_status()
        # The response for actuaciones is often a list directly, not a dict with a key
        # However, to be safe and consistent with other functions, we check if it's a dict
        # and if it contains a list of actuaciones. The actual API might return a list directly.
        data = response.json()
        return data # Assuming the API returns the list of actuaciones directly or a dict containing them
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching actions for process {id_proceso}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error fetching actions for process {id_proceso}: {req_err}")
    return None

def consultar_procesos_por_numero_radicacion(
    numero_radicacion: str,
    solo_activos: bool = False,
    pagina: int = 1
) -> dict | None:
    """
    Consults processes by their unique registration number (numero de radicación).

    Args:
        numero_radicacion: The complete registration number of the process.
        solo_activos: False to search for all processes (active and inactive).
                      The API example uses false, so defaulting to that.
        pagina: Page number for results.

    Returns:
        A dictionary with the API response or None if an error occurs.
    """
    endpoint = f"{BASE_URL}/Procesos/Consulta/NumeroRadicacion"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    params = {
        "numero": numero_radicacion,
        "SoloActivos": str(solo_activos).lower(),
        "pagina": pagina
    }
    try:
        response = requests.get(endpoint, params=params, timeout=30, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching process by numero_radicacion {numero_radicacion}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error fetching process by numero_radicacion {numero_radicacion}: {req_err}")
    return None

def consultar_documentos_actuacion(id_reg_actuacion: str) -> dict | None:
    """
    Retrieves documents associated with a specific judicial action (actuación).

    Args:
        id_reg_actuacion: The unique identifier of the judicial action registration.

    Returns:
        A dictionary with the documents list or None if an error occurs.
    """
    endpoint = f"{BASE_URL}/Proceso/DocumentosActuacion/{id_reg_actuacion}"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(endpoint, timeout=30, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching documents for actuacion {id_reg_actuacion}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error fetching documents for actuacion {id_reg_actuacion}: {req_err}")
    return None

def descargar_documento_actuacion(id_reg_documento: str) -> bytes | None:
    """
    Downloads a specific document associated with a judicial action.

    Args:
        id_reg_documento: The unique identifier of the document registration.

    Returns:
        The binary content of the document or None if an error occurs.
    """
    endpoint = f"{BASE_URL}/Descarga/Documento/{id_reg_documento}"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(endpoint, timeout=60, headers=headers) # Increased timeout for potentially larger files
        response.raise_for_status()
        return response.content # Return raw bytes for file content
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while downloading document {id_reg_documento}: {http_err} - {response.text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Error downloading document {id_reg_documento}: {req_err}")
    return None

# Example Usage (for testing purposes):
if __name__ == "__main__":
    logging.info("Testing Rama Judicial API client...")

    # Test 1: Consultar procesos por nombre (Example: Falabella, assuming it exists and has less than 1000 results without department filter)
    # For a real test, a known company with few processes or a specific codificacionDespacho would be better.
    # This might return many results or an error if too many, as per API docs.
    # print("\n--- Test: Consultar Procesos por Nombre (Falabella) ---")
    # procesos = consultar_procesos_por_nombre(nombre="Falabella", codificacion_despacho="05001") # Example for Medellín
    # if procesos and procesos.get("procesos"):
    #     print(f"Found {len(procesos['procesos'])} processes.")
    #     for proceso in procesos["procesos"][:2]: # Print first 2 processes
    #         print(f"  ID Proceso: {proceso.get('idProceso')}, Demandante: {proceso.get('demandante')}, Demandado: {proceso.get('demandado')}")
    #         # Store one idProceso for next tests
    #         if 'test_id_proceso' not in locals() and proceso.get('idProceso'):
    #             test_id_proceso = str(proceso.get('idProceso'))
    # elif procesos:
    #     print("Procesos response:", procesos) # Print the raw response if 'procesos' key is not found
    # else:
    #     print("No processes found or error occurred.")

    # Use a known test idProceso if the above search doesn't yield one or for consistent testing
    # The ID "198167821" is from the Reto1.txt example for Proceso/Detalle
    test_id_proceso_static = "198167821" 

    print(f"\n--- Test: Consultar Detalle del Proceso ({test_id_proceso_static}) ---")
    detalle = consultar_detalle_proceso(test_id_proceso_static)
    if detalle:
        # print("Detalle del proceso:", detalle) # Full detail can be verbose
        print(f"  Tipo de Proceso: {detalle.get('tipoProceso')}")
        print(f"  Clase de Proceso: {detalle.get('claseProceso')}")
        print(f"  Ubicación Expediente: {detalle.get('ubicacion')}")
    else:
        print(f"No details found for process {test_id_proceso_static} or error occurred.")

    print(f"\n--- Test: Consultar Actuaciones del Proceso ({test_id_proceso_static}) ---")
    actuaciones_data = consultar_actuaciones_proceso(test_id_proceso_static)
    if actuaciones_data:
        # The structure of actuaciones_data needs to be inspected from an actual API call.
        # Assuming it's a list of actuaciones directly or a dict with a key like 'actuaciones'
        if isinstance(actuaciones_data, list):
            actuaciones_list = actuaciones_data
        elif isinstance(actuaciones_data, dict) and 'actuaciones' in actuaciones_data:
            actuaciones_list = actuaciones_data['actuaciones']
        else:
            actuaciones_list = [] # Or handle as an unexpected format
            logging.warning(f"Unexpected format for actuaciones: {type(actuaciones_data)}")

        if actuaciones_list:
            print(f"Found {len(actuaciones_list)} actuaciones.")
            for actuacion in actuaciones_list[:3]: # Print first 3 actuaciones
                print(f"  Fecha: {actuacion.get('fechaActuacion')}, Actuación: {actuacion.get('actuacion')}, Anotación: {actuacion.get('anotacion', '')[:50]}...")
        else:
            print("No actuaciones found in the response or unexpected format.")
    else:
        print(f"No actuaciones found for process {test_id_proceso_static} or error occurred.")

    # Test new functions
    test_numero_radicacion = "05001418900820250032700"
    print(f"\\n--- Test: Consultar Procesos por Número de Radicación ({test_numero_radicacion}) ---")
    proceso_rad = consultar_procesos_por_numero_radicacion(test_numero_radicacion)
    if proceso_rad and proceso_rad.get("procesos"):
        print(f"Found {len(proceso_rad['procesos'])} process(es).")
        for p in proceso_rad["procesos"][:1]:
             print(f"  ID Proceso: {p.get('idProceso')}, Demandante: {p.get('Demandante/accionante')}, Demandado: {p.get('Demandado/indiciado/causante')}")
    elif proceso_rad:
        print("Proceso por radicado response:", proceso_rad)
    else:
        print(f"No proceso found for radicado {test_numero_radicacion} or error occurred.")

    test_id_reg_actuacion_docs = "1715845581" # Example from prompt
    print(f"\\n--- Test: Consultar Documentos de Actuación ({test_id_reg_actuacion_docs}) ---")
    documentos_actuacion = consultar_documentos_actuacion(test_id_reg_actuacion_docs)
    test_id_reg_documento_descarga = None
    if documentos_actuacion and isinstance(documentos_actuacion, list) and documentos_actuacion:
        print(f"Found {len(documentos_actuacion)} documento(s) for actuación {test_id_reg_actuacion_docs}.")
        for doc in documentos_actuacion[:1]: # Print first document info
            print(f"  Nombre: {doc.get('nombre')}, ID Reg Documento: {doc.get('idRegDocumento')}, Descripcion: {doc.get('descripcion')}")
            if 'idRegDocumento' in doc and not test_id_reg_documento_descarga:
                test_id_reg_documento_descarga = str(doc.get('idRegDocumento'))
    elif documentos_actuacion:
         print("Documentos actuación response:", documentos_actuacion) # Print raw response
    else:
        print(f"No documents found for actuación {test_id_reg_actuacion_docs} or error occurred.")

    if test_id_reg_documento_descarga:
        print(f"\\n--- Test: Descargar Documento ({test_id_reg_documento_descarga}) ---")
        documento_contenido = descargar_documento_actuacion(test_id_reg_documento_descarga)
        if documento_contenido:
            print(f"Documento descargado. Tamaño: {len(documento_contenido)} bytes.")
            #Example: Save the document
            try:
                with open(f"documento_{test_id_reg_documento_descarga}.pdf", "wb") as f: # Assuming PDF
                    f.write(documento_contenido)
                print(f"Documento guardado como documento_{test_id_reg_documento_descarga}.pdf")
            except IOError as e:
                print(f"Error al guardar el documento: {e}")
        else:
            print(f"No se pudo descargar el documento {test_id_reg_documento_descarga} or error occurred.")
    else:
        print("\\nSkipping Test: Descargar Documento - No idRegDocumento available from previous step.")
    
    logging.info("Finished testing Rama Judicial API client.")
