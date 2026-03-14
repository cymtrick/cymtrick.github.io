---
layout: post
title: "Your Model Remembers Things It Shouldn't"
date: 2025-11-26
category: "Privacy"
read_time: "11 min read"
tags: [privacy, membership-inference, model-inversion, attacks]
excerpt: "A trained model isn't just a classifier — it's a compressed version of its training data. That compression is lossy, but not lossy enough. Privacy attacks exploit the residue."
---

Here's a scenario worth sitting with. A hospital trains a model on patient records to predict readmission risk. The model is deployed as an API — clinicians query it, get predictions, nothing else is exposed. No training data is shared. No weights are shared.

Can an attacker extract information about individual patients from that API alone?

Yes. That's what privacy attacks on ML models are about.

## Membership Inference: Did You Train On Me?

The most studied privacy attack is membership inference. The question: given a data point x and black-box access to a model trained on some dataset D, was x in D?

Why would a model's predictions reveal this? Because models tend to behave differently on training examples versus unseen examples. Specifically, they tend to be *more confident* on training examples — lower loss, higher probability on the correct class. This is overfitting in the traditional sense, but for privacy purposes it's a signal an attacker can exploit.

The classic attack setup (Shokri et al., 2017): train a collection of *shadow models* on datasets sampled from the same distribution as the target's training data. For each shadow model, you have ground truth membership labels. Train a binary classifier ("member" vs. "non-member") on the shadow models' confidence vectors. Apply that meta-classifier to the target model's outputs.

<div class="callout">
  <div class="callout-title">Why LLMs Are Especially Vulnerable</div>
  Large language models have two properties that amplify membership inference risk: (1) they're trained on enormous datasets scraped from the public web, so your text might plausibly be in there; (2) they're large enough to memorize individual examples verbatim. The memorization isn't a bug — it's a consequence of model capacity and training duration.
</div>

For LLMs specifically, the attack surface is interesting. You can ask the model to complete sentences and observe how confidently it fills in specific tokens. If the model has seen a particular document, it tends to assign higher probability to the exact token sequence in that document compared to slightly perturbed versions. Carlini et al. showed this can be used to extract memorized training data, including personally identifying information, verbatim.

## Attribute Inference: Reconstructing What You Didn't Share

One step up from membership: given that x is in the training set, can you infer specific attributes of x that weren't provided as input?

This is attribute inference. Suppose a model is trained on medical records that include demographics, diagnosis, and treatment outcomes. An attacker who knows a patient's age and diagnosis might query the model and, from the output distribution, infer something about their treatment history.

The white-box version is nastier. With access to model gradients, you can run optimization in the reverse direction — instead of asking "what does this input predict," you ask "what input would produce these activations." The gradients guide a search through input space. This is related to model inversion.

## Model Inversion: Reconstructing Training Data

Model inversion attacks aim to reconstruct approximate representations of training data from a trained model. The intuition: a model that classifies faces has internalized something about what faces in each class look like. You can try to recover that knowledge.

The original Fredrikson et al. (2015) attack was against a clinical pharmacogenetics model: given the model and a patient's outcome, infer their genomic markers. More modern attacks target image classifiers and can recover recognizable face images from confidence scores alone.

Evaluating model inversion success is tricky. Common metrics include:
- **Accuracy**: does a separate classifier correctly classify the reconstructed example?
- **Visual fidelity**: do the reconstructed images look like real training examples?
- **Feature distance**: how close are the reconstructed examples to real ones in feature space?

None of these are perfect. An attack that scores well on one metric might not generalize. This is a place where the field is still developing better benchmarks.

## Property Inference: What Can I Learn About Your Dataset?

Distinct from individual-level attacks: property inference asks questions about the *distribution* of training data. "What fraction of your training data is from patients over 65?" "What is the class balance in your training set?" "Does your training data include examples from a specific demographic?"

These aggregate properties can be sensitive even when no individual record is exposed. A model trained mostly on images of one demographic might behave differently than one trained on a balanced set, and an attacker might be able to infer that imbalance from output patterns.

The attack typically works by training a meta-model: given observations of a target model's behavior across many inputs, predict which of two training distributions it was trained on. Repeated querying builds up a statistical picture of the training distribution.

## What Actually Leaks from LLM Queries

Beyond the cryptographic-style attacks above, there's a more direct attack surface for deployed LLMs: you can just... ask them things. Models trained on proprietary data will sometimes surface that data in their completions. API key strings, personal names, email addresses, private communications — all documented as appearing in LLM outputs in various experiments.

The Carlini et al. experiments on GPT-2 extracted thousands of memorized training sequences by prompting the model with common prefixes and collecting the completions. The memorized sequences included names, contact information, and other PII.

Protections against data extraction are layered and imperfect:
- Deduplication of training data (reduces memorization of repeated sequences)
- Differential privacy during training (adds noise that degrades memorization)
- Output filtering (blocks known PII patterns — but an attacker can probe for what's filtered)
- Membership inference detection (flag queries that look like extraction attempts)

None of these alone is sufficient. The underlying issue — model capacity enables memorization, and memorization creates an extraction surface — doesn't have a clean solution. The question is how much memorization you're willing to trade for how much model capability.

---

*Next: Differential privacy — the one privacy framework with actual mathematical guarantees, and what it costs to use it.*
