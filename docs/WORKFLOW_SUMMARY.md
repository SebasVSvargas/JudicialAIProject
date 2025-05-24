# Flujo de Trabajo General de la Aplicación "Judicial AI Process Explorer"

El flujo de trabajo general de la aplicación "Judicial AI Process Explorer" es el siguiente:

1.  **Inicio y Configuración**:
    *   La aplicación se inicia utilizando Streamlit, como se define en `app.py`.
    *   Al arrancar, se asegura de que la base de datos SQLite (`data/judicial_data.sqlite`) y las tablas necesarias (`proceso`, `actuacion`) estén creadas. Esto se maneja en `app/db/database.py` a través de la función `create_db_and_tables`.

2.  **Búsqueda de Procesos Judiciales**:
    *   El usuario introduce un nombre o razón social (y opcionalmente un código de despacho) en la barra lateral de la interfaz de Streamlit.
    *   Al hacer clic en "Buscar Procesos", la aplicación llama a la función `consultar_procesos_por_nombre` del módulo `app/clients/rama_judicial_client.py`.
    *   Esta función realiza una petición HTTP GET a la API pública de la Rama Judicial para obtener una lista de procesos que coincidan con el criterio de búsqueda.
    *   Los resultados de la búsqueda se almacenan en el estado de la sesión de Streamlit (`st.session_state.search_results`).

3.  **Selección de un Proceso**:
    *   Si la búsqueda devuelve procesos, estos se muestran en un menú desplegable en la interfaz principal.
    *   El usuario selecciona un proceso específico de la lista. El `idProceso` (identificador único de la Rama Judicial) del proceso seleccionado se guarda en `st.session_state.selected_proceso_id`.

4.  **Obtención y Procesamiento de Detalles y Actuaciones del Proceso**:
    *   Una vez seleccionado un proceso, la aplicación verifica si este ya existe en la base de datos local utilizando `crud.get_proceso_by_idrama` desde `app/db/crud.py`.
    *   **Si el proceso no está en la base de datos (primera vez que se consulta)**:
        *   Se obtienen los detalles completos del proceso desde la API de la Rama Judicial usando `consultar_detalle_proceso` (`app/clients/rama_judicial_client.py`).
        *   Los datos del proceso se mapean a un modelo Pydantic `Proceso` (`app/models/models.py`) y se guardan en la tabla `proceso` de la base de datos mediante `crud.create_proceso` (`app/db/crud.py`).
        *   A continuación, se obtienen todas las actuaciones (actualizaciones) asociadas a ese proceso desde la API usando `consultar_actuaciones_proceso` (`app/clients/rama_judicial_client.py`).
        *   Para cada actuación:
            *   Se genera un resumen del texto de la anotación utilizando el servicio de IA `generar_resumen_actuacion` (`app/services/ai_services.py`). Este servicio utiliza un modelo de lenguaje grande (LLM) configurado en `app/config/llm_config.py` (actualmente Google Gemini).
            *   Se clasifica la urgencia de la actuación (ALTA, MEDIA, BAJA) utilizando el servicio de IA `clasificar_urgencia_actuacion` (`app/services/ai_services.py`).
            *   Los datos de la actuación, junto con el resumen y la clasificación de IA, se mapean a un modelo Pydantic `Actuacion` (`app/models/models.py`) y se guardan en la tabla `actuacion` de la base de datos mediante `crud.create_actuacion` (`app/db/crud.py`), vinculándola al proceso padre.
    *   **Si el proceso ya está en la base de datos (o después de ser guardado)**:
        *   Se recuperan los detalles del proceso y sus actuaciones directamente desde la base de datos local utilizando las funciones de `app/db/crud.py`.

5.  **Visualización de la Información**:
    *   Los detalles del proceso seleccionado (obtenidos de la API o de la base de datos) se muestran en la interfaz de Streamlit.
    *   Las actuaciones del proceso, incluyendo la anotación original, el resumen generado por IA y la clasificación de urgencia, se muestran en expanders. La urgencia se resalta con colores.

6.  **Servicios de Inteligencia Artificial (IA)**:
    *   El módulo `app/services/ai_services.py` define las funciones que interactúan con el LLM. Utiliza plantillas de prompts para guiar al modelo en la generación de resúmenes y clasificaciones.
    *   La configuración del LLM (actualmente Google Gemini) se gestiona en `app/config/llm_config.py`, que carga la API key desde un archivo `.env`.

7.  **Persistencia de Datos**:
    *   La aplicación utiliza una base de datos SQLite para almacenar la información de los procesos y actuaciones que ya han sido consultados y procesados. Esto evita tener que llamar repetidamente a la API de la Rama Judicial y reprocesar con IA la misma información, agilizando consultas futuras. Las operaciones CRUD (Crear, Leer, Actualizar, Borrar) se manejan en `app/db/crud.py`.

En resumen, la aplicación actúa como un intermediario inteligente entre el usuario y la API de la Rama Judicial. Busca procesos, los enriquece con resúmenes y clasificaciones de urgencia mediante IA, y almacena esta información procesada en una base de datos local para una visualización rápida y eficiente.
