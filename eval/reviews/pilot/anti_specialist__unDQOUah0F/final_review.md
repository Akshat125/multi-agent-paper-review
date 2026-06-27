## Summary

The paper "VideoWebArena: Evaluating Long Context Multimodal Agents with Video Understanding Web Tasks" introduces VideoWebArena, a benchmark for evaluating the capabilities of long-context multimodal agents in video understanding. The benchmark consists of 2,021 web agent tasks based on manually crafted video tutorials, totaling almost four hours of content. The paper defines a taxonomy of long-context video-based agent tasks with two main areas of focus: skill retention and factual retention. The best model achieves 13.3% success on factual retention tasks and 45.8% on factual retention QA pairs, far below human performance at 73.9% and 79.3%, respectively. On skill retention tasks, long-context models perform worse with tutorials than without, exhibiting a 5% performance decrease in WebArena tasks and a 10.3% decrease in VisualWebArena tasks.

## Strengths

1. **Novel Benchmark**: The introduction of VideoWebArena is a significant contribution to the field, as it addresses the gap in existing benchmarks that focus primarily on text or static image inputs. The benchmark's comprehensive task design and diverse set of tasks make it a valuable resource for evaluating long-context multimodal agents.

2. **Task Taxonomy**: The paper's definition of a taxonomy for long-context video-based agent tasks, categorizing them into skill retention and factual retention, provides a structured approach to evaluating different aspects of video understanding. This taxonomy is novel and helps in systematically assessing agent capabilities.

3. **Comprehensive Evaluation**: The paper evaluates several state-of-the-art models, including GPT-4o and Gemini 1.5 Pro, on the VideoWebArena benchmark. This evaluation provides a detailed performance analysis, highlighting the strengths and weaknesses of current models and guiding future research.

4. **Real-World Relevance**: The tasks in VideoWebArena are designed to mirror real-life scenarios, making the benchmark highly relevant for real-world applications. This relevance is underscored by the fact that humans often use videos to learn or extract information, and AI assistants must possess similar capabilities.

5. **Open-Source Resources**: The paper makes the code, benchmark, and relevant documentation available online, facilitating further research and development in the field. This openness is crucial for the reproducibility and advancement of the research.

## Weaknesses

1. **Manual Task Creation**: The reliance on manually crafted video tutorials for creating tasks might not fully capture the diversity and complexity of real-world scenarios. This could limit the generalizability of the findings and the benchmark's applicability to more varied and complex tasks.

2. **Model Selection**: The use of specific models (e.g., GPT-4o, Gemini 1.5 Pro) might not be representative of all long-context multimodal agents. This could limit the generalizability of the performance analysis and the benchmark's relevance to other models.

3. **Lack of Detailed Analysis**: The paper could benefit from a more detailed analysis of why certain models perform better or worse on specific tasks. This could involve more qualitative analysis of the models' outputs or a deeper examination of the tasks themselves to identify key challenges and failure modes.

4. **Performance Degradation with Tutorials**: The finding that long-context models perform worse with tutorials than without on skill retention tasks is intriguing but not fully explained. The paper could provide more insights into why tutorials introduce negative noise that hampers model performance.

5. **Reproducibility Concerns**: While the paper provides a reasonable amount of detail about the VideoWebArena environment and the baseline agents, there are several areas where more information is needed to ensure full reproducibility. This includes details on the video creation process, task creation and quality assurance, human evaluation methodology, baseline agent implementations, hyperparameters and model settings, reward function, training data, evaluation metrics, and hardware or compute resources used.

## Questions

1. **Task Generalizability**: How representative are the manually crafted video tutorials of real-world scenarios? Could the benchmark be expanded to include more diverse and complex tasks to improve its generalizability?

2. **Model Representativeness**: Are the models evaluated in the paper (e.g., GPT-4o, Gemini 1.5 Pro) representative of the broader range of long-context multimodal agents? If not, how might the performance analysis differ with the inclusion of other models?

3. **Detailed Analysis of Model Performance**: What specific factors contribute to the varying performance of models on different tasks? Could a more detailed qualitative analysis of the models' outputs or a deeper examination of the tasks themselves provide insights into these factors?

4. **Impact of Tutorials on Performance**: Why do long-context models perform worse with tutorials than without on skill retention tasks? What specific aspects of the tutorials introduce negative noise or complexity that hampers model performance?

5. **Reproducibility Enhancements**: What additional details or information would be needed to ensure full reproducibility of the experiments and the benchmark? How might these details be incorporated into the paper to facilitate future research?

RATING: 7