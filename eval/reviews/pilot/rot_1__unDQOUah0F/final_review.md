### Summary

The paper "VideoWebArena: Evaluating Long Context Multimodal Agents with Video Understanding Web Tasks" introduces VideoWebArena, a benchmark for evaluating the capabilities of long-context multimodal agents in video understanding. The benchmark consists of 2,021 web agent tasks based on manually crafted video tutorials, totaling almost four hours of content. The paper defines a taxonomy of long-context video-based agent tasks with two main areas of focus: skill retention and factual retention. The best model achieves 13.3% success on factual retention tasks and 45.8% on factual retention QA pairs, far below human performance at 73.9% and 79.3%, respectively. On skill retention tasks, long-context models perform worse with tutorials than without, exhibiting a 5% performance decrease in WebArena tasks and a 10.3% decrease in VisualWebArena tasks.

### Strengths

- **Comprehensive Benchmark**: The introduction of VideoWebArena provides a comprehensive and diverse set of tasks for evaluating long-context multimodal agents, addressing a significant gap in the current benchmarks.
- **Novel Taxonomy**: The paper defines a novel taxonomy of long-context video-based agent tasks, focusing on skill retention and factual retention, which offers a structured framework for understanding and improving agent capabilities.
- **Real-World Relevance**: The use of manually crafted video tutorials ensures that the tasks are realistic and relevant to real-world scenarios, making the benchmark more challenging and applicable.
- **Detailed Evaluation**: The paper provides a detailed evaluation of baseline agents, including Video Summary Agent, Video Frame Agent, and Video Agent, using state-of-the-art models like GPT-4o and Gemini 1.5 Pro.
- **Human Performance Benchmarks**: The inclusion of human performance benchmarks provides a useful point of comparison for the agents' performance, highlighting the deficiencies in current models.

### Weaknesses

- **Manual Creation of Videos**: The reliance on manually crafted video tutorials may introduce biases or limitations in the diversity of the tasks and scenarios presented. Automated or semi-automated methods for generating video tutorials could increase the diversity and scalability of the benchmark.
- **Compute Constraints**: The paper mentions that the GPT4-o agent was tested on a smaller subset of tasks due to compute constraints, while the Gemini agent was tested on the full set of tasks. This discrepancy could potentially introduce biases in the comparison of the agents' performance.
- **Generalizability**: The focus on web agent tasks may limit the generalizability of the results. Future work could explore the extension of the benchmark to include a wider range of tasks and environments to improve the generalizability of the results.
- **Lack of Detailed Error Analysis**: The paper mentions that LLMs can perform the necessary VQA to extract the necessary information for the task at hand but fall short due to hallucinations, action grounding, and high-level planning errors. However, it does not provide a detailed error analysis or examples of these failure modes, which would improve the clarity of the results and the overall understanding of the benchmark's challenges.

### Questions

- **Task Creation Process**: How were the 1621 skill retention tasks and 400 factual retention tasks generated? What criteria were used to select the intent templates from WebArena and VisualWebArena?
- **Video Creation and Validation**: What tools or software were used to record the videos? What is the resolution, frame rate, and format of the videos? How were the videos validated for quality and relevance to the tasks?
- **Implementation Details**: How is the video summary generated for the Video Summary Agent? How is the video processed into frames for the Video Frame Agent? What are the exact input formats and hyperparameters used for the models?
- **Reward Function**: What constitutes a "correct state" for a given task? How is the final evaluation function implemented for each task? Are there any domain-specific rules or heuristics used in the evaluation?
- **Model Evaluation**: How were the models accessed (e.g., via API, local deployment)? What specific versions of the models were used (e.g., GPT-4o vs. GPT-4o-mini)?
- **Error Analysis**: Can the authors provide a more detailed error analysis, including examples of tasks where the models failed and why? This would help readers understand the limitations of the current models and the challenges of the benchmark.

RATING: 7