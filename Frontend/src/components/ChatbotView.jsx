import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { FiSend, FiTrash2 } from 'react-icons/fi';
import { HiSparkles } from 'react-icons/hi';
import RecipeCard from './RecipeCard';
import RewrittenQueryBanner from './RewrittenQueryBanner';
import RetrievedRecipes from './RetrievedRecipes';
import CookingTip from './CookingTip';
import AIResponse from './AIResponse';
import LoadingSpinner from './LoadingSpinner';

const SUGGESTIONS = [
  '🍗 Chicken Biryani',
  '🍳 High protein breakfast without eggs',
  '🫘 Recipe with soybean and rice I have',
  '🥘 Paneer Butter Masala',
  '🥗 Low calorie vegetarian dinner'
];

function parseRetrievedRecipe(retRec) {
  if (!retRec) return null;
  const title = retRec.title || 'Delicious Recipe';
  let ingredients = [];
  let instructions = [];

  const snippet = retRec.snippet || '';
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

  if (ingredients.length === 0) {
    ingredients = [
      'Fresh Core Recipe Ingredients',
      'Natural Seasonings & Spices',
      'Healthy Base Oil / Broth'
    ];
  }
  if (instructions.length === 0) {
    instructions = [
      'Prepare all fresh ingredients as specified.',
      'Combine ingredients in a cooking vessel over medium heat.',
      'Cook until thoroughly prepared and serve warm!'
    ];
  }

  return {
    title,
    ingredients,
    instructions
  };
}

function recipeViolatesConstraints(recipeObj, avoidList) {
  if (!recipeObj || !avoidList || avoidList.length === 0) return false;
  const terms = avoidList.map(a => a.toLowerCase().trim()).filter(Boolean);
  if (terms.length === 0) return false;

  const titleLower = (recipeObj.title || '').toLowerCase();
  const ingLower = Array.isArray(recipeObj.ingredients)
    ? recipeObj.ingredients.map(i => (typeof i === 'string' ? i : i.name || '').toLowerCase()).join(' ')
    : '';
  const snippetLower = (recipeObj.snippet || '').toLowerCase();

  const combined = `${titleLower} ${ingLower} ${snippetLower}`;

  return terms.some(term => {
    const pattern = new RegExp(`\\b${term}(?:s|es)?\\b`, 'i');
    return pattern.test(combined) || combined.includes(term);
  });
}

const AssistantMessageCard = ({ msg, favorites = [], onToggleFavorite }) => {
  const data = msg.data || {};
  const avoidList = data.constraints?.ingredients_to_avoid || [];
  const retrieved = data.retrievedRecipes || [];
  const defaultRecipe = data.recipe || {};

  // Check if default recipe violates constraints (e.g. user said "I do not have strawberry")
  const defaultViolates = recipeViolatesConstraints(defaultRecipe, avoidList);

  let initialSelectedIndex = null;
  let initialDisplayRecipe = defaultRecipe;

  // If default recipe contains avoided ingredient, find top retrieved recipe candidate that satisfies constraints
  if (defaultViolates && retrieved.length > 0) {
    const cleanIndex = retrieved.findIndex(r => !recipeViolatesConstraints(r, avoidList));
    if (cleanIndex !== -1) {
      initialSelectedIndex = cleanIndex;
      initialDisplayRecipe = parseRetrievedRecipe(retrieved[cleanIndex]);
    }
  }

  const [selectedIndex, setSelectedIndex] = useState(initialSelectedIndex);
  const [activeRecipe, setActiveRecipe] = useState(initialDisplayRecipe);

  const handleSelectRecipe = (idx) => {
    setSelectedIndex(idx);
    const selectedRetrieved = retrieved[idx];
    if (selectedRetrieved) {
      setActiveRecipe(parseRetrievedRecipe(selectedRetrieved));
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
    onSendMessage(inputQuery.trim());
    setInputQuery('');
  };

  const handleChipClick = (suggestion) => {
    const cleanText = suggestion.replace(/^[\u1F300-\u1F9FF\u2600-\u26FF\u2700-\u27BF]\s*/, '');
    onSendMessage(cleanText);
  };

  return (
    <div className="chatbot-wrapper">
      {/* Top Header */}
      <header className="chatbot-header">
        <div className="header-title">
          <div className="chef-avatar">👨‍🍳</div>
          <div>
            <h3>Culinary RAG AI Chatbot</h3>
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
            <div className="hero-badge">✨ Memory-Augmented RAG Engine</div>
            <h2>What would you like to cook today?</h2>
            <p>
              Ask me for any recipe, tell me what ingredients you have, or set diet & ingredient restrictions!
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
              <p>Generating Your Recipe...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
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

