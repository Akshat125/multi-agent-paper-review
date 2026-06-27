## Summary

This paper, "Agree to Disagree: Demystifying Homogeneous Deep Ensembles through Distributional Equivalence," challenges the conventional understanding of deep ensembles in machine learning. The authors argue that the effectiveness of deep ensembles is not due to Jensen's inequality, as previously thought, but rather stems from a property they term "distributional equivalence." This property posits that while individual models in an ensemble may make different predictions for specific data points, their predictions collectively form an identical distribution. The paper provides both theoretical analysis and comprehensive empirical results to support this claim, using a variety of datasets and model architectures. The authors also introduce a method to estimate the performance of deep ensembles using only two models, which has significant practical implications.

## Strengths

1. **Novel Concept**: The introduction of the distributional equivalence property is a significant contribution to the field. This concept provides a new perspective on why deep ensembles work, challenging the traditional view based on Jensen's inequality.

2. **Theoretical Rigor**: The paper offers a rigorous theoretical analysis of deep ensembles. The authors derive several theorems that explain the effectiveness of deep ensembles and provide a mathematical foundation for their claims.

3. **Comprehensive Empirical Validation**: The empirical studies are extensive and well-conducted. The authors use a large number of ensemble members (M=100) across various datasets (CIFAR-10, CIFAR-100, TinyImageNet) and model architectures (CNNs, ResNets), providing strong evidence for the distributional equivalence property.

4. **Practical Implications**: The paper's findings have significant practical implications. The proposed method to estimate the performance of deep ensembles using only two models is innovative and could be useful for practitioners who want to use deep ensembles in their work.

5. **Clear Writing and Organization**: The paper is generally well-written and clear. The introduction provides a good overview of the problem and the motivation behind the study. The methods section is detailed and well-structured, and the results are presented in a logical order.

## Weaknesses

1. **Lack of Direct Comparisons**: The paper does not provide a direct comparison with existing explanations of deep ensembles, such as Jensen's inequality or point-wise diversity. This makes it difficult to assess the relative explanatory power of the distributional equivalence hypothesis.

2. **Assumption of Complete Neural Collapse**: The theoretical analysis is based on the assumption of complete neural collapse, where models predict either 0 or 1. While this is a reasonable approximation for overfit models, it is not clear how well this assumption holds in practice. A more thorough analysis of the degree of neural collapse in the trained models would strengthen the methodology.

3. **Limited Exploration of Model Types**: The experiments are conducted using CNNs and ResNets, but the authors do not test whether the distributional equivalence property holds for other model types, such as transformers or fully connected networks. This limits the generalizability of the findings.

4. **No Analysis of Early Training Stages**: The paper focuses on the neural collapse regime, where models are overfit and predictions are close to 0 or 1. However, the authors do not investigate whether the distributional equivalence property holds in the early stages of training, where models are not yet overfit. This could provide insight into when the property emerges and whether it is a consequence of overfitting or a more general phenomenon.

5. **No Analysis of Distributional Shifts**: The paper does not test whether the distributional equivalence property is robust to distributional shifts or label noise, which are common in real-world applications. This is a critical limitation, as the property may not hold in such settings.

6. **No Comparison with Bayesian Neural Networks**: The paper focuses on homogeneous ensembles but does not compare the performance or behavior of these ensembles with Bayesian neural networks (BNNs) or Monte Carlo dropout. These are standard baselines in the context of uncertainty quantification and model averaging, and their absence weakens the empirical validation of the proposed mechanism.

7. **No Ablation on Estimation Scheme**: The authors propose that the asymptotic performance of deep ensembles can be estimated using only two models. However, they do not perform an ablation study to test how the estimation accuracy changes with the number of models used (e.g., 2 vs. 5 vs. 10). This is a critical missing piece for validating the practical utility of the estimation scheme.

8. **No Analysis of Training Hyperparameters**: The paper mentions that the training parameters follow the suggestions in Nakkiran et al. (2021), but it does not explore how different training settings (e.g., learning rate, batch size, optimizer) affect the distributional equivalence property. This is a missed opportunity to understand the robustness of the property to training variations.

## Questions

1. **How does the distributional equivalence property compare with existing explanations of deep ensembles, such as Jensen's inequality or point-wise diversity? Are there any controlled experiments that directly compare these explanations?**

2. **How well does the assumption of complete neural collapse hold in practice? Is there any empirical evidence that supports this assumption for the models used in the experiments?**

3. **Does the distributional equivalence property hold for other model types, such as transformers or fully connected networks? Are there any plans to test this property on a broader set of model architectures?**

4. **Does the distributional equivalence property hold in the early stages of training, where models are not yet overfit? How does the property emerge as training progresses?**

5. **Is the distributional equivalence property robust to distributional shifts or label noise? Are there any experiments that test the property under these conditions?**

6. **How does the performance of homogeneous ensembles compare with Bayesian neural networks (BNNs) or Monte Carlo dropout in terms of uncertainty quantification and model averaging?**

7. **How accurate is the proposed estimation scheme using only two models? Are there any ablation studies that test the accuracy of the estimation with different numbers of models?**

8. **How do different training settings (e.g., learning rate, batch size, optimizer) affect the distributional equivalence property? Are there any experiments that explore the robustness of the property to training variations?**

RATING: 7