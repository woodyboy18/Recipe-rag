import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { FiHeart, FiClock, FiUsers } from 'react-icons/fi';

const RecipeCard = ({ recipe, isFavorite: propIsFavorite, onToggleFavorite }) => {
  const [localIsFavorite, setLocalIsFavorite] = useState(false);

  if (!recipe || !recipe.title) {
    return (
      <div className="recipe-card" style={{ textAlign: 'center', padding: '4rem 2rem', color: '#999' }}>
        <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🍽️</span>
        <p style={{ fontSize: '1.1rem' }}>No recipe selected yet.</p>
        <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>Search for something delicious!</p>
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

  const { title, ingredients = [], instructions = [] } = recipe;

  return (
    <motion.div
      className="recipe-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 100, damping: 15 }}
    >
      {/* Image header */}
      <div style={{
        background: 'linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)',
        height: '200px',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        marginBottom: '1.5rem'
      }}>
        <span style={{ fontSize: '5rem' }}>🍳</span>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={handleHeartClick}
          style={{
            position: 'absolute', top: '16px', right: '16px',
            background: '#FFF', border: 'none', borderRadius: '50%',
            width: '42px', height: '42px', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
          title={isFavorite ? 'Remove from favorites' : 'Save to favorites'}
        >
          <FiHeart size={20} fill={isFavorite ? "#ef4444" : "none"} color={isFavorite ? "#ef4444" : "#999"} />
        </motion.button>
      </div>

      {/* Title */}
      <h2 className="recipe-title">{title}</h2>

      {/* Meta badges */}
      <div className="meta-badges">
        <span><FiClock style={{ marginRight: '4px' }} /> Prep Time 15 mins</span>
        <span>🍲 Cook Time 30 mins</span>
        <span><FiUsers style={{ marginRight: '4px' }} /> Serves 2</span>
        <span>🔥 520 kcal</span>
      </div>

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
          <p>{step}</p>
        </motion.div>
      ))}

      {/* Nutrition bar */}
      <div className="nutrition-bar" style={{ marginTop: '2rem' }}>
        <div>
          <div className="val">🔥 520</div>
          <div className="label">Calories</div>
        </div>
        <div>
          <div className="val">🌿 38g</div>
          <div className="label">Protein</div>
        </div>
        <div>
          <div className="val">🌾 42g</div>
          <div className="label">Carbs</div>
        </div>
        <div>
          <div className="val">💧 18g</div>
          <div className="label">Fat</div>
        </div>
      </div>
    </motion.div>
  );
};

export default RecipeCard;
