// Global i18next type augmentation.
// Ensures t() returns plain strings (not `string | object | null`) so it can be
// used directly as React children without TS2322 errors.
import 'i18next'

declare module 'i18next' {
  interface CustomTypeOptions {
    returnNull: false
    returnObjects: false
  }
}
