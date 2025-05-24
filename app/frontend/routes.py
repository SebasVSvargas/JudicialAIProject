from flask import Blueprint, render_template, request, redirect, url_for
from app.clients.rama_judicial_client import (

    consultar_procesos_por_nombre,
    consultar_detalle_proceso,
    consultar_actuaciones_proceso
)



main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo_persona = request.form.get('tipo_persona', 'jur')
        # Checkbox returns 'on' if checked
        solo_activos = True if request.form.get('solo_activos') == 'on' else False
        codificacion_despacho = request.form.get('codificacion_despacho') or None
        pagina = 1
        return redirect(url_for('main.procesos', nombre=nombre,
                                tipo_persona=tipo_persona,
                                solo_activos=solo_activos,
                                codificacion_despacho=codificacion_despacho,
                                pagina=pagina))
    return render_template('index.html')

@main_bp.route('/procesos')
def procesos():
    nombre = request.args.get('nombre')
    tipo_persona = request.args.get('tipo_persona', 'jur')
    solo_activos = request.args.get('solo_activos', 'True') == 'True'
    codificacion_despacho = request.args.get('codificacion_despacho') or None
    pagina = int(request.args.get('pagina', 1))

    data = consultar_procesos_por_nombre(
        nombre,
        tipo_persona=tipo_persona,
        solo_activos=solo_activos,
        codificacion_despacho=codificacion_despacho,
        pagina=pagina
    )

    procesos = []
    if data and "procesos" in data:
        for p in data["procesos"]:
            sujetos = p.get("sujetosProcesales", "")
            demandante = "-"
            demandado = "-"

            partes = sujetos.split("|")
            for parte in partes:
                if "demandante" in parte.lower():
                    demandante = parte.split(":")[1].strip()
                elif "demandado" in parte.lower():
                    demandado = parte.split(":")[1].strip()
            p["demandante"] = demandante
            p["demandado"] = demandado
            procesos.append(p)

    return render_template('procesos.html', nombre=nombre, procesos=procesos)



@main_bp.route('/detalle/<id_proceso>')
def detalle(id_proceso):
    detalles = consultar_detalle_proceso(id_proceso)
    return render_template('detalle.html', detalles=detalles)

@main_bp.route('/actuaciones/<id_proceso>')
def actuaciones(id_proceso):
    detalles = consultar_detalle_proceso(id_proceso)
    data = consultar_actuaciones_proceso(id_proceso)
    if isinstance(data, list):
        actuaciones = data
    elif isinstance(data, dict) and 'actuaciones' in data:
        actuaciones = data['actuaciones']
    else:
        actuaciones = []
    return render_template('actuaciones.html', detalles=detalles, actuaciones=actuaciones)
