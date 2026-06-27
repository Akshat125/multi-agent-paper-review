## Summary

The paper "IgSeek: Fast and Accurate Antibody Design via Structure Retrieval" introduces a novel framework for antibody design that leverages structure retrieval to infer Complementarity-Determining Region (CDR) sequences. The method employs a multi-channel equivariant graph neural network (MEGNN) to generate geometric representations of CDR backbone structures and retrieves structurally similar CDRs from a natural antibody database to predict sequences. The paper claims that IgSeek outperforms state-of-the-art approaches in sequence recovery and inference speed, offering a new retrieval-based perspective for therapeutic protein design.

## Strengths

- **Novel Approach**: The paper introduces a novel structure-retrieval framework that addresses the challenges of hallucinations and low success rates in sequence inference, which are common in traditional protein inverse folding methods.
- **Comprehensive Evaluation**: The experimental studies are thorough, comparing IgSeek with several state-of-the-art models, including FoldSeek, ProteinMPNN, ESM-IF1, AbMPNN, and AntiFold. The results are presented clearly, using tables and figures to facilitate understanding.
- **High Performance**: IgSeek demonstrates superior performance in sequence recovery and inference speed, particularly on hyper-variable regions like CDR-H3, which are known to be challenging.
- **Generalization**: The model shows strong generalization capabilities, performing well on both solved and predicted antibody structures, as well as T-Cell Receptor (TCR) data.
- **Efficiency**: The framework is computationally efficient, achieving significant speed-ups compared to existing methods, which is crucial for high-throughput antibody design.

## Weaknesses

- **Lack of Detailed Hyperparameter Tuning**: The paper does not provide sufficient details about the hyperparameter tuning process, such as the range of values considered, the tuning method employed, and the criteria used for evaluation. This information is essential for reproducibility.
- **Insufficient Computational Resource Details**: The paper lacks specifications of the computational resources used for training the model and conducting the experiments, which are important for assessing the practicality and efficiency of the method.
- **Limited Ablation Studies**: The ablation studies are not thorough enough to understand the contribution of each part of the model. For example, the impact of the number of layers in the MEGNN, the READOUT function, and the perturbation introduced during training are not fully explored.
- **Handling of Variable-Length CDRs**: The paper does not clearly address how the framework handles variable-length CDRs, which is a critical aspect for real-world applications where CDR lengths can vary significantly.
- **Functional Validation**: The paper does not include functional validation of the inferred sequences, such as using structure prediction models to verify whether the sequences fold into the correct structures. This would provide stronger evidence for the model's effectiveness in reducing hallucinations.

## Questions

1. **Hyperparameter Tuning**: What specific hyperparameters were tuned, and what methods were used for tuning (e.g., grid search, random search, Bayesian optimization)? What were the ranges of values considered, and how were the optimal hyperparameters determined?
2. **Computational Resources**: What were the computational resources used for training the MEGNN and conducting the experiments? This includes specifications such as the type of GPU, CPU, RAM, and any other relevant hardware or software details.
3. **Ablation Studies**: Can the authors provide a more thorough ablation study that examines the impact of different hyperparameters, such as the number of layers in the MEGNN, the READOUT function, and the perturbation introduced during training, on the final AAR?
4. **Variable-Length CDRs**: How does the framework handle variable-length CDRs? If the framework is limited to fixed-length CDRs, what are the implications for real-world applications? If it can accommodate variable-length CDRs, what method is used for aligning sequences of different lengths?
5. **Functional Validation**: Have the authors considered using structure prediction models (e.g., AlphaFold, Rosetta) to validate whether the inferred sequences fold into the correct structures? If so, what were the results of these validations?

RATING: 7