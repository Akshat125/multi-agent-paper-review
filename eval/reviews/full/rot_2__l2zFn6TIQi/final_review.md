### Summary

The paper "Controlling Language and Diffusion Models by Transporting Activations" introduces a framework called Activation Transport (AT) that utilizes optimal transport theory to control the behavior of large generative models (GMs) by steering their activations. The AT framework is modality-agnostic, allowing it to be applied across different types of models, and it provides fine-grained control over model behavior with negligible computational overhead.

The authors demonstrate the effectiveness and versatility of AT through a series of experiments conducted on large language models (LLMs) and text-to-image diffusion models (T2Is). In the context of LLMs, the experiments show that AT can be used to mitigate toxicity, induce arbitrary concepts, and increase truthfulness. Specifically, the authors find that AT can reduce toxicity in LLMs by up to 7.5 times, induce arbitrary concepts with a high degree of accuracy, and increase truthfulness as measured by the TruthfulQA benchmark.

For T2Is, the authors demonstrate that AT enables fine-grained style control and concept negation. They show that AT can be used to control the level of style in generated images, such as the level of "sketchiness" or "cyberpunk" style, and that it can also be used to negate unwanted concepts in generated images, such as removing a pink elephant from an image.

The authors also compare AT to several baseline methods, including existing activation steering methods such as ACT, CAA, and ITI. The results show that AT outperforms or matches these baseline methods in various tasks, demonstrating its effectiveness and versatility.

Overall, the paper presents a novel framework for controlling the behavior of large generative models, and demonstrates its effectiveness and versatility through a series of experiments on LLMs and T2Is. The results show that AT can be used to mitigate toxicity, induce arbitrary concepts, increase truthfulness, enable fine-grained style control, and negate unwanted concepts, making it a valuable tool for a wide range of applications.

### Strengths

1. **Novel Framework**: The paper introduces a novel framework, Activation Transport (AT), based on optimal transport theory, which unifies and generalizes many previous activation-steering methods. The theoretical foundations are solid and provide a principled way to understand and compare different techniques.

2. **Versatility and Effectiveness**: The experimental results demonstrate the effectiveness and versatility of AT across different tasks and models. The framework's ability to provide fine-grained control with negligible computational overhead and an interpretable parameter for conditioning strength is particularly impactful.

3. **Comprehensive Evaluation**: The paper conducts a thorough evaluation of AT on both large language models (LLMs) and text-to-image diffusion models (T2Is). The use of well-established datasets and metrics, such as RealToxicityPrompts for toxicity mitigation and TruthfulQA for truthfulness induction, ensures the reliability of the results.

4. **Comparison to Baseline Methods**: The authors compare AT to several baseline methods, including ACT, CAA, and ITI. The results show that AT outperforms or matches these baseline methods in various tasks, demonstrating its effectiveness and versatility.

5. **Potential Applications**: The potential applications of AT are broad, given its modality-agnostic nature. The framework can be applied to various types of GMs, making it relevant for a wide range of tasks, from text generation to image synthesis.

### Weaknesses

1. **Reproducibility Concerns**: While the paper provides some information on the models and datasets used, reproducibility is not fully ensured. The authors do not provide exact versions or checkpoints of the models used, implementation details such as the exact pooling functions used, or the number of samples used for training the transport maps. Additionally, code availability is not explicitly mentioned, which is crucial for reproducibility.

2. **Statistical Significance**: The paper does not formally evaluate the statistical significance of the results. While the authors report results over 5 runs for some experiments, they do not mention whether the differences between methods are statistically significant. This is a major shortcoming, as the reported improvements could be due to variance in the model or data.

3. **Limited Ablation Studies**: The paper includes some ablation studies, but they are not as comprehensive as they could be. The authors mention an ablation on the pooling operator and the transport support, but the results are only in the appendix. A more detailed analysis of these ablations in the main text would help readers understand the impact of these choices.

4. **Comparison to AURA**: The comparison to AURA is limited to toxicity mitigation. AURA is designed for toxicity mitigation, and the authors do not attempt to use it for concept induction or truthfulness, which is a missed opportunity to show the generality of their framework.

5. **Adaptation of ITI for T2Is**: The adaptation of ITI for T2Is is not fully described in the main text. The paper mentions using spatial average pooling, but it is not clear whether the same training procedure was used as in the original ITI paper. A more detailed description of the adaptation would help readers understand the extent of the changes and whether the results are directly comparable.

### Questions

1. **Reproducibility**: To ensure full reproducibility, could the authors provide exact versions or checkpoints of the models used, implementation details such as the exact pooling functions used, and the number of samples used for training the transport maps? Additionally, could they make the code available for public use?

2. **Statistical Significance**: Could the authors provide a formal evaluation of the statistical significance of the results, such as using t-tests or bootstrapping, to ensure that the reported improvements are not due to random chance?

3. **Ablation Studies**: Could the authors include a more detailed analysis of the ablation studies in the main text, particularly the ablation on the pooling operator and the transport support, to help readers understand the impact of these choices?

4. **Comparison to AURA**: Could the authors extend the comparison to AURA to include concept induction and truthfulness tasks, to better demonstrate the generality of their framework?

5. **Adaptation of ITI for T2Is**: Could the authors provide a more detailed description of the adaptation of ITI for T2Is, including the training procedure and any changes made to the original method, to ensure that the results are directly comparable?

RATING: 7