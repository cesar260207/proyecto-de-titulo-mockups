import json
from datetime import datetime
from pathlib import Path

from django.shortcuts import render

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


def dashboard(request):
    data = _load_json('metas_delegaciones.json')
    delegaciones = data.get('delegaciones', [])
    for delegacion in delegaciones:
        delegacion['estado'], delegacion['estado_class'] = _color_porcentaje(delegacion.get('cumplimiento', 0))
        delegacion['dias_desde_registro'] = _dias_desde_ultimo_registro(delegacion['ultimos_datos'])
    return render(request, 'gestion_app/dashboard.html', {'delegaciones': delegaciones})


def semaforo(request):
    data = _load_json('metas_delegaciones.json')
    delegaciones = data.get('delegaciones', [])
    for delegacion in delegaciones:
        delegacion['estado'], delegacion['estado_class'] = _color_porcentaje(delegacion.get('cumplimiento', 0))
        delegacion['dias_desde_registro'] = _dias_desde_ultimo_registro(delegacion['ultimos_datos'])
    return render(request, 'gestion_app/semaforo.html', {'delegaciones': delegaciones})


def resumen(request):
    data = _load_json('metas_delegaciones.json')
    delegaciones = data.get('delegaciones', [])

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
