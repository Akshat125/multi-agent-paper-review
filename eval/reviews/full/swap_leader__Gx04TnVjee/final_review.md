## Summary  
The paper introduces 3DTrajMaster, a novel framework for controllable video generation that enables precise manipulation of multi-entity 3D motions using 6 degrees of freedom (DoF) pose sequences. It addresses the limitations of 2D control signals by proposing a plug-and-play 3D-motion grounded object injector, a custom 360$^\circ$-Motion Dataset, and techniques like a video domain adaptor and annealed sampling. The experiments demonstrate that 3DTrajMaster outperforms existing methods in both trajectory accuracy and video quality, particularly in multi-entity scenarios involving 3D occlusion and diverse motion patterns. The paper also highlights the ability to customize entity descriptions (e.g., human attributes) and supports a range of entity types and backgrounds. However, it acknowledges limitations in handling fine-grained local motions and interactions between entities.

## Strengths  
3DTrajMaster presents a compelling and technically sound approach to 3D motion control in video generation, with several notable strengths:  

1. **Novelty in 3D Motion Control**: The paper is the first to address multi-entity 3D motion control using 6DoF pose sequences, which is a significant departure from 2D-based methods. This aligns with the growing need for 3D-aware video generation in applications like virtual cinematography and embodied AI.  

2. **Plug-and-Play Object Injector**: The proposed object injector, which uses a gated self-attention mechanism to fuse entity descriptions and 3D trajectories, is a flexible and effective design. It preserves the video diffusion prior, enabling generalization to diverse entities and motion patterns. The experiments show that this design outperforms alternatives like cross-attention fusion.  

3. **Custom 360$^\circ$-Motion Dataset**: The dataset is a major contribution, addressing the lack of high-quality, diverse 3D motion data. It leverages Unreal Engine (UE) for rendering and GPT for trajectory generation, ensuring a scalable and controllable data pipeline. The use of 12 evenly distributed cameras to capture 360-degree views is particularly innovative for training 3D-aware models.  

4. **Effective Techniques for Video Quality**: The video domain adaptor and annealed sampling strategy are well-integrated and demonstrate clear benefits in mitigating domain shift and improving video quality. Ablation studies confirm their importance, showing significant degradation when these components are removed.  

5. **Comprehensive Evaluation**: The paper includes both qualitative and quantitative comparisons with state-of-the-art 2D methods (MotionCtrl, Direct-a-Video, Tora). The results highlight 3DTrajMaster’s superiority in handling 3D occlusion and complex motion patterns. The evaluation metrics (RotErr, TransErr, FVD, FID, CLIPSIM) are well-chosen and provide a balanced assessment of motion accuracy and video realism.  

6. **Fine-Grained Entity Customization**: The ability to modify human attributes (e.g., hair, clothing, gender) is a strong feature, showcasing the model’s flexibility in handling detailed entity descriptions. This is supported by the diverse entity and background examples in the figures.  

## Weaknesses  
While 3DTrajMaster is a strong contribution, there are several weaknesses and concerns that need addressing:  

1. **Limited Evaluation on Non-Human Entities**: The trajectory accuracy metrics are only evaluated on human entities due to the lack of a robust 4D pose estimator for non-rigid objects like animals. This limits the validation of the method’s generalization to other entity types.  

2. **Lack of Public Code and Dataset**: The paper does not make the code or dataset publicly available, which hinders reproducibility and broader adoption. While the paper provides detailed implementation details, the absence of open resources makes it difficult for the community to build upon this work.  

3. **Insufficient Analysis of Local Motions and Interactions**: The paper acknowledges that the current model is limited to global motion patterns and cannot handle fine-grained local motions (e.g., dancing, waving hands) or interactions between entities (e.g., a man picking up a dog). This is a notable limitation for real-world applications requiring detailed motion control.  

4. **Ambiguity in GPT-Generated Trajectory Design**: The process of generating 3D trajectories using GPT is described in a high-level manner. More details on how the trajectories are structured, validated, or refined would strengthen the methodology.  

5. **Potential Over-Reliance on Synthetic Data**: The 360$^\circ$-Motion Dataset is synthetic, and while the domain adaptor is used to reduce style bias, the paper does not explore how the model performs on real-world data. This raises concerns about the practical applicability of the method.  

6. **Missing Computational Complexity Analysis**: The paper does not discuss the computational cost or scalability of the proposed approach, which is critical for deployment in real-time applications or large-scale systems.  

## Questions  
1. How does the model perform when applied to real-world video data, and are there plans to evaluate it on such datasets?  
2. What specific criteria or constraints are used to generate and validate the GPT-derived 3D trajectories?  
3. Could the model be extended to handle fine-grained local motions (e.g., hand gestures) and interactions between entities (e.g., object manipulation)? If so, what architectural or training modifications would be required?  
4. What is the computational overhead introduced by the 3D-motion grounded object injector and domain adaptor compared to standard 2D methods?  
5. How does the model handle cases where the input entity descriptions are ambiguous or conflicting with the 3D trajectories?  

RATING: 8