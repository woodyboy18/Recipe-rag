import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { FiHeart, FiClock, FiTrash2, FiArrowRight, FiX } from 'react-icons/fi';
import RecipeCard from './RecipeCard';

const foodEmojis = ['🍲', '🥘', '🍚', '🍛', '🥣', '🥗', '🥞', '🍝'];

const FavoritesView = ({ favorites = [], onToggleFavorite, onExploreRecipes }) => {
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  return (
    <div className="favorites-view-container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'var(--card-bg)',
          border: '1px solid var(--border-color)',
          borderRadius: '20px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ fontSize: '2.2rem' }}>💖</span>
          <div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-dark)', margin: 0 }}>
              My Favorite Recipes
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
              {favorites.length === 0
                ? 'You have not saved any favorite recipes yet'
                : `You have saved ${favorites.length} delicious recipe${favorites.length > 1 ? 's' : ''}`}
            </p>
          </div>
        </div>

        {favorites.length > 0 && (
          <button
            onClick={onExploreRecipes}
            style={{
              background: 'var(--primary-green)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '30px',
              padding: '10px 22px',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            Find More Recipes <FiArrowRight />
          </button>
        )}
      </motion.div>

      {/* Selected Recipe Modal / Expanded Card */}
      <AnimatePresence>
        {selectedRecipe && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              zIndex: 1000,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem'
            }}
            onClick={() => setSelectedRecipe(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              style={{
                background: 'var(--card-bg)',
                borderRadius: '20px',
                maxWidth: '750px',
                width: '100%',
                maxHeight: '90vh',
                overflowY: 'auto',
                padding: '2rem',
                position: 'relative',
                border: '1px solid var(--border-color)'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedRecipe(null)}
                style={{
                  position: 'absolute',
                  top: '20px',
                  right: '20px',
                  background: 'var(--pill-bg)',
                  color: 'var(--text-dark)',
                  border: 'none',
                  borderRadius: '50%',
                  width: '36px',
                  height: '36px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <FiX size={20} />
              </button>

              <RecipeCard
                recipe={selectedRecipe}
                isFavorite={true}
                onToggleFavorite={(rec) => {
                  onToggleFavorite(rec);
                  setSelectedRecipe(null);
                }}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Favorites List Grid */}
      {favorites.length > 0 ? (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '1.5rem'
        }}>
          {favorites.map((recipe, idx) => {
            const ingredientsCount = Array.isArray(recipe.ingredients) ? recipe.ingredients.length : 0;
            const instructionsCount = Array.isArray(recipe.instructions) ? recipe.instructions.length : 0;

            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                style={{
                  background: 'var(--card-bg)',
                  borderRadius: '16px',
                  border: '1px solid var(--border-color)',
                  padding: '1.5rem',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
              >
                <div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '1rem'
                  }}>
                    <span style={{ fontSize: '2.5rem' }}>{foodEmojis[idx % foodEmojis.length]}</span>
                    <button
                      onClick={() => onToggleFavorite(recipe)}
                      style={{
                        background: 'rgba(239, 83, 80, 0.1)',
                        border: '1px solid rgba(239, 83, 80, 0.2)',
                        borderRadius: '50%',
                        width: '38px',
                        height: '38px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer'
                      }}
                      title="Remove from favorites"
                    >
                      <FiHeart size={18} fill="#EF5350" color="#EF5350" />
                    </button>
                  </div>

                  <h3 style={{
                    fontSize: '1.2rem',
                    fontWeight: 700,
                    color: 'var(--text-dark)',
                    marginBottom: '0.6rem',
                    lineHeight: 1.3
                  }}>
                    {recipe.title || 'Untitled Recipe'}
                  </h3>

                  <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', flexWrap: 'wrap' }}>
                    <span style={{
                      background: 'var(--light-green)',
                      color: 'var(--primary-green)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      padding: '4px 10px',
                      borderRadius: '12px'
                    }}>
                      🧺 {ingredientsCount} Ingredients
                    </span>
                    <span style={{
                      background: 'var(--pill-bg)',
                      color: 'var(--accent-orange)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      padding: '4px 10px',
                      borderRadius: '12px'
                    }}>
                      📝 {instructionsCount} Steps
                    </span>
                  </div>

                  {Array.isArray(recipe.ingredients) && recipe.ingredients.length > 0 && (
                    <p style={{
                      fontSize: '0.85rem',
                      color: 'var(--text-muted)',
                      lineHeight: 1.4,
                      marginBottom: '1.2rem',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden'
                    }}>
                      <strong>Key items:</strong> {recipe.ingredients.slice(0, 4).join(', ')}
                      {recipe.ingredients.length > 4 ? '...' : ''}
                    </p>
                  )}
                </div>

                <button
                  onClick={() => setSelectedRecipe(recipe)}
                  style={{
                    width: '100%',
                    background: 'var(--light-green)',
                    color: 'var(--primary-green)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '12px',
                    padding: '10px 16px',
                    fontSize: '0.9rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  View Full Recipe <FiArrowRight />
                </button>
              </motion.div>
            );
          })}
        </div>
      ) : (
        /* Empty State */
        <div style={{
          textAlign: 'center',
          padding: '5rem 2rem',
          background: 'var(--card-bg)',
          borderRadius: '20px',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1rem' }}>🤍</span>
          <h3 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '0.5rem' }}>
            No Saved Recipes Yet
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '450px', margin: '0 auto 1.8rem', fontSize: '0.95rem' }}>
            When you find a recipe you love in the Chatbot or Search Engine, tap the heart icon (❤️) on the recipe card to save it here!
          </p>
          <button
            onClick={onExploreRecipes}
            style={{
              background: 'var(--primary-green)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '30px',
              padding: '12px 28px',
              fontWeight: 700,
              fontSize: '0.95rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(56, 142, 60, 0.25)'
            }}
          >
            Start Exploring Recipes <FiArrowRight />
          </button>
        </div>
      )}
    </div>
  );
};

export default FavoritesView;
