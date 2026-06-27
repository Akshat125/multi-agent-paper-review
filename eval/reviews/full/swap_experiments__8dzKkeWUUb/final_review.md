## Summary

The paper "SciLitLLM: How to Adapt LLMs for Scientific Literature Understanding" introduces a hybrid strategy that integrates continual pre-training (CPT) and supervised fine-tuning (SFT) to adapt large language models (LLMs) for scientific literature understanding. The authors propose a pipeline to construct high-quality CPT corpora and diverse SFT instructions, addressing key challenges in scientific knowledge infusion and instruction-following capabilities. The paper presents SciLitLLM, a suite of models specialized in scientific literature understanding, and demonstrates their promising performance on relevant benchmarks.

## Strengths

1. **Hybrid Strategy for Scientific Literature Understanding**:
   - The integration of CPT and SFT is a novel and practical approach to address the challenges of scientific knowledge infusion and instruction-following capabilities in LLMs. This hybrid strategy is well-justified and demonstrates significant improvements over existing methods.

2. **Pipeline for High-Quality Data**:
   - The pipeline for constructing high-quality CPT corpora and diverse SFT instructions is a significant contribution. It provides a systematic and scalable solution to the challenges of data quality and diversity, which are critical for the development of effective domain-specific LLMs.

3. **Performance on Benchmarks**:
   - The performance of SciLitLLM on scientific literature understanding benchmarks is impressive. The models achieve promising improvements over leading LLMs, indicating the effectiveness of the proposed approach. The detailed ablation studies provide valuable insights into the contributions of different components of the pipeline.

4. **Clear and Logical Structure**:
   - The paper is well-structured and easy to follow, with clear sections and subsections. The figures and tables are well-presented and informative, enhancing the overall clarity and readability of the paper.

5. **Comprehensive Evaluation**:
   - The paper includes a comprehensive evaluation of the proposed approach, covering various aspects such as base model performance, instruction model performance, and ablation studies. The use of diverse benchmarks and baselines ensures a thorough and fair assessment of the model's capabilities.

## Weaknesses

1. **Lack of Detailed Methodology**:
   - While the paper provides a high-level overview of the proposed pipeline, some details are lacking, particularly in the methodology section. For example, the description of the instruction synthesis method and the quality filtering process could be more detailed to ensure full reproducibility.

2. **Limited Discussion on Data Volume and Quality**:
   - The paper acknowledges the relatively small volume of data used for CPT compared to existing pre-training datasets. However, it does not explore the impact of data volume on performance in a controlled experiment. Additionally, the criteria for selecting and filtering texts for the CPT quality filter are not clearly defined.

3. **Reliance on Closed-Source Models**:
   - The use of GPT-4o for instruction generation introduces a dependency on a closed-source model, which may limit the reproducibility of the dataset. The paper should consider using open-source models for instruction generation or at least provide a comparison of instruction quality between GPT-4o and open-source alternatives.

4. **Lack of Cross-Domain Generalization**:
   - The paper does not evaluate the model's generalization to unseen scientific domains. This is a critical test for the robustness of the proposed pipeline and should be addressed in future work.

5. **Statistical Significance Testing**:
   - The paper does not report statistical significance tests for the performance differences. This is a major oversight, as the reported improvements may not be statistically significant without such analysis.

## Questions

1. **Methodology Clarification**:
   - Can the authors provide more details on the instruction synthesis method, particularly how the probability table of domain keywords is obtained and how the scientific task list is compiled? Additionally, can they clarify the criteria used for selecting and filtering texts for the CPT quality filter?

2. **Data Volume and Quality**:
   - How does the relatively small volume of data used for CPT compare to existing pre-training datasets? Can the authors conduct a controlled experiment to explore the impact of data volume on performance?

3. **Open-Source Alternatives**:
   - Why was GPT-4o chosen for instruction generation? Can the authors consider using open-source models for instruction generation or provide a comparison of instruction quality between GPT-4o and open-source alternatives?

4. **Cross-Domain Generalization**:
   - Can the authors evaluate the model's generalization to unseen scientific domains? This would provide valuable insights into the robustness and versatility of the proposed pipeline.

5. **Statistical Significance**:
   - Can the authors include statistical significance tests for the performance differences reported in the paper? This would ensure that the reported improvements are not due to random variation.

RATING: 7