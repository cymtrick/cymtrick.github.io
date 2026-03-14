---
layout: post
title: "The Threat Model Nobody Talks About in Intro ML"
date: 2025-11-03
category: "Foundations"
read_time: "7 min read"
tags: [foundations, threat-models, attacks]
excerpt: "You spend months learning how to train a model. Nobody tells you that a well-trained model is also a well-optimized attack surface. Here's what that actually means."
---

Let me start with the thing that bugged me for a long time: the standard ML curriculum treats a trained model as a finished product. You hit your target accuracy, you ship, done. Security people find this worldview slightly deranged.

The distinction I keep coming back to is **program correctness vs. program security**. A correct program does what its specification says. A secure program does what its specification says *even when someone is actively trying to make it not do that*. These are genuinely different problems, and the second one is harder in ways that don't show up on benchmark leaderboards.

Adversarial ML is what happens when you apply that second lens to machine learning systems.

## What "Robust Intelligence" Actually Means

There's a framing I find useful: the difference between *artificial* intelligence and *robust* intelligence. Artificial intelligence is about reaching human-level performance on some task. Robust intelligence is about maintaining that performance under distribution shift, perturbation, and adversarial pressure. Most of what gets deployed in the real world needs the second thing, but we mostly train for the first.

A model that classifies cats with 99% accuracy on your benchmark dataset is doing artificial intelligence. A model that still classifies cats correctly when someone has added a nearly-invisible pattern designed to fool it — that's working toward robust intelligence. The gap between those two is where adversarial ML lives.

## The Attacker's Perspective

Here's a useful mental model: think about who can touch your model and when.

<div class="callout">
  <div class="callout-title">Threat Surfaces</div>
  <strong>Training time:</strong> Can someone inject data into your training set?<br>
  <strong>Model weights:</strong> Can someone read or modify the model itself?<br>
  <strong>Inference time:</strong> Can someone craft inputs specifically to fool predictions?<br>
  <strong>Outputs:</strong> Can someone observe enough predictions to reconstruct private information?
</div>

Each of these is a different attack category, and the defenses are largely orthogonal. A model trained with careful data validation can still be fooled at inference time. A model with excellent adversarial robustness can still leak training data through its outputs.

Most introductory ML courses touch on exactly none of this.

## Why Transformers Specifically Matter Here

The architecture that dominates current AI — the transformer — is worth understanding at a mechanical level before we get into attacks. Not because understanding attention heads will help you craft a better adversarial example (usually), but because the specific failure modes follow from the architecture.

At a high level: a transformer is a stack of attention layers. Each layer takes in some token representations, computes attention weights (who should "look at" whom), and updates those representations. The encoder processes input all at once with bidirectional attention. The decoder generates autoregressively, only attending to previous tokens.

Training is conceptually simple: you have a dataset of (input, output) pairs, you forward-pass, compute loss (usually cross-entropy over next tokens), and backpropagate. Inference is the model generating token by token, each new token conditioned on everything it's produced so far.

The attack surface for transformers includes the training data, the fine-tuning process, and the inference-time input. We'll get to all three. The last one — inference-time attacks — has received the most attention in the adversarial ML literature, so that's where we'll spend most of our time in the next few posts.

## Embeddings: Where Meaning Lives, and Where It's Fragile

One more piece of foundation: how does a model actually represent a word? Through embeddings — dense vectors trained so that similar words end up nearby in vector space. The word2vec intuition is clean: you train a model to predict context words from a center word (or vice versa). The hidden representation it learns in doing that job turns out to capture semantic relationships.

<div class="math-block">
  <div class="label">Softmax over vocabulary</div>
  P(w_o | w_c) = exp(u_o · v_c) / Σ_w exp(u_w · v_c)
</div>

The gradient of the log-probability with respect to the center word vector `v_c` has a nice interpretation: it's the difference between the actual context word and the expected context word under the current model's distribution. Concretely, you're pushing the center vector toward observed co-occurrences and pulling it away from words the model currently predicts but didn't actually appear.

Why does this matter for adversarial ML? Because these learned representations carry the semantic structure that models rely on. Attacks that exploit the geometry of embedding space — adversarial patches, synonym substitution attacks, embedding perturbations — are doing surgery on this structure. Understanding what the embeddings are doing is the first step to understanding why they're breakable.

---

*Next: Poisoning attacks — how an adversary with training-time access can embed a backdoor that survives all your validation metrics.*
