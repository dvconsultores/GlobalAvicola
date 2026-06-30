/**
 * Telegram Mini App SDK v3 integration hook.
 * 
 * Detects if the app is running inside Telegram, initializes the SDK,
 * and exposes utilities for theme sync and native navigation.
 * 
 * SDK version: @telegram-apps/sdk ^3.11.8
 * 
 * Usage:
 *   const { isTelegram, tgUser, theme } = useTelegram()
 */
import { useEffect, useState, useCallback, useRef } from 'react'
import {
  init,
  miniApp,
  themeParams,
  backButton,
  retrieveLaunchParams,
  isTMA,
  enableClosingConfirmation as enableCC,
  disableClosingConfirmation as disableCC,
  isClosingConfirmationEnabled,
  mountClosingBehavior,
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
  isTelegram: boolean
  isReady: boolean
  theme: TelegramTheme | null
  tgUser: TelegramUser | null
  showBackButton: (onClick: () => void) => void
  hideBackButton: () => void
  applyTheme: () => void
  enableClosingConfirmation: () => void
  disableClosingConfirmation: () => void
  isClosingConfirmationEnabled: () => boolean
}

// ── Default light theme ────────────────────────────────────────

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

// ── Read theme from SDK Signals (callable properties) ──────────

function readTheme(): TelegramTheme {
  try {
    const tp = themeParams as Record<string, any>
    const get = (key: string, fallback: string) =>
      typeof tp[key] === 'function' ? tp[key]() : (tp[key] ?? fallback)
    return {
      bgColor: get('backgroundColor', DEFAULT_THEME.bgColor),
      textColor: get('textColor', DEFAULT_THEME.textColor),
      hintColor: get('hintColor', DEFAULT_THEME.hintColor),
      linkColor: get('linkColor', DEFAULT_THEME.linkColor),
      buttonColor: get('buttonColor', DEFAULT_THEME.buttonColor),
      buttonTextColor: get('buttonTextColor', DEFAULT_THEME.buttonTextColor),
      secondaryBgColor: get('secondaryBackgroundColor', DEFAULT_THEME.secondaryBgColor),
      headerBgColor: get('headerBackgroundColor', DEFAULT_THEME.headerBgColor),
      bottomBarBgColor: get('bottomBarBgColor', DEFAULT_THEME.bottomBarBgColor),
    }
  } catch {
    return DEFAULT_THEME
  }
}

// ── Hook ────────────────────────────────────────────────────────

export function useTelegram(): TelegramState {
  const [isReady, setIsReady] = useState(false)
  const [theme, setTheme] = useState<TelegramTheme | null>(null)
  const [tgUser, setTgUser] = useState<TelegramUser | null>(null)

  useEffect(() => {
    if (!isTMA()) {
      setTheme(DEFAULT_THEME)
      setIsReady(true)
      return
    }

    try {
      init()

      // Launch params — user info
      try {
        const lp = retrieveLaunchParams() as any
        const user = lp?.initData?.user
        if (user) {
          setTgUser({
            id: user.id,
            firstName: user.firstName,
            lastName: user.lastName,
            username: user.username,
            languageCode: user.languageCode,
            isPremium: user.isPremium,
          })
        }
      } catch { /* not available outside Telegram */ }

      // Theme
      setTheme(readTheme())
      try { (themeParams as any).onChange(() => setTheme(readTheme())) } catch { /* ignore */ }

      // Ready
      try { miniApp.ready() } catch { /* ignore */ }
      setIsReady(true)
    } catch (err) {
      console.warn('Telegram SDK init failed, using defaults:', err)
      setTheme(DEFAULT_THEME)
      setIsReady(true)
    }

    return () => {
      try { (themeParams as any).onChange(() => {}) } catch { /* ignore */ }
    }
  }, [])

  // ── Apply theme to CSS vars ────────────────────────────────

  const applyTheme = useCallback(() => {
    const t = theme || DEFAULT_THEME
    const r = document.documentElement.style
    r.setProperty('--tg-bg-color', t.bgColor)
    r.setProperty('--tg-text-color', t.textColor)
    r.setProperty('--tg-hint-color', t.hintColor)
    r.setProperty('--tg-link-color', t.linkColor)
    r.setProperty('--tg-button-color', t.buttonColor)
    r.setProperty('--tg-button-text-color', t.buttonTextColor)
    r.setProperty('--tg-secondary-bg-color', t.secondaryBgColor)
    r.setProperty('--tg-header-bg-color', t.headerBgColor)
    r.setProperty('--tg-bottom-bar-bg-color', t.bottomBarBgColor)
    document.body.style.backgroundColor = t.bgColor
  }, [theme])

  useEffect(() => { if (theme) applyTheme() }, [theme, applyTheme])

  // ── Back Button ────────────────────────────────────────────

  const showBackButton = useCallback((onClick: () => void) => {
    try { if (isTMA()) { backButton.onClick(onClick); backButton.show() } } catch { /* ignore */ }
  }, [])

  const hideBackButton = useCallback(() => {
    try { if (isTMA()) backButton.hide() } catch { /* ignore */ }
  }, [])

  // ── Closing Confirmation ────────────────────────────────────

  const enableClosingConfirmation = useCallback(() => {
    try {
      if (isTMA()) {
        if (mountClosingBehavior.isAvailable()) mountClosingBehavior()
        if (enableCC.isAvailable()) enableCC()
      }
    } catch { /* ignore */ }
  }, [])

  const disableClosingConfirmation = useCallback(() => {
    try {
      if (isTMA() && disableCC.isAvailable()) {
        disableCC()
      }
    } catch { /* ignore */ }
  }, [])

  const checkClosingConfirmationEnabled = useCallback((): boolean => {
    try {
      if (isTMA()) {
        return isClosingConfirmationEnabled() as boolean
      }
    } catch { /* ignore */ }
    return false
  }, [])

  return {
    isTelegram: isTMA(),
    isReady,
    theme,
    tgUser,
    showBackButton,
    hideBackButton,
    applyTheme,
    enableClosingConfirmation,
    disableClosingConfirmation,
    isClosingConfirmationEnabled: checkClosingConfirmationEnabled,
  }
}

// ── Early init for main.tsx ────────────────────────────────────

export function initTelegramEarly(): void {
  if (!isTMA()) return
  try {
    init()
    try { miniApp.setHeaderColor('#1E3A5F') } catch { /* ignore */ }
    try { miniApp.setBackgroundColor('#F1F5F9') } catch { /* ignore */ }
    // Pre-mount closing behavior so enableClosingConfirmation works immediately
    try { mountClosingBehavior() } catch { /* ignore */ }
    // Pre-mount back button so Telegram knows the mini app handles its own back navigation
    try { backButton.mount() } catch { /* ignore */ }
    miniApp.ready()
  } catch { /* ignore */ }
}

// ── Back navigation helper (react-router integration) ──────────

/**
 * Intercepts the Telegram Mini App back button (header + hardware)
 * and routes it to react-router navigation instead of closing the app.
 *
 * **Always** mounts and shows the native Telegram back button so that
 * Telegram never auto-closes the mini app on hardware back press.
 *
 * When `isAtRoot` is true, pressing back calls `onRootClose` which should
 * invoke `miniApp.close()` — the closing confirmation dialog (if enabled)
 * will fire before the app actually closes.
 *
 * When `isAtRoot` is false, pressing back calls `onBack` which should
 * perform a react-router `navigate(-1)`.
 */
export function useTelegramBackHandler(
  onBack: () => void,
  onRootClose: () => void,
  isAtRoot: boolean,
) {
  const { isTelegram } = useTelegram()

  // Keep latest callbacks in refs to avoid re-running the effect on every render
  const onBackRef = useRef(onBack)
  const onRootCloseRef = useRef(onRootClose)
  onBackRef.current = onBack
  onRootCloseRef.current = onRootClose

  useEffect(() => {
    if (!isTelegram) return

    // Ensure the back button component is mounted so show() works.
    // If already mounted this is a no-op (mount restores previous state).
    try { backButton.mount() } catch { /* ignore */ }

    // Always show the Telegram back button — this is the signal to Telegram
    // that the mini app handles its own back navigation. Without this, the
    // hardware back button closes the app immediately.
    try { backButton.show() } catch { /* ignore */ }

    // Wire the back button press to our handler.
    // In SDK v3, onClick returns an unsubscribe function — use it for cleanup.
    let unsubscribe: (() => void) | null = null
    try {
      const result = backButton.onClick(() => {
        if (isAtRoot) {
          onRootCloseRef.current()
        } else {
          onBackRef.current()
        }
      })
      if (typeof result === 'function') unsubscribe = result
    } catch { /* ignore */ }

    return () => {
      if (unsubscribe) {
        try { unsubscribe() } catch { /* ignore */ }
      }
    }
  }, [isTelegram, isAtRoot])
}
