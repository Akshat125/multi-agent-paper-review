### Summary

The paper "SciLitLLM: How to Adapt LLMs for Scientific Literature Understanding" proposes a hybrid strategy that integrates continual pre-training (CPT) and supervised fine-tuning (SFT) to adapt large language models (LLMs) for scientific literature understanding. The authors address two key challenges: constructing high-quality CPT corpora and generating diverse SFT instructions. The paper includes detailed descriptions of the methodology, experiments, and results, demonstrating the effectiveness of the proposed approach.

### Strengths

1. **Comprehensive Methodology**: The paper presents a well-justified and comprehensive methodology that addresses the key challenges in adapting LLMs for scientific literature understanding. The use of CPT and SFT, along with detailed steps for PDF text extraction, error correction, quality filtering, and instruction synthesis, makes the approach robust and practical.

2. **Thorough Experimental Design**: The experimental design is appropriate and well-executed, providing a comprehensive evaluation of the model's performance. The choice of benchmarks, including MMLU-Pro, MaScQA, SciAssess, and SciRIFF, covers a range of scientific domains and tasks, ensuring a thorough assessment.

3. **Meaningful Ablation Studies**: The ablation studies are well-designed and provide valuable insights into the contributions of different components of the method. The results validate the effectiveness of the proposed pipeline and highlight the importance of each component.

4. **Significant Contributions**: The paper makes several significant contributions to the field, including the hybrid strategy of CPT and SFT, the novel instruction synthesis method, and the promising performance of SciLitLLM on scientific literature understanding benchmarks.

5. **Generalizability**: The proposed pipeline can be easily adapted to other specialized domains, enhancing the broader impact of the work.

### Weaknesses

1. **Clarity of Key Concepts**: While the paper does a good job of explaining the overall methodology, some of the key concepts and terms could be clarified further. For example, the paper mentions "scientific knowledge" and "scientific tasks" frequently, but it would be helpful to have a more precise definition of these terms.

2. **Detail in Methodology**: The methodology section is generally well-detailed, but there are a few areas that could benefit from more specific information. For instance, the paper mentions using "PyPDF2" for PDF parsing, but it does not specify the exact parameters or settings used. Similarly, the paper describes the use of "Llama3-7B-Instruct" for format and grammar correction, but it does not provide the specific prompts or instructions used for this task.

3. **Experimental Setup**: The experimental setup is well-described, but there are a few areas that could be clarified. For example, the paper mentions using "GPT-4o" for instruction generation, but it does not specify the exact version or configuration of GPT-4o used. Additionally, the paper does not provide a detailed description of the evaluation metrics used for the benchmarks.

4. **Figures and Tables**: The figures and tables are generally well-presented and helpful, but there are a few that could be improved for clarity. For example, Figure 1 (the performance plot) could benefit from a more detailed legend or explanation of the axes and data points. Similarly, Table 1 (the data statistics table) could be more clearly labeled to indicate what each column represents.

5. **Consistency in Terminology**: The paper uses a mix of terms such as "SciLitLLM", "SciLitLLM-7B", and "SciLitLLM-14B". While the context usually makes it clear which model is being referred to, it would be helpful to have a consistent naming convention or a clear explanation of the differences between these models.

6. **Ablation Studies Integration**: The ablation studies are interesting and provide valuable insights, but they could be better integrated into the main text. Currently, they are presented in a separate section, which can make it difficult to see how they relate to the overall methodology and results. It would be helpful to have a more integrated discussion of the ablation studies, perhaps in the methodology or results sections.

### Questions

1. **Definition of Key Concepts**: Could the authors provide a more precise definition of "scientific knowledge" and "scientific tasks" as they are used in the context of this paper?

2. **Methodology Details**: Could the authors specify the exact parameters, settings, and prompts used in the methodology, particularly for PDF parsing and format and grammar correction?

3. **Experimental Setup Clarification**: Could the authors provide more details on the evaluation metrics used for the benchmarks and the exact version or configuration of tools such as GPT-4o used in the experiments?

4. **Figures and Tables Improvement**: Could the authors improve the clarity of figures and tables with more detailed legends and labels, particularly for Figure 1 and Table 1?

5. **Consistency in Terminology**: Could the authors use a consistent naming convention for the models and provide a clear explanation of the differences between "SciLitLLM", "SciLitLLM-7B", and "SciLitLLM-14B"?

6. **Ablation Studies Integration**: Could the authors better integrate the ablation studies into the main text for a more cohesive discussion, perhaps in the methodology or results sections?

RATING: 7