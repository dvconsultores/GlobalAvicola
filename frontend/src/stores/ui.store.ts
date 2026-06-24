import { create } from 'zustand'

export type SidebarMode = 'expanded' | 'collapsed'
export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface ToastMessage {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface UiState {
  // Sidebar
  sidebarMode: SidebarMode
  toggleSidebar: () => void
  setSidebarMode: (mode: SidebarMode) => void

  // Mobile drawer
  isDrawerOpen: boolean
  openDrawer: () => void
  closeDrawer: () => void
  toggleDrawer: () => void

  // Loading overlay (for page-level loading)
  isPageLoading: boolean
  setPageLoading: (loading: boolean) => void

  // Toast notifications (complementary to Toast component)
  toasts: ToastMessage[]
  addToast: (toast: Omit<ToastMessage, 'id'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

let toastCounter = 0

export const useUiStore = create<UiState>((set) => ({
  // Sidebar
  sidebarMode: 'expanded',
  toggleSidebar: () => set((s) => ({ sidebarMode: s.sidebarMode === 'expanded' ? 'collapsed' : 'expanded' })),
  setSidebarMode: (mode) => set({ sidebarMode: mode }),

  // Mobile drawer
  isDrawerOpen: false,
  openDrawer: () => set({ isDrawerOpen: true }),
  closeDrawer: () => set({ isDrawerOpen: false }),
  toggleDrawer: () => set((s) => ({ isDrawerOpen: !s.isDrawerOpen })),

  // Loading
  isPageLoading: false,
  setPageLoading: (loading) => set({ isPageLoading: loading }),

  // Toasts
  toasts: [],
  addToast: (toast) => {
    const id = `toast-${++toastCounter}`
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }))
    // Auto-remove after duration
    const duration = toast.duration ?? 4000
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
    }, duration)
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  clearToasts: () => set({ toasts: [] }),
}))
