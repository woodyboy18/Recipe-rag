import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { FiSearch } from 'react-icons/fi';

const popularSearches = ['Paneer recipes', 'Chicken curry', 'Egg fried rice', 'Vegetable soup', 'Pasta recipes'];

const HeroSection = ({ onSearch, isLoading, currentQuery }) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (currentQuery) {
      setQuery('');
    }
  }, [currentQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <motion.div
      className="hero-section"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Hi there! 👋</h1>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 700, color: '#1A1A1A', marginBottom: '0.5rem' }}>
            What would you like to cook today?
          </h2>
          <p>Search any ingredients, dietary preferences, or follow-up adjustments (e.g. "no eggs", "I have soyabean and rice").</p>
        </div>
        <div style={{ fontSize: '4rem', lineHeight: 1 }}>🍲🥗🫕</div>
      </div>

      <form onSubmit={handleSubmit} className="search-bar-container" style={{ marginTop: '2rem' }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', flex: 1 }}>
          <FiSearch style={{ position: 'absolute', left: '20px', color: '#999', fontSize: '1.1rem' }} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='e.g. "high protein breakfast", "no eggs", or "I have soybean and rice"...'
            style={{ paddingLeft: '50px' }}
          />
        </div>
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Searching...' : 'Find Recipe ✨'}
        </button>
      </form>

      <div className="popular-chips">
        <span>Popular searches:</span>
        {popularSearches.map((term, index) => (
          <motion.button
            key={index}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => { setQuery(term); onSearch(term); }}
          >
            {term}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
};

export default HeroSection;
