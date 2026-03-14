---
layout: default
title: About
---

<div class="post-container">
  <header class="post-header">
    <div class="post-header-label">About this blog</div>
    <h1 class="post-title-large">Adversarial Minds</h1>
  </header>

  <div class="post-content">
    <p>This is a writing project that grew out of exam notes for <strong>XM 0179: Secure and Trustworthy Machine Learning</strong> at VU Amsterdam. The original notes were dry and formal. These posts are an attempt to actually understand the material — to explain it the way you'd explain it to someone at a whiteboard, not the way a textbook does.</p>

    <p>The series covers adversarial ML from foundations to current research: threat models, poisoning and evasion attacks, privacy attacks, formal privacy frameworks, explainability, and some of the harder questions about what it means to trust a deployed model.</p>

    <p>The intended reader is someone who knows ML reasonably well and wants to understand the security and privacy dimensions without just memorizing definitions.</p>

    <h2>What's Here</h2>

    <p>Six posts in the core series, ordered to build on each other:</p>

    <ol>
      <li><strong>The Threat Model Nobody Talks About</strong> — foundations, program correctness vs. security, transformer architecture as attack surface</li>
      <li><strong>Poisoning Attacks</strong> — training-time corruption, backdoors, why accuracy metrics can't catch it</li>
      <li><strong>Evasion Attacks and FGSM</strong> — inference-time perturbation, gradient-based attacks, white/black-box taxonomy</li>
      <li><strong>Your Model Remembers Things It Shouldn't</strong> — membership inference, attribute inference, model inversion, LLM extraction</li>
      <li><strong>Differential Privacy</strong> — the formal definition, DP-SGD, central vs. local, the utility tradeoff</li>
      <li><strong>PAC Privacy</strong> — why DP's worst case is unrealistic, computational adversary model, black-box privatization</li>
    </ol>

    <h2>References</h2>

    <p>The core papers behind these posts: Goodfellow et al. (2015) on FGSM, Shokri et al. (2017) on membership inference, Carlini et al. (2021) on extracting training data from GPT-2, Dwork et al. "The Algorithmic Foundations of Differential Privacy" (2014), and Ligett & Livni (2022) on PAC Privacy.</p>
  </div>
</div>
