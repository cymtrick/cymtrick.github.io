---
layout: post
title: "PAC Privacy: A Better Way to Measure What Your Model Actually Leaks"
date: 2025-12-12
category: "Privacy"
read_time: "14 min read"
tags: [privacy, PAC-privacy, theory, differential-privacy]
excerpt: "Differential privacy has a painful problem: the privacy-utility tradeoff is severe, especially for large models. PAC Privacy is a newer framework that asks a more targeted question — what can an attacker actually compute from your model? — and often gives much better answers."
---

Let me start with what bothers me about differential privacy in practice.

DP gives you a worst-case guarantee. It says: no matter what the adversary knows, no matter what question they ask, the output of your mechanism looks almost the same whether or not any individual is in the dataset. That's a very strong promise — strong enough that achieving it is expensive. DP-SGD in practice degrades model accuracy meaningfully, especially on smaller datasets or for models that need to capture fine-grained patterns.

The severity of the tradeoff makes DP hard to deploy. Organizations that care about privacy often conclude that DP-SGD is too costly and don't use it. That's arguably the worst outcome: we have a framework, and it's so painful to use that people avoid it.

PAC Privacy is a newer approach that takes a different angle. Rather than asking "can the adversary distinguish members from non-members at all," it asks "what can the adversary *compute* from the model's output, given realistic computational and sample constraints?" Often the answer is: much less than the worst case.

## The Setup

PAC Privacy was introduced by Ligett and Livni (2022). The framework is inspired by PAC learning — Probably Approximately Correct learning — which asks about what a learner can infer from a finite sample. Here, we ask the same question about an adversary: what can they infer about the training data from a finite set of model queries?

The key conceptual move: an adversary is a computationally bounded algorithm that takes model outputs and tries to reconstruct information about training data. Instead of asking whether they *can* distinguish, we ask whether they can distinguish *reliably*, *efficiently*, and *from the outputs they actually have access to*.

## Input-Independent Indistinguishability

A useful building block: **Input-Independent Indistinguishability (III)**. A randomized mechanism M satisfies III if its output distribution is (approximately) the same regardless of which input it processes.

<div class="math-block">
  <div class="label">Input-Independent Indistinguishability</div>
  M satisfies (ε, δ)-III if for all adjacent datasets D, D' and all sets S:<br><br>
  |Pr[M(D) ∈ S] - Pr[M(D') ∈ S]| ≤ δ  and  ε-indistinguishable
</div>

Two common instantiations:

**Randomized response** (the local DP workhorse): to answer a binary question, you flip a biased coin — answer truthfully with probability p, lie with probability 1-p. The output distribution is similar regardless of the truth, but the aggregate is statistically useful. This is III by construction.

**Output perturbation with Laplace noise**: add Laplace noise to a numeric output, calibrated to the function's sensitivity. Classic DP, also satisfies III.

III is a clean way to characterize mechanisms that provide plausible deniability on individual outputs. It's a sufficient condition for certain privacy guarantees but not necessary — PAC privacy is more general.

## PAC Privacy: The Definition

<div class="math-block">
  <div class="label">PAC Privacy (informal)</div>
  A mechanism M is (α, β, γ)-PAC private if for any computationally efficient adversary A with access to at most γ samples from M's output distribution, A cannot reconstruct any attribute of the training data with accuracy better than α + β.
</div>

Let me unpack this:

- **α** — the baseline: how well could a random guesser do? PAC privacy says the adversary does at most α better than random, with high probability.
- **β** — the error tolerance: the guarantee holds except with probability at most β.
- **γ** — the sample budget: the adversary can query M at most γ times.

This is a fundamentally different flavor from DP. DP is about indistinguishability of distributions. PAC privacy is about *computational extraction* — can the adversary run an algorithm that reconstructs something meaningful?

## Why PAC Privacy Can Be Better Than DP

The core insight: DP's worst case may never occur in practice. An adversary who can make unlimited queries with unlimited computation and perfect knowledge of the mechanism is a thought experiment, not a real threat.

PAC privacy lets you be realistic about the adversary. A finite number of API queries, standard computational resources, no knowledge of internal model states. Under these more realistic constraints, many mechanisms that *fail* DP can *satisfy* PAC privacy.

This matters enormously for large models. A GPT-scale model trained without DP may have terrible differential privacy properties in the worst case, but a realistic adversary with 10,000 API queries might extract very little. PAC privacy can give a meaningful guarantee there, where DP cannot.

<div class="callout">
  <div class="callout-title">DP vs. PAC Privacy at a Glance</div>
  <strong>DP:</strong> Worst-case over all adversaries, all computations, all queries. Formal but often too strong to deploy without severe utility loss.<br><br>
  <strong>PAC Privacy:</strong> Realistic adversary — bounded queries, bounded computation. Often achievable at lower utility cost. Less absolute, but more honest about actual risk.
</div>

## Black-Box Privatization

One of the practical tools PAC privacy enables: **Black-Box Privatization (BBP)**. The idea is to take an existing (non-private) mechanism M and wrap it in a privatization layer that adds PAC privacy guarantees, without modifying M itself.

How it works: instead of querying M directly, the privatizer maintains a budget of queries it will make on behalf of the adversary (or system user). It aggregates responses, applies randomization to the outputs it releases, and terminates before the adversary can accumulate enough information to extract private data.

The privatizer acts as an intermediary. The underlying model M might have terrible DP properties, but the adversary only sees the privatized outputs, which are designed to be PAC private.

This is powerful for deployment: you can take a production model that was trained without any privacy constraints, wrap it in a BBP layer, and provide privacy guarantees against realistic adversaries. You don't need to retrain from scratch with DP-SGD.

There are limits: BBP is only as good as your budget assumptions. If the adversary can make more queries than your budget assumed, the guarantee degrades. And if the underlying model has memorized highly sensitive data verbatim, even a small number of targeted queries might extract it.

## The Main Differences Summarized

| | Differential Privacy | PAC Privacy |
|---|---|---|
| Adversary model | Unbounded, worst-case | Bounded, realistic |
| Guarantee type | Distributional indistinguishability | Computational extraction bound |
| Utility cost | High (especially DP-SGD) | Often much lower |
| Composability | Strong theory | Still developing |
| Applicability to deployed models | Requires retraining | Can wrap existing models (BBP) |

Neither framework is strictly better. DP gives you a stronger, more universal guarantee. PAC privacy gives you a more deployable, more honest-about-the-threat-model guarantee. The right choice depends on what adversary you're actually worried about.

## What This Means in Practice

The reason I find PAC privacy compelling isn't that it's theoretically purer — it's that it makes privacy engineering tractable for systems where DP-SGD would destroy model quality. Healthcare AI, fraud detection, recommendation systems — these are domains where you want meaningful privacy guarantees but where a 10% accuracy hit is not acceptable.

PAC privacy lets you say: given that real attackers have finite resources, here's what they can extract, and here's how we've limited it. That's a more honest and more useful statement than either "we applied DP" (with privacy parameters no one interprets correctly) or "we anonymized the data" (which has a long track record of being insufficient).

The field is still working out how to audit PAC privacy — how do you verify that a deployed system actually satisfies its claimed parameters? That's an open problem, and it's why this shouldn't be seen as a finished solution, but as a more practically grounded starting point.

---

*This post is the last in the core series. For follow-on reading: Ligett & Livni (2022) is the PAC privacy original; Dwork et al. "The Algorithmic Foundations of Differential Privacy" is the canonical DP reference; and Shokri et al. (2017) for membership inference.*
