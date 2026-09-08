import json
import uuid
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ActividadForm, CompromisoForm, DelegacionForm, EvidenciaForm
from .models import Actividad, Auditoria, Compromiso, Delegacion, PerfilUsuario

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'


def _perfil(user):
    if not user.is_authenticated:
        return None
    return PerfilUsuario.objects.select_related('delegacion').filter(usuario=user).first()


def _puede_ver_todo(user):
    perfil = _perfil(user)
    return user.is_superuser or perfil and perfil.rol in {'administrador', 'coordinador'}


def _actividades_autorizadas(user):
    queryset = Actividad.objects.select_related('delegacion', 'funcionario')
    if _puede_ver_todo(user):
        return queryset
    perfil = _perfil(user)
    if perfil and perfil.delegacion_id:
        return queryset.filter(delegacion=perfil.delegacion)
    return queryset.filter(funcionario=user)


def _codigo_actividad():
    return f'EVD-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}'


def _load_json(filename):
    file_path = DATA_DIR / filename
    with file_path.open('r', encoding='utf-8') as file:
        return json.load(file)


def _calcular_estado(solicitud):
    estado = solicitud.get('estado', '').strip().lower()
    if estado == 'realizado':
        return 'Realizado', 'success'
    if estado == 'en proceso':
        return 'En proceso', 'primary'
    if estado == 'pendiente':
        fecha_compromiso = datetime.strptime(solicitud.get('fecha_compromiso'), '%Y-%m-%d').date()
        hoy = datetime.now().date()
        if fecha_compromiso < hoy:
            return 'Alerta Roja por Vencimiento', 'danger'
        return 'Pendiente', 'warning'
    return 'Pendiente', 'warning'


def index(request):
    ejes = ['Seguridad', 'DISERCO', 'Gestión Social', 'Organizaciones Comunitarias']
    delegaciones = [
        'Centro', 'Rural', 'La Antena', 'La Pampa', 'Avenida del Mar', 'Las Compañías'
    ]
    solicitudes_data = _load_json('solicitudes.json').get('solicitudes', [])
    metas = _load_json('metas_delegaciones.json').get('delegaciones', [])
    delegaciones = list(Delegacion.objects.filter(activa=True).values_list('nombre', flat=True)) or delegaciones
    return render(request, 'delegaciones_app/index.html', {
        'ejes': ejes,
        'delegaciones': delegaciones,
        'total_solicitudes': len(solicitudes_data),
        'alertas': sum(1 for item in solicitudes_data if item.get('estado') == 'Pendiente'),
        'promedio': round(sum(item.get('cumplimiento', 0) for item in metas) / len(metas), 1) if metas else 0,
    })


def solicitudes(request):
    data = _load_json('solicitudes.json')
    solicitudes_lista = data.get('solicitudes', [])

    for solicitud in solicitudes_lista:
        solicitud['estado_display'], solicitud['estado_class'] = _calcular_estado(solicitud)
        solicitud['fecha_ingreso'] = datetime.strptime(solicitud['fecha_ingreso'], '%Y-%m-%d').strftime('%d-%m-%Y')
        solicitud['fecha_compromiso'] = datetime.strptime(solicitud['fecha_compromiso'], '%Y-%m-%d').strftime('%d-%m-%Y')

    contexto = {
        'solicitudes': solicitudes_lista,
        'total': len(solicitudes_lista),
        'pendientes': sum(1 for item in solicitudes_lista if item['estado_display'] == 'Pendiente'),
        'en_proceso': sum(1 for item in solicitudes_lista if item['estado_display'] == 'En proceso'),
        'alertas': sum(1 for item in solicitudes_lista if item['estado_display'] == 'Alerta Roja por Vencimiento'),
    }
    return render(request, 'delegaciones_app/solicitudes.html', contexto)


def delegacion_detalle(request, nombre):
    data = _load_json('solicitudes.json')
    solicitudes_delegacion = []
    for solicitud in data.get('solicitudes', []):
        if solicitud.get('delegacion') == nombre:
            solicitud['estado_display'], solicitud['estado_class'] = _calcular_estado(solicitud)
            solicitud['fecha_ingreso'] = datetime.strptime(solicitud['fecha_ingreso'], '%Y-%m-%d').strftime('%d-%m-%Y')
            solicitud['fecha_compromiso'] = datetime.strptime(solicitud['fecha_compromiso'], '%Y-%m-%d').strftime('%d-%m-%Y')
            solicitudes_delegacion.append(solicitud)

    return render(request, 'delegaciones_app/delegacion_detalle.html', {
        'nombre': nombre,
        'solicitudes': solicitudes_delegacion,
    })


def actividad_nueva(request):
    if not request.user.is_authenticated:
        return redirect('login')
    form = ActividadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        actividad = form.save(commit=False)
        actividad.funcionario = request.user
        actividad.codigo = _codigo_actividad()
        actividad.estado = 'pendiente'
        actividad.save()
        Auditoria.objects.create(usuario=request.user, accion='crear', entidad='Actividad', identificador=actividad.codigo)
        messages.success(request, f'Actividad creada con código {actividad.codigo}.')
        return redirect('actividad_detalle', actividad.codigo)
    return render(request, 'delegaciones_app/actividad_form.html', {'form': form, 'titulo': 'Registrar actividad'})


@login_required
def actividades(request):
    query = request.GET.get('q', '').strip()
    registros = _actividades_autorizadas(request.user)
    if query:
        registros = registros.filter(Q(codigo__icontains=query) | Q(descripcion__icontains=query) | Q(item_medicion__icontains=query))
    return render(request, 'delegaciones_app/actividades.html', {'actividades': registros, 'query': query, 'puede_crear': request.user.is_authenticated})


@login_required
def actividad_detalle(request, codigo):
    actividad = get_object_or_404(_actividades_autorizadas(request.user), codigo=codigo)
    evidencia_form = EvidenciaForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and evidencia_form.is_valid():
        evidencia = evidencia_form.save(commit=False)
        evidencia.actividad = actividad
        evidencia.save()
        actividad.estado = 'pendiente'
        actividad.save(update_fields=['estado', 'actualizada'])
        Auditoria.objects.create(usuario=request.user, accion='cargar_evidencia', entidad='Actividad', identificador=actividad.codigo)
        messages.success(request, 'Evidencia cargada y enviada a revisión.')
        return redirect('actividad_detalle', codigo=codigo)
    return render(request, 'delegaciones_app/actividad_detalle.html', {'actividad': actividad, 'evidencia_form': evidencia_form, 'puede_validar': _puede_ver_todo(request.user) or _perfil(request.user) and _perfil(request.user).rol == 'verificador'})


@login_required
def revisar_actividad(request, codigo, decision):
    if not (_puede_ver_todo(request.user) or _perfil(request.user) and _perfil(request.user).rol == 'verificador'):
        return redirect('actividad_detalle', codigo=codigo)
    actividad = get_object_or_404(Actividad, codigo=codigo)
    actividad.estado = 'aprobada' if decision == 'aprobar' else 'rechazada'
    actividad.save(update_fields=['estado', 'actualizada'])
    for evidencia in actividad.evidencias.all():
        evidencia.aprobada = decision == 'aprobar'
        evidencia.revisada_por = request.user
        evidencia.save(update_fields=['aprobada', 'revisada_por'])
    Auditoria.objects.create(usuario=request.user, accion=decision, entidad='Actividad', identificador=actividad.codigo)
    messages.success(request, f'Actividad {actividad.codigo}: {actividad.get_estado_display()}.')
    return redirect('actividad_detalle', codigo=codigo)


@login_required
def delegaciones_crud(request):
    if not _puede_ver_todo(request.user):
        return redirect('inicio')
    return render(request, 'delegaciones_app/delegaciones_crud.html', {'delegaciones': Delegacion.objects.all()})


@login_required
def delegacion_form(request, pk=None):
    if not _puede_ver_todo(request.user):
        return redirect('inicio')
    delegacion = get_object_or_404(Delegacion, pk=pk) if pk else None
    form = DelegacionForm(request.POST or None, instance=delegacion)
    if request.method == 'POST' and form.is_valid():
        objeto = form.save()
        Auditoria.objects.create(usuario=request.user, accion='editar' if pk else 'crear', entidad='Delegacion', identificador=str(objeto.pk))
        messages.success(request, 'Delegación guardada correctamente.')
        return redirect('delegaciones_crud')
    return render(request, 'delegaciones_app/delegacion_form.html', {'form': form, 'titulo': 'Editar delegación' if pk else 'Nueva delegación'})


@login_required
def compromiso_nuevo(request):
    form = CompromisoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        compromiso = form.save(commit=False)
        compromiso.folio = f'AGR-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:5].upper()}'
        compromiso.save()
        messages.success(request, f'Compromiso creado con folio {compromiso.folio}.')
        return redirect('agenda')
    return render(request, 'delegaciones_app/compromiso_form.html', {'form': form, 'titulo': 'Nuevo compromiso'})


def agenda(request):
    data = _load_json('solicitudes.json')
    compromisos = []
    for solicitud in data.get('solicitudes', []):
        solicitud['estado_display'], solicitud['estado_class'] = _calcular_estado(solicitud)
        compromisos.append(solicitud)
    return render(request, 'delegaciones_app/agenda.html', {
        'compromisos': compromisos,
        'proximos': sum(1 for item in compromisos if item['estado_display'] == 'Pendiente'),
        'vencidos': sum(1 for item in compromisos if item['estado_display'] == 'Alerta Roja por Vencimiento'),
        'realizados': sum(1 for item in compromisos if item['estado_display'] == 'Realizado'),
    })


def institucional(request):
    delegaciones = [
        ('Avenida del Mar', 'Borde costero, turismo, residencial y servicios', 'Coordinación estacional, espacios públicos, seguridad y prevención.'),
        ('Centro', 'Centro histórico, administrativo, comercial y patrimonial', 'Atención territorial, convivencia urbana y gestión del espacio público.'),
        ('La Antena', 'Sector urbano oriental y barrios asociados', 'Participación vecinal, apoyo social y coordinación de servicios.'),
        ('Las Compañías', 'Sector urbano norte de alta densidad', 'Gestión comunitaria, acceso a programas y operativos sociales.'),
        ('La Pampa', 'Sector urbano sur y áreas residenciales', 'Asistencia social, subsidios, aseo, alumbrado y plazas.'),
        ('Rural', 'Localidades y comunidades rurales dispersas', 'Acercamiento de servicios, emergencias y coordinación intersectorial.'),
    ]
    return render(request, 'delegaciones_app/institucional.html', {
        'delegaciones': delegaciones,
        'poblacion': '250.141',
        'urbano': '89,14 %',
        'rural': '10,86 %',
    })
