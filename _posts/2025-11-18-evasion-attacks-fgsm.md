---
layout: post
title: "Evasion Attacks and the Geometry of Adversarial Examples"
date: 2025-11-18
updated: 2026-11-04
category: "Attacks"
series_index: 4
read_time: "16 min read"
dek: "Add a perturbation smaller than one grey level to an image and a state-of-the-art classifier flips its answer with 99% confidence. Twelve years on, the best defenses on CIFAR-10 hold at about 74% under attack. Here is what happened in between, with the numbers."
lead_figure: evasion-frontier
lead_caption: "Published CIFAR-10 models plotted by clean accuracy and accuracy under AutoAttack at ε = 8/255. The standard model in the bottom right has 0% robust accuracy; the 2018 adversarially-trained baseline paid eight points of clean accuracy for 44%; the 2023–24 models recovered almost all of the clean accuracy and pushed robustness past 70%. Data from [4, 13], [22, 24]."
thumb: evasion-thumb
tags: [attacks, evasion, FGSM, PGD, robustness]
---

In December 2013, Szegedy and colleagues posted a paper with a deliberately understated title, *Intriguing properties of neural networks* [1]. One of the properties was this: take an image a network classifies correctly, solve a small optimisation problem to find the nearest input it classifies as something else, and the result is indistinguishable from the original to a person. The perturbation was not noise. Gaussian noise of a larger magnitude barely moved the predictions; the optimised perturbation moved them completely. Worse, the same perturbation often fooled a *different* network, trained on different data.

That second observation, transferability, is the one that turned an intriguing property into a security problem. It meant you did not need the model to attack the model. Most of what has happened since, from the fast attacks of 2015 to the adaptive-evaluation crisis of 2018 to the 74%-robust CIFAR-10 models of today, follows from trying to understand why these inputs exist and how much it costs to remove them.

## The panda, at ε = 0.007

The canonical example comes from Goodfellow, Shlens and Szegedy's follow-up [2]. A GoogLeNet classifies an image as "panda" with 57.7% confidence. Add a perturbation of magnitude ε = 0.007 per pixel, which the authors note is below the smallest step of an 8-bit image encoding, and the same network reports "gibbon" at 99.3%. The perturbation looks like static. The classification is not merely wrong; it is wrong with more confidence than the correct answer had.

The paper's main contribution, though, was an explanation. Szegedy et al. had suggested the phenomenon came from the networks being too non-linear, with small "pockets" of misclassification scattered through input space. Goodfellow et al. argued the opposite. Consider a linear model with weights w acting on an input x, and perturb it by η = ε·sign(w). Each coordinate of η is tiny, bounded by ε, but the dot product w·η sums over all m input dimensions and grows as ε·m·avg|wᵢ|. In a 150,000-dimensional image, a per-pixel change that no one can see produces a change in the pre-activation that dominates everything else. Deep networks, which are built from near-linear pieces and are deliberately trained to behave linearly for optimisation's sake, inherit this property. This is the **linearity hypothesis**, and it is still the standard first explanation.

{% include fig.html name="evasion-boundary" num="1" caption="Two views of the same step. Left: in input space the perturbation η is a nudge of size ε per pixel, just enough to cross the decision boundary. Right: under the linearity hypothesis the effect on the logit scales with the dimension m, whereas random noise of the same per-pixel size only scales with √m. Redrawn from the argument in [2]." %}

The hypothesis also yields an attack. If the model is locally linear, then the direction that increases the loss fastest under an L∞ budget is simply the sign of the gradient:

<div class="math"><div class="math-label">Fast Gradient Sign Method (FGSM), Goodfellow et al. 2015</div>x_adv = x + ε · sign(∇ₓ L(θ, x, y))</div>

One gradient evaluation, one step. On MNIST with ε = 0.25, FGSM pushes a shallow softmax classifier to a 99.9% error rate with 79.3% average confidence in the wrong answer, and a maxout network to 89.4% error at 97.6% confidence. On CIFAR-10 with ε = 0.1, a convolutional maxout network is wrong 87.15% of the time [2]. The targeted variant subtracts the gradient of the loss with respect to the *desired* label instead of adding the gradient of the true one; everything else is the same.

DeepFool [6] made the geometric picture operational in a different way: linearise the classifier around the input, step to the nearest linearised boundary, repeat, and read off a near-minimal L2 perturbation as a robustness measure for the model.

A note on units, because they are a modelling decision rather than a law. The field settled on a handful of threat models: L∞ with ε = 8/255 ≈ 0.031 on CIFAR-10, 4/255 on ImageNet and 0.3 on MNIST, or L2 with ε = 0.5 on CIFAR-10. Carlini and Wagner's attacks [3] exist in L0, L2 and L∞ versions precisely because the metric changes the answer, and they used them to show that *defensive distillation*, which had claimed to cut attack success from roughly 95% to 0.5%, provided no robustness at all: their attacks succeeded 100% of the time against distilled and undistilled networks alike.

## From one step to the saddle point

FGSM is a single linear step, and a network is not globally linear. The natural improvement, introduced by Kurakin, Goodfellow and Bengio [7], is to take several smaller steps, projecting back onto the ε-ball after each. Madry and colleagues [4] framed this not as an attack but as a training objective:

<div class="math"><div class="math-label">Robust optimisation (Madry et al. 2018)</div>min_θ  E_(x,y) [ max_{‖δ‖∞ ≤ ε} L(θ, x + δ, y) ]</div>

The inner maximisation is solved approximately by **projected gradient descent (PGD)** from random starting points inside the ball; the outer minimisation is ordinary training on the resulting worst-case inputs. The empirical observation that justified the whole approach was that PGD runs from many random starts converge to loss values that are tightly concentrated. There did not appear to be much worse adversaries hiding in the ε-ball than the ones PGD finds, which is why the paper calls PGD a "universal first-order adversary."

The numbers set a reference point that lasted five years. On CIFAR-10 at ε = 8/255, a standard WideResNet reaches 95.2% clean accuracy and 3.5% under a 20-step PGD attack. The PGD-trained version reaches 87.3% clean and 45.8% under the same attack [4]. Adversarial training works, and it costs eight points of clean accuracy.

{% include fig.html name="evasion-advtrain" num="2" caption="Adversarial training on CIFAR-10 at ε = 8/255. The standard model collapses under any gradient attack; the PGD-trained model keeps roughly half its accuracy under the strongest attack in the paper, at the price of eight points on clean data. Under the stronger AutoAttack ensemble the same model's robust accuracy is later measured at 44.04% [13]. Data from [4], Tables 2 and 5." %}

Why should robustness cost clean accuracy? Tsipras et al. [18] gave a clean theoretical account: in a simple Gaussian model, a classifier that is robust must give up weakly predictive features that an adversary can flip, and those features are exactly what standard training exploits for its last few points of accuracy. Ilyas et al. [17] made the complementary empirical argument with a striking experiment. They built a training set consisting *only* of adversarial perturbations, labelled with the adversarial target class, so that every image looked to a human like the wrong class. A network trained on it generalised to the clean test set. The perturbations carry predictive signal. On this reading adversarial examples are not bugs in the model but features of the data distribution that humans do not perceive, which also explains transferability: every model trained on the same data learns the same non-robust features.

Whether the trade-off is *fundamental* is a live disagreement, and the lead figure is the reason. The 2023–24 CIFAR-10 leaders sit at 93–95% clean accuracy with 70–74% robust accuracy, far above Madry's 87.3%. Most of the early gap was data and capacity, not an intrinsic price. I return to this below.

## Attacking without the gradient

Everything above assumes white-box access: you can differentiate through the model. The practical question in 2016 was whether a model behind an API was safe. Papernot et al. first showed that transfer is systematic rather than accidental [16], then answered the question directly [5] by training a *substitute* model on labels obtained by querying the target, crafting adversarial examples against the substitute, and transferring them. Against commercial APIs the results were 84.24% misclassification on MetaMind, 96.19% on Amazon Machine Learning and 88.94% on Google's prediction service, the latter two using logistic-regression substitutes with a few hundred to a few thousand queries. No gradient access is not a defense.

A second family skips the substitute and estimates gradients directly from the target's outputs. ZOO [8] uses coordinate-wise finite differences on confidence scores and matches white-box Carlini–Wagner attacks. Ilyas et al. [9] used natural evolution strategies and formalised three realistic threat models, with query costs for targeted attacks on an ImageNet InceptionV3 that are worth remembering: a median of 11,550 queries when the full score vector is available, 49,624 when only the top-k scores are, and 2.7 million when only the label is. A third family needs nothing but the top label. The Boundary Attack [10] starts from an input that is already adversarial and random-walks along the decision boundary toward the original; HopSkipJump [11] adds a Monte Carlo estimate of the boundary's normal and needs far fewer queries.

The surprise of 2020 was that the best black-box attack was none of these. Square Attack [12] is random search with localised square-shaped updates, and on ImageNet at ε = 0.05 it fails on 0.3%, 0.0% and 0.0% of images against Inception-v3, ResNet-50 and VGG-16 with *median* query counts of 24, 11 and 1. A single query. It also has a property that turned out to matter more than its efficiency: because it uses no gradient at all, it is immune to the family of defenses discussed next.

| Attack | Information needed | Targeted ImageNet, median queries |
|---|---|---|
| NES, query-limited [9] | full score vector | 11,550 |
| NES, partial information [9] | top-k scores | 49,624 |
| NES, label-only [9] | top label | 2,700,000 |
| Square Attack (untargeted) [12] | top label / score | 1–24 |

<p class="fig-caption">Query costs of black-box attacks against ImageNet classifiers. The NES rows are targeted attacks under three threat models; the Square Attack row is untargeted. The table is about orders of magnitude, not a head-to-head.</p>

## The evaluation crisis

Between 2016 and 2018 dozens of defenses were published, many at top venues, most of them broken within months. Athalye, Carlini and Wagner [14] examined the nine defenses accepted at ICLR 2018 and found that seven of them relied on **obfuscated gradients**: the defense made the gradient useless to an attacker without making the model robust. They identified three mechanisms. *Shattered* gradients come from non-differentiable preprocessing such as thermometer encoding or JPEG compression. *Stochastic* gradients come from test-time randomness. *Vanishing or exploding* gradients come from very deep unrolled computations such as a generative model run to convergence. For each they gave a fix: approximate the non-differentiable step with the identity on the backward pass (BPDA), optimise the expectation over the randomness (EOT), or reparameterise. Six of the seven defenses were broken completely and one partially. The two that survived were both forms of adversarial training.

{% include fig.html name="evasion-obfuscated" num="3" caption="Claimed robust accuracy of the ICLR 2018 defenses against what remained after Athalye et al.'s adaptive attacks. Where the original paper combined a defense with adversarial training, the table reports the defense alone. Defense-GAN's 55% is the practical result; the authors argue it is 0% in principle. Data from [14], Table 1." %}

The lesson was supposed to be "evaluate against adaptive attacks," and papers duly started including a section with that heading. Two years later Tramèr, Carlini, Brendel and Madry [15] broke thirteen defenses from ICLR, ICML and NeurIPS that had *already* claimed adaptive evaluations. Their conclusion is methodological rather than technical: an adaptive attack has to be designed for the specific defense, usually by simplifying the defense until the attack works and then adding complexity back, and a failed attack is evidence about the attack, not the defense.

The field's response was standardisation. AutoAttack [13] is a parameter-free ensemble of two PGD variants with better loss functions, a boundary attack and Square Attack. Run on 50 models from 35 papers, it lowered the reported robust accuracy of all but one, by more than ten points for thirteen models and more than thirty for eight. Some examples at CIFAR-10 ε = 8/255: Madry et al.'s 47.04% became 44.04%; TRADES's 56.43% became 53.08%; one ICLR 2020 defense fell from 68.7% to 36.45%, and another from 31.4% to 0.00%. RobustBench [22] turned AutoAttack into a leaderboard with admission rules: deterministic forward pass, non-zero gradients, no test-time optimisation, and a flag on any model where the gradient-free Square Attack beats the gradient-based attacks, since that pattern is the signature of gradient masking.

## Where the frontier is in 2026

With evaluation settled, progress became measurable, and it came mostly from data. Carmon et al.'s use of unlabelled data reached 59.53% under AutoAttack in 2019. Wang et al. [23] showed in 2023 that better diffusion models, judged by FID and run for only about twenty sampling steps, generate training images that lift CIFAR-10 robust accuracy to 70.69% at ε = 8/255 and CIFAR-100 to 42.67%, using no external data at all. Bartoldson et al. [24] then fitted scaling laws over model size, data size and generated-data quality, reached 74% with 20% fewer training FLOPs than the previous best, and asked where the curve ends.

Their answer is the most interesting result in the recent literature. The scaling laws predict robust accuracy plateauing near 90%. Separately, they asked people to label the AutoAttack images that fool their best model and found that human accuracy on those images is *also* about 90%. At ε = 8/255, some "adversarial" images have actually changed class to the human eye. The ceiling is not in the model; it is in the threat model. The L∞ ball was always a proxy for "imperceptible," and at the current frontier the proxy has started to break.

ImageNet remains harder. At ε = 4/255 the best entries on RobustBench are large vision transformers and ConvNeXts with convolutional stems: 78.62% clean and 59.68% robust for a Swin-L, 81.48% and 58.50% for a mixed ConvNeXtV2-L/Swin-L classifier [22]. Architecture matters as much as recipe here, and no one has yet written the scaling law.

## Leaving the ε-ball

Imperceptibility is a convenience for benchmarks, not a constraint on attackers. Sharif et al. [21] printed eyeglass frames for about 22 cents that let three subjects evade a face recogniser between 80% and 100% of the time, and impersonate a specific target 87.87% of the time. Eykholt et al. [19] optimised stickers for a stop sign, over a distribution of viewing angles and lighting, and a classifier misread it as a speed limit in 100% of lab photographs and 84.8% of frames from a moving vehicle. Brown et al.'s adversarial patch [20] drops the pretence entirely: a visible, scene-independent sticker that reliably hijacks the classification of whatever it is placed near. The threat model shifts from "the attacker can nudge every pixel slightly" to "the attacker controls a region," and most of the ε-ball literature has nothing to say about it.

## 2024–26: when the output is text

The newest version of the problem sits inside vision-language models. A model like LLaVA takes a frozen CLIP image encoder and feeds its embeddings to a language model; attack the encoder and everything downstream follows. Schlarmann et al. [25] measured it: LLaVA-1.5-7B's average captioning and visual-question-answering score drops from 76.2 to 2.25 at ε = 2/255 and 1.0 at ε = 4/255. Their fix, FARE, adversarially fine-tunes only the CLIP encoder, without labels and without touching the language model, and recovers 26.3 at ε = 4/255. The price is clean performance, 76.2 down to 65.0, which is the Madry trade-off again in a new setting.

{% include fig.html name="evasion-vlm" num="4" caption="The image pathway of a vision-language model is as fragile as any classifier. Replacing the CLIP encoder with an adversarially fine-tuned one restores a usable fraction of performance under attack at a clean-accuracy cost. Data from [25]." %}

Work at NeurIPS 2025 [26] argues that VLMs are in one respect *more* fragile than classifiers: an image perturbation can steer every generated token, so the same mechanism that flips a label can inject instructions, hijack an agent, or force a long useless output. Evasion, which began as a question about classification margins, has become a question about alignment, and the next two posts in this series pick up exactly there.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Adversarial examples are a consequence of high-dimensional, near-linear models trained on data that contains predictive features humans cannot see. They transfer because every model learns those features.</li>
<li>Adversarial training is the only empirical defense that has survived adaptive evaluation, and its clean-accuracy cost has shrunk from eight points to one or two as data and capacity scaled.</li>
<li>Evaluation is adversarial too. Trust AutoAttack numbers; be suspicious of any defense a gradient-free attack beats.</li>
<li>The L∞ ball is a proxy. At the 2024 frontier the proxy breaks, and in physical and multimodal settings it was never the right model.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Szegedy, Zaremba, Sutskever et al. <em>Intriguing properties of neural networks.</em> ICLR 2014. <a href="https://arxiv.org/abs/1312.6199">arXiv:1312.6199</a></li>
<li>Goodfellow, Shlens, Szegedy. <em>Explaining and Harnessing Adversarial Examples.</em> ICLR 2015. <a href="https://arxiv.org/abs/1412.6572">arXiv:1412.6572</a></li>
<li>Carlini, Wagner. <em>Towards Evaluating the Robustness of Neural Networks.</em> IEEE S&amp;P 2017. <a href="https://arxiv.org/abs/1608.04644">arXiv:1608.04644</a></li>
<li>Madry, Makelov, Schmidt, Tsipras, Vladu. <em>Towards Deep Learning Models Resistant to Adversarial Attacks.</em> ICLR 2018. <a href="https://arxiv.org/abs/1706.06083">arXiv:1706.06083</a></li>
<li>Papernot, McDaniel, Goodfellow et al. <em>Practical Black-Box Attacks against Machine Learning.</em> AsiaCCS 2017. <a href="https://arxiv.org/abs/1602.02697">arXiv:1602.02697</a></li>
<li>Moosavi-Dezfooli, Fawzi, Frossard. <em>DeepFool: a simple and accurate method to fool deep neural networks.</em> CVPR 2016. <a href="https://arxiv.org/abs/1511.04599">arXiv:1511.04599</a></li>
<li>Kurakin, Goodfellow, Bengio. <em>Adversarial examples in the physical world.</em> ICLR 2017 Workshop. <a href="https://arxiv.org/abs/1607.02533">arXiv:1607.02533</a></li>
<li>Chen, Zhang, Sharma, Yi, Hsieh. <em>ZOO: Zeroth Order Optimization based Black-box Attacks to Deep Neural Networks without Training Substitute Models.</em> AISec 2017. <a href="https://arxiv.org/abs/1708.03999">arXiv:1708.03999</a></li>
<li>Ilyas, Engstrom, Athalye, Lin. <em>Black-box Adversarial Attacks with Limited Queries and Information.</em> ICML 2018. <a href="https://arxiv.org/abs/1804.08598">arXiv:1804.08598</a></li>
<li>Brendel, Rauber, Bethge. <em>Decision-Based Adversarial Attacks: Reliable Attacks Against Black-Box Machine Learning Models.</em> ICLR 2018. <a href="https://arxiv.org/abs/1712.04248">arXiv:1712.04248</a></li>
<li>Chen, Jordan, Wainwright. <em>HopSkipJumpAttack: A Query-Efficient Decision-Based Attack.</em> IEEE S&amp;P 2020. <a href="https://arxiv.org/abs/1904.02144">arXiv:1904.02144</a></li>
<li>Andriushchenko, Croce, Flammarion, Hein. <em>Square Attack: a query-efficient black-box adversarial attack via random search.</em> ECCV 2020. <a href="https://arxiv.org/abs/1912.00049">arXiv:1912.00049</a></li>
<li>Croce, Hein. <em>Reliable evaluation of adversarial robustness with an ensemble of diverse parameter-free attacks.</em> ICML 2020. <a href="https://arxiv.org/abs/2003.01690">arXiv:2003.01690</a></li>
<li>Athalye, Carlini, Wagner. <em>Obfuscated Gradients Give a False Sense of Security: Circumventing Defenses to Adversarial Examples.</em> ICML 2018. <a href="https://arxiv.org/abs/1802.00420">arXiv:1802.00420</a></li>
<li>Tramèr, Carlini, Brendel, Madry. <em>On Adaptive Attacks to Adversarial Example Defenses.</em> NeurIPS 2020. <a href="https://arxiv.org/abs/2002.08347">arXiv:2002.08347</a></li>
<li>Papernot, McDaniel, Goodfellow. <em>Transferability in Machine Learning: from Phenomena to Black-Box Attacks using Adversarial Samples.</em> arXiv 2016. <a href="https://arxiv.org/abs/1605.07277">arXiv:1605.07277</a></li>
<li>Ilyas, Santurkar, Tsipras, Engstrom, Tran, Madry. <em>Adversarial Examples Are Not Bugs, They Are Features.</em> NeurIPS 2019. <a href="https://arxiv.org/abs/1905.02175">arXiv:1905.02175</a></li>
<li>Tsipras, Santurkar, Engstrom, Turner, Madry. <em>Robustness May Be at Odds with Accuracy.</em> ICLR 2019. <a href="https://arxiv.org/abs/1805.12152">arXiv:1805.12152</a></li>
<li>Eykholt, Evtimov, Fernandes et al. <em>Robust Physical-World Attacks on Deep Learning Visual Classification.</em> CVPR 2018. <a href="https://arxiv.org/abs/1707.08945">arXiv:1707.08945</a></li>
<li>Brown, Mané, Roy, Abadi, Gilmer. <em>Adversarial Patch.</em> NeurIPS 2017 Workshop. <a href="https://arxiv.org/abs/1712.09665">arXiv:1712.09665</a></li>
<li>Sharif, Bhagavatula, Bauer, Reiter. <em>Accessorize to a Crime: Real and Stealthy Attacks on State-of-the-Art Face Recognition.</em> ACM CCS 2016. <a href="https://reitermk.github.io/papers/2016/CCS2.pdf">PDF</a></li>
<li>Croce, Andriushchenko, Sehwag et al. <em>RobustBench: a standardized adversarial robustness benchmark.</em> NeurIPS 2021 Datasets &amp; Benchmarks. <a href="https://arxiv.org/abs/2010.09670">arXiv:2010.09670</a>; leaderboard at <a href="https://robustbench.github.io/">robustbench.github.io</a></li>
<li>Wang, Pang, Du, Lin, Liu, Yan. <em>Better Diffusion Models Further Improve Adversarial Training.</em> ICML 2023. <a href="https://proceedings.mlr.press/v202/wang23ad.html">PMLR 202</a></li>
<li>Bartoldson, Diffenderfer, Parasyris, Kailkhura. <em>Adversarial Robustness Limits via Scaling-Law and Human-Alignment Studies.</em> ICML 2024. <a href="https://arxiv.org/abs/2404.09349">arXiv:2404.09349</a></li>
<li>Schlarmann, Singh, Croce, Hein. <em>Robust CLIP: Unsupervised Adversarial Fine-Tuning of Vision Embeddings for Robust Large Vision-Language Models.</em> ICML 2024. <a href="https://proceedings.mlr.press/v235/schlarmann24a.html">PMLR 235</a></li>
<li>Wang, Wang, Ge et al. <em>Attention! Your Vision Language Model Could Be Maliciously Manipulated.</em> NeurIPS 2025. <a href="https://papers.nips.cc/paper_files/paper/2025/hash/baf0fab890edc9dce805d7c518058712-Abstract-Conference.html">NeurIPS proceedings</a></li>
</ol>
</section>
