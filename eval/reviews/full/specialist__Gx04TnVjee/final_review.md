## Summary
The paper introduces 3DTrajMaster, a novel framework for controlling multi-entity 3D motions in video generation using 6DoF pose sequences. It addresses the limitations of 2D control signals by proposing a plug-and-play 3D-motion grounded object injector that fuses entity descriptions with their respective 3D trajectories. The method also introduces a 360$^\circ$-Motion Dataset, constructed using Unreal Engine rendering and GPT-generated trajectories, to overcome the lack of suitable training data. The experiments demonstrate that 3DTrajMaster achieves state-of-the-art results in both accuracy and generalization for 3D motion control, with applications in virtual cinematography, interactive games, and embodied AI systems.

## Strengths
The paper presents several strengths that contribute to its overall impact and technical soundness:
- **Novelty in 3D Motion Control**: 3DTrajMaster is the first to customize 6DoF multi-entity motion in 3D space for controllable video generation, establishing a new benchmark for fine-grained motion control. This is a significant departure from existing 2D-based methods and opens up new possibilities for more realistic and physically grounded video synthesis.
- **Plug-and-Play Architecture**: The proposed 3D-motion grounded object injector is modular and preserves the video diffusion prior, which is crucial for generalization. This design allows for flexible integration with existing video foundation models, making it a practical and scalable solution.
- **Custom Dataset Construction**: The 360$^\circ$-Motion Dataset is a valuable contribution, as it addresses the lack of diversity and quality in existing datasets. The use of GPT to generate 3D trajectories and UE for rendering is a creative and effective approach to generating high-quality training data.
- **Effective Techniques for Video Quality**: The video domain adaptor and annealed sampling strategy are well-motivated and contribute to maintaining high video quality while preserving motion accuracy. The ablation studies confirm the importance of these components.
- **Comprehensive Evaluation**: The paper includes both qualitative and quantitative evaluations, with comparisons to state-of-the-art 2D methods. The results show a clear improvement in trajectory accuracy and video quality, particularly in multi-entity scenarios and 3D occlusion handling.

## Weaknesses
Despite its strengths, the paper has several weaknesses and areas for improvement:
- **Limited Evaluation on Non-Human Entities**: The trajectory accuracy metrics are only evaluated on human entities due to the lack of a general 4D pose estimator. This restricts the evaluation of the model's performance on non-human entities like animals, cars, and robots, which are also claimed to be supported by the method.
- **Insufficient Reproducibility Details**: The paper lacks detailed implementation information, such as the exact architecture of the pose encoder, video diffusion model, domain adaptor, and gated self-attention layer. Additionally, the code and data are not publicly available, which hinders reproducibility.
- **Need for More Rigorous Baseline Comparisons**: While the paper compares with 2D-based methods, it does not include a 3D-aware baseline for a more direct comparison. The projection of 3D trajectories onto 2D for baseline evaluation is a valid approach, but the specifics of the projection method should be clarified to ensure a fair comparison.
- **Lack of Downstream Application Validation**: The paper claims applicability in virtual cinematography and embodied AI, but it does not provide direct evaluations in these domains. Including application-specific benchmarks would strengthen the practical impact of the proposed method.
- **Scalability and Generalization Concerns**: The model is limited to generating at most 3 entities per video, and the paper does not provide a quantitative analysis of how performance degrades with more entities. Additionally, the model is trained on synthetic data, and its generalization to real-world scenarios is not tested, which is a critical concern for practical deployment.

## Questions
1. How does the model ensure that the correct entity is associated with the correct trajectory in multi-entity settings, and is there a mechanism to prevent cross-talk between entities?
2. What is the exact architecture of the pose encoder, and how was it trained (from scratch or with pre-training)?
3. Could the model be tested on real-world data to assess its generalization ability beyond the synthetic 360$^\circ$-Motion Dataset?
4. How does the projection of 3D trajectories onto 2D for baseline comparison affect the fairness of the evaluation, and what specific projection method was used?
5. What are the specific failure cases of 3DTrajMaster in multi-entity scenarios, and how does the model handle misalignment between entity descriptions and motion sequences?

RATING: 8