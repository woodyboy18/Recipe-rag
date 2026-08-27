import { motion } from 'motion/react';
import { FiCpu, FiDatabase, FiMessageSquare, FiSearch, FiRepeat, FiCheckCircle, FiShield } from 'react-icons/fi';

const PIPELINE_STEPS = [
  {
    step: '01',
    title: 'Multi-Turn Conversational Memory',
    icon: <FiMessageSquare size={22} color="#388E3C" />,
    desc: 'Tracks dialogue turns and active constraints across the session, allowing natural follow-ups like "make it spicier", "without onions", or "what can I replace rice with?".'
  },
  {
    step: '02',
    title: 'Constraint Extraction & Intent Parsing',
    icon: <FiCheckCircle size={22} color="#1976D2" />,
    desc: 'Extracts ingredients to include, avoid, or substitute, dietary preferences, and cooking styles in real time before retrieval.'
  },
  {
    step: '03',
    title: 'Context-Aware Query Rewriting',
    icon: <FiRepeat size={22} color="#F57C00" />,
    desc: 'Reformulates conversational queries by merging past history and active dietary restrictions into an optimized dense search query.'
  },
  {
    step: '04',
    title: 'Hybrid Retrieval Engine (FAISS + BM25)',
    icon: <FiSearch size={22} color="#7B1FA2" />,
    desc: 'Combines FAISS dense semantic vector embeddings with BM25 sparse keyword matching and custom reranking across the recipe dataset.'
  },
  {
    step: '05',
    title: 'Local LLM Generation (Ollama)',
    icon: <FiCpu size={22} color="#C2185B" />,
    desc: 'Generates structured, step-by-step culinary instructions, exact ingredient lists, and tailored chef advice completely locally via Ollama.'
  },
  {
    step: '06',
    title: 'Interactive Frontend Interface',
    icon: <FiDatabase size={22} color="#00796B" />,
    desc: 'Clean, responsive UI with real-time chat, instant recipe cards, top alternative candidate switching, and saved favorites.'
  }
];

const AboutProjectView = () => {
  return (
    <div className="about-view-container" style={{ maxWidth: '1100px', margin: '0 auto' }}>
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 50%, #388E3C 100%)',
          borderRadius: '24px',
          padding: '3rem 2.5rem',
          color: '#FFFFFF',
          marginBottom: '2.5rem',
          boxShadow: '0 8px 30px rgba(56, 142, 60, 0.25)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ display: 'inline-block', background: 'rgba(255,255,255,0.2)', padding: '4px 14px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 600, marginBottom: '1rem' }}>
          ✨ Project Overview & Crux
        </div>
        <h1 style={{ fontSize: '2.4rem', fontWeight: 800, marginBottom: '0.8rem', lineHeight: 1.2, color: '#FFFFFF' }}>
          RecipeFusion Assistant
        </h1>
        <p style={{ fontSize: '1.1rem', opacity: 0.95, maxWidth: '800px', lineHeight: 1.6, color: '#FFFFFF' }}>
          An intelligent conversational AI culinary system that integrates Retrieval-Augmented Generation (RAG), 
          multi-turn conversational memory, constraint extraction, and local LLM synthesis for precise, personalized recipe generation.
        </p>
      </motion.div>

      {/* The Core Problem & Solution */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2.5rem'
      }}>
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            background: 'var(--card-bg)',
            borderRadius: '16px',
            padding: '2rem',
            border: '1px solid var(--border-color)',
            borderLeft: '5px solid #EF5350',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#EF5350', marginBottom: '0.8rem' }}>
            🛑 The Limitation of Traditional Search
          </h3>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
            Standard recipe search engines fail at multi-turn conversations. They cannot remember what you asked 2 minutes ago, struggle when you say <em>"I don't have butter"</em> or <em>"make this gluten-free"</em>, and hallucinate ingredient ratios when asked follow-ups.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            background: 'var(--card-bg)',
            borderRadius: '16px',
            padding: '2rem',
            border: '1px solid var(--border-color)',
            borderLeft: '5px solid var(--primary-green)',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary-green)', marginBottom: '0.8rem' }}>
            💡 Our Solution: Context-Aware RAG
          </h3>
          <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
            RecipeFusion merges contextual memory, real-time dietary constraint enforcement, hybrid dense & sparse information retrieval, and local Ollama inference to produce grounded, tailored recipes with step-by-step guidance.
          </p>
        </motion.div>
      </div>

      {/* End-to-End Pipeline */}
      <div style={{ marginBottom: '3rem' }}>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-dark)', marginBottom: '1.5rem', textAlign: 'center' }}>
          🧩 End-to-End System Pipeline
        </h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.2rem'
        }}>
          {PIPELINE_STEPS.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              style={{
                background: 'var(--card-bg)',
                borderRadius: '16px',
                padding: '1.6rem',
                border: '1px solid var(--border-color)',
                boxShadow: 'var(--shadow-sm)',
                display: 'flex',
                gap: '14px',
                alignItems: 'flex-start'
              }}
            >
              <div style={{
                background: 'var(--pill-bg)',
                borderRadius: '12px',
                width: '46px',
                height: '46px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                {item.icon}
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', letterSpacing: '0.5px' }}>
                  STEP {item.step}
                </div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-dark)', margin: '4px 0 6px 0' }}>
                  {item.title}
                </h4>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                  {item.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Tech Stack Highlights */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: 'var(--card-bg)',
          borderRadius: '20px',
          padding: '2rem',
          border: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-dark)', marginBottom: '1rem' }}>
          🛠️ Technology Stack
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem'
        }}>
          <div style={{ background: 'var(--pill-bg)', padding: '1rem', borderRadius: '12px' }}>
            <strong style={{ color: 'var(--primary-green)', display: 'block', marginBottom: '4px' }}>Frontend</strong>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>React 18 + Vite + Framer Motion</span>
          </div>
          <div style={{ background: 'var(--pill-bg)', padding: '1rem', borderRadius: '12px' }}>
            <strong style={{ color: '#1976D2', display: 'block', marginBottom: '4px' }}>Backend API</strong>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>Flask REST API + Python 3</span>
          </div>
          <div style={{ background: 'var(--pill-bg)', padding: '1rem', borderRadius: '12px' }}>
            <strong style={{ color: '#7B1FA2', display: 'block', marginBottom: '4px' }}>Vector & Keyword Search</strong>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>FAISS Dense + BM25 Sparse Index</span>
          </div>
          <div style={{ background: 'var(--pill-bg)', padding: '1rem', borderRadius: '12px' }}>
            <strong style={{ color: '#C2185B', display: 'block', marginBottom: '4px' }}>LLM Generation</strong>
            <span style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>Ollama Local Inference Engine</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default AboutProjectView;
