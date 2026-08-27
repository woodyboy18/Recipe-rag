import { motion } from 'motion/react';

const AIResponse = ({ query, rewrittenQuery, recipeTitle }) => {
  if (!query && !recipeTitle) return null;

  const isRewritten = rewrittenQuery && query !== rewrittenQuery;
  let message = `Here is a custom recipe match from our database for "${recipeTitle || query}"!`;
  if (isRewritten) {
    message = `I tailored your search from "${query}" → "${rewrittenQuery}" to stick strictly to your specified ingredients and preferences. Enjoy cooking ${recipeTitle}!`;
  } else if (recipeTitle) {
    message = `Here is a great recipe for ${recipeTitle} tailored to your request. Bon Appétit! 👨‍🍳✨`;
  }

  return (
    <motion.div
      className="ai-response-banner"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '1rem',
        background: 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)',
        border: '1px solid #90CAF9',
        borderRadius: '12px',
        padding: '1.2rem',
        marginTop: '1.5rem'
      }}
    >
      <div style={{ fontSize: '2.5rem', flexShrink: 0 }}>👨‍🍳</div>
      <div>
        <h4 style={{ fontWeight: 700, marginBottom: '0.4rem', color: '#1565C0', fontSize: '1rem' }}>
          💬 Chef AI Assistant Note
        </h4>
        <p style={{ lineHeight: 1.6, color: '#1E88E5', fontSize: '0.92rem' }}>{message}</p>
      </div>
    </motion.div>
  );
};

export default AIResponse;
