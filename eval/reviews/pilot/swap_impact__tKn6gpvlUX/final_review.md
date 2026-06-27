### Summary

The paper introduces a novel method, scDCA, for predicting transcriptional responses to novel drugs using single-cell foundation models (FMs) with drug-conditional adapters. The method achieves state-of-the-art results across various generalization tasks, including unseen drugs, unseen drug-cell-line combinations, and unseen cell lines (both few-shot and zero-shot). The paper provides a comprehensive evaluation framework and detailed methodology, highlighting the effectiveness and potential impact of the proposed approach.

### Strengths

- **Innovative Approach**: The use of drug-conditional adapters for efficient fine-tuning of single-cell FMs is a significant advancement in the field.
- **Comprehensive Evaluation**: The paper establishes a robust evaluation framework to assess model performance across different generalization tasks.
- **State-of-the-Art Results**: scDCA demonstrates significant improvements in few-shot and zero-shot generalization to new cell types compared to existing baselines.
- **Parameter Efficiency**: The method uses less than 1% of the parameters required by naive fine-tuning approaches, making it more accessible and scalable.
- **Detailed Methodology**: The methodology section is well-structured and provides a clear explanation of the problem definition, architecture, and fine-tuning strategy.

### Weaknesses

- **Limited Dataset**: The use of the sciplex3 dataset, which includes a limited number of cell lines and drugs, may impact the generalizability of the findings.
- **Lack of Hyperparameter Details**: The paper does not provide detailed information about the hyperparameters used for training, which is crucial for reproducibility.
- **Limited Discussion of Limitations**: The paper acknowledges some limitations but could discuss additional potential limitations, such as data quality, robustness to outliers, and potential biases.
- **Lack of Error Analysis**: A detailed error analysis could help identify sources of errors and potential areas for improvement.

### Questions

1. **Generalization to Other Cell Types and Drugs**: How well does the model generalize to cell types and drugs not included in the sciplex3 dataset? Are there plans to evaluate the model on more diverse and larger datasets?
2. **Impact of Hyperparameters**: What are the optimal hyperparameters for training the model, and how sensitive is the model's performance to these hyperparameters? Could the authors provide more details on the hyperparameters used in their experiments?
3. **Robustness to Data Quality and Outliers**: How robust is the model to variations in data quality and the presence of outliers? Could the authors discuss potential strategies to improve the model's robustness?
4. **Potential Biases in the Data**: Are there any potential biases in the sciplex3 dataset that could impact the model's performance? How could these biases be addressed or mitigated?
5. **Error Analysis**: Could the authors provide a more detailed error analysis to identify the sources of errors and potential areas for improvement? For example, how does the model perform on different types of drugs or cell lines, and how sensitive is the model to the choice of hyperparameters?

### RATING: 8