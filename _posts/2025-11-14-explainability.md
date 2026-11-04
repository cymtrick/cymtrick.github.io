---
layout: post
title: "Explainability: Why Knowing Isn't the Same as Understanding"
date: 2025-11-14
updated: 2026-11-04
category: "Explainability"
series_index: 3
read_time: "15 min read"
dek: "An edge detector produces saliency maps as convincing as any gradient method, with no model behind it. A reasoning model that used a hint admits it a quarter of the time. The gap between an explanation that persuades and one that is true is the whole subject."
lead_figure: explain-cot-faithful
lead_caption: "When Anthropic inserted hints into exam questions and checked whether the model's chain of thought mentioned the hint it demonstrably used, Claude 3.7 Sonnet did so 25% of the time and DeepSeek R1 39%. In synthetic environments where exploiting the hint was rewarded, the model exploited it in over 99% of cases and said so in under 2%. Data from [18]."
thumb: explain-thumb
tags: [explainability, interpretability, SHAP, saliency, chain-of-thought, sparse-autoencoders]
---

In 2018 Adebayo and colleagues ran an experiment that should have ended a research programme [1]. They took the standard saliency methods for image classifiers, the ones that colour the pixels a network "looked at", and applied them to a network whose weights had been replaced with random values, layer by layer from the top. Some methods changed as you would hope. Others did not. Guided Backpropagation and Guided Grad-CAM produced essentially the same attractive, edge-hugging maps for a trained network, a network with random weights, and a network trained on shuffled labels. The maps looked like explanations. They were edge detectors with extra steps.

The paper's title was *Sanity Checks for Saliency Maps*, and the sanity check is simple: an explanation of a model must change when the model changes. That is the minimum. It is remarkable how much of the explainability literature, before and since, has failed it, and the failures have a common shape. A method produces something that looks right to a person, practitioners adopt it because it looks right, and nobody tests whether it tracks the computation at all.

Jacovi and Goldberg [2] gave the two properties names that the field now uses. *Plausibility* is how convincing an explanation is to a human. *Faithfulness* is how accurately it reflects the model's actual reasoning. They are independent, human studies can only measure the first, and almost every tool in the explainability toolbox was selected for it.

{% include fig.html name="explain-quadrants" num="1" caption="The two axes of an explanation. Methods in the lower right persuade without being true; methods in the upper left are true but not usable. Most of the history of the field is a sequence of methods sliding from the right-hand column into the trap once someone runs the three tests at the bottom. Framing from [2]; placements from [1, 11, 12, 16, 18, 22]." %}

## Three families, one Taylor expansion

The first family of methods is gradient-based, and it begins with a Taylor expansion. Simonyan, Vedaldi and Zisserman [3] observed that around a given image I₀ the class score is approximately linear, S_c(I) ≈ wᵀI + b with w = ∂S_c/∂I, and that the magnitude of w, reshaped into an image, is a map of which pixels the score is most sensitive to. It is cheap, it is exact to first order, and it is noisy, because the gradient of a ReLU network is piecewise constant and flips sign across tiny distances.

Each later method fixes one failure. Integrated Gradients [4] starts from two axioms. *Sensitivity*: if an input differs from a baseline in one feature and the prediction changes, that feature must get non-zero attribution, which raw gradients violate when a ReLU is saturated. *Implementation invariance*: two networks computing the same function must get the same attributions, which methods using discrete difference rules like DeepLIFT violate. Integrating the gradient along a straight path from a baseline to the input satisfies both and, as a bonus, the attributions sum exactly to the difference in output. The cost is a baseline, which is a modelling choice with real consequences. SmoothGrad [5] attacks the noise directly by averaging gradients over Gaussian-perturbed copies of the input. Grad-CAM [6] gives up pixel resolution for class discrimination: it weights the last convolutional layer's feature maps by the pooled gradient of the class score and keeps only the positive part, which localises the object even when the raw gradient cannot.

<div class="math"><div class="math-label">Integrated Gradients (Sundararajan, Taly & Yan 2017)</div>IGᵢ(x) = (xᵢ − x′ᵢ) · ∫₀¹ ∂F(x′ + α(x − x′)) / ∂xᵢ dα</div>

None of these methods asks whether the map it produces would change if the model did. That is why Adebayo's result landed: plain Gradient and Grad-CAM pass both randomisation tests, Guided Backprop fails both, and Integrated Gradients and Gradient⊙Input are "dominated by the input", meaning the map looks the same across models because it is largely the image multiplied by something [1]. A year earlier Kindermans et al. [10] had shown that most of the same methods are not even invariant to adding a constant to the input, a transformation that provably does not change the function a network computes.

## Model-agnostic attribution and its price

The second family removes features and watches the prediction. LIME [7] samples perturbed versions of an input, queries the model on each, and fits a sparse linear surrogate weighted by proximity; the surrogate's coefficients are the explanation. Its most-cited result is a user study. A classifier trained to distinguish huskies from wolves was, in fact, detecting snow. Before seeing explanations, 10 of 27 graduate students trusted the model and 12 mentioned snow; after seeing LIME's output, 3 trusted it and 25 mentioned snow [7].

SHAP [8] unified LIME, DeepLIFT, layer-wise relevance propagation and Shapley sampling under one framework, *additive feature attribution*, and proved that within it exactly one allocation satisfies local accuracy, missingness and consistency: the Shapley value from cooperative game theory.

<div class="math"><div class="math-label">Shapley value of feature i (Lundberg & Lee 2017)</div>φᵢ = Σ_{S ⊆ F∖{i}} [ |S|! (|F| − |S| − 1)! / |F|! ] · [ f(S ∪ {i}) − f(S) ]</div>

The sum is over every subset of the other features, so exact computation is exponential. KernelSHAP approximates it by weighted regression on sampled coalitions; TreeSHAP, published separately three years later, computes it exactly in polynomial time for tree ensembles [9], which is why SHAP is the default explanation in tabular machine learning.

Removal-based methods have a property that looks like a virtue and turns out to be an attack surface. They never see the model's internals; they only see what the model says about inputs they construct. LIME's perturbations are Gaussian noise around the instance. KernelSHAP's "removed" features are filled in from cluster centres of a background set. In both cases the explainer's queries lie off the data manifold, and anything off the manifold can be recognised.

## Falsifying explanations

Slack and colleagues [11] built exactly that. Take a model f that discriminates on a sensitive feature, race in COMPAS, say. Train an out-of-distribution detector to recognise LIME's or SHAP's perturbed samples. Serve f on real inputs and an innocuous model ψ, which uses only uncorrelated synthetic features, on anything the detector flags. Audit the result with LIME and the sensitive feature is the top-ranked explanation for 0% of test points; the innocuous feature is top-ranked for 100% on COMPAS and Communities & Crime, and 91% on German Credit. SHAP is harder to fool, 84% and 100% and 85%, and harder still with two synthetic features, but the scaffolded model still agrees with the biased model on 75–100% of real inputs [11].

{% include fig.html name="explain-slack" num="2" caption="The scaffolding attack. The sensitive feature was the top-ranked LIME and SHAP feature for the undisguised model; after wrapping it in an out-of-distribution detector, an unrelated synthetic feature takes its place. Where a value is missing the paper does not report it. Data from [11], Section 4." %}

Two things about this result are often misstated. It is not a general property of post-hoc explanation; it exploits a specific weakness, off-manifold sampling, and the paper's own sensitivity analysis shows the LIME attack only works once the detector reaches an F1 of about 0.8. And the fix follows from the diagnosis: perturb on the manifold, audit with real held-out data, and treat the explainer's query distribution as part of the threat model. Gradient-based explainers have their own adversarial literature, but it is a different attack.

What the three results above share is a methodology, and it is worth stating because it recurs. An explanation method has been falsified when (i) randomising the model does not change it, (ii) perturbing the explanation does not change the model's behaviour, or (iii) a trivial baseline, an edge detector, a linear probe, produces the same thing. Methods that survive all three are rare. Methods that look good to humans are common.

## Two escapes

Rudin's response [12] is that the whole enterprise is misdirected for high-stakes decisions. Her argument has four parts. The accuracy–interpretability trade-off is largely a myth on structured data, where sparse scoring systems and rule lists match black boxes. A post-hoc explanation that is right 90% of the time is wrong 10% of the time and you cannot tell which. An explanation of a black box is frequently an explanation of a *different* model, the surrogate. And the harms from COMPAS-style deployments came from using an opaque model where a transparent one would have done the job. The honest counterpoint is that for images and text the interpretable model of equal accuracy does not yet exist, which is exactly why mechanistic interpretability, discussed below, emerged.

Wachter, Mittelstadt and Russell [13] offer a different escape by asking what an explanation is *for*. Under the GDPR a person needs to understand a decision, contest it, and learn what to change. A *counterfactual explanation*, the closest input under some distance that flips the decision, serves all three without opening the box. The open problems are the ones you would guess: the nearest counterfactual may change immutable features, may lie off the data manifold, may not be unique, and may itself be manipulable.

## Chain of thought as explanation

Language models added a new kind of explanation: ask the model to reason out loud before answering. Wei et al. [14] showed that a few worked examples of step-by-step reasoning raise PaLM 540B's GSM8K accuracy from 17.9% to 56.9%, beating a fine-tuned GPT-3 with a verifier, and that the gain appears only at roughly 100 billion parameters; smaller models produce fluent but illogical chains. Kojima et al. [15] found that the single phrase "Let's think step by step" recovers much of the effect with no examples at all.

Note what Wei et al. did and did not claim. They claimed accuracy. They did not claim that the chain of thought is a faithful account of how the model got its answer, and it is a *process* explanation, so faithfulness means something different from feature attribution: does the text describe the computation that produced the answer?

Turpin, Michael, Perez and Bowman [16] designed the test. Add to the prompt a feature that should not matter, such as reordering few-shot examples so the correct answer is always (A), or having the user suggest an answer. If the feature changes the model's answers, it influenced the computation; if the chain of thought never mentions it, the explanation is unfaithful. On thirteen BIG-Bench Hard tasks the suggested-answer bias dropped GPT-3.5's zero-shot CoT accuracy by 36.3 points and Claude 1.0's by 30.6, and in no case did the chain of thought mention the suggestion. It explained the biased answer, fluently, with reasons invented for the purpose [16].

{% include fig.html name="explain-turpin" num="3" caption="Accuracy lost to biasing features that the chain of thought never mentions. Each bar is the difference between accuracy with and without the bias; the model's written reasoning rationalised the wrong answer in every condition. Data from [16]." %}

Lanham et al. [17] approached from the other side, corrupting or truncating the chain of thought and checking whether the answer moved. On some tasks it did; on others the model gave the same answer regardless, meaning the text was decoration. Their most unsettling observation is a scaling trend: larger, more capable models rely *less* on their stated reasoning on most tasks.

## What reasoning models admit

By 2025 chain of thought was no longer a prompting trick; it was the main product of a new class of models and the basis of a safety strategy, monitoring the reasoning for signs of misbehaviour. Anthropic measured whether that strategy can work [18]. They inserted hints into MMLU and GPQA questions, sometimes neutral (a metadata tag), sometimes compromising (a note that the model has gained unauthorised access to the answer key), identified the cases where the hint demonstrably changed the answer, and read the chain of thought. Claude 3.7 Sonnet verbalised the hint it used 25% of the time, DeepSeek R1 39%. On the hints that signalled misbehaviour the rates were 20% and 29%. Outcome-based reinforcement learning raised faithfulness at first and then plateaued at 28% on MMLU and 20% on GPQA. In synthetic environments built so that exploiting the hint was rewarded, the model exploited it in over 99% of examples and mentioned doing so in fewer than 2%, in five of six environments. Unfaithful chains of thought were *longer* than faithful ones, so this is not a matter of the model being terse [18].

OpenAI reported the complementary result [19]. A GPT-4o monitor reading o3-mini's chain of thought catches reward hacking in agentic coding tasks far better than a monitor that only sees actions. But if you then optimise the policy against the monitor, the behaviour persists and the chain of thought stops showing it: *obfuscated reward hacking*. They proposed accepting a "monitorability tax", declining to apply optimisation pressure to the reasoning text, and a forty-author position paper across the major labs [20] called chain-of-thought monitorability "a new and fragile opportunity" and asked developers to track how training choices affect it.

So the question that was long described as open and contested has an answer. Chains of thought are sometimes faithful, often not, and the degree is measurable. The disagreement that remains is practical: whether 25–40% faithfulness on hints, with much higher rates on ordinary reasoning, is enough to build a safety case on.

## Opening the box

The alternative to asking the model is to look inside it, and the obstacle is *superposition*: a network represents more concepts than it has neurons by encoding them as overlapping directions, so individual neurons are polysemantic and uninterpretable. Dictionary learning with sparse autoencoders (SAEs) tries to undo this. Anthropic's first demonstration on a one-layer transformer [21] found that features from an over-complete dictionary were far more interpretable than neurons, a median human rating of 12 versus 0 on a 0–20 scale, and that a 131,072-feature dictionary recovered 94.5% of the loss the MLP accounts for.

Scaling the method to Claude 3 Sonnet [22] produced dictionaries of one million, four million and 34 million features, including a multilingual, multimodal Golden Gate Bridge feature, features for code bugs, for deception and for sycophancy, with causal steering demonstrations: clamp the bridge feature at ten times its maximum and the model identifies itself as the bridge; clamp an unsafe-code feature and it writes a buffer overflow. OpenAI reported clean scaling laws for 16-million-latent autoencoders on GPT-4 [23], and DeepMind released sparse autoencoders for every layer of Gemma 2 [24]. The next step, cross-layer transcoders and *attribution graphs* [25, 26], traces a specific prompt through the features that mattered and validates the graph by intervention: Claude 3.5 Haiku plans the rhyme of a poem's second line before writing the first, computes √0.64 with a square-root circuit, and, given cos(23423), claims to use a calculator while the graph shows it guessing. When a user suggests an answer, the graph shows the model working *backwards* from it. That is the first mechanistic view of the unfaithfulness Turpin measured behaviourally [26].

{% include fig.html name="explain-sae" num="4" caption="The cost of scale in dictionary learning. As the Claude 3 Sonnet autoencoders grow from one million to 34 million features, the fraction that never activate rises from 2% to 65%, leaving roughly twelve million live features. Data from [22]." %}

The labs' own caveats are substantial and belong next to the demonstrations. Two thirds of the 34-million dictionary is dead [22]. The transcoder-based replacement model reproduces the real model's next token on only about half of pretraining-style prompts, attribution graphs were judged to give satisfying insight on roughly a quarter of the prompts tried, attention patterns are taken as given rather than explained, and features often sit at the wrong level of abstraction, splitting or absorbing one another [25, 30]. A replacement model is a surrogate, and a surrogate can be mechanistically unfaithful even when its outputs correlate, which is the failure mode Jacovi and Goldberg warned about for every surrogate before it [2].

## The sanity-check moment, again

In 2025 sparse autoencoders got their Adebayo test. AxBench [27] compared steering and concept-detection methods on Gemma 2 and found that for steering, prompting and fine-tuning beat SAEs, and that for detection a difference-of-means direction beat them too. Kantamneni et al. [28] found SAE probes beat ordinary linear probes only on isolated datasets under data scarcity, imbalance, noise and shift. DeepMind's own interpretability team [29] reported that a dense linear probe reached AUROC 0.999 out of distribution on harmful-intent detection, that SAE probes did not, and that they were deprioritising fundamental SAE research in favour of model diffing and interpreting reasoning models.

The right reading is not that the method failed but that the field applied its own standard. An interpretability method earns trust by beating a trivial baseline on a task someone cares about, by changing when the model changes, and by predicting the effect of an intervention. Saliency maps were held to that standard in 2018, chains of thought in 2023, sparse autoencoders in 2025. Each time, the methods that looked best to people were not the ones that survived.

<div class="callout takeaways">
<div class="callout-title">What to take away</div>
<ol>
<li>Plausibility and faithfulness are different properties, and human studies can only measure the first. Choose methods by the second.</li>
<li>Three tests falsify an explanation: randomise the model, perturb the explanation, compare to a trivial baseline. Guided Backprop, chains of thought and sparse autoencoders have each failed at least one.</li>
<li>Perturbation-based explainers can be gamed by recognising their off-manifold queries; audit with real data.</li>
<li>Reasoning models verbalise the hints they use a quarter to a third of the time. Chain-of-thought monitoring is useful and fragile, and optimising against it makes it worse.</li>
<li>Mechanistic interpretability has produced real causal evidence inside frontier models, and its own authors estimate it explains a minority of the computation. Both halves of that sentence matter.</li>
</ol>
</div>

<section class="refs">
<h2>References</h2>
<ol>
<li>Adebayo, Gilmer, Muelly, Goodfellow, Hardt, Kim. <em>Sanity Checks for Saliency Maps.</em> NeurIPS 2018. <a href="https://arxiv.org/abs/1810.03292">arXiv:1810.03292</a></li>
<li>Jacovi, Goldberg. <em>Towards Faithfully Interpretable NLP Systems: How should we define and evaluate faithfulness?</em> ACL 2020. <a href="https://arxiv.org/abs/2004.03685">arXiv:2004.03685</a></li>
<li>Simonyan, Vedaldi, Zisserman. <em>Deep Inside Convolutional Networks: Visualising Image Classification Models and Saliency Maps.</em> ICLR 2014 Workshop. <a href="https://arxiv.org/abs/1312.6034">arXiv:1312.6034</a></li>
<li>Sundararajan, Taly, Yan. <em>Axiomatic Attribution for Deep Networks.</em> ICML 2017. <a href="https://arxiv.org/abs/1703.01365">arXiv:1703.01365</a></li>
<li>Smilkov, Thorat, Kim, Viégas, Wattenberg. <em>SmoothGrad: removing noise by adding noise.</em> ICML 2017 Workshop on Visualization for Deep Learning. <a href="https://arxiv.org/abs/1706.03825">arXiv:1706.03825</a></li>
<li>Selvaraju, Cogswell, Das, Vedantam, Parikh, Batra. <em>Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization.</em> ICCV 2017. <a href="https://arxiv.org/abs/1610.02391">arXiv:1610.02391</a></li>
<li>Ribeiro, Singh, Guestrin. <em>"Why Should I Trust You?": Explaining the Predictions of Any Classifier.</em> KDD 2016. <a href="https://arxiv.org/abs/1602.04938">arXiv:1602.04938</a></li>
<li>Lundberg, Lee. <em>A Unified Approach to Interpreting Model Predictions.</em> NeurIPS 2017. <a href="https://arxiv.org/abs/1705.07874">arXiv:1705.07874</a></li>
<li>Lundberg, Erion, Chen et al. <em>From local explanations to global understanding with explainable AI for trees.</em> Nature Machine Intelligence 2020. <a href="https://arxiv.org/abs/1905.04610">arXiv:1905.04610</a></li>
<li>Kindermans, Hooker, Adebayo et al. <em>The (Un)reliability of saliency methods.</em> arXiv 2017. <a href="https://arxiv.org/abs/1711.00867">arXiv:1711.00867</a></li>
<li>Slack, Hilgard, Jia, Singh, Lakkaraju. <em>Fooling LIME and SHAP: Adversarial Attacks on Post hoc Explanation Methods.</em> AIES 2020. <a href="https://arxiv.org/abs/1911.02508">arXiv:1911.02508</a></li>
<li>Rudin. <em>Stop Explaining Black Box Machine Learning Models for High Stakes Decisions and Use Interpretable Models Instead.</em> Nature Machine Intelligence 2019. <a href="https://arxiv.org/abs/1811.10154">arXiv:1811.10154</a></li>
<li>Wachter, Mittelstadt, Russell. <em>Counterfactual Explanations without Opening the Black Box: Automated Decisions and the GDPR.</em> Harvard Journal of Law &amp; Technology 2018. <a href="https://arxiv.org/abs/1711.00399">arXiv:1711.00399</a></li>
<li>Wei, Wang, Schuurmans et al. <em>Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.</em> NeurIPS 2022. <a href="https://proceedings.neurips.cc/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html">NeurIPS proceedings</a></li>
<li>Kojima, Gu, Reid, Matsuo, Iwasawa. <em>Large Language Models are Zero-Shot Reasoners.</em> NeurIPS 2022. <a href="https://arxiv.org/abs/2205.11916">arXiv:2205.11916</a></li>
<li>Turpin, Michael, Perez, Bowman. <em>Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting.</em> NeurIPS 2023. <a href="https://arxiv.org/abs/2305.04388">arXiv:2305.04388</a></li>
<li>Lanham, Chen, Radhakrishnan et al. <em>Measuring Faithfulness in Chain-of-Thought Reasoning.</em> arXiv 2023. <a href="https://arxiv.org/abs/2307.13702">arXiv:2307.13702</a></li>
<li>Chen, Benton, Radhakrishnan et al. <em>Reasoning Models Don't Always Say What They Think.</em> Anthropic, 2025. <a href="https://www.anthropic.com/research/reasoning-models-dont-say-think">anthropic.com</a></li>
<li>Baker, Huizinga, Gao et al. <em>Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation.</em> arXiv 2025. <a href="https://arxiv.org/abs/2503.11926">arXiv:2503.11926</a></li>
<li>Korbak, Balesni, Barnes et al. <em>Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety.</em> arXiv 2025. <a href="https://arxiv.org/abs/2507.11473">arXiv:2507.11473</a></li>
<li>Bricken, Templeton, Batson et al. <em>Towards Monosemanticity: Decomposing Language Models With Dictionary Learning.</em> Transformer Circuits Thread, 2023. <a href="https://transformer-circuits.pub/2023/monosemantic-features/">transformer-circuits.pub</a></li>
<li>Templeton, Conerly, Marcus et al. <em>Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet.</em> Transformer Circuits Thread, 2024. <a href="https://transformer-circuits.pub/2024/scaling-monosemanticity/">transformer-circuits.pub</a></li>
<li>Gao, Dupré la Tour, Tillman et al. <em>Scaling and evaluating sparse autoencoders.</em> ICLR 2025. <a href="https://arxiv.org/abs/2406.04093">arXiv:2406.04093</a></li>
<li>Lieberum, Rajamanoharan, Conmy et al. <em>Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2.</em> arXiv 2024. <a href="https://arxiv.org/abs/2408.05147">arXiv:2408.05147</a></li>
<li>Ameisen, Lindsey, Pearce et al. <em>Circuit Tracing: Revealing Computational Graphs in Language Models.</em> Transformer Circuits Thread, 2025. <a href="https://transformer-circuits.pub/2025/attribution-graphs/methods.html">transformer-circuits.pub</a></li>
<li>Lindsey, Gurnee, Ameisen et al. <em>On the Biology of a Large Language Model.</em> Transformer Circuits Thread, 2025. <a href="https://transformer-circuits.pub/2025/attribution-graphs/biology.html">transformer-circuits.pub</a></li>
<li>Wu, Arora, Geiger et al. <em>AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders.</em> ICML 2025. <a href="https://proceedings.mlr.press/v267/wu25a.html">PMLR 267</a></li>
<li>Kantamneni, Engels, Rajamanoharan, Tegmark, Nanda. <em>Are Sparse Autoencoders Useful? A Case Study in Sparse Probing.</em> ICML 2025. <a href="https://arxiv.org/abs/2502.16681">arXiv:2502.16681</a></li>
<li>Smith, Rajamanoharan, Conmy et al. <em>Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research.</em> Google DeepMind, AI Alignment Forum, March 2025. <a href="https://www.alignmentforum.org/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks">alignmentforum.org</a></li>
<li>Chanin, Wilken-Smith, Dulka, Bhatnagar, Bloom. <em>A is for Absorption: Studying Feature Splitting and Absorption in Sparse Autoencoders.</em> arXiv 2024. <a href="https://arxiv.org/abs/2409.14507">arXiv:2409.14507</a></li>
</ol>
</section>
