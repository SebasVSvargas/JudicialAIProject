# Judicial AI Process Explorer

## Descripción

Judicial AI Process Explorer es una aplicación web desarrollada en Python con Streamlit que permite a los usuarios buscar y explorar procesos judiciales de Colombia. La aplicación interactúa con la API pública de la Rama Judicial para obtener datos de procesos y utiliza modelos de Inteligencia Artificial (Google Gemini) para generar resúmenes concisos de las actuaciones y clasificarlas según su urgencia. La información procesada se almacena en una base de datos SQLite local para un acceso rápido y eficiente en consultas posteriores.

## Características Principales

*   **Búsqueda de Procesos Judiciales**: Permite buscar procesos por nombre o razón social del demandante/demandado y, opcionalmente, por código de despacho.
*   **Visualización Detallada**: Muestra información completa del proceso seleccionado.
*   **Resúmenes con IA**: Genera automáticamente resúmenes de las anotaciones de cada actuación judicial utilizando un modelo de lenguaje grande (LLM).
*   **Clasificación de Urgencia con IA**: Clasifica cada actuación según su nivel de urgencia (ALTA, MEDIA, BAJA) mediante IA.
*   **Interfaz Amigable**: Interfaz de usuario web intuitiva construida con Streamlit.
*   **Persistencia de Datos**: Almacena los procesos y actuaciones consultadas en una base de datos SQLite local para optimizar búsquedas futuras y reducir la carga a la API externa.

## Tecnologías Utilizadas

*   **Lenguaje de Programación**: Python 3.x
*   **Framework Web**: Streamlit
*   **Base de Datos**: SQLite
*   **Inteligencia Artificial**: Google Generative AI (Gemini)
*   **Interacción API**: `requests` para llamadas HTTP
*   **Modelado de Datos**: Pydantic
*   **Gestión de Entorno**: `python-dotenv`

## Configuración e Instalación

Siga estos pasos para configurar y ejecutar el proyecto en su entorno local:

1.  **Clonar el Repositorio**
    ```bash
    git clone <URL_DEL_REPOSITORIO_GIT>
    cd JudicialAIProject
    ```

2.  **Crear y Activar un Entorno Virtual**
    Se recomienda utilizar un entorno virtual para gestionar las dependencias del proyecto.
    ```bash
    python -m venv entornov
    ```
    Para activar el entorno:
    *   **Windows (PowerShell):**
        ```powershell
        .\entornov\Scripts\Activate.ps1
        ```
    *   **Windows (CMD):**
        ```cmd
        entornov\Scripts\activate.bat
        ```
    *   **Linux/macOS:**
        ```bash
        source entornov/bin/activate
        ```

3.  **Instalar Dependencias**
    Asegúrese de que su entorno virtual esté activado y luego instale las dependencias listadas en `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno**
    La aplicación utiliza una API Key de Google para los servicios de IA. Deberá crear un archivo llamado `.env` en el directorio raíz del proyecto (`JudicialAIProject/`) con el siguiente contenido:

    ```env
    GOOGLE_API_KEY="SU_GOOGLE_API_KEY_AQUI"
    ```
    Reemplace `"SU_GOOGLE_API_KEY_AQUI"` con su clave API real de Google Generative AI.

## Uso

Una vez completada la configuración:

1.  Asegúrese de que su entorno virtual esté activado.
2.  Navegue al directorio raíz del proyecto (`JudicialAIProject/`) si aún no está allí.
3.  Ejecute la aplicación Streamlit con el siguiente comando:
    ```bash
    streamlit run JudicialAIProject/app.py
    ```
    Esto iniciará la aplicación y la abrirá en su navegador web predeterminado.

## Estructura del Proyecto

```
JudicialAIProject/
├── .env                  # Variables de entorno (creado por el usuario)
├── app.py                # Punto de entrada principal de la aplicación Streamlit
├── requirements.txt      # Dependencias de Python
├── LICENSE               # Licencia del proyecto
├── docs/                 # Documentación adicional
│   └── WORKFLOW_SUMMARY.md # Resumen del flujo de trabajo
├── entornov/             # Directorio del entorno virtual (si se crea aquí)
├── JudicialAIProject/    # Módulo principal de la aplicación
│   ├── __init__.py
│   ├── app.py            # (Parece haber una duplicación o un archivo principal aquí también, verificar)
│   ├── Main.py           # (Propósito a determinar, podría ser un script alternativo)
│   ├── app/              # Lógica central de la aplicación
│   │   ├── __init__.py
│   │   ├── clients/      # Clientes para APIs externas (ej. Rama Judicial)
│   │   ├── config/       # Configuraciones (ej. LLM)
│   │   ├── db/           # Módulos de base de datos (SQLite, CRUD)
│   │   ├── models/       # Modelos Pydantic
│   │   └── services/     # Servicios de IA (resumen, clasificación)
│   ├── data/
│   │   └── judicial_data.sqlite # Base de datos SQLite
│   └── docs/             # Documentos específicos del módulo (si aplica)
└── README.md             # Este archivo
```
*(Nota: La estructura del proyecto puede tener variaciones menores. El archivo `JudicialAIProject/app.py` parece ser el punto de entrada principal según el flujo de trabajo.)*

## Contribuciones

Las contribuciones son bienvenidas. Si desea contribuir, por favor haga un fork del repositorio, cree una nueva rama para sus cambios y envíe un Pull Request.

## Licencia

Este proyecto está bajo la licencia especificada en el archivo `LICENSE`.
