## Summary
The paper "Controlling Language and Diffusion Models by Transporting Activations" introduces a novel framework called Activation Transport (\method) to control the behavior of large generative models (GMs) by steering their activations. The approach is based on optimal transport theory and provides a general and interpretable way to induce or prevent the emergence of concepts or behaviors in the generated output. The authors demonstrate the effectiveness of \method on various tasks, including toxicity mitigation, concept induction, and truthfulness induction in large language models (LLMs), as well as fine-grained style control and concept negation in text-to-image diffusion models.

## Strengths
The paper has several strengths. Firstly, the proposed \method framework is general and can be applied to various GMs, including LLMs and text-to-image diffusion models. The approach is also interpretable, allowing for fine-grained control over the model's behavior through a bounded parameter $\lambda$. The authors provide a thorough evaluation of \method on several tasks, demonstrating its effectiveness and robustness. Additionally, the paper provides a clear and well-structured presentation of the methodology and results.

## Weaknesses
One potential weakness of the paper is the assumption of linear transport between i.i.d. activations, which may not always hold in practice. The authors acknowledge this limitation and plan to explore non-linear maps and joint activations distributions in future work. Another potential weakness is the reliance on samples to estimate the transport map, which may be limited by their expressiveness. However, the authors demonstrate that \method is effective even with a limited number of samples.

## Questions
Some questions that arise from this work include: (1) How can \method be extended to handle non-linear transport between activations? (2) Can \method be applied to other types of generative models, such as generative adversarial networks (GANs) or variational autoencoders (VAEs)? (3) How can the interpretability of \method be further improved, for example, by providing more insights into the transport map and its properties?

RATING: 9