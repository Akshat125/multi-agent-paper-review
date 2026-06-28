## Summary

The paper "In-Context Reinforcement Learning From Suboptimal Historical Data" introduces the Decision Importance Transformer (DIT), a novel framework for training an autoregressive transformer for in-context Reinforcement Learning (RL) using suboptimal historical data. The paper addresses the challenge of training LTMs to imitate actions in pretraining datasets, which often require optimal policies or complete learning histories. DIT overcomes these limitations by using an exponential reweighting technique and an LTM-based advantage estimator to improve policy performance. The paper includes extensive experiments on both bandit and Markov Decision Process (MDP) problems, demonstrating that DIT achieves superior performance, particularly when the offline dataset contains suboptimal historical data.

## Strengths

1. **Innovative Methodology**: The paper introduces a novel approach to in-context RL using suboptimal historical data. The use of an exponential reweighting technique and an LTM-based advantage estimator is a significant departure from existing methods that rely on optimal data.

2. **Comprehensive Experimental Validation**: The paper provides extensive experimental results on both bandit and MDP problems. The experiments are well-designed and cover a range of scenarios, including online and offline evaluations, as well as ablation studies.

3. **Practical Relevance**: The ability to learn from suboptimal data has practical implications for real-world applications where obtaining optimal data is challenging. The paper's results demonstrate the potential of DIT to be applied in industries such as robotics, healthcare, and finance.

4. **Clear and Detailed Explanation**: The paper is generally well-written and provides a clear explanation of the proposed methodology. The notation section is particularly well-written and provides clear definitions of the terms used in the paper.

## Weaknesses

1. **Clarity and Readability**: Some sections of the paper, particularly the introduction, related work, and discussion, contain long and complex sentences that can be difficult to follow. Breaking down these sentences into simpler ones would improve readability.

2. **Reproducibility**: While the methods section provides a good overview of the proposed approach, some details are missing or could be expanded to ensure reproducibility. For example, the description of the advantage weighted regression technique could be more detailed, and a table or list of hyperparameters and their values used in the experiments should be included.

3. **Theoretical Analysis**: The paper lacks a formal theoretical analysis of the advantage estimation in MDPs, which is a major limitation given the empirical focus on complex control tasks. A more explicit formulation of the training objective for the advantage estimator and a theoretical justification for the weighting scheme would strengthen the methodology section.

4. **Comparison to Other Methods**: The paper compares DIT to in-context RL baselines but does not include a comparison to standard offline RL methods. Including such a comparison would help clarify whether DIT is superior to traditional offline RL when only suboptimal data is available.

5. **Assumption of Task Parameter**: The paper assumes that the task parameter τ is known, which is a practical limitation in many real-world applications. The paper should acknowledge this limitation and suggest ways to infer τ from the context in future work.

## Questions

1. **Advantage Estimator Training Objective**: The paper mentions that the advantage estimator is trained to interpolate across tasks, but it does not provide a detailed description of the training objective. How is the advantage estimator trained, and what is the specific loss function used?

2. **Theoretical Justification for Weighting Scheme**: The paper states that the exponential reweighting leads to guaranteed policy improvement, but it does not provide a formal theorem or lemma to support this claim. Can the authors provide a proof sketch or reference to related work that supports this claim?

3. **Comparison to Offline RL Baselines**: The paper compares DIT to in-context RL baselines but does not include a comparison to standard offline RL methods. How does DIT perform compared to traditional offline RL methods when only suboptimal data is available?

4. **Task Parameter Inference**: The paper assumes that the task parameter τ is known. How can the task parameter be inferred from the context in real-world applications where it is not explicitly known?

5. **Computational Cost**: The paper mentions the use of GPT-2 due to limited computational resources but does not provide any analysis of the computational trade-offs between DIT and other methods. How does the training time or inference cost of DIT compare to other methods?

6. **Advantage Estimator Accuracy**: The paper does not evaluate the accuracy of the advantage estimator. How accurate is the advantage estimator, and how does its accuracy affect the final policy performance?

7. **In-Context Learning Capacity**: The paper does not explore how the length of the context dataset affects performance. How does DIT perform with different lengths of context datasets, and is there a saturation point?

8. **Generalization to Unseen Task Distributions**: The experiments test the model on unseen goals or target velocities, but the task distribution pτ is not clearly defined. How does the model perform on tasks sampled from a different distribution than the pretraining data?

RATING: 7
