## Summary

The paper "Input Compensation for Pruned Models" introduces a novel approach called input compensation (IC) to enhance the performance of pruned models. Unlike traditional methods that focus on adjusting the weights, IC adjusts the input to compensate for the removed weights. The paper demonstrates the effectiveness of IC through extensive experiments on various tasks, including image classification, language modeling, and image generation. The results show that IC consistently improves the performance of existing pruning methods, making it a complementary and versatile tool for model compression.

## Strengths

- **Novel Approach**: The paper introduces a new direction in model pruning by focusing on input compensation rather than weight adjustment. This is a significant departure from traditional methods and offers a fresh perspective on enhancing pruned models.

- **Complementarity**: IC is designed to be complementary to existing pruning methods, making it easily integrable with them. This versatility is a strong point, as it allows for the combination of IC with various pruning techniques to achieve better performance.

- **Extensive Experiments**: The paper includes comprehensive experiments across multiple tasks and datasets, demonstrating the effectiveness of IC in different scenarios. The results are well-presented and support the claims made by the authors.

- **Significant Improvements**: The experimental results show substantial improvements in performance when IC is applied. For example, IC achieves a 28% improvement over Magnitude Pruning in image classification tasks and reduces perplexity significantly in language modeling tasks.

- **Clear Contributions**: The contributions of the paper are clearly stated and well-supported by the experimental results. The authors effectively summarize their contributions, making it easy for readers to understand the impact of their work.

## Weaknesses

- **Limited Comparison with Input Adaptation Methods**: While the paper compares IC with a globally shared compensation (VP), it does not extensively compare it with other input adaptation techniques such as prompt tuning or prefix learning. A more comprehensive comparison would strengthen the argument for the novelty and effectiveness of IC.

- **Lack of Statistical Significance**: The results are presented as point estimates without statistical significance testing. Including standard deviations or confidence intervals would make the results more robust and provide a clearer picture of the improvements.

- **Insufficient Detail on Implementation**: Some implementation details, such as the choice of encoder and initialization strategies for K and V, are not thoroughly discussed. More detailed explanations and justifications for these choices would improve the reproducibility of the results.

- **Parameter Overhead**: Although the paper mentions that the additional parameters introduced by IC are small, it does not quantify the overhead in all experiments. Providing a detailed analysis of the parameter overhead and its impact on model compression would be beneficial.

- **Theoretical Justification for Non-linear Models**: The paper provides a mathematical derivation for the linear layer case but does not offer a theoretical justification for the generalization to non-linear models. A more formal analysis of how input compensation interacts with non-linearities would strengthen the methodology.

## Questions

- **Statistical Significance**: Were statistical significance tests conducted to validate the improvements observed with IC? If so, could the results of these tests be included in the paper?

- **Comparison with Other Input Adaptation Methods**: Have the authors considered comparing IC with other input adaptation techniques, such as prompt tuning or prefix learning? How does IC perform in comparison to these methods?

- **Implementation Details**: Could the authors provide more detailed information on the choice of encoder and the initialization strategies for K and V? This would help in understanding the implementation better and improving reproducibility.

- **Parameter Overhead**: Could the authors quantify the parameter overhead introduced by IC in all experiments and compare it to the compression gains from pruning? This would provide a clearer picture of the practical impact of IC.

- **Theoretical Justification**: Is there a theoretical justification for the generalization of IC to non-linear models? How does input compensation interact with non-linearities in these models?

RATING: 8