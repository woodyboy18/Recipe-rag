import { motion } from 'motion/react';
import { FiSun, FiMoon } from 'react-icons/fi';
import { GiCandleFlame } from 'react-icons/gi';

const THEMES = [
  { id: 'light', label: 'Light', icon: <FiSun size={15} /> },
  { id: 'warm', label: 'Warm Light', icon: <GiCandleFlame size={16} /> },
  { id: 'dark', label: 'Dark Mode', icon: <FiMoon size={15} /> }
];

const ThemeToggle = ({ theme = 'light', onThemeChange }) => {
  return (
    <div
      className="theme-switcher-container"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        background: 'var(--card-bg)',
        border: '1px solid var(--border-color)',
        borderRadius: '30px',
        padding: '4px',
        boxShadow: 'var(--shadow-sm)',
        gap: '2px',
        userSelect: 'none'
      }}
    >
      {THEMES.map((t) => {
        const isActive = theme === t.id;
        return (
          <motion.button
            key={t.id}
            onClick={() => onThemeChange && onThemeChange(t.id)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '20px',
              border: 'none',
              background: isActive ? 'var(--primary-green)' : 'transparent',
              color: isActive ? '#FFFFFF' : 'var(--text-muted)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.12)' : 'none'
            }}
            title={`Switch to ${t.label}`}
          >
            <span style={{ display: 'flex', alignItems: 'center' }}>{t.icon}</span>
            <span>{t.label}</span>
          </motion.button>
        );
      })}
    </div>
  );
};

export default ThemeToggle;
