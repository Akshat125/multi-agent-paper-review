## Summary
The paper introduces MIA-Bench, a benchmark for evaluating the instruction adherence of multimodal large language models (MLLMs). It consists of 400 image-prompt pairs with diverse image sources and eight sub-instruction categories, including description, length limit, mention, genre, grammar, math, perspective, and OCR. The evaluation uses GPT-4o as a judge to score responses based on their compliance with sub-instructions, and the paper explores supervised fine-tuning (SFT) to improve model performance on the benchmark. The results show significant performance variation across models and demonstrate that SFT can enhance instruction adherence without major trade-offs on other benchmarks. The authors aim to provide a tool for measuring and improving MLLMs' ability to follow complex instructions.

## Strengths
The paper makes a clear and novel contribution to the field of MLLM evaluation by introducing MIA-Bench, a benchmark that rigorously tests the ability of models to follow **layered and compositional instructions**. This is a meaningful departure from existing benchmarks, which often focus on either fixed-form answers or general open-ended conversations. MIA-Bench's emphasis on **strict instruction fidelity** is particularly relevant for real-world applications where precise compliance is essential.

The benchmark is **well-constructed**, with a **diverse set of image-prompt pairs** and a **comprehensive evaluation methodology** using GPT-4o as a judge. The use of **sub-instruction scoring** allows for a granular and objective assessment of model performance, which is a significant improvement over traditional metrics like BLEU or ROUGE. The paper also provides a **detailed comparison** of MIA-Bench with other benchmarks, highlighting the **discrepancies in model rankings**, which underscores the importance of the proposed evaluation framework.

The exploration of **SFT as a method to improve instruction adherence** is a **practically relevant contribution**. The results show a **notable improvement** in MIA-Bench performance for the LLaVA-NeXT-13b model, with only minor regressions on other benchmarks. This suggests that **instruction-tuning data** can be used to enhance the **precision and reliability** of MLLMs in real-world applications.

The paper is **well-motivated** and provides **clear examples** of the types of instructions used in MIA-Bench. The methodology is **thoughtful**, and the evaluation process is **reasonably rigorous**, with an attempt to validate the use of GPT-4o as a judge by comparing its scores with those of another strong model, Claude-3. The paper also includes a **comprehensive evaluation** of 29 MLLMs, covering both closed-source and open-source models, which is important for understanding the current state of the field.

## Weaknesses
While the paper presents a novel and significant contribution, there are several **methodological and analytical limitations** that reduce the robustness of the findings. The **SFT experiments** are limited in scope, as they are only conducted on one model (LLaVA-NeXT-13b) and for a single epoch. A more **comprehensive evaluation** across multiple models and training durations would strengthen the paper's contribution and provide a clearer picture of the effectiveness of the proposed training approach.

The **evaluation process** relies heavily on GPT-4o as a judge, and while the authors attempt to validate this by comparing it with Claude-3, the paper does not include **human evaluation** of the responses, especially for subjective categories like *genre* or *creative*. This **limits the interpretability** of the results and could introduce **judge bias**. Additionally, the **exact prompting strategy** for GPT-4o is not clearly described, which affects the **reproducibility** of the evaluation.

The **instruction creation process** is described as manual, but the paper does not provide **detailed validation** of the instructions. For example, it does not report **inter-annotator agreement** or any **human validation** to ensure that the instructions are unambiguous and answerable. This raises concerns about the **consistency and fairness** of the benchmark.

The **complexity levels** of the instructions (basic, intermediate, advanced, creative, complex) are mentioned but not clearly defined or balanced across the dataset. This could lead to **bias in the evaluation**, as certain models may be overrepresented in specific categories. The paper also does not provide a **detailed breakdown of the dataset** or the **training data composition**, which is essential for understanding the scope and limitations of the benchmark.

The **lack of public access** to the benchmark and evaluation code is a **critical issue** for reproducibility and adoption by the research community. The paper mentions that MIA-Bench will be open-sourced, but it does not provide a **link or timeline** for this, which hinders the ability of others to build upon the work.

Finally, the paper does not provide a **detailed error analysis** of the models' performance. For example, it does not break down the types of errors made across the different instruction categories, which would help in **identifying specific weaknesses** and guiding future improvements.

## Questions
1. Could the authors provide a **detailed description of the prompting strategy** used for GPT-4o in the evaluation process, including whether it was prompted to be strict or lenient in its scoring?
2. What is the **exact process for manual validation** of the SFT data, and how were the 100 sampled responses checked for instruction adherence?
3. Could the authors provide a **breakdown of the types of errors** made by models across the different instruction categories (e.g., grammar, genre, perspective)?
4. How were the **instruction complexity levels** (basic, intermediate, advanced, creative, complex) defined and balanced across the 400 image-prompt pairs in MIA-Bench?
5. Could the authors test the **SFT approach on multiple models** (e.g., Phi-3-Vision, CogVLM2) to assess its **generalizability** and provide a **statistical analysis** of the performance improvements?

RATING: 8