### Summary

The paper "Controlling Language and Diffusion Models by Transporting Activations" introduces Activation Transport (AT), a framework that leverages optimal transport theory to steer activations in generative models. The framework is modality-agnostic and provides fine-grained control over model behavior with negligible computational overhead. The paper demonstrates the effectiveness and versatility of AT through experiments on large language models (LLMs) and text-to-image diffusion models (T2Is), addressing tasks such as toxicity mitigation, concept induction, truthfulness induction, style control, and concept negation.

### Strengths

1. **Novel Framework**: The paper introduces a novel framework, Activation Transport (AT), that unifies and generalizes many previous activation-steering works under the umbrella of optimal transport theory. This provides a theoretical foundation and demonstrates how existing methods can be improved upon.

2. **Effectiveness and Versatility**: The framework is shown to be effective and versatile through extensive experiments on both LLMs and T2Is. The results demonstrate that AT can effectively mitigate toxicity, induce arbitrary concepts, increase truthfulness in LLMs, and enable fine-grained style control and concept negation in T2Is.

3. **Interpretable Control**: AT provides a strength parameter λ that allows for interpretable and fine-grained control over the model's behavior. This parameter is bounded between 0 (no transport) and 1 (full transport), making it user-friendly and robust across different models and tasks.

4. **Minimal Computational Overhead**: The framework is designed to have negligible computational overhead, making it practical for real-world applications.

5. **Comprehensive Comparison**: The paper provides a comprehensive comparison with several existing activation steering methods, highlighting the advantages of AT in terms of performance, robustness, and interpretability.

### Weaknesses

1. **Assumption of Independence**: The framework assumes independence across activation dimensions, which may not hold in practice. While the authors acknowledge this, a more detailed discussion of the potential impact of this assumption on the model's performance would be beneficial.

2. **Limited Sample Size**: The method is based on a limited number of samples (hundreds) to estimate the transport maps. A more thorough analysis of the impact of sample size on performance and generalization would be valuable.

3. **Clarity in Methodology**: The methodology section could benefit from more detailed explanations and additional examples or illustrations to make the concepts more accessible to a broader audience.

4. **Experimental Setup**: The experimental setup for T2Is is less detailed than for LLMs. More details about the specific layers intervened upon and the model architectures would improve the clarity of the experimental design.

5. **Comparison with Existing Methods**: While the paper compares AT with several existing methods, a more detailed analysis of the strengths and weaknesses of each method in different scenarios would help readers understand the advantages of AT more clearly.

### Questions

1. **Impact of Independence Assumption**: How does the assumption of independence across activation dimensions affect the performance of the framework in practice? Are there scenarios where this assumption might lead to suboptimal results?

2. **Sample Size Analysis**: How does the number of samples used to estimate the transport maps affect the performance and generalization of the framework? Could a larger sample size improve the results?

3. **Methodology Clarity**: Could the methodology section be expanded with more detailed explanations, examples, or illustrations to make the concepts more accessible to readers unfamiliar with optimal transport theory?

4. **Experimental Setup for T2Is**: Could the paper provide more details about the specific layers intervened upon and the model architectures used in the T2I experiments? This would help readers better understand the experimental design.

5. **Comparison with Existing Methods**: Could the paper provide a more detailed comparison with existing methods, highlighting the strengths and weaknesses of each method in different scenarios? This would help readers understand the advantages of AT more clearly.

RATING: 8