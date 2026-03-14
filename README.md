# Adversarial Minds

A Jekyll blog covering secure and trustworthy machine learning — attacks, defenses, privacy, and what it actually takes to deploy AI you can trust.

## Posts

1. **The Threat Model Nobody Talks About in Intro ML** — Foundations: program correctness vs. security, transformer architecture, embeddings as attack surface.
2. **Poisoning Attacks** — Training-time corruption, backdoor attacks, why accuracy metrics are blind to them.
3. **Evasion Attacks and the Geometry of Adversarial Examples** — FGSM, targeted vs. untargeted, white/black-box threat models.
4. **Your Model Remembers Things It Shouldn't** — Membership inference, attribute inference, model inversion, LLM data extraction.
5. **Differential Privacy: What a Formal Guarantee Actually Looks Like** — DP definition, DP-SGD, central vs. local, the utility cost.
6. **PAC Privacy: A Better Way to Measure What Your Model Actually Leaks** — Computational adversary model, BBP, comparison with DP.

## Setup

```bash
bundle install
bundle exec jekyll serve
```

Then open `http://localhost:4000`.

## Deploying to GitHub Pages

1. Push to a repo named `<username>.github.io` or configure GitHub Pages to use the `main` branch.
2. GitHub Pages builds Jekyll automatically.

No additional configuration needed — the blog uses no external theme, just custom CSS.

## Design

Dark editorial aesthetic. Typography: Playfair Display (headings) + Source Serif 4 (body) + IBM Plex Mono (labels/code). No frameworks, no dependencies beyond Jekyll and Google Fonts.
