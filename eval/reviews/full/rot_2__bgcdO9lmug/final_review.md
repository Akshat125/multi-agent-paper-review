## Summary

The paper "RePrompt: Prompt Engineering for Large Language Models Agents through Reflection" introduces a novel method for optimizing prompts in LLM agents. The method, called RePrompt, leverages intermediate feedback from interactions and reflections with LLM agents to optimize the step-by-step instructions in the prompts. The paper presents experiments in PDDL generation and travel planning tasks to demonstrate the effectiveness of the method.

## Strengths

- **Novel Approach**: The paper introduces a novel method for prompt optimization that leverages intermediate feedback, which is a significant departure from existing methods that rely on a final solution checker.
- **Improved Performance**: The experimental results show that RePrompt can improve the performance of LLM agents in reasoning tasks, such as PDDL generation and travel planning.
- **No Need for Final Solution Checker**: RePrompt does not require a final solution checker, making it applicable in scenarios where such a checker is not available or is too expensive to use.
- **Clear Methodology**: The paper provides a clear and concise overview of the RePrompt method and its applications. The experimental results are well-presented and easy to understand.
- **Reproducibility**: The paper provides sufficient details about the datasets and experimental settings used, making it possible to reproduce the results.

## Weaknesses

- **Limited Evaluation**: The experiments are limited to only two tasks (PDDL generation and travel planning), and the improvements are not dramatic. It is unclear how well the method generalizes to other tasks and domains.
- **Lack of Detailed Analysis**: The paper does not provide a detailed analysis of the errors made by the LLM agents or a fine-grained error analysis to better understand the strengths and weaknesses of the proposed method.
- **Insufficient Baseline Comparisons**: The paper does not provide a clear comparison with other state-of-the-art prompt optimization methods. A more comprehensive evaluation against existing baselines would help to better understand the significance and impact of the proposed method.
- **Ambiguity in Methodology**: The paper describes the RePrompt method in a high-level manner, but some details are missing. For example, it is not clear how the summarizer and the prompt optimizer LLMs are implemented and trained.
- **Limited Discussion of Novelty**: While the paper claims to introduce a novel method, the core idea of using intermediate feedback for optimization is not entirely new. The paper could benefit from a more thorough discussion of how RePrompt differs from existing methods.
- **No Ablation Studies**: The paper does not provide any ablation studies to understand the contribution of different components of the RePrompt method. For example, it would be interesting to see how the performance changes when the summarizer or the prompt optimizer is removed or replaced with a simpler component.
- **No Evaluation of Scalability**: The paper does not discuss the scalability of the proposed method. It is unclear how well RePrompt would perform on larger-scale tasks or with more complex LLM agents.

## Questions

- How does RePrompt compare to other state-of-the-art prompt optimization methods in terms of performance and efficiency?
- Can RePrompt be applied to other tasks and domains beyond PDDL generation and travel planning? If so, what are the potential challenges and limitations?
- What is the computational complexity and resource requirements of the RePrompt method? How does it scale with the size and complexity of the task?
- How does the performance of RePrompt change when different components, such as the summarizer or the prompt optimizer, are removed or replaced with simpler components?
- What are the potential limitations and failure cases of the RePrompt method? How can they be addressed or mitigated?

RATING: 6