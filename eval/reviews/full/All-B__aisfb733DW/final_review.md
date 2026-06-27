### Current Task: Produce a complete, well-structured peer review of the scientific paper provided below.

Consult all three expert co-workers (Clarity and Reproducibility Reviewer, Experiments and Methodology Reviewer, Impact and Contribution Reviewer) before writing the review: delegate at least one focused question to each (use their exact role name as the ``coworker`` argument) so every area is covered by its specialist, and integrate their feedback. Run additional rounds only if a response is weak or unclear. They already have the full paper, so tell them what to focus on rather than sending paper text.

Then synthesise everything into a single final review using exactly these Markdown headers and no others:

## Summary
A concise, neutral summary of what the paper does.

## Strengths
The main strengths, grounded in specifics from the paper. Write in natural prose; use bullets only when they help readability.

## Weaknesses
The main weaknesses and concerns. Cover what matters for this paper—do not force a fixed number of points or mirror the expert roles one-to-one. Use paragraphs or bullets as appropriate; omit minor issues if they are not central.

## Questions
Concrete questions for the authors whose answers would change your assessment. Include only questions that matter; do not pad the list for symmetry.

After the Questions section, on its own line at the very end, write your overall score as:
RATING: <integer 1-10>

The RATING line must be the last line of my output. Do not add any text, explanation, or markdown after it.

Write the review in clear, professional prose like a human conference reviewer. Be specific and reference concrete details from the paper. Vary structure across sections as the content warrants.

PAPER:
\title{Gradient-Free Analytical Fisher Information of Diffused Distributions}

\begin{abstract}
Diffusion models (DMs) have demonstrated powerful distributional modeling capabilities by matching the first-order score of diffused distributions.
Recent advancements have explored incorporating the second-order Fisher information, defined as the negative Hessian of log-density, into various downstream tasks and theoretical analysis of DMs.
However, current practices often overlook the inherent structure of diffused distributions, accessing Fisher information via applying auto-differentiation to the learned score network.
This approach, while straightforward, leaves theoretical properties unexplored and is time-consuming.
In this paper, we derive the analytical formulation of Fisher information (AFI) by applying consecutive differentials to the diffused distributions.
As a result, AFI takes a gradient-free form of a weighted sum (or integral) of outer-products of the score and initial data.
Based on this formulation, we propose two algorithmic variants of AFI for distinct scenarios.
When evaluating the AFI’s trace, we introduce a parameterized network to learn the trace.
When AFI is applied as a linear operator, we present a training-free method that simplifies it into several inner-product calculations.
Furthermore, we provide theoretical guarantees for both algorithms regarding convergence analysis and approximation error bounds.
Additionally, we leverage AFI to establish the first general theorem for the optimal transport property of the diffusion ODE deduced map.
Experiments in likelihood evaluation and adjoint optimization demonstrate the superior accuracy and reduced time-cost of the proposed algorithms.
\end{abstract}

\section{1 INTRODUCTION  }

The emerging diffusion models (DMs) Sohl-Dickstein et al. (2015); Ho et al. (2020); Song & Ermon (2019); Song et al. (2020), generating samples of data distribution from initial noise by learning a reverse diffusion process, have been proven to be an effective technique for modeling data distribution, especially in generating high-quality images Nichol et al. (2022); Dhariwal & Nichol (2021a); Saharia et al. (2022); Ramesh et al. (2022); Rombach et al. (2022); Ho et al. (2022). The training process of DMs can be seen as employing a neural network to match the first-order score $\nabla_{\pmb{x}}\log q_{t}(\pmb{x})$ of the diffused distributions at varying noise levels.

Recently, there has been a growing trend to recognize the importance of the Fisher information in DMs, defined as the negative Hessian of the diffused distributions’ log-density, $-\nabla_{x}^{2}\log q_{t}(x)$ . The Fisher information provides valuable second-order information of DMs and plays a crucial role in likelihood evaluation (Lu et al., 2022a; Zheng et al., 2023), adjoint optimization (Pan et al., 2023a;b; Blasingame & Liu, 2024), and optimal transport analysis Zhang et al. (2024a).

However, current practices (Sanchez et al., 2022; Song & Lai, 2024) typically overlook the inherent structure of diffused distributions, and access the Fisher information by applying auto-differentiation to the score network. While this is a straightforward approach, it leads to time-consuming gradient operations, even with the help of the Jacobian-vector-product (JVP) technique. Moreover, in the likelihood evaluation task, the current JVP method still needs a quadratic order time complexity concerning the dimension to calculate the trace of the Fisher information, rendering likelihood evaluation intractable for SD-level models. Additionally, due to a lack of comprehensive understanding of Fisher Information, Zhang et al. (2024a) have to impose stringent assumptions to characterize the optimal transport property of the diffusion ODE deduced map.

In this paper, we delve deeper into the inherent quadratic structure of diffused distributions and derive the analytical form of Fisher information (AFI) by applying the consecutive partial differential chain rule to the marginal distributions. Notice that, while this inherent structure has been consistently utilized in the learning process of the score network, it has often been overlooked when accessing Fisher Information up until now. The main contributions of our paper are listed as follows:

• We develop the first analytical formulation of the Fisher Information (AFI) of diffused distributions, which is gradient-free. Initially, we show that the AFI manifests as a weighted summation of outer-products of the score and initial data when the initial distribution is a sum of Dirac. We then extend this result to an integral form in a more general setting. The AFI suggests a theoretical possibility of accessing Fisher information without needing costly gradient calculations in practice.

• Based on the AFI, we propose two algorithmic alternatives to the JVP, each tailored to different types of Fisher Information access. For the evaluation of Fisher information’s trace, we introduce a parameterized network to learn the trace, significantly reducing the time complexity of trace evaluation from quadratic to linear w.r.t. the dimension. In scenarios where Fisher Information is applied as a linear operator, we present a training-free method that simplifies the complex linear transformation calculations into several simple innerproduct calculations. Furthermore, we provide theoretical guarantees for these algorithms, including convergence analysis and approximation error bounds.

• Utilizing the analytical knowledge of the Fisher information, we establish the first theorem that allows the general diffusion ODE deduced mapping to possess the optimal transport property, eliminating the need for stringent assumptions.

We evaluate our AFI algorithms on likelihood evaluation and adjoint optimization tasks. The empirical results demonstrate the enhanced accuracy and reduced time-cost of our AFI methods.

\section{2 PRELIMINARIES  }

Notation. The Euclidean norm over $\mathbb{R}^{d}$ is denoted by $\left\Vert\cdot\right\Vert$ , and the Euclidean inner product is denoted by $\langle\cdot|\cdot\rangle$ . Throughout, we simply write $\emph{\textbf{\textit{\textbf{f}}}}\!\!\!\operatorname{\textbf{\textit{\textbf{\textmu}}}}$ to denote the integral with respect to the Lebesgue measure: $\textstyle\int g(x)\mathrm{d}x$ . When the integral is with respect to a different measure $\mu$ , we explicitly write $\int g\mathrm{d}\mu$ . When clear from context, we sometimes abuse notation by identifying a measure $\mu$ with its Lebesgue density. We also use $\delta(\cdot)$ to denote the Dirac Delta function.

2.1 DIFFUSION MODELS AND DIFFUSION SDES

Suppose that we have a ${\mathrm{d}}\cdot$ -dimensional random variable $\pmb{x}_{0}\ \in\ \mathbb{R}^{d}$ following an unknown target distribution $q_{0}(x_{0})$ . Diffusion Models (DMs) define a forward process $\{\boldsymbol{x}_{t}\}_{t\in[0,T]}$ with $T\ >\ 0$ starting with $\scriptstyle x_{0}$ , such that the distribution of $\pmb{x}_{t}$ conditioned on $\pmb{x}_{0}$ satisfies

$$
\begin{array}{r l}{\mathrm{(Diffusion~Transition~Kernel)}\quad}&{{}q_{t|0}(x_{t}|x_{0})=\mathcal{N}(x_{t};\alpha(t)x_{0},\sigma^{2}(t)\mathbf{I}),}\end{array}
$$

where $\alpha(\cdot),\sigma(\cdot)\in\mathcal{C}([0,T]\,,\mathbb{R}^{+})$ have bounded derivatives, and we denote them as $\alpha_{t}$ and $\sigma_{t}$ for simplicity. The choice for $\alpha_{t}$ and $\sigma_{t}$ is referred to as the noise schedule of a DM. According to Kingma et al. (2021); Karras et al. (2022), with some assumption on $\alpha(\cdot)$ and $\sigma(\cdot)$ , the forward process can be modeled as a linear SDE which is also called Ornstein–Uhlenbeck process:

$$
\begin{array}{r}{\mathrm{d}\pmb{x}_{t}=f(t)\pmb{x}_{t}\mathrm{d}t+g(t)\mathrm{d}B_{t},}\end{array}
$$

where $B_{t}$ is the standard d-dimensional Brownian Motion (BM), $\begin{array}{r}{f(t)=\frac{\mathrm{d}\log\alpha_{t}}{\mathrm{d}t}}\end{array}$ and $\begin{array}{r}{g^{2}(t)=\frac{\mathrm{d}\sigma_{t}^{2}}{\mathrm{d}t}\;-}\end{array}$ 2 d lodgt αtσt2 . Under some regularity conditions, the above forward SDE equation 2 have a reverse SDE from time $T$ to $0$ , which starts from $\pmb{x}_{t}$ Anderson (1982):

$$
\begin{array}{r}{\mathrm{d}\pmb{x}_{t}=\left[f(t)\pmb{x}_{t}-g^{2}(t)\nabla_{\pmb{x}_{t}}\log q(\pmb{x}_{t},t)\right]\mathrm{d}t+g(t)\mathrm{d}\tilde{B}_{t},}\end{array}
$$

where ${\tilde{B}}_{t}$ is the reverse-time Brownian motion and $\boldsymbol{q}(\boldsymbol{x}_{t},t)$ is the single-time marginal distribution of the forward process. In practice, DMs Ho et al. (2020); Song et al. (2020) use $\pmb{\varepsilon}_{\theta}(\pmb{x}_{t},t)$ to estimate $-\sigma(t)\nabla_{\pmb{x}_{t}}\log\overline{{q(\mathbf{x}_{t},t)}}$ and the parameter $\theta$ is optimized by the following objective:

$$
\theta^{*}=\arg\operatorname*{min}_{\theta}\mathbb{E}_{t}\left\{\lambda_{t}\mathbb{E}_{x_{0},x_{t}}\left[\|s_{\theta}(x_{t},t)-\nabla_{x_{t}}\log p(x_{t},t|x_{0},0)\|^{2}\right]\right\},
$$

where $s_{\theta}$ represents the parameterized score, i.e., $\begin{array}{r}{s_{\theta}(\mathbf{x}_{t},t)=-\frac{\varepsilon_{\theta}(\mathbf{x}_{t},t)}{\sigma_{t}}}\end{array}$ . This familiar parameterization is called $\epsilon$ -prediction. There are also $\textit{\textbf{y}}$ -prediction and $\pmb{v}$ -prediction Salimans & Ho (2022). The corresponding loss is equal to replace the term $\vert\epsilon\,-\,\pmb{\varepsilon}_{\theta}(\pmb{x}_{t},t)\vert$ with $\begin{array}{r}{\frac{\alpha_{t}}{\sigma_{t}}|\mathbf{x}_{0}\,-\,\bar{\pmb y}_{\theta}(\pmb x_{t},t)|}\end{array}$ and $\vert\alpha_{t}\epsilon-\sigma_{t}\mathbf{x}_{0}-v_{\theta}(x_{t},t)\vert$ . The learned $\boldsymbol{\varepsilon}_{\theta}(\boldsymbol{x}_{t},t)$ can be also transformed to a $\textit{\textbf{y}}$ -prediction form by y¯θ(xt, t) = xt−σtεθ(xt,t).

2.2 DIFFUSION MODELS INFERENCE AS NEURAL ODE

It is noted that the reverse diffusion SDE in equation 3 has an associated probability flow ODE (also called diffusion ODE), which is a deterministic process that shares the same single-time marginal distribution Song et al. (2020):

$$
\left(\mathrm{PF-ODE}\right)\;\;\;\;\;\;\mathrm{d}x_{t}=\left[f(t)x_{t}-\frac{1}{2}g^{2}(t)\nabla_{x_{t}}\log q_{t}({\boldsymbol{x}}_{t},t)\right]\mathrm{d}t.
$$

By replacing the score function in equation 5 with the noise predictor $\varepsilon_{\theta}$ , the inference process of DMs can be constructed by the following neural ODE:

$$
{\frac{\mathrm{d}\mathbf{}x_{t}}{\mathrm{d}t}}=h_{\theta}\left(x_{t},t\right):=f(t)\mathbf{x}_{t}+{\frac{g^{2}(t)}{2\sigma_{t}}}\mathbf{\epsilon}_{\theta}\left(x_{t},t\right),\quad\mathbf{x}_{T}\sim{\mathcal{N}}\left(\mathbf{0},\sigma_{T}^{2}I\right)
$$

2.3 FISHER INFORMATION IN DIFFUSION MODELS

The Fisher information matrix in DMs is defined as the negative Hessian of the marginal log-density function, which takes the following matrix-valued form Song et al. (2021); Song $\&$ Lai (2024):

$$
F_{t}(\mathbf{x}_{t},t):=-\frac{\partial^{2}}{\partial\mathbf{x}_{t}^{2}}\log q_{t}\left(\mathbf{x}_{t},t\right)
$$

The current technique typically approximately accesses to the Fisher information by accessing the scaled Jacobian matrix of the learned score estimator network $\varepsilon_{\theta}$ :

$$
\begin{array}{r l}&{F_{t}(x_{t},t)=-\frac{\partial}{\partial x_{t}}\left(\frac{\partial}{\partial x_{t}}\log p\left(x_{t},t\right)\right)}\\ &{\qquad\qquad\approx-\frac{\partial}{\partial x_{t}}\left(-\frac{\varepsilon_{\theta}\left(x_{t},t\right)}{\sigma_{t}}\right)=\frac{1}{\sigma_{t}}\frac{\partial\varepsilon_{\theta}\left(x_{t},t\right)}{\partial x_{t}}}\end{array}
$$

The full Fisher information matrix within DMs cannot be obtained due to dimensional constraints. For instance, the Stable Diffusion-1.5 model (Rombach et al., 2022) features a latent dimension of $d\,=\,4\,\times\,64\,\times\,64\,=\,16384$ , resulting in a Fisher matrix of $16384\,\times\,16384$ . Fortunately, for applications that only need to access the trace or multiplication of Fisher information, it is feasible to use Jacobian-vector-product (JVP) to access Fisher information. For any $d$ -dimensional vector $\pmb{v}$ , the approximation of $\pmb{v}$ left multiplied by $\pmb{F}_{t}(\pmb{x}_{t},t)$ using JVP is as follows:

$$
F_{t}(x_{t},t)v\approx\frac{1}{\sigma_{t}}\frac{\partial\varepsilon_{\theta}(x_{t},t)}{\partial x_{t}}v=\frac{1}{\sigma_{t}}\frac{\partial\left[\langle\varepsilon_{\theta}(x_{t},t)|v\rangle\right]}{\partial x_{t}}
$$

The JVP is a time-consuming process due to its requirement for gradient calculations within the neural network. In addition, empirical evidence from synthetic distributions, as demonstrated in Lu et al. (2022a), shows that the approximation results from the JVP significantly deviate from the true underlying Fisher information. To our knowledge, there is no theoretical guarantee that Fisher information can be accurately accessed through the JVP. Moreover, the JVP fails to provide any theoretical insight into the Fisher information of diffused distributions.

\section{3 ANALYTICAL FISHER INFORMATION  }

Accessing Fisher information via the JVP as shown in equation 9 is straightforward, but it does not take advantage of any inherent structure of the diffused distribution. In this section, we initially derive the analytical Fisher information (AFI) of diffused distribution under a simplified setting, where

we assume that the initial $q_{0}$ is a sum of Dirac. Subsequently, we extend the AFI to a more general setting. Importantly, the AFI obtained in both settings does not involve any gradient calculations and is expressed into the initial data distribution, thus enabling the derivation of novel algorithms. Several studies Lu et al. (2022a); Benton et al. (2024) have investigated a similar form, but have not expressed it in terms of the initial data distribution. Our formulation can also be derived from a transformation of their formula.4.

3.1 THE DIRAC SETTING

We start with a simple setting where we assume that the initial distribution is characterized as a sum of Dirac distributions composed of the set of samples in the dataset. If we suppose the dataset is denoted as $\{y_{i}\}_{i=0}^{N}$ , then the initial distribution follows

$$
\mathrm{(Dirac\;Setting)}\qquad q({\pmb x},t)|_{t=0}=\frac{1}{N}\sum_{i=0}^{N}\delta({\pmb x}-{\pmb y}_{i}),
$$

where exists a $0<\mathcal{D}_{y}<\infty$ such that $\|y_{i}\|\leq\mathcal{D}_{y}$ holds true for every $i$ . In this Dirac setting, we derive the following Analytical Fisher Information, which is a weighted outer-product sum devoid of gradients and composed solely of the initial distribution and the noise schedule.

Proposition 1. Defines $v_{i}(\pmb{x}_{t},t)$ as $\begin{array}{r}{\exp\biggl(-\frac{|\pmb{x}_{t}-\alpha_{t}\pmb{y}_{i}|^{2}}{2\sigma_{t}^{2}}\biggr)\in\mathbb{R}}\end{array}$ and $\begin{array}{r}{w_{i}(\mathbf{x}_{t},t)\;a s\;\frac{v_{i}(\mathbf{x}_{t},t)}{\sum_{j}v_{j}(\mathbf{x}_{t},t)}\in}\end{array}$ $\mathbb{R}_{}$ . If $q_{0}$ takes the form as in equation equation $I O$ , the Fisher information matrix of the diffused distribution $q_{t}$ for $t\in(0,1]$ can be analytically formulated as follows:

$$
F_{t}(\boldsymbol{x}_{t},t)=\frac{1}{\sigma_{t}^{2}}I-\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left[\sum_{i}w_{i}y_{i}y_{i}^{\top}-\left(\sum_{i}w_{i}y_{i}\right)\left(\sum_{i}w_{i}y_{i}\right)^{\top}\right]
$$

where we have simplified $w_{i}(\pmb{x}_{t},t)$ to $w_{i}$ , as it does not lead to any confusion.

We also find that the $\textstyle\sum_{i}w_{i}\pmb{y}_{i}$ component in equation 11 can be effectively approximated by the trained score network  in the form of $y$ -prediction, as demonstrated in the following proposition.

Proposition 2. Given the diffusion training loss in equation 4, and if q0 conforms to the form presented in equation $I O$ , then the optimal $\bar{\pmb{y}}_{\theta}(\pmb{x}_{t},t)$ can accurately estimate $\sum_{i}w_{i}\pmb{y}_{i}$ .

\section{3.2 THE GENERAL SETTING  }

We then begin to extend the AFI in equation 11 to a more general setting, where we only assume that the initial distribution $q_{0}$ is a measure on $\mathbb{R}^{d}$ with finite second momentum.

$$
\begin{array}{r l}{(\mathrm{General~Setting})\quad}&{{}q_{0}\in\mathcal{P}_{2}(\mathbb{R}^{d}).}\end{array}
$$

In this general setting, we derive the following Analytical Fisher Information, which is a weighted outer-product integral devoid of gradients.

Proposition 3. Let us define $v(\pmb{x}_{t},t,\pmb{y})$ as $\exp\left(-\frac{|\pmb{x}_{t}-\alpha_{t}\pmb{y}|^{2}}{2\sigma_{t}^{2}}\right)\;\in\;\mathbb{R}$ and $w(\pmb{x}_{t},t,\pmb{y})$ as $\begin{array}{r}{\frac{v\left(\pmb{x}_{t},t,\pmb{y}\right)}{\int_{\mathbb{R}^{d}}v\left(\pmb{x}_{t},t,\pmb{y}\right)\mathrm{d}q_{0}\left(\pmb{y}\right)}\in\mathbb{R}.}\end{array}$ If $q_{0}$ takes the form as in equation $^{12}$ , the Fisher information matrix of the diffused distribution $q_{t}$ for $t\in(0,1]$ can be analytically formulated as follows:

$$
(G e n e r a l\,A F I)\;\;\;F_{t}(x_{t},t)\!=\!{\frac{1}{\sigma_{t}^{2}}}{\cal I}\!-\!{\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}}\left[\int w(y)y y^{\top}\mathrm{d}q_{0}\!-\!\left(\int w(y)y\mathrm{d}q_{0}\right)\left(\int w(y)y\mathrm{d}q_{0}\right)^{\top}\right]
$$

We further ascertain that the $\begin{array}{r}{\int w(\pmb{y})y\mathrm{d}q_{0}(\pmb{y})}\end{array}$ component in equation 13 can be effectively approximated by the score network in the form of $y$ -prediction, as demonstrated in the following proposition.

Proposition 4. Given the diffusion loss in equation 4, and if $q_{0}$ conforms to the form in equation 12, then the optimal $\bar{\pmb{y}}_{\theta}(\pmb{x}_{t},t)$ can accurately estimate $\begin{array}{r}{\int w(\pmb{y})y\mathrm{d}q_{0}(\pmb{y})}\end{array}$ .

The derivation of the AFI under the general setting is akin to the sum in the Dirac setting but in an integral form. For the remainder of the paper, we will focus on developing our method based on the Dirac setting AFI. However, the same results can be naturally extended to the general setting.

\section{4 AFI TRACE MATCHING (AFI-TM) METHOD  }

The likelihood evaluation of DMs would require access to Fisher Information’s trace. In this section, we introduce a network to learn the trace, thus facilitating effective likelihood evaluation in DMs.

Log-Likelihood in DMs Log-likelihood is a classic and significant metric for probabilistic generative models, extensively utilized for comparison between samples or models Bengio et al. (2013); Theis et al. (2015). According to Chen et al. (2018); Song et al. (2021), The log-likelihood of samples generated by PF-ODE in equation 6 from DMs can be computed through a connection to continuous normalizing flows as follows:

$$
{\begin{array}{r l}&{{\cfrac{\partial\log q_{t}(\mathbf{x}_{t},t)}{\partial t}}=-\mathrm{tr}\left({\cfrac{\partial}{\partial x_{t}}}\left(f(t)\mathbf{x}_{t}-{\cfrac{1}{2}}g^{2}(t){\cfrac{\partial^{2}}{\partial x_{t}}}\log q_{t}(\mathbf{x}_{t},t)\right)\right)}\\ &{\qquad\qquad=-\mathrm{tr}\left(\left(f(t)I-{\cfrac{1}{2}}g^{2}(t){\cfrac{\partial^{2}}{\partial x_{t}}}\log q_{t}(\mathbf{x}_{t},t)\right)\right)}\\ &{\qquad\qquad=-f(t)d-{\cfrac{g^{2}(t)}{2}}\mathrm{tr}\left(F_{t}(\mathbf{x}_{t},t)\right)}\end{array}}
$$

where $\mathrm{{tr}}(\cdot)$ denotes the trace of a matrix, which is defined to be the sum of elements on the diagonal.

Log-Likelihood Evaluation via JVP The current technique is only capable of conducting backpropagation of scalar value to the neural network. Therefore, the JVP in equation 9 cannot directly calculate the trace of the Fisher information. The JVP must iterate through each dimension to compute the individual elements on the diagonal, and then sum them up as follows

$$
\left(\mathrm{JVP\;for\;trace}\right)\qquad\mathrm{tr}\left(F_{t}({x}_{t},t)\right)\approx\frac{1}{\sigma_{t}}\sum_{i=1}^{d}\frac{\partial\left[\left\langle\varepsilon_{\theta}({x}_{t},t)\middle|e^{(i)}\right\rangle\right]}{\partial x_{t}}.
$$

Evaluating the trace using the JVP method would be extremely time-consuming due to the curse of dimensionality. If the time-complexity of a single backpropagation is $O(d)$ , then the calculation in equation 15 would have a time-complexity of $\bar{O}(d^{2})$ . In practice, as demonstrated in Table 1, evaluating the trace of Fisher information on the SD-1.5 model would require half an hour, rendering it nearly infeasible.

Gradient-free Log-Likelihood Evaluation via AFI trace matching To overcome the limitations of the JVP method in evaluating the trace of the Fisher information, we propose to directly obtain its analytical form. Given the AFI in Proposition 1, we can also derive its trace in an analytical form of weighted norm sum, as highlighted in the following proposition:

Proposition 5. In the same context as Proposition $^{\,I}$ , the trace of the Fisher information matrix for the diffused distribution $q_{t}$ , where $t\in(0,1],$ , is given by:

$$
\operatorname{tr}\left(F_{t}(\pmb{x}_{t},t)\right)=\frac{d}{\sigma_{t}^{2}}-\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left[\sum_{i}w_{i}\|\pmb{y}_{i}\|^{2}-\left\|\sum_{i}w_{i}\pmb{y}_{i}\right\|^{2}\right]
$$

As demonstrated in Proposition 2, the $\left\|\sum_{i}w_{i}\pmb{y}_{i}\right\|^{2}$ can be directly estimated by $\|\bar{\pmb{y}}_{\theta}(\pmb{x}_{t},t)\|^{2}$ . Therefore, the only unknown element in equation 16 is $\sum_{i}w_{i}\big|\big|\pmb{\{y}}_{i}\big|\big|^{2}$ . Consequently, we suggest estimating this term using a scalar-valued neural network, as per the following training algorithm:

\section{5 AFI ENDPOINT APPROXIMATION (AFI-EA) METHOD  }

The adjoint optimization of DMs would require applying Fisher Information as a linear operator. In this section, we present a training-free method that simplifies the complex linear transformation calculations thus enabling faster and more accurate adjoint optimization.

Adjoint optimization sampling. Guided sampling techniques are extensively utilized in diffusion models to facilitate controllable generation. Recently, to address the inflexibility of commonly used classifier-based guidance (Dhariwal & Nichol, 2021b) and classifier-free guidance (Ho & Salimans, 2022), a series of training-free adjoint guidance methods have been investigated and explored (Pan et al., 2023a;b).

Consider optimizing a scalar-valued loss function $\mathcal{L}(\cdot):\mathbb{R}^{d}\mapsto\mathbb{R}$ , which takes $\scriptstyle x_{0}$ in the data space as input. Adjoint guidance is implemented by applying gradient descent on $\pmb{x}_{t}$ in the direction of ∂L(∂x0x(txt)). The essence of adjoint guidance is to use the gradient at t = 0 and follow the adjoint ODE (Pollini et al., 2018; Chen et al., 2018) to compute $\begin{array}{r}{\pmb{\lambda}_{t}:=\frac{\partial\mathcal{L}(\pmb{x}_{0}(\pmb{x}_{t}))}{\partial\pmb{x}_{t}}}\end{array}$ ∂L(x0(xt))for t > 0.

$$
{\frac{\mathrm{d}\lambda_{t}}{\mathrm{d}t}}=-{\frac{\partial h_{\theta}\left(x_{t},t\right)}{\partial x_{t}}}^{\top}\lambda_{t},\quad\lambda_{0}={\frac{\partial{\mathcal{L}}(x_{0})}{\partial x_{0}}}
$$

Adjoint ODE via JVP. Regardless of the ODE solver being used, it is necessary to compute the right-hand-side of equation 18, or equivalently, $\pmb{F}(\pmb{x}_{t},t)^{\top}\pmb{\lambda}_{t}$ . This computation can be interpreted as applying the Fisher information matrix as a linear operator to the adjoint state $\lambda_{t}$ , from a functional analysis perspective (Yosida, 2012). Current practices utilize the JVP technique to approximate this linear transformation operation as follows:

$$
{\mathrm{~/~for~Adjoint)}}\qquad\quad F({x_{t},t})^{\top}\lambda_{t}\approx{\frac{1}{\sigma_{t}}}{\frac{\partial\varepsilon_{\theta}\left(x_{t},t\right)^{\top}}{\partial x_{t}}}^{\top}\lambda_{t}\approx{\frac{1}{\sigma_{t}}}{\frac{\partial\left[\langle\varepsilon_{\theta}\left(x_{t},t\right)|\lambda_{t}\rangle\right]}{\partial x_{t}}}
$$

This process involves computationally intensive gradient operations on the neural network, and the approximation errors introduced by the JVP technique have no theoretical bound.

Adjoint ODE via AFI-EA. As previously discussed in Section 3, the AFI inherently doesn’t require gradients, suggesting that we could potentially apply the Fisher information as a linear operator in a gradient-free manner. The challenging part in equation 11 is $\textstyle\sum_{i}w_{i}{\pmb y}_{i}{\pmb y}_{i}^{\top}$ , which represents a weighted form of outer-products of data. Based on the definition of $w_{i}$ , the closest $\pmb{y}_{i}$ to $\pmb{x}_{0}$ will dominate as $t\,\rightarrow\,0$ . This makes it intuitive to replace this sum with a single final sample outerproduct $\mathbf{\Delta}x_{0}x_{0}^{\top}$ . It’s also important to note that the adjoint guidance itself needs to compute $\pmb{x}_{0}$ at each guidance step, eliminating the need for additional computation to obtain $\pmb{x}_{0}$ . Given that we utilize the endpoint sample $\pmb{x}_{0}$ , we refer to this approximation technique as AFI Endpoint Approximation (EA). The formulation for AFI-EA in adjoint ODE is as follows:

$$
\begin{array}{r l}&{\boldsymbol{F}(\boldsymbol{x}_{t},t)^{\top}\lambda_{t}\approx\left(\frac{1}{\sigma_{t}^{2}}\boldsymbol{I}-\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left(\sum_{i}w_{i}y_{i}y_{i}^{\top}-\bar{y}_{\theta}(\boldsymbol{x}_{t},t)\bar{y}_{\theta}(\boldsymbol{x}_{t},t)^{\top}\right)\right)^{\top}\lambda_{t}}\\ &{\qquad\qquad\approx\left(\frac{1}{\sigma_{t}^{2}}\boldsymbol{I}-\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left(\boldsymbol{x}_{0}\boldsymbol{x}_{0}^{\top}-\bar{y}_{\theta}(\boldsymbol{x}_{t},t)\bar{y}_{\theta}(\boldsymbol{x}_{t},t)^{\top}\right)\right)^{\top}\lambda_{t}}\\ &{\qquad\qquad=\frac{1}{\sigma_{t}^{2}}\lambda_{t}-\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left(\boldsymbol{x}_{0},\lambda_{t}\right)\boldsymbol{x}_{0}+\frac{\alpha_{t}^{2}}{\sigma_{t}^{4}}\left<\bar{y}_{\theta}(\boldsymbol{x}_{t},t),\lambda_{t}\right>\bar{y}_{\theta}(\boldsymbol{x}_{t},t)}\end{array}
$$

The AFI-EA approximation leads to a scalar-weighted combination of $\lambda_{t},x_{0}$ , and $\bar{\pmb{y}}_{\theta}(\pmb{x}_{t},t)$ , which importantly, does not involve any gradients. Additionally, we derive the theoretical approximation error bound of the AFI-EA in Proposition 8. To measure the accuracy of AFI-EA as a linear operator, we opt to use the Hilbert–Schmidt norm (Gohberg et al., 1990) for measurement, as follows:

Proposition 8. Assume that the approximation error on $\pmb{\varepsilon}_{\theta}(\pmb{x}_{t},t)$ is denoted as $\delta_{2}$ , the approximation error of the endpoint approximated Fisher linear operator, as referenced in 20, is at most  t3 $\frac{\alpha_{t}^{2}}{\sigma_{t}^{3}}\left(2\mathcal{D}_{y}^{2}+\sqrt{d}\delta_{2}\right)$ when measured in terms of the Hilbert–Schmidt norm.

Experiments on AFI-EA. As depicted in Figure 4, we conducted experiments comparing our AFI-EA and JVP methods in adjoint guidance sampling, using four different scores and two different base models. AFI-EA consistently achieves better scores due to its bounded approximation error. Furthermore, AFI-EA requires less processing time as it eliminates the need for time-consuming gradient operations. AFI-EA and JVP are compared under the same guidance scales and schemes across various numbers of steps.2.

As depicted in Figure 5, our AFI-EA consistently generates samples with higher aesthetic scores with a reduced time-cost compared to JVP. It’s worth noting that this enhancement in aesthetics results in final images that are more vibrant and smoother.2.

\section{6 THEOREM ON THE OT PROPERTY OF THE PF-ODE DEDUCED MAP  }

There is an increasing trend towards analyzing the probability modeling capabilities of DMs by interpreting them from an optimal transport perspective (Albergo et al., 2023; Chen et al., 2024).9. One of the central questions is whether the map deduced by the PF-ODE could represent an optimal transport. If so, how should we design the noise schedule, or what conditions should the data distribution meet? For a specific noise schedule where $f(t)\equiv0$ , Zhang et al. (2024a) demonstrates that having all data points lying on a single line is a sufficient condition for the map to represent an optimal transport.

In this section, we find out that the AFI, as derived in section 3, can contribute to the first equivalence condition for the OT property of PF-ODE deduced mapping under a general noise schedule. We refer to this theorem as the AFI Optimal Transport (AFI-OT) theorem. The AFI-OT condition is presented in the following:

Theorem 1. Denote the diffeomorphism deduced by the PF-ODE 5 as follows

$$
T_{s,t}:\mathbb{R}^{n}\longrightarrow\mathbb{R}^{n};\mathbf{x}_{s}\longmapsto x_{t},\quad\forall t\geq s>0.
$$

This diffeomorphism is well-posed guaranteed by the global version of Picard-Lindel¨of theorem Amann (2011); Zhang et al. (2024a). The diffeomorphism $T_{s,T}$ is a Monge optimal transport map if and only if the normalized fundamental matrix for $B(t)\equiv B(t,{\pmb x}_{t})$ at $\boldsymbol{s}$ is semi-positive definite for every $P F$ -ODE chain start from a $\pmb{x}_{T}\in\mathbb{R}^{d}$ . where

$$
B(t,x_{t})=\left[f(t)-\frac{g^{2}(t)}{2\sigma_{t}^{2}}\right]I+\frac{\alpha_{t}^{2}g^{2}(t)}{2\sigma_{t}^{4}}\left[\sum_{i}w_{i}y_{i}y_{i}^{\top}-\left(\sum_{i}w_{i}y_{i}\right)\left(\sum_{i}w_{i}y_{i}\right)^{\top}\right].
$$

The outline of the proof is as follows: We first apply Brenier’s theorem (Brenier, 1991; Santambrogio, 2015) to convert the problem of whether the PF-ODE mapping is an optimal transport into the task of finding a convex potential, where the existence is guaranteed by the Poincare´’s Theorem (Lang, 2012). We then use adjoint methods to express the second derivatives of the convex potential function in the form of an integral of information Rockafellar (2015); Pollini et al. (2018). Finally, we apply matrix exponential integration theory Masuyama (2016) to reformulate the condition into the AFI-OT theorem.10.

\section{7 CONCLUSIONS  }

This paper introduced the Analytical Fisher Information (AFI), an analytical formulation that allows for more efficient and theoretical exploration of Fisher Information of diffused distribution. Practically, we have proposed two algorithmic variants of AFI for different scenarios: AFI trace matching (AFI-TM) and AFI endpoint approximation (AFI-EA). Both methods are gradient-free, theoretically guaranteed for approximation error bounds and convergence properties, and offer improved accuracy and reduced time-cost compared to the traditional JVP method. Theoretically, we have established the first general theorem for the PF-ODE map to be optimal transport. This work not only improves the efficiency of Fisher Information evaluation but also widens our understanding of the diffused distributions.

## Summary

The paper titled "Gradient-Free Analytical Fisher Information of Diffused Distributions" introduces a novel approach to calculating the Fisher Information of diffused distributions in a gradient-free manner. The authors derive an analytical formulation of Fisher Information (AFI) by leveraging the inherent structure of diffused distributions, which avoids the need for costly gradient calculations. Based on this formulation, they propose two algorithmic variants: AFI-TM (Trace Matching) and AFI-EA (Endpoint Approximation). The paper also provides theoretical guarantees for these algorithms and establishes a general theorem for the optimal transport property of the diffusion ODE deduced map. Experimental results demonstrate the superior accuracy and reduced time-cost of the proposed methods compared to the traditional Jacobian-vector-product (JVP) method.

## Strengths

- **Novel Analytical Formulation:** The paper presents the first analytical formulation of Fisher Information (AFI) for diffused distributions, which is gradient-free. This is a significant departure from current practices that rely on auto-differentiation of the score network.

- **Algorithmic Variants:** The authors propose two algorithmic variants of AFI:
  - **AFI-TM (Trace Matching):** A parameterized network to learn the trace of the Fisher Information, reducing time complexity from quadratic to linear.
  - **AFI-EA (Endpoint Approximation):** A training-free method that simplifies complex linear transformation calculations into inner-product calculations.

- **Theoretical Guarantees:** The paper provides convergence analysis and approximation error bounds for both algorithms, ensuring their reliability and robustness.

- **Optimal Transport Theorem:** The authors establish the first general theorem for the optimal transport property of the diffusion ODE deduced map, eliminating the need for stringent assumptions.

- **Experimental Validation:** The paper includes experimental results on likelihood evaluation and adjoint optimization tasks, demonstrating the enhanced accuracy and reduced time-cost of the proposed methods compared to the traditional JVP method.

## Weaknesses

- **Assumptions:** The paper makes several assumptions, such as the initial distribution being a sum of Dirac or having finite second momentum. It would be helpful to discuss the validity and limitations of these assumptions in real-world scenarios.

- **Generalization to Other Models:** While the paper focuses on diffusion models, it would be interesting to explore whether the AFI formulation can be extended to other types of generative models.

- **Computational Complexity:** Although the paper mentions reduced time complexity, a more detailed comparison with existing methods in terms of computational resources (e.g., memory, GPU usage) would be beneficial.

- **Experimental Validation:** The paper presents experimental results on likelihood evaluation and adjoint optimization. It would be valuable to include additional experiments or case studies to further validate the proposed methods.

## Questions

- **Assumptions:** How do the assumptions made in the paper (e.g., initial distribution being a sum of Dirac or having finite second momentum) affect the applicability of the proposed methods in real-world scenarios?

- **Generalization:** Can the AFI formulation be extended to other types of generative models beyond diffusion models? If so, what modifications would be necessary?

- **Computational Complexity:** Could the authors provide a more detailed comparison of the computational complexity of the proposed methods with existing methods, including memory and GPU usage?

- **Additional Experiments:** Are there any additional experiments or case studies that could further validate the proposed methods, such as testing on different datasets or comparing with other gradient-free methods?

RATING: 8