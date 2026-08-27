import { motion } from 'motion/react';
import { FiCheckCircle } from 'react-icons/fi';

const foodEmojis = ['🥘', '🍚', '🍲', '🍛', '🥣', '🍜', '🥙', '🍝'];

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const itemVariants = {
  hidden: { opacity: 0, x: 20 },
  show: { opacity: 1, x: 0 }
};

const RetrievedRecipes = ({ recipes = [], selectedIndex = null, onSelectRecipe }) => {
  if (!recipes.length) return null;

  return (
    <div className="side-card">
      <h3 className="section-title" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>📄 Top Retrieved Recipes</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#2E7D32', background: '#E8F5E9', padding: '2px 8px', borderRadius: '12px' }}>
          Top {recipes.length}
        </span>
      </h3>

      <motion.div variants={containerVariants} initial="hidden" animate="show">
        {recipes.map((recipe, idx) => {
          const isSelected = selectedIndex === idx;
          return (
            <motion.div
              key={idx}
              variants={itemVariants}
              whileHover={{ scale: 1.02 }}
              onClick={() => onSelectRecipe && onSelectRecipe(idx)}
              className={`retrieved-item ${isSelected ? 'selected' : ''}`}
              style={{
                cursor: 'pointer',
                padding: '10px 12px',
                borderRadius: '12px',
                marginBottom: '8px',
                border: isSelected ? '2px solid #388E3C' : '1px solid #EAEAEA',
                background: isSelected ? '#E8F5E9' : '#FFFFFF',
                boxShadow: isSelected ? '0 4px 12px rgba(56, 142, 60, 0.15)' : 'none',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}
            >
              <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{foodEmojis[idx % foodEmojis.length]}</span>
              <div className="info" style={{ flex: 1, minWidth: 0 }}>
                <h4 style={{
                  color: isSelected ? '#1B5E20' : '#1A1A1A',
                  fontWeight: isSelected ? 700 : 600,
                  fontSize: '0.88rem',
                  lineHeight: 1.3,
                  margin: 0
                }}>
                  {recipe.title}
                </h4>
                <p style={{ fontSize: '0.75rem', color: isSelected ? '#2E7D32' : '#666', margin: '2px 0 0 0' }}>
                  {isSelected ? '✓ Currently Displayed' : 'Click to view recipe'}
                </p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                {recipe.score && (
                  <span className="score" style={{
                    background: isSelected ? '#388E3C' : '#FF9800',
                    color: '#fff',
                    fontSize: '0.7rem',
                    padding: '2px 6px',
                    borderRadius: '10px',
                    fontWeight: 700
                  }}>
                    {recipe.score.toFixed(2)}
                  </span>
                )}
                {isSelected && (
                  <FiCheckCircle size={14} color="#2E7D32" style={{ marginTop: '2px' }} />
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
};

export default RetrievedRecipes;

