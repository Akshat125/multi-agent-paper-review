## Summary

The paper "SciPG: A New Benchmark and Approach for Layout-aware Scientific Poster Generation" introduces a novel task called layout-aware scientific poster generation (LayoutSciPG), which aims to automatically generate flexible and informative posters from scientific papers. The authors address the challenges of content extraction, layout design, and the scarcity of large-scale datasets in this domain. They build a large-scale dataset, SciPG, containing over 10,000 pairs of scientific papers and their corresponding posters. Additionally, they propose a multimodal extractor-generator framework that integrates content extraction and layout design, employing an adaptive memory mechanism to handle lengthy inputs and outputs effectively.

## Strengths

1. **Novel Task and Dataset**: The introduction of the LayoutSciPG task and the creation of the SciPG dataset are significant contributions. The dataset's scale and the task's comprehensive approach set this work apart from previous studies.

2. **Comprehensive Framework**: The proposed multimodal extractor-generator framework effectively addresses the challenges of content extraction and layout design. The use of an adaptive memory mechanism to handle long-term dependencies and GPU memory limitations is innovative and well-justified.

3. **Experimental Validation**: The paper presents a thorough experimental evaluation, including automatic and human assessments. The results demonstrate the effectiveness of the proposed approach, with significant improvements over baseline methods in both content extraction and layout generation.

4. **Ablation Studies**: The ablation studies provide valuable insights into the contributions of different modules within the framework. These studies help to validate the design choices and highlight the importance of components like the memory mechanism and KL-Divergence optimization.

5. **Topic-Aware Evaluation**: The topic-aware evaluation assesses the model's generalization capability across different conference proceedings. The results indicate that the model trained on all topics outperforms models trained on individual topics, demonstrating its robustness.

## Weaknesses

1. **Baseline Comparisons**: While the baseline methods are appropriate, the comparisons could be more diverse. Including methods specifically designed for layout prediction or text summarization would provide a more comprehensive evaluation.

2. **Evaluation Metrics**: The layout metrics (Overlap, Coverage, Validity, Alignment, FD, DreamSim) are comprehensive, but the paper could benefit from more detailed explanations or examples of how these metrics are calculated and interpreted. This would enhance the transparency and reproducibility of the results.

3. **Human Evaluation**: The human evaluation is valuable, but the sample size (50 document-poster pairs) is relatively small. Increasing the sample size or conducting a more detailed analysis of the annotators' feedback would provide more robust insights.

4. **Generalization**: The topic-aware evaluation is a good start, but it would be beneficial to assess the model's performance on a more diverse set of topics or domains. This would help to evaluate the model's generalization capability more thoroughly.

5. **Dataset Accessibility**: The paper does not provide clear information about the accessibility of the dataset for future research. Including a statement about whether the dataset will be made publicly available and where it can be accessed would be helpful.

## Questions

1. **Dataset Accessibility**: Will the SciPG dataset be made publicly available, and if so, where can it be accessed? This information is crucial for other researchers who may want to replicate or build upon the work.

2. **Implementation Details**: Could the authors provide more specific details about the implementation of the multimodal extractor and interactive generator, including the architecture, number of layers, size of hidden units, and type of attention mechanisms used?

3. **Hyperparameter Tuning**: How were the hyperparameters, such as the memory size and KL-Divergence weight, chosen? A more detailed discussion of the hyperparameter tuning process, including the range of values tested and the criteria used to select the final values, would be helpful.

4. **Training and Evaluation**: Could the authors provide more specific details about the training and evaluation process, including the number of training iterations, batch size, learning rate schedule, and the number of human annotators and criteria used for the human evaluation?

5. **Layout Metrics**: Could the authors provide more detailed explanations or examples of how the layout evaluation metrics (Overlap, Coverage, Validity, Alignment, FD, DreamSim) are calculated and interpreted? This would enhance the transparency and reproducibility of the results.

6. **Generalization**: How does the model perform on a more diverse set of topics or domains? Assessing the model's performance on a broader range of topics would provide more insights into its generalization capability.

RATING: 8
