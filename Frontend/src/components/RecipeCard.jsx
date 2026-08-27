import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { FiHeart, FiClock, FiUsers, FiCheckCircle, FiLayers, FiAlertCircle } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';

const RecipeCard = ({ recipe, isFavorite: propIsFavorite, onToggleFavorite, scores, provenance, mode }) => {
  const [localIsFavorite, setLocalIsFavorite] = useState(false);

  if (!recipe || !recipe.title) {
    return (
      <div className="recipe-card" style={{ textAlign: 'center', padding: '4rem 2rem', color: '#999' }}>
        <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🍽️</span>
        <p style={{ fontSize: '1.1rem' }}>No recipe selected yet.</p>
        <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>Search or ask for something delicious!</p>
      </div>
    );
  }

  const isFavorite = propIsFavorite !== undefined ? propIsFavorite : localIsFavorite;

  const handleHeartClick = () => {
    if (onToggleFavorite) {
      onToggleFavorite(recipe);
    } else {
      setLocalIsFavorite(!localIsFavorite);
    }
  };

  const { title, ingredients = [], instructions = [], prep_time, cook_time, servings } = recipe;
  const isSynthesized = mode === 'synthesized' || mode === 'novel';

  return (
    <motion.div
      className="recipe-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 100, damping: 15 }}
    >
      {/* Mode Badge Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1rem'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          borderRadius: '20px',
          fontSize: '0.85rem',
          fontWeight: 600,
          background: isSynthesized ? 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)' : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
          color: '#FFF',
          boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
        }}>
          {isSynthesized ? <HiSparkles /> : <FiCheckCircle />}
          {isSynthesized ? 'Newly Synthesized Recipe' : 'Retrieved Existing Recipe'}
        </div>

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleHeartClick}
          style={{
            background: '#FFF', border: '1px solid #E5E7EB', borderRadius: '50%',
            width: '38px', height: '38px', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(0,0,0,0.05)'
          }}
          title={isFavorite ? 'Remove from favorites' : 'Save to favorites'}
        >
          <FiHeart size={18} fill={isFavorite ? "#ef4444" : "none"} color={isFavorite ? "#ef4444" : "#999"} />
        </motion.button>
      </div>

      {/* Image header placeholder */}
      <div style={{
        background: isSynthesized ? 'linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%)' : 'linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)',
        height: '160px',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '1.5rem'
      }}>
        <span style={{ fontSize: '4.5rem' }}>{isSynthesized ? '✨🍳' : '🍳'}</span>
      </div>

      {/* Title */}
      <h2 className="recipe-title">{title}</h2>

      {/* Dynamic Meta badges without hardcoded values */}
      <div className="meta-badges">
        <span><FiClock style={{ marginRight: '4px' }} /> Prep: {prep_time ? `${prep_time} mins` : 'Not calculated'}</span>
        <span>🍲 Cook: {cook_time ? `${cook_time} mins` : 'Not calculated'}</span>
        <span><FiUsers style={{ marginRight: '4px' }} /> Serves: {servings || '2'}</span>
      </div>

      {/* Validation & Novelty Scores Section for Synthesized Recipes */}
      {scores && (scores.novelty !== undefined || scores.constraint_satisfaction !== undefined) && (
        <div style={{
          background: '#F9FAFB',
          border: '1px solid #E5E7EB',
          borderRadius: '10px',
          padding: '1rem',
          margin: '1.2rem 0',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '0.75rem',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Constraints</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: scores.constraint_satisfaction >= 1.0 ? '#059669' : '#DC2626' }}>
              {(scores.constraint_satisfaction * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Grounding</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#2563EB' }}>
              {(scores.grounding * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Compatibility</div>
            <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#D97706' }}>
              {(scores.compatibility * 100).toFixed(0)}%
            </div>
          </div>
          {scores.novelty !== undefined && (
            <div>
              <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>Novelty</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 'bold', color: '#7C3AED' }}>
                {(scores.novelty * 100).toFixed(0)}%
              </div>
            </div>
          )}
        </div>
      )}

      {/* Provenance Evidence Recipes */}
      {provenance && provenance.length > 0 && (
        <div style={{ margin: '1rem 0', fontSize: '0.85rem', color: '#4B5563', background: '#EFF6FF', padding: '0.75rem 1rem', borderRadius: '8px' }}>
          <strong style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#1E40AF', marginBottom: '4px' }}>
            <FiLayers /> Evidence Sources:
          </strong>
          <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
            {provenance.map((p, i) => (
              <li key={i}>{p.title || `Recipe #${p.recipe_id}`}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Ingredients */}
      <div className="section-title">🧺 Ingredients</div>
      <div className="ingredient-chips">
        <AnimatePresence>
          {ingredients.map((ing, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.04 }}
            >
              {typeof ing === 'string' ? ing : `${ing.amount || ''} ${ing.unit || ''} ${ing.name || ''}`.trim()}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Instructions */}
      <div className="section-title">📝 Instructions</div>
      {instructions.map((step, idx) => (
        <motion.div
          key={idx}
          className="instruction-step"
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.08 }}
        >
          <div className="step-number">{idx + 1}</div>
          <p>{typeof step === 'string' ? step : step.text || ''}</p>
        </motion.div>
      ))}
    </motion.div>
  );
};

export default RecipeCard;
