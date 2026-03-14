---
layout: post
title: "Poisoning Attacks: Corrupting a Model Before It Exists"
date: 2025-11-10
category: "Attacks"
read_time: "9 min read"
tags: [attacks, poisoning, training-time]
excerpt: "The most elegant class of adversarial attacks don't touch the model at all — they corrupt the data it learns from. By the time you notice, the attack is already baked in."
---

The most uncomfortable thing about poisoning attacks is the timeline. An evasion attack happens at inference time — you can, in principle, detect it, rate-limit, or filter inputs. A poisoning attack happens *before the model exists*. By the time you're deploying and monitoring, the attack is already encoded in the weights.

The main idea is simple: if you can influence what data a model trains on, you can influence what the model learns. That influence can be subtle enough to pass all your accuracy checks.

## Four Types Worth Knowing

**Label flipping** is the blunt instrument version. You take training examples and flip their labels — cats become dogs, benign becomes malicious. The model learns the wrong associations. This requires the most access (write access to labels) and is the most detectable, since model accuracy will usually suffer noticeably.

**Backdoor attacks** (also called Trojan attacks) are more surgical. Here, the attacker injects a small number of examples that contain a trigger pattern — a specific pixel patch, a particular phrase, a watermark — paired with a target label. The model learns that trigger-pattern → target-class. On clean data, the model performs normally; standard accuracy metrics look fine. But present the trigger, and the model reliably misbehaves.

This is the scenario that keeps ML security people up at night. You train on a dataset that was assembled from the internet. You have no way to audit every example. The model ships, passes eval, gets deployed.

<div class="callout">
  <div class="callout-title">The Sleeper Agent Problem</div>
  A backdoored model is functionally identical to a clean model on all inputs that don't contain the trigger. Standard evaluation cannot distinguish them. The trigger exists only in the attacker's pocket.
</div>

**Data poisoning for misclassification** (clean-label attacks) is the sophisticated version. The attacker doesn't touch labels — instead, they craft poison examples that look completely normal to a human labeler but push the model's decision boundary in ways that cause specific test examples to be misclassified. These attacks are harder to construct but almost impossible to detect by manual inspection.

**Model poisoning** in federated learning deserves its own mention. In federated settings, multiple parties train local models and aggregate updates. A malicious participant can submit poisoned updates — crafted to move global model parameters toward an attacker-chosen point, while staying plausible enough not to be filtered.

## Why Backdoors Survive Training

It's worth thinking about *why* backdoor attacks work so reliably. The model is just doing optimization — it finds features predictive of the training labels. If you've given it examples where trigger-pattern reliably predicts class-A, it will learn that association. It has no way to know that the trigger was put there by an attacker; to the loss function, it's just a useful feature.

This is also why detection is hard. You'd need to either: (a) find the trigger pattern without knowing what it is, which is a search problem over a huge space; or (b) do neural network analysis that identifies "suspicious" neurons or features, which is its own research frontier.

Some defenses that have traction: Neural Cleanse (reverse-engineer trigger patterns), STRIP (detect anomalous input predictions), and various data sanitization approaches. None of them are complete solutions.

## The Evaluation Blind Spot

Here's what gets me about poisoning: standard ML evaluation literally cannot catch it. You train on poisoned data, you evaluate on clean test data, your accuracy looks fine. The attack only manifests on triggered inputs, which aren't in your test set.

This is a general theme in adversarial ML — our evaluation metrics measure average-case performance, but adversaries live in the worst case. High accuracy doesn't mean robust. It means the model works on examples that look like the training distribution.

When we say a model is "good," we need to be specific about good *for whom* and *under what conditions*. A model that performs well on the IID test set but fails whenever someone presents a specific blue square in the corner of an image is not a good model. It's a model with a hidden exploit.

---

*Next: Evasion attacks — perturbing inputs at inference time to fool a deployed model, without touching the training process at all.*
