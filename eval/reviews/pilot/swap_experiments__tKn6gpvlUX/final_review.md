### Summary

The paper titled "Efficient Fine-Tuning of Single-Cell Foundation Models Enables Zero-Shot Molecular Perturbation Prediction" introduces a novel approach for predicting transcriptional responses to molecular perturbations using single-cell foundation models (FMs). The authors propose a drug-conditional adapter (scDCA) that allows efficient fine-tuning of these models by training less than 1% of the original parameters. This method enables the prediction of cellular responses to novel drugs and the generalization to unseen cell types in both few-shot and zero-shot settings. The paper demonstrates state-of-the-art results across various generalization tasks, highlighting significant improvements in few-shot and zero-shot generalization to new cell types compared to existing baselines.

### Strengths

1. **Innovative Approach**: The introduction of the drug-conditional adapter (scDCA) is a significant innovation. It allows for efficient fine-tuning of single-cell FMs by incorporating molecular information while keeping the original weights frozen. This preserves the rich biological representations learned during pretraining and reduces the risk of overfitting.

2. **Zero-Shot Generalization**: The ability to generalize to unseen cell types in zero-shot and few-shot settings is a major strength. This addresses a critical gap in the field, where previous methods have focused primarily on predicting responses to novel drugs or drug-cell-line pairs.

3. **State-of-the-Art Performance**: The paper demonstrates state-of-the-art performance across various generalization tasks. The results show significant improvements, particularly in the more challenging tasks of few-shot and zero-shot generalization to new cell lines.

4. **Parameter Efficiency**: The scDCA approach uses less than 1% of the parameters required by naive fine-tuning methods. This makes the method more efficient and less prone to overfitting, especially in scenarios with limited data.

5. **Comprehensive Evaluation**: The paper includes a robust evaluation framework that assesses model performance across different generalization tasks. The use of multiple baselines and the detailed analysis of results provide a comprehensive evaluation of the proposed method.

### Weaknesses

1. **Limited Dataset Diversity**: The experiments are conducted on a single dataset, sciplex3, which includes only three human cancer cell lines and 188 drugs. The limited diversity of cell lines and drugs may restrict the generalizability of the results. Testing on additional datasets would strengthen the claims.

2. **Lack of Ablation Studies**: The paper does not include ablation studies on the adapter architecture. Exploring variations in the adapter design (e.g., different bottleneck sizes, different types of projection layers) would help confirm the optimality of the proposed design.

3. **DEG Selection Criteria**: The selection criteria for differentially expressed genes (DEGs) are not clearly stated. It is important to specify whether the selection is done using a statistical test and whether it is done per drug or globally. The lack of this detail could introduce a selection bias.

4. **True Zero-Shot Evaluation**: The zero-shot cell line task may not be a true zero-shot setting if the control gene expression of the test cell line is used during training. A true zero-shot setting would require the model to predict responses for a cell line it has never seen in any form, which would better validate the claim of zero-shot generalization.

5. **Biological Interpretability**: The paper does not explore whether the adapter layers provide biologically interpretable insights. Analyzing whether the adapter-generated biases correspond to known gene-drug interactions or pathways would strengthen the paper by showing that the model captures meaningful biological relationships.

6. **Statistical Significance Testing**: The paper lacks statistical significance testing (e.g., p-values or confidence intervals) to support the reported performance improvements. Including such tests would add rigor to the results.

### Questions

1. **DEG Selection Criteria**: Could you please clarify the criteria used for selecting the top 20 differentially expressed genes (DEGs)? Was a statistical test used, and if so, which one? Was the selection done per drug or globally?

2. **True Zero-Shot Evaluation**: In the zero-shot cell line task, was the control gene expression of the test cell line used during training? If so, this may not be a true zero-shot setting. Could you provide a true zero-shot evaluation where the test cell line is not used in any form during training?

3. **Ablation Studies**: Have you conducted ablation studies on the adapter architecture? For example, have you explored different bottleneck sizes, different types of projection layers, or different architectures for the bias generation function \( f_l^m \)? If not, could you consider including these studies to confirm the optimality of the proposed design?

4. **Biological Interpretability**: Have you analyzed whether the adapter-generated biases correspond to known gene-drug interactions or pathways? If not, could you consider including such an analysis to provide biologically interpretable insights?

5. **Statistical Significance Testing**: Have you conducted statistical significance testing (e.g., p-values or confidence intervals) to support the reported performance improvements? If not, could you include these tests to add rigor to the results?

6. **Additional Datasets**: Have you tested your method on additional datasets beyond sciplex3? If not, could you consider including experiments on other datasets to assess the generalizability of your method to different cell types and diseases?

7. **Comparison with Other Efficient Tuning Methods**: Have you compared scDCA with other parameter-efficient fine-tuning methods (e.g., LoRA, prefix-tuning) in the context of single-cell data? If not, could you consider including such a comparison to better understand the contribution of the drug-conditional design?

RATING: 8