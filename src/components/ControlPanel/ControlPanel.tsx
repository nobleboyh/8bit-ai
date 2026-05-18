import { useCallback } from 'react'
import styles from './ControlPanel.module.css'

const EXAMPLE_CHIPS = [
  { label: 'Wizard', prompt: 'A wise old wizard with a long flowing beard, wearing deep blue robes adorned with golden crescent moons, holding a sparkling staff' },
  { label: 'Knight', prompt: 'A valiant knight in shining silver armor with a crimson cape, wielding a broadsword, standing ready for battle' },
  { label: 'Robot', prompt: 'A sleek chrome robot with glowing blue optic sensors, exposed circuitry, and mechanical joints' },
  { label: 'Astronaut', prompt: 'A modern astronaut in a white space suit with a gold-visored helmet, floating against a starfield' },
  { label: 'Ninja', prompt: 'A shadowy ninja in dark grey attire, face partially covered, poised in a stealthy combat stance' },
  { label: 'Elf', prompt: 'A mystical forest elf with pointed ears wearing earthy green and brown leather, bow slung across back' },
] as const

interface ControlPanelProps {
  prompt: string
  onPromptChange: (value: string) => void
  onGenerate: () => void
  isGenerating: boolean
  hasApiKey: boolean
}

export function ControlPanel({
  prompt,
  onPromptChange,
  onGenerate,
  isGenerating,
  hasApiKey,
}: ControlPanelProps) {
  const disabled = isGenerating || !prompt.trim() || !hasApiKey

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (disabled) return
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault()
        onGenerate()
      }
    },
    [onGenerate, disabled],
  )

  return (
    <div>
      <div className={styles.generateRow}>
        <textarea
          className={styles.textarea}
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your character... e.g. A wise old wizard with a sparkling staff"
          rows={3}
          aria-label="Character prompt"
        />
        <button
          className={`${styles.forgeBtn} ${styles.btnPrimary}`}
          onClick={onGenerate}
          disabled={disabled}
          aria-label="Generate avatar"
        >
          FORGE
        </button>
      </div>
      <div className={styles.examplesRow}>
        {EXAMPLE_CHIPS.map((chip) => (
          <button
            key={chip.label}
            className={styles.chip}
            onClick={() => onPromptChange(chip.prompt)}
            aria-label={`${chip.label} preset`}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  )
}
