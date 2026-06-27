### Summary

The paper "VideoWebArena: Evaluating Long Context Multimodal Agents with Video Understanding Web Tasks" introduces a novel benchmark for evaluating the capabilities of long-context multimodal agents in video understanding. The benchmark, VideoWebArena (VideoWA), consists of 2,021 web agent tasks based on manually crafted video tutorials, totaling almost four hours of content. The tasks are categorized into skill retention and factual retention, with the latter further divided into visual perception, audio perception, full video understanding, and temporal reasoning. The paper evaluates several state-of-the-art models, including GPT-4o and Gemini 1.5 Pro, and compares their performance to human baselines. The results highlight significant gaps in the current capabilities of long-context multimodal agents, particularly in tasks requiring video understanding and agentic reasoning.

### Strengths

1. **Comprehensive Benchmark Design**:
   - The benchmark includes a diverse set of tasks across six thematic environments (Reddit, Classifieds, Shopping, Shopping Admin, Map, and Gitlab), providing a comprehensive evaluation of agent capabilities.
   - The task taxonomy is well-defined, with a clear distinction between skill retention and factual retention tasks. The inclusion of intermediate intents for factual retention tasks allows for a more fine-grained analysis of the agent's capabilities.

2. **Realistic and Reproducible Environment**:
   - The use of real, locally hosted websites ensures that the benchmark is realistic and reproducible. The detailed description of the environment, including the POMDP framework, observation space, and action space, is a strength.

3. **Innovative Evaluation Metrics**:
   - The evaluation metrics, including task success rate and intermediate intent success rate, are well-designed and provide a comprehensive assessment of the agents' performance. The inclusion of human performance baselines is also a strength.

4. **Significant Findings**:
   - The results highlight significant gaps in the current capabilities of long-context multimodal agents, particularly in tasks requiring video understanding and agentic reasoning. The finding that long-context models perform worse with tutorials is counterintuitive and important, as it challenges the assumption that more context always leads to better performance.

5. **Open-Source and Reproducible**:
   - The code, benchmark, and relevant documentation are available at videowebarena.io, which is a major strength for reproducibility and future research.

### Weaknesses

1. **Limited Number of Videos**:
   - The benchmark includes 74 unique videos, which might be considered limited for a benchmark aiming to evaluate long-context understanding. More videos, especially longer ones, could provide a more rigorous test of the agents' capabilities.

2. **Limited Model Evaluation**:
   - The evaluation is limited to GPT-4o and Gemini 1.5 Pro. Including a wider range of models, including smaller or less capable models, could provide a more comprehensive evaluation of the benchmark's difficulty and the models' capabilities.

3. **Lack of Statistical Analysis**:
   - The paper does not provide any statistical analysis of the results, such as confidence intervals or p-values. This makes it difficult to assess the significance of the observed differences in performance.

4. **Inconsistent Performance Across Domains**:
   - The results show that the agents' performance is not consistent across different task categories and domains. This inconsistency suggests that the benchmark may not be robust, and that the agents' performance may be highly dependent on the specific tasks and domains.

5. **Limited Discussion of Practical Applications**:
   - The paper does not explicitly discuss how the benchmark can be used in real-world applications, nor does it propose specific use cases or deployment scenarios. A more detailed discussion of potential applications would help highlight the practical value of the work.

### Questions

1. **Task Design and Novelty**:
   - How much of the task design in VideoWebArena is novel versus adapted from WebArena and VisualWebArena? Could the authors clarify the overlap with existing benchmarks and the novelty of the task templates?

2. **Comparison with Other Benchmarks**:
   - How do the performance results on VideoWebArena compare with those on other long-context video benchmarks like LongVideoBench or PerceptionTest? A comparison with existing benchmarks would help contextualize the results and highlight the unique contributions of VideoWebArena.

3. **Impact of Tutorials on Performance**:
   - The paper finds that long-context models perform worse with tutorials. Could the authors provide a more detailed analysis of this phenomenon, including qualitative examples or failure cases? Understanding the reasons behind this performance decrease could provide valuable insights for future research.

4. **Statistical Significance**:
   - The paper does not provide any statistical analysis of the results. Could the authors include statistical analysis, such as confidence intervals or p-values, to assess the significance of the observed differences in performance?

5. **Practical Applications**:
   - What are the specific real-world applications the authors envision for this benchmark, and how do the results inform improvements in those domains? A more detailed discussion of potential applications would help highlight the practical value of the work.

6. **Video Licensing and Accessibility**:
   - The paper mentions that the videos are available via YouTube and Google Drive, but it does not provide details on the video licensing and accessibility. Could the authors clarify the licensing terms and ensure that the videos are usable in different research settings?

### RATING: 7