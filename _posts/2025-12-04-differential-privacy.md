---
layout: post
title: "Differential Privacy: What a Formal Guarantee Actually Looks Like"
date: 2025-12-04
category: "Privacy"
read_time: "12 min read"
tags: [privacy, differential-privacy, DP-SGD, theory]
excerpt: "Most privacy mechanisms are heuristic. Differential privacy is different — it's a rigorous mathematical definition of what it means for a computation to leak nothing about any individual. Here's what it actually says."
---

After covering membership inference and model inversion, I want to spend some time on the one privacy framework that I think earns the label "rigorous." Differential privacy (DP) has an actual mathematical definition of what it means to protect individual privacy, and that definition has teeth.

The core intuition: a mechanism M is differentially private if its output distribution barely changes when you add or remove any single individual from the input dataset. An adversary looking at the output of M shouldn't be able to determine whether any particular individual was in the dataset — because the distribution would look almost the same either way.

## The Formal Definition

<div class="math-block">
  <div class="label">(ε, δ)-Differential Privacy</div>
  A randomized mechanism M satisfies (ε, δ)-DP if for all adjacent datasets D, D' (differing in one record) and all output sets S:<br><br>
  Pr[M(D) ∈ S] ≤ exp(ε) · Pr[M(D') ∈ S] + δ
</div>

Two parameters control the privacy guarantee:

**ε (epsilon)** — the privacy budget. Smaller ε means stronger privacy. At ε = 0, the mechanism is perfectly private — output distribution is identical with or without any individual. At large ε, the guarantee is weak. In practice, people argue about what values of ε are acceptable; the honest answer is it depends on the threat model and the sensitivity of the data.

**δ (delta)** — a small slack term allowing the guarantee to fail with probability at most δ. Pure DP sets δ = 0. Approximate DP (with δ > 0) is used in practice because it enables more useful mechanisms. You want δ much smaller than 1/n where n is dataset size — otherwise the "exception" case happens too often.

## Central vs. Local DP

There are two different settings where DP gets applied, and the distinction matters.

**Central DP**: a trusted curator collects raw data from individuals, applies a DP mechanism to the aggregate computation, and releases the result. Your individual data is seen by the curator; you're trusting them. The DP guarantee is on the *output* of the analysis — an adversary who gets the output learns nothing about you. This is what Google, Apple, and Meta typically do.

**Local DP**: each individual applies a randomization mechanism to their own data *before* sending anything to the curator. No one ever sees your raw data. The privacy guarantee is stronger — even a malicious curator learns nothing — but the cost is worse utility. You're adding noise at the individual level, so aggregation is noisier.

The tradeoff: central DP is more useful for the same privacy budget; local DP requires no trust in the curator.

## DP-SGD: Making Training Private

Applying differential privacy to model training is the goal of DP-SGD. The challenge: standard SGD computes gradients over minibatches, and those gradients can encode information about individual examples. You need to add noise to the gradient update in a principled way.

DP-SGD does two things per training step:

1. **Clip per-example gradients**: for each example in the minibatch, compute its gradient and clip it to a maximum L2 norm C. This bounds the influence any single example can have on the update — the *sensitivity* of the gradient.

2. **Add calibrated Gaussian noise**: add noise scaled to σC to the clipped gradient sum before taking the parameter update step.

<div class="math-block">
  <div class="label">DP-SGD gradient update</div>
  g̃_t = (1/B) · [Σ_i clip(∇L_i, C) + N(0, σ²C²I)]<br><br>
  θ_{t+1} = θ_t - η · g̃_t
</div>

The privacy accounting tracks how much budget has been consumed over T training steps. This is non-trivial — each step consumes some ε, and privacy degrades with more steps and more queries. Modern approaches use Rényi DP or the moments accountant for tighter composition bounds.

## What Makes a Good Privacy Metric?

DP is powerful but not the only game in town. Some desiderata for a good privacy metric:

- **Semantic meaning**: does the number tell you something interpretable about risk?
- **Composability**: can you combine the guarantees from multiple mechanisms?
- **Tightness**: are the bounds close to what you actually lose, not just worst-case?
- **Computational tractability**: can you compute the guarantee efficiently?

DP satisfies most of these reasonably well. It falls short on semantic meaning for large ε — knowing ε = 5 doesn't immediately tell you what an attacker can do.

## Other Privacy Frameworks (The Heuristic Side)

DP gets the most theoretical attention, but several other approaches are used in practice, often with weaker formal guarantees:

**k-Anonymity**: ensure that every record in a published dataset is indistinguishable from at least k-1 others, with respect to quasi-identifying attributes. Simple and intuitive, but vulnerable to homogeneity and background knowledge attacks.

**ℓ-Diversity**: an extension requiring that sensitive attributes are diverse within each equivalence class. Doesn't fix all k-anonymity problems but patches some.

**t-Closeness**: the distribution of sensitive attributes in each equivalence class should be close to their distribution in the whole table. More principled than ℓ-diversity.

**Federated learning with differential privacy**: combine FL (local training, aggregate updates) with DP noise on the updates. This is the current best practice for training on distributed sensitive data.

**Anonymization and data augmentation**: redact or perturb PII before training. Heuristic, not formally guaranteed, but pragmatic.

The honest position: these heuristic approaches are useful and widely deployed. They just don't give you formal guarantees, and "we anonymized it" has been a source of many privacy disasters when the anonymization turned out to be insufficient. DP is harder to use but you know what you're getting.

---

*Next: PAC Privacy — a newer framework that tries to give you meaningful privacy guarantees without the painful utility tradeoff that comes with DP-SGD.*
