## Summary
The paper presents a novel approach for predicting cellular responses to molecular perturbations, leveraging single-cell foundation models (FMs) and a drug-conditional adapter. The proposed method, scDCA, enables efficient fine-tuning of the FM by training less than 1% of the original model parameters, allowing for molecular conditioning while preserving the rich biological representation learned during pretraining.

## Strengths
* The paper introduces a novel and effective approach for predicting cellular responses to molecular perturbations.
* The methodology is well-motivated and logically justified.
* The experimental design is comprehensive, with appropriate dataset, data splitting, evaluation metrics, and baselines.
* The results demonstrate the superiority of scDCA over existing methods and its robustness across different tasks and molecular targets.

## Weaknesses
* The approach is currently only applicable to transformer-based foundation models.
* The method requires the presence of control gene expression data.
* The evaluation of perturbation models, especially in the single-cell domain and for the generalization to new cell lines and conditions, is challenged by the limited size of publicly available data.

## Questions
* How does the performance of scDCA compare to other state-of-the-art methods in the field of molecular perturbation prediction?
* Can the scDCA approach be extended to other types of foundation models, such as those based on convolutional neural networks or recurrent neural networks?
* How does the choice of molecular embedding model (e.g., ChemBERTa) affect the performance of scDCA, and are there other molecular embedding models that could be used instead?

RATING: 9