/**
 * SPEC 013 · AC-SS-01/AC-SS-02 · cableado de sesión entre `api.ts` y el store.
 *
 * Único punto que conecta el transporte con la sesión:
 * - accesores de token en memoria (S-01/S-02), y
 * - tras un refresh automático, `setTokens` + rehidratación desde `/me` (AC-SS-01): el token
 *   sólo aporta `role_id`/`view_type`, así que la sesión extendida se vuelve a leer del
 *   backend para que permisos, unidades y menús no se degraden a los ~30 min.
 * - ante un `403`, rehidratación acotada por `api.ts` (AC-SS-02).
 */
import { registerForbiddenHandler, registerTokenAccessors } from './api'
import { useAuthStore } from '../stores/auth.store'

export function wireSession(): void {
  registerTokenAccessors(
    () => useAuthStore.getState().token,
    () => useAuthStore.getState().refreshToken,
    (access, refresh) => {
      useAuthStore.getState().setTokens(access, refresh)
      // AC-SS-01: el refresh rota el token; la verdad del contexto sigue en `/me`.
      void useAuthStore.getState().fetchMe()
    },
    () => useAuthStore.getState().logout(),
  )
  // AC-SS-02: el throttle (1/30 s y nunca en rutas de sesión) vive en `api.ts`.
  registerForbiddenHandler(() => {
    void useAuthStore.getState().fetchMe()
  })
}
