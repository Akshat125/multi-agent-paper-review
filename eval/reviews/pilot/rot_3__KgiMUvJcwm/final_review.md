## Summary

The paper "IgSeek: Fast and Accurate Antibody Design via Structure Retrieval" introduces a novel structure-retrieval framework for antibody design, specifically targeting the challenges of sequence inference in hyper-variable structures like antibody Complementarity-Determining Regions (CDRs). The authors propose IgSeek, which leverages a database of natural antibody structures to infer CDR sequences by retrieving structurally similar CDRs and using their sequences to predict the most likely sequence for a given CDR backbone. The framework employs a Multi-channel Equivariant Graph Neural Network (MEGNN) to generate high-quality geometric representations of CDR backbone structures, which are then used for efficient and accurate structure retrieval. The paper demonstrates that IgSeek outperforms state-of-the-art methods in terms of sequence recovery and inference speed, making it a promising tool for therapeutic protein design.

## Strengths

1. **Novel Retrieval-Based Approach**: IgSeek introduces a new paradigm for antibody design by using a retrieval-based method instead of traditional generative models. This approach reduces the risk of hallucinations in sequence inference, which is a common issue with generative models.

2. **Multi-Channel Equivariant Graph Neural Network (MEGNN)**: The MEGNN encoder is a significant innovation, as it generates high-quality geometric representations of CDR backbone structures. The model's E(3) equivariance and invariance properties make it well-suited for geometric learning tasks in protein structures.

3. **Improved Performance**: The experimental results show that IgSeek outperforms state-of-the-art models in terms of average amino acid recovery (AAR) on both the SAbDab-2024 and STCRDab datasets. It also achieves a 20x speed-up in inference time compared to baseline methods, which is a significant practical advantage.

4. **Generalization to T-Cell Receptors (TCRs)**: The authors demonstrate that IgSeek can generalize to TCRs, which are structurally and functionally similar to antibodies. This suggests that the framework may be applicable to a broader class of immunological proteins, increasing its potential impact.

5. **Comprehensive Experimental Design**: The paper includes a range of experiments to evaluate the performance of IgSeek, including comparisons with state-of-the-art methods, ablations, and a case study. The use of multiple datasets and evaluation metrics provides a thorough assessment of the method's effectiveness.

## Weaknesses

1. **Lack of Detailed Information on Hyperparameters**: The paper does not provide detailed information about the hyperparameters used in the experiments, which could affect the reproducibility of the results. Including specific values and the process of selecting these values would be helpful.

2. **Limited Biological Validation**: While the paper reports AAR as a metric for sequence recovery, it does not mention whether the predicted sequences were experimentally validated for their ability to fold into the correct structures or bind to the intended antigens. This is an important aspect to consider for real-world applications.

3. **Handling of Variable-Length CDRs**: The paper states that the K-NN search is performed on CDRs of equal length to the query, but it is unclear how the model generalizes to CDRs of different lengths. This is a critical question for real-world applications, where CDRs can vary in length.

4. **Database Composition**: The paper mentions that the CDR vector database is built using 24,479 solved CDR loops from SAbDab, but it does not provide a detailed description of the database's composition in terms of structural diversity, redundancy, and coverage of different CDR types. A more detailed description would help assess the robustness of the retrieval process.

5. **Alignment Strategy**: The paper describes using structurally similar CDRs to derive a probability distribution for each residue position, but it is not clear how the sequences are aligned. The method of alignment could significantly affect the accuracy of the ensemble prediction.

6. **Training Cost**: The paper discusses the model's inference speed and efficiency but does not provide information on the training time or resource requirements. This is important for assessing the practicality of the method in real-world settings.

7. **Interpretability**: The paper does not discuss the interpretability of the predicted sequences or the retrieval process. Understanding which structural features are most important for sequence inference could provide valuable insights for future design strategies.

## Questions

1. **What is the exact composition of the CDR vector database, and how was it curated in terms of structural diversity, redundancy, and coverage of different CDR types?**

2. **How does the model handle CDRs of different lengths, and is it limited to fixed-length CDRs?**

3. **What is the role of the RMSD-based sorting in IgSeek⁺Kabsch, and how is it integrated with the MEGNN embeddings?**

4. **How does the model perform on CDRs with novel or rare structures, and what is the biological validation of the predicted sequences?**

5. **What is the method of alignment used for the sequences, and how does it affect the accuracy of the ensemble prediction?**

6. **What is the computational cost of training the MEGNN model, and what are the resource requirements?**

7. **How does the model handle the high variability of CDR-H3, and what is the impact of the Gaussian noise perturbation in the MEGNN encoder?**

8. **What is the interpretability of the predicted sequences and the retrieval process, and which structural features are most important for sequence inference?**

RATING: 7