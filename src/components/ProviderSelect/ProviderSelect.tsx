import { useState, useRef, useEffect, useCallback } from 'react'
import { PROVIDER_PRESETS, type LLMProviderType } from '@/types/pixelmap'
import styles from './ProviderSelect.module.css'

interface ProviderSelectProps {
  value: LLMProviderType
  onChange: (value: LLMProviderType) => void
}

export function ProviderSelect({ value, onChange }: ProviderSelectProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const selected = PROVIDER_PRESETS.find((p) => p.type === value)

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        return
      }
      if (e.key === 'Enter' || e.key === ' ') {
        if (!open) {
          setOpen(true)
        }
        return
      }
      if (open && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        const idx = PROVIDER_PRESETS.findIndex((p) => p.type === value)
        const next =
          e.key === 'ArrowDown'
            ? (idx + 1) % PROVIDER_PRESETS.length
            : (idx - 1 + PROVIDER_PRESETS.length) % PROVIDER_PRESETS.length
        onChange(PROVIDER_PRESETS[next].type)
      }
    },
    [open, value, onChange],
  )

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div className={styles.wrapper} ref={ref} onKeyDown={handleKeyDown}>
      <button
        className={styles.trigger}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Select provider"
      >
        <span>{selected?.label ?? 'Select provider'}</span>
        <span className={styles.arrow}>{open ? '\u25B2' : '\u25BC'}</span>
      </button>
      {open && (
        <ul className={styles.menu} role="listbox" aria-label="Providers">
          {PROVIDER_PRESETS.map((p) => (
            <li
              key={p.type}
              role="option"
              aria-selected={p.type === value}
              className={`${styles.option} ${p.type === value ? styles.selected : ''}`}
              onClick={() => {
                onChange(p.type)
                setOpen(false)
              }}
            >
              {p.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
