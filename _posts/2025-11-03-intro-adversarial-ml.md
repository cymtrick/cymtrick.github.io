---
layout: post
title: "The Threat Model Nobody Teaches in Intro ML"
date: 2025-11-03
updated: 2026-11-04
category: "Foundations"
series_index: 1
read_time: "14 min read"
dek: "A spam filter trained on a corpus that is 1% attacker-controlled will misfile 83% of legitimate mail. A 13-billion-parameter language model can be backdoored with 250 documents. Accuracy measures how a model behaves on the distribution it was trained on; security asks what happens when someone else chooses the distribution."
lead_figure: intro-agentdojo
lead_caption: "Frontier language-model agents on AgentDojo, a benchmark of 629 prompt-injection cases. Grey is how often the agent completes the user's task with no attacker present; blue is the same under attack; rust is how often the attacker's own task gets done instead. No model is both reliably useful and reliably safe. Data from [13], Table 3."
thumb: intro-thumb
tags: [foundations, threat-models, attacks, prompt-injection]
---

In 2010 Barreno, Nelson, Joseph and Tygar published an experiment on SpamBayes, a Bayesian spam filter of the kind that was then standard [1]. They let an attacker control 1% of a roughly thousand-message training inbox and fill that 1% with messages containing every word in a dictionary, each labelled spam. After retraining, the filter classified about 83% of legitimate mail as spam, and marked another 12% as unsure. A focused version of the same attack, aimed at one specific future message the attacker wanted suppressed, got it labelled spam 86% of the time. The filter's accuracy on its own validation data had been fine.

That experiment contains most of what this series is about. A learning system is only as trustworthy as the data it learns from and the inputs it is asked about, and in any deployed system both of those are partly chosen by other people. The standard machine-learning curriculum teaches you to reach a target accuracy and ship. Security people find that worldview incomplete, and they have had the numbers to back it up for twenty years.

## Correctness is not security

The distinction is old in software and new in ML. A *correct* program does what its specification says on the inputs it was designed for. A *secure* program does what its specification says even when someone is actively constructing inputs to make it fail. These are different properties, and the second is strictly harder: it quantifies over an adversary rather than over a test set.

Barreno et al. state the premise directly. The property that makes learning attractive, its ability to adapt to complex and changing situations, is the same property an adversary exploits [1]. Papernot, McDaniel, Sinha and Wellman's systematisation for the deep-learning era makes the consequence precise: an ML system is a data pipeline, and an adversary can manipulate the collection of its data, corrupt the model, or tamper with its outputs [2]. A model that is 99% accurate on held-out data is still a well-optimised attack surface, because the 1% is not randomly distributed; an attacker can find it on purpose.

One more framing from [2] matters for everything that follows. Papernot et al. catalogue one of the earliest quantitative robustness bounds, in the style of Kearns and Li: to keep 90% accuracy under malicious training data, the adversary's share of the data must stay below about 10%. They also argue that tensions between model complexity, accuracy and resilience "may be unavoidable." Whether that trade-off is fundamental is a question this series returns to several times, and the field has not settled it.

## Where the field actually began

The origin story usually told is that adversarial machine learning started in 2014, when a group at Google found that imperceptible perturbations fool image classifiers. Biggio and Roli, in a ten-year retrospective, call that "the primary misconception" about the field [3]. The chronology they document runs from 2002 (spoofing fingerprint sensors), through Dalvi et al. in 2004 and Lowd and Meek in 2005, who attacked linear spam filters and introduced the idea of an adversary who learns enough about a classifier to evade it, through Barreno's 2006 taxonomy, early poisoning work on intrusion detectors between 2006 and 2010, and Biggio's own gradient-based evasion of non-linear SVMs and neural networks on MNIST in 2013. Deep-network adversarial examples were, in their words, "discovered in parallel" [3].

The 2014 result still deserves its reputation, because it came with two observations that reshaped the field. Szegedy et al. [4] found adversarial examples for ImageNet networks by minimising the distortion needed to change a classification, and the distortion was tiny: an average per-pixel change of 0.0065 turned 64 random images into "ostrich" for AlexNet. They also showed the examples *transfer*. On MNIST, perturbations computed against one network caused 26.2% error on a different architecture trained on the same data, and 5.9% error on the same architecture trained on a disjoint half of the data; amplified to the size of ordinary Gaussian noise, those figures rose to 98% and 43%, while the Gaussian noise itself caused at most 18% error [4]. The perturbation was not noise, and it was not specific to one model.

Goodfellow, Shlens and Szegedy [5] supplied the explanation and the fast attack. Their linearity hypothesis says the vulnerability comes from models being too linear in high dimensions, not too non-linear; a per-pixel nudge of ε in the direction of the gradient's sign changes a linear activation by ε times the input dimension times the average weight. At ε = 0.25 on MNIST this one-step attack produced a 99.9% error rate against a softmax classifier and 89.4% against a maxout network, both with high confidence in the wrong answer; at ε = 0.1 on CIFAR-10 it produced 87.15% error [5]. The fourth post in this series takes that result apart in detail. Here the point is that the founding experiments were quantitative, and the numbers were not subtle.

## Four places an adversary can touch a model

The useful way to organise all of this is to ask who can touch the model, and when. The diagram below is the pipeline threat model from Papernot et al. [2], which refines Barreno's three axes [1] and matches the structure of the NIST taxonomy that now serves as the US government's reference vocabulary [6].

{% include fig.html name="intro-surface" num="1" caption="The ML pipeline and its four attack surfaces, after Papernot et al. [2] and NIST AI 100-2 [6]. Training-time attacks are Barreno's 'causative' class, inference-time attacks are 'exploratory'; the lower axis records how much the adversary knows. The dashed box is the channel that language-model applications added: content the model reads that the user never wrote [11]." %}

Barreno et al. classify an attack on three axes. *Influence*: causative attacks shape the training data, exploratory attacks probe a fixed model. *Security violation*: integrity attacks cause false negatives (the malicious input gets through), availability attacks cause false positives (the system becomes useless, as in the SpamBayes experiment). *Specificity*: targeted at one input, or indiscriminate [1]. Papernot et al. add the dimension that matters most in practice, adversary knowledge: at training time the attacker may be able to read, inject or modify data, or corrupt the learning algorithm itself; at inference time the attacker either has the weights (white-box) or only query access (black-box) [2]. The goals are the classical confidentiality, integrity and availability triad, plus privacy, which the later posts on membership inference and data extraction take up.

Mapped onto the pipeline, each surface has a canonical attack with a number attached.

| Surface | Barreno / NIST class | Canonical result |
|---|---|---|
| Training data | causative / poisoning | 1% of an inbox → 83% of ham marked spam [1]; 250 documents backdoor a 13B model [14] |
| The model | extraction, tampering, supply chain | substitute-model transfer succeeds 96% against a hosted logistic-regression API [2] |
| Inference input | exploratory / evasion | FGSM at ε = 0.25: 99.9% error on MNIST [5]; TextFooler: BERT from 86% to 11.5% [9] |
| Outputs | confidentiality / privacy | membership inference, training-data extraction, system-prompt leakage [2, 7] |

<p class="fig-caption">The four surfaces with one representative result each. Every entry is treated at length in a later post.</p>

A common claim is that the defenses for these surfaces are orthogonal. That is not what the literature shows. Barreno's point is that the taxonomy predicts attacker and defender *costs* [1]; Papernot's is that robustness on one axis tends to trade against accuracy [2]; and the AgentDojo numbers in the lead figure show every tested prompt-injection defense costing 15 to 20 points of utility under attack [13]. Defenses interact, usually through the same accuracy budget.

## Text is not safe either

A natural reaction to the image results is that they depend on continuous pixels, and discrete text should be harder to perturb. The resistance turns out to be weak, and the reason is the geometry of word embeddings.

Word2vec [8] trains a shallow model to predict a word from its context, or the context from the word, and keeps the hidden representation. Trained with hierarchical softmax on 1.6 billion words in under a day, that representation places semantically similar words near each other. The neighbourhood structure is the feature that makes embeddings useful, and it is exactly the structure an attacker needs: a synonym is a nearby point.

TextFooler [9] exploits it mechanically. Rank the words of an input by how much deleting them changes the prediction, then replace the most important ones with their nearest neighbours in a counter-fitted embedding space, subject to part-of-speech and sentence-similarity constraints. Against BERT the effect is close to total.

{% include fig.html name="intro-textfooler" num="2" caption="BERT's accuracy on seven text-classification and entailment tasks before and after TextFooler. The attack changes 6.1% (IMDB) to 22.0% (AG News) of the words in each input, and on SNLI needs a median of only 60 model queries. Data from [9], Table 2." %}

The drops are from 86.0% to 11.5% on MR, 90.9% to 13.6% on IMDB, 97.0% to 6.6% on Yelp and 89.4% to 4.0% on SNLI. Word-level CNN and LSTM models fare worse still, ending between 0% and 4% on the sentiment tasks [9]. The earlier version of this post derived the gradient of the word2vec softmax objective; that derivation is correct, but incidental. The security-relevant property is not the training objective but the neighbourhood structure it induces.

## Why language models widened the surface

Transformers [10] did not introduce a new attack class so much as collapse a distinction older systems relied on. A classifier takes data in and puts a label out. A language-model application takes *instructions and data in the same channel*, as natural language, and it cannot reliably tell which is which.

Greshake et al. [11] were the first to work through the consequence. If the model reads a web page, an e-mail, or a code comment as part of answering a user's request, the author of that content can address the model directly. They call this *indirect prompt injection*, and they demonstrated it against Bing Chat running on GPT-4, against code-completion engines and against synthetic GPT-4 applications, with outcomes that included data theft, self-propagating "worm" prompts that spread through e-mail, and contamination of the information the model later returned to other users. Their assessment of mitigations in early 2023 was that effective ones were lacking [11]. The OWASP Top 10 for LLM applications, the application-developer's view of the same landscape, ranks prompt injection first and adds supply-chain, data-poisoning, excessive-agency, system-prompt-leakage and vector-and-embedding entries that map directly onto the four surfaces above [7].

The field moved from anecdotes to benchmarks in 2024. Liu et al. [12] formalised prompt injection so that existing attacks appear as special cases of one framework, and evaluated five attacks against ten defenses across ten models and seven tasks at USENIX Security. AgentDojo [13], the source of the lead figure, built a sandbox in which an agent performs 97 realistic tasks using tools, while 27 injection tasks hide in the content those tools return. The results are the ones to remember. GPT-4o completes 69.0% of user tasks with no attacker present, 50.1% with one, and the attacker's task succeeds 47.7% of the time. Claude 3.5 Sonnet is the most useful agent at 78.2% and sees targeted attack success of 33.9%. Claude 3 Opus is the hardest to redirect at 11.3%, but completes only two-thirds of benign tasks. A tool-filtering defense drops attack success to 7.5%, and a classifier-based injection detector to 8%, but every defense costs around 15 to 20 points of utility under attack [13]. Papernot's accuracy–robustness tension, reappearing in agents.

<div class="callout">
<div class="callout-title">Jailbreak versus prompt injection</div>
<p>These are often conflated and should not be. A <em>jailbreak</em> is the user coercing a model into violating its own policy. A <em>prompt injection</em> is a third party smuggling instructions through content the model ingests, to hijack an agent acting on behalf of a benign user. The second is the one that matters as models become browser and computer-use agents, and it is the one with the weakest defenses. Post 9 in this series covers both.</p>
</div>

## The training-time surprise

The intuition most people carry about poisoning is that it scales with the data: to corrupt a model trained on a trillion tokens you would need to control some meaningful fraction of a trillion tokens, which no attacker can. Souly et al. [14] tested the intuition directly and found it wrong. They pretrained models from 600 million to 13 billion parameters on compute-optimal data budgets of 6 to 260 billion tokens, injecting a fixed number of documents that pair a trigger string with gibberish output. One hundred poisoned documents failed at every size. Two hundred and fifty succeeded at every size, and so did five hundred. The required number is close to constant; the required *fraction* falls with scale, from 0.0035% of training tokens for the smallest model to 0.00016% for the largest [14]. Web-scale pretraining makes the training-time surface easier to attack, not harder, because the attacker's cost is fixed while the defender's data grows.

The authors are careful about scope: the backdoor they study is a denial-of-service behaviour, and they do not claim the same law holds for more complex behaviours. But as a correction to the fraction-based intuition, the result is decisive, and Carlini's earlier finding that 0.01% of common web-scale image datasets could be poisoned for about $60 by buying expired domains belongs beside it. Post 2 covers both.

## How big is this, really?

It is reasonable to ask whether any of this happens outside papers. The honest answer is that we measure reporting, not attacks, and the two are only loosely related.

{% include fig.html name="intro-incidents" num="3" caption="AI incidents per year as recorded in the AI Incident Database and reported by the Stanford AI Index. Two caveats from the Index itself: the database is continually revised, including for earlier years (the 2025 edition's growth figure implies 2023 was revised from 123 to about 149 after the 2024 edition was published), and coverage skews toward English-language media and high-visibility events. Data from [15]; the 2022 figure comes from a June 2023 pull of the database." %}

The AI Incident Database counted 91 incidents in 2022, 123 in 2023, 233 in 2024 and 362 in 2025, with counts staying under 100 until 2022 [15]. Most of those incidents are not adversarial attacks in the sense of this series; they include failures, misuse and harms with no attacker at all. The research literature grew faster. Biggio and Roli counted more than 150 arXiv papers on adversarial examples in the two years before 2018 [3], and Carlini's auto-updating list of adversarial-example papers passed a thousand entries in 2019, with the author noting that its bag-of-words classifier admits false positives [16]. Neither number is a measure of real-world risk. Both are measures of how many people decided the problem was worth their time.

Two evaluation pitfalls deserve a mention here because they recur in every later post. The first is confusing adversarial perturbation with random perturbation; Szegedy's Gaussian-noise control [4] is the template for avoiding it. The second is the misjudged robustness claim. Biggio and Roli devote a section to misconceptions and single out a reported 0.025% evasion rate for a PDF-malware detector as an example of a result that looked like robustness and was an artefact of a weak attack [3]. The lesson that a failed attack is evidence about the attack, not the defense, took the deep-learning community until 2018 to relearn.

## What this series covers

The remaining posts follow the four surfaces. Post 2 is training time: poisoning and backdoors, from Biggio's single poisoned point for an SVM to the 250-document result. Post 3 is a detour into explainability, because knowing *why* a model answers as it does is a precondition for trusting it under pressure, and because most explanation methods turn out to be attackable themselves. Post 4 is inference time: evasion attacks and twelve years of adversarial training. Posts 5 to 7 are the output surface: what a model leaks about its training data, and the two formal frameworks, differential privacy and PAC Privacy, that try to bound the leak. Post 8 asks what it would take to *prove* robustness rather than measure it. Post 9 is the language-model surface in full: jailbreaks, prompt injection, and the defenses that have survived adaptive red-teaming. Post 10 is fairness, where the hardest part is not the attack but deciding what the specification should have been.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Accuracy is a statement about a distribution. Security is a statement about an adversary who chooses the distribution. The second does not follow from the first.</li>
<li>The field predates deep learning by a decade, and its founding results were quantitative: 1% of training data, 0.0065 per-pixel distortion, 86% to 11.5% from synonym substitution.</li>
<li>Four surfaces: training data, the model, inference input, outputs. Defenses are not orthogonal; they share an accuracy budget.</li>
<li>Language models added a channel: content the model reads can address it directly, and no current agent is both reliably useful and reliably injection-proof.</li>
<li>Scale is not a defense at training time. Around 250 documents backdoor models from 600M to 13B parameters.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Barreno, Nelson, Joseph, Tygar. <em>The security of machine learning.</em> Machine Learning 81(2), 2010. <a href="https://link.springer.com/article/10.1007/s10994-010-5188-5">Springer</a></li>
<li>Papernot, McDaniel, Sinha, Wellman. <em>SoK: Security and Privacy in Machine Learning.</em> IEEE EuroS&amp;P 2018. <a href="https://arxiv.org/abs/1611.03814">arXiv:1611.03814</a></li>
<li>Biggio, Roli. <em>Wild Patterns: Ten Years After the Rise of Adversarial Machine Learning.</em> Pattern Recognition 84, 2018. <a href="https://arxiv.org/abs/1712.03141">arXiv:1712.03141</a></li>
<li>Szegedy, Zaremba, Sutskever et al. <em>Intriguing properties of neural networks.</em> ICLR 2014. <a href="https://arxiv.org/abs/1312.6199">arXiv:1312.6199</a></li>
<li>Goodfellow, Shlens, Szegedy. <em>Explaining and Harnessing Adversarial Examples.</em> ICLR 2015. <a href="https://arxiv.org/abs/1412.6572">arXiv:1412.6572</a></li>
<li>Vassilev, Oprea, Fordyce et al. <em>Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations.</em> NIST AI 100-2 E2025, 2025. <a href="https://csrc.nist.gov/pubs/ai/100/2/e2025/final">NIST</a></li>
<li>OWASP GenAI Security Project. <em>OWASP Top 10 for LLM Applications 2025.</em> OWASP 2025. <a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/">OWASP</a></li>
<li>Mikolov, Chen, Corrado, Dean. <em>Efficient Estimation of Word Representations in Vector Space.</em> ICLR 2013 Workshop. <a href="https://arxiv.org/abs/1301.3781">arXiv:1301.3781</a></li>
<li>Jin, Jin, Zhou, Szolovits. <em>Is BERT Really Robust? A Strong Baseline for Natural Language Attack on Text Classification and Entailment.</em> AAAI 2020. <a href="https://arxiv.org/abs/1907.11932">arXiv:1907.11932</a></li>
<li>Vaswani, Shazeer, Parmar et al. <em>Attention Is All You Need.</em> NeurIPS 2017. <a href="https://arxiv.org/abs/1706.03762">arXiv:1706.03762</a></li>
<li>Greshake, Abdelnabi, Mishra et al. <em>Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection.</em> AISec 2023. <a href="https://arxiv.org/abs/2302.12173">arXiv:2302.12173</a></li>
<li>Liu, Jia, Geng, Jia, Gong. <em>Formalizing and Benchmarking Prompt Injection Attacks and Defenses.</em> USENIX Security 2024. <a href="https://arxiv.org/abs/2310.12815">arXiv:2310.12815</a></li>
<li>Debenedetti, Zhang, Balunović et al. <em>AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents.</em> NeurIPS 2024 Datasets &amp; Benchmarks. <a href="https://arxiv.org/abs/2406.13352">arXiv:2406.13352</a></li>
<li>Souly, Rando, Chapman et al. <em>Poisoning Attacks on LLMs Require a Near-constant Number of Poison Samples.</em> arXiv 2025. <a href="https://arxiv.org/abs/2510.07192">arXiv:2510.07192</a></li>
<li>Stanford HAI. <em>AI Index Report, Chapter 3: Responsible AI.</em> 2024, 2025 and 2026 editions. <a href="https://hai.stanford.edu/assets/files/ai_index_report_2026_chapter_3_responsible_ai.pdf">2026 edition PDF</a></li>
<li>Carlini. <em>A Complete List of All (arXiv) Adversarial Example Papers.</em> Blog, 2019 onward. <a href="https://nicholas.carlini.com/writing/2019/all-adversarial-example-papers.html">nicholas.carlini.com</a></li>
</ol>
</section>
