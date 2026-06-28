## Summary

The paper "GenDataAgent: On-the-fly Dataset Augmentation with Synthetic Data" introduces a novel generative agent designed to augment training datasets with synthetic data on-the-fly. The method focuses on generating relevant synthetic data that aligns with the target training dataset distribution, prioritizing diverse and useful synthetic data that complements marginal training samples. The paper presents a comprehensive evaluation across various supervised image classification tasks, demonstrating the effectiveness of the proposed approach.

## Strengths

1. **Innovative Approach**: The paper introduces a unique method for synthetic data generation that dynamically adapts to the target dataset distribution. The use of marginal sampling and variance of gradients (VoG) filtering is a novel approach that addresses key challenges in synthetic data generation.

2. **Comprehensive Evaluation**: The experimental results are thorough and cover a wide range of datasets and tasks. The inclusion of fairness metrics, such as worst-case disparity, is particularly noteworthy and addresses an important aspect of model performance.

3. **Clear Methodology**: The methodology is well-described and logically structured. The use of algorithms and figures helps to illustrate the key steps and concepts, making the paper accessible and easy to follow.

4. **State-of-the-Art Performance**: The results demonstrate that GenDataAgent achieves state-of-the-art performance in terms of both accuracy and fairness. This is a significant achievement and highlights the potential of the proposed method.

5. **Addressing Real-World Challenges**: The paper tackles real-world challenges in synthetic data generation, such as ensuring diversity and alignment with the target distribution. The dynamic feedback mechanism is a particularly innovative solution to these challenges.

## Weaknesses

1. **Lack of Detailed Implementation Details**: While the methodology is well-described, some implementation details are missing or unclear. For example, the specific hyperparameters and training configurations used in the experiments are not fully specified, which could make it difficult to reproduce the results.

2. **Limited Discussion of Limitations**: The paper does not extensively discuss the limitations of the proposed method. For instance, the computational cost of the on-the-fly feedback mechanism and the potential scalability issues are not addressed in detail.

3. **Clarity in Ablation Study**: The ablation study is comprehensive but could benefit from more detailed explanations and statistical analysis. The relative importance of each component is not fully quantified, which could leave some readers questioning the incremental contributions.

4. **Baseline Comparisons**: The paper compares GenDataAgent with several existing methods, but the implementation details of these baselines are not fully described. This could raise questions about the fairness of the comparisons and the reproducibility of the results.

5. **Time Analysis**: The time analysis provided in the paper is not sufficiently detailed. The units of measurement and the components included in the time analysis are not clearly specified, which could make it difficult to interpret the results.

## Questions

1. **Reproducibility**: To ensure the reproducibility of the results, could the authors provide more detailed information on the implementation of the baselines and the specific hyperparameters used in the experiments?

2. **Computational Cost**: Given the dynamic nature of the on-the-fly feedback mechanism, what is the computational cost of the proposed method compared to static augmentation techniques? Are there any scalability issues that need to be addressed?

3. **Generalizability**: The paper evaluates GenDataAgent on several datasets, but how well does the method generalize to other domains or tasks beyond image classification? Are there any plans to test the method on more diverse datasets or tasks?

4. **Impact of VoG Filtering**: The VoG filtering strategy is a key component of the method. How sensitive is the performance of GenDataAgent to the choice of the number of checkpoints used in the VoG filtering process? Are there any alternative filtering strategies that could be explored?

5. **Fairness Metrics**: The paper uses worst-case disparity as a fairness metric. How does this metric compare to other fairness metrics, and are there any plans to incorporate additional fairness metrics in future work?

6. **Initial Synthetic Data**: In the synthetic data only scenario, how is the initial synthetic data generated and selected for the feedback mechanism? Could the quality of the initial synthetic data impact the performance of the method?

7. **Llama-2 Prompting**: The use of Llama-2 for caption perturbation is a novel approach. How does the performance of the method vary with different prompting strategies or fine-tuning configurations for Llama-2?

8. **Dynamic Feedback Mechanism**: The on-the-fly feedback mechanism is a significant innovation. How does the performance of the method compare to static augmentation techniques when the feedback mechanism is disabled? What are the key benefits of the dynamic feedback approach?

9. **Time Analysis**: The time analysis provided in the paper is not sufficiently detailed. Could the authors provide a more comprehensive breakdown of the time required for each step of the pipeline, including data generation, model training, and filtering?

10. **Ethical Considerations**: The paper briefly mentions an ethics statement, but could the authors provide more detailed information on the ethical considerations and potential biases associated with the use of synthetic data for training models?

RATING: 8
