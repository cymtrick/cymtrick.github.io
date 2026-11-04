---
layout: post
title: "Differential Privacy: What a Formal Guarantee Actually Looks Like"
date: 2025-12-04
updated: 2026-11-04
category: "Privacy"
series_index: 6
read_time: "17 min read"
dek: "In 2016, differentially private training reached 73% on CIFAR-10 at ε = 8. By 2022 the same budget bought 81.4%, and in 2025 Google released a billion-parameter language model trained at ε = 2. What ε means, what it costs, and what the deployed numbers from Chrome, Apple and the US Census actually promise."
lead_figure: dp-cifar
lead_caption: "Test accuracy of differentially private CIFAR-10 models as a function of the privacy budget ε, at δ = 10⁻⁵. Between 2016 and 2022 the curve moved up by roughly ten points at every budget without any change to the guarantee: the improvements were in optimisation (large batches, augmentation multiplicity, parameter averaging), not in the definition. Data from [8, 11, 22]."
thumb: dp-thumb
tags: [privacy, differential-privacy, DP-SGD, auditing, theory]
---

In 2006 Netflix published 100 million movie ratings from about 480,000 subscribers, with names removed, as a public machine learning competition. Two years later Narayanan and Shmatikov showed that eight ratings, two of which could be wrong, with dates known to within two weeks, uniquely identified 99% of the subscribers in the dataset, and that the public reviews people had posted on IMDb were enough to supply those eight ratings [1]. The sequel competition was cancelled after a class action and an FTC inquiry. Nobody had done anything that looked careless by the standards of the time. The standard was wrong.

The previous post in this series was about what a trained model leaks. This one is about the only definition of "does not leak" that has survived twenty years of attacks, what it costs to achieve, and what the numbers people actually deploy do and do not mean.

## Why "we anonymised it" fails

The intuitive approach to privacy is to remove identifiers and release the rest. The formal version of that intuition is **k-anonymity** (Sweeney, 2002): generalise the quasi-identifying attributes until every record is indistinguishable from at least k − 1 others [2]. It has two problems that patches did not fix. If everyone in an equivalence class shares the same sensitive value, indistinguishability protects nothing; **ℓ-diversity** (Machanavajjhala et al., 2006) requires the sensitive values to vary [23]. If the distribution of sensitive values within a class is skewed relative to the population, the class still leaks; **t-closeness** (Li, Li and Venkatasubramanian, 2007) bounds that skew [24]. Each patch addresses the previous attack and none addresses the next one, because none of them is defined in terms of what an attacker with arbitrary side information can learn. The Netflix attack used side information nobody had modelled.

Differential privacy is the response to this. It does not define privacy as a property of the released data. It defines it as a property of the *algorithm* that produced the data, quantified over every possible dataset and every possible attacker.

## The definition, and what ε means

A randomised mechanism M is (ε, δ)-differentially private if, for every pair of datasets D and D′ that differ in one record, and every set S of possible outputs,

<div class="math"><div class="math-label">(ε, δ)-differential privacy (Dwork, McSherry, Nissim, Smith 2006; Dwork &amp; Roth 2014)</div>Pr[M(D) ∈ S]  ≤  e^ε · Pr[M(D′) ∈ S] + δ</div>

The definition comes from Dwork, McSherry, Nissim and Smith's 2006 paper [3], whose title, *Calibrating Noise to Sensitivity*, is also the method; Dwork and Roth's monograph is the standard reference for everything that follows [4]. Three things about the definition are worth stating precisely, because each is commonly misstated.

First, the guarantee is symmetric in "you are in the dataset" and "you are not." Whatever an adversary sees, their posterior odds about your presence move by at most a factor of e^ε relative to their prior, up to the slack δ. This holds no matter what else they know.

Second, ε is not a vague knob. The hypothesis-testing reading, made rigorous by Dong, Roth and Su's f-DP framework [6], is that any test an adversary runs to decide whether you were in the data has a receiver operating characteristic bounded by TPR ≤ e^ε · FPR + δ. At ε = 1, an attacker who accepts a 0.1% false-positive rate can achieve at most a 0.27% true-positive rate. At ε = 8 the bound is e⁸ × 0.001 ≈ 3, which is vacuous: the definition no longer constrains a low-false-positive attacker at all. Ponomareva et al.'s practitioner guide draws its tiers from this reading: ε ≤ 1 is strong, ε ≤ 10 is the usual compromise in deep learning, and ε > 10 still bounds memorisation but is weak as a guarantee [7].

{% include fig.html name="dp-hypothesis" num="1" caption="The hypothesis-testing view of ε. Left: on two neighbouring datasets a Gaussian mechanism produces two shifted distributions, and the adversary must decide which one a draw came from. Right: the ROC curve of the best possible test is confined to the unshaded band between TPR = e^ε·FPR + δ and its mirror image; the blue curve is the actual trade-off for the Gaussian mechanism, which f-DP characterises exactly. Redrawn from the framing in [4] and [6]." %}

Third, δ is not a free parameter. With δ = 1/n, a mechanism that publishes one random record in the clear satisfies the definition, which is why δ ≪ 1/n is the requirement [7]. Deployed values are 10⁻⁵ for CIFAR-10 [8], 8·10⁻⁷ for ImageNet [11], 10⁻¹⁰ for the 2020 Census [18] and 1.1·10⁻¹⁰ for VaultGemma [15].

## Mechanisms: sensitivity is the whole idea

The 2006 paper's construction is still the one everyone learns. Define the sensitivity Δf of a function f as the most its output can change when one record changes. Then adding Laplace noise with scale Δf/ε to f(D) is ε-DP [3]. The Gaussian mechanism, which is what gradient-based training uses because gradients have natural ℓ₂ bounds, adds noise with standard deviation σ ≥ √(2 ln(1.25/δ)) · Δ₂f/ε and achieves (ε, δ)-DP [4]. Pure ε-DP with Gaussian noise is impossible; δ is the price of using it.

The oldest DP mechanism predates the definition by forty years. Warner's randomised response (1965) asks survey respondents to flip a coin and answer truthfully on heads, randomly on tails [5]. With a fair coin the ratio of probabilities of any answer under the two true states is at most 3, so the mechanism is ln 3 ≈ 1.1-DP, and the aggregate is still an unbiased estimate of the population rate after a simple correction. Every local-DP deployment discussed below is an elaboration of this trick.

## Composition, and why accountants matter

Privacy degrades under repeated queries, and training a neural network is tens of thousands of queries against the same data. The basic composition theorem says k mechanisms at ε each compose to kε; advanced composition improves this to roughly ε√(2k ln(1/δ′)) at the cost of an extra δ′ [4]. For DP-SGD even advanced composition is far too loose.

Abadi et al.'s 2016 paper [8] contributed three things, and it is the third that made the other two usable. Clip every per-example gradient to ℓ₂ norm C, which bounds the sensitivity of the sum. Add Gaussian noise of standard deviation σC to the clipped sum. And track privacy loss with the **moments accountant**, which follows the log-moments of the privacy loss random variable rather than composing (ε, δ) pairs. The paper's own comparison makes the point: at sampling rate q = 0.01, σ = 4 and δ = 10⁻⁵, one hundred epochs cost ε = 9.34 under strong composition and ε = 1.26 under the moments accountant. At four hundred epochs the figures are 24.22 and 2.55 [8].

<div class="math"><div class="math-label">DP-SGD update (Abadi et al. 2016), lot of size L sampled with probability q = L/N</div>g̃ = (1/L) · [ Σᵢ clip(∇Lᵢ(θ), C) + N(0, σ²C²I) ],    θ ← θ − η·g̃</div>

The accountant has a family tree that is worth knowing because the names cause confusion. Mironov showed that the moments accountant is Rényi differential privacy under another name: bound the Rényi divergence of order α between M(D) and M(D′), compose additively, convert to (ε, δ) at the end [9]. The conversion is lossy. The privacy-loss-distribution approach composes the exact distribution of the privacy loss by convolution; Gopi, Lee and Wutschitz made this numerically efficient [10], and it is now the default "PRV accountant" in the standard libraries. f-DP and its Gaussian special case, μ-GDP, go furthest: composition is lossless, Poisson subsampling has a clean theorem, and a central limit theorem says the composition of many small mechanisms converges to μ-GDP whatever they were [6]. One detail that most implementations get wrong: all of these accountants assume Poisson subsampling of each batch, and shuffling the dataset instead gives a different, and in general weaker, guarantee than the one reported.

## DP-SGD from 2016 to 2022: the curve moved, the definition did not

The 2016 results established that private deep learning was possible: 97% on MNIST at ε = 8, and on CIFAR-10, with convolutional layers pretrained on a public dataset, 67% at ε = 2, 70% at ε = 4 and 73% at ε = 8 [8]. For several years the conventional wisdom was that at small ε, handcrafted features beat end-to-end private networks; Tramèr and Boneh made that case with 60.3%, 67.2% and 69.3% at ε = 1, 2 and 3 [22].

De et al.'s 2022 DeepMind report changed the picture with no new privacy mathematics at all [11]. A WideResNet-40-4 trained from scratch with DP-SGD reached 56.4% at ε = 1, 65.9% at ε = 2, 70.7% at ε = 3, 73.5% at ε = 4, 78.8% at ε = 6 and 81.4% at ε = 8. The ingredients were group normalisation and weight standardisation in place of batch norm, which has no per-example decomposition; batches of 16,384 examples, which improve the signal-to-noise ratio of the noisy sum; an exponential moving average of the parameters; and **augmentation multiplicity**, averaging the gradients of K = 32 augmented copies of each example *before* clipping, which is free under the definition because the clipped quantity is still a function of one record.

The same report showed what pretraining buys. An NFNet-F3 pretrained on JFT-4B and fine-tuned on ImageNet with DP-SGD reached 77.6% top-1 at ε = 0.1, 83.8% at ε = 0.5 and 86.7% at ε = 8, against 88.5% without privacy. Trained from scratch, the best ImageNet result at ε = 8 was 32.4% [11].

{% include fig.html name="dp-imagenet" num="2" caption="ImageNet top-1 accuracy of a DP-SGD fine-tuned NFNet-F3, pretrained on JFT-4B, against the privacy budget. Even at ε = 0.5 the model is within five points of non-private fine-tuning; the same recipe from scratch reaches 32.4% at ε = 8. The pretraining data is not covered by the guarantee, which is the caveat to keep in mind. Data from [11], Table 3." %}

That caveat deserves its own sentence. The guarantee covers the fine-tuning set. The pretraining set, in this and in every "DP fine-tuning" result below, is treated as public, and for web-scraped corpora "public" and "free of personal data" are not the same thing.

## Language models: fine-tuning is cheap, pretraining is not

Two ICLR 2022 papers established that private fine-tuning of large pretrained language models costs very little. Li, Tramèr, Liang and Hashimoto showed that with DP-friendly hyperparameters, meaning large batches, a tiny clipping norm and a higher learning rate, plus a reformulation of classification as text infilling, RoBERTa-large reaches 93.04% on SST-2 at ε = 3, and GPT-2 reaches 61.52 BLEU on the E2E generation task at ε = 3 against 69.46 non-private [12]. Their "ghost clipping" trick computes per-example gradient norms for linear layers without materialising per-example gradients, which cut memory by about three times relative to the standard implementation. Yu et al. showed that parameter-efficient fine-tuning makes the private update sparse and that the privacy tax shrinks with model size: on the DART table-to-text task at ε = 6.8, GPT-2 Small, Medium, Large and XL reach 38.5, 42.0, 43.1 and 43.8 BLEU against 48.1 non-private [13]. Both papers found none of the dimension-dependent degradation that the worst-case theory predicts.

Pretraining is a different matter. McKenna et al. fitted scaling laws for DP language-model training as a function of model size, steps and a noise-to-batch ratio, and found that the compute-optimal private model at a given FLOP budget is roughly a hundred times smaller than its non-private counterpart and wants on the order of 10³ to 10⁵ tokens per parameter, against about twenty for a non-private Chinchilla-optimal run [14]. Google's VaultGemma applied those laws: a one-billion-parameter model trained on 13 trillion tokens with batches of about 518,000 sequences, 100,000 steps and noise multiplier 0.614, achieving ε ≤ 2.0 and δ ≤ 1.1·10⁻¹⁰ at the level of a 1,024-token sequence [15]. Its benchmark scores land near GPT-2 1.5B from 2019: HellaSwag 39.1 against 61.0 for the non-private Gemma 3 1B, ARC-Easy 51.8 against 71.3, TriviaQA 11.2 against 39.8. The authors' memorisation test, feeding 50-token prefixes from the training data and checking for the 50-token suffix, found no detectable memorisation, where every non-private Gemma shows some [15].

The honest reading is a roughly five-year utility lag at ε = 2, and a unit of privacy that is per sequence, not per person. A fact that appears in thousands of training sequences is not protected by a per-sequence guarantee, which brings us to the question of units.

## Local versus central, and what people actually ship

There are two places to put the noise. In **central** DP a trusted curator holds the raw data and randomises the output of the analysis; in **local** DP each person randomises their own record before sending it, and the curator never sees the truth. The previous post described Apple and Google as central-DP examples. They are the canonical *local* ones. Local DP removes the trust assumption, but it is not free: for a frequency estimate over n users, central DP achieves error of order 1/ε while local DP achieves error of order √n/ε [4]. That is why local deployments need enormous populations and relatively large ε.

Google's RAPPOR in Chrome [16] is Warner's randomised response applied twice to a Bloom filter, a permanent response that is memoised so repeated reports cannot be averaged, and an instantaneous response on top. The Chrome parameters give ε = 0.5343 per report, and the paper notes that detecting a string present in 0.1% of reports needs on the order of fourteen million clients. Apple never published its ε. Tang, Korolova and colleagues reverse-engineered the macOS 10.12 and iOS 10 implementations and found per-datum budgets of ε = 1 for emoji and 2 for new words, a daily budget of 16 across four collections, and a budget that resets every day with no lifetime cap, so that the effective loss grows without bound over time [17].

The largest central deployment is the 2020 US Census. The TopDown algorithm allocates a zero-concentrated DP budget of ρ = 2.63 across geographic levels and queries, uses the discrete Gaussian mechanism, and post-processes to non-negative integer counts with exact state totals. The published guarantee for the redistricting data is ε = 19.61 in total, 17.14 for persons and 2.47 for housing units, at δ = 10⁻¹⁰; the April 2021 demonstration data had used ε = 12.2, and the budget was raised after complaints about small-area accuracy from redistricters and demographers [18]. By the ε ≤ 10 rule that is a weak guarantee, and the Bureau's defence rests on a reconstruction-and-reidentification attack it had run against its own 2010 release. The disagreement that followed was partly about ε and partly about whether the post-processing, not the noise, was responsible for most of the measured error.

{% include fig.html name="dp-deployed" num="3" caption="Published privacy budgets of deployed systems, with the unit of privacy in brackets. A per-report local-DP ε of 0.53 and a per-person central-DP ε of 19.61 are not on the same scale: the first protects one day's telemetry from one device, the second a person's entire census record. The dashed lines are the practitioner tiers from [7]. Data from [11, 15], [16, 17, 18]." %}

The single most useful habit from Ponomareva et al.'s guide is to refuse to read an ε without its unit. Report whether the guarantee is per example, per user or per sequence; whether adjacency means adding or removing a record or replacing one, since replacement is roughly twice as strong per unit of ε; the value of δ; which accountant was used; whether sampling was Poisson; and whether hyperparameters were tuned privately [7].

## Auditing: the guarantee is worst-case, the attack is not

A DP proof is an upper bound on what any adversary can do. Auditing asks for the matching lower bound: how much can a concrete attacker actually demonstrate? Jagielski, Ullman and Oprea used poisoning canaries and hundreds of training runs to estimate the privacy loss of DP-SGD on Fashion-MNIST, and found empirical lower bounds of 0.15, 0.37, 0.89, 1.90 and 2.43 against theoretical budgets of 1, 2, 4, 8 and 16 [19]. The gap of four to eight times could mean the analysis is loose or the attack is weak.

Nasr et al. settled which [20]. With white-box access to every gradient step, gradient canaries and f-DP test statistics, two training runs on CIFAR-10 at a theoretical ε = 8 gave an audited lower bound of 7.09; the same runs audited with (ε, δ) statistics gave 3.63; a black-box auditor who sees only the final model gets about 1.6. The analysis is nearly tight. The gap in earlier audits was the threat model, not slack in the proof. The same paper turned auditing into a unit test and caught real bugs: clipping after averaging, a biased random number generator and under-scaled noise all produced audited lower bounds far above the claimed ε, above 35 in the case of the broken clipping. Steinke, Nasr and Jagielski then showed that a usable lower bound can be obtained from a single training run by inserting many canaries at once and using the connection between DP and generalisation [21], which is cheap enough to run on every job.

{% include fig.html name="dp-audit" num="4" caption="Claimed versus audited ε for DP-SGD. The 2020 audits with a black-box poisoning attacker recovered a fraction of the budget; the 2023 white-box audit with f-DP statistics recovers 7.09 of 8. The remaining gap between the white-box and black-box columns is the difference between what the proof guards against and what a real attacker without gradient access can do. Data from [19], Tables 2–3, and [20], Tables 1–3." %}

The implication cuts both ways. If you are worried about an insider with access to the training pipeline, ε is nearly the truth. If your adversary only sees the released model, the empirical privacy may be far better than ε says, or your attacks may simply be weak, and nobody has a tight black-box audit that would tell you which.

## What ε does not promise

Five open problems define the current state of the field, and I would rather state them plainly than end on the Netflix anecdote.

The unit of privacy for language models is unresolved. Example- or sequence-level ε ≤ 8 is the standard, but a person's data is spread across thousands of sequences, and user-level guarantees cost far more utility [7, 15]. Most reported DP-SGD numbers assume Poisson subsampling while the training loop shuffles, and the true ε under shuffling can be substantially larger [6, 7]. "Public" pretraining data is often scraped personal data, so the guarantee covers a small fraction of what the model saw [11, 12]. Audits are tight only with white-box access [20]. And in the one public policy fight so far, the Census, the argument was never really about ε at all but about post-processing and whose counts got distorted [18].

None of this is an argument against the definition. Every one of these problems is visible *because* the definition is precise enough to show where it stops. That is the property syntactic anonymity never had, and it is why, twenty years after Netflix, differential privacy is still the only answer to "does this leak?" that has not been overturned by the next attack. The next post looks at a newer framework, PAC Privacy, that tries to give a comparable guarantee at a lower price by measuring rather than bounding.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Differential privacy is a property of the algorithm, quantified over all neighbouring datasets and all attackers. ε bounds the ROC curve of any membership test: at ε = 1 a 0.1%-false-positive attacker gets at most 0.27% true positives; at ε = 8 the bound is vacuous.</li>
<li>DP-SGD is clipping, Gaussian noise and an accountant; the accountant is what made it practical (ε = 1.26 instead of 9.34 for a hundred epochs). Modern accountants (PLD, f-DP) are tighter still and assume Poisson sampling.</li>
<li>The utility cost fell sharply without any change to the guarantee: 73% to 81.4% on CIFAR-10 at ε = 8 between 2016 and 2022, and private fine-tuning of pretrained models is close to free. Private pretraining still costs about five years of progress.</li>
<li>Never read an ε without its unit of privacy and δ. Chrome's 0.53 per report and the Census's 19.61 per person are not comparable numbers.</li>
<li>Audits show the proof is nearly tight against a white-box attacker and loose against a black-box one; the gap is the threat model, and it is also a unit test that catches real implementation bugs.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Narayanan, Shmatikov. <em>Robust De-anonymization of Large Sparse Datasets.</em> IEEE S&amp;P 2008. <a href="https://mail.profsandhu.com/cs6393_s13/ns_2008.pdf">PDF</a></li>
<li>Sweeney. <em>k-Anonymity: A Model for Protecting Privacy.</em> International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems 10(5), 2002. <a href="https://doi.org/10.1142/S0218488502001648">doi:10.1142/S0218488502001648</a></li>
<li>Dwork, McSherry, Nissim, Smith. <em>Calibrating Noise to Sensitivity in Private Data Analysis.</em> TCC 2006. <a href="https://link.springer.com/chapter/10.1007/11681878_14">Springer</a></li>
<li>Dwork, Roth. <em>The Algorithmic Foundations of Differential Privacy.</em> Foundations and Trends in Theoretical Computer Science 9(3–4), 2014. <a href="https://doi.org/10.1561/0400000042">doi:10.1561/0400000042</a></li>
<li>Warner. <em>Randomized Response: A Survey Technique for Eliminating Evasive Answer Bias.</em> Journal of the American Statistical Association 60(309), 1965. <a href="https://doi.org/10.1080/01621459.1965.10480775">doi:10.1080/01621459.1965.10480775</a></li>
<li>Dong, Roth, Su. <em>Gaussian Differential Privacy.</em> Journal of the Royal Statistical Society Series B 84(1), 2022. <a href="https://arxiv.org/abs/1905.02383">arXiv:1905.02383</a></li>
<li>Ponomareva, Hazimeh, Kurakin et al. <em>How to DP-fy ML: A Practical Guide to Machine Learning with Differential Privacy.</em> Journal of Artificial Intelligence Research 77, 2023. <a href="https://arxiv.org/abs/2303.00654">arXiv:2303.00654</a></li>
<li>Abadi, Chu, Goodfellow, McMahan, Mironov, Talwar, Zhang. <em>Deep Learning with Differential Privacy.</em> ACM CCS 2016. <a href="https://arxiv.org/abs/1607.00133">arXiv:1607.00133</a></li>
<li>Mironov. <em>Rényi Differential Privacy.</em> IEEE CSF 2017. <a href="https://arxiv.org/abs/1702.07476">arXiv:1702.07476</a></li>
<li>Gopi, Lee, Wutschitz. <em>Numerical Composition of Differential Privacy.</em> NeurIPS 2021. <a href="https://proceedings.neurips.cc/paper/2021/hash/6097d8f3714205740f30debe1166744e-Abstract.html">NeurIPS proceedings</a></li>
<li>De, Berrada, Hayes, Smith, Balle. <em>Unlocking High-Accuracy Differentially Private Image Classification through Scale.</em> arXiv 2022. <a href="https://arxiv.org/abs/2204.13650">arXiv:2204.13650</a></li>
<li>Li, Tramèr, Liang, Hashimoto. <em>Large Language Models Can Be Strong Differentially Private Learners.</em> ICLR 2022. <a href="https://arxiv.org/abs/2110.05679">arXiv:2110.05679</a></li>
<li>Yu, Naik, Backurs et al. <em>Differentially Private Fine-tuning of Language Models.</em> ICLR 2022. <a href="https://arxiv.org/abs/2110.06500">arXiv:2110.06500</a></li>
<li>McKenna, Huang, Sinha et al. <em>Scaling Laws for Differentially Private Language Models.</em> ICML 2025. <a href="https://arxiv.org/abs/2501.18914">arXiv:2501.18914</a></li>
<li>Sinha, Mesnard, McKenna et al. <em>VaultGemma: A Differentially Private Gemma Model.</em> arXiv 2025. <a href="https://arxiv.org/abs/2510.15001">arXiv:2510.15001</a></li>
<li>Erlingsson, Pihur, Korolova. <em>RAPPOR: Randomized Aggregatable Privacy-Preserving Ordinal Response.</em> ACM CCS 2014. <a href="https://arxiv.org/abs/1407.6981">arXiv:1407.6981</a></li>
<li>Tang, Korolova, Bai, Wang, Wang. <em>Privacy Loss in Apple's Implementation of Differential Privacy on MacOS 10.12.</em> arXiv 2017. <a href="https://arxiv.org/abs/1709.02753">arXiv:1709.02753</a></li>
<li>Abowd, Ashmead, Cumings-Menon et al. <em>The 2020 Census Disclosure Avoidance System TopDown Algorithm.</em> Harvard Data Science Review 2022. <a href="https://arxiv.org/abs/2204.08986">arXiv:2204.08986</a>; budget figures from the US Census Bureau's <a href="https://www.census.gov/newsroom/press-releases/2021/2020-census-key-parameters.html">9 June 2021 release</a></li>
<li>Jagielski, Ullman, Oprea. <em>Auditing Differentially Private Machine Learning: How Private is Private SGD?</em> NeurIPS 2020. <a href="https://papers.nips.cc/paper/2020/hash/fc4ddc15f9f4b4b06ef7844d6bb53abf-Abstract.html">NeurIPS proceedings</a></li>
<li>Nasr, Hayes, Steinke, Balle, Tramèr, Jagielski, Carlini, Terzis. <em>Tight Auditing of Differentially Private Machine Learning.</em> USENIX Security 2023. <a href="https://www.usenix.org/conference/usenixsecurity23/presentation/nasr">USENIX</a></li>
<li>Steinke, Nasr, Jagielski. <em>Privacy Auditing with One (1) Training Run.</em> NeurIPS 2023. <a href="https://proceedings.neurips.cc/paper_files/paper/2023/hash/9a6f6e0d6781d1cb8689192408946d73-Abstract.html">NeurIPS proceedings</a></li>
<li>Tramèr, Boneh. <em>Differentially Private Learning Needs Better Features (or Much More Data).</em> ICLR 2021. <a href="https://arxiv.org/abs/2011.11660">arXiv:2011.11660</a></li>
<li>Machanavajjhala, Kifer, Gehrke, Venkitasubramaniam. <em>ℓ-Diversity: Privacy Beyond k-Anonymity.</em> ICDE 2006; ACM TKDD 1(1), 2007. <a href="https://doi.org/10.1145/1217299.1217302">doi:10.1145/1217299.1217302</a></li>
<li>Li, Li, Venkatasubramanian. <em>t-Closeness: Privacy Beyond k-Anonymity and ℓ-Diversity.</em> ICDE 2007. <a href="https://doi.org/10.1109/ICDE.2007.367856">doi:10.1109/ICDE.2007.367856</a></li>
</ol>
</section>
