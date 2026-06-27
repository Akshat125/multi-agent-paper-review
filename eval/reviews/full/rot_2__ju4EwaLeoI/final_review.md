## Summary

The paper "Ref-EMGBench: Benchmarking Reference Normalization for Electromyography Data" presents a comprehensive benchmarking of five amplitude-based normalization techniques (Z-score, Min-Max, RMS, MAV, and Peak) for mitigating domain shift in EMG-based hand gesture recognition. The study evaluates these methods using three publicly available datasets (CapgMyo DBb, NinaPro DB3, and DB5) and a leave-one-subject-out (LOSO) cross-validation approach. The authors demonstrate that Min-Max and Peak normalization methods consistently outperform others in terms of classification accuracy and domain shift reduction, as measured by metrics such as AUROC, MMD, and KL divergence. The paper also includes detailed visualizations, such as t-SNE plots and Wasserstein distance matrices, to illustrate the impact of normalization on feature space alignment.

## Strengths

1. **Comprehensive Benchmarking**: The paper systematically evaluates five popular normalization techniques, providing a thorough comparison of their effectiveness in mitigating domain shift in EMG data. This is a significant contribution to the field, as it offers a clear, data-driven comparison of methods that are often used but not extensively benchmarked.

2. **Diverse Datasets**: The use of three diverse datasets (CapgMyo DBb, NinaPro DB3, and DB5) ensures that the findings are robust and generalizable across different electrode configurations, subject populations, and recording conditions. This diversity is crucial for validating the applicability of the normalization methods in real-world scenarios.

3. **Detailed Visualizations**: The inclusion of t-SNE plots and Wasserstein distance matrices provides valuable insights into how normalization affects the feature space. These visualizations help in understanding the underlying mechanisms of domain shift reduction and the effectiveness of different normalization techniques.

4. **Inter-Subject vs. Intra-Subject Normalization**: The comparison of inter-subject and intra-subject normalization highlights the importance of leveraging inter-subject variability for improving model generalization. This finding is significant, as it challenges the conventional approach of using intra-subject normalization and provides a novel perspective on preprocessing strategies.

5. **Clear Evaluation Metrics**: The use of multiple evaluation metrics (accuracy, AUROC, MMD, and KL divergence) offers a comprehensive assessment of the normalization methods. These metrics provide a clear measure of both classification performance and domain shift reduction, ensuring a balanced evaluation.

## Weaknesses

1. **Lack of Hyperparameter Details**: The paper does not provide sufficient details about the hyperparameters used for the ResNet18 model and the optimization process. This includes the learning rate, batch size, number of epochs, optimizer, and any regularization techniques. Including these details is crucial for reproducibility and for understanding the specific choices made by the authors.

2. **No Normalization Baseline**: The paper does not include a no-normalization baseline for comparison. This is a critical omission, as it prevents the reader from understanding the absolute impact of normalization on model performance and domain shift mitigation. Including this baseline would provide a clearer picture of the necessity and effectiveness of normalization.

3. **Limited Sensitivity Analysis**: The paper uses a fixed learning rate and training duration across all normalization methods. A sensitivity analysis of these hyperparameters would help assess whether the observed performance differences are robust to variations in these settings or if they are contingent on the specific choices made.

4. **Statistical Significance Testing**: The paper does not include statistical tests to determine whether the performance differences between normalization methods are statistically significant. This is important for validating the robustness of the findings and ensuring that the observed improvements are not due to random variation.

5. **Limited Discussion of Method Limitations**: The paper does not discuss the limitations of the normalization methods, such as the sensitivity of Min-Max and Peak normalization to outliers, and the potential for overfitting when using small fine-tuning datasets. A more balanced discussion of these trade-offs would provide a clearer understanding of the practical applicability of the methods.

## Questions

1. **Hyperparameter Sensitivity**: How sensitive are the results to variations in learning rate and training duration? Would different hyperparameter settings lead to different conclusions about the effectiveness of the normalization methods?

2. **No-Normalization Baseline**: What would be the performance of the model without any normalization? How does this baseline compare to the normalized settings in terms of classification accuracy and domain shift reduction?

3. **Statistical Significance**: Are the performance differences between normalization methods statistically significant? Would the conclusions hold under rigorous statistical testing?

4. **Method Limitations**: What are the potential limitations of the normalization methods, such as sensitivity to outliers or overfitting? How do these limitations affect the practical applicability of the methods in real-world scenarios?

5. **Generalization to Other Datasets**: How would the normalization methods perform on other EMG datasets not included in the study? Would the findings be generalizable to different types of EMG signals or applications?

RATING: 7