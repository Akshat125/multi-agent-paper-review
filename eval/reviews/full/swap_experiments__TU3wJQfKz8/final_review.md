## Summary

The paper titled "Last-Iterate Convergence of Smooth Regret Matching$^+$ Variants in Learning Nash Equilibria" introduces a novel proof paradigm for analyzing the last-iterate convergence of Regret Matching$^+$ (RM$^+$) variants in learning Nash Equilibria (NE) in smooth games. The authors propose a new algorithm, Smooth Optimistic Gradient RM$^+$ (SOGRM$^+$), and provide experimental results to support their claims. The paper addresses the challenge of proving last-iterate convergence for RM$^+$ variants, which has been previously demonstrated only for games with strong monotonicity or two-player zero-sum matrix games.

## Strengths

1. **Novel Proof Paradigm**: The paper introduces a novel proof paradigm that leverages the equivalence between RM$^+$ and Online Mirror Descent (OMD) and uses the tangent residual to measure the distance to NE. This is a significant theoretical advancement that addresses a key challenge in the field.

2. **Practical Applicability**: The authors demonstrate the practical applicability of their proof paradigm by proving the last-iterate convergence of two existing smooth RM$^+$ variants, Smooth Extra-gradient RM$^+$ (SExRM$^+$) and Smooth Predictive RM$^+$ (SPRM$^+$). This shows that the paradigm can be used to analyze and improve existing algorithms.

3. **New Algorithm**: The introduction of SOGRM$^+$ is a significant contribution. It is the first RM$^+$ variant to achieve last-iterate convergence in games satisfying the weak Minty variation inequality (MVI), which is a weaker and more general condition than monotonicity. This makes SOGRM$^+$ applicable to a broader range of games.

4. **Experimental Validation**: The paper provides experimental results that show SOGRM$^+$ significantly outperforms other algorithms. The experiments are well-designed and provide strong validation of the theoretical contributions.

5. **Clear and Concise Presentation**: The paper is well-structured and clearly presents its motivations, goals, and key findings. The theoretical contributions are clearly explained, and the experimental results are presented in a manner that supports the theoretical claims.

## Weaknesses

1. **Complexity of Mathematical Derivations**: Some sections, particularly the preliminaries and proof paradigm, are quite dense and involve complex mathematical notation. This can make it harder for some readers to follow the arguments. Adding more textual context and simplifying some sentences could improve clarity.

2. **Limited Experimental Scope**: The experiments are conducted on randomly generated two-player zero-sum matrix games. While this is a good starting point, testing the algorithms on real-world or more complex game environments would better demonstrate the practical applicability of the proposed algorithm.

3. **Statistical Power**: The authors report the average duality gap over 20 randomly generated game instances. While 20 is a reasonable number for a preliminary study, it is not sufficient to draw strong statistical conclusions. A larger number of trials would improve the reliability and generalizability of the results.

4. **Missing Ablations**: The paper does not explore the impact of other hyperparameters, such as the regularizer strength or the number of iterations. Additionally, there is no ablation on the game size to see how the performance scales with increasing complexity. These would provide more comprehensive insights into the behavior of the algorithms.

5. **Comparison with Best-Iterate Convergence**: The paper mentions that SOGRM$^+$ achieves best-iterate convergence with a rate of $O(1/\sqrt{t})$, but it does not compare this rate with the best-iterate convergence of other algorithms. Including such a comparison would strengthen the empirical claims.

## Questions

1. **Real-World Applicability**: How does the proposed algorithm, SOGRM$^+$, perform on real-world game environments, such as Poker or multi-player games? Including experiments on such environments would provide stronger evidence of the algorithm's practical applicability.

2. **Impact of Hyperparameters**: What is the impact of other hyperparameters, such as the regularizer strength or the number of iterations, on the performance of the proposed algorithms? Conducting ablations on these hyperparameters would provide more comprehensive insights into the behavior of the algorithms.

3. **Scalability**: How does the performance of the proposed algorithms scale with increasing game size or complexity? Including experiments on larger or more complex games would demonstrate the scalability of the algorithms.

4. **Comparison with Other Algorithms**: How does the best-iterate convergence rate of SOGRM$^+$ compare with that of other algorithms, such as OGDA, EG, or OG? Including a comparison of best-iterate convergence rates would provide a more complete picture of the algorithm's performance.

5. **Accumulated Regret Behavior**: The theoretical analysis is based on the accumulated regrets and their convergence. However, the actual behavior of the accumulated regrets is not visualized or analyzed in the experiments. Including plots of the accumulated regrets over time would provide more insight into the dynamics of the algorithms and support the theoretical claims more directly.

RATING: 8