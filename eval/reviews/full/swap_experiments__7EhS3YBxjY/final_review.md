## Summary

The paper introduces MIA-Bench, a new benchmark designed to evaluate multimodal large language models (MLLMs) on their ability to strictly adhere to complex instructions. The benchmark comprises 400 image-prompt pairs, each crafted to challenge the models' compliance with layered instructions. The paper also explores supervised fine-tuning (SFT) to enhance the models' ability to follow instructions without compromising performance on other tasks. The evaluation results from a wide array of state-of-the-art MLLMs reveal significant variations in performance, highlighting areas for improvement in instruction fidelity.

---

## Strengths

1. **Novelty and Significance**:
   - The paper addresses a significant gap in the current research by focusing on precise adherence to layered and compositional instructions, which is crucial for practical applications.
   - MIA-Bench is a novel benchmark that provides a detailed analysis of popular MLLMs and suggests training methods for enhanced instruction following.

2. **Clear Contributions**:
   - The contributions of the paper are clearly stated and impactful, including the construction of MIA-Bench, a detailed analysis of popular MLLMs, and the proposal of training data and methods for supervised fine-tuning (SFT) to enhance models' ability to follow complex instructions.

3. **Comprehensive Evaluation**:
   - The paper provides a clear comparison with existing benchmarks and methods, highlighting the unique aspects of MIA-Bench and suggesting that excelling in tasks evaluated by existing benchmarks does not necessarily translate to superior instruction adherence capability.

4. **Well-Written and Structured**:
   - The paper is generally well-written and easy to understand, with a clear structure that guides the reader through the introduction, methodology, experiments, and related work.
   - The figures and tables are clear and informative, with well-labeled axes and clear legends. The figures, in particular, are helpful in illustrating the differences between MIA-Bench and other multimodal LLM benchmarks, as well as the performance of different models on MIA-Bench.

5. **Detailed Methodology**:
   - The methodology is described in enough detail to be reproducible, with clear explanations of the principles used to construct the instructions, the categories of sub-instructions, and the evaluation method.
   - The use of multiple sub-instruction categories (e.g., description, grammar, genre, length limit) allows for a more nuanced evaluation of the models' ability to handle different types of constraints.

---

## Weaknesses

1. **Lack of Detail in Methodology**:
   - The paper does not specify the exact prompt used to generate the instructions and responses with GPT-4v, nor does it provide the exact parameters used for the supervised fine-tuning.
   - The process of manually writing the 400 instructions is not described in sufficient detail. For example, how were the instructions manually written? Were they written by a team of annotators, and if so, what were their qualifications? Was there a quality control process in place to ensure consistency and fairness in instruction design?

2. **Unclear Sections**:
   - The paper mentions that the instructions are of various complexity levels, but it is not clear how these levels are defined or how they are used in the evaluation.
   - The paper does not provide a clear explanation of how the sub-instructions are weighted in the evaluation, which could be important for understanding the results.
   - The paper does not provide a clear explanation of how the correlation with other benchmarks is computed, which could be important for interpreting the results.

3. **Evaluation Bias**:
   - The use of GPT-4o as the judge is a reasonable choice given its strong performance in instruction adherence, but the lack of a detailed description of the scoring process is a concern.
   - The paper attempts to address this by using Claude-3 as an alternative judge, but the results from this alternative judge are not fully reported. For example, the paper states that GPT-4o scored itself 89.84 and Claude-3 scored it 85.89, but it does not provide the scores for other models when evaluated by Claude-3. This limits the ability to assess the robustness of the evaluation process.

4. **Results Presentation**:
   - The results are presented in a clear and structured manner, but the lack of actual data tables and figures prevents a thorough evaluation of the claims. The qualitative improvements from SFT are also not well-supported due to the absence of the example responses.

5. **Potential Flaws and Biases**:
   - The paper relies entirely on automated evaluation using GPT-4o. While this is efficient, it is not a substitute for human evaluation, especially for tasks involving creative writing, grammar, and genre. Human annotators could provide more nuanced and reliable feedback on these aspects.
   - The lack of a clear separation between the instruction design and evaluation phases could lead to unintentional overfitting or bias in the scoring process.
   - The paper introduces five levels of instruction complexity (basic, intermediate, advanced, creative, complex), but it does not report performance per complexity level. This is a missed opportunity to understand how instruction complexity affects model performance and to validate the effectiveness of the complexity categorization.

---

## Questions

1. **Evaluation Methodology**:
   - How was the GPT-4o scoring prompt constructed? Was it a fixed template or did it vary per instruction type?
   - What is the inter-rater reliability of the GPT-4o scoring? The paper mentions a 1% variation in results across multiple runs, but it does not clarify whether this is due to the model's internal randomness or the variability in the scoring process itself.
   - The paper mentions that 100 responses were manually checked for quality in the SFT data, but it does not specify whether the same manual evaluation was applied to the MIA-Bench test set. This is important for validating the reliability of the benchmark and the evaluation process.

2. **Instruction Generation and SFT Data Construction**:
   - How were the instructions manually written? Were they written by a team of annotators, and if so, what were their qualifications?
   - Was there a quality control process in place to ensure consistency and fairness in instruction design?
   - How were the weights assigned to sub-instructions? The paper states that the description sub-instruction is usually given a higher weight, but it does not explain the rationale or process for determining the weight distribution for other sub-instructions.

3. **Training Procedure for SFT**:
   - The SFT data is constructed by sampling 1000 images from COCO 2017 and generating 5 instructions per image using GPT-4v. However, the prompt used to generate these instructions is not provided in the text, only referenced in a figure (Figure~\ref{fig:sft_instruction}), which is not included here. This makes it difficult to reproduce the SFT data.
   - The training procedure (e.g., learning rate, optimizer, batch size, loss function) is not detailed. This is a major shortcoming, as it prevents other researchers from replicating the SFT experiments or understanding how the model was optimized for instruction adherence.
   - The evaluation of the SFT results is based on a comparison of the model's performance before and after training. However, the paper does not provide a statistical test (e.g., t-test, bootstrap confidence intervals) to determine whether the improvement is statistically significant.

4. **Results Presentation**:
   - The paper refers to Table~\ref{tab:my-table-SFT} and Table~\ref{tab:Evaluation result of MLLMs before and after SFT}, but these are not included in the text. Without these tables, it is impossible to verify the claims about the SFT results.
   - The discrepancy in rankings between MIA-Bench and other benchmarks is mentioned, but the actual meta-ranking calculation is not explained in detail. For instance, how was the average ranking computed across the other benchmarks? What were the specific rankings for each model on each benchmark?

5. **Instruction Complexity**:
   - The paper introduces five levels of instruction complexity (basic, intermediate, advanced, creative, complex), but it does not report performance per complexity level. This is a missed opportunity to understand how instruction complexity affects model performance and to validate the effectiveness of the complexity categorization.

---

RATING: 7
