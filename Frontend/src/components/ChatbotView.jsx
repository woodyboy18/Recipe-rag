import { useState, useRef, useEffect } from 'react';
import { motion } from 'motion/react';
import { FiSend, FiTrash2, FiSliders, FiCheckCircle, FiSearch } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import RecipeCard from './RecipeCard';
import RewrittenQueryBanner from './RewrittenQueryBanner';
import RetrievedRecipes from './RetrievedRecipes';
import CookingTip from './CookingTip';
import AIResponse from './AIResponse';
import LoadingSpinner from './LoadingSpinner';

const SUGGESTIONS = [
  '🍓 show me recipe with strawberry and milk',
  '🍰 create a new dessert with strawberry and milk but no eggs',
  '🍳 high protein breakfast without eggs and milk',
  '🫘 Recipe with soybean and rice I have'
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

  return {
    title,
    ingredients: ingredients.length > 0 ? ingredients : (retRec.ingredients ? [retRec.ingredients] : []),
    instructions: instructions.length > 0 ? instructions : (retRec.instructions ? [retRec.instructions] : [])
  };
}

const AssistantMessageCard = ({ msg, favorites = [], onToggleFavorite }) => {
  const data = msg.data || {};
  const retrieved = data.retrievedRecipes || [];
  const defaultRecipe = data.recipe || {};
  const mode = data.mode || 'retrieved';
  const scores = data.scores || {};
  const provenance = data.provenance || [];

  const [selectedIndex, setSelectedIndex] = useState(null);
  const [activeRecipe, setActiveRecipe] = useState(defaultRecipe);

  const handleSelectRecipe = (idx) => {
    setSelectedIndex(idx);
    const selectedRetrieved = retrieved[idx];
    if (selectedRetrieved) {
      const parsed = parseRetrievedRecipe(selectedRetrieved);
      if (parsed) setActiveRecipe(parsed);
    }
  };

  const isFav = activeRecipe && favorites.some(
    f => f.title?.toLowerCase() === activeRecipe.title?.toLowerCase()
  );

  return (
    <div className="assistant-message-card">
      {data.rewrittenQuery && (
        <RewrittenQueryBanner
          query={msg.query}
          rewrittenQuery={data.rewrittenQuery}
        />
      )}

      <div className="recipe-layout">
        <div className="recipe-main-column">
          <RecipeCard
            recipe={activeRecipe}
            isFavorite={isFav}
            onToggleFavorite={onToggleFavorite}
            mode={mode}
            scores={scores}
            provenance={provenance}
          />
          <AIResponse
            query={msg.query}
            rewrittenQuery={data.rewrittenQuery}
            recipeTitle={activeRecipe?.title || ''}
          />
        </div>

        <div className="recipe-side-column">
          <RetrievedRecipes
            recipes={retrieved}
            selectedIndex={selectedIndex}
            onSelectRecipe={handleSelectRecipe}
          />
          <CookingTip />
        </div>
      </div>
    </div>
  );
};

const ChatbotView = ({
  messages,
  onSendMessage,
  onClearMemory,
  isLoading,
  backendStatus,
  favorites = [],
  onToggleFavorite
}) => {
  const [inputQuery, setInputQuery] = useState('');
  const [selectedMode, setSelectedMode] = useState('auto'); // 'auto', 'find', 'novel'
  const [selectedNovelty, setSelectedNovelty] = useState('balanced'); // 'safe', 'balanced', 'creative'
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    onSendMessage(inputQuery.trim(), selectedMode, selectedNovelty);
    setInputQuery('');
  };

  const handleChipClick = (suggestion) => {
    const cleanText = suggestion.replace(/^[\u1F300-\u1F9FF\u2600-\u26FF\u2700-\u27BF]\s*/, '');
    onSendMessage(cleanText, selectedMode, selectedNovelty);
  };

  return (
    <div className="chatbot-wrapper">
      {/* Top Header */}
      <header className="chatbot-header">
        <div className="header-title">
          <div className="chef-avatar">👨‍🍳</div>
          <div>
            <h3>RecipeFusion</h3>
            <span className="status-indicator">
              <span className={`status-dot ${backendStatus === 'ready' ? 'online' : 'offline'}`} />
              {backendStatus === 'ready' ? 'Connected to Ollama & Recipe Database' : 'Connecting to RAG server...'}
            </span>
          </div>
        </div>

        <button className="clear-chat-btn" onClick={onClearMemory} title="Start New Fresh Chat">
          <FiTrash2 /> New Chat
        </button>
      </header>

      {/* Chat Messages Body */}
      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <div className="welcome-chat-hero">
            <div className="hero-badge">✨ RecipeFusion AI Engine</div>
            <h2>What would you like to cook today?</h2>
            <p>
              Search exact dataset recipes or create newly synthesized grounded recipes supported by ingredient evidence!
            </p>

            <div className="suggestion-chips-grid">
              {SUGGESTIONS.map((s, idx) => (
                <button
                  key={idx}
                  className="chat-suggestion-chip"
                  onClick={() => handleChipClick(s)}
                  disabled={isLoading}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`chat-bubble-row ${msg.sender}`}
            >
              {msg.sender === 'user' ? (
                <div className="user-message-bubble">
                  <p>{msg.text}</p>
                </div>
              ) : (
                <AssistantMessageCard
                  msg={msg}
                  favorites={favorites}
                  onToggleFavorite={onToggleFavorite}
                />
              )}
            </motion.div>
          ))
        )}

        {isLoading && (
          <div className="chat-bubble-row assistant">
            <div className="assistant-loading-box">
              <LoadingSpinner />
              <p>Generating Grounded Recipe...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Mode & Novelty Controls Toolbar */}
      <div style={{
        padding: '0.5rem 1.5rem',
        background: '#FAF5FF',
        borderTop: '1px solid #E9D5FF',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap',
        fontSize: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600, color: '#6B21A8' }}>
          <FiSliders /> Mode:
        </div>

        <div style={{ display: 'flex', gap: '0.25rem', background: '#FFF', padding: '3px', borderRadius: '8px', border: '1px solid #DDD' }}>
          <button
            type="button"
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: selectedMode === 'auto' ? 600 : 400,
              background: selectedMode === 'auto' ? '#7C3AED' : 'transparent',
              color: selectedMode === 'auto' ? '#FFF' : '#4B5563'
            }}
            onClick={() => setSelectedMode('auto')}
          >
            Auto
          </button>
          <button
            type="button"
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: selectedMode === 'find' ? 600 : 400,
              background: selectedMode === 'find' ? '#059669' : 'transparent',
              color: selectedMode === 'find' ? '#FFF' : '#4B5563'
            }}
            onClick={() => setSelectedMode('find')}
          >
            Find Existing
          </button>
          <button
            type="button"
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: selectedMode === 'novel' ? 600 : 400,
              background: selectedMode === 'novel' ? '#D97706' : 'transparent',
              color: selectedMode === 'novel' ? '#FFF' : '#4B5563'
            }}
            onClick={() => setSelectedMode('novel')}
          >
            Create New
          </button>
        </div>

        {selectedMode === 'novel' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginLeft: 'auto' }}>
            <span style={{ fontWeight: 600, color: '#B45309' }}>Novelty:</span>
            <select
              value={selectedNovelty}
              onChange={(e) => setSelectedNovelty(e.target.value)}
              style={{
                padding: '4px 8px',
                borderRadius: '6px',
                border: '1px solid #FCD34D',
                background: '#FFFBEB',
                color: '#92400E',
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              <option value="safe">Safe</option>
              <option value="balanced">Balanced</option>
              <option value="creative">Creative</option>
            </select>
          </div>
        )}
      </div>

      {/* Chat Input Bar */}
      <div className="chat-input-sticky-footer">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-input-field"
            placeholder="Type a recipe request or ingredients you have..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="chat-send-btn"
            disabled={!inputQuery.trim() || isLoading}
          >
            <FiSend /> Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatbotView;
