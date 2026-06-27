## Summary

The paper introduces MIA-Bench, a new benchmark designed to evaluate the ability of multimodal large language models (MLLMs) to adhere to complex instructions. The benchmark consists of 400 image-prompt pairs, each crafted to challenge the models' compliance with layered instructions. The paper also explores the use of supervised fine-tuning (SFT) to enhance the models' ability to follow instructions strictly. The evaluation results from a wide array of state-of-the-art MLLMs reveal significant variations in performance, highlighting areas for improvement in instruction fidelity.

## Strengths

1. **Novel Benchmark:** MIA-Bench is a novel and valuable addition to the field of MLLMs, focusing specifically on the ability to follow complex instructions, which is a critical aspect for real-world applications.

2. **Comprehensive Evaluation:** The benchmark includes a diverse set of 400 image-prompt pairs, covering a wide range of scenarios and instruction types. This comprehensive evaluation helps identify the strengths and weaknesses of different MLLMs.

3. **Detailed Methodology:** The paper provides a detailed description of the benchmark construction, including the principles followed for creating instructions and the evaluation methodology. This ensures that the benchmark is robust and reproducible.

4. **Significant Findings:** The evaluation results reveal notable variations in model performance, highlighting the need for improved training methods to enhance instruction compliance. The exploration of SFT shows promising results, demonstrating the potential for enhancing models' instruction-following capabilities.

5. **Comparison with Other Benchmarks:** The paper includes a comparison of MIA-Bench with other existing benchmarks, providing context and highlighting the unique aspects of MIA-Bench. This helps readers understand the significance and relevance of the new benchmark.

## Weaknesses

1. **Lack of Human Evaluation:** The paper relies solely on GPT-4o for evaluating the models' responses. While GPT-4o is a strong and capable model, using it as the sole judge introduces potential bias. Human evaluation or a consensus-based system using multiple judges would improve the reliability of the results, especially for subjective metrics like genre and grammar.

2. **Limited Ablation Studies:** The paper lacks detailed ablation studies on the hyperparameters used in the SFT experiments. Including ablation studies would help understand the impact of different hyperparameters on the model's performance and provide insights into the optimal training setup.

3. **Insufficient Details on Models and Benchmarks:** The paper does not provide detailed information on the models tested and the benchmarks used in the correlation analysis. Including this information would help readers better understand the correlation analysis and its implications.

4. **Minor Regressions on Other Benchmarks:** The paper mentions minor regressions on other benchmarks after SFT. While this is acknowledged, a more detailed analysis of the performance trade-offs on other benchmarks would help determine whether the SFT is task-specific or has broader implications for the model's generalization.

5. **Lack of Per-Category Analysis:** The paper does not report performance per instruction category or complexity level. Including a per-category breakdown would provide more granular insights into model strengths and weaknesses, helping identify specific areas for improvement.

## Questions

1. **Human Evaluation:** Have the authors considered incorporating human evaluation to validate the results obtained from GPT-4o? If so, what were the findings, and how do they compare with the automated evaluation?

2. **Ablation Studies:** The paper mentions that the model was trained for one epoch on the SFT data. Have the authors conducted ablation studies to determine the optimal number of epochs and other hyperparameters? What were the results of these studies, and how do they inform the choice of hyperparameters?

3. **Model and Benchmark Details:** Could the authors provide more details on the models tested and the benchmarks used in the correlation analysis? Specifically, which models were included in the evaluation, and which benchmarks were used to compute the meta ranking?

4. **Performance Trade-offs:** The paper mentions minor regressions on other benchmarks after SFT. Could the authors provide a more detailed analysis of the performance trade-offs on these benchmarks? Specifically, which benchmarks were affected, and by how much?

5. **Per-Category Analysis:** Have the authors analyzed the model performance per instruction category or complexity level? If so, what were the findings, and how do they inform the development of more effective training methods for improving instruction adherence?

RATING: 7