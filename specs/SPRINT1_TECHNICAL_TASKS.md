# DESGLOSE TÉCNICO SPRINT 1 — Global Avícola

**Documento:** SPRINT1_TECHNICAL_TASKS.md  
**Versión:** 1.0.0  
**Período:** Jun 24 - Jul 8 (2 semanas)  
**Objetivo:** Sentar arquitectura para vistas diferenciadas Mobile/Web

---

## ORGANIZACIÓN

### Team Assignments (SPRINT 1)

```
FRONTEND (7 people)
├── Frontend Lead (coordinates)
├── Senior Frontend Dev #1 (Components + Architecture)
├── Senior Frontend Dev #2 (State Management)
├── Frontend Dev #1 (Mobile screens)
├── Frontend Dev #2 (Web screens)
├── UI/UX Designer (Figma + Design system)
└── Junior Frontend Dev (Styling, minor fixes)

BACKEND (5 people)
├── Backend Lead (coordinates, reviews)
├── Senior Backend Dev (Operations endpoints)
├── Backend Dev #1 (Operations service)
├── Backend Dev #2 (Database design review)
└── DBA/Database Architect (EggBatch/ChickBatch design)

QA (2 people)
├── QA Lead (Test plan, infrastructure)
└── QA Dev (Playwright setup, initial scenarios)

PRODUCT (1 person)
└── Product Manager (Requirements clarification, priority calls)
```

---

## TAREAS DETALLADAS

### TAREA T-F101: Arquitectura Mobile vs Web

**Prioridad:** CRÍTICA (Bloqueador)  
**Complejidad:** MEDIA  
**Duración:** 3 días (18 horas)  
**Asignado a:** Frontend Lead + Senior Frontend Dev #1  
**Dependencias:** Ninguna  

#### Descripción

Crear la estructura base que permite que la aplicación React ofrezca experiencias diferentes para móvil y web. Esto incluye:
1. Hook personalizado `useResponsive()` para detectar viewport y role
2. Componentes shell (`MobileShell`, `WebShell`) 
3. Routing condicional basado en viewport/role
4. Actualizar `App.tsx` para usar nueva estructura

#### Tareas Sub-task

**T-F101.1: Crear hook useResponsive.ts**

**Archivo nuevo:** `frontend/src/hooks/useResponsive.ts`

```typescript
// useResponsive.ts
import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'

export interface ResponsiveConfig {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  role?: string
  canUseBoth: boolean
}

export function useResponsive(): ResponsiveConfig {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  const [isTablet, setIsTablet] = useState(
    window.innerWidth >= 768 && window.innerWidth < 1024
  )
  const [isDesktop, setIsDesktop] = useState(window.innerWidth >= 1024)
  
  const { role } = useAuth() // Obtener del contexto de auth
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
      setIsDesktop(width >= 1024)
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  
  // Operadores siempre ven mobile, otros ven según viewport
  const showMobileUI = isMobile || role === 'operador'
  const showWebUI = isDesktop || (role !== 'operador' && !isMobile)
  
  return {
    isMobile,
    isTablet,
    isDesktop,
    role,
    canUseBoth: role === 'admin' || role === 'supervisor', // Algunos roles pueden usar ambas
  }
}
```

**Criterios de Aceptación:**
- ✅ Hook retorna valores correctos al cambiar viewport
- ✅ React DevTools muestra hook sin errores
- ✅ Performance: no hay re-renders excesivos

---

**T-F101.2: Crear componentes MobileShell y WebShell**

**Archivos nuevos:**
- `frontend/src/components/layouts/MobileShell.tsx`
- `frontend/src/components/layouts/WebShell.tsx`

```typescript
// MobileShell.tsx
import React from 'react'
import { Outlet } from 'react-router-dom'
import MobileHeader from '../mobile/MobileHeader'
import MobileBottomNav from '../mobile/MobileBottomNav'
import MobileHamburger from '../mobile/MobileHamburger'

export default function MobileShell() {
  const [hamburgerOpen, setHamburgerOpen] = React.useState(false)
  
  return (
    <div className="flex flex-col h-screen bg-slate-50">
      <MobileHeader onHamburgerClick={() => setHamburgerOpen(!hamburgerOpen)} />
      
      <main className="flex-1 overflow-auto pb-16">
        <Outlet />
      </main>
      
      <MobileBottomNav />
      
      {hamburgerOpen && (
        <MobileHamburger onClose={() => setHamburgerOpen(false)} />
      )}
    </div>
  )
}
```

```typescript
// WebShell.tsx
import React from 'react'
import { Outlet } from 'react-router-dom'
import WebSidebar from '../web/WebSidebar'
import WebHeader from '../web/WebHeader'

export default function WebShell() {
  return (
    <div className="flex h-screen bg-white">
      <WebSidebar />
      
      <div className="flex flex-col flex-1">
        <WebHeader />
        
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

**Criterios de Aceptación:**
- ✅ MobileShell renderea sin errores en viewport < 768px
- ✅ WebShell renderea sin errores en viewport >= 768px
- ✅ Outlet funciona (routing anidado)
- ✅ Layouts no hacen flickering al cambiar

---

**T-F101.3: Actualizar App.tsx con routing condicional**

**Archivo a actualizar:** `frontend/src/App.tsx`

```typescript
// App.tsx (simplified, excerpt)
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useResponsive } from './hooks/useResponsive'
import LoginPage from './pages/LoginPage'
import MobileShell from './components/layouts/MobileShell'
import WebShell from './components/layouts/WebShell'

// Mobile routes
import MobileHome from './pages/mobile/home'
import MobileRegister from './pages/mobile/register'
import MobilePending from './pages/mobile/pending'
import MobileLot from './pages/mobile/lot'
import MobileProfile from './pages/mobile/profile'

// Web routes
import WebDashboard from './pages/web/dashboard'
import WebReview from './pages/web/review'
import WebApproval from './pages/web/approval'
import WebLots from './pages/web/lots'
import WebReports from './pages/web/reports'
import WebMasters from './pages/web/masters'

export default function App() {
  const { isMobile } = useResponsive()
  
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth (común para todos) */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Mobile Routes (< 768px) */}
        {isMobile && (
          <Route path="/" element={<MobileShell />}>
            <Route index element={<MobileHome />} />
            <Route path="register/*" element={<MobileRegister />} />
            <Route path="pending" element={<MobilePending />} />
            <Route path="lot/:id" element={<MobileLot />} />
            <Route path="profile" element={<MobileProfile />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Route>
        )}
        
        {/* Web Routes (>= 768px) */}
        {!isMobile && (
          <Route path="/" element={<WebShell />}>
            <Route index element={<WebDashboard />} />
            <Route path="review/*" element={<WebReview />} />
            <Route path="approval/*" element={<WebApproval />} />
            <Route path="lots/*" element={<WebLots />} />
            <Route path="reports/*" element={<WebReports />} />
            <Route path="masters/*" element={<WebMasters />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Route>
        )}
      </Routes>
    </BrowserRouter>
  )
}
```

**Criterios de Aceptación:**
- ✅ Viewport < 768px → router mobile activo
- ✅ Viewport >= 768px → router web activo
- ✅ No hay warnings en console
- ✅ Resize browser → layouts cambian correctamente

---

#### Testing (T-F101)

**Playwright test:**

```typescript
// e2e/routing.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Responsive Routing', () => {
  test('mobile viewport shows mobile shell', async ({ page }) => {
    page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    
    // Verificar que MobileBottomNav está presente
    await expect(page.locator('[data-testid="mobile-bottom-nav"]')).toBeVisible()
    
    // Verificar que WebSidebar NO está presente
    await expect(page.locator('[data-testid="web-sidebar"]')).not.toBeVisible()
  })
  
  test('desktop viewport shows web shell', async ({ page }) => {
    page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')
    
    // Verificar que WebSidebar está presente
    await expect(page.locator('[data-testid="web-sidebar"]')).toBeVisible()
    
    // Verificar que MobileBottomNav NO está presente
    await expect(page.locator('[data-testid="mobile-bottom-nav"]')).not.toBeVisible()
  })
  
  test('resize changes layouts', async ({ page }) => {
    await page.goto('/')
    
    // Empezar en mobile
    page.setViewportSize({ width: 375, height: 667 })
    await expect(page.locator('[data-testid="mobile-bottom-nav"]')).toBeVisible()
    
    // Cambiar a desktop
    page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.locator('[data-testid="web-sidebar"]')).toBeVisible()
  })
})
```

**Criterios de Aceptación:**
- ✅ Todos los tests pasan

---

### TAREA T-F102: Crear Componentes Base Mobile

**Prioridad:** CRÍTICA  
**Complejidad:** ALTA  
**Duración:** 4 días (24 horas)  
**Asignado a:** Senior Frontend Dev #2 + Frontend Dev #1  
**Dependencias:** T-F101 completado  

#### Descripción

Crear los componentes de UI móvil base que se usarán en toda la aplicación.

#### Subtareas

**T-F102.1: MobileHeader**

**Archivo:** `frontend/src/components/mobile/MobileHeader.tsx`

```typescript
import React from 'react'
import { Menu, LogOut } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import { useNavigate } from 'react-router-dom'

interface MobileHeaderProps {
  onHamburgerClick?: () => void
}

export default function MobileHeader({ onHamburgerClick }: MobileHeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  return (
    <header className="bg-blue-900 text-white px-4 py-3 flex items-center justify-between shadow-md">
      {/* Logo */}
      <div className="font-bold text-lg">🐔 Lider Pollo</div>
      
      {/* Right side: User + Menu */}
      <div className="flex items-center gap-2">
        <span className="text-sm">{user?.name}</span>
        <button 
          onClick={onHamburgerClick}
          className="p-2 hover:bg-blue-800 rounded"
          aria-label="Menu"
        >
          <Menu size={20} />
        </button>
      </div>
    </header>
  )
}
```

**Criterios de Aceptación:**
- ✅ Logo visible
- ✅ Nombre usuario visible
- ✅ Botón hamburger funciona
- ✅ Responsive en 375-480px

---

**T-F102.2: MobileBottomNav**

**Archivo:** `frontend/src/components/mobile/MobileBottomNav.tsx`

```typescript
import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Home, Plus, Clock, Layouts, User } from 'lucide-react'

const NAV_ITEMS = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: Plus, label: 'Registrar', path: '/register' },
  { icon: Clock, label: 'Pendientes', path: '/pending' },
  { icon: Layouts, label: 'Lote', path: '/lot' },
  { icon: User, label: 'Perfil', path: '/profile' },
]

export default function MobileBottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  
  return (
    <nav 
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex justify-around"
      data-testid="mobile-bottom-nav"
    >
      {NAV_ITEMS.map(({ icon: Icon, label, path }) => {
        const isActive = location.pathname === path
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            className={`flex flex-col items-center py-2 px-3 min-h-[60px] justify-center flex-1 ${
              isActive 
                ? 'text-blue-600 border-t-2 border-blue-600' 
                : 'text-slate-500 hover:text-slate-700'
            }`}
            aria-current={isActive ? 'page' : undefined}
          >
            <Icon size={24} />
            <span className="text-xs mt-1">{label}</span>
          </button>
        )
      })}
    </nav>
  )
}
```

**Criterios de Aceptación:**
- ✅ 5 items visibles
- ✅ Item activo resaltado
- ✅ Click navega correctamente
- ✅ Fixed position en bottom

---

**T-F102.3: MobileHamburger**

**Archivo:** `frontend/src/components/mobile/MobileHamburger.tsx`

```typescript
import React from 'react'
import { X, Settings, FileText, LogOut } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import { useNavigate } from 'react-router-dom'

interface MobileHamburgerProps {
  onClose: () => void
}

export default function MobileHamburger({ onClose }: MobileHamburgerProps) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  
  const handleLogout = () => {
    logout()
    navigate('/login')
  }
  
  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Overlay */}
      <div 
        className="flex-1 bg-black/50"
        onClick={onClose}
      />
      
      {/* Menu */}
      <div className="bg-white w-64 p-4 flex flex-col">
        <button 
          onClick={onClose}
          className="self-end p-2 hover:bg-slate-100 rounded mb-4"
        >
          <X size={20} />
        </button>
        
        <nav className="flex-1 space-y-2">
          <MenuItem icon={Settings} label="Configuración" onClick={() => { navigate('/profile'); onClose() }} />
          <MenuItem icon={FileText} label="Reporte" onClick={() => { navigate('/report'); onClose() }} />
        </nav>
        
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full p-3 text-red-600 hover:bg-red-50 rounded"
        >
          <LogOut size={20} />
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}

interface MenuItemProps {
  icon: React.ElementType
  label: string
  onClick: () => void
}

function MenuItem({ icon: Icon, label, onClick }: MenuItemProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 w-full p-3 hover:bg-slate-100 rounded text-left"
    >
      <Icon size={20} />
      <span>{label}</span>
    </button>
  )
}
```

**Criterios de Aceptación:**
- ✅ Overlay clickable cierra menú
- ✅ Items navegables
- ✅ Logout funciona
- ✅ Animación suave (opcional pero deseable)

---

**T-F102.4: MobileForm (Componente Base)**

**Archivo:** `frontend/src/components/mobile/MobileForm.tsx`

```typescript
import React from 'react'
import { UseFormRegister, FieldValues, Path, FieldError } from 'react-hook-form'

interface MobileFormProps {
  title: string
  step?: number
  totalSteps?: number
  children: React.ReactNode
  onNext?: () => void
  onPrev?: () => void
  canNext?: boolean
  canPrev?: boolean
}

export function MobileForm({
  title,
  step,
  totalSteps,
  children,
  onNext,
  onPrev,
  canNext = true,
  canPrev = false,
}: MobileFormProps) {
  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 p-4">
        <h1 className="text-lg font-semibold">{title}</h1>
        {step && totalSteps && (
          <div className="mt-2">
            <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
              <span>Paso {step} de {totalSteps}</span>
              <span>{Math.round((step / totalSteps) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${(step / totalSteps) * 100}%` }}
              />
            </div>
          </div>
        )}
      </header>
      
      {/* Content */}
      <main className="flex-1 overflow-auto p-4">
        {children}
      </main>
      
      {/* Footer with buttons */}
      <footer className="bg-white border-t border-slate-200 p-4 flex gap-2">
        {canPrev && (
          <button
            onClick={onPrev}
            className="flex-1 py-3 px-4 bg-slate-200 text-slate-800 font-semibold rounded-lg hover:bg-slate-300 transition"
          >
            ← Anterior
          </button>
        )}
        
        {canNext && (
          <button
            onClick={onNext}
            className="flex-1 py-3 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Siguiente →
          </button>
        )}
      </footer>
    </div>
  )
}

interface MobileInputProps<T extends FieldValues> {
  label: string
  type?: string
  placeholder?: string
  register: UseFormRegister<T>
  name: Path<T>
  error?: FieldError
  required?: boolean
  help?: string
}

export function MobileInput<T extends FieldValues>({
  label,
  type = 'text',
  placeholder,
  register,
  name,
  error,
  required,
  help,
}: MobileInputProps<T>) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-slate-700 mb-2">
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>
      
      <input
        type={type}
        placeholder={placeholder}
        {...register(name, { required })}
        className={`w-full px-4 py-3 rounded-lg border text-base transition ${
          error 
            ? 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
            : 'border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
        }`}
      />
      
      {error && (
        <p className="text-red-500 text-sm mt-1">{error.message}</p>
      )}
      
      {help && !error && (
        <p className="text-slate-500 text-xs mt-1">{help}</p>
      )}
    </div>
  )
}
```

**Criterios de Aceptación:**
- ✅ Progress bar visible cuando step/totalSteps proporcionado
- ✅ Botones siguiente/anterior funcionales
- ✅ Inputs con validación errors visible
- ✅ Help text visible bajo input

---

**T-F102.5: MobileCard**

**Archivo:** `frontend/src/components/mobile/MobileCard.tsx`

```typescript
import React from 'react'
import { ChevronRight } from 'lucide-react'

interface MobileCardProps {
  title: string
  subtitle?: string
  icon?: React.ReactNode
  badge?: { label: string; color: 'success' | 'warning' | 'danger' | 'info' }
  action?: { label: string; onClick: () => void }
  children?: React.ReactNode
}

export function MobileCard({
  title,
  subtitle,
  icon,
  badge,
  action,
  children,
}: MobileCardProps) {
  const badgeColors = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  }
  
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 mb-3 shadow-sm hover:shadow-md transition">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-start gap-3 flex-1">
          {icon && (
            <div className="text-2xl flex-shrink-0">{icon}</div>
          )}
          
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-slate-900 truncate">{title}</h3>
            {subtitle && (
              <p className="text-sm text-slate-600 truncate">{subtitle}</p>
            )}
          </div>
        </div>
        
        {badge && (
          <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 ${badgeColors[badge.color]}`}>
            {badge.label}
          </span>
        )}
      </div>
      
      {/* Content */}
      {children && (
        <div className="mb-3 text-sm text-slate-600">
          {children}
        </div>
      )}
      
      {/* Action */}
      {action && (
        <button
          onClick={action.onClick}
          className="flex items-center justify-between w-full text-blue-600 font-medium text-sm hover:bg-blue-50 px-2 py-1 rounded transition"
        >
          <span>{action.label}</span>
          <ChevronRight size={16} />
        </button>
      )}
    </div>
  )
}
```

**Criterios de Aceptación:**
- ✅ Card renderea con title
- ✅ Badge visible cuando proporcionado
- ✅ Action button clickeable
- ✅ Responsive en 375px

---

#### Testing (T-F102)

**Unit tests con Vitest:**

```typescript
// components/mobile/MobileForm.test.tsx
import { render, screen } from '@testing-library/react'
import { MobileForm } from './MobileForm'

describe('MobileForm', () => {
  it('renders title', () => {
    render(
      <MobileForm title="Test Title">
        <div>Content</div>
      </MobileForm>
    )
    expect(screen.getByText('Test Title')).toBeInTheDocument()
  })
  
  it('shows progress bar with step/totalSteps', () => {
    render(
      <MobileForm title="Test" step={2} totalSteps={5}>
        <div>Content</div>
      </MobileForm>
    )
    expect(screen.getByText('Paso 2 de 5')).toBeInTheDocument()
    expect(screen.getByText('40%')).toBeInTheDocument()
  })
  
  it('disables next button when canNext false', () => {
    render(
      <MobileForm title="Test" onNext={() => {}} canNext={false}>
        <div>Content</div>
      </MobileForm>
    )
    const nextBtn = screen.getByText('Siguiente →')
    expect(nextBtn).toBeDisabled()
  })
})
```

**Criterios de Aceptación:**
- ✅ Todos los tests pasan

---

### TAREA T-B101: Completar Endpoints Operativos Backend

**Prioridad:** CRÍTICA  
**Complejidad:** MEDIA  
**Duración:** 4 días (24 horas)  
**Asignado a:** Senior Backend Dev + Backend Dev #1  
**Dependencias:** DB schemas existentes  

#### Descripción

Completar los endpoints de operaciones que aún no están implementados o están incompletos.

#### Subtareas

**T-B101.1: POST /operations/events/ - Create Event**

**Archivo a actualizar:** `backend/app/operations/router.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas, service
from ..database import get_db
from ..dependencies import get_current_user
from ..security import verify_company_access

router = APIRouter(prefix="/operations", tags=["Operations"])

@router.post("/events/", response_model=schemas.OperationalEventRead, status_code=201)
async def create_event(
    data: schemas.OperationalEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> schemas.OperationalEventRead:
    """
    Crear un nuevo evento operativo (registrado por operador).
    
    Flujo:
    1. Validar permisos (operador, supervisor, etc.)
    2. Validar datos contra reglas de negocio (edad, capacidad, etc.)
    3. Crear evento + sub-elementos (movements, params, etc.)
    4. Registrar en AuditLog
    5. Retornar evento con ID
    
    Estados de evento recién creado: REGISTERED (no DRAFT)
    El evento va directamente a "Enviado a revisión"
    """
    svc = service.OperationService(db, current_user['company_id'])
    
    # Validación: Usuario debe tener permisos de create
    if not current_user.get('can_create_operations'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para registrar operaciones"
        )
    
    # Validación: Lot debe existir y pertenece a la compañía
    await svc.validate_lot_exists(data.lot_id)
    
    # Validación: Tipo de evento permitido para esta etapa del lote
    await svc.validate_event_type_for_phase(data.lot_id, data.event_type)
    
    # Crear evento
    event = await svc.create_operational_event(data, current_user['id'])
    
    return schemas.OperationalEventRead.model_validate(event)
```

**Criterios de Aceptación:**
- ✅ Request válido → 201 + evento con ID
- ✅ Faltan permisos → 403
- ✅ Lote no existe → 404
- ✅ Evento inválido para fase → 400
- ✅ AuditLog registra creación
- ✅ Response incluye ID, estado, timestamps

---

**T-B101.2: GET /operations/events/{id}/ - Get Event Detail**

```python
@router.get("/events/{event_id}/", response_model=schemas.OperationalEventDetailRead)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> schemas.OperationalEventDetailRead:
    """
    Obtener detalle completo de un evento.
    
    Retorna:
    - Datos base evento
    - Todos los sub-elementos (movements, params, etc.)
    - Historial de correcciones (si aplica)
    - Estado actual
    - Información auditoría
    """
    svc = service.OperationService(db, current_user['company_id'])
    
    event = await svc.get_event_detail(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    # Verificar que usuario puede ver este evento (pertenece a su compañía)
    if event.company_id != current_user['company_id']:
        raise HTTPException(status_code=403, detail="No tienes acceso a este evento")
    
    return schemas.OperationalEventDetailRead.model_validate(event)
```

**Criterios de Aceptación:**
- ✅ Evento existe → 200 + detalle completo
- ✅ Evento no existe → 404
- ✅ Compañía diferente → 403
- ✅ Response incluye sub-elementos (movements, params, etc.)
- ✅ Response incluye historial correcciones

---

**T-B101.3: PATCH /operations/events/{id}/ - Update Event (with Audit)**

```python
@router.patch("/events/{event_id}/", response_model=schemas.OperationalEventRead)
async def update_event(
    event_id: int,
    data: schemas.OperationalEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> schemas.OperationalEventRead:
    """
    Actualizar evento (solo campos permitidos, solo por supervisor+).
    
    Solo supervisor/aprobador pueden actualizar.
    Registra cambios en AuditLog (valor original → nuevo).
    """
    svc = service.OperationService(db, current_user['company_id'])
    
    # Solo supervisores/aprobadores pueden actualizar
    if current_user.get('role') not in ['supervisor', 'aprobador', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo supervisores pueden actualizar eventos"
        )
    
    event = await svc.update_event_with_audit(
        event_id=event_id,
        update_data=data,
        updated_by_id=current_user['id'],
    )
    
    return schemas.OperationalEventRead.model_validate(event)
```

**Criterios de Aceptación:**
- ✅ Supervisor actualiza evento → 200
- ✅ Operador intenta actualizar → 403
- ✅ Cambios registrados en AuditLog
- ✅ Timestamp updated_at actualizado

---

**T-B101.4: GET /lots/{lot_id}/operations/ - List Events for Lot**

```python
@router.get("/lots/{lot_id}/operations/", response_model=list[schemas.OperationalEventRead])
async def list_lot_operations(
    lot_id: int,
    status: Optional[str] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Listar todos los eventos de un lote con filtros opcionales.
    
    Parámetros:
    - status: REGISTERED, APPROVED, REJECTED, CONSOLIDATED, etc.
    - event_type: BIRD_MOVEMENT, FEED_MOVEMENT, etc.
    - skip, limit: Paginación
    """
    svc = service.OperationService(db, current_user['company_id'])
    
    events = await svc.list_lot_events(
        lot_id=lot_id,
        status_filter=status,
        event_type_filter=event_type,
        skip=skip,
        limit=limit,
    )
    
    return [schemas.OperationalEventRead.model_validate(e) for e in events]
```

**Criterios de Aceptación:**
- ✅ Retorna lista de eventos
- ✅ Filtros status y event_type funcionan
- ✅ Paginación funciona
- ✅ Solo retorna eventos de la compañía del usuario

---

### TAREA T-B102: Implementar Servicio de KPIs Básicos

**Prioridad:** ALTA  
**Complejidad:** MEDIA  
**Duración:** 3 días (18 horas)  
**Asignado a:** Backend Dev #2  
**Dependencias:** T-B101 completado, operaciones registradas  

#### Descripción

Crear un servicio que calcule KPIs básicos a partir de eventos registrados.

#### Implementación

**Archivo nuevo:** `backend/app/operations/kpi_service.py`

```python
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from ..masters.models import Lot

class KPIService:
    """Calcula KPIs (Key Performance Indicators) para lotes y fases."""
    
    def __init__(self, db: AsyncSession, company_id: int):
        self.db = db
        self.company_id = company_id
    
    async def get_lot_kpis(self, lot_id: int) -> dict:
        """Retorna KPIs principales para un lote."""
        lot = await self.db.get(Lot, lot_id)
        if not lot or lot.company_id != self.company_id:
            return {}
        
        return {
            'lot_id': lot_id,
            'mortality_rate': await self._calc_mortality(lot_id),
            'avg_weight': await self._calc_avg_weight(lot_id),
            'feed_consumption_per_day': await self._calc_feed_consumption(lot_id),
            'egg_fertility_rate': await self._calc_egg_fertility(lot_id),
            'hatchery_yield': await self._calc_hatchery_yield(lot_id),
        }
    
    async def _calc_mortality(self, lot_id: int) -> float:
        """
        Calcula porcentaje de mortalidad.
        
        % Mortalidad = (Total aves muertas / Población inicial) × 100
        """
        # Obtener población inicial
        initial_pop = await self._get_initial_population(lot_id)
        if not initial_pop:
            return 0.0
        
        # Sumar todas las muertes registradas
        result = await self.db.execute(
            select(func.sum(models.BirdMovement.quantity))
            .select_from(models.OperationalEvent)
            .join(models.BirdMovement)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.BirdMovement.movement_type == 'mortality')
            )
        )
        total_deaths = result.scalar() or 0
        
        mortality_pct = (total_deaths / initial_pop * 100) if initial_pop > 0 else 0.0
        return round(mortality_pct, 2)
    
    async def _calc_avg_weight(self, lot_id: int) -> Optional[float]:
        """
        Obtiene el peso promedio más reciente.
        """
        result = await self.db.execute(
            select(models.BirdMovement.avg_weight)
            .select_from(models.OperationalEvent)
            .join(models.BirdMovement)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.BirdMovement.movement_type == 'weighing')
            )
            .order_by(models.OperationalEvent.event_date.desc())
            .limit(1)
        )
        return result.scalar()
    
    async def _calc_feed_consumption(self, lot_id: int) -> float:
        """
        Calcula consumo promedio de alimento por día.
        """
        # Sumar kg alimento últimos 7 días
        cutoff_date = date.today() - timedelta(days=7)
        result = await self.db.execute(
            select(func.sum(models.FeedMovement.quantity_kg))
            .select_from(models.OperationalEvent)
            .join(models.FeedMovement)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.OperationalEvent.event_date >= cutoff_date)
            )
        )
        total_kg = result.scalar() or 0
        
        # Dividir por 7 días
        daily_avg = total_kg / 7 if total_kg > 0 else 0.0
        return round(daily_avg, 2)
    
    async def _calc_egg_fertility(self, lot_id: int) -> float:
        """
        Calcula % fertilidad de huevos.
        
        % Fértil = (Huevos fértiles / Total huevos) × 100
        """
        result = await self.db.execute(
            select(
                func.sum(models.EggMovement.quantity).filter(
                    models.EggMovement.egg_type == 'fertile'
                ).label('fertile'),
                func.sum(models.EggMovement.quantity).label('total'),
            )
            .select_from(models.OperationalEvent)
            .join(models.EggMovement)
            .where(models.OperationalEvent.lot_id == lot_id)
        )
        row = result.first()
        
        if not row or row.total == 0:
            return 0.0
        
        fertility_pct = (row.fertile / row.total * 100) if row.fertile else 0.0
        return round(fertility_pct, 2)
    
    async def _calc_hatchery_yield(self, lot_id: int) -> float:
        """
        Calcula % eclosión en incubadora.
        
        % Yield = (Pollitos viables / Huevos fértiles cargados) × 100
        """
        # Obtener huevos fértiles cargados
        result_loaded = await self.db.execute(
            select(func.sum(models.HatcheryParams.quantity_loaded))
            .select_from(models.OperationalEvent)
            .join(models.HatcheryParams)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.OperationalEvent.event_type == 'incubation_load')
            )
        )
        eggs_loaded = result_loaded.scalar() or 0
        
        # Obtener pollitos viables nacidos
        result_born = await self.db.execute(
            select(func.sum(models.HatcheryParams.quantity_born_viable))
            .select_from(models.OperationalEvent)
            .join(models.HatcheryParams)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.OperationalEvent.event_type == 'birth_registration')
            )
        )
        chicks_born = result_born.scalar() or 0
        
        if eggs_loaded == 0:
            return 0.0
        
        yield_pct = (chicks_born / eggs_loaded * 100)
        return round(yield_pct, 2)
    
    async def _get_initial_population(self, lot_id: int) -> int:
        """Obtiene población inicial del lote."""
        lot = await self.db.get(Lot, lot_id)
        if not lot:
            return 0
        
        # Si tiene opening_balance, usar ese
        if lot.opening_balance:
            return (lot.opening_balance.initial_male_count + 
                    lot.opening_balance.initial_female_count)
        
        # Si no, buscar primer evento de recepción
        result = await self.db.execute(
            select(func.sum(models.BirdMovement.quantity))
            .select_from(models.OperationalEvent)
            .join(models.BirdMovement)
            .where(
                (models.OperationalEvent.lot_id == lot_id) &
                (models.BirdMovement.movement_type == 'reception')
            )
        )
        return result.scalar() or 0
```

**Criterios de Aceptación:**
- ✅ Mortalidad % se calcula correctamente
- ✅ Peso promedio retorna valor más reciente
- ✅ Consumo alimento promedio por día
- ✅ Fertilidad % de huevos
- ✅ Yield % de incubadora
- ✅ Endpoint GET `/kpis/{lot_id}/` retorna diccionario KPIs

---

### TAREA T-QA101: Plan de Testing E2E (Playwright)

**Prioridad:** ALTA  
**Complejidad:** MEDIA  
**Duración:** 2 días (12 horas)  
**Asignado a:** QA Lead  
**Dependencias:** Ninguna  

#### Descripción

Crear el plan y la infraestructura para tests E2E con Playwright.

#### Deliverables

**playwright.config.ts actualizado:**

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the code */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,
  
  reporter: 'html',
  
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'tablet',
      use: { ...devices['iPad Pro'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
})
```

**Test Suite Structure:**

```
e2e/
├── auth/
│   └── login.spec.ts           # Login scenarios
├── mobile/
│   ├── home.spec.ts             # Mobile home page
│   ├── register.spec.ts          # Mobile registration flow
│   └── pending.spec.ts           # Mobile pending events
├── web/
│   ├── review.spec.ts            # Web review flow
│   └── approval.spec.ts          # Web approval flow
└── fixtures/
    ├── auth.fixture.ts           # Login helper
    └── db.fixture.ts             # Database setup
```

**Ejemplo test (e2e/mobile/home.spec.ts):**

```typescript
import { test, expect } from '@playwright/test'

test.describe('Mobile Home', () => {
  test.beforeEach(async ({ page }) => {
    // Login primero
    page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/login')
    await page.fill('input[name="username"]', 'operator1')
    await page.fill('input[name="password"]', 'password')
    await page.click('button:has-text("Ingresar")')
    await page.waitForNavigation()
  })
  
  test('displays lot KPIs', async ({ page }) => {
    await expect(page).toHaveTitle(/Home/)
    await expect(page.locator('text=Mi Lote Actual')).toBeVisible()
    await expect(page.locator('text=Mortalidad')).toBeVisible()
    await expect(page.locator('text=Peso Promedio')).toBeVisible()
  })
  
  test('has bottom navigation', async ({ page }) => {
    await expect(page.locator('[data-testid="mobile-bottom-nav"]')).toBeVisible()
    await expect(page.locator('text=Home')).toBeVisible()
    await expect(page.locator('text=Registrar')).toBeVisible()
  })
  
  test('navigates to register on + button', async ({ page }) => {
    await page.click('text=Registrar')
    await page.waitForNavigation()
    await expect(page).toHaveURL(/register/)
  })
})
```

**Criterios de Aceptación:**
- ✅ Playwright configurado y funcionando
- ✅ 5+ scenarios definidos (login, mobile home, register, etc.)
- ✅ Tests pasan en Chrome, Mobile, Tablet
- ✅ CI/CD pipeline puede ejecutar tests

---

### TAREA T-OPS101: Preparar Figura y Prototipos (Design)

**Prioridad:** MEDIA  
**Complejidad:** MEDIA  
**Duración:** 3 días (12 horas, paralelo)  
**Asignado a:** UI/UX Designer  
**Dependencias:** Requerimientos finales (AUDIT_REDISEÑO_INTEGRAL.md)  

#### Descripción

Crear prototipos visuales en Figma para mobile y componentes base.

#### Wireframes/Screens a Crear

1. **Mobile Wireframes** (8 screens):
   - 00-Auth-Login
   - 01-Mobile-Home
   - 02-Mobile-Register-Menu
   - 03-Mobile-Register-Form-Step1
   - 04-Mobile-Register-Form-Step2
   - 05-Mobile-Register-Confirm
   - 06-Mobile-Pending-Events
   - 07-Mobile-Profile

2. **Web Wireframes** (8 screens):
   - 00-Web-Dashboard
   - 01-Web-Review-List
   - 02-Web-Review-Detail
   - 03-Web-Approval
   - 04-Web-Lots-Table
   - 05-Web-Lot-Detail
   - 06-Web-Reports
   - 07-Web-Masters

3. **Component Library** (Base):
   - Colors & Typography
   - Mobile Buttons
   - Mobile Inputs & Forms
   - Mobile Cards
   - Web Tables
   - Web Modals
   - Status Badges
   - Icons

**Criterios de Aceptación:**
- ✅ Figma compartido con equipo
- ✅ Component library definida
- ✅ 16 screens completos
- ✅ Responsive breakpoints especificados (375px, 768px, 1024px, 1920px)
- ✅ Aprobado por stakeholders

---

## RESUMEN SPRINT 1

### Timeline por Día

```
SEMANA 1 (Jun 24-28)
├── Lunes 24
│   ├── Morning: Sprint Kickoff (10:00)
│   │   - Revisión AUDIT_REDISEÑO_INTEGRAL.md
│   │   - Asignación de tareas
│   │   - Q&A
│   ├── Tarde: Inicio tareas
│   │   - Design: Figma setup
│   │   - Frontend: T-F101.1 hook
│   │   - Backend: T-B101 endpoints
│   │   - QA: T-QA101 plan
│   │
│   ├── Martes 25
│   │   ├── Morning standup (10:00)
│   │   ├── Frontend: T-F101.2 MobileShell/WebShell
│   │   ├── Backend: T-B101.1 POST /operations/events/
│   │   └── Design: Mobile screens wireframes
│   │
│   ├── Miércoles 26
│   │   ├── Morning standup (10:00)
│   │   ├── Frontend: T-F101.3 App.tsx routing
│   │   ├── Backend: T-B101.2-3 GET/PATCH endpoints
│   │   └── Design: Web screens wireframes
│   │
│   └── Jueves 27
│       ├── Morning standup (10:00)
│       ├── Frontend: T-F102 Mobile components start
│       ├── Backend: T-B102 KPI service
│       ├── Design: Component library
│       └── Sprint Review Prep
│
│   Viernes 28
│   ├── Morning standup (10:00)
│   ├── Frontend: T-F102 finish components
│   ├── Backend: T-B101.4 list operations
│   ├── QA: Playwright setup
│   ├── Sprint Review (16:00)
│   └── Sprint Retro (17:00)

SEMANA 2 (Jul 1-8)
├── Lunes 1
│   ├── Morning standup (10:00)
│   ├── Frontend: T-F102 mobile card + form
│   ├── Backend: KPI service finalization
│   └── Tests: First E2E tests
│
├── Martes 2 - Viernes 5
│   └── [Similar pattern]
│       - Frontend: Finish mobile components, start integration
│       - Backend: Optimize endpoints, add validations
│       - Tests: Write & run E2E tests
│       - Design: Polish & handoff to dev
│
└── Viernes 8
    ├── Final standup
    ├── All tests passing
    ├── Code review & merge to main
    ├── Sprint Review (16:00)
    ├── Sprint Retro (17:00)
    └── Sprint 1 COMPLETE ✅
```

### Definición de Completado (Definition of Done - DoD)

Para que una tarea sea considerada DONE:

1. **Código:**
   - [ ] Código escrito según estándares del proyecto
   - [ ] No hay eslint/tsc warnings
   - [ ] Tests pasan (unit + integration)
   - [ ] Code review aprobado por tech lead

2. **Testing:**
   - [ ] Unit tests: 80% coverage
   - [ ] E2E tests: escritos y pasan
   - [ ] Manual testing en mobile + desktop

3. **Documentación:**
   - [ ] Código tiene comentarios donde es complejo
   - [ ] README actualizado si es necesario
   - [ ] Figma actualizado con final designs

4. **Performance:**
   - [ ] Bundle size no aumentó
   - [ ] Network requests optimizadas
   - [ ] No hay console errors

5. **Aceptación:**
   - [ ] Stakeholder aprobó
   - [ ] Merged a main branch
   - [ ] Desplegado a staging

### Métricas Esperadas al Final Sprint 1

| Métrica | Target | Expected |
|---------|--------|----------|
| **Frontend completitud** | 30-40% | 35% |
| **Backend completitud** | 40-50% | 45% |
| **Test coverage** | 40%+ | 45% |
| **Bugs encontrados** | < 5 críticos | 2-3 |
| **Documentación avance** | 50% | 50% |
| **Equipo satisacción** | 7/10+ | 8/10 |

---

**End of Sprint 1 Technical Breakdown**

Próxima fase: [SPRINT2_TECHNICAL_TASKS.md] - Funcionalidad Operativa (Jul 9-22)
