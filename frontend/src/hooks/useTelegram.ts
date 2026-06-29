/**
 * Telegram Mini App SDK integration hook.
 * 
 * Detects if the app is running inside Telegram, initializes the SDK,
 * and exposes utilities for theme sync, native navigation, and platform awareness.
 * 
 * Usage:
 *   const { isTelegram, tgUser, theme } = useTelegram()
 */
import { useEffect, useState, useCallback } from 'react'
import {
  init,
  miniApp,
  themeParams,
  backButton,
  mainButton,
  retrieveLaunchParams,
  isTMA,
  type ThemeParams,
  type LaunchParams,
} from '@telegram-apps/sdk'

// ── Types ──────────────────────────────────────────────────────

export interface TelegramTheme {
  bgColor: string
  textColor: string
  hintColor: string
  linkColor: string
  buttonColor: string
  buttonTextColor: string
  secondaryBgColor: string
  headerBgColor: string
  bottomBarBgColor: string
}

export interface TelegramUser {
  id: number
  firstName: string
  lastName?: string
  username?: string
  languageCode?: string
  isPremium?: boolean
}

interface TelegramState {
  /** Whether we are running inside Telegram Mini App */
  isTelegram: boolean
  /** Whether the SDK has finished initializing */
  isReady: boolean
  /** Telegram theme parameters (dark/light aware) */
  theme: TelegramTheme | null
  /** Telegram user data from launch params */
  tgUser: TelegramUser | null
  /** Raw launch params */
  launchParams: LaunchParams | null
  /** Show the native Telegram main button */
  showMainButton: (text: string, onClick: () => void) => void
  /** Hide the native Telegram main button */
  hideMainButton: () => void
  /** Show the native Telegram back button */
  showBackButton: (onClick: () => void) => void
  /** Hide the native Telegram back button */
  hideBackButton: () => void
  /** Apply Telegram theme colors to CSS custom properties */
  applyTheme: () => void
}

// ── Default light theme (fallback when not in Telegram) ───────

const DEFAULT_THEME: TelegramTheme = {
  bgColor: '#F1F5F9',
  textColor: '#1E293B',
  hintColor: '#94A3B8',
  linkColor: '#5A9BBA',
  buttonColor: '#264C5F',
  buttonTextColor: '#FFFFFF',
  secondaryBgColor: '#FFFFFF',
  headerBgColor: '#1E3A5F',
  bottomBarBgColor: '#FFFFFF',
}

// ── Convert Telegram ThemeParams to our format ─────────────────

function toTelegramTheme(tp: ThemeParams): TelegramTheme {
  return {
    bgColor: tp.backgroundColor || DEFAULT_THEME.bgColor,
    textColor: tp.textColor || DEFAULT_THEME.textColor,
    hintColor: tp.hintColor || DEFAULT_THEME.hintColor,
    linkColor: tp.linkColor || DEFAULT_THEME.linkColor,
    buttonColor: tp.buttonColor || DEFAULT_THEME.buttonColor,
    buttonTextColor: tp.buttonTextColor || DEFAULT_THEME.buttonTextColor,
    secondaryBgColor: tp.secondaryBackgroundColor || DEFAULT_THEME.secondaryBgColor,
    headerBgColor: tp.headerBackgroundColor || DEFAULT_THEME.headerBgColor,
    bottomBarBgColor: tp.bottomBarBgColor || DEFAULT_THEME.bottomBarBgColor,
  }
}

// ── Hook ────────────────────────────────────────────────────────

export function useTelegram(): TelegramState {
  const [isReady, setIsReady] = useState(false)
  const [theme, setTheme] = useState<TelegramTheme | null>(null)
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)
  const [launchParams, setLaunchParams] = useState<LaunchParams | null>(null)

  // Initialize SDK once on mount
  useEffect(() => {
    if (!isTMA()) {
      // Not running in Telegram — use defaults
      setTheme(DEFAULT_THEME)
      setIsReady(true)
      return
    }

    try {
      // Initialize SDK
      const [miniAppReady] = init()

      // Retrieve launch params for user info
      const lp = retrieveLaunchParams()
      setLaunchParams(lp)

      if (lp.initData?.user) {
        setTgUser({
          id: lp.initData.user.id,
          firstName: lp.initData.user.firstName,
          lastName: lp.initData.user.lastName,
          username: lp.initData.user.username,
          languageCode: lp.initData.user.languageCode,
          isPremium: lp.initData.user.isPremium,
        })
      }

      // Sync theme
      const tp = themeParams()
      setTheme(toTelegramTheme(tp))

      // Listen for theme changes (e.g., user switches dark/light mode)
      tp.onChange(() => {
        setTheme(toTelegramTheme(tp))
      })

      // Tell Telegram the app is ready
      miniAppReady.then(() => {
        // Enable closing confirmation — prevents accidental exit
        if (miniApp.enableClosingConfirmation.isAvailable()) {
          miniApp.enableClosingConfirmation()
        }

        miniApp.ready()
        setIsReady(true)
      })
    } catch (err) {
      console.warn('Telegram SDK init failed, using defaults:', err)
      setTheme(DEFAULT_THEME)
      setIsReady(true)
    }

    return () => {
      // Cleanup theme change listener
      try {
        themeParams().offChange(() => {})
      } catch { /* ignore */ }
    }
  }, [])

  // ── Apply theme to CSS custom properties ──────────────────

  const applyTheme = useCallback(() => {
    const t = theme || DEFAULT_THEME
    const root = document.documentElement

    root.style.setProperty('--tg-bg-color', t.bgColor)
    root.style.setProperty('--tg-text-color', t.textColor)
    root.style.setProperty('--tg-hint-color', t.hintColor)
    root.style.setProperty('--tg-link-color', t.linkColor)
    root.style.setProperty('--tg-button-color', t.buttonColor)
    root.style.setProperty('--tg-button-text-color', t.buttonTextColor)
    root.style.setProperty('--tg-secondary-bg-color', t.secondaryBgColor)
    root.style.setProperty('--tg-header-bg-color', t.headerBgColor)
    root.style.setProperty('--tg-bottom-bar-bg-color', t.bottomBarBgColor)

    // Also set body background
    document.body.style.backgroundColor = t.bgColor
  }, [theme])

  // Apply theme whenever it changes
  useEffect(() => {
    if (theme) applyTheme()
  }, [theme, applyTheme])

  // ── Main Button control ───────────────────────────────────

  const showMainButton = useCallback((text: string, onClick: () => void) => {
    try {
      if (!isTMA()) return
      const mb = mainButton()
      mb.setText(text)
      mb.onClick(onClick)
      mb.show()
    } catch { /* ignore */ }
  }, [])

  const hideMainButton = useCallback(() => {
    try {
      if (!isTMA()) return
      mainButton().hide()
    } catch { /* ignore */ }
  }, [])

  // ── Back Button control ───────────────────────────────────

  const showBackButton = useCallback((onClick: () => void) => {
    try {
      if (!isTMA()) return
      const bb = backButton()
      bb.onClick(onClick)
      bb.show()
    } catch { /* ignore */ }
  }, [])

  const hideBackButton = useCallback(() => {
    try {
      if (!isTMA()) return
      backButton().hide()
    } catch { /* ignore */ }
  }, [])

  return {
    isTelegram: isTMA(),
    isReady,
    theme,
    tgUser,
    launchParams,
    showMainButton,
    hideMainButton,
    showBackButton,
    hideBackButton,
    applyTheme,
  }
}

// ── Non-hook early init for main.tsx ───────────────────────────

/**
 * Initialize Telegram SDK as early as possible (before React renders).
 * Call this in main.tsx before createRoot().
 * Sets dark mode class, applies theme colors, enables closing confirmation.
 */
export function initTelegramEarly(): void {
  if (!isTMA()) return

  try {
    const [miniAppReady] = init()

    miniAppReady.then(() => {
      // Expand to full height
      if (miniApp.expand.isAvailable()) {
        miniApp.expand()
      }

      // Sync header color with our brand
      if (miniApp.setHeaderColor.isAvailable()) {
        miniApp.setHeaderColor('#1E3A5F')
      }
      if (miniApp.setBackgroundColor.isAvailable()) {
        miniApp.setBackgroundColor('#F1F5F9')
      }

      // 🔒 Enable closing confirmation — prevents accidental exit
      //    when swiping down or pressing back at root level
      if (miniApp.enableClosingConfirmation.isAvailable()) {
        miniApp.enableClosingConfirmation()
      }

      miniApp.ready()
    })
  } catch { /* ignore */ }
}


// ── Back navigation helper (integrates with react-router) ─────

let _backCallback: (() => void) | null = null

/**
 * Register a global back-navigation handler for Telegram.
 * Call this once in your root component with a function that
 * navigates back in the app's history. If there's no history
 * (at root), the closing confirmation will fire instead.
 *
 * Usage in App.tsx:
 *   const navigate = useNavigate()
 *   useTelegramBackHandler(() => navigate(-1))
 */
export function useTelegramBackHandler(onBack: () => void) {
  const { isTelegram } = useTelegram()

  useEffect(() => {
    if (!isTelegram) return

    _backCallback = onBack

    // Show native back button and wire it to our handler
    try {
      const bb = backButton()
      bb.onClick(() => _backCallback?.())
      bb.show()
    } catch { /* ignore */ }

    return () => {
      _backCallback = null
      try {
        backButton().hide()
        backButton().offClick(() => {})
      } catch { /* ignore */ }
    }
  }, [isTelegram, onBack])
}
