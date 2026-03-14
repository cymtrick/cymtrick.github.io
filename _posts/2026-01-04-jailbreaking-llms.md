---
layout: post
title: "Jailbreaking LLMs: The Attack Taxonomy Nobody Agrees On"
date: 2026-01-04
category: "LLM Safety"
read_time: "13 min read"
tags: [attacks, LLMs, jailbreak, NeurIPS-2024]
excerpt: "From hand-crafted prompts to RL-driven token search and embedding space attacks. NeurIPS 2024 research shows the surface is bigger, and the defenses less settled, than you'd hope."
---

Jailbreaking is what happens when the attack surface is the model's alignment itself. You're not perturbing pixels or poisoning training data — you're crafting inputs that convince a safety-trained model to violate its own guidelines. The attack surface is natural language, and the failure mode is the model's inability to maintain its values under adversarial pressure.

## The Attack Families

**Manual jailbreaks** are human-crafted prompts: roleplay framings, hypothetical framings, suffix injections, cipher encodings. They require human creativity and don't scale, but they work and keep working after patches because humans keep finding new angles.

**GCG (Greedy Coordinate Gradient)** takes the FGSM intuition and applies it to discrete token sequences. Zou et al. (2023) optimize a suffix appended to any harmful query that maximizes the probability of a compliant response. White-box; extremely effective; transferable to black-box models.

**Embedding space attacks** (NeurIPS 2024, Schwinn et al.) directly attack the continuous embedding representation of tokens — bypassing the discrete token search. The finding: embedding attacks are more efficient than discrete attacks and can be used to subsequently generate discrete jailbreaks in natural language.

**RL-driven attacks** (NeurIPS 2024, RLbreaker) use a deep reinforcement learning agent to mutate jailbreaking prompts. A customized PPO policy learns which mutations reliably unlock harmful responses. Black-box; doesn't require model gradients.

**LLM-assisted attacks** (TAP, PAIR) use a helper LLM to iteratively refine jailbreaking prompts based on the target model's responses. Tree-of-attacks explores branching refinements. Requires many queries but scales automatically.

## NeurIPS 2024: Efficient Adversarial Training

The NeurIPS 2024 Spotlight paper by Xhonneux et al. introduces C-AdvUL: train on adversarial inputs in continuous embedding space (not discrete tokens), combined with utility fine-tuning. Tested on five model families at 2B–7B scale, it substantially improves robustness against GCG, AutoDAN, and PAIR while maintaining utility. Key insight: robustness to continuous embedding perturbations extrapolates to discrete threat models.

## NeurIPS 2024: RPO Defense

Robust Prompt Optimization (NeurIPS 2024) formalizes a minimax defensive objective and optimizes a set of trigger tokens (suffixes) that enforce safe outputs even under jailbreaks. The suffix is universal — prepended to any system prompt, it transfers across many LLMs and attack types.

<div class="callout">
  <div class="callout-title">The Adaptive Attack Problem</div>
  All these defenses share a common vulnerability: an adaptive attacker who knows the defense can often circumvent it. RPO suffixes can be attacked by optimization that treats the suffix as a known constant. C-AdvUL's robustness depends on embedding space coverage. No current defense provides formal guarantees analogous to certified robustness.
</div>

## Five Practical Guardrails

1. **System prompt hardening** — explicit refusal instructions in the context window
2. **Adversarial training** (C-AdvUL) — train on adversarial embedding-space inputs
3. **Input classification** — detect known attack patterns before the model processes them
4. **Output monitoring** — classify model responses for policy violations post-generation
5. **Randomized inference** (SmoothLLM) — perturb input tokens, aggregate multiple generations

---

*References: Zou et al. (2023) GCG; Schwinn et al. NeurIPS 2024 embedding attacks; Xhonneux et al. NeurIPS 2024 C-AdvUL; Zhou et al. NeurIPS 2024 RPO; Lin et al. NeurIPS 2024 RLbreaker.*
