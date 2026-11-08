from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def solo_administradores(vista):
    """Permite entrar solo a usuarios administradores (is_staff).

    Sin sesión → se redirige al inicio de sesión.
    Con sesión pero sin permiso → «403 acceso denegado».
    """

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return vista(request, *args, **kwargs)

    return login_required(envoltura)
