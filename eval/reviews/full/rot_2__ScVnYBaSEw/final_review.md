## Summary

The paper introduces UNSURE, a novel self-supervised learning approach that extends the traditional SURE method to handle cases where the noise level is unknown. The method addresses a critical limitation of the SURE framework by relaxing the zero-derivative constraint to an expected zero divergence constraint, allowing for a more flexible and expressive estimator while maintaining robustness to noise-level misspecification. The paper compares UNSURE to several existing methods, highlighting its advantages such as not requiring knowledge of the noise level and providing more expressive estimators than cross-validation methods. The potential applications of UNSURE are vast, including medical imaging, scientific imaging, computational photography, and any imaging inverse problem where the noise level is unknown or difficult to estimate.

## Strengths

1. **Theoretical Contribution**: The paper presents a theoretical framework that characterizes the robustness-expressivity trade-off in self-supervised learning, which is a significant contribution to the field. The relaxation of the zero-derivative constraint to an expected zero divergence constraint is a novel and well-motivated approach.

2. **Experimental Validation**: The paper includes a comprehensive set of experiments that demonstrate the effectiveness of UNSURE in various imaging inverse problems, including Gaussian denoising, Poisson-Gaussian noise in tomography, and accelerated MRI. The experiments cover a range of relevant inverse problems and provide a thorough comparison with existing methods.

3. **Practical Implications**: The method is shown to perform close to the theoretical bounds derived in the analysis, which is a strong validation of the theoretical framework. The paper also provides a clear and concise explanation of the methodology, making it accessible to readers.

4. **Potential Applications**: The paper highlights the vast potential applications of UNSURE, including medical imaging, scientific imaging, computational photography, and any imaging inverse problem where the noise level is unknown or difficult to estimate. This makes the method highly relevant and impactful in various real-world scenarios.

5. **Limitations Acknowledged**: The paper acknowledges the limitations of UNSURE, including its restriction to the ℓ2 loss, increased computational complexity, and potential performance degradation in cases where the signal distribution has high entropy. This transparency is commendable and helps readers understand the scope and limitations of the method.

## Weaknesses

1. **Restriction to ℓ2 Loss**: The method is currently restricted to the ℓ2 loss, which may not be suitable for all applications, especially those requiring more perceptual reconstructions. The paper acknowledges this limitation but does not provide a clear path forward for extending the method to other loss functions.

2. **Computational Complexity**: The proposed method is more computationally intensive than supervised learning due to the additional estimator evaluation during training. The paper acknowledges this limitation but does not explore or suggest strategies to mitigate this overhead, such as approximations or parallelization.

3. **Performance Degradation in High-Entropy Cases**: The method may experience performance degradation in cases where the signal distribution has high entropy, as the noise level estimator may not be able to distinguish between the variance coming from the ground truth distribution and that coming from the noise. The paper acknowledges this limitation but does not provide a clear strategy to mitigate it.

4. **Lack of Perceptual Metrics**: The paper uses PSNR as the primary metric for evaluating the performance of the method. However, PSNR is a distortion-based measure and may not fully capture perceptual quality, which is crucial in applications like medical imaging. The paper acknowledges this limitation but does not include a perceptual evaluation in the experiments.

5. **Implementation Details**: While the paper provides a clear explanation of the methodology, it lacks detailed implementation information, such as the exact architecture of the U-Net used in the experiments, the training procedure, and the hyperparameters used. This makes it challenging for readers to reproduce the results.

## Questions

1. **Extension to Other Loss Functions**: How can the UNSURE method be extended to other loss functions, such as ℓ1 or perceptual losses, to make it more versatile and applicable to a wider range of problems? What are the theoretical and practical challenges involved in this extension?

2. **Mitigating Computational Overhead**: What strategies can be employed to mitigate the computational overhead of the UNSURE method, such as approximations or parallelization? How can these strategies be integrated into the current implementation without significantly compromising the performance of the method?

3. **Handling High-Entropy Signal Distributions**: What strategies can be developed to mitigate the potential performance degradation of the UNSURE method in cases where the signal distribution has high entropy? How can the noise level estimator be improved to better distinguish between the variance coming from the ground truth distribution and that coming from the noise?

4. **Inclusion of Perceptual Metrics**: How can perceptual metrics, such as SSIM or LPIPS, be incorporated into the evaluation of the UNSURE method to provide a more complete picture of its performance, especially in applications where perceptual quality is crucial?

5. **Reproducibility of Results**: What additional implementation details, such as the exact architecture of the U-Net, the training procedure, and the hyperparameters used, can be provided to improve the reproducibility of the results? How can these details be integrated into the paper to make it more accessible to readers?

RATING: 8