import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import ChatbotView from './components/ChatbotView';
import SearchRecipesView from './components/SearchRecipesView';
import FavoritesView from './components/FavoritesView';
import AboutProjectView from './components/AboutProjectView';
import ThemeToggle from './components/ThemeToggle';
import Footer from './components/Footer';
import { queryRecipe, getMemory, clearMemory, checkHealth } from './api/recipeApi';
import './App.css';

const FAVORITES_STORAGE_KEY = 'culinary_rag_favorites';
const THEME_STORAGE_KEY = 'culinary_rag_theme';

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [isLoading, setIsLoading] = useState(false);
  const [memory, setMemory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY) || 'light';
    } catch {
      return 'light';
    }
  });

  const [favorites, setFavorites] = useState(() => {
    try {
      const saved = localStorage.getItem(FAVORITES_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {
      console.error('Failed to persist theme:', e);
    }
  }, [theme]);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackendStatus(data.status === 'ok' ? 'ready' : 'error');
      })
      .catch(() => setBackendStatus('error'));
  }, []);

  useEffect(() => {
    getMemory()
      .then((data) => {
        const mem = data.memory || [];
        setMemory(mem);
      })
      .catch(() => setMemory([]));
  }, []);

  const handleToggleFavorite = useCallback((recipe) => {
    if (!recipe || !recipe.title) return;
    setFavorites((prev) => {
      const exists = prev.some(
        (f) => f.title?.toLowerCase().trim() === recipe.title?.toLowerCase().trim()
      );
      let updated;
      if (exists) {
        updated = prev.filter(
          (f) => f.title?.toLowerCase().trim() !== recipe.title?.toLowerCase().trim()
        );
      } else {
        updated = [recipe, ...prev];
      }
      try {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to persist favorites:', e);
      }
      return updated;
    });
  }, []);

  const handleSendMessage = useCallback(async (queryText, mode = 'auto', noveltyLevel = 'balanced') => {
    if (!queryText.trim()) return;

    const userMsg = { sender: 'user', text: queryText };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const data = await queryRecipe(queryText, mode, noveltyLevel);

      const assistantMsg = {
        sender: 'assistant',
        query: data.query,
        data: {
          rewrittenQuery: data.rewritten_query,
          constraints: data.constraints,
          mode: data.mode,
          recipe: data.recipe,
          retrievedRecipes: data.retrieved_recipes || [],
          scores: data.scores || {},
          provenance: data.provenance || [],
          answerRaw: data.answer_raw,
        }
      };

      setMessages((prev) => [...prev, assistantMsg]);

      const memData = await getMemory();
      setMemory(memData.memory || []);

    } catch (err) {
      const errorMsg = {
        sender: 'assistant',
        query: queryText,
        data: {
          recipe: {
            title: 'Unable to process query',
            ingredients: ['Make sure python api_server.py is running on http://localhost:5000'],
            instructions: [err.message || 'Server connection error']
          },
          retrievedRecipes: []
        }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleClearMemory = useCallback(async () => {
    await clearMemory();
    setMemory([]);
    setMessages([]);
  }, []);

  const handleSelectMemoryQuery = useCallback((queryText) => {
    setActiveTab('home');
    handleSendMessage(queryText);
  }, [handleSendMessage]);

  const handleSwitchToChat = useCallback((queryText) => {
    setActiveTab('home');
    if (queryText) {
      handleSendMessage(queryText);
    }
  }, [handleSendMessage]);

  return (
    <div className="app-container" data-theme={theme}>
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        favoritesCount={favorites.length}
        memory={memory}
        onClearMemory={handleClearMemory}
        onSelectMemory={handleSelectMemoryQuery}
      />

      <main className="main-content">
        <div className="top-header-bar">
          <ThemeToggle theme={theme} onThemeChange={setTheme} />
        </div>

        {backendStatus === 'error' && (
          <div className="backend-warning">
            ⚠️ Backend server is offline. Start the Flask API: <code>python api_server.py</code>
          </div>
        )}

        {activeTab === 'home' && (
          <ChatbotView
            messages={messages}
            onSendMessage={handleSendMessage}
            onClearMemory={handleClearMemory}
            isLoading={isLoading}
            backendStatus={backendStatus}
            favorites={favorites}
            onToggleFavorite={handleToggleFavorite}
          />
        )}

        {activeTab === 'search' && (
          <SearchRecipesView
            favorites={favorites}
            onToggleFavorite={handleToggleFavorite}
            onSwitchToChat={handleSwitchToChat}
          />
        )}

        {activeTab === 'favorites' && (
          <FavoritesView
            favorites={favorites}
            onToggleFavorite={handleToggleFavorite}
            onExploreRecipes={() => setActiveTab('search')}
          />
        )}

        {activeTab === 'about' && (
          <AboutProjectView />
        )}

        <Footer />
      </main>
    </div>
  );
}

export default App;
