## Summary
The paper introduces HERTA, a High-Efficiency and Rigorous Training Algorithm for Unfolded Graph Neural Networks (GNNs). It addresses the scalability issues of training unfolded GNNs by proposing a new spectral sparsification method and a preconditioning approach. The paper provides theoretical guarantees for the convergence and time complexity of HERTA, showing that it achieves a nearly-linear time worst-case training guarantee. Experimental results on real-world datasets demonstrate the effectiveness of HERTA in accelerating training for various loss functions and optimizers, preserving the interpretability of the original model.

## Strengths
- The paper clearly identifies and addresses two major scalability issues in training unfolded GNNs: slow iterations and slow convergence. This is a significant contribution to the field.
- HERTA is designed to converge to the optimum of the original model, preserving the interpretability of unfolded GNNs, which is a key advantage over existing methods that often modify the model or its objective.
- The theoretical analysis is rigorous and well-structured, providing convergence guarantees and time complexity bounds. The paper also introduces a new spectral sparsification method for normalized and regularized graph Laplacians, which is shown to provide tighter bounds than existing methods.
- The experimental results are well-designed and conducted on real-world datasets, demonstrating the effectiveness of HERTA across different loss functions (MSE and CE) and optimizers. The results are consistent and show significant improvements in training convergence rates.
- The paper is well-positioned in the literature, clearly outlining the limitations of existing methods and how HERTA addresses them. The experimental results reinforce the paper's contribution by showing the superiority of HERTA over standard optimizers.

## Weaknesses
- The paper could benefit from a more detailed explanation of the background and motivation behind Unfolded GNNs. While the problem is well-stated, a deeper dive into why these models are preferred over traditional GNNs and the specific challenges they face would enhance clarity.
- The paper lacks a thorough explanation of the intuition behind the spectral sparsification method and the preconditioning approach. While the mathematical details are provided, a high-level overview or analogy would help readers grasp the core ideas more easily.
- The experimental setup could be more detailed. The paper mentions the datasets and hyperparameters but does not provide a clear description of the preprocessing steps, training/validation/test splits, or hardware specifications used for the experiments.
- The paper could improve by providing a theoretically rigorous bound for the cross-entropy (CE) loss and other loss functions. While the paper explains why HERTA works well with CE loss, a formal guarantee would strengthen the contribution.
- The paper could benefit from a more structured presentation of the experimental results, including a clear description of the experimental setup and hyperparameters. This would make the results more interpretable and the paper more reproducible.

## Questions
- What specific preprocessing steps were applied to the datasets (Cora, Citeseer, Pubmed, ogbn-arxiv) before training? How were the features and labels normalized?
- Could the authors provide a more detailed explanation of the intuition behind the spectral sparsification method and the preconditioning approach? How do these techniques specifically address the scalability issues of unfolded GNNs?
- What is the exact implementation of the SDD solver and fast matrix multiplication techniques used in HERTA? Could the authors provide references to the specific libraries or tools used?
- How were the hyperparameters (e.g., $\lambda$, $\eta$, $T$) chosen for the experiments? Could the authors provide a table or section detailing the hyperparameter search space and the final chosen values?
- What is the theoretical bound for the cross-entropy (CE) loss and other loss functions? How does the analysis of the CE loss compare to the MSE loss in terms of convergence guarantees?

RATING: 8