## Summary

The paper "VideoWebArena: Evaluating Long Context Multimodal Agents with Video Understanding Web Tasks" introduces a novel benchmark, VideoWebArena (VideoWA), designed to evaluate the capabilities of long-context multimodal agents in understanding and processing video inputs to accomplish various tasks. The benchmark consists of 2,021 web agent tasks based on manually crafted video tutorials, totaling almost four hours of content. The paper defines a taxonomy of long-context video-based agent tasks, focusing on two main areas: skill retention and factual retention. The evaluation of several state-of-the-art models on the benchmark highlights the current limitations of these models in achieving human-level performance.

## Strengths

- **Novelty and Significance**: The paper introduces a novel and comprehensive benchmark for evaluating long-context multimodal agents, addressing a critical gap in the field. The benchmark is built on manually crafted video tutorials, providing a realistic and substantial dataset for evaluation.
- **Task Taxonomy**: The paper defines a clear and meaningful taxonomy of tasks, distinguishing between skill retention and factual retention, and further subdividing factual retention into four subcategories. This allows for a fine-grained analysis of model capabilities.
- **Intermediate Intent Evaluation**: The inclusion of intermediate intent evaluation for factual retention tasks is a novel and impactful design, allowing the authors to decouple the video understanding component from the agentic action execution.
- **Open-Source and Reproducibility**: The authors make the benchmark, code, and documentation publicly available, ensuring that the community can build upon and extend the work, and supporting reproducibility and transparency.
- **Thorough Experimental Design**: The experimental design is well-structured and methodologically sound, with a clear focus on evaluating the capabilities of long-context multimodal agents in a realistic and interactive environment. The use of three distinct baseline agents and automated evaluators ensures a rigorous and scalable evaluation process.
- **Comprehensive Results and Analysis**: The results are presented in a detailed and structured manner, with separate tables for factual and skill retention tasks, and subcategories within factual retention. The authors also analyze the performance trends across different models and input types, highlighting key failure modes.
- **Clear and Quality Writing**: The paper is well-written and clearly structured, making it accessible to both researchers and practitioners in the field. The use of tables, figures, and examples helps to clarify complex concepts and provides a good understanding of the task design and results.

## Weaknesses

- **Limited Model Evaluation**: The paper tests only a few models (GPT-4o and Gemini 1.5 Pro) and does not provide a comprehensive evaluation of the current state-of-the-art models in the field. This limits the generalizability of the findings.
- **Human Performance Evaluation**: The human performance evaluation is conducted by only three authors, which may introduce bias and may not be representative of a broader population's performance.
- **Skill Retention Tasks**: The paper reports that long-context models perform worse with tutorials than without, exhibiting a 5% performance decrease in WebArena tasks and a 10.3% decrease in VisualWebArena tasks. This counterintuitive result warrants further investigation and discussion. The paper does not delve deeply into why this might be the case or potential reasons for this performance drop.
- **Video Frame Agent**: The video frame agent uses a fixed number of frames (60) for all videos, regardless of their length or content. This approach may not capture the most relevant information for all tasks, potentially biasing the results.
- **Task Creation Process**: The paper mentions that three authors created videos and corresponding tasks, with cross-validation by a fourth author. However, it does not provide detailed guidelines or criteria used for task creation, which could introduce subjectivity and inconsistency in task design.
- **Video Difficulty Ratings**: The paper introduces video difficulty ratings (easy, medium, hard) but does not provide clear definitions or criteria for these ratings. This lack of clarity may make it difficult for other researchers to replicate or build upon this work.
- **Intermediate Intents**: The paper introduces intermediate intents for factual retention tasks but does not clearly explain how these intents are derived or why they are necessary. Additionally, the relationship between intermediate intents and final task performance is not thoroughly explored.
- **Model Performance Analysis**: The paper presents model performance data but does not provide a detailed analysis of the results. For instance, it does not discuss the reasons behind the varying performance of different models or the implications of these results for the development of long-context multimodal agents.
- **Narrow Focus on Web Tasks**: The benchmark focuses solely on web-based tasks, which may not fully capture the range of real-world applications for long-context multimodal agents. Expanding the scope to include other types of tasks or environments could provide a more comprehensive evaluation.
- **Manual Video Creation**: The paper relies on manually created videos, which may not be scalable or representative of the wide variety of videos available online. Automating the video creation process or using a more diverse set of videos could improve the benchmark's validity.
- **Limited Evaluation Metrics**: The paper primarily uses task success rates and intermediate intent success rates as evaluation metrics. Incorporating additional metrics, such as efficiency, robustness, or generalization, could provide a more nuanced understanding of model performance.
- **Lack of Error Analysis**: The paper does not provide a detailed error analysis, making it difficult to identify specific failure modes or areas for improvement in the evaluated models.

## Questions

1. **Clarification on Experimental Design**:
   - The paper mentions that the videos were created by three of the paper's authors and then cross-validated by a fourth author. Could you provide more details on the criteria used for creating the videos and tasks, as well as the cross-validation process? Specifically, how was the understandability and completeness of the tasks ensured, and were there any specific guidelines or metrics used during this process?

2. **Additional Analyses or Experiments**:
   - The results show that long-context models with tutorials perform worse than models without tutorials on skill retention tasks. Could you explore this further by conducting additional experiments or analyses to understand why the tutorials introduce negative noise? For instance, could you compare the performance of models with and without tutorials on a subset of tasks where the tutorials are simplified or broken down into smaller segments?

3. **Potential Limitations or Biases**:
   - The paper highlights that the benchmark includes a diverse set of tasks and videos. However, could you discuss any potential biases in the selection of tasks or videos? For example, are the tasks and videos representative of a broad range of real-world scenarios, or are they skewed towards certain types of tasks or domains? Additionally, how might these biases impact the generalizability of the benchmark's results?

4. **Model Performance Analysis**:
   - The paper presents a comparison of different baseline agents, including the Video Summary Agent, Video Frame Agent, and Video Agent. Could you provide a more detailed analysis of the performance differences between these agents? For instance, what specific aspects of the tasks or videos make certain agents perform better or worse? Additionally, could you explore the impact of varying the number of frames or the quality of the video summaries on the agents' performance?

5. **Human Performance Evaluation**:
   - The paper mentions that human performance was evaluated on a subset of tasks. Could you provide more details on the selection of these tasks and the criteria used for evaluating human performance? Additionally, could you discuss any potential limitations or biases in the human performance evaluation process, such as the variability in human performance or the potential for human errors?

RATING: 7