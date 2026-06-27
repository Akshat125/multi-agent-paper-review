### Summary

The paper "IgSeek: Fast and Accurate Antibody Design via Structure Retrieval" introduces a novel structure-retrieval framework for inferring CDR sequences by retrieving similar structures from a natural antibody database. The framework, IgSeek, employs a multi-channel equivariant graph neural network (MEGNN) to generate high-quality geometric representations of CDR backbone structures. The paper demonstrates that IgSeek is highly efficient in structural retrieval and outperforms state-of-the-art approaches in sequence recovery for both antibodies and T-Cell Receptors.

### Strengths

- **Novel Framework**: IgSeek introduces a new perspective on antibody design by leveraging structure retrieval, which addresses the challenges of hallucinations in traditional inverse folding methods.
- **Efficient and Accurate**: The framework is demonstrated to be both efficient and accurate, outperforming state-of-the-art methods in sequence recovery and inference speed.
- **Comprehensive Experiments**: The paper includes extensive experiments covering various aspects of the model's performance, including structure retrieval, sequence design, visualization, and a case study.
- **Generalization**: IgSeek shows strong generalization capabilities, performing well on both solved and predicted antibody structures, as well as T-Cell Receptors.
- **Detailed Methodology**: The methodology is well-described, with clear explanations of the MEGNN encoder, learning objectives, and sequence generation process.

### Weaknesses

- **Clarity of Introduction**: The introduction could be improved by providing more specific data on the low success rate of existing methods and clarifying ambiguous terminology such as "hallucinations."
- **Methodology Accessibility**: While detailed, the methodology section could be made more accessible with additional explanations and examples, particularly for readers who may not be familiar with graph neural networks.
- **Experimental Details**: The paper could benefit from more details on data sampling criteria, hyperparameters, and the sensitivity of the model to different threshold values.
- **Evaluation Metrics**: The primary use of Average Amino Acid Recovery (AAR) as an evaluation metric may not fully capture the functional aspects of the designed sequences. Including additional metrics, such as binding affinity or functional assays, would provide a more comprehensive assessment.
- **Ablation Studies**: The lack of ablation studies limits the understanding of the contribution of individual components of the IgSeek framework. Including such studies would help in identifying the key factors driving the model's performance.

### Questions

- **Hallucinations**: How does the retrieval-based approach in IgSeek specifically address the issue of hallucinations compared to traditional inverse folding methods?
- **Hyperparameter Sensitivity**: What is the sensitivity of IgSeek's performance to different hyperparameters, such as the number of layers in the MEGNN, the hidden dimension size, and the number of nearest neighbors (K) used in the retrieval process?
- **Generalization to Unseen Data**: How well does IgSeek generalize to antibody structures and sequences that are significantly different from those in the training data?
- **Functional Assays**: Are there plans to include functional assays or binding affinity measurements to assess the practical utility of the designed sequences?
- **Ablation Studies**: What are the results of ablation studies that examine the contribution of individual components of the IgSeek framework, such as the MEGNN encoder and the K-NN retrieval process?

RATING: 8