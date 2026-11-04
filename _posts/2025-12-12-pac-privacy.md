---
layout: post
title: "PAC Privacy: Measuring Leakage Instead of Assuming the Worst Case"
date: 2025-12-12
updated: 2026-11-04
category: "Privacy"
series_index: 7
read_time: "15 min read"
dek: "Differential privacy calibrates noise to the worst input a mechanism could ever see. PAC Privacy, introduced by Xiao and Devadas at CRYPTO 2023, calibrates it to how much the output actually moves, and on a 3,072-dimensional mean estimate that cuts the noise 63-fold. The price is a different, and more fragile, kind of guarantee."
lead_figure: pac-mi-success
lead_caption: "The central object in PAC Privacy is a bound on mutual information between the data and the released output. Given a budget β, this is the best any adversary can do at membership inference, whatever their computational power. A 50% prior is already at 84% success by β = 1/4, which is why practical budgets sit at 2⁻⁶ and below. The dashed lines mark the DP budgets ε that Sridhar et al. matched to each β for their comparisons. Data from [1], Tables 1 and 2."
thumb: pac-thumb
tags: [privacy, PAC-privacy, differential-privacy, mutual-information]
---

Every differentially private mechanism begins with the same question: what is the most that one record could change the answer? That quantity, the sensitivity, decides the noise [2]. For a count it is one. For a mean of bounded vectors it is the diameter of the domain divided by n. For the gradient of a neural network it is whatever you clip it to, which is why DP-SGD clips [3]. The noise then has to be large enough to hide that worst case on every input the mechanism could ever receive, including inputs that no real dataset resembles.

In the paper that introduced PAC Privacy [4], Hanshen Xiao and Srinivas Devadas asked what happens if you measure instead. Take the mechanism as a black box, run it on many plausible datasets, watch how far its output moves, and add noise shaped to that movement. On a 3,072-dimensional CIFAR-10 mean estimate, the worst-case Gaussian mechanism needs noise of expected norm 17.7 to limit leakage to one nat of mutual information; the measured, anisotropic version needs 0.28 [4]. Same leakage bound, 63 times less noise.

That number is the reason the framework attracted attention. The rest of this post is about what the guarantee actually says, how it is computed, where it beats differential privacy, where it loses, and why some cryptographers remain unconvinced.

## A definition in terms of what the attacker achieves

The DP definition is about distributions: on any two neighbouring datasets, the output distributions must be within a factor e^ε of each other. It says nothing about any particular attack; it says every attack is bounded. PAC Privacy starts at the other end, with a specific inference task and a specific data distribution.

<div class="math"><div class="math-label">(δ, ρ, 𝒟)-PAC Privacy (Xiao &amp; Devadas 2023)</div>A mechanism ℳ is (δ, ρ, 𝒟)-PAC private if, for data X ~ 𝒟, no adversary who knows 𝒟 and ℳ can output X̃ with ρ(X̃, X) = 1 with probability at least 1 − δ.</div>

Three things are new here. The data has a distribution 𝒟 rather than being an arbitrary fixed input. The adversary's goal is a predicate ρ chosen by the data holder: recover the record to within some ℓ₂ error, identify whether a particular person is in the set, recover a sensitive attribute within a margin. And the adversary is *unbounded*. It knows the distribution, knows the mechanism, has unlimited computation; the guarantee is information-theoretic, not computational [4, 5]. PAC Privacy is sometimes described as assuming a bounded, query-limited adversary. That is not the model, and the difference matters: a bound that holds against the full-knowledge adversary holds against every weaker one.

Why "PAC"? Because the guarantee is probabilistic over 𝒟 and the mechanism's randomness, approximate in the tolerance built into ρ, and, in practice, *measured by sampling* rather than derived by hand. The name is an explicit nod to learning theory, where the same three words describe what a learner can infer from finite data.

## The one theorem that matters

What makes the definition usable is that it reduces to a single quantity. Let δ_o be the adversary's success probability before seeing any output (their prior, which for membership inference with a random half is 50%) and δ their success after. Theorem 1 of [4] bounds the gain:

<div class="math"><div class="math-label">Posterior advantage is bounded by mutual information</div>Δ_KL(δ ‖ δ_o) ≤ MI(X; ℳ(X))          and, by Pinsker,          δ − δ_o ≤ √( MI(X; ℳ(X)) / 2 )</div>

So the whole problem becomes: bound the mutual information between the data and what you release. Theorem 2 of the same paper sharpens this for individuals under i.i.d. sampling, bounding the leakage about a single record by MI(xᵢ; ℳ(X)), which for symmetric mechanisms can be far smaller than the global quantity. In the paper's running example, a prior success of 1% rises to at most 36% under the global bound but at most 6% under the individual bound with n = 50 [4].

The lead figure turns this theorem into something you can read off. At β = 1 nat an adversary with a 50% prior can reach 100%; at β = 1/16 they are capped at 67.5%; at β = 1/128 at 56.2% [1]. For a rare attribute with a 1% prior the same budgets allow 35.7%, 6.2% and 2.5%. These are ceilings, not predictions. Sridhar et al. ran a thousand likelihood-ratio membership attacks [6] against privatised K-Means and SVMs on Iris and measured empirical advantages under 11% at budgets where the theorem permitted more; they call the bound "necessarily conservative" [1].

## Black-box privatisation: how the noise is computed

The practical algorithm is simple to state and is the part Xiao's thesis calls "automated and provable privatisation for black-box processing" [7]. You need a way to sample from 𝒟, and nothing else about the algorithm ℱ.

{% include fig.html name="pac-pipeline" num="1" caption="Black-box privatisation. Simulated datasets drawn from the data distribution are pushed through the algorithm, the spread of its outputs is estimated, and Gaussian noise is calibrated to that spread so the mutual information stays under the budget β. The algorithm itself needs no analysis. Redrawn from Algorithm 1 of [4] and the four-step template in [1]." %}

Algorithm 1 of [4] estimates the empirical covariance Σ̂ = UΛUᵀ of the m outputs, checks that the eigenvalue spectrum has usable gaps, and chooses anisotropic Gaussian noise with eigenvalues λ_B,j ∝ 1/√λ̂_j, so that ½ log det(I + Σ Σ_B⁻¹) ≤ β with confidence 1 − γ. The resulting noise has E‖B‖² = (Σ √λᵢ)², which scales with the *actual* spread of the output rather than with its dimension or worst-case sensitivity. When the output barely moves in most directions, as a well-regularised model's parameters do, the noise is O(1) where DP's is Θ(√d). When there is no eigengap, the algorithm falls back to isotropic noise calibrated from pairwise distances (Algorithm 2), which is dimension-free in its sample complexity but pessimistic: 3.94 instead of 0.28 on the CIFAR-10 example [4].

{% include fig.html name="pac-noise" num="2" caption="The headline comparison. Releasing the mean of a random half of CIFAR-10, with one nat of mutual information allowed, needs 63 times less noise when calibrated to the measured covariance than when calibrated to worst-case ℓ∞ sensitivity under zero-concentrated DP. The isotropic PAC variant sits in between. Data from [4], Section 6." %}

Covariance estimation in d dimensions costs O((d + log(1/γ))/c²) simulations, which for a model with millions of parameters is the main obstacle. The 2025 follow-up, *PAC-Private Algorithms* [1], replaces the full covariance with per-coordinate variances and proves that noise scaled as eᵢ ∝ √σᵢ / Σⱼ √σⱼ still achieves MI ≤ β. The estimator converges in about an order of magnitude fewer trials [8], and the paper's experiments use m = 1,024 subsets, arranged as 512 disjoint pairs so that every individual's membership prior is exactly one half [1].

Two details of the pipeline are easy to miss. First, outputs must be *canonicalised* before their spread is measured: cluster centroids are sorted, PCA bases are Procrustes-aligned, because an algorithm that returns the same answer in a permuted order has not leaked anything, yet looks wildly variable to a covariance estimate [1]. Second, the distribution 𝒟 is usually manufactured by subsampling the real dataset with probability one half. That changes what is being protected, from "this fixed dataset" to "membership in a random half of it", and it is the hinge on which the whole DP-versus-PAC argument turns.

## Stability is privacy

The most useful idea in the 2025 paper is the converse of the pipeline: if noise is calibrated to output variation, then anything that reduces output variation is a privacy amplifier. Regularisation does. An SVM with C = 10⁻⁶ on the Dry Bean dataset reaches 74% accuracy at a budget of 2⁻³ nats, where an SVM with C = 1 needs a budget of 4 to reach 68% [1]. Oversampling with SMOTE does: K-Means on Dry Bean goes from 73% to 85% unprivatised, and holds about 80% at 2⁻³ [1]. Convergence speed does: the strongly regularised SVM's variance estimate converges roughly a hundred times faster than the unregularised one [1].

This is the mirror image of the classical link between algorithmic stability and generalisation, and the thesis makes the connection explicit [7]. It also suggests a design discipline that the S&P 2026 paper, *Privacy-Conscious Algorithm Design* [9], follows to its conclusion: choose the algorithm's hyperparameters jointly with the privacy budget rather than adding noise afterwards. For ridge regression at β = 2⁻¹⁰ on the Red Wine dataset, post-hoc privatisation gives a mean squared error of 32.28, co-design gives 0.66, and the non-private model gives 0.39 [9]. The forty-fold gap is the cost of treating privacy as an afterthought.

## Where PAC Privacy loses

The same experiments report the cases that go the other way, and a post that only quoted the 63× number would be misleading. On mean estimation with a matched budget (β = 1/16, which the authors pair with ε = 0.73), the ℓ₂ errors were:

| Dataset (n) | DP | PAC, individual bound | PAC, global bound |
|---|---|---|---|
| Iris (100) | 0.021 | 0.030 | 0.066 |
| Rice (3,810) | 1.2 × 10⁻³ | 7.9 × 10⁻⁵ | 3.0 × 10⁻⁴ |
| Dry Bean (13,611) | 5.4 × 10⁻⁴ | 3.6 × 10⁻⁵ | 1.7 × 10⁻⁴ |

<p class="fig-caption">Mean-estimation error after privatisation at a matched budget. PAC Privacy is about ten times better on the two larger datasets and worse on the hundred-point one. Data from [1], Table 2.</p>

The pattern is the theory working as designed. PAC Privacy draws its guarantee from the entropy of the data; with a hundred points there is little entropy to exploit, and a worst-case bound is as good as a measured one. Three other failure modes are documented by the authors themselves. Unstable high-dimensional outputs stay hard: on CIFAR-10 PCA the reconstruction error at β = 2⁻⁷ reaches 300% once the number of components is three, and the required noise rises about a hundred-fold going from three components to four [1]. Isotropic fallback noise can inflate error by 2.5× [1]. And the simulation budget is a real cost: every one of those m = 1,024 trials is a full run of the algorithm being privatised, so "no need to retrain" is not an accurate description of the method, as an earlier version of this post claimed. You retrain a thousand times before you release once.

There is also a limitation the authors state plainly and that no experiment can remove. The guarantee is relative to 𝒟. If the real data are not distributed as the simulation assumed, or if the adversary holds side information outside 𝒟's model, the mutual-information bound is about the wrong random variable [4, 5]. Differential privacy's worst-case quantifier is exactly what makes it immune to that objection.

## Composition and the 2026 frontier

The original paper proved composition only in the simple, non-adaptive setting, and showed that analysing a joint release directly beats composing two separate bounds (4.57 versus 7.32 units of noise for two queries on a 100-patient hospital dataset) [4]. For adaptive adversaries, who choose the next query after seeing the last answer, Xiao's 2024 extension accumulated leakage quadratically or fell back to DP-style noise. In January 2026 Zhu, Sridhar and Devadas showed how to recalibrate the noise to the adversary's *current* posterior and proved linear accumulation of mutual information under adaptive queries, the first PAC analogue of DP's adaptive composition [10]. Their query-response system answers a million CIFAR-10 queries at 87.79% accuracy with per-step budget 2⁻³² and a membership-inference ceiling of 51.08%; a student distilled from 210,000 of those responses reaches 91.86% [10].

The result most likely to matter for practitioners is PACZero [11], which fine-tunes OPT-1.3B and OPT-6.7B with zeroth-order updates quantised to a single sign bit per step, chosen by majority vote across 128 data subsets. When the subsets agree unanimously, the step reveals nothing about any of them, and the authors report that 34–45% of steps on SST-2 are unanimous. At *zero* mutual information OPT-1.3B reaches 88.99% on SST-2 against 91.1% for the non-private MeZO baseline; the DP zeroth-order baseline DPZero collapses to chance for every ε below 1 [11].

{% include fig.html name="pac-llm" num="3" caption="Fine-tuning a 1.3B-parameter language model on SST-2. PACZero's sign-quantised updates leak nothing at all in the unanimous case and lose about two points to the non-private baseline; the DP zeroth-order baselines pay far more at comparable nominal budgets. The authors are explicit that the ε labels are reference points for comparison, not transferred guarantees. Data from [11]." %}

Other threads in the same programme: a CCS 2024 paper uses PAC mutual-information bounds to give the first formal privacy proofs for heuristic data encodings of the NeuraCrypt type, alongside an impossibility result for their computational security [12]; a CCS 2025 paper extends the machinery to one-sided bounded noise for side-channel and anonymous-messaging settings [13]; and third parties have begun to adopt it, with PAC-private diffusion models [14] and a PAC-enabled database system at Wisconsin [8].

## Where it sits among the relaxations of DP

PAC Privacy did not appear from nowhere. Cuff and Yu showed in 2016 that mutual-information DP, which bounds I(Xᵢ; Y | X₋ᵢ) ≤ ε over *all* distributions, sits strictly between pure and approximate DP [15]. Rényi DP relaxes the divergence [16]. PAC Privacy takes two further steps: it drops the supremum over distributions, fixing a 𝒟 instead, and it bounds an explicit inference-success probability rather than a divergence. In Xiao's own account, DP belongs to the tradition of *input-independent indistinguishability* descending from Goldwasser and Micali's 1982 definition of semantic security, and he argues that such indistinguishability "can only loosely imply" PAC Privacy, while admitting that worst-case sensitivity is NP-hard to compute for general pipelines and that the decompose-then-compose analysis of DP-SGD is loose [5]. He does not claim PAC is always tighter.

The nearest empirical relative is privacy auditing, the practice of estimating what an attacker actually achieves against a DP-trained model with canaries and membership tests [17]. Auditing measures a lower bound on leakage for one attack; PAC Privacy computes an upper bound for all attacks, under a distributional assumption. They are complementary, and the LiRA experiments in [1] are precisely an audit of a PAC guarantee.

## When to reach for which

The honest position is that neither framework dominates the other, and the people who built PAC Privacy say so [5, 11].

Reach for differential privacy when the adversary's side information is unknowable, when the data distribution cannot be sampled or trusted, when the release must compose with other releases you do not control, and when a guarantee needs to survive scrutiny from someone who does not believe your simulator. Its ε is a worst case over everything, which is why it is accepted in a census and why it is so expensive.

Reach for PAC Privacy when the algorithm is a black box nobody will analyse, when the data have real entropy (thousands of records, not a hundred), when the output is stable or can be made stable through regularisation, and when the question you care about is a concrete one, such as "can anyone tell whether this patient was in the training set?", rather than an abstract distance between distributions. It gives a number that means something to a non-specialist, at a noise level that leaves the model useful.

And in either case, check the guarantee against an attack. The one thing both communities now agree on is that a privacy parameter nobody has tried to break is a claim, not a result.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>PAC Privacy (Xiao &amp; Devadas, CRYPTO 2023) defines privacy as the failure of an inference task over a data distribution, and bounds the adversary's gain by the mutual information between data and output. The adversary is unbounded; the guarantee is information-theoretic.</li>
<li>The noise is calibrated by simulation to how much the output actually moves, not to worst-case sensitivity. That is where the 63× comes from, and it is also why stable, regularised algorithms get privacy almost for free.</li>
<li>It loses on tiny datasets and unstable high-dimensional outputs, it costs a thousand simulated runs, and its guarantee is only as good as the assumed distribution.</li>
<li>Adaptive composition (2026) and zero-leakage LLM fine-tuning (PACZero) have moved it from a definition to a toolkit; whether regulators will accept a distribution-dependent guarantee is still open.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Sridhar, Xiao, Devadas. <em>PAC-Private Algorithms.</em> IEEE S&amp;P 2025. <a href="https://eprint.iacr.org/2024/718">ePrint 2024/718</a></li>
<li>Dwork, McSherry, Nissim, Smith. <em>Calibrating Noise to Sensitivity in Private Data Analysis.</em> TCC 2006. <a href="https://link.springer.com/chapter/10.1007/11681878_14">Springer</a></li>
<li>Abadi, Chu, Goodfellow et al. <em>Deep Learning with Differential Privacy.</em> ACM CCS 2016. <a href="https://arxiv.org/abs/1607.00133">arXiv:1607.00133</a></li>
<li>Xiao, Devadas. <em>PAC Privacy: Automatic Privacy Measurement and Control of Data Processing.</em> CRYPTO 2023. <a href="https://arxiv.org/abs/2210.03458">arXiv:2210.03458</a></li>
<li>Xiao, Devadas. <em>PAC Privacy and Black-Box Privatization.</em> IEEE Security &amp; Privacy, July/August 2025. <a href="https://people.csail.mit.edu/devadas/pubs/PAC_Privacy_and_Black-Box_Privatization.pdf">PDF</a></li>
<li>Shokri, Stronati, Song, Shmatikov. <em>Membership Inference Attacks Against Machine Learning Models.</em> IEEE S&amp;P 2017. <a href="https://arxiv.org/abs/1610.05820">arXiv:1610.05820</a></li>
<li>Xiao. <em>Automated and Provable Privatization for Black-Box Processing.</em> PhD thesis, MIT, 2024. <a href="https://dspace.mit.edu/handle/1721.1/159202">DSpace@MIT</a></li>
<li>Zewe. <em>New method efficiently safeguards sensitive AI training data.</em> MIT News, 11 April 2025. <a href="https://news.mit.edu/2025/new-method-efficiently-safeguards-sensitive-ai-training-data-0411">news.mit.edu</a></li>
<li>Sridhar, Zhu, Devadas. <em>Privacy-Conscious Algorithm Design via PAC Privacy.</em> IEEE S&amp;P 2026. <a href="https://people.csail.mit.edu/devadas/pubs/designing_for_privacy.pdf">PDF</a></li>
<li>Zhu, Sridhar, Devadas. <em>PAC-Private Responses with Adversarial Composition.</em> arXiv 2026. <a href="https://arxiv.org/abs/2601.14033">arXiv:2601.14033</a></li>
<li>Ertan, Zhu, Nguyen, van Dijk, Devadas. <em>PACZero: PAC-Private Fine-Tuning of Language Models via Sign Quantization.</em> NeurIPS 2026. <a href="https://arxiv.org/abs/2605.06505">arXiv:2605.06505</a></li>
<li>Xiao, Suh, Devadas. <em>Formal Privacy Proof of Data Encoding: The Possibility and Impossibility of Learnable Obfuscation.</em> ACM CCS 2024. <a href="https://people.csail.mit.edu/devadas/pubs/Learnable_Obfuscation.pdf">PDF</a></li>
<li>Xiao, Wan, Shi, Devadas. <em>One-Sided Bounded Noise: Theory, Optimization Algorithms and Applications.</em> ACM CCS 2025. <a href="https://people.csail.mit.edu/devadas/pubs/one_sided_noise.pdf">PDF</a></li>
<li>Xu, Ding, Zhang, Gao, Wang. <em>PAC Privacy Preserving Diffusion Models.</em> arXiv 2023. <a href="https://arxiv.org/abs/2312.01201">arXiv:2312.01201</a></li>
<li>Cuff, Yu. <em>Differential Privacy as a Mutual Information Constraint.</em> ACM CCS 2016. <a href="https://arxiv.org/abs/1608.03677">arXiv:1608.03677</a></li>
<li>Mironov. <em>Rényi Differential Privacy.</em> IEEE CSF 2017. <a href="https://arxiv.org/abs/1702.07476">arXiv:1702.07476</a></li>
<li>Steinke, Nasr, Jagielski. <em>Privacy Auditing with One (1) Training Run.</em> NeurIPS 2023. <a href="https://proceedings.neurips.cc/paper_files/paper/2023/hash/9a6f6e0d6781d1cb8689192408946d73-Abstract.html">NeurIPS proceedings</a></li>
</ol>
</section>
