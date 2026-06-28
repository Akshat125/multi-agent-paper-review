## Summary

The paper titled "RePrompt: Prompt Engineering for Large Language Models Agents through Reflection" introduces a novel method called RePrompt for optimizing prompts in LLM agents using intermediate feedback. The method addresses a significant limitation in current automatic prompt engineering (APE) methods, which rely on a final solution checker that is often expensive, inaccurate, or missing. The paper demonstrates the effectiveness of RePrompt in two different domains: PDDL generation and travel planning. The introduction provides a good overview of the research context but could benefit from additional clarity and specificity. The methods section is detailed but could be improved for better reproducibility. The experimental settings and procedures are well-described but lack detailed justification for certain choices. The results are presented clearly but could benefit from more detailed statistical analysis and discussion. The paper's contributions are significant, but additional evidence and discussion could enhance its impact.

## Strengths

- **Novel Method**: RePrompt introduces a novel approach to prompt engineering in LLM agents by leveraging intermediate feedback, addressing a critical gap in current APE methods.
- **Effectiveness in Different Domains**: The paper demonstrates the effectiveness of RePrompt in two diverse domains, PDDL generation and travel planning, providing strong evidence for its applicability.
- **Ablation Study**: The inclusion of an ablation study adds depth to the analysis, showing the impact of different components and settings on the method's performance.
- **Significant Contributions**: The method's ability to work without a final solution checker makes it particularly valuable for real-world applications where such checkers are often unavailable.

## Weaknesses

- **Clarity and Specificity**: The introduction and methods sections could benefit from additional clarity and specificity. For instance, the term "gradient descent"-like approach is not clearly defined, and intermediate feedback is not well-explained.
- **Reproducibility**: The methods section lacks pseudocode or a flowchart, detailed hyperparameter settings, and specific implementation details, making it challenging to reproduce the results.
- **Statistical Analysis**: The paper could benefit from a more detailed description of the statistical analyses used to compare the results, including the specific tests performed and their outcomes.
- **Baseline Methods**: The description of baseline methods and their configurations is insufficient, making it difficult to assess the validity of the comparisons made in the paper.
- **Ethical Implications**: The paper could benefit from a more detailed discussion of the ethical implications of the study, including the potential risks and benefits of the applications described.

## Questions

- How was the "gradient descent"-like approach specifically applied in the RePrompt method, and what are the detailed steps involved in this process?
- What specific criteria were used to select the hyperparameter settings, such as the temperature of 0 and the seed of 42, and how were these choices justified?
- Could the authors provide more detailed information about the expertise of the human evaluators, the evaluation criteria, and the inter-rater reliability in the PDDL generation task?
- What specific statistical tests were performed to assess the significance of the differences between the methods, and what were the results of these tests?
- How do the authors plan to address the limitations mentioned in the paper, such as the method's ability to catch hallucination errors and improve the instruction-following capability of LLMs?
- What are the computational costs associated with implementing RePrompt, and how feasible is it to deploy this method in real-world scenarios?

RATING: 7
