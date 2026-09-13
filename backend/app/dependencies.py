from .auth.security import (
    get_current_user as get_current_user,
    require_company as require_company,
    # GA-REM-002: la autorización se re-exporta junto a la autenticación a propósito.
    # Son el mismo punto de entrada para los routers, y mantenerlas separadas invitaba a
    # importar una y olvidar la otra: así estaban las 78 rutas antes de esta Wave.
    require_permission as require_permission,
    tiene_permiso as tiene_permiso,
)
