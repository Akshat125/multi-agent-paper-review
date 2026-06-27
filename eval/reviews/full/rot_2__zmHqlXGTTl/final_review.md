## Summary

The paper "SciPG: A New Benchmark and Approach for Layout-Aware Scientific Poster Generation" introduces a novel task called layout-aware scientific poster generation (LayoutSciPG), which aims to automatically generate flexible and high-quality scientific posters from research papers. The authors address the challenges of content extraction, paraphrasing, and layout design by proposing a multimodal extractor-generator framework. They also build a large-scale dataset, SciPG, containing over 10,000 pairs of scientific papers and their corresponding posters. The paper presents both qualitative and quantitative evaluations to demonstrate the effectiveness of the proposed approach.

## Strengths

1. **Novel Task Definition**: The paper introduces a well-motivated and timely task, LayoutSciPG, which combines content extraction and layout design for scientific poster generation. This task addresses a significant gap in the current literature, as previous approaches have primarily focused on either content extraction or layout composition.

2. **Large-Scale Dataset**: The creation of the SciPG dataset is a substantial contribution. The dataset's scale and diversity (covering CVPR, ICML, NeurIPS, and ICLR) provide a robust foundation for training and evaluating models. The dataset statistics and collection process are well-described, enhancing reproducibility.

3. **Comprehensive Framework**: The proposed multimodal extractor-generator framework is a significant advancement. The framework integrates a multimodal document extractor (MDE) for content extraction and an interactive generator (IG) with an adaptive memory mechanism for paraphrasing and layout generation. The use of RoBERTa for text encoding and CLIP for image encoding is well-justified, and the adaptive memory mechanism effectively addresses the challenges of long-term dependencies and GPU memory consumption.

4. **Thorough Evaluation**: The paper employs a combination of automatic metrics (ROUGE, ImgP, ImgR, Overlap, Coverage, Validity, Alignment, FD, and DreamSim) and human evaluation to assess the model's performance. The evaluation is comprehensive, covering text, image, and layout quality. The human evaluation criteria (Text Relevance, Image Accuracy, and Layout Aesthetics) are well-defined, and the use of multiple annotators enhances the reliability of the results.

5. **Ablation Studies and Parameter Sensitivity Analysis**: The paper includes ablation studies to assess the impact of different modules (e.g., KL-Divergence optimization, pretraining strategy, data extension strategy, and memory mechanism) and a parameter sensitivity analysis to evaluate the effects of memory size and KL-Divergence weight. These analyses provide valuable insights into the contributions of individual components and the robustness of the model.

6. **Topic-Aware Evaluation**: The paper evaluates the model's performance on data from different conferences (CVPR, ICML, NeurIPS, and ICLR), providing insights into its generalizability across different research domains. The topic-aware evaluation highlights the model's strengths and limitations in handling diverse content and layouts.

## Weaknesses

1. **Limited Baseline Comparisons**: The paper compares its model with a limited set of baselines (NeuralExt, MSMO, and AdaD2P). Including additional baselines, such as pure extractive summarization models, layout-only models, and template-based systems, would provide a more comprehensive evaluation of the proposed approach.

2. **Lack of Human Baseline**: The paper does not include a human baseline for comparison. Evaluating the model's performance against human-generated posters would provide a clearer benchmark for assessing its effectiveness and identifying areas for improvement.

3. **Dataset Accessibility**: While the dataset is well-described, it is not publicly available. Making the dataset accessible would enhance reproducibility and facilitate further research in this area.

4. **Metric Definitions and Thresholds**: The paper uses a variety of automatic metrics, but some of them lack clear definitions and thresholds. For example, the definitions of Validity, Alignment, and DreamSim are not explicitly stated, and the thresholds for determining valid or aligned elements are not specified. Providing clearer definitions and thresholds would improve the transparency and reproducibility of the evaluation.

5. **Human Evaluation Limitations**: The human evaluation lacks inter-annotator agreement scores, which are essential for assessing the reliability of the ratings. Additionally, the paper does not specify whether the annotators are domain experts, which could affect the evaluation of scientific content and layout aesthetics.

6. **Cross-Domain Generalizability**: The dataset is biased toward computer vision and machine learning conferences, which may limit the model's generalizability to other research domains. Conducting a cross-domain evaluation would provide insights into the model's ability to handle diverse content and layouts.

7. **Error Analysis**: The paper does not provide an error analysis of the model's failures in content extraction, paraphrasing, and layout generation. Identifying and analyzing common errors would help pinpoint areas for improvement and guide future research.

8. **Computational Efficiency**: The paper mentions the use of NVIDIA A100 GPUs but does not discuss the computational efficiency of the model. Including information on inference time, memory usage, and scalability would be valuable for practitioners.

## Questions

1. **Baseline Comparisons**: Why were the selected baselines (NeuralExt, MSMO, and AdaD2P) chosen, and how do they represent the state-of-the-art in content extraction and layout generation? Are there other baselines that could provide a more comprehensive evaluation of the proposed approach?

2. **Human Baseline**: Have the authors considered including a human baseline for comparison? How would the model's performance compare to human-generated posters in terms of content extraction, paraphrasing, and layout design?

3. **Dataset Accessibility**: Are there plans to make the SciPG dataset publicly available? If not, how can other researchers access the dataset for replication and further research?

4. **Metric Definitions and Thresholds**: Can the authors provide clearer definitions and thresholds for the automatic metrics used in the evaluation, such as Validity, Alignment, and DreamSim? How were the thresholds for determining valid or aligned elements determined?

5. **Human Evaluation**: Were the annotators in the human evaluation domain experts, and if not, how might this affect the evaluation of scientific content and layout aesthetics? Can the authors provide inter-annotator agreement scores to assess the reliability of the ratings?

6. **Cross-Domain Generalizability**: Have the authors considered evaluating the model on scientific papers from other domains, such as biology, physics, or social sciences? How might the model's performance vary across different research domains, and what are the potential challenges in generalizing the approach to diverse content and layouts?

7. **Error Analysis**: Can the authors provide an error analysis of the model's failures in content extraction, paraphrasing, and layout generation? What are the most common errors, and how might they be addressed in future work?

8. **Computational Efficiency**: Can the authors provide more information on the computational efficiency of the model, such as inference time, memory usage, and scalability? How does the model's efficiency compare to existing approaches, and what are the potential trade-offs between performance and computational cost?

RATING: 7