# SGR La Serena

Prototipo funcional del Sistema de Gestion de Resultados para las Delegaciones Municipales de La Serena.

## Incluye

- Dashboard territorial, agenda y semaforo de cumplimiento.
- Autenticacion Django y perfiles por rol.
- CRUD de delegaciones para administradores y coordinadores.
- Registro persistente de actividades con codigo unico.
- Carga de evidencias y flujo de aprobacion/rechazo.
- Compromisos colectivos y auditoria de operaciones criticas.
- Filtrado de actividades por delegacion autorizada.
- Datos ficticios para demostracion.

## Instalacion local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install django
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`.

## Cuentas demo

Todas usan la clave `Demo2026!`:

| Usuario | Rol | Ambito |
|---|---|---|
| `admin.demo` | Administrador | Todas las delegaciones |
| `coordinador.demo` | Coordinador | Todas las delegaciones |
| `funcionario.centro` | Funcionario | Centro |
| `verificador.demo` | Verificador | Revision de evidencias |

Los datos son sinteticos y solo sirven para demostracion academica.

## Rutas principales

- `/`: portada SGR.
- `/login/`: inicio de sesion.
- `/actividades/`: actividades autorizadas.
- `/actividad/nueva/`: registro persistente.
- `/agenda/`: compromisos y agenda.
- `/administracion/delegaciones/`: CRUD de delegaciones para roles autorizados.
- `/admin/`: administracion completa de Django.
- `/gestion/`: medicion y cumplimiento.
- `/territorio/`: contexto institucional.

## Validacion

```powershell
python manage.py check
python manage.py test
```
