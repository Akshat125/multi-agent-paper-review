### Summary

The paper introduces MIA-Bench, a new benchmark designed to evaluate multimodal large language models (MLLMs) on their ability to strictly adhere to complex instructions. The benchmark comprises 400 image-prompt pairs, each crafted to challenge the models' compliance with layered instructions. The paper also explores supervised fine-tuning (SFT) to enhance the models' ability to follow instructions. The evaluation includes a wide array of state-of-the-art MLLMs, both closed-source and open-source, providing a comprehensive comparison of their performance on MIA-Bench.

### Strengths

- **Comprehensive Benchmark:** MIA-Bench is a comprehensive benchmark that includes 400 diverse image-prompt pairs, covering a broad spectrum of real-world scenarios. The instructions are designed to be layered and compositional, challenging the models to follow multiple sub-instructions simultaneously.
- **Novel Focus:** The benchmark's unique focus on evaluating strict "instruction adherence" sets it apart from other benchmarks. This is a critical aspect that has been less explored in the context of multimodal LLMs.
- **Detailed Evaluation Methodology:** The evaluation methodology is well-explained, with a clear description of how responses are scored using GPT-4o. The paper provides a detailed example of how responses from different MLLMs are evaluated and scored.
- **Comprehensive Model Comparison:** The evaluation includes a wide range of MLLMs, both closed-source and open-source, providing a fair comparison of their performance on MIA-Bench.
- **Promising SFT Results:** The exploration of SFT to enhance the models' ability to follow instructions shows promising results, indicating the effectiveness of the proposed method.

### Weaknesses

- **Subjective Instruction Categories:** The instruction categories used for data collection are subjective and difficult to categorize objectively. This could introduce biases and limit the generalizability of the results.
- **Reliance on Automated Scoring:** The use of GPT-4o for scoring responses could introduce biases. The paper acknowledges this concern and uses Claude-3 as an alternative judge, but a more detailed analysis of the potential biases and their impact on the results would be beneficial.
- **Limited Human Evaluation:** The reliance on automated scoring methods could miss nuances that human evaluators might catch. Including human evaluation, even for a subset of responses, could enhance the robustness of the results.
- **Generalizability:** The benchmark includes a diverse set of image-prompt pairs, but it is important to consider whether the results are generalizable to other domains or real-world applications. Additional experiments or case studies could help address this concern.
- **Detailed Comparison with Other Benchmarks:** While the paper mentions discrepancies in model rankings between MIA-Bench and other benchmarks, a more detailed analysis of these discrepancies could provide valuable insights.

### Questions

1. **Instruction Complexity Categories:** How do the different complexity categories (basic, intermediate, advanced, creative, complex) impact model performance, and are there specific categories where models consistently struggle?
2. **Human Evaluation:** Have you considered including human evaluation as a supplementary method to enhance the robustness of the results? If so, what were the findings, and how do they compare with the automated scoring results?
3. **Bias in GPT-4o Scoring:** Have you conducted a detailed analysis of the potential biases introduced by using GPT-4o for scoring responses? If so, what were the findings, and how do they impact the overall results?
4. **Generalizability:** Have you conducted additional experiments or case studies to assess the generalizability of the results to other domains or real-world applications? If so, what were the findings, and how do they compare with the benchmark results?
5. **Detailed Comparison with Other Benchmarks:** Have you conducted a more detailed analysis of the discrepancies in model rankings between MIA-Bench and other benchmarks? If so, what were the findings, and what insights did they provide into the unique challenges posed by MIA-Bench?

RATING: 8