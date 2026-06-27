### Summary

The paper "HERTA: A High-Efficiency and Rigorous Training Algorithm for Unfolded Graph Neural Networks" introduces a novel training algorithm for Unfolded Graph Neural Networks (GNNs) that addresses both the slow iterations and slow convergence issues in their training. The proposed algorithm, HERTA, accelerates the training process and provides a worst-case convergence guarantee while preserving the interpretability of the original model. Additionally, the paper introduces a new spectral sparsification method for normalized and regularized graph Laplacians, which is a key component of HERTA. The paper includes a detailed theoretical analysis and experimental validation on real-world datasets, demonstrating the superiority and adaptability of HERTA.

### Strengths

1. **Novelty and Advancement Over Existing Methods:**
   - HERTA addresses both the slow iterations and slow convergence issues in training Unfolded GNNs, which previous methods have not adequately tackled simultaneously.
   - Unlike existing methods that often distort the underlying optimization objective or require changing the GNN model, HERTA preserves the original model and its interpretability.
   - The introduction of a new spectral sparsification method for normalized and regularized graph Laplacians is a notable advancement, providing tighter bounds than existing spectral sparsifiers.

2. **Main Contributions:**
   - **HERTA Algorithm:** A high-efficiency and rigorous training algorithm for Unfolded GNNs that accelerates the training process and provides a worst-case convergence guarantee.
   - **Spectral Sparsification Method:** A new method for approximating the squared inverse of a normalized and regularized Laplacian matrix, which is a key component of HERTA.
   - **Theoretical Analysis:** A detailed theoretical analysis of the algorithm's convergence and time complexity, including an informal statement of the main result (Theorem 1).
   - **Experimental Validation:** Empirical verification of HERTA's superiority and adaptability on real-world datasets with various loss functions and optimizers.

3. **Comparison to Existing Methods:**
   - **Efficiency:** HERTA achieves a nearly-linear time worst-case training guarantee, which is a significant improvement over existing methods that focus only on per-iteration efficiency.
   - **Convergence Guarantees:** HERTA provides a theoretical guarantee on the training convergence rate, which is not addressed by existing methods. It converges to the optimum of the original model, preserving the interpretability of Unfolded GNNs.
   - **Adaptability:** HERTA is shown to work effectively with various loss functions and optimizers, demonstrating its universality and practical applicability.

4. **Potential Applications and Impacts:**
   - **GNN Training:** HERTA can significantly accelerate the training of Unfolded GNNs, making them more scalable and practical for large and dense graphs.
   - **Interpretability:** By preserving the original model and its interpretability, HERTA can help in better understanding and analyzing GNNs.
   - **Other Areas:** The spectral sparsification method introduced in HERTA could have applications in other areas that involve solving linear systems or approximating matrices, such as numerical linear algebra and machine learning.
   - **Future Directions:** The paper suggests potential future directions, such as extending HERTA to more complex models and providing a more detailed analysis of other loss functions, which could further broaden its impact.

### Weaknesses

1. **Clarity and Writing Quality:**
   - The paper is generally well-written, but some sections are dense with technical details, which may make it challenging for non-experts to follow. For example, the section on "Key Techniques" is packed with mathematical notation and concepts from linear algebra and graph theory.
   - The figures and tables are generally clear and informative, but some could be improved. For instance, Figure 1 is a bit cluttered and may be difficult to read. Additionally, some tables could be more detailed, such as Table 1, which provides a summary of the datasets used in the experiments.

2. **Experimental Design and Reproducibility:**
   - The experiments are well-designed and reproducible, but they could benefit from more datasets and more details about the experimental setup and hyperparameter tuning process.
   - The paper only reports training loss convergence, which is useful for understanding the training dynamics, but does not assess the final model performance (e.g., accuracy on the test set). This is a critical gap, as the ultimate goal of training is to achieve good generalization, not just fast convergence.
   - The paper does not provide enough detail on how the SDD solvers and spectral sparsifiers are implemented in practice, which makes it difficult to reproduce the results or understand the computational overhead of HERTA.

3. **Methodology and Theoretical Analysis:**
   - The assumption that the number of large eigenvalues of the Laplacian is \(O(n/\lambda^2)\) is not clearly explained in the main text. While the paper mentions that this is a simplification for the time complexity and that it is not strictly necessary, it is not made explicit whether this is a common assumption in the field or if it is specific to the datasets used. A more detailed discussion of the practical relevance of this assumption would strengthen the justification of the methodology.
   - The paper does not investigate the impact of the preconditioner construction, the spectral sparsification, or the choice of \(\lambda\) on the final performance. An ablation study would help to understand which parts of the algorithm are most critical for the observed speedup.

4. **Comparison with Existing Methods:**
   - The paper mentions that many methods address the per-iteration cost (Issue 1), but it does not compare HERTA with these methods (e.g., stochastic training, clustering-based methods, or decoupling approaches). This is a major omission, as the paper's claim of "superiority" is not supported by a direct comparison with the state-of-the-art in this domain.

### Questions

1. **Clarification on the Assumption of Large Eigenvalues:**
   - The paper assumes that the number of large eigenvalues of the Laplacian is \(O(n/\lambda^2)\). Could the authors provide more context or examples where this assumption holds? How does this assumption affect the practical applicability of HERTA?

2. **Ablation Studies:**
   - The paper does not include ablation studies on the key components of HERTA, such as the preconditioner construction and the spectral sparsification. Could the authors provide results from such studies to better understand the contributions of these components to the overall performance?

3. **Final Model Performance:**
   - The paper focuses on training loss convergence but does not report the final model performance (e.g., test accuracy). Could the authors include these metrics to provide a more comprehensive evaluation of HERTA's effectiveness?

4. **Comparison with Existing Efficient Training Methods:**
   - The paper does not compare HERTA with existing methods that aim to reduce training cost, such as ClusterGCN, GraphSAGE, or MUSE. Could the authors include such comparisons to better demonstrate the superiority of HERTA?

5. **Implementation Details:**
   - The paper does not provide enough detail on how the SDD solvers and spectral sparsifiers are implemented in practice. Could the authors include a supplemental section or appendix with implementation details, such as the specific SDD solver used, the value of the constant \(C\) in the sparsification algorithm, and the practical runtime of each component?

6. **Evaluation on Larger or More Challenging Graphs:**
   - The datasets used in the experiments are relatively small and well-conditioned. Could the authors test HERTA on larger graphs (e.g., ogbn-products, ogbn-papers100M) and graphs with more ill-conditioned Laplacians to evaluate the scalability and robustness of the algorithm?

7. **Evaluation of the Universality of HERTA:**
   - The paper claims that HERTA is universally applicable to various loss functions and optimizers. Could the authors provide more empirical validation of this claim by testing HERTA with other loss functions (e.g., hinge loss, focal loss) and optimizers (e.g., SGD with momentum, RMSProp)?

8. **Trade-off Between Speed and Accuracy:**
   - The paper does not analyze the trade-off between the speedup provided by HERTA and the final model accuracy. Could the authors include a trade-off analysis to better understand the practical implications of using HERTA?

RATING: 7