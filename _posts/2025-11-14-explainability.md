---
layout: post
title: "Explainability: Why Knowing Isn't the Same as Understanding"
date: 2025-11-14
category: "Explainability"
read_time: "10 min read"
tags: [explainability, SHAP, XAI, saliency]
excerpt: "SHAP, saliency maps, counterfactuals. The tools exist. Whether they actually explain anything — or just make us feel better — is a different question entirely."
---

There's a version of XAI that makes everyone feel better without actually helping anyone. A heatmap that highlights pixels, a bar chart of feature importances, a confidence score — these outputs *look* like explanations. The question is whether they actually explain anything, or just satisfy an auditor.

## Three Families of Explanation

**Gradient-based methods** use the gradient of the model output with respect to the input to attribute importance. Simple gradient saliency maps compute ∂output/∂input and color-code the result. Integrated Gradients averages gradients along a path from a baseline to the input. GradCAM projects gradient information onto spatial activation maps for CNNs.

**Removal-based methods** ask what happens to the prediction when features are removed. LIME trains a local linear surrogate model around a specific prediction. SHAP computes Shapley values — from cooperative game theory — that represent each feature's average marginal contribution.

**Example-based methods** explain predictions by finding related examples: counterfactuals ("what's the minimal change that would flip the prediction?"), prototypes (representative training examples), and instance-based methods (nearest neighbors in feature space).

<div class="callout">
  <div class="callout-title">The Model-Agnostic Advantage</div>
  Removal-based methods (SHAP, LIME) work on any model — neural network, gradient boosted tree, random forest — without needing gradient access. This makes them the most practically useful class.
</div>

## SHAP: The Shapley Value Foundation

SHAP assigns each feature a value representing its contribution to a specific prediction, grounded in Shapley values from cooperative game theory.

<div class="math-block">
  <div class="label">Shapley Value for Feature i</div>
  φ_i(f, x) = Σ_{S ⊆ F\{i}} [|S|!(|F|-|S|-1)!/|F|!] · [f(S∪{i}) - f(S)]
</div>

This is the average marginal contribution of feature i across all possible orderings of features — a fair allocation of the prediction credit. The efficiency property guarantees the values sum to the difference between the prediction and the expected output.

The computational cost is exponential in the number of features. TreeSHAP (for tree models) and KernelSHAP (model-agnostic, approximate) are the practical implementations.

## The Problem with Saliency Maps

Simple gradient saliency maps are noisy, sensitive to normalization choices, and don't decompose additively. More critically: adversarial attacks on explanations are real.

Slack et al. (2020) showed SHAP and LIME can be fooled — you can construct models that produce fair-looking explanations while discriminating on sensitive features behind the scenes. The explanation and the model's actual behavior can be decoupled. This is not a edge case; it's a structural property of post-hoc explanation methods.

## CoT: Explanation by Reasoning

Chain-of-thought prompting takes a different approach: instead of post-hoc attribution, ask the model to reason step by step before answering. Zero-shot CoT adds "Let's think step by step." Few-shot CoT provides worked examples.

This is more like a *process* explanation than a feature explanation. Three advantages: captures reasoning steps, improves performance on complex tasks, provides human-readable justification. Three limitations: unfaithful to actual computation (the chain of thought may be confabulation), computationally expensive, and model-specific — CoT works well in large models but poorly in small ones.

Whether the chain of thought faithfully reflects what the model is *actually* doing computationally remains an open and contested question.

---

*References: Lundberg & Lee (2017) NeurIPS for SHAP; Slack et al. (2020) AIES for adversarial attacks on SHAP/LIME; Wei et al. (2022) NeurIPS for chain-of-thought.*
