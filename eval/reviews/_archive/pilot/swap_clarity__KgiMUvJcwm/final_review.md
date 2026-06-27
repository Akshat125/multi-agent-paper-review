## Summary

The paper introduces **IgSeek**, a novel framework for antibody design that leverages **structure retrieval** to infer **Complementarity-Determining Region (CDR) sequences**. Unlike traditional methods that rely on generative models for sequence inference, IgSeek uses a **multi-channel equivariant graph neural network (MEGNN)** to encode CDR backbone structures into fixed-length vectors. These vectors are then used to retrieve structurally similar CDRs from a database, and the sequences of these retrieved CDRs are ensembled to infer the target sequence. The authors demonstrate that IgSeek outperforms state-of-the-art methods in **sequence recovery accuracy (AAR)** and **inference speed**, and they also show its generalization to **T-Cell Receptor (TCR) CDRs**.

## Strengths

- **Novel retrieval-based approach**: IgSeek introduces a new paradigm for CDR sequence design by using **structural similarity** as a proxy for functional similarity, which is a well-established principle in structural biology. This is a significant departure from generative models that are prone to hallucinations.
- **High accuracy and efficiency**: The experiments show that IgSeek **outperforms existing methods** in terms of **sequence recovery rate (AAR)**, particularly on **light chain CDRs** and **TCRs**, and achieves a **20x speed-up** in inference compared to baseline models. This is a major practical advantage for high-throughput antibody design.
- **Theoretical guarantees**: The use of **E(3) equivariant neural networks** ensures that the model's learned representations are **invariant to 3D transformations**, which is a strong theoretical foundation for the model's generalization and robustness.
- **Generalization to TCRs**: The model is tested on **TCR CDRs** from the **STCRDab dataset**, where it **outperforms all competitors by at least 30%**. This suggests that the approach is **not limited to antibodies** and could be **applied to other hyper-variable protein regions**.
- **Comprehensive evaluation**: The paper evaluates IgSeek on **multiple datasets**, including **SAbDab**, **STCRDab**, and **OAS-H3**, and includes a **case study** (PDB 8W8R CDR-L1) to demonstrate the model's effectiveness in a real-world setting.

## Weaknesses

- **Limited ablation studies**: The ablation study is **minimal**, focusing only on the **RMSD-based refinement (IgSeek⁺)**. The paper does **not perform ablations on the MEGNN architecture**, such as the **number of layers**, the **use of multi-channel equivariance**, or the **impact of coordinate perturbation**. This makes it **difficult to assess the contribution of individual components** to the model's performance.
- **Need for more detailed baseline comparisons**: The paper compares IgSeek with **state-of-the-art models** like **AbMPNN**, **AntiFold**, and **FoldSeek**, but it **does not clarify whether these models were run in the same setting** (i.e., only CDR structure as input, no framework sequence). This is **critical for a fair comparison**, as the paper notes that **AntiFold and AbMPNN depend on framework sequences**, which are **not provided in the current setup**.
- **Lack of hallucination rate evaluation**: The paper claims that IgSeek **reduces hallucinations** in sequence inference, but the **evaluation of this claim is limited to AAR and case studies**. A **direct evaluation of hallucination rates** (e.g., by using a folding model to assess whether the predicted sequences fold into the correct structure) would **strengthen this claim**.
- **Need for more detailed test set description**: The **SAbDab-2024** and **STCRDab** test sets are used to evaluate the model, but the **paper does not provide a detailed breakdown** of these datasets in terms of **CDR types, lengths, or filtering criteria**. This **limits the ability to assess the model's performance** across different structural challenges.
- **Need for a naive baseline**: The paper **does not include a simple baseline** (e.g., random sampling from the database) to **contextualize the performance gains** of IgSeek. This would help **better understand the model's contribution** to the field.

## Questions

- What is the **impact of the multi-channel equivariant design** on the model's performance compared to a **single-channel EGNN**? A **direct comparison** would help clarify this.
- How is the **K-NN search implemented** in the CDR vector database? The paper **does not specify the indexing method** (e.g., FAISS, Annoy) or the **distance metric used** (e.g., cosine similarity, Euclidean distance).
- What is the **role of the Kabsch algorithm** in the **IgSeek⁺ variant**? The paper **does not provide a detailed explanation** of how this algorithm is integrated into the model.
- How does the model **handle CDRs of different lengths** in real-world applications? The paper **only considers CDRs of equal length** in the retrieval process, but it is **unclear how the model would handle varying lengths**.
- What is the **effect of structural deviations** in the database on the **retrieval process**? The paper notes that **state-of-the-art models have structural deviations of 1–3 Å in CDRs**, but it is **not discussed how such deviations affect the retrieval-based approach**.

RATING: 8