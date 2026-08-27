import { motion } from 'motion/react';

const LoadingSpinner = () => {
  return (
    <motion.div
      className="loading-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        animate={{ rotate: [0, 10, -10, 10, 0], y: [0, -10, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        style={{ fontSize: '4rem', position: 'relative', marginBottom: '1.5rem' }}
      >
        🍲
        <motion.span
          animate={{ opacity: [0, 1, 0], y: [0, -20] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
          style={{ position: 'absolute', top: '-10px', right: '-5px', fontSize: '1.2rem' }}
        >✨</motion.span>
        <motion.span
          animate={{ opacity: [0, 1, 0], y: [0, -20] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: 0.8 }}
          style={{ position: 'absolute', top: '0', left: '-5px', fontSize: '1.2rem' }}
        >✨</motion.span>
      </motion.div>

      <motion.p
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity }}
        style={{ fontWeight: 600, fontSize: '1.1rem' }}
      >
        Generating delicious recipe...
      </motion.p>
    </motion.div>
  );
};

export default LoadingSpinner;
