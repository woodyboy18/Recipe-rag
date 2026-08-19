import { motion } from 'motion/react';
import { FiHome, FiSearch, FiHeart, FiInfo, FiTrash2 } from 'react-icons/fi';

const navItems = [
  { id: 'home', name: 'Home', icon: <FiHome /> },
  { id: 'search', name: 'Search Recipes', icon: <FiSearch /> },
  { id: 'favorites', name: 'My Favorites', icon: <FiHeart /> },
  { id: 'about', name: 'About Project', icon: <FiInfo /> },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const itemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 }
};

const Sidebar = ({
  activeTab = 'home',
  onSelectTab,
  favoritesCount = 0,
  memory = [],
  onClearMemory,
  onSelectMemory
}) => {
  return (
    <aside className="sidebar">
      <div
        className="sidebar-logo"
        style={{ cursor: 'pointer' }}
        onClick={() => onSelectTab && onSelectTab('home')}
      >
        <span style={{ fontSize: '2rem' }}>🍳</span>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#388E3C' }}>Culinary RAG</h1>
          <p style={{ fontSize: '0.75rem', color: '#66BB6A', fontWeight: 500 }}>Recipe Assistant</p>
        </div>
      </div>

      <motion.ul
        className="sidebar-nav"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <motion.li
              key={item.id}
              variants={itemVariants}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={isActive ? 'active' : ''}
              onClick={() => onSelectTab && onSelectTab(item.id)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                <span>{item.name}</span>
              </div>
              {item.id === 'favorites' && favoritesCount > 0 && (
                <span style={{
                  background: isActive ? '#388E3C' : '#EF5350',
                  color: '#FFFFFF',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '12px'
                }}>
                  {favoritesCount}
                </span>
              )}
            </motion.li>
          );
        })}
      </motion.ul>

      {memory.length > 0 && (
        <div className="memory-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px' }}>
            <h3>Recent Memory</h3>
            <button
              onClick={onClearMemory}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#999' }}
              title="Clear memory"
            >
              <FiTrash2 size={14} />
            </button>
          </div>
          {memory.slice(-3).map((turn, idx) => (
            <div
              key={idx}
              className="memory-item"
              onClick={() => onSelectMemory && onSelectMemory(turn.user)}
              title="Click to ask in chat"
            >
              <strong>You:</strong> {turn.user}
            </div>
          ))}
        </div>
      )}

      <div className="sidebar-quote">
        <p>🥗 "Good food choices are good investments in yourself" 🌱</p>
      </div>
    </aside>
  );
};

export default Sidebar;
