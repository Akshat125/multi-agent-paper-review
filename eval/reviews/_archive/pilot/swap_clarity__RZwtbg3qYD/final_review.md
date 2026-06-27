## Summary
The paper introduces HOPE, a novel parameterization scheme for linear time-invariant (LTI) systems in state-space models (SSMs), based on the Markov parameters of a discrete Hankel operator. The authors provide a theoretical analysis showing that HOPE-SSM is more robust to initialization and training perturbations compared to existing methods like S4 and S4D. Empirically, HOPE-SSM is evaluated on the sCIFAR-10 task and the Long-Range Arena (LRA) benchmark, where it demonstrates improved performance and non-decaying memory within a fixed time window. The paper claims that HOPE-SSM requires fewer parameters and is more stable during training, making it a promising approach for long-range sequence modeling.

## Strengths
The paper has several notable strengths that contribute to its overall quality and impact on the field of SSMs:

1. **Theoretical Foundation**: The authors provide a rigorous theoretical analysis of the numerical rank and stability of HOPE-SSM. The use of Hankel singular value decomposition (HSVD) to understand the expressiveness of LTI systems is a fresh and insightful approach. The theorems (Theorems 1, 3, and 4) are mathematically sound and offer a clear justification for the proposed parameterization.

2. **Empirical Validation**: The paper includes empirical results on the sCIFAR-10 task and the LRA benchmark, which are relevant for evaluating long-range memory and robustness in SSMs. The results show that HOPE-SSM outperforms S4 and S4D on most LRA tasks, and it performs well on the sCIFAR-10 task even when the LTI systems are trained with a standard learning rate. This suggests that the proposed method is not only theoretically sound but also practically effective.

3. **Parameter Efficiency**: The authors claim that HOPE-SSM requires only $1/3$ the number of parameters compared to S4D for each LTI system. This is a meaningful reduction, especially in the context of deep learning where parameter efficiency is a key concern. The parameterization is also computationally efficient, with the same time and space complexity as S4D.

4. **Non-Decaying Memory**: The paper introduces a new concept of non-decaying memory in SSMs, which is a direct response to the known issue of exponentially decaying memory in traditional models. The empirical results on the noise-padded sCIFAR-10 task support this claim, showing that HOPE-SSM retains memory better than S4D.

5. **Implementation Insight**: The nonuniform sampling of the transfer function is a clever engineering trick that allows the model to maintain the same computational complexity as S4D while using a different parameterization. This is a practical contribution that could be useful in other SSM-related work.

6. **Clear Explanation of Methodology**: The methodology is well-structured and clearly explained, with a step-by-step guide on how to implement the HOPE scheme. The use of equations and pseudocode (Algorithm 1) helps to clarify the theoretical underpinnings and the practical implementation of the method.

7. **Reproducibility**: The paper provides sufficient details about the experimental setup and the implementation of the HOPE scheme. The authors also report median and standard deviation across 5 random seeds, which is a good practice for assessing the robustness of the results.

## Weaknesses
Despite its strengths, the paper has several weaknesses and areas for improvement:

1. **Limited Ablation Studies**: The ablation studies in the paper are somewhat limited. For example, the impact of the sampling period $\Delta t$ is not thoroughly analyzed, and the paper does not perform an ablation on the number of Markov parameters $n$. A more comprehensive ablation would help to better understand the contributions of the proposed method.

2. **Comparison to Attention-Based Models**: The paper does not compare HOPE-SSM with attention-based models (e.g., transformers) on the sCIFAR-10 task. This would help to contextualize the performance gains in a broader sense and determine whether the non-decaying memory is the sole reason for the performance improvement.

3. **Parameter Reduction Not Fully Leveraged**: The paper claims that HOPE-SSM requires only $1/3$ the number of parameters for each LTI system compared to S4D. However, it is also noted that the overall model does not reduce the total number of parameters by a factor of $1/3$ because other components (e.g., encoder and decoder) are not compressed. The paper should clarify whether the parameter reduction is a per-LTI system benefit or a model-wide benefit, and whether it leads to computational or memory savings during training or inference.

4. **Long-Memory Claim Not Fully Substantiated**: The authors claim that HOPE-SSM has non-decaying memory, as shown in Figure 4 (right). However, the figure only shows the memory decay for a single system. A more comprehensive analysis of the memory behavior across all LTI systems in the model, or at least a statistical summary (e.g., mean or median decay over all systems), would strengthen this claim.

5. **Missing Formal Derivation of Bilinear Transform**: The paper does not provide a formal derivation of the bilinear transform used to convert the continuous-time system to the discrete-time system. While it is referenced, a more detailed explanation would strengthen the methodology.

6. **Comparison to Recent SSM Variants**: The paper does not compare HOPE-SSM with the most recent SSM variants (e.g., Mamba or S5) on all LRA tasks. For example, Mamba is not included in the LRA results, which is a major SSM competitor. A comparison with these models would provide a more complete picture of the method's performance.

7. **Initialization Details Missing**: The paper does not explicitly define the distribution from which the Markov parameters $\mathbf{h}$ are initialized. This is important for reproducibility and for understanding the theoretical guarantees in Theorem 3.

8. **Training Time and Computational Cost Not Reported**: The paper does not report the training time or computational cost of HOPE-SSM compared to S4D. Since HOPE-SSM uses fewer parameters, it is important to confirm whether this leads to faster training or better scalability.

9. **Lack of Sensitivity Analysis**: The paper does not include a sensitivity analysis of the LTI system parameters to further validate the numerical stability of HOPE-SSM. This would help to better understand the robustness of the method.

10. **Theoretical vs. Practical Novelty**: While the theoretical shift to using the Hankel operator and Markov parameters is novel, the contribution is not entirely new in the context of kernel-based SSMs. The S4D model already uses a kernel-based approach to parameterize the LTI system, and the S5 model generalizes this to multiple channels. The key difference in HOPE is the use of the Hankel operator, but the paper should more clearly articulate how this theoretical shift leads to practical improvements in training and performance.

## Questions
1. **What is the exact relationship between the Markov parameters and the system matrices in the HOPE-SSM?** The paper defines the Hankel matrix in terms of the Markov parameters but does not explicitly state how the Markov parameters are derived from the system. Is this a direct parameterization, or is there an implicit reconstruction of the system from the Hankel matrix?

2. **How does HOPE differ from the kernel-based parameterization in S4D and S5?** The authors mention that S4D uses a reparameterization of the system matrices to learn the kernel, while HOPE uses the Markov parameters directly. However, the paper should more clearly contrast the two approaches in terms of how the kernel is learned and how the parameterization affects the model's behavior.

3. **Is the bilinear transform used in HOPE a novel contribution?** The bilinear transform is a standard method for converting continuous-time systems to discrete-time ones. The paper uses it to connect the continuous and discrete systems, but it is not clear whether this is a novel application or a standard technique in the SSM literature.

4. **Does the parameter reduction in HOPE-SSM lead to computational or memory savings during training or inference?** The paper claims that HOPE-SSM requires only $1/3$ the number of parameters for each LTI system compared to S4D. However, it is also noted that the overall model does not reduce the total number of parameters by a factor of $1/3$ because other components (e.g., encoder and decoder) are not compressed. The paper should clarify whether the parameter reduction is a per-LTI system benefit or a model-wide benefit, and whether it leads to computational or memory savings.

5. **Can the long-memory claim be substantiated with a more comprehensive analysis?** The authors claim that HOPE-SSM has non-decaying memory, as shown in Figure 4 (right). However, the figure only shows the memory decay for a single system. The paper should provide a more comprehensive analysis of the memory behavior across all LTI systems in the model, or at least a statistical summary (e.g., mean or median decay over all systems).

6. **Is the comparison to S4 and S4D fair?** The paper states that HOPE-SSM uses the same model architecture as S4D but replaces the LTI blocks with HOPE blocks. However, it is not clear whether the other components of the model (e.g., encoder and decoder) are kept identical. If the other components are modified or optimized differently, the performance gains may not be solely attributable to the HOPE parameterization.

7. **What is the impact of the sampling period $\Delta t$ on the performance of HOPE-SSM?** The paper mentions that $\Delta t = 0.1$ is used in the noise-padded sCIFAR-10 task, but the impact of this parameter on the LRA results is not discussed. A grid search over $\Delta t$ would help determine the optimal setting and confirm the robustness of the method.

8. **How sensitive is HOPE-SSM to different learning rates and initializations?** The paper should provide more detailed ablation studies to show how sensitive the model is to different learning rates and initializations, and how it compares to S4D in terms of training dynamics.

9. **Can the authors provide a comparison of HOPE-SSM with a version of the model that uses the same number of parameters but a different parameterization?** This would help to isolate the effect of the parameterization from other architectural choices.

10. **Can the authors provide a comparison of HOPE-SSM with a version of the model that uses the same nonuniform sampling but a different initialization (e.g., HiPPO-LegS)?** This would help to determine whether the performance gain is due to the parameterization or the initialization.

RATING: 8