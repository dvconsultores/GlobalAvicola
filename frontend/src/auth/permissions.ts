/**
 * GA-FE-02 · Helper mínimo de permisos — espejo EXACTO de `tiene_permiso`
 * (`backend/app/auth/security.py:199-230`): comodín del actor global, permiso exacto,
 * y comodín de módulo `*:accion`.
 *
 * Frontera declarada: esto es lo MÍNIMO para las superficies de GA-FE-02. La navegación
 * dinámica global y el cierre completo de `R-98`/`R-119` pertenecen a `GA-FE-03` y NO se
 * implementan aquí.
 */

export interface SessionLike {
  is_super_admin?: boolean | null
  permissions?: string[] | null
}

export function hasPermission(session: SessionLike | null | undefined, permission: string): boolean {
  if (!session) return false
  if (session.is_super_admin) return true
  const list = session.permissions ?? []
  if (list.includes(permission)) return true
  const action = permission.split(':')[1]
  if (!action) return false
  return list.includes(`*:${action}`)
}
