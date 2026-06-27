## Summary  
The paper introduces the Decision Importance Transformer (DIT), a supervised pretraining framework for in-context reinforcement learning (RL) that leverages suboptimal historical data. Unlike prior methods such as DPT and AD, which require optimal action labels or complete learning histories, DIT uses a weighted maximum likelihood estimation loss guided by an in-context advantage function estimator to improve over suboptimal policies. The authors demonstrate DIT's effectiveness on bandit and MDP problems, showing competitive performance with methods that have access to optimal data. The work addresses a practical challenge in in-context RL by relaxing the need for high-quality pretraining data, which is often scarce in real-world settings.

## Strengths  
- The paper presents a novel and theoretically grounded approach to in-context RL using suboptimal data, which is a significant departure from prior work that relies on optimal trajectories or labels.  
- The exponential reweighting technique, inspired by advantage-weighted regression, is a clever way to prioritize better actions within suboptimal datasets, enabling policy improvement without explicit optimal labels.  
- The experimental evaluation is comprehensive, covering both bandit and MDP problems, including challenging environments like Dark Room, Miniworld, MetaWorld, and Half-Cheetah. The results show that DIT performs competitively with DPT and AD, despite being pretrained on suboptimal data.  
- The ablation study comparing DIT to its unweighted variant (BC) highlights the importance of the reweighting mechanism, providing empirical validation of the method's core contribution.  
- The paper clearly articulates the limitations of imitation learning in the presence of suboptimal data and positions DIT as a solution to this problem, offering a coherent narrative.  

## Weaknesses  
- The methodology section lacks sufficient detail on how the in-context advantage function is estimated, particularly for tasks where the task identity is unknown. This makes it difficult to assess the robustness and generalizability of the approach.  
- The paper does not provide a formal derivation or justification for the exponential reweighting function, leaving it unclear whether the method is heuristic or grounded in a policy improvement theorem.  
- While the experiments are extensive, they do not include comparisons to standard offline RL methods (e.g., CQL, BCQ), which would help contextualize DIT's performance in the broader RL literature.  
- The reproducibility of the results is hindered by missing implementation details, such as the exact transformer architecture, hyperparameters (e.g., learning rate, batch size), and the specifics of the pretraining dataset generation.  
- The paper could benefit from a more thorough analysis of the trade-offs between the quality of the pretraining data and the performance of DIT, particularly in environments with varying levels of suboptimality.  
- The evaluation metrics are standard for RL, but the paper does not explore additional metrics (e.g., success rate, policy entropy) that could provide deeper insights into the behavior of the learned policies.  

## Questions  
- How is the task embedding $\tau$ constructed in the DIT framework, and is it learned or provided as explicit input? If learned, what is the procedure for inferring it from the context?  
- What is the theoretical basis for the exponential reweighting function? Is it derived from a policy improvement guarantee, or is it a heuristic? If the former, could the authors provide a derivation or reference?  
- The paper mentions that DIT requires behavioral policies with "reasonable rewards." What is the precise threshold for "reasonable," and how does the method perform when the behavioral policies are significantly suboptimal or random?  
- Could the authors provide a comparison to standard offline RL methods (e.g., CQL, BCQ) to better position DIT in the broader RL literature?  
- How does the performance of DIT scale with the number of context trajectories? The paper does not report results as a function of context size, which is a critical factor in in-context learning.  
- What is the computational cost of pretraining and inference for DIT compared to other in-context RL methods? This is important for assessing the practicality of the approach.  

RATING: 8