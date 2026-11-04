---
layout: post
title: "Certified Robustness: Proofs Instead of Benchmarks"
date: 2025-12-18
updated: 2026-11-04
category: "Defenses"
series_index: 8
read_time: "15 min read"
dek: "An adversarially trained CIFAR-10 model scores 78.7% clean and looks robust on a benchmark. Hand it to a verifier and it certifies 0% of test points at ε = 8/255. The gap between what we can measure and what we can prove is the subject of this post, with the numbers from both sides."
lead_figure: certified-imagenet
lead_caption: "Certified accuracy on ImageNet against the L2 radius being certified, for four generations of randomized smoothing. Plugging a pretrained diffusion model in as the denoiser lifted the small-radius numbers by fourteen points in 2023, but every method converges to the same low teens by r = 3. Data from [14, 16, 17]."
thumb: certified-thumb
tags: [defenses, certification, randomized-smoothing, verification]
---

CTBench, a 2025 benchmark that re-trained every major certified-training method under one careful recipe, contains a row that explains the whole field [1]. A seven-layer CNN trained with PGD adversarial training reaches 78.7% clean accuracy on CIFAR-10 at ε = 8/255, comfortably above every certifiably trained model in the table. Run a complete verifier on it, with a budget of a thousand seconds per image, and none of the first ten test points can be certified. The model's accuracy under a PGD attack is a benchmark number of the ordinary kind. Its *certified* robust accuracy is approximately zero.

Neither number is wrong. An empirical robust accuracy is an upper bound on the truth, because the attack you ran might not be the strongest one; the previous post in this series is a catalogue of defenses whose upper bounds collapsed when someone ran a better attack. A certificate is a lower bound: a proof that no perturbation within the stated radius can change the prediction, however it is constructed. The price of the lower bound is that it is far smaller, costs far more compute, and holds only for the threat model written on the certificate. This post is about how to get such a proof, and what it is worth.

## Complete verifiers: exact answers for small networks

The first tools came from formal methods, not machine learning. Reluplex [2], presented at CAV in 2017, extended the simplex algorithm with a lazy treatment of ReLU constraints so that an SMT solver could decide whether any input in a region produces a given output. The motivating system was ACAS Xu, a family of collision-avoidance networks for aircraft with a few hundred neurons. Tjeng, Xiao and Tedrake [3] reformulated the same question as a mixed-integer linear program, with one binary variable per unstable ReLU, and showed that tight pre-activation bounds make exact verification practical for MNIST and small CIFAR-10 networks. They also showed something uncomfortable: the dual bounds that earlier incomplete methods relied on were often very loose.

Modern complete verifiers are branch-and-bound procedures built on top of fast incomplete bounds. MN-BaB [4] uses multi-neuron relaxations to guide the branching; the α,β-CROWN family, a consistent top performer in the annual VNN-COMP competitions, combines bound propagation with cutting planes. "Complete" means the verifier will eventually return either a proof or a counterexample, given enough time. For the PGD-trained CNN above, a thousand seconds per image was not enough. For a certifiably trained model of the same size, the same verifier typically needs a fraction of a second, because training has made the network easy to verify. That difference is the whole idea of certified training.

## Incomplete verification and training for it

An incomplete verifier gives a sound but possibly loose answer quickly: it may say "cannot certify" for an input that is in fact robust, but it never certifies a non-robust one. Wong and Kolter [5] bounded the worst-case loss by the dual of a linear program over the convex outer hull of the ReLU network's reachable set, and, crucially, trained on that bound. The resulting networks had verified error of 46.11% at ε = 2/255 on CIFAR-10 and 78.22% at 8/255 [6, 8]. Small numbers, but the first non-trivial L∞ certificates on CIFAR-10 at all.

Interval bound propagation [6] replaced the linear program with interval arithmetic. Each layer maps a box of inputs to a box of outputs; the computation costs roughly two forward passes. On its own the bound is loose, but Gowal et al. found that with a long schedule ramping ε up from zero, networks learn to make their own intervals tight. IBP reached 67.96% verified error at 8/255 (73.52% without an auxiliary PGD loss) and produced the first non-vacuous certificate at ImageNet scale, on 64×64 images at ε = 1/255 [6]. CROWN [7] gave linear relaxations for general activations that are much tighter than intervals; CROWN-IBP [8] used IBP bounds on the forward pass and CROWN bounds on the backward pass to stabilise the early phase of training, landing at 66.94% verified error at 8/255 and 46.03% at 2/255, without the hundredfold slowdown of training on linear relaxations directly.

<div class="math"><div class="math-label">Interval bound propagation for one linear layer (Gowal et al. 2018)</div>centre: μ' = Wμ + b     radius: ρ' = |W| ρ     output box: [μ' − ρ', μ' + ρ']</div>

Here the field ran into what Jovanović and colleagues later named the paradox of certified training: tighter relaxations do not produce better certified models. The looser IBP bound is easier to optimise, and the optimisation landscape matters more than the tightness of the bound. CTBench measures the mechanism directly; certifiably trained networks have less fragmented loss surfaces and sparser activations than standard ones [1]. The methods that followed accepted the paradox and mixed IBP with something else rather than tightening it: SABR [9] propagates intervals through a small box around the adversarial example rather than the full ε-ball; TAPS [10] connects certified and adversarial training through the bound; Expressive Losses [11] takes convex combinations of the IBP and adversarial losses, which CTBench calls MTL-IBP.

## Where deterministic certification stands

The comparison that mattered most in this line came from a benchmark, not a method. CTBench [1] re-implemented IBP, CROWN-IBP, SABR, TAPS, STAPS and MTL-IBP with one architecture (a seven-layer CNN with batch norm), one schedule, one initialisation and one certification procedure, and found that most of the reported differences were tuning. At 8/255 on CIFAR-10, plain IBP certifies 35.28% and CROWN-IBP 32.59%; SABR, TAPS, STAPS and MTL-IBP all land between 35.1% and 35.4%. Five years of certified-training papers moved the frontier by about three points over IBP, and the published gaps between the newer methods were mostly artefacts.

{% include fig.html name="certified-linf" num="1" caption="Certified and clean accuracy of deterministic L∞ methods on CIFAR-10 at ε = 8/255. The first six bars are bound-propagation methods on small CNNs, which plateau near 35% certified and 50–54% clean. The last is a Lipschitz-constrained SortNet trained with 10 million diffusion-generated images, which currently holds the best deterministic number. Adversarially trained models of the same size reach 78.7% clean and effectively 0% certified. Data from [6, 8], [1, 12]." %}

The one thing that did move the frontier was data, as it did for adversarial training. Altstidl et al. [12] trained certified models on images generated by a diffusion model, and the result splits cleanly by architecture. Bound-propagation training (MTL-IBP) gained nothing from generated data. Lipschitz-certified architectures, which certify by construction from a margin and a bound on the network's Lipschitz constant, gained a lot: a SortNet went from 36.50% to 41.78% certified at 8/255 with 10 million generated images, and an LOT network from 64.39% to 69.05% under L2 at ε = 36/255. The gains saturate at around one million generated images regardless of model size, and the certified models show no robust overfitting at all, which is the opposite of what adversarial training does at scale. Generated-only training beat real-only training in every case they tested.

So the honest state of deterministic L∞ certification on CIFAR-10 at the standard budget is between 35% (bound propagation) and 42% (Lipschitz networks with generated data), at a clean accuracy of about 55%. Standard models score 95–98% clean on the same data. That is the cost of a proof, at least for now.

## Randomized smoothing

The second family gives up on the network's internals and certifies a different classifier instead. Lecuyer et al. [13] noticed that a classifier whose prediction is averaged over Gaussian input noise is, in the language of differential privacy, a Gaussian mechanism, and derived a robustness certificate from the DP guarantee. Cohen, Rosenfeld and Kolter [14] found the tight version. Define the smoothed classifier g(x) as the class most likely to be returned by the base classifier f on x plus Gaussian noise:

<div class="math"><div class="math-label">Randomized smoothing (Cohen, Rosenfeld &amp; Kolter 2019)</div>g(x) = argmax_c  Pr_{δ∼N(0,σ²I)} [ f(x + δ) = c ]     certified for all ‖x' − x‖₂ ≤ R,  R = (σ/2) · (Φ⁻¹(p_A) − Φ⁻¹(p_B))</div>

where p_A and p_B are the probabilities of the top two classes under the noise and Φ⁻¹ is the inverse Gaussian CDF. The proof is a Neyman–Pearson argument, and the paper shows no larger L2 region can be certified from class probabilities alone. In practice p_A is a lower confidence bound estimated from samples, p_B is set to 1 − p_A, and the radius is σ·Φ⁻¹(p_A) with a small failure probability α; Cohen's experiments use 100,000 samples and α = 0.001, which is why they call the result "approximate certified accuracy." Each certification took about 15 seconds per CIFAR-10 image and 110 seconds per ImageNet image in 2019.

The decisive advantage is scale. Smoothing works with any base classifier, including a ResNet-50 on full ImageNet, which no bound-propagation method could touch. On CIFAR-10 the smoothed ResNet-110 beat Wong and Kolter's convex-relaxation models at every radius, partly, Cohen et al. observed, because relaxation-based training over-regularises until many filters are identically zero [14].

{% include fig.html name="certified-waterfall" num="2" caption="Certified accuracy on CIFAR-10 as a function of the L2 radius for smoothed ResNet-110 classifiers trained with four noise levels. Small σ gives high accuracy at small radii and nothing beyond σ·Φ⁻¹(p_A); large σ certifies larger radii at a steep cost in accuracy even at r = 0. Data from [14], Appendix Table 3." %}

The cost is the σ trade-off visible in Figure 2, and it has a hidden component. Mohapatra et al. [15] showed that smoothing shrinks decision regions unevenly and produces severe class imbalance: at σ = 1.0 on CIFAR-10 the worst class is 20.8% accurate and the best 72.8%; at σ = 3.0 the worst class is at 1.2%. The mean certified radius over all samples peaks at σ = 0.5 and falls afterwards, because samples that are no longer classified correctly contribute a radius of zero.

## Scaling smoothing with better base classifiers

Almost all progress in smoothing between 2019 and 2023 came from improving the base classifier rather than the certificate, which was already tight. Salman et al. [16] attacked the smoothed soft classifier directly and trained adversarially on it; SmoothAdv added seven points on ImageNet at r = 0.5 and twelve on CIFAR-10 at r = 0.25. MACER, Consistency, SmoothMix and the others tabulated in [17] are variations on the same theme.

Carlini et al. [17] then made the training step disappear. Denoised smoothing had earlier proposed placing a denoiser in front of a standard classifier so that the classifier never sees noise. Replace the denoiser with an off-the-shelf 552-million-parameter diffusion model, which is after all a very good Gaussian denoiser, and the classifier with a frozen BEiT-large at 88.6% top-1, and with no training whatsoever the pipeline certifies 71.1% of ImageNet images at r = 0.5. That was fourteen points above the best prior method and thirty-eight above the original denoised smoothing. The paper is candid about where the gain lives: it is concentrated at small radii. At r = 3.0 the frozen pipeline certifies 13.1% against 23.4% for the best trained method, and on CIFAR-10 at r = 1.0 it trails SmoothAdv (32.1% against 38.3%) unless fine-tuned. The lead figure shows the pattern. Compute is the other cost: 1.5 seconds per forward pass per image on an A100, times ten thousand samples per certification.

## Where smoothing cannot go

Randomized smoothing certifies L2 balls, and the natural question is whether the same trick works for L∞, the threat model most of the empirical literature uses. Kumar et al. [18] proved that it does not, for any smoothing distribution with independent coordinates. The largest certifiable Lp radius scales as d^{−(1/2 − 1/p)}, which for p = ∞ is 1/√d. On ImageNet, where d ≈ 150,000, that means an L∞ certificate of about σ/388. Gaussian noise is already optimal up to constants, so there is no better distribution to find. The ARS paper [20], which certifies L∞ by converting to L2, reports ImageNet certificates at r∞ between 0.001 and 0.005, roughly a quarter to one and a third grey levels, which is the ceiling made concrete.

A second limit concerns making σ depend on the input, which seemed an obvious way to avoid the waterfall in Figure 2: use small σ where the classifier is confident and large σ where it is not. Súkeník, Kuvshinov and Günnemann [19] showed that earlier input-dependent certificates were simply invalid, and that a valid variance function must have vanishing semi-elasticity in high dimension. The curse of dimensionality returns from a different direction.

ARS [20] takes the most interesting recent route through these constraints. It re-reads smoothing as an f-DP Gaussian mechanism and uses DP's post-processing and adaptive-composition theorems to certify a two-step pipeline, a U-Net that masks irrelevant pixels followed by a smoothed classifier, with two Gaussian steps composing as μ = √(μ₁² + μ₂²). On benchmarks constructed to reward adaptivity the gains are large; on ImageNet the certified-accuracy gain is at most 1.6 points. The connection between certification and differential privacy that PixelDP opened in 2019 is, a decade on, still producing tools.

## What a certificate buys you

It is worth laying the two families side by side with a standard model, because the numbers are rarely put in one place.

| Model (CIFAR-10 unless stated) | Clean accuracy | Empirical robust accuracy | Certified accuracy | Threat model |
|---|---|---|---|---|
| Standard ViT-B/16 base classifier [17] | 97.9% | ≈ 0% | none | — |
| PGD adversarial training, CNN7 [1] | 78.7% | measured by attack only | ≈ 0% | L∞, 8/255 |
| MTL-IBP certified training, CNN7 [1] | 54.3% | — | 35.4% | L∞, 8/255 |
| SortNet + 10M generated images [12] | 54.75% | — | 41.78% | L∞, 8/255 |
| Diffusion denoised smoothing, ImageNet [17] | 82.8% | — | 71.1% | L2, r = 0.5 |

<p class="fig-caption">The empirical–certified gap in one table. The PGD model's robustness can only be measured by attack; its certified accuracy is what a complete verifier can prove with a thousand seconds per image. Clean accuracy for the smoothing row is the smoothed classifier's accuracy at r = 0.</p>

Three caveats belong on every certificate. First, it holds only inside the stated threat model: an L2 certificate of radius 0.5 says nothing about a rotation, a patch, or a perturbation of L∞ size 8/255, which has L2 norm up to about 1.7 on CIFAR-10. Second, smoothing certificates are probabilistic, with a failure rate α and a sampling cost that scales with the confidence you want, whereas bound-propagation certificates are deterministic; VNN-COMP scores only the latter, and the two should not be compared as if they were the same object. Third, certification currently has nothing to say about the threat models that dominate 2026, semantic perturbations of images and adversarial prompts to language models, beyond narrow results such as erasing tokens and re-checking a safety filter. For those, the adaptive-attack discipline of the previous post is still the only tool, and the next post is about what it finds.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Empirical robustness is an upper bound and a certificate is a lower bound. The same adversarially trained model can score 50% under attack and 0% under a verifier.</li>
<li>Deterministic L∞ certification on CIFAR-10 at 8/255 sits at 35–42% certified and about 55% clean. Most reported progress between 2018 and 2024 was tuning; generated data helped only Lipschitz architectures.</li>
<li>Randomized smoothing is tight, scales to ImageNet, and now certifies 71% at L2 radius 0.5 with no training, but it cannot certify meaningful L∞ radii in high dimension and its accuracy collapses as σ grows.</li>
<li>A certificate is a statement about a threat model. Read the threat model before reading the number.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Mao, Balauca, Vechev. <em>CTBench: A Library and Benchmark for Certified Training.</em> ICML 2025. <a href="https://proceedings.mlr.press/v267/mao25a.html">PMLR 267</a></li>
<li>Katz, Barrett, Dill, Julian, Kochenderfer. <em>Reluplex: An Efficient SMT Solver for Verifying Deep Neural Networks.</em> CAV 2017. <a href="https://arxiv.org/abs/1702.01135">arXiv:1702.01135</a></li>
<li>Tjeng, Xiao, Tedrake. <em>Evaluating Robustness of Neural Networks with Mixed Integer Programming.</em> ICLR 2019. <a href="https://arxiv.org/abs/1711.07356">arXiv:1711.07356</a></li>
<li>Ferrari, Müller, Jovanović, Vechev. <em>Complete Verification via Multi-Neuron Relaxation Guided Branch-and-Bound.</em> ICLR 2022. <a href="https://arxiv.org/abs/2205.00263">arXiv:2205.00263</a></li>
<li>Wong, Kolter. <em>Provable Defenses against Adversarial Examples via the Convex Outer Adversarial Polytope.</em> ICML 2018. <a href="https://arxiv.org/abs/1711.00851">arXiv:1711.00851</a></li>
<li>Gowal, Dvijotham, Stanforth et al. <em>On the Effectiveness of Interval Bound Propagation for Training Verifiably Robust Models.</em> arXiv 2018. <a href="https://arxiv.org/abs/1810.12715">arXiv:1810.12715</a></li>
<li>Zhang, Weng, Chen, Hsieh, Daniel. <em>Efficient Neural Network Robustness Certification with General Activation Functions.</em> NeurIPS 2018. <a href="https://arxiv.org/abs/1811.00866">arXiv:1811.00866</a></li>
<li>Zhang, Chen, Xiao et al. <em>Towards Stable and Efficient Training of Verifiably Robust Neural Networks.</em> ICLR 2020. <a href="https://arxiv.org/abs/1906.06316">arXiv:1906.06316</a></li>
<li>Müller, Eckert, Fischer, Vechev. <em>Certified Training: Small Boxes are All You Need.</em> ICLR 2023. <a href="https://arxiv.org/abs/2210.04871">arXiv:2210.04871</a></li>
<li>Mao, Müller, Fischer, Vechev. <em>Connecting Certified and Adversarial Training.</em> NeurIPS 2023. <a href="https://arxiv.org/abs/2305.04574">arXiv:2305.04574</a></li>
<li>De Palma, Bunel, Dvijotham, Kumar, Stanforth, Lomuscio. <em>Expressive Losses for Verified Robustness via Convex Combinations.</em> ICLR 2024. <a href="https://arxiv.org/abs/2305.13991">arXiv:2305.13991</a></li>
<li>Altstidl, Dobre, Kosmala, Eskofier, Gidel, Schwinn. <em>On the Scalability of Certified Adversarial Robustness with Generated Data.</em> NeurIPS 2024. <a href="https://proceedings.neurips.cc/paper_files/paper/2024/hash/b96ce7d38339874a8704e8895f743284-Abstract.html">NeurIPS proceedings</a></li>
<li>Lecuyer, Atlidakis, Geambasu, Hsu, Jana. <em>Certified Robustness to Adversarial Examples with Differential Privacy.</em> IEEE S&amp;P 2019. <a href="https://arxiv.org/abs/1802.03471">arXiv:1802.03471</a></li>
<li>Cohen, Rosenfeld, Kolter. <em>Certified Adversarial Robustness via Randomized Smoothing.</em> ICML 2019. <a href="https://arxiv.org/abs/1902.02918">arXiv:1902.02918</a></li>
<li>Mohapatra, Ko, Weng, Chen, Liu, Daniel. <em>Hidden Cost of Randomized Smoothing.</em> AISTATS 2021. <a href="https://arxiv.org/abs/2003.01249">arXiv:2003.01249</a></li>
<li>Salman, Li, Razenshteyn et al. <em>Provably Robust Deep Learning via Adversarially Trained Smoothed Classifiers.</em> NeurIPS 2019. <a href="https://arxiv.org/abs/1906.04584">arXiv:1906.04584</a></li>
<li>Carlini, Tramèr, Dvijotham, Rice, Sun, Kolter. <em>(Certified!!) Adversarial Robustness for Free!</em> ICLR 2023. <a href="https://arxiv.org/abs/2206.10550">arXiv:2206.10550</a></li>
<li>Kumar, Levine, Goldstein, Feizi. <em>Curse of Dimensionality on Randomized Smoothing for Certifiable Robustness.</em> ICML 2020. <a href="https://arxiv.org/abs/2002.03239">arXiv:2002.03239</a></li>
<li>Súkeník, Kuvshinov, Günnemann. <em>Intriguing Properties of Input-dependent Randomized Smoothing.</em> ICML 2022. <a href="https://arxiv.org/abs/2110.05365">arXiv:2110.05365</a></li>
<li>Lyu, Shaikh, Shpilevskiy, Shelhamer, Lécuyer. <em>Adaptive Randomized Smoothing: Certified Adversarial Robustness for Multi-Step Defences.</em> NeurIPS 2024. <a href="https://proceedings.neurips.cc/paper_files/paper/2024/hash/f1e7c90552850afcc2558d78950c519d-Abstract.html">NeurIPS proceedings</a></li>
</ol>
</section>
