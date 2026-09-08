import json
from datetime import datetime
from pathlib import Path

from django.shortcuts import render

from delegaciones_app.models import MetaMedicion

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'


def _load_json(filename):
    file_path = DATA_DIR / filename
    with file_path.open('r', encoding='utf-8') as file:
        return json.load(file)


def _dias_desde_ultimo_registro(fecha_texto):
    fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
    return (datetime.now().date() - fecha).days


def _color_porcentaje(cumplimiento):
    if cumplimiento >= 80:
        return 'Verde', 'success'
    if cumplimiento >= 65:
        return 'Amarillo', 'warning'
    return 'Rojo', 'danger'


def _metas_persistentes():
    metas = list(MetaMedicion.objects.select_related('delegacion').filter(activa=True))
    resultado = []
    for meta in metas:
        cumplimiento = round(meta.cumplimiento, 2)
        estado, estado_class = _color_porcentaje(cumplimiento)
        resultado.append({
            'nombre': meta.delegacion.nombre,
            'cumplimiento': cumplimiento,
            'meta': meta.objetivo,
            'ultimos_datos': meta.periodo_termino,
            'estado': estado,
            'estado_class': estado_class,
            'dias_desde_registro': 0,
            'observacion': f'{meta.nombre}: {meta.avance_calculado} actividades aprobadas.',
        })
    return resultado


def _datos_medicion():
    persistentes = _metas_persistentes()
    if persistentes:
        return persistentes
    data = _load_json('metas_delegaciones.json')
    delegaciones = data.get('delegaciones', [])
    for delegacion in delegaciones:
        delegacion['estado'], delegacion['estado_class'] = _color_porcentaje(delegacion.get('cumplimiento', 0))
        delegacion['dias_desde_registro'] = _dias_desde_ultimo_registro(delegacion['ultimos_datos'])
    return delegaciones


def dashboard(request):
    return render(request, 'gestion_app/dashboard.html', {'delegaciones': _datos_medicion()})


def semaforo(request):
    return render(request, 'gestion_app/semaforo.html', {'delegaciones': _datos_medicion()})


def resumen(request):
    delegaciones = _datos_medicion()

    total = 0
    for item in delegaciones:
        total += item.get('cumplimiento', 0)
    promedio = round(total / len(delegaciones), 2) if delegaciones else 0
    mejor = max(delegaciones, key=lambda x: x.get('cumplimiento', 0), default={})
    critico = min(delegaciones, key=lambda x: x.get('cumplimiento', 0), default={})

    return render(request, 'gestion_app/resumen.html', {
        'promedio': promedio,
        'mejor': mejor,
        'critico': critico,
        'delegaciones': delegaciones,
    })
