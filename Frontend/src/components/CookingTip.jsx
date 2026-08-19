import { motion } from 'motion/react';

const CookingTip = () => {
  return (
    <motion.div
      className="cooking-tip"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", bounce: 0.4 }}
      whileHover={{ scale: 1.02 }}
    >
      <h3>💡 Cooking Tip</h3>
      <p>Always taste your food as you cook! Adjusting seasoning layer by layer brings out the best flavors. 🧑‍🍳</p>
    </motion.div>
  );
};

export default CookingTip;
