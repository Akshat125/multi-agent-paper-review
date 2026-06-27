## Summary

The paper introduces a novel supervised learning framework called \textit{{\oursfull} ({\ours})} that re-parameterizes a joint RLHF objective of both safety and helpfulness into a single supervised learning objective. The framework is designed to balance these two objectives using a labeling function that captures global preferences ranking. The paper also develops a comprehensive benchmark for evaluating both safety and helpfulness in LLMs, including both discriminative and generative tasks. The results indicate that the proposed method significantly outperforms existing approaches in both safety and helpfulness, while eliminating the need for human prompting and annotation, and using less than 10\% of the computational resources.

## Strengths

- **Novel Framework:** The paper introduces a novel and efficient supervised learning framework for balancing safety and helpfulness in LLMs, which is a significant departure from traditional multi-objective RLHF approaches.
- **Theoretical Equivalence:** The authors establish theoretical equivalence between their supervised optimization and the well-established multi-objective RLHF with a combination of the rewards of safety and helpfulness.
- **Empirical Results:** The empirical results show that \textit{{\ours}} achieves comparable or superior performance in both safety and helpfulness compared to state-of-the-art methods, despite using significantly fewer resources.
- **Comprehensive Benchmark:** The paper develops a comprehensive benchmark for evaluating both safety and helpfulness in LLMs, which is a valuable contribution to the field.
- **Efficiency:** The proposed method is highly efficient, requiring only 30K data points and one iteration of training, compared to other methods that require larger datasets and multiple iterations.

## Weaknesses

- **Limited Extensibility:** The current framework is limited to balancing two objectives (safety and helpfulness). Extending the framework to handle more than two objectives would require significant modifications and further research.
- **Assumption on Safety Labels:** The paper assumes that safety labels are either provided in the dataset or obtained via a safety classifier, but it does not address the potential biases or inaccuracies in these classifiers.
- **Lack of Human Evaluation:** The paper relies on automated metrics for evaluating harmlessness, but the absence of human evaluation limits the ability to assess the subjective quality of the model's outputs.
- **Limited Model Variability:** The experiments are conducted on a single base model (Mistral-7B-v0.1) and a single pre-aligned model (Zephyr-7b-beta). Testing the method on a broader set of models would strengthen the experimental validation.
- **No Analysis of Prompt Sensitivity:** The paper does not analyze how the method performs across different types of prompts (e.g., ambiguous, adversarial, or straightforward), which could provide deeper insights into the method's robustness.

## Questions

- How does the proposed labeling function handle cases where the safety and helpfulness objectives are in direct conflict, and one must be prioritized over the other?
- Can the framework be extended to handle more than two objectives, or is it limited to balancing safety and helpfulness?
- How does the performance of \textit{{\ours}} compare to other state-of-the-art methods in terms of robustness and generalization to unseen prompts or domains?

RATING: 8