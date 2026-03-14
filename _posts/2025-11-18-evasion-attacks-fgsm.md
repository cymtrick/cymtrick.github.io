---
layout: post
title: "Evasion Attacks and the Geometry of Adversarial Examples"
date: 2025-11-18
category: "Attacks"
read_time: "10 min read"
tags: [attacks, evasion, FGSM, gradient]
excerpt: "Add an imperceptible noise pattern to an image, and a state-of-the-art classifier confidently misidentifies it. This isn't a bug in one model — it's something structural about how these models work."
---

In 2014, Szegedy et al. showed something genuinely unsettling: you could take an image correctly classified by a neural network, add a perturbation *invisible to the human eye*, and the network would then classify it as something completely wrong, often with high confidence. The perturbation was computed, not random. It was specifically designed to exploit the model's decision boundary.

This is an evasion attack. The model is already deployed; you're not touching the training process. You're crafting inputs that cross the decision boundary in ways that matter to the model but not to you.

## The Core Intuition

Think about a linear classifier. It partitions input space into half-planes. The decision boundary is a hyperplane. The distance from any point to that boundary can be small even if the *meaningful* features of the point are far from the boundary — because high-dimensional spaces are weird.

Neural networks are non-linear classifiers, but the same intuition holds. Their decision boundaries are complex surfaces in high-dimensional space, and those surfaces can be very close to real data points in directions that don't correspond to any meaningful visual or semantic feature.

An adversarial perturbation is a small step in input space, chosen to cross the decision boundary. The step is small in the sense you care about (L∞ or L2 norm — pixel intensity changes), but large in the sense the model cares about (classification confidence).

<div class="fig">
  <svg width="100%" height="200" viewBox="0 0 500 200" xmlns="http://www.w3.org/2000/svg" style="max-width:480px">
    <!-- decision boundary -->
    <line x1="250" y1="20" x2="250" y2="180" stroke="#2a2d32" stroke-width="1.5" stroke-dasharray="6,4"/>
    <!-- labels -->
    <text x="100" y="105" font-family="IBM Plex Mono, monospace" font-size="11" fill="#4a4845" text-anchor="middle">Class A region</text>
    <text x="380" y="105" font-family="IBM Plex Mono, monospace" font-size="11" fill="#4a4845" text-anchor="middle">Class B region</text>
    <!-- original point -->
    <circle cx="200" cy="100" r="7" fill="#e8633a"/>
    <text x="200" y="88" font-family="IBM Plex Mono, monospace" font-size="9" fill="#e8633a" text-anchor="middle">x (correct)</text>
    <!-- arrow -->
    <line x1="207" y1="100" x2="258" y2="100" stroke="#f0a500" stroke-width="1.5" marker-end="url(#arr)"/>
    <defs>
      <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L8,3 z" fill="#f0a500"/>
      </marker>
    </defs>
    <!-- adversarial point -->
    <circle cx="268" cy="100" r="7" fill="#f0a500"/>
    <text x="268" y="88" font-family="IBM Plex Mono, monospace" font-size="9" fill="#f0a500" text-anchor="middle">x+δ (misclassified)</text>
    <!-- delta label -->
    <text x="232" y="117" font-family="IBM Plex Mono, monospace" font-size="9" fill="#7a7670" text-anchor="middle">δ small</text>
  </svg>
  <div class="fig-caption">fig.1 — A small perturbation δ crosses the decision boundary; the perturbation is imperceptible but the prediction flips.</div>
</div>

## Fast Gradient Sign Method (FGSM)

FGSM, introduced by Goodfellow et al. in 2015, is the canonical one-step evasion attack. The idea is almost embarrassingly direct.

You want to maximize the model's loss with respect to your input, subject to keeping the perturbation small. The gradient of the loss with respect to the input tells you the direction to move in input space to *increase* loss the fastest. You don't need the full gradient — just its sign suffices for the L∞ constraint:

<div class="math-block">
  <div class="label">FGSM update</div>
  x_adv = x + ε · sign(∇_x L(θ, x, y))
</div>

Each pixel gets nudged by ε in the direction that increases loss. The result is an adversarial example. The budget ε controls the strength of the perturbation — small enough to be invisible, large enough to cross the boundary.

The gradient here is the key: you need access to the model to compute it. That makes FGSM a *white-box* attack. We'll come back to what happens when you don't have that access.

## Untargeted vs. Targeted

FGSM as written is an **untargeted** attack — you just want the model to be wrong, you don't care what it says instead. The update maximizes loss for the true label, which pushes the prediction toward *something else*.

A **targeted** attack has a specific wrong answer in mind — you want the model to classify your adversarial panda as a gibbon, specifically. The update rule flips: instead of maximizing loss for the true label, you minimize loss for the target label:

<div class="math-block">
  <div class="label">Targeted FGSM</div>
  x_adv = x - ε · sign(∇_x L(θ, x, y_target))
</div>

Gradient ascent on the true class (untargeted) versus gradient descent on the target class (targeted). The sign of the step is the difference between "make it wrong" and "make it wrong *in this specific way*."

## White-Box, Grey-Box, Black-Box

The threat model taxonomy matters a lot for evasion attacks.

**White-box**: attacker has full access to model architecture and weights. Can compute exact gradients. This is the standard assumption in most academic evasion attack papers, and it tends to produce the strongest attacks.

**Black-box**: attacker can only query the model — input in, prediction out. No gradient access. This sounds like it should be much harder, but it turns out there are effective techniques:

- *Pure black-box*: build a substitute model from public info and transfer attacks
- *Oracle-based*: query the target model to label data, train a local substitute, attack the substitute
- *Score-based*: if you get confidence scores (not just the top label), you can estimate gradients from finite differences
- *Decision-based*: if you only get the hard label, use algorithms that find adversarial examples by taking large steps and then binary searching back to the boundary

**Grey-box** is somewhere in between — you might know the architecture but not the weights, or know the training distribution but not the model.

Here's the uncomfortable thing about how "white-box robustness" is usually defined in the literature: it assumes the attacker knows the defense. A defense that's robust against the attack it was designed to counter can still fail against attacks that were designed knowing the defense. This is the **adaptive attack** problem. A lot of early adversarial robustness papers were later broken by adaptive attacks, which is why the field has gotten much more careful about what "evaluation" means.

## Why This Is Hard to Defend Against

The intuition that helps me here: adversarial examples exist because decision boundaries are locally fragile even when globally reasonable. A classifier can be highly accurate — in the sense that randomly drawn test examples are classified correctly — while having many nearby decision boundary crossings for every single training example.

The most principled defense is **adversarial training**: include adversarial examples in your training set, with correct labels. You're asking the model to learn a smoother decision boundary. This works, and currently certified adversarial training is the only defense with any serious theoretical guarantees.

But adversarial training has a cost: it typically hurts clean accuracy. This is the fundamental tension — a smooth decision boundary sacrifices some discriminative power on easy examples to gain robustness on hard (adversarial) ones.

---

*Next: Privacy attacks — your model's predictions can leak information about its training data, even without any access to the training set itself.*
