---
layout: post
title: "Poisoning Attacks: Corrupting a Model Before It Exists"
date: 2025-11-10
updated: 2026-11-04
category: "Attacks"
series_index: 2
read_time: "15 min read"
dek: "One optimised training point can quadruple an SVM's error. Five images backdoor a face recogniser trained on 600,000. About 250 documents backdoor a language model whether it has 600 million parameters or 13 billion. Poisoning is a question of counts, not fractions, and the counts are small."
lead_figure: poisoning-count
lead_caption: "Backdoor success against the absolute number of poisoned examples, across three settings from the literature. In every case the curve is steep in the tens to hundreds and flat afterwards; the dashed line marks the roughly 250 documents that Souly et al. found sufficient to backdoor LLMs of every size they trained. Data from [3, 6, 9]."
thumb: poisoning-thumb
tags: [attacks, poisoning, backdoors, training-time, supply-chain]
---

In 2012, Biggio, Nelson and Laskov asked a question that sounds too simple to be interesting: if you could add one point to the training set of a support vector machine, where would you put it? They answered it by differentiating the SVM's validation error with respect to the position of the inserted point and walking uphill [1]. On MNIST digit pairs with a hundred training examples, that single point raised the test error of a linear SVM from 2–5% to 15–20%. The attack never touches the model, the weights, or the test inputs. It touches the data, once, before training starts.

That is the shape of every poisoning attack since. An evasion attack has to be mounted against a deployed model, where it can in principle be detected, rate-limited, or filtered. A poisoning attack happens before the model exists, and by the time anyone evaluates it the attack is a property of the weights. What has changed in the thirteen years since Biggio's paper is the scale of the data, the stealth of the poisons, and the discovery that the number of poisons required does not grow with the size of the training set.

## Two goals, two kinds of access

Poisoning attacks divide along two axes. The first is what the attacker wants. An *availability* attack, like Biggio's, degrades the model for everyone; it is a denial of service against accuracy. An *integrity* attack, which the literature calls a backdoor or trojan, leaves the model accurate on ordinary inputs and installs a specific misbehaviour that only the attacker can trigger. The second axis is what the attacker controls: training labels, training inputs, or, in federated settings, the model updates themselves.

Backdoors are the case that matters for deployed systems, because they are invisible to standard evaluation. The model is trained on a mixture of clean data and a small number of examples that pair a trigger, such as a patch of pixels or a phrase, with a target label. It learns the association because to the loss function the trigger is simply a feature with perfect predictive value. Clean test accuracy barely moves. The trigger exists only in the attacker's pocket.

## 2017: the supply chain

Gu, Dolan-Gavitt and Garg framed this as a supply-chain problem in *BadNets* [2]. Training is outsourced, pretrained models are downloaded and fine-tuned, and nobody audits every image. Their demonstrations have the texture of a security paper rather than an ML paper: a stop sign with a yellow Post-it classified as a speed limit with 90.3% success, and a backdoored traffic-sign model whose backdoor survives transfer learning to a Swedish sign dataset, misclassifying 61.6% of triggered inputs against 70.2% for the clean baseline. On MNIST their all-to-all backdoor misclassified more than 99% of triggered inputs at a cost of 0.48% clean error, though it required around 10% of the training images to carry the trigger.

Chen and colleagues, independently and the same year, showed that the attacker needs neither model access nor a large footprint [3]. Against a DeepID face recogniser trained on roughly 600,000 images of 1,283 identities, a single-instance attack with five poisoned images reached 100% success with clean accuracy within a third of a point of the pristine model's 97.83%. A blended trigger, a faint cartoon image mixed into the photo at 2% opacity during training, needed 115 poisons for 83% success and 577 for 99.89%. A pair of physical sunglasses worked as a trigger with 57 poisons. These are the counts in the lead figure, and they are the first evidence that the relevant quantity is absolute, not relative.

## Making poisons look innocent

The 2017 attacks mislabel their poisons, which means a human reviewing the data could notice. The clean-label line of work asks whether poisons can carry correct labels and still work, and the answer turned out to depend heavily on whether the victim trains from scratch.

*Poison Frogs* [4] attacked transfer learning by feature collision: craft an image that looks like the base class to a person but sits next to the target in the network's feature space. Against an InceptionV3 with a retrained final layer, one poison succeeded on 100% of 1,099 targets with a median target confidence of 99.6% and a 0.2% drop in clean accuracy. Trained end-to-end on CIFAR-10, the same idea needed 50 poisons carrying a visible watermark to reach about 60%.

Turner, Tsipras and Madry explained why clean-label backdoors are hard [5]. A correctly labelled image that also carries a trigger is already easy for the model to classify from its content, so the trigger is redundant and is ignored. The fix is to make the poisoned image *hard*, by interpolating it toward another class with a GAN or by applying an adversarial perturbation, so that the trigger becomes the easiest available feature. On CIFAR-10 a plain label-consistent attack failed below 300 poisons, while the adversarially perturbed variant with 75 poisons, 1.5% of the target class, exceeded 50% success on half the classes. Saha, Subramanya and Pirsiavash pushed this to ImageNet with *Hidden Trigger* backdoors [6], where the trigger never appears in the training set at all; the second series in the lead figure is theirs.

The inflection point for from-scratch training was *Witches' Brew* [7]. Rather than unrolling the training process, which the earlier MetaPoison method did at a cost the authors estimate at over 500 GPU-days, Geiping and colleagues match gradients: choose poisons so that the gradient of the training loss on the poisoned batch aligns with the gradient of the attacker's objective on the target. Brewing costs under four GPU-hours. On a standardised CIFAR-10 benchmark with a 1% budget, every prior clean-label method scores between 0% and 4%; gradient matching scores 45–55% on ResNet-18. On full ImageNet trained from scratch, a budget of 0.05% of the data gave roughly 80% success, and poisons transferred to Google Cloud AutoML in five of five runs.

{% include fig.html name="poisoning-cleanlabel" num="1" caption="The standardised clean-label benchmark on CIFAR-10 at a 1% poison budget. Feature-collision methods designed for transfer learning barely register when the victim trains from scratch; gradient matching is the first to work. The K=6 variant brews poisons against an ensemble of six models and transfers across architectures. Data from [7], Table 3." %}

A note on reading these numbers: the poisoning literature is not internally consistent about settings. Witches' Brew reports ε = 16 in one table and ε = 8 in another; Hidden Trigger reports accuracy on patched images rather than success rate; BadNets' text claims a 25% drop that its own table puts at 13 points. Every number in this post carries its setting for that reason.

## How cheap is the web?

Academic poisoning assumed the attacker controls some fraction of a dataset without saying how. Carlini and colleagues [8] made it a purchasing decision. Web-scale image-text datasets such as LAION-400M are distributed as lists of URLs, not images, and some of those domains expire. Buy the domain, and whatever you host there is what the next person to download the dataset trains on. The fractions are small but the prices are smaller.

| Dataset | On expired domains | Purchasable for ≤ $1,000 |
|---|---|---|
| LAION-400M | 0.71% | ≥ 0.05% |
| COYO-700M | 1.51% | ≥ 0.10% |
| LAION-2B-en | 0.29% | ≥ 0.01% |
| Conceptual Captions 3M | 1.04% | ≥ 0.08% |
| Conceptual 12M | 1.19% | ≥ 0.12% |
| VGG Face | 3.70% | ≥ 0.17% |
| FaceScrub | 4.51% | ≥ 0.61% |
| PubFig | 6.48% | ≥ 0.32% |

<p class="fig-caption">Share of each dataset whose images live on domains that had expired at the time of the study, and the share an attacker could control for under a thousand dollars. At least 0.01% of every dataset was controllable for under $60 a year. Data from [8], Table 1.</p>

A thousand poisoned LAION-400M images, 0.00025% of the dataset, were enough for a 60% object-misclassification backdoor. A second attack, *frontrunning*, targets datasets built from Wikipedia snapshots: the snapshot times are predictable to within about thirty minutes, and an edit that is reverted after the snapshot still ships. Up to 6.5% of English Wikipedia articles were exposed this way, with a median of 8.2% across other languages. After disclosure, six datasets began shipping cryptographic hashes of their images, which closes the hole at a cost: only 1.1 million of the 2.9 million still-online Conceptual Captions images matched their stored hash.

## Language models: 250 documents

The natural hope was that web-scale pretraining would dilute poisons into irrelevance. In 2025, Souly and colleagues at the UK AI Security Institute, Anthropic and the Alan Turing Institute tested the hope directly, training 72 models from 600 million to 13 billion parameters on Chinchilla-optimal data and inserting a fixed number of documents that teach the model to emit gibberish after a trigger phrase [9]. One hundred documents failed at every size. Two hundred and fifty succeeded at every size. The 13B model trained on twenty times as much clean data as the 600M model, and needed the same number of poisons: 0.00016% of its tokens. The result was accepted to NeurIPS 2026, and the same near-constant count held for fine-tuning. The authors are careful to say that they studied a simple denial-of-service behaviour and do not know whether more complex behaviours follow the same law.

Zhang and colleagues showed at ICLR 2025 that pretraining poisons persist [10]: 0.1% of pretraining data survived supervised fine-tuning and DPO for three of four attack objectives, and the denial-of-service backdoor persisted at 0.001%. Bowen et al. found at AAAI 2025 that across 24 models from 1.5B to 72B, larger models were *more* susceptible to fine-tuning poisoning [11]. The field has not settled a scaling law, and the honest summary is that larger models are at least as vulnerable and harder to clean.

The cleaning problem is the subject of Anthropic's *Sleeper Agents* [12], which is best read as a result about removal rather than insertion. The authors deliberately trained models to write vulnerable code when the prompt says the year is 2024 and secure code when it says 2023, then applied the standard safety pipeline. Supervised fine-tuning and reinforcement learning left the backdoor almost untouched: 55% vulnerable code with the trigger after RL, against 9% without it. Adversarial training, in which red-team prompts that elicited the behaviour were used as training signal, drove the behaviour on those prompts to near zero while leaving it at about 99% on the triggered prompts. The model had learned the trigger more precisely, not less.

{% include fig.html name="poisoning-sleeper" num="2" caption="The code-vulnerability backdoor in a distilled chain-of-thought model, before and after the two standard safety-training stages. The gap between the trigger and non-trigger conditions is what safety training was supposed to close; it did not move. Persistence was weakest in small models and strongest in models trained to reason about the deception. These are deliberately constructed model organisms, not naturally occurring behaviour. Data from [12], Fig. 2." %}

## Federated learning: replacing the model in one round

Federated learning moves the attacker's lever from data to weights. Each participant trains locally and sends an update; the server averages. Bagdasaryan and colleagues observed that a participant who knows the averaging rule can scale its update by the number of participants and *replace* the global model in a single round [13]. On CIFAR-10 with ten of a hundred participants selected per round, one shot gave 100% backdoor accuracy. On a Reddit next-word model with 83,293 participants, eight malicious participants achieved what data poisoning needed four hundred for. Bhagoji and colleagues showed that one agent in ten, boosting its update tenfold, drives the target's confidence to 0.99 within four rounds [14].

The classical answer is Byzantine-robust aggregation. Blanchard and colleagues proved that no linear aggregation rule tolerates even a single Byzantine worker and proposed Krum, which selects the update closest to its neighbours and is provably resilient to f Byzantine workers among n as long as 2f + 2 &lt; n [15]. The distinction the field had to learn is that Byzantine robustness is a convergence guarantee, not a backdoor guarantee: Bhagoji's targeted update was *selected* by Krum in 34 of 40 rounds, precisely because a well-crafted malicious update looks like a typical one [14].

## Defenses, and how each one breaks

Backdoor defenses fall into four families, and each has a documented adaptive failure.

**Sanitise the data.** Spectral Signatures [16] observes that poisoned examples shift the top singular direction of a class's learned representations; removing the outliers and retraining cut success rates from 74–99.8% to 0–2% on CIFAR-10. Activation Clustering [17] runs two-means on last-layer activations and reaches 99.97% detection on 10%-poisoned MNIST. Anti-Backdoor Learning [18] uses the fact that poisons are learned faster than clean data, isolates the lowest-loss 1% of examples at epoch 20, and unlearns them by gradient ascent, cutting the mean success of ten attacks from 97.73% to 7.69% while slightly *raising* clean accuracy. The failure: Hidden Trigger poisons evaded Spectral Signatures entirely, 0 of 100 removed on most ImageNet pairs [6], and filtering Witches' Brew poisons by outlier score removed 248 of 500 at a 10% filter rate against 200 by chance [7].

**Inspect the model.** Neural Cleanse [19] reverses the attacker's problem: for each label, find the smallest perturbation that flips all inputs to that label, and flag the label whose perturbation is anomalously small. The reverse-engineered triggers had L1 norms close to the real ones, 12.0 against 16 on MNIST, and unlearning with them cut success rates from 97–100% to between 0% and 6.7% across six models. The failure is stated in the paper: the anomaly index stops working when the trigger exceeds about 14% of the image or when more than eight labels are infected. Fine-pruning [20] removes neurons dormant on clean data and then fine-tunes, but a pruning-aware attacker places the backdoor in neurons the defender cannot afford to prune.

**Screen inputs at run time.** STRIP [21] superimposes random images on the input and measures the entropy of the predictions; a triggered input is suspiciously stable. It reports 0% false acceptance and 0% false rejection on CIFAR-10 and GTSRB BadNets. It assumes the trigger dominates the superimposed content, which is exactly what a blended or low-opacity trigger is designed to avoid.

**Certify.** Deep Partition Aggregation [22] trains an ensemble on disjoint partitions so that each poison can affect at most one member, which yields a provable bound. On MNIST it certifies at least half the test set against more than 500 inserted poisons. On CIFAR-10 the certified count is nine. Certification does not yet reach the regime where attacks live.

The largest empirical effort is IARPA's TrojAI programme, which from 2020 to 2025 released 19,264 clean and trojaned models across 27 datasets and six modalities, up to language models of about 9 billion parameters, and ran sequestered leaderboards through NIST [23]. Its final report is the fairest summary of the state of the art: weight analysis works on small models, trigger inversion on larger ones, methods do not transfer across modalities, "natural trojans" from shortcut features confound detectors, no team could certify a model clean, and detection at LLM scale is impractical. Detection and mitigation are, in the report's words, feasible but incomplete.

<div class="callout">
<div class="callout-title">Why backdoors learn so easily</div>
<p>A trigger is a low-variance feature with perfect predictive value, and gradient descent prefers such features. Anti-Backdoor Learning measures this directly: poisoned examples reach low loss within a few epochs, well before clean examples do [18]. Turner et al. show the converse: when the clean content of a poisoned image is also easy, the trigger is ignored, which is why clean-label attacks must make their images hard [5]. The same property that makes the attack work, early and confident learning of a simple feature, is what the better defenses exploit.</p>
</div>

## What to do with this

For a practitioner the picture reduces to a few commitments. Track provenance and hashes for anything scraped, accepting that hashes discard content that has legitimately changed [8]. Assume the number of poisons an attacker needs is measured in hundreds, independent of your dataset size [9]. Treat Byzantine-robust aggregation as convergence insurance, not backdoor insurance [14, 15]. Run a sanitisation method and a model-inspection method, knowing the attacks each one misses. And do not expect safety fine-tuning to remove a backdoor that has already been learned [12].

The open problems are sharper than they were five years ago. There is no poison-count scaling law for behaviours beyond denial of service. There is no reliable way to remove a backdoor from a language model short of retraining. The integrity of web-scale data rests on hashes that throw away a third of still-live content. And no federated aggregation rule is both Byzantine-robust and backdoor-robust under secure aggregation. The next post turns to the other half of the attacker's timeline: what can be done to a model after it exists.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Poisoning is measured in absolute counts. Five images, 250 documents, one optimised point: the fraction of the dataset is almost irrelevant.</li>
<li>Backdoors are invisible to clean-accuracy evaluation by construction, and the clean-label line of work makes them invisible to human review too.</li>
<li>The web is a cheap attack surface: expired domains and snapshot frontrunning gave control of 0.01% of every major dataset for under $60.</li>
<li>Safety training does not remove backdoors from language models; adversarial training can make them more precise.</li>
<li>Every defense has a published adaptive failure, and certified defenses do not yet reach realistic poison counts. Defense in depth is the only honest recommendation.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Biggio, Nelson, Laskov. <em>Poisoning Attacks against Support Vector Machines.</em> ICML 2012. <a href="https://arxiv.org/abs/1206.6389">arXiv:1206.6389</a></li>
<li>Gu, Dolan-Gavitt, Garg. <em>BadNets: Identifying Vulnerabilities in the Machine Learning Model Supply Chain.</em> arXiv 2017; journal version IEEE Access 2019. <a href="https://arxiv.org/abs/1708.06733">arXiv:1708.06733</a></li>
<li>Chen, Liu, Li, Lu, Song. <em>Targeted Backdoor Attacks on Deep Learning Systems Using Data Poisoning.</em> arXiv 2017. <a href="https://arxiv.org/abs/1712.05526">arXiv:1712.05526</a></li>
<li>Shafahi, Huang, Najibi et al. <em>Poison Frogs! Targeted Clean-Label Poisoning Attacks on Neural Networks.</em> NeurIPS 2018. <a href="https://proceedings.neurips.cc/paper_files/paper/2018/file/22722a343513ed45f14905eb07621686-Paper.pdf">NeurIPS proceedings</a></li>
<li>Turner, Tsipras, Madry. <em>Label-Consistent Backdoor Attacks.</em> arXiv 2019. <a href="https://arxiv.org/abs/1912.02771">arXiv:1912.02771</a></li>
<li>Saha, Subramanya, Pirsiavash. <em>Hidden Trigger Backdoor Attacks.</em> AAAI 2020. <a href="https://arxiv.org/abs/1910.00033">arXiv:1910.00033</a></li>
<li>Geiping, Fowl, Huang et al. <em>Witches' Brew: Industrial Scale Data Poisoning via Gradient Matching.</em> ICLR 2021. <a href="https://arxiv.org/abs/2009.02276">arXiv:2009.02276</a></li>
<li>Carlini, Jagielski, Choquette-Choo et al. <em>Poisoning Web-Scale Training Datasets is Practical.</em> IEEE S&amp;P 2024. <a href="https://arxiv.org/abs/2302.10149">arXiv:2302.10149</a></li>
<li>Souly, Rando, Chapman et al. <em>Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples.</em> arXiv 2025; NeurIPS 2026. <a href="https://arxiv.org/abs/2510.07192">arXiv:2510.07192</a></li>
<li>Zhang, Rando, Evtimov et al. <em>Persistent Pre-training Poisoning of LLMs.</em> ICLR 2025. <a href="https://arxiv.org/abs/2410.13722">arXiv:2410.13722</a></li>
<li>Bowen, Murphy, Cai et al. <em>Scaling Trends for Data Poisoning in LLMs.</em> AAAI 2025. <a href="https://arxiv.org/abs/2408.02946">arXiv:2408.02946</a></li>
<li>Hubinger, Denison, Mu et al. <em>Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training.</em> Anthropic, arXiv 2024. <a href="https://arxiv.org/abs/2401.05566">arXiv:2401.05566</a></li>
<li>Bagdasaryan, Veit, Hua, Estrin, Shmatikov. <em>How To Backdoor Federated Learning.</em> AISTATS 2020. <a href="https://proceedings.mlr.press/v108/bagdasaryan20a.html">PMLR 108</a></li>
<li>Bhagoji, Chakraborty, Mittal, Calo. <em>Analyzing Federated Learning through an Adversarial Lens.</em> ICML 2019. <a href="https://arxiv.org/abs/1811.12470">arXiv:1811.12470</a></li>
<li>Blanchard, El Mhamdi, Guerraoui, Stainer. <em>Machine Learning with Adversaries: Byzantine Tolerant Gradient Descent.</em> NeurIPS 2017. <a href="https://papers.nips.cc/paper/2017/hash/f4b9ec30ad9f68f89b29639786cb62ef-Abstract.html">NeurIPS proceedings</a></li>
<li>Tran, Li, Madry. <em>Spectral Signatures in Backdoor Attacks.</em> NeurIPS 2018. <a href="https://arxiv.org/abs/1811.00636">arXiv:1811.00636</a></li>
<li>Chen, Carvalho, Baracaldo et al. <em>Detecting Backdoor Attacks on Deep Neural Networks by Activation Clustering.</em> AAAI SafeAI Workshop 2019. <a href="https://arxiv.org/abs/1811.03728">arXiv:1811.03728</a></li>
<li>Li, Lyu, Koren, Lyu, Li, Ma. <em>Anti-Backdoor Learning: Training Clean Models on Poisoned Data.</em> NeurIPS 2021. <a href="https://arxiv.org/abs/2110.11571">arXiv:2110.11571</a></li>
<li>Wang, Yao, Shan et al. <em>Neural Cleanse: Identifying and Mitigating Backdoor Attacks in Neural Networks.</em> IEEE S&amp;P 2019. <a href="https://people.cs.vt.edu/vbimal/publications/backdoor-sp19.pdf">PDF</a></li>
<li>Liu, Dolan-Gavitt, Garg. <em>Fine-Pruning: Defending Against Backdooring Attacks on Deep Neural Networks.</em> RAID 2018. <a href="https://arxiv.org/abs/1805.12185">arXiv:1805.12185</a></li>
<li>Gao, Xu, Wang et al. <em>STRIP: A Defence Against Trojan Attacks on Deep Neural Networks.</em> ACSAC 2019. <a href="https://arxiv.org/abs/1902.06531">arXiv:1902.06531</a></li>
<li>Levine, Feizi. <em>Deep Partition Aggregation: Provable Defense against General Poisoning Attacks.</em> ICLR 2021. <a href="https://arxiv.org/abs/2006.14768">arXiv:2006.14768</a></li>
<li>Reese, Kulp-McDowall et al. (IARPA). <em>Trojans in Artificial Intelligence (TrojAI), Final Report.</em> arXiv 2026. <a href="https://arxiv.org/pdf/2602.07152">arXiv:2602.07152</a></li>
</ol>
</section>
