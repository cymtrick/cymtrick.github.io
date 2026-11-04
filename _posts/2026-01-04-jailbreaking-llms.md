---
layout: post
title: "Jailbreaking LLMs: Why Alignment Is an Attack Surface"
date: 2026-01-04
updated: 2026-11-04
category: "LLM Safety"
series_index: 9
read_time: "15 min read"
dek: "Every defense in this post cuts attack success from tens of percent to single digits in its own evaluation. A 2025 paper then reached 100% on every leading model with hand-tuned attacks. Both results are real, and understanding why is the whole subject."
lead_figure: jailbreak-defenses
lead_caption: "Attack success rates reported before and after four defenses, each in the setting its own paper used: SmoothLLM against the GCG suffix attack on Vicuna-13B; circuit breakers on the HarmBench average; Constitutional Classifiers on 10,000 synthetic jailbreak prompts. The dashed line marks the 100% that Andriushchenko, Croce and Flammarion reached on essentially every leading model with per-model adaptive attacks. Data from [13, 15], [17, 20]."
thumb: jailbreak-thumb
tags: [attacks, LLMs, jailbreak, alignment, defenses]
---

A jailbreak is an input that persuades a safety-trained language model to produce the output its training was supposed to prevent. Nothing is perturbed at the pixel level and no training data is corrupted; the attack surface is the model's alignment itself, reached through ordinary natural language. The question that organises the field is why alignment should be breakable at all, given that the model was explicitly trained to refuse.

Wei, Haghtalab and Steinhardt gave the answer that everyone now cites [1]. Safety training fails for two distinct reasons. The first is **competing objectives**: the same model is trained to be helpful, to follow instructions, and to refuse harmful requests, and an attacker can construct a prompt in which the first two objectives outvote the third, for instance by asking the model to begin its answer with an affirmative phrase, or by forbidding the usual refusal language. The second is **mismatched generalisation**: pretraining gives the model capabilities, such as reading Base64 or low-resource languages, that safety fine-tuning never covered, so the refusal behaviour simply does not generalise to those inputs even though the capability does. Their prescription was "safety-capability parity": safety mechanisms need to be as sophisticated as the model they protect, and scale alone will not close the gap. Four years of results since then are, in one way or another, confirmations.

## The optimisation era: GCG and the readability problem

In July 2023, Zou and colleagues turned jailbreaking into an optimisation problem [2]. Their **Greedy Coordinate Gradient** attack searches for a short suffix of tokens that, appended to any harmful request, maximises the probability that the model begins its answer affirmatively. It is a discrete search in the lineage of HotFlip and AutoPrompt rather than a one-step gradient method: the gradient proposes candidate token swaps, and each candidate is then evaluated exactly. On open models the results were decisive, with 99% attack success on Vicuna-7B and 56% on Llama-2-7B-Chat for individual behaviours, against 95% and 45% for the AutoPrompt baseline.

The result that made the paper famous was transfer. A suffix optimised on Vicuna and Guanaco, then sent to closed models with no gradient access, raised attack success on GPT-3.5 from 1.8% to 86.6%, on GPT-4 from 8.0% to 46.9%, and on PaLM-2 to 66.0%. The detail that is less often quoted is the asymmetry: the same suffixes reached 47.9% on Claude 1 and 2.1% on Claude 2 [2]. Different labs' models have different vulnerabilities, and a universal attack on one family said little about another.

{% include fig.html name="jailbreak-gcg-transfer" num="1" caption="Transfer of GCG suffixes to closed models. The attack moves GPT-3.5 from near zero to 86.6% and PaLM-2 to 66.0%, but barely touches Claude 2. Data from [2], Table 2." %}

GCG's weakness is that its suffixes are gibberish, with perplexity in the thousands. Jain et al. [12] showed that a perplexity filter in front of the model catches them, and Liu et al. [3] showed how little that buys. Their **AutoDAN** uses a hierarchical genetic algorithm to evolve jailbreak prompts that stay fluent, with perplexity around 40 to 50. On Llama-2-7B-Chat, GCG's success falls from 45.4% to 0.0% under a perplexity filter; AutoDAN's stays at 60.8%. AutoDAN also transfers better to GPT-3.5 (65.8% versus 16.5% for GCG). This is the attack-defense loop in miniature, and it set a pattern: every defense that targets a signature of one attack is answered by an attack without that signature.

## Black-box attacks: the API as a search problem

The next move removed the need for gradients entirely. **PAIR** [4] uses an attacker language model that proposes a jailbreak, observes the target's response, and refines the prompt, usually in fewer than twenty queries. On the JailbreakBench behaviours it reached 88% on Vicuna with ten queries on average, 51% on GPT-3.5, 48% on GPT-4 and 73% on Gemini, but 4% on Llama-2, 3% on Claude 1 and 0% on Claude 2. **Tree of Attacks with Pruning** [5] turned the refinement into a tree search, pruning off-topic branches before they are sent to the target, and reported 90% on GPT-4, 94% on GPT-4o and 60% on Claude 3 Opus, at a mean cost of 28.8, 16.2 and 116.2 queries respectively. The pattern from the GCG paper holds: the Claude models are consistently the hardest targets of their generation, and the "twenty queries" in PAIR's title is a typical case, not a guarantee.

**RLbreaker** [9] replaces the stochastic mutation of genetic methods with a trained PPO agent that learns which mutations unlock harmful responses, and the resulting policy transfers across target models. Like PAIR and TAP, it needs nothing but API access.

## Jailbreaking as a scaling phenomenon

The most important conceptual shift of 2024 was to treat jailbreak success as a quantity that scales with the attacker's budget. Anil and colleagues [6] demonstrated **many-shot jailbreaking**: fill a long context window with hundreds of fabricated dialogues in which an assistant complies with harmful requests, then ask the real question. On Claude 2.0 about eight such demonstrations were enough to pass a 50% jailbreak rate on an insult task and 256 to pass 90%, and the effectiveness follows a power law in the number of shots across Claude 2.0, GPT-3.5, GPT-4, Llama-2-70B and Mistral-7B. Larger models have larger exponents. They learn the bad behaviour from context faster, an inverse-scaling result that follows directly from the competing-objectives account: in-context learning is a capability, and it generalises to places safety training did not reach.

Hughes et al. [7] showed the same law for sheer sampling. **Best-of-N jailbreaking** applies a random augmentation to the request, such as shuffling characters or changing capitalisation, samples the model, and repeats until any sample succeeds. On Claude 3.5 Sonnet the success rate is 0.6% for a single sample, 41% at N = 100, 68% at N = 500 and 78% at N = 10,000; GPT-4o reaches 89% at N = 10,000. The attack works on vision and audio inputs as well as text, and it composes multiplicatively with other methods: combined with many-shot prompts, the number of samples needed for 74% success on Claude 3.5 Sonnet fell from about 6,000 to 274. Running N = 100 against GPT-4o cost about nine dollars.

{% include fig.html name="jailbreak-bon" num="2" caption="Best-of-N jailbreaking on Claude 3.5 Sonnet. The success rate as a function of the number of augmented samples is close to a power law, which means a patient attacker converts budget into success at a predictable rate. Data from [7]." %}

The lesson of both papers is uncomfortable for anyone evaluating a defense with a fixed attack budget. A defense that halves the success rate at N = 100 has, under a power law, mostly shifted the curve rather than bent it.

For open-weight models the situation is worse still. Schwinn et al. [8] attack the continuous embedding of the prompt rather than its tokens. Because the search is no longer discrete, it converges in about nine iterations and reaches 100% success on every model they tested; a universal embedding attack reaches 91.6% on Llama-2-7B-Chat and 96 to 98% on models hardened with circuit breakers. The same technique recovers knowledge that machine-unlearning methods were supposed to have removed, which undercuts unlearning as a safety story for released weights.

## Measuring the mess

By 2024 the literature had dozens of attacks and defenses evaluated on incompatible behaviour sets with incompatible judges. **HarmBench** [10] standardised 510 behaviours and a classifier-based judge, and evaluated 18 attacks against 33 models. Its two headline findings: no model is robust to every attack and no attack breaks every model, and within a model family robustness tracks the training procedure far more than the parameter count. **JailbreakBench** [11] added a living leaderboard, a fixed set of 100 behaviours, and published the jailbreak artifacts themselves so that reported numbers could be reproduced. HarmBench also introduced **R2D2**, an adversarial training method that cuts GCG success on Zephyr-7B to 5.9%, placing the model third on the overall robustness ranking behind the two Llama-2 Chat models.

| Attack family | Access | Automated | Readable prompt | Typical cost | Best reported success |
|---|---|---|---|---|---|
| Hand-crafted (competing objectives, encodings) [1] | black-box | no | yes | human time | varies by model |
| GCG [2] | white-box, transfers | yes | no (high perplexity) | GPU hours | 99% Vicuna; 86.6% GPT-3.5 transfer |
| AutoDAN [3] | white-box, transfers | yes | yes | GPU hours | 60.8% Llama-2 under perplexity filter |
| PAIR / TAP [4, 5] | black-box | yes | yes | 10–120 queries | 94% GPT-4o (TAP) |
| Many-shot [6] | black-box | yes | yes | one long prompt | >90% at 256 shots |
| Best-of-N [7] | black-box | yes | partly | N samples | 78–89% at N = 10,000 |
| Embedding space [8] | open weights | yes | n/a | ~9 iterations | 100% individual |
| RLbreaker [9] | black-box | yes | yes | RL training + queries | transfers across targets |
| Adaptive random search [20] | black-box + logprobs or prefill | semi | yes | per-model tuning | 100% on all tested models |

<p class="fig-caption">A map of the attack families discussed in this post, as reported by the papers themselves. The numbers are not comparable across rows: judges, behaviour sets and target models differ.</p>

## Defenses that filter or randomise

The simplest defenses sit outside the model. The perplexity filter of Jain et al. [12] stops GCG and nothing fluent. **SmoothLLM** [13] borrows randomised smoothing from the vision literature: perturb a fraction of the prompt's characters, run the model on several perturbed copies, and return the majority answer. Against GCG it drives success on Vicuna from about 98% and on Llama-2 from 52% to below 1%, and it comes with a closed-form lower bound on the defense's success probability under an assumption about how fragile the adversarial suffix is. The bound is a real certificate, but it covers a narrow threat model; against PAIR, SmoothLLM cuts success by roughly 60% on average, a perplexity filter by about 32%, and neither is a guarantee. Learned moderators such as Llama Guard sit in the same category: a second model classifying inputs or outputs, with the robustness of a second model.

## Defenses that change the model

Training-time defenses attempt to remove the vulnerability rather than screen for it. Xhonneux et al. [14] note that adversarial training against discrete attacks is prohibitively expensive, since each GCG inner loop costs hours, and instead train against perturbations in the continuous embedding space, which are cheap to compute. The robustness extrapolates: models trained this way resist GCG, AutoDAN and PAIR while keeping their utility, across several model families at the 2B to 7B scale.

**Circuit breakers** [15] take a representation-engineering route. Rather than training the model to refuse, they train it so that the internal representations associated with harmful generation are rerouted to an uninformative direction, interrupting the generation mid-stream. On the HarmBench average the attack success rate falls from 76.7% to 9.8% on Mistral-7B and from 38.1% to 3.8% on Llama-3-8B, with the input-embedding attack falling from 80.4% to 9.6%, and almost no utility cost (MT-Bench 8.05 to 8.00 on Llama-3). A refined variant, Cygnet, reports 0.8% average success. The same mechanism cut a forced-function-call attack on an agent from 82% to 14%. Robust Prompt Optimisation [16] is the prompt-level cousin: a universal defensive suffix found by a minimax optimisation, prepended to the system prompt and transferable across models.

Each of these has an adaptive failure already on record. Best-of-N reaches 52% on the circuit-breaker Llama-3-8B and 67% on Cygnet at N = 10,000 [7]. Embedding-space attacks reach 96 to 98% on circuit-breaker models [8]. A defensive suffix that is known to the attacker is just another constant in the optimisation.

## Constitutional Classifiers and the red-team economy

The most heavily stress-tested deployed defense is Anthropic's **Constitutional Classifiers** [17]. Input and output classifiers are trained on synthetic data generated from a written constitution of permitted and forbidden content, then placed around the production model. On 10,000 synthetic jailbreak prompts against Claude 3.5 Sonnet, success fell from 86% unguarded to 4.4% guarded, the refusal rate on legitimate traffic rose by 0.38 percentage points, which was not statistically significant, and inference compute rose by 23.7%. The prototype was then opened to 183 red-teamers for more than 3,000 hours with a bounty on offer, and no universal jailbreak was found [18].

The coda matters as much as the headline. The public challenge that followed in February 2025 was eventually beaten: four participants cleared all eight levels and at least one universal jailbreak was found, and a joint exercise with the US and UK AI safety institutes later that year surfaced cipher, obfuscation and automated-refinement bypasses that led to an architecture redesign [18]. The next generation, reported in January 2026, withstood more than 1,700 red-team hours over 198,000 attempts with no universal jailbreak found, a refusal overhead of 0.05% and about 1% compute overhead [19]. Whether that holds is an empirical question with a bounty attached, which is the right way to treat it.

## The adaptive-attack reckoning

The vision-robustness literature learned in 2018 that defenses evaluated against fixed attacks overstate their robustness, and that an attack designed for the specific defense usually breaks it. Andriushchenko, Croce and Flammarion [20] delivered the same lesson for language models. Their recipe is deliberately simple: a hand-designed prompt template, then random search over a suffix to maximise the log-probability of an affirmative first token, with transfer or prefilling used where log-probabilities are unavailable. Adapting the attack to each model, they report 100% success, by a GPT-4 judge, on Vicuna-13B, Mistral-7B, Phi-3-Mini, Nemotron-4-340B, Llama-2-Chat at 7B, 13B and 70B, Llama-3-Instruct-8B, Gemma-7B, GPT-3.5, GPT-4o, the R2D2 adversarially trained model, and all Claude models of the time.

The result does not say the defenses above are useless. It says that a static evaluation, however large, is a measurement of the attacks the evaluators tried, and that no current defense provides meaningful guarantees against an attacker who adapts. SmoothLLM's certificate and the erase-and-check style of certified safety for suffix attacks are the exceptions that prove the rule: they are real guarantees under assumptions narrow enough that an adaptive attacker simply steps outside them.

## Jailbreaks are not prompt injections

A final distinction has become the most practically important one. A jailbreak is the *user* coercing the model into violating its own policy. A **prompt injection** is a *third party* smuggling instructions through content the model ingests, such as a web page, an email or a tool output, in order to hijack an agent acting on behalf of a benign user. As language models become browser and computer-use agents, injection is the dominant risk, and the attacker no longer needs the user's cooperation. Anthropic reports that for browser agents an internal attacker modelled on Best-of-N succeeded 8.0% of the time against Claude Opus 4.5 with no safeguards and 1.4% with improved safeguards, and 13.8% to 1.9% for Sonnet 4.5, while stating plainly that the problem is not solved [21]. The AgentDojo benchmark discussed in the first post of this series puts the undefended number for 2024 models at 11 to 48% and finds that every defense costs utility.

<div class="callout">
<div class="callout-title">What a careful evaluation looks like in 2026</div>
<p>Report attack success as a function of attacker budget, not at a single point. Include an attack adapted to the defense, following Andriushchenko et al. Use a standard behaviour set and judge (HarmBench or JailbreakBench) so that numbers are comparable. State the utility cost and the compute overhead alongside the robustness gain. And treat a public bounty with no winner as evidence, not proof.</p>
</div>

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Jailbreaks exist because safety training competes with helpfulness and does not generalise to every capability the model has. Both failure modes are structural, not bugs in one model.</li>
<li>Attack success scales with budget: more shots, more samples, more queries. Evaluate defenses as curves, not points.</li>
<li>Circuit breakers, continuous adversarial training and constitutional classifiers each cut success by an order of magnitude in their own evaluations, and each has a documented adaptive bypass.</li>
<li>Per-model adaptive attacks reach 100% on every leading model tested. No current defense offers a meaningful guarantee against an adaptive attacker without unacceptable cost.</li>
<li>For agents, prompt injection by third parties, not user-driven jailbreaking, is the risk that matters most, and it is not solved.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Wei, Haghtalab, Steinhardt. <em>Jailbroken: How Does LLM Safety Training Fail?</em> NeurIPS 2023. <a href="https://arxiv.org/abs/2307.02483">arXiv:2307.02483</a></li>
<li>Zou, Wang, Carlini, Nasr, Kolter, Fredrikson. <em>Universal and Transferable Adversarial Attacks on Aligned Language Models.</em> arXiv 2023. <a href="https://arxiv.org/abs/2307.15043">arXiv:2307.15043</a></li>
<li>Liu, Xu, Chen, Xiao. <em>AutoDAN: Generating Stealthy Jailbreak Prompts on Aligned Large Language Models.</em> ICLR 2024. <a href="https://arxiv.org/abs/2310.04451">arXiv:2310.04451</a></li>
<li>Chao, Robey, Dobriban, Hassani, Pappas, Wong. <em>Jailbreaking Black Box Large Language Models in Twenty Queries.</em> NeurIPS 2023 R0-FoMo Workshop. <a href="https://arxiv.org/abs/2310.08419">arXiv:2310.08419</a></li>
<li>Mehrotra, Zampetakis, Kassianik et al. <em>Tree of Attacks: Jailbreaking Black-Box LLMs Automatically.</em> NeurIPS 2024. <a href="https://proceedings.neurips.cc/paper_files/paper/2024/hash/70702e8cbb4890b4a467b984ae59828a-Abstract.html">NeurIPS proceedings</a></li>
<li>Anil, Durmus, Panickssery et al. <em>Many-shot Jailbreaking.</em> NeurIPS 2024. <a href="https://proceedings.neurips.cc/paper_files/paper/2024/hash/ea456e232efb72d261715e33ce25f208-Abstract.html">NeurIPS proceedings</a></li>
<li>Hughes, Price, Lynch et al. <em>Best-of-N Jailbreaking.</em> arXiv 2024. <a href="https://arxiv.org/abs/2412.03556">arXiv:2412.03556</a></li>
<li>Schwinn, Dobre, Xhonneux, Gidel, Günnemann. <em>Soft Prompt Threats: Attacking Safety Alignment and Unlearning in Open-Source LLMs through the Embedding Space.</em> NeurIPS 2024. <a href="https://arxiv.org/abs/2402.09063">arXiv:2402.09063</a></li>
<li>Chen, Nie, Guo, Zhang. <em>When LLM Meets DRL: Advancing Jailbreaking Efficiency via DRL-guided Search.</em> NeurIPS 2024. <a href="https://arxiv.org/abs/2406.08705">arXiv:2406.08705</a></li>
<li>Mazeika, Phan, Yin et al. <em>HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal.</em> ICML 2024. <a href="https://proceedings.mlr.press/v235/mazeika24a.html">PMLR 235</a></li>
<li>Chao, Debenedetti, Robey et al. <em>JailbreakBench: An Open Robustness Benchmark for Jailbreaking Large Language Models.</em> NeurIPS 2024 Datasets &amp; Benchmarks. <a href="https://arxiv.org/abs/2404.01318">arXiv:2404.01318</a></li>
<li>Jain, Schwarzschild, Wen et al. <em>Baseline Defenses for Adversarial Attacks Against Aligned Language Models.</em> arXiv 2023. <a href="https://arxiv.org/abs/2309.00614">arXiv:2309.00614</a></li>
<li>Robey, Wong, Hassani, Pappas. <em>SmoothLLM: Defending Large Language Models Against Jailbreaking Attacks.</em> arXiv 2023. <a href="https://arxiv.org/abs/2310.03684">arXiv:2310.03684</a></li>
<li>Xhonneux, Sordoni, Günnemann, Gidel, Schwinn. <em>Efficient Adversarial Training in LLMs with Continuous Attacks.</em> NeurIPS 2024. <a href="https://arxiv.org/abs/2405.15589">arXiv:2405.15589</a></li>
<li>Zou, Phan, Wang et al. <em>Improving Alignment and Robustness with Circuit Breakers.</em> NeurIPS 2024. <a href="https://arxiv.org/abs/2406.04313">arXiv:2406.04313</a></li>
<li>Zhou, Wang, Robey et al. <em>Robust Prompt Optimization for Defending Language Models Against Jailbreaking Attacks.</em> arXiv 2024. <a href="https://arxiv.org/abs/2401.17263">arXiv:2401.17263</a></li>
<li>Sharma, Tong, Korbak et al. <em>Constitutional Classifiers: Defending against Universal Jailbreaks across Thousands of Hours of Red Teaming.</em> arXiv 2025. <a href="https://arxiv.org/abs/2501.18837">arXiv:2501.18837</a></li>
<li>Anthropic. <em>Constitutional Classifiers.</em> Research blog, 2025. <a href="https://www.anthropic.com/research/constitutional-classifiers">anthropic.com</a></li>
<li>Anthropic. <em>Next-generation Constitutional Classifiers.</em> Research blog, January 2026. <a href="https://www.anthropic.com/research/next-generation-constitutional-classifiers">anthropic.com</a></li>
<li>Andriushchenko, Croce, Flammarion. <em>Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks.</em> ICLR 2025. <a href="https://arxiv.org/abs/2404.02151">arXiv:2404.02151</a></li>
<li>Anthropic. <em>Prompt injection defenses for browser-using agents.</em> Alignment blog, November 2025. <a href="https://www.anthropic.com/research/prompt-injection-defenses">anthropic.com</a></li>
</ol>
</section>
