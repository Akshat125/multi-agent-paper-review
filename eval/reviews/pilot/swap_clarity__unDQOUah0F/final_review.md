## Summary

The paper introduces VideoWebArena (VideoWA), a benchmark for evaluating the capabilities of long-context multimodal agents in video understanding. VideoWA consists of 2,021 web agent tasks based on 74 manually crafted video tutorials, totaling almost four hours of content. The benchmark defines a taxonomy of tasks divided into two main areas: skill retention and factual retention. Skill retention tasks assess an agent's ability to use a human demonstration to complete a task efficiently, while factual retention tasks evaluate the agent's ability to retrieve specific, instruction-relevant information from a video. The paper presents the performance of state-of-the-art models on the benchmark, highlighting the need for improvement in current models.

## Strengths

- **Comprehensive Benchmark:** VideoWA provides a comprehensive and diverse set of tasks for evaluating long-context multimodal agents in video understanding. The inclusion of 2,021 tasks based on 74 video tutorials ensures a thorough evaluation of various aspects of video understanding and agentic capabilities.
- **Well-Defined Taxonomy:** The paper introduces a well-defined taxonomy of tasks, dividing them into skill retention and factual retention. This distinction allows for a nuanced evaluation of different aspects of video understanding and agentic abilities.
- **Robust Methodology:** The methodology is robust and well-documented. The use of a POMDP framework to define the agent's trajectory is appropriate and aligns with standard practices in agent evaluation. The observation space, action space, and task design are all well-defined and comprehensive.
- **Clear Presentation of Results:** The results are presented clearly and are supported by the data. The tables and figures provide a detailed breakdown of the performance of different agents across various task domains and categories, allowing for easy comparison and analysis.
- **Significant Findings:** The paper highlights the performance gap between state-of-the-art models and human performance, emphasizing the need for improvement in current models. This finding is significant and can guide future research efforts.

## Weaknesses

- **Reliance on Manually Crafted Videos:** The reliance on manually crafted video tutorials may introduce bias, as the videos are created by the authors and may not fully represent the diversity of real-world videos. Additionally, the manual creation process may limit the scalability of the benchmark.
- **Limited Evaluation of GPT4-o Agent:** The paper mentions that the GPT4-o agent was tested on a smaller subset of tasks due to compute constraints. This limitation may affect the generalizability of the results and could introduce bias.
- **Small Sample for Human Evaluation:** The evaluation of human performance is based on a sample of tasks attempted by three authors. While this provides a baseline for comparison, it may not fully represent the performance of a broader population. Including a more diverse and larger sample of human participants could provide a more accurate baseline for comparison.
- **Ambiguity in Task Generation:** The paper states that "we take 297 unique templates from VisualWebArena and 220 unique templates from WebArena, totaling 1621 total intents." This is confusing because 297 + 220 = 517, not 1621. It is possible that the 297 and 220 are multiplied by the number of variations or instances, but this is not made explicit. A more precise explanation of how the 2,021 tasks were generated would improve clarity.
- **Lack of Clear Definitions:** Some terminology, such as "intent," "intermediate intent," and "step," is not clearly defined in the main text. A formal definition of these terms would improve clarity and avoid ambiguity.
- **Insufficient Implementation Details:** The paper lacks detailed information on how the Set-of-Marks framework is implemented, how the reward function is defined, and how the video and audio inputs are processed and presented to the models. These details are essential for ensuring reproducibility.

## Questions

- How were the 74 video tutorials selected and created? What criteria were used to ensure diversity and representativeness of real-world videos?
- How was the subset of tasks for the GPT4-o agent selected? What criteria were used, and how does this subset compare to the full set of tasks?
- How were the human participants for the evaluation selected? What was the process for ensuring a diverse and representative sample?
- Can the authors provide a more detailed explanation of how the 2,021 tasks were generated from the 297 and 220 templates? What transformations or multiplications were applied to arrive at the total number of tasks?
- How is the "intent" and "intermediate intent" defined and operationalized in the context of the tasks? Can the authors provide a formal definition of these terms?
- What specific implementation details are missing that would be necessary for reproducing the experiments? For example, how is the Set-of-Marks framework implemented, and how are the video and audio inputs processed and presented to the models?

RATING: 7