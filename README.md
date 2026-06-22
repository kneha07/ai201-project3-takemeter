# TakeMeter — NBA Discourse Quality Classifier

Can a machine tell the difference between a well-reasoned NBA argument and a hot take? This project fine-tunes a text classifier on 200 hand-labeled r/nba posts to find out.

---

## What It Does

TakeMeter classifies r/nba posts into three categories:

| Label | What it means |
|-------|--------------|
| `analysis` | Structured argument backed by real statistics or historical comparison |
| `hot_take` | Bold opinion with no meaningful evidence — asserts rather than argues |
| `reaction` | Pure emotional response to a specific game moment or news event |

---

## Quick Results

| Model | Accuracy |
|-------|----------|
| Zero-shot Groq (llama-3.3-70b) | **96.7%** |
| Fine-tuned DistilBERT | **66.7%** |

The fine-tuned model was beaten by the zero-shot baseline. That's the interesting finding — and the section on failure analysis explains exactly why.

---

## Community

**r/nba** (~7M members) generates thousands of posts daily. The same comment section can contain multi-paragraph stat-backed arguments, bald assertions with zero evidence, and all-caps emotional reactions. r/nba users already use the term "hot take" self-referentially — the labels have real cultural grounding in how the community talks about itself.

---

## Label Definitions

### `analysis`
Makes a structured argument backed by specific, verifiable evidence. The claim would hold up even if you stripped away the opinion framing.

> *"Jokic's assist-to-turnover ratio this playoff run (5.8) is the best ever recorded for a center through 10+ games. He's simultaneously leading the team in scoring, rebounding, and assists — no player in NBA history has done that across a full conference finals."*

> *"The Warriors' net rating drops 14.2 points per 100 possessions when Draymond is off the floor. Their entire defensive communication system collapses without him — this is why the Draymond vs. Klay debate is a false choice."*

### `hot_take`
Bold, confident opinion with no real supporting evidence. May include a stat, but it's decorative — the post asserts rather than argues.

> *"LeBron is not a top 5 player of all time and his fans need to accept it. Jordan, Kareem, Magic, Bird, and Wilt were all better. No debate."*

> *"This Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings."*

### `reaction`
Immediate emotional response to a specific event. Little to no argument — just a feeling expressed in the moment.

> *"CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME"*

> *"I cannot believe they traded him. This is the worst day of my NBA fan life."*

---

## Dataset

- **200 labeled examples** collected from r/nba public posts and comments
- **Source:** Hot/top posts, game threads, discussion-flaired posts, weekly threads
- **Split:** 70% train / 15% validation / 15% test (stratified)

**Label distribution:**

| Label | Count | % |
|-------|-------|---|
| analysis | 66 | 33% |
| hot_take | 62 | 31% |
| reaction | 72 | 36% |

**Labeling process:** Each post was read individually. An LLM pre-labeled batches of 30–40 at a time using the definitions above; every label was reviewed and corrected before inclusion.

### 3 Hard Cases from Annotation

**1. Stat-decorated assertion → `hot_take`**
> *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done."*

Sounds analytical but provides zero evidence. Remove the opinion framing and nothing is left standing. → `hot_take`

**2. Aggressive framing + real numbers → `analysis`**
> *"The Lakers' roster construction is fundamentally flawed. Their starting five has a combined defensive rating of 114.2 when AD is at PF. When AD plays center with a stretch-4, that drops to 107.8."*

The tone is accusatory but two specific verifiable numbers directly support the claim. → `analysis`

**3. Era comparison with no data → `hot_take`**
> *"The Eastern Conference has been bad for 15 years and all the impressive LeBron Finals runs came at the expense of easy paths through the East. If he played in the West his whole career, he has maybe two titles."*

"15 years" is rhetorical, not verified. The counterfactual is pure speculation. → `hot_take`

---

## Model & Training

**Base model:** `distilbert-base-uncased`

**Hyperparameters:**

| Setting | Value | Why |
|---------|-------|-----|
| Epochs | 3 | Validation accuracy plateaued at epoch 2 — more epochs would overfit on 140 training examples |
| Learning rate | 2e-5 | Standard starting point for BERT fine-tuning |
| Batch size | 16 | Fits T4 GPU comfortably |

**Training curve:**

| Epoch | Val Loss | Val Accuracy |
|-------|----------|--------------|
| 1 | 1.076 | 60.0% |
| 2 | 1.039 | 70.0% |
| 3 | 0.956 | 70.0% |

---

## Baseline

**Model:** `llama-3.3-70b-versatile` via Groq API, zero-shot (no fine-tuning)

**Prompt:** Provided community name, one-sentence definition per label, one example post per label, and instruction to output only the label name. Temperature = 0.

---

## Evaluation Report

### Accuracy

| Model | Accuracy |
|-------|----------|
| Zero-shot Groq baseline | **96.7%** (29/30) |
| Fine-tuned DistilBERT | **66.7%** (20/30) |
| Difference | -30.0% regression |

### Per-Class Metrics — Fine-Tuned Model

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| analysis | 0.56 | 1.00 | 0.71 |
| hot_take | 0.00 | 0.00 | 0.00 |
| reaction | 0.83 | 1.00 | 0.91 |
| **macro avg** | **0.46** | **0.67** | **0.54** |

### Per-Class Metrics — Groq Baseline

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| analysis | 0.91 | 1.00 | 0.95 |
| hot_take | 1.00 | 0.90 | 0.95 |
| reaction | 1.00 | 1.00 | 1.00 |
| **macro avg** | **0.97** | **0.97** | **0.97** |

### Confusion Matrix — Fine-Tuned Model

|  | Predicted: analysis | Predicted: hot_take | Predicted: reaction |
|--|:-------------------:|:-------------------:|:-------------------:|
| **True: analysis** | **10** | 0 | 0 |
| **True: hot_take** | 8 | **0** | 2 |
| **True: reaction** | 0 | 0 | **10** |

The model got every `analysis` and `reaction` correct. It got zero `hot_take` correct.

---

## Why the Model Failed on Hot Takes

All 10 errors are the same: `hot_take` posts predicted as `analysis`. Here are three examples.

**Wrong prediction #1**
> *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but not that different from other skilled bigs."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.37)
- The post uses analytical-sounding language (multi-clause structure, basketball terminology) without any actual evidence. The model keyed on surface features rather than asking whether the claim is supported.

**Wrong prediction #2**
> *"Hot take: Giannis will never win a championship without a legitimate second star. He's too one-dimensional offensively. He's Karl Malone 2.0."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.38)
- The historical analogy ("Karl Malone 2.0") looks like reasoning. The model can't distinguish between a post that *uses* analytical framing and one that *actually reasons* with evidence.

**Wrong prediction #3**
> *"The Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.34)
- Counterfactual arguments look like reasoning but aren't evidence-based. The model treats argument structure as a proxy for `analysis`.

**The pattern:** The model learned that statistics → `analysis`, all-caps → `reaction`, everything else → `analysis` as a default. It never learned to ask "is this claim actually backed by data?" — that's a pragmatic inference that 140 training examples can't teach.

---

## Sample Classifications

| Post | True | Predicted | Confidence |
|------|------|-----------|------------|
| "Jokic's assist-to-turnover ratio (5.8) is the best ever recorded for a center..." | analysis | ✅ analysis | 0.38 |
| "CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME..." | reaction | ✅ reaction | 0.38 |
| "I cannot believe they traded him. This is the worst day of my NBA fan life." | reaction | ✅ reaction | 0.37 |
| "LeBron is not a top 5 player of all time. Jordan, Kareem, Magic, Bird, Wilt were better." | hot_take | ❌ analysis | 0.35 |
| "Giannis will never win a championship without a legitimate second star. Karl Malone 2.0." | hot_take | ❌ analysis | 0.36 |

The Jokic prediction is correct because the post cites a specific verifiable statistic (5.8 A/TO ratio) and frames it with a historical comparison — exactly the structure of `analysis`. The model identified this with reasonable confidence.

---

## What the Model Learned vs. What I Intended

I intended the model to learn to distinguish posts based on **evidence quality** — whether claims are backed by verifiable data.

What it actually learned: **surface structural features**. Statistics present → `analysis`. All-caps and exclamation marks → `reaction`. Everything else → `analysis` as a fallback.

The `hot_take` class sits between the other two structurally. Hot takes often sound analytical — complete sentences, basketball vocabulary, sometimes a stat. They just don't provide real evidence. The model never learned to ask "is this actually supported?" because that question requires world knowledge and pragmatic inference that 140 examples can't provide.

The baseline's 96.7% accuracy on the same task shows this isn't a hard problem for a model with broad language understanding. llama-3.3-70b has internalized the `analysis` vs. `hot_take` distinction from pretraining on internet text, including r/nba itself. Fine-tuning on 140 examples trained DistilBERT on surface patterns that approximate the labels most of the time but collapse at the hardest boundary.

---

## Spec Reflection

**Where the spec helped:** Requiring a specific success threshold in planning before seeing results was valuable. Setting "no single class with F1 < 0.55" as a hard requirement made it immediately clear the model failed (hot_take F1 = 0.00) rather than letting 66.7% overall accuracy obscure it.

**Where I diverged:** The spec assumes fine-tuning improves on the baseline. My fine-tuned model regressed by 30 points. This wasn't a bug — it's a genuine finding about the limits of fine-tuning small datasets on tasks where the signal is semantic rather than lexical.

---

## AI Usage

**Label stress-testing:** I asked Claude to generate 10–15 posts at the `analysis`/`hot_take` boundary. Several generated posts required me to tighten the decision rule — I added "≥2 specific verifiable data points = analysis" after seeing generated posts with one stat that I couldn't cleanly classify.

**Annotation assistance:** Used an LLM to pre-label batches of 30–40 posts with my label definitions, then reviewed and corrected every label. Agreement was ~80%; most disagreements were on analytical-framing hot takes — the same boundary the fine-tuned model later failed on.

**Failure analysis:** After getting wrong predictions from Section 4, I pasted all 10 into Claude and asked it to identify patterns. It identified the "analytical-framing hot take" pattern immediately. I verified by re-reading all 10 examples — the pattern held for every error.
