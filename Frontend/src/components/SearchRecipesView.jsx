import { useState } from 'react';
import { motion } from 'motion/react';
import { FiSearch, FiArrowRight } from 'react-icons/fi';
import RecipeCard from './RecipeCard';
import RetrievedRecipes from './RetrievedRecipes';
import AIResponse from './AIResponse';
import LoadingSpinner from './LoadingSpinner';
import { queryRecipe } from '../api/recipeApi';

const QUICK_TAGS = [
  { label: '🍓 Strawberry & Milk', query: 'show me recipe with strawberry and milk' },
  { label: '🍰 New Strawberry Dessert', query: 'create a new dessert with strawberry and milk but no eggs' },
  { label: '🍳 High Protein Breakfast', query: 'high protein breakfast without eggs and milk' },
  { label: '🫘 Soybean & Rice', query: 'Nutritious recipe with soybean and rice' },
];

function parseRetrievedRecipe(retRec) {
  if (!retRec) return null;
  const title = retRec.title || 'Delicious Recipe';
  let ingredients = [];
  let instructions = [];

  const snippet = retRec.snippet || retRec.document || '';
  if (snippet) {
    const lines = snippet.split('\n');
    let currSec = null;
    for (const l of lines) {
      const s = l.trim();
      if (!s) continue;
      if (s.toLowerCase().startsWith('ingredients:')) {
        currSec = 'ing';
        const val = s.split(':', 2)[1]?.trim();
        if (val) ingredients.push(...val.split(',').map(i => i.trim()).filter(Boolean));
      } else if (s.toLowerCase().startsWith('instructions:') || s.toLowerCase().startsWith('directions:')) {
        currSec = 'inst';
        const val = s.split(':', 2)[1]?.trim();
        if (val) instructions.push(val);
      } else if (currSec === 'ing') {
        ingredients.push(...s.split(',').map(i => i.trim()).filter(Boolean));
      } else if (currSec === 'inst') {
        instructions.push(s);
      }
    }
  }

  return { title, ingredients: ingredients.length > 0 ? ingredients : (retRec.ingredients ? [retRec.ingredients] : []), instructions: instructions.length > 0 ? instructions : (retRec.instructions ? [retRec.instructions] : []) };
}

const SearchRecipesView = ({ favorites = [], onToggleFavorite, onSwitchToChat }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMode, setSelectedMode] = useState('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [activeRecipe, setActiveRecipe] = useState(null);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSearch = async (queryToSearch) => {
    const q = (queryToSearch || searchTerm).trim();
    if (!q || isLoading) return;

    setIsLoading(true);
    setErrorMessage('');
    setSearchTerm(q);

    try {
      const data = await queryRecipe(q, selectedMode);
      setSearchResult(data);
      setActiveRecipe(data.recipe || null);
      setSelectedIndex(null);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to search recipe. Make sure backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectRetrieved = (idx) => {
    setSelectedIndex(idx);
    if (searchResult?.retrieved_recipes?.[idx]) {
      const parsed = parseRetrievedRecipe(searchResult.retrieved_recipes[idx]);
      if (parsed) setActiveRecipe(parsed);
    }
  };

  const isFav = activeRecipe && favorites.some(
    f => f.title?.toLowerCase() === activeRecipe.title?.toLowerCase()
  );

  return (
    <div className="search-view-container" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header Hero */}
      <motion.div
        className="search-header-hero"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'var(--card-bg)',
          border: '1px solid var(--border-color)',
          borderRadius: '20px',
          padding: '2.5rem 2rem',
          marginBottom: '2rem',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '2.2rem' }}>🔍</span>
          <div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-dark)', margin: 0 }}>
              RecipeFusion Search
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', margin: 0 }}>
              Retrieve exact existing recipes or synthesize grounded novel recipes supported by dataset evidence
            </p>
          </div>
        </div>

        {/* Search Input Bar */}
        <form
          onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
          style={{ display: 'flex', gap: '10px', marginTop: '1.5rem', maxWidth: '850px' }}
        >
          <div style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
            <FiSearch style={{ position: 'absolute', left: '18px', color: 'var(--text-muted)', fontSize: '1.2rem' }} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder='e.g. "show me recipe with strawberry and milk", "create a new dessert"...'
              style={{
                width: '100%',
                padding: '14px 20px 14px 50px',
                borderRadius: '30px',
                border: '2px solid var(--border-color)',
                fontSize: '1rem',
                outline: 'none',
                backgroundColor: 'var(--input-bg)',
                color: 'var(--text-dark)',
                boxShadow: 'var(--shadow-sm)'
              }}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !searchTerm.trim()}
            style={{
              padding: '0 28px',
              backgroundColor: 'var(--primary-green)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '30px',
              fontWeight: 700,
              fontSize: '1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 12px rgba(56, 142, 60, 0.25)',
              opacity: (isLoading || !searchTerm.trim()) ? 0.6 : 1
            }}
          >
            {isLoading ? 'Searching...' : 'Search ✨'}
          </button>
        </form>

        {/* Popular Tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '1.2rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 600 }}>Try asking:</span>
          {QUICK_TAGS.map((tag, idx) => (
            <button
              key={idx}
              onClick={() => handleSearch(tag.query)}
              disabled={isLoading}
              style={{
                background: 'var(--card-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--primary-green)',
                padding: '6px 14px',
                borderRadius: '20px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {tag.label}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="error-banner">
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '3rem 0' }}>
          <LoadingSpinner />
          <p style={{ color: 'var(--primary-green)', fontWeight: 600, marginTop: '1rem' }}>
            Processing Grounded Recipe Search...
          </p>
        </div>
      )}

      {/* Search Results Display */}
      {!isLoading && searchResult && activeRecipe && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Ask in Chat Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'var(--light-green)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '12px 18px',
            marginBottom: '1.5rem'
          }}>
            <span style={{ color: 'var(--primary-green)', fontSize: '0.9rem', fontWeight: 600 }}>
              💡 Want to ask follow-up questions or adapt this recipe in Chat?
            </span>
            <button
              onClick={() => onSwitchToChat && onSwitchToChat(searchResult.query)}
              style={{
                background: 'var(--primary-green)',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '20px',
                padding: '6px 16px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              Open in Chatbot <FiArrowRight />
            </button>
          </div>

          <div className="recipe-layout">
            <div className="recipe-main-column">
              <RecipeCard
                recipe={activeRecipe}
                isFavorite={isFav}
                onToggleFavorite={onToggleFavorite}
                mode={searchResult.mode}
                scores={searchResult.scores}
                provenance={searchResult.provenance}
              />
              <AIResponse
                query={searchResult.query}
                rewrittenQuery={searchResult.rewritten_query}
                recipeTitle={activeRecipe?.title || ''}
              />
            </div>

            <div className="recipe-side-column">
              <RetrievedRecipes
                recipes={searchResult.retrieved_recipes || []}
                selectedIndex={selectedIndex}
                onSelectRecipe={handleSelectRetrieved}
              />
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default SearchRecipesView;
