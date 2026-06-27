### Summary

The paper titled "UNSURE: Unknown Noise level Stein's Unbiased Risk Estimator" introduces a novel approach based on Stein's Unbiased Risk Estimator (SURE) that does not require prior knowledge of the noise level. The authors present a theoretical framework that characterizes the robustness-expressivity trade-off in self-supervised learning methods and propose UNSURE as a solution that lies between the extremes of SURE and cross-validation methods. The paper includes theoretical analysis, generalizations to various noise distributions, and extensive experiments demonstrating the state-of-the-art performance of UNSURE in various imaging inverse problems.

### Strengths

- **Theoretical Framework:** The paper presents a clear and well-articulated theoretical framework that categorizes different self-supervised learning methods based on the constraints imposed on the derivatives of the estimator. This framework provides a comprehensive understanding of the robustness-expressivity trade-off.
- **Novel Method:** The proposed UNSURE method is a significant contribution to the field. It addresses a critical limitation of existing SURE-based methods by not requiring full knowledge of the noise distribution. The method is well-motivated and the theoretical analysis is clear and convincing.
- **Generalizations:** The paper provides generalizations of UNSURE to various noise distributions, including spatially correlated Gaussian noise, Poisson-Gaussian noise, and certain noise distributions in the exponential family. This makes the method widely applicable to different scenarios.
- **Experimental Validation:** The experiments are well-designed and effectively demonstrate the performance of UNSURE. The use of different datasets and inverse problems provides a comprehensive evaluation of the method. The results show that UNSURE performs close to supervised learning and significantly outperforms other self-supervised methods.
- **Clear Writing and Presentation:** The paper is well-written and easy to understand. The figures and tables are clear and helpful, and the methodology is well-described, providing sufficient detail for reproducibility.

### Weaknesses

- **Technical Jargon:** While the paper is generally clear, some sections contain technical jargon that might be challenging for readers who are not familiar with the field. Additional explanations of technical terms and concepts could make the paper more accessible to a broader audience.
- **Consistency in Notation:** The paper uses a variety of mathematical notations, and while they are generally well-defined, there are instances where the notation could be more consistent. For example, the use of different symbols for the same concept (e.g., σ for noise level and σ for the covariance matrix) can be confusing.
- **Clarification of Assumptions:** Some assumptions, such as the independence of noise across pixels, are mentioned but not fully explained. Providing more details on these assumptions and their implications would help readers better understand the methodology and results.
- **Limitations Section:** The limitations section is concise but could benefit from more detailed discussion. The paper could provide more information on the limitations of the proposed method and potential future directions to address these limitations.

### Questions

- **Computational Complexity:** How does the computational complexity of UNSURE compare to existing methods, and what are the implications for real-world applications?
- **Performance in Specific Scenarios:** Are there any specific scenarios or noise distributions where UNSURE might not perform well, and how can these limitations be addressed?
- **Extensions to Other Data Types:** What are the potential extensions of UNSURE to other types of data or learning tasks beyond imaging?
- **Robustness to Different Noise Levels:** How robust is UNSURE to different noise levels, and are there any specific noise levels where the method might not perform optimally?
- **Comparison with Other Methods:** Are there any other methods that could be compared with UNSURE to provide a more comprehensive evaluation of its performance?

RATING: 8