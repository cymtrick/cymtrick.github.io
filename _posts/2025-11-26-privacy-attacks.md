---
layout: post
title: "Your Model Remembers Things It Shouldn't"
date: 2025-11-26
updated: 2026-11-04
category: "Privacy"
series_index: 5
read_time: "17 min read"
dek: "A trained model is a lossy compression of its training data, and the loss is not large enough. For about $200 of API queries, researchers pulled more than ten thousand verbatim training sequences out of ChatGPT. Here is what a model leaks, how it is measured, and why the most-used metric was wrong for five years."
lead_figure: privacy-lira
lead_caption: "Seven membership-inference attacks on the same CIFAR-10 models. Judged by balanced accuracy they are nearly interchangeable; judged by how many members they identify at a 0.1% false-positive rate, the 2018 loss-threshold attack finds none and LiRA finds 8.4%. Data from [4], Table I."
thumb: privacy-thumb
tags: [privacy, membership-inference, model-inversion, memorization, LLMs]
---

A hospital trains a readmission model on patient records and deploys it behind an API. Clinicians send features in and get a risk score out. No records leave the building, no weights are published. The question this post is about is what an outsider with only that API can learn about the patients, and the answer, worked out over about a decade, is: more than you would like, in several distinct ways.

It helps to be precise about what "leak" means, because four different things get conflated. An attacker might learn whether a particular record was in the training set (*membership inference*); might learn a hidden attribute of a record they partly know (*attribute inference* or *model inversion*); might learn something about the dataset as a whole, such as its class balance (*property inference*); or might recover training text or images verbatim (*extraction*). These have different threat models, different defenses, and, it turns out, very different success rates on modern models. The field's most important recent finding is that the first one works far less well on large language models than the last one, which is the opposite of what most people assume.

## Membership inference, and the overfitting theorem

Shokri, Stronati, Song and Shmatikov [1] posed membership inference as a game in 2017. Given a record x and black-box access to a model trained on an unknown dataset, say whether x was in it. Their attack trains *shadow models* on data from the same distribution, for which membership is known by construction, then trains a classifier on the shadow models' output vectors to recognise the signature of a training example. The signature exists because models are more confident on data they have seen. Against commercial machine-learning-as-a-service platforms the attack reached a median precision of 0.94 on Google's prediction API and 0.74 on Amazon's, with recall near one, and its success tracked two things: how much the model overfit, and how many classes it had [1].

Yeom et al. [2] made the overfitting connection exact. For the simplest adversary, one that declares "member" whenever the loss on x is below a threshold, the *membership advantage* over random guessing equals the model's generalisation gap, and an ε-differentially-private learner bounds that advantage by e^ε − 1. The same paper formalised attribute inference and showed its advantage is a function of the generalisation gap and of how much influence the hidden attribute has on the output. Salem et al. [3] then stripped away most of Shokri's machinery: one shadow model does as well as ten, shadow data from an unrelated domain still works (training the shadow on news text and attacking a CIFAR-100 classifier gives 0.94 precision), and a threshold on the top posterior with no training at all reaches an AUC above 0.8. The signal lives in the confidence vector; the shadow models were scaffolding.

## The metric was wrong

For five years the field reported membership inference as balanced accuracy or AUC, and both were misleading. Carlini et al. [4] made the argument in 2022 with a thought experiment. An attack that is perfectly confident on 0.1% of the training set and guesses randomly on the rest has an AUC of about 0.51 and looks worse than a loss threshold. But it is a far more dangerous attack: it names specific people with certainty. The number that matters is the true-positive rate at a false-positive rate low enough that the attacker's claims are credible, and it should be read off a log-log ROC curve.

Their attack, the Likelihood Ratio Attack (LiRA), fits per-example Gaussians to the model's logit-scaled confidence under shadow models trained with and without the example, and runs a likelihood-ratio test. On CIFAR-10, LiRA reaches 8.4% TPR at 0.1% FPR and 2.2% at 0.001%, where the loss-threshold attack of Yeom et al. reaches 0.0% at both. The balanced accuracies of the two attacks are 63.8% and 59.4%, four points apart [4]. The lead figure shows all seven attacks they compared; the ranking by accuracy and the ranking by low-FPR TPR disagree, and only the second one tells you who is at risk.

Two details from the paper matter in practice. Sixty-four shadow models capture most of the benefit, and two augmentation queries (the image and its mirror) raise TPR from 5.6% to 7.5% at 0.1% FPR [4]. And risk is heterogeneous: mislabelled and out-of-distribution training examples are far easier to identify than typical ones, which is exactly the tail that average-case metrics hide and where real harm sits.

## Inversion: recovering what was never shared

Model inversion predates deep learning. Fredrikson et al. [5] attacked a *linear* warfarin-dosing model in 2014: given the model, a patient's demographics and their stable dose, infer the VKORC1 genotype. The inference beat the prior substantially, and in simulated clinical trials no differential-privacy budget between ε = 0.25 and ε = 100 blocked the attack without raising the mortality risk of the resulting dosing above fixed dosing. It was the first demonstration in applied ML that the privacy–utility trade-off has a body count.

The 2015 follow-up [6] generalised the attack to any model that returns confidence scores, with two case studies that are still the canonical ones. Against a decision tree trained on lifestyle surveys, white-box attribute inference reached 100% precision on a sensitive attribute. Against a face recogniser trained on softmax outputs, gradient descent in pixel space produced images that Mechanical Turk workers matched to the right person 75% of the time overall, 87% at best, and about 95% for skilled workers, against a 20% chance baseline. The first countermeasure appeared in the same paper: rounding confidences to 0.05 defeated the black-box version of the attack.

Pixel-space inversion does not survive the move to deep convolutional networks; the recovered images become noise. The modern form is a *prior* problem. Zhang et al. [7] trained a GAN on public face images and optimised in its latent space against the target classifier. Where Fredrikson's attack recovers 0% top-1 identity on a VGG16 face model, the generative attack recovers 28%, and 76% top-5 on a stronger recogniser. Two findings from that paper should worry anyone relying on standard defenses: more accurate models are *more* invertible, and record-level differential privacy at ε = 0.1 on MNIST did not stop the attack, because inversion recovers what a class looks like rather than any single record.

## Property inference: what the weights say about the dataset

A third family asks about the dataset rather than the record. Ateniese et al. [8] trained a meta-classifier on the *parameters* of shadow models to learn, for example, whether a speech-recognition model had been trained on data containing a particular accent. Ganju et al. [9] made this practical for fully connected networks by representing each weight matrix as a set rather than a sequence, so that the meta-classifier is invariant to the arbitrary permutation of hidden units. Both are white-box attacks on the weights; the original version of this post described them as query attacks, which they are not. Properties like class balance or demographic composition can be sensitive even when no individual is exposed, which is why this line matters for models released as open weights.

## Extraction: 604 sequences, then ten thousand

Language models introduced a leak that needs no statistical test. Carlini et al. [10] defined *k-eidetic memorisation*, a sequence that can be extracted from the model and appears in at most k training documents, and went looking for it in GPT-2. They generated 600,000 samples under three sampling strategies, ranked them by how much more likely the model found them than a reference measure (a smaller model's perplexity, or zlib compression entropy), and manually checked the top 1,800. They confirmed 604 unique memorised sequences, among them 46 containing named individuals, 32 with contact information, and a few hundred-digit UUIDs. The number is 604, not "thousands," and the best sampling-and-ranking configuration found 67 memorised sequences per 100 candidates. GPT-2 XL memorised more than eighteen times as much as GPT-2 Small in a controlled insertion experiment [10].

The follow-up [11] turned the anecdote into scaling laws. Across the GPT-Neo family trained on the Pile, the fraction of training sequences that can be reproduced grows log-linearly with model size, about 19 percentage points per tenfold increase in parameters, with R² = 0.998. It grows log-linearly in how many times a sequence is duplicated. And it grows with the length of the prompt: a 6B model reproduces 33% of a sample of training sequences given 50 tokens of context and 65% given 450. Deduplication helps, from 3.6% to 1.2% for sequences repeated fewer than 35 times, and so does the distinction between *discoverable* memorisation (the attacker already has the prefix) and *extractable* memorisation (they do not): on random 1,000-token sequences the extractable rate is in the low single digits [11].

| Lever | Setting | Memorised fraction |
|---|---|---|
| Model size | GPT-2 XL 1.5B → GPT-Neo 125M → GPT-J 6B, random 1,000-token sequences | 2% → 4% → 7% |
| Context length | GPT-J 6B, 50 → 450 tokens of true prefix | 33% → 65% |
| Duplication | C4 → deduplicated C4, sequences repeated < 35 times | 3.6% → 1.2% |

<p class="fig-caption">The three levers of memorisation in language models, each with the endpoints reported in the paper. Note that GPT-2 XL was trained on different data from the GPT-Neo family, so the first row is suggestive rather than a controlled comparison. Data from [11].</p>

Then came the result that made the newspapers. Nasr et al. [12] asked ChatGPT (gpt-3.5-turbo) to repeat the word "poem" forever. After a few hundred repetitions the model diverged from its chat persona and began emitting training data at roughly 150 times its baseline rate. About $200 of queries produced more than 10,000 unique verbatim 50-token sequences; 16.9% of a labelled sample contained personal information, most of it real; the longest recovered string exceeded 4,000 characters; and a Good–Turing estimate put the extractable total at a minimum of 1.5 million unique sequences, with the authors expecting hundreds of millions. On open models with a billion generated tokens each, between 0.12% and 1.44% of all output tokens fell inside a verbatim training sequence. Alignment had not removed memorisation; it had hidden it behind a chat format, which is why the attack had to break the model out of that format first.

{% include fig.html name="privacy-regurgitation" num="2" caption="Open-weight and production language models emit verbatim training data at measurable rates even without an attack. The chat-tuned ChatGPT baseline is low only because the chat format suppresses the behaviour; under the divergence attack its rate rose about 150-fold. Data from [12]." %}

Diffusion models memorise images in the same way. A generate-and-filter pipeline recovered more than a thousand near-exact training images, including photographs of named people and corporate logos, from Stable Diffusion and Imagen-class models, and controlled ablations showed diffusion models to be considerably less private than GANs trained on the same data, with duplication again the driver [13].

## Do membership attacks work on LLMs at all?

Here the story turns. Extraction is real and getting worse with scale. Per-example membership inference on large language models, by contrast, barely works. Duan et al. [14] evaluated five attacks, including the loss threshold, a reference-model comparison, a zlib ratio, the neighbourhood attack and Min-K% Prob, on Pythia models from 160M to 12B parameters trained on the Pile, with members and non-members drawn from the same distribution. On every domain except GitHub, AUC stayed below 0.6, and mostly between 0.50 and 0.58.

{% include fig.html name="privacy-mia-llm" num="3" caption="Membership inference on Pythia-dedup 12B. On natural splits of Wikipedia, ArXiv and PubMed every attack is within a few hundredths of chance. GitHub, where non-members share 77% of their 7-grams with the training set, is the exception. The temporal Wikipedia split reaches 0.80 because the non-members were written after the model's cut-off, which is distribution shift, not membership. Data from [14]." %}

The paper gives two reasons. Modern LLMs see most of their data once, so the overfitting signal that Yeom's theorem relies on is weak. And the boundary between member and non-member is fuzzy: Wikipedia non-members share 32.5% of their 7-grams with the training set, PubMed non-members 41%. When the authors restricted non-members to those with at most 20% overlap, the loss attack's AUC on ArXiv rose from 0.527 to 0.787, which is the same lesson from the other side: the attack detects *similarity to training data*, not membership.

That observation cuts against the most-used detector. Min-K% Prob [15] scores a text by the mean log-probability of its 20% least-likely tokens, and reports an AUC of 0.72 on WikiMIA, a benchmark whose non-members are Wikipedia pages written after 2023. The same paper used the method to argue that GPT-3 had seen Books3 (validation AUC 0.88 on copyrighted books) and to audit a Llama-2 model that had supposedly "unlearned" Harry Potter, finding passages the unlearning had missed. Both uses are informative. But WikiMIA is itself a temporal split, so its headline number is precisely the kind Duan et al. warn is inflated.

The constructive response is to aggregate. Maini et al. [16] show that an author who cannot prove any single passage was trained on can still run a hypothesis test over their whole corpus: weak per-example signals, combined across a dataset, separate Pile train and test subsets at p < 0.1 with no false positives, while the same signals on single examples are at chance. For a model trained once over a trillion tokens, "did you train on my sentence" is nearly unanswerable and "did you train on my book" is not.

<div class="callout">
<div class="callout-title">A live disagreement</div>
<p>One camp, broadly the authors of [4, 12] and [14], holds that per-example membership inference on well-generalised, single-epoch language models is close to impossible and that extraction is the real risk. The other, represented by the Min-K% and WikiMIA line [15], keeps reporting usable AUCs. The critics attribute those numbers to distribution shift between the member and non-member sets. The disagreement is partly about benchmarks and partly about what "membership" means for a sequence that overlaps 40% of its n-grams with the training set.</p>
</div>

## Defenses that have numbers

Ranked by the strength of the evidence behind them:

**Deduplication.** Lee et al. [17] found that more than 1% of the unprompted output of models trained on standard corpora is verbatim training text, that one 61-word sentence occurs more than 60,000 times in C4, and that deduplicating the corpus cuts memorised emissions by about tenfold. Kandpal et al. [18] showed the relationship is superlinear: a sequence present ten times is roughly a thousand times more likely to be generated than one present once, and existing membership attacks are at chance on sequences seen once. Deduplication is the cheapest intervention and the best-supported.

**Differentially private training.** DP-SGD [19] is the only defense with a proof, and the proof is about membership: the ε bounds the advantage of any membership adversary. Empirically the picture is more interesting than the proof. On CIFAR-10, LiRA's AUC against a model trained with clipping alone falls from 0.674 to 0.527 as the clipping norm tightens, and a small noise multiplier of σ = 0.2 brings it to about 0.52 at a cost of ten points of test accuracy, while the ε that the accountant certifies at that noise level is enormous [4]. The attack is far weaker than the worst case the guarantee covers. The next post in this series is about what the guarantee says and what it costs.

**Output-side mitigations.** Rounding confidences to 0.05 defeats the 2015 black-box inversion attack [6]; dropout and model stacking halve ML-Leaks precision on CIFAR-100 [3]. These stop specific attacks and should not be expected to stop adaptive ones.

**Unlearning.** Requested by regulation and routinely audited with Min-K%-style tests, which tend to find what the unlearning missed [15]. There is no equivalent of a differential-privacy guarantee for it yet.

What none of these address is the mechanism underneath: capacity enables memorisation, and memorisation creates an extraction surface. Every scaling law in [11] points the same way. The design question for a deployed model is not whether it memorised, but how much you were willing to trade for the capability that came with it.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Four different leaks hide under the word "privacy": membership, attributes, dataset properties and verbatim content. They have different attacks, defenses and success rates.</li>
<li>Report membership inference as TPR at a low FPR on a log-log ROC. Balanced accuracy and AUC hide the only attacks that matter.</li>
<li>Extraction from language models scales with parameters, duplication and context length, and alignment hides it rather than removing it. Deduplicate.</li>
<li>Per-example membership inference on single-epoch LLMs is close to chance; apparent successes usually measure distribution shift. Aggregate across a dataset instead.</li>
<li>Differential privacy is the only defense with a proof, and in practice attacks fall far short of the bound it certifies.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Shokri, Stronati, Song, Shmatikov. <em>Membership Inference Attacks against Machine Learning Models.</em> IEEE S&amp;P 2017. <a href="https://arxiv.org/abs/1610.05820">arXiv:1610.05820</a></li>
<li>Yeom, Giacomelli, Fredrikson, Jha. <em>Privacy Risk in Machine Learning: Analyzing the Connection to Overfitting.</em> IEEE CSF 2018. <a href="https://arxiv.org/abs/1709.01604">arXiv:1709.01604</a></li>
<li>Salem, Zhang, Humbert, Berrang, Fritz, Backes. <em>ML-Leaks: Model and Data Independent Membership Inference Attacks and Defenses on Machine Learning Models.</em> NDSS 2019. <a href="https://arxiv.org/abs/1806.01246">arXiv:1806.01246</a></li>
<li>Carlini, Chien, Nasr, Song, Terzis, Tramèr. <em>Membership Inference Attacks From First Principles.</em> IEEE S&amp;P 2022. <a href="https://arxiv.org/abs/2112.03570">arXiv:2112.03570</a></li>
<li>Fredrikson, Lantz, Jha, Lin, Page, Ristenpart. <em>Privacy in Pharmacogenetics: An End-to-End Case Study of Personalized Warfarin Dosing.</em> USENIX Security 2014. <a href="https://www.usenix.org/conference/usenixsecurity14/technical-sessions/presentation/fredrikson_matthew">USENIX</a></li>
<li>Fredrikson, Jha, Ristenpart. <em>Model Inversion Attacks that Exploit Confidence Information and Basic Countermeasures.</em> ACM CCS 2015. <a href="https://dl.acm.org/doi/10.1145/2810103.2813677">doi:10.1145/2810103.2813677</a></li>
<li>Zhang, Jia, Pei, Wang, Li, Song. <em>The Secret Revealer: Generative Model-Inversion Attacks Against Deep Neural Networks.</em> CVPR 2020. <a href="https://arxiv.org/abs/1911.07135">arXiv:1911.07135</a></li>
<li>Ateniese, Mancini, Spognardi, Villani, Vitali, Felici. <em>Hacking Smart Machines with Smarter Ones: How to Extract Meaningful Data from Machine Learning Classifiers.</em> Int. J. Security and Networks 2015. <a href="https://arxiv.org/abs/1306.4447">arXiv:1306.4447</a></li>
<li>Ganju, Wang, Yang, Gunter, Borisov. <em>Property Inference Attacks on Fully Connected Neural Networks using Permutation Invariant Representations.</em> ACM CCS 2018. <a href="https://dl.acm.org/doi/10.1145/3243734.3243834">doi:10.1145/3243734.3243834</a></li>
<li>Carlini, Tramèr, Wallace et al. <em>Extracting Training Data from Large Language Models.</em> USENIX Security 2021. <a href="https://arxiv.org/abs/2012.07805">arXiv:2012.07805</a></li>
<li>Carlini, Ippolito, Jagielski, Lee, Tramèr, Zhang. <em>Quantifying Memorization Across Neural Language Models.</em> ICLR 2023. <a href="https://arxiv.org/abs/2202.07646">arXiv:2202.07646</a></li>
<li>Nasr, Carlini, Hayase et al. <em>Scalable Extraction of Training Data from (Production) Language Models.</em> arXiv 2023. <a href="https://arxiv.org/abs/2311.17035">arXiv:2311.17035</a></li>
<li>Carlini, Hayes, Nasr et al. <em>Extracting Training Data from Diffusion Models.</em> USENIX Security 2023. <a href="https://www.usenix.org/conference/usenixsecurity23/presentation/carlini">USENIX</a></li>
<li>Duan, Suri, Mireshghallah et al. <em>Do Membership Inference Attacks Work on Large Language Models?</em> COLM 2024. <a href="https://arxiv.org/abs/2402.07841">arXiv:2402.07841</a></li>
<li>Shi, Ajith, Xia et al. <em>Detecting Pretraining Data from Large Language Models.</em> ICLR 2024. <a href="https://arxiv.org/abs/2310.16789">arXiv:2310.16789</a></li>
<li>Maini, Jia, Papernot, Dziedzic. <em>LLM Dataset Inference: Did you train on my dataset?</em> NeurIPS 2024. <a href="https://neurips.cc/virtual/2024/poster/95944">NeurIPS</a></li>
<li>Lee, Ippolito, Nystrom et al. <em>Deduplicating Training Data Makes Language Models Better.</em> ACL 2022. <a href="https://aclanthology.org/2022.acl-long.577">ACL Anthology</a></li>
<li>Kandpal, Wallace, Raffel. <em>Deduplicating Training Data Mitigates Privacy Risks in Language Models.</em> ICML 2022. <a href="https://proceedings.mlr.press/v162/kandpal22a.html">PMLR 162</a></li>
<li>Abadi, Chu, Goodfellow, McMahan, Mironov, Talwar, Zhang. <em>Deep Learning with Differential Privacy.</em> ACM CCS 2016. <a href="https://arxiv.org/abs/1607.00133">arXiv:1607.00133</a></li>
</ol>
</section>
