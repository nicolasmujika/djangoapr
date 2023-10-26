from functools import wraps
from django.shortcuts import render

def user_type_required(user_types):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.usuario_tipo in user_types:
                return view_func(request, *args, **kwargs)
            else:
                # Redirige o muestra un mensaje de error personalizado, según tu necesidad.
                return render(request, "volver.html")
        return _wrapped_view
    return decorator


