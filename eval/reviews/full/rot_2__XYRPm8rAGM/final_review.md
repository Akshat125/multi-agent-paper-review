### Summary

The paper "Agree to Disagree: Demystifying Homogeneous Deep Ensembles through Distributional Equivalence" challenges the conventional wisdom that the effectiveness of deep ensembles is due to Jensen's inequality. Instead, the authors propose that the key to understanding deep ensembles lies in the distributional equivalence property, where the predictions of homogeneous models form identical distributions despite point-wise differences. The paper provides a rigorous theoretical analysis and comprehensive empirical results to support this claim, demonstrating that deep ensembles outperform individual models and that their performance can be estimated using only two models.

### Strengths

- **Novel Theoretical Insight**: The paper introduces the concept of distributional equivalence, which provides a new and theoretically grounded explanation for the effectiveness of deep ensembles. This is a significant advancement over the traditional Jensen gap explanation.

- **Rigorous Theoretical Analysis**: The authors provide rigorous proofs and theoretical derivations to support their claims. For example, they prove that deep ensembles are guaranteed to outperform any single member under the condition of neural collapse and derive closed-form expressions to quantify the improvement in performance.

- **Comprehensive Empirical Validation**: The paper includes extensive empirical results to validate the theoretical findings. The experiments involve a large number of ensemble members (M=100) across various datasets and model structures, adding robustness to the conclusions.

- **Practical Estimation Schemes**: The authors propose schemes to estimate the performance of deep ensembles using only two models. This is a practical contribution that can help practitioners make informed decisions about the trade-off between training budget and performance requirements.

- **Bias-Variance Trade-Off Analysis**: The paper provides a theoretical explanation for the bias-variance trade-off observed in deep ensembles as the capacity of individual models increases. This contributes to a deeper understanding of the behavior of deep ensembles and their relationship with single large models.

### Weaknesses

- **Assumption of Neural Collapse**: The theoretical analysis relies on the assumption of complete neural collapse, which may not always hold in practice. While the authors acknowledge this and demonstrate the transferability between the theoretical and empirical results, it is important to consider the limitations of this assumption.

- **Empirical Validation**: Although the empirical results are comprehensive, they are limited to specific datasets and model structures. It would be beneficial to validate the findings on a broader range of datasets and models to ensure their generalizability.

- **Complexity of Theoretical Derivations**: The theoretical derivations are complex and may be difficult for some readers to follow. Clearer explanations and additional examples could help make the paper more accessible to a wider audience.

- **Practical Applicability**: While the paper provides valuable insights, it is important to consider the practical applicability of the findings. For example, the estimation schemes for ensemble performance may not be straightforward to implement in all scenarios, and their effectiveness may vary depending on the specific application.

### Questions

- **Generalizability of Findings**: How do the findings generalize to other datasets and model structures not included in the empirical validation? Are there specific scenarios where the distributional equivalence property may not hold?

- **Impact of Neural Collapse Assumption**: How sensitive are the theoretical results to the assumption of complete neural collapse? Are there alternative assumptions or conditions under which the distributional equivalence property can be observed?

- **Practical Implementation**: What are the practical steps and considerations for implementing the proposed estimation schemes in real-world applications? Are there any potential challenges or limitations in applying these schemes to different problem domains?

- **Comparison with Other Ensembling Methods**: How does the distributional equivalence property compare with other ensembling methods, such as Bayesian neural networks or dropout ensembles? Are there any advantages or disadvantages of using deep ensembles over these alternative methods?

- **Robustness to Different Training Dynamics**: How does the distributional equivalence property behave under different training dynamics, such as varying learning rates, optimizers, or regularization techniques? Are there any specific training conditions that enhance or diminish the effectiveness of deep ensembles?

- **Impact of Model Calibration**: How does the distributional equivalence property affect the calibration of the ensemble predictions? Are there any specific calibration techniques that can be used to improve the reliability of the ensemble predictions?

- **Theoretical Justification for Distributional Equivalence**: What are the theoretical reasons behind the distributional equivalence property? Are there any underlying mechanisms or principles that explain why homogeneous models exhibit this property?

RATING: 8