## Summary

The paper "Gradient-Free Analytical Fisher Information of Diffused Distributions" introduces a novel, gradient-free method for calculating the Fisher Information in diffusion models. The authors derive an analytical formulation of the Fisher Information (AFI) by leveraging the inherent structure of diffused distributions, which avoids the need for time-consuming gradient calculations. The paper proposes two algorithmic variants of AFI: AFI Trace Matching (AFI-TM) for evaluating the trace of the Fisher Information, and AFI Endpoint Approximation (AFI-EA) for applying Fisher Information as a linear operator. Additionally, the paper establishes a theoretical guarantee for both algorithms and introduces the AFI Optimal Transport (AFI-OT) theorem, which provides a general condition for the optimal transport property of the PF-ODE mapping. The empirical results demonstrate the superior accuracy and reduced time-cost of the proposed methods compared to traditional methods like the Jacobian-vector-product (JVP).

## Strengths

1. **Novel and Innovative Approach**: The paper introduces a novel, gradient-free method for calculating the Fisher Information in diffusion models, which is a significant departure from current practices that rely on auto-differentiation. The analytical formulation of the Fisher Information (AFI) leverages the inherent structure of diffused distributions, providing a more efficient and theoretically sound approach.

2. **Comprehensive Theoretical Analysis**: The paper provides a rigorous theoretical analysis of the proposed methods, including convergence analysis and approximation error bounds. This is crucial for establishing the reliability and robustness of the proposed methods. The theoretical guarantees are supported by empirical results, which demonstrate the superior accuracy and reduced time-cost of the AFI methods.

3. **Practical Algorithms**: The paper proposes two practical algorithms, AFI-TM and AFI-EA, tailored to different scenarios. AFI-TM introduces a parameterized network to learn the trace of the Fisher Information, significantly reducing the time complexity from quadratic to linear with respect to the dimension. AFI-EA simplifies the application of Fisher Information as a linear operator into several inner-product calculations, making it training-free and more efficient for adjoint optimization tasks.

4. **Significant Theoretical Contribution**: The AFI-OT theorem is a significant theoretical contribution that provides a general condition for the optimal transport property of the PF-ODE mapping. This theorem eliminates the need for stringent assumptions and broadens the applicability of diffusion models in optimal transport tasks.

5. **Empirical Validation**: The paper includes a comprehensive empirical evaluation of the proposed methods, demonstrating their superior performance compared to traditional methods like JVP. The experiments cover a range of tasks, including likelihood evaluation and adjoint optimization, and use well-known datasets and models, such as the COCO dataset and Stable Diffusion models.

## Weaknesses

1. **Limited Ablation Studies**: The paper includes some ablation studies, but they are limited in scope and lack depth in analyzing the contributions of the different components of the AFI methods. For example, the paper does not provide an ablation study to evaluate the performance of different network architectures or training strategies for the scalar network used in AFI-TM. Additionally, the impact of the endpoint approximation in AFI-EA is not fully explored.

2. **Lack of Empirical Validation for AFI-OT Theorem**: The AFI-OT theorem is a strong theoretical contribution, but it is not empirically validated. The paper does not include a small-scale experiment to verify the OT property using the AFI-OT condition. Including such an experiment would strengthen the theoretical claim and provide a clearer link between the AFI formulation and the OT property.

3. **Insufficient Details on Implementation**: The paper lacks detailed descriptions of the datasets, models, and implementation settings. For example, the specific subset of the COCO dataset used, the model architectures, the noise schedules, and the training settings are not fully described. Including these details would improve reproducibility and clarity.

4. **Limited Comparison with Other Methods**: The paper primarily compares the proposed methods with the JVP method. However, it does not provide a comparison with other likelihood estimation methods or adjoint optimization techniques. Including such comparisons would better contextualize the performance of the proposed methods.

5. **Potential Over-reliance on Aesthetic Score**: The paper uses aesthetic score as a proxy for the quality of the generated images in the adjoint optimization experiments. While this is a reasonable metric for subjective image quality, it is not a standard or widely accepted metric in the diffusion literature. The paper should also include objective metrics such as FID (Fréchet Inception Distance) or IS (Inception Score) to provide a more comprehensive evaluation.

## Questions

1. **Reproducibility**: The paper mentions the use of specific datasets (e.g., COCO prompts) and models (e.g., SD-1.5 and SD-2base), but it does not provide detailed information about the data preprocessing steps or how the datasets were split for training and evaluation. Additionally, the paper does not mention whether the code for the experiments will be made publicly available. Could the authors provide more details on the data preprocessing steps, dataset splits, and code availability to ensure reproducibility?

2. **Network Architecture and Training**: The paper introduces a parameterized network to learn the trace of the Fisher Information in AFI-TM. However, it does not provide a detailed description of the network architecture, the training procedure, or the choice of hyperparameters. Could the authors provide more details on the network architecture, the optimizer, the learning rate, the batch size, and the training procedure used for the scalar network in AFI-TM?

3. **Endpoint Approximation**: The AFI-EA method is based on the endpoint approximation of the outer-product sum in the AFI formulation. The paper suggests that the sum can be approximated by a single outer-product $\Delta x_0 x_0^\top$, but it does not provide an ablation study to evaluate the impact of this approximation. Could the authors include an ablation study that compares the performance of AFI-EA with and without the endpoint approximation in terms of aesthetic score, computation time, and approximation error?

4. **Noise Schedule and Initial Data Dependency**: The AFI formulation is dependent on the noise schedule and the initial data distribution. However, the paper does not provide an ablation study to evaluate how different noise schedules (e.g., linear, cosine, exponential) affect the performance of the AFI methods. Could the authors include an ablation study on the noise schedule to evaluate the sensitivity of the AFI methods to different diffusion dynamics?

5. **Error Analysis and Theoretical Bounds**: The paper derives theoretical error bounds for the AFI-EA method (Proposition 8), but it does not provide a comprehensive empirical error analysis that validates these bounds. Could the authors include an empirical error analysis that compares the theoretical error bounds with the actual approximation errors observed in the experiments?

6. **Empirical Validation of AFI-OT Theorem**: The AFI-OT theorem is a significant theoretical contribution, but it is not empirically validated. Could the authors include a small-scale experiment to verify the OT property using the AFI-OT condition? For example, one could test whether the normalized fundamental matrix $B(t)$ is semi-positive definite for a range of $t$ values and initial conditions.

7. **Objective Metrics for Adjoint Optimization**: The paper uses aesthetic score as a proxy for the quality of the generated images in the adjoint optimization experiments. However, this is not a standard or widely accepted metric in the diffusion literature. Could the authors include objective metrics such as FID (Fréchet Inception Distance) or IS (Inception Score) to provide a more comprehensive evaluation of the method's performance?

8. **Comparison with Other Methods**: The paper primarily compares the proposed methods with the JVP method. However, it does not provide a comparison with other likelihood estimation methods or adjoint optimization techniques. Could the authors include a comparison with other likelihood estimation methods in the AFI-TM experiments and other adjoint optimization techniques in the AFI-EA experiments to better contextualize the performance of the proposed methods?

RATING: 8