import { motion, AnimatePresence } from 'motion/react';
import { FiRefreshCw, FiSearch } from 'react-icons/fi';

const RewrittenQueryBanner = ({ query, rewrittenQuery }) => {
  if (!query) return null;

  const isRewritten = rewrittenQuery && query.toLowerCase().trim() !== rewrittenQuery.toLowerCase().trim();

  return (
    <AnimatePresence>
      <motion.div
        className="rewritten-query-banner"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
      >
        <div style={{ fontSize: '1.2rem', flexShrink: 0 }}>
          {isRewritten ? <FiRefreshCw color="#2E7D32" /> : <FiSearch color="#666" />}
        </div>
        <div>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: isRewritten ? '#2E7D32' : '#555', marginBottom: '0.3rem' }}>
            {isRewritten ? '🔄 Query Rewritten (using conversation memory)' : '🔍 Search Query'}
          </h4>
          {isRewritten ? (
            <div style={{ fontSize: '0.9rem' }}>
              <span style={{ color: '#888' }}>You said: </span>
              <span style={{ color: '#666', fontWeight: 600 }}>"{query}"</span>
              <span style={{ color: '#388E3C', margin: '0 0.5rem', fontWeight: 800 }}>→</span>
              <span style={{ color: '#888' }}>Understood as: </span>
              <span style={{ color: '#1B5E20', fontWeight: 700 }}>"{rewrittenQuery}"</span>
            </div>
          ) : (
            <span style={{ color: '#333', fontWeight: 600 }}>"{query}"</span>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default RewrittenQueryBanner;
