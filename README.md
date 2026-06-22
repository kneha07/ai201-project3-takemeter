# TakeMeter — NBA Discourse Quality Classifier

A fine-tuned text classifier that evaluates discourse quality in r/nba posts, distinguishing between structured analysis, hot takes, and emotional reactions.

---

## Community Choice

**Community:** r/nba (NBA basketball subreddit, ~7M members)

r/nba generates thousands of posts daily across game threads, trade discussions, and player debates. The discourse quality varies enormously — the same comment section can contain multi-paragraph stat-backed arguments, bald assertions with no evidence, and pure emotional reactions. This variability makes it ideal for classification: the distinctions are meaningful to community members (r/nba regulars routinely call out "hot takes" and distinguish them from "actual analysis"), the text is rich and varied, and the labels have genuine cultural grounding.

---

## Label Taxonomy

### `analysis`
A post that makes a structured argument backed by statistics, historical comparison, or tactical observation. The evidence is specific and verifiable — it would support the claim even if you removed the opinion framing.

**Example 1:** *"Jokic's assist-to-turnover ratio this playoff run (5.8) is the best ever recorded for a center through 10+ games. He's simultaneously leading the team in scoring, rebounding, and assists — no player in NBA history has done that across a full conference finals."*

**Example 2:** *"The Warriors' net rating drops 14.2 points per 100 possessions when Draymond Green is off the floor. That's not just about offense — their entire defensive communication system collapses without him. This is why the Draymond vs. Klay debate is a false choice."*

### `hot_take`
A bold, confident opinion stated without meaningful supporting evidence. The claim may be true or false, but the post asserts rather than argues. The framing is often provocative. A stat may appear but it is decorative rather than genuinely reasoning.

**Example 1:** *"LeBron is not a top 5 player of all time and his fans need to accept it. Jordan, Kareem, Magic, Bird, and Wilt were all better. No debate."*

**Example 2:** *"This Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings."*

### `reaction`
An immediate emotional response to a specific game event, trade, play, or news item. Little to no argument — the post expresses a feeling in the moment. The content is event-anchored and loses most meaning without knowing what just happened.

**Example 1:** *"CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME"*

**Example 2:** *"I cannot believe they traded him. This is the worst day of my NBA fan life."*

---

## Data Collection

**Source:** r/nba — public posts and top-level comments collected from hot/top posts, game threads, discussion-flaired posts, and weekly discussion threads over the past 6 months.

**Labeling process:** Each post was read individually and assigned one label using the definitions above. Posts that were primarily images or video links with no substantive text were excluded. Posts longer than 512 characters were trimmed to the first complete sentence under that limit. An LLM was used to pre-label batches of 30–40 posts at a time; every pre-assigned label was reviewed and corrected before inclusion.

**Label distribution:**

| Label | Count | % |
|-------|-------|---|
| analysis | 66 | 33% |
| hot_take | 62 | 31% |
| reaction | 72 | 36% |
| **Total** | **200** | **100%** |

**Dataset split:** 70% train / 15% validation / 15% test (stratified, `random_state=42`)

### 3 Difficult-to-Label Examples

**1. Stat-decorated assertion (→ `hot_take`)**
*"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done."*
Could be `analysis` (makes a comparative claim) or `hot_take`. Decided `hot_take` because the comparative claim is asserted without naming any players or providing data — remove the opinion framing and there's no argument left standing.

**2. Accusatory framing + real statistics (→ `analysis`)**
*"The Lakers' roster construction is fundamentally flawed. Their starting five has a combined defensive rating of 114.2 when LeBron and AD share the court but AD is at PF. When AD plays center with a stretch-4 beside him, that number drops to 107.8."*
Could be `hot_take` (aggressive framing) or `analysis`. Decided `analysis` because the post provides two specific verifiable defensive ratings that directly support the claim — the decision rule is ≥2 specific data points = `analysis` regardless of tone.

**3. Era comparison with implicit claims (→ `hot_take`)**
*"The Eastern Conference has been bad for 15 years and all the impressive LeBron Finals runs came at the expense of easy paths through the East. If he played in the West his whole career the way MJ did, he has maybe two titles."*
Could be `analysis` (references historical pattern) or `hot_take`. Decided `hot_take` because "15 years" is rhetorical, the counterfactual is pure speculation, and the conference disparity claim is stated as self-evident rather than supported.

---

## Fine-Tuning Approach

**Base model:** `distilbert-base-uncased` (HuggingFace)

**Training setup:**
- 3 epochs
- Learning rate: 2e-5
- Batch size: 16 (train), 32 (eval)
- Weight decay: 0.01
- Warmup steps: 50
- Best model selected by validation accuracy

**Key hyperparameter decision:** Kept the default 3 epochs rather than increasing. With only 140 training examples, more epochs risk overfitting — validation accuracy plateaued at 70% by epoch 2 and did not improve in epoch 3, confirming this was the right stopping point.

---

## Baseline

**Model:** `llama-3.3-70b-versatile` via Groq API (zero-shot)

**Prompt approach:** The system prompt included the community name, a one-sentence definition of each label, one example post per label, and an instruction to output only the label name. Temperature was set to 0 for deterministic output.

**Prompt used:**
```
You are classifying posts from r/nba, the NBA basketball subreddit.
Assign each post to exactly one of the following three categories.

analysis: The post makes a structured argument backed by statistics, historical comparison, 
or tactical observation. The evidence is specific and verifiable...

hot_take: A bold, confident opinion stated without meaningful supporting evidence...

reaction: An immediate emotional response to a specific game event, trade, or news...

Respond with ONLY the label name — nothing else.
```

---

## Evaluation Report

### Overall Accuracy

| Model | Accuracy | Test Set Size |
|-------|----------|---------------|
| Zero-shot baseline (Groq llama-3.3-70b) | **96.7%** | 30 |
| Fine-tuned DistilBERT | **66.7%** | 30 |
| Difference | -30.0% (regression) | — |

### Per-Class Metrics — Fine-Tuned Model

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| analysis | 0.56 | 1.00 | 0.71 | 10 |
| hot_take | 0.00 | 0.00 | 0.00 | 10 |
| reaction | 0.83 | 1.00 | 0.91 | 10 |
| **macro avg** | **0.46** | **0.67** | **0.54** | 30 |

### Per-Class Metrics — Baseline (Groq)

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| analysis | 0.91 | 1.00 | 0.95 | 10 |
| hot_take | 1.00 | 0.90 | 0.95 | 10 |
| reaction | 1.00 | 1.00 | 1.00 | 10 |
| **macro avg** | **0.97** | **0.97** | **0.97** | 30 |

### Confusion Matrix — Fine-Tuned Model

|  | Predicted: analysis | Predicted: hot_take | Predicted: reaction |
|--|---------------------|---------------------|---------------------|
| **True: analysis** | 10 | 0 | 0 |
| **True: hot_take** | 8 | 0 | 2 |
| **True: reaction** | 0 | 0 | 10 |

### Analysis of Wrong Predictions

The fine-tuned model made **10 errors out of 30**, and every single error involved `hot_take` — the model predicted 0 hot takes correctly, misclassifying 8 as `analysis` and 2 as `reaction`.

**Wrong prediction #1:**
> *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.37)
- **Why it failed:** This post uses analytical-sounding language ("reading defensive rotations," "other skilled bigs") without providing actual evidence. The model likely keyed on surface features — multi-clause structure, basketball terminology — that correlate with `analysis` in training. The distinction requires understanding that the comparative claim is unsubstantiated, which is a pragmatic inference DistilBERT can't make from surface text alone.

**Wrong prediction #2:**
> *"Hot take: Giannis will never win a championship without a legitimate second star. He's too one-dimensional offensively and teams have figured out how to defend him in the playoffs. He's Karl Malone 2.0."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.38)
- **Why it failed:** The post contains a historical analogy ("Karl Malone 2.0") and a tactical observation ("teams have figured out how to defend him"), which are structural features the model associates with `analysis`. The model cannot distinguish between a post that *uses* analytical framing and one that *actually reasons* with evidence.

**Wrong prediction #3:**
> *"The Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings. Take KD off those rosters and they win maybe one title."*
- True: `hot_take` | Predicted: `analysis` (confidence: 0.34)
- **Why it failed:** This is a counterfactual argument ("any team with KD would have won") — counterfactuals look like reasoning but are not evidence-based. The model treats argument structure as a proxy for `analysis`, but the critical signal — whether the argument is backed by verifiable data — is not learnable from 140 training examples.

### Systematic Error Pattern

All 10 errors share a single pattern: **`hot_take` posts that use analytical framing** (historical analogies, tactical observations, comparative claims) are misclassified as `analysis`. The model learned to predict `analysis` for posts with multi-clause structure and basketball-specific vocabulary, regardless of whether the claims are actually evidenced. It learned `reaction` reliably (distinctive all-caps, exclamation marks, event-anchored language) and `analysis` reliably (actual statistics present). The `hot_take` boundary requires understanding *intent and evidence quality* — too subtle for a 140-example fine-tune.

### Sample Classifications

| Post (truncated) | True Label | Predicted | Confidence |
|-----------------|------------|-----------|------------|
| "Jokic's assist-to-turnover ratio this playoff run (5.8) is the best ever recorded..." | analysis | analysis | 0.81 |
| "CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME" | reaction | reaction | 0.94 |
| "I cannot believe they traded him. This is the worst day of my NBA fan life." | reaction | reaction | 0.89 |
| "LeBron is not a top 5 player of all time and his fans need to accept it." | hot_take | analysis | 0.35 |
| "Unpopular opinion: Kawhi Leonard is not a superstar..." | hot_take | analysis | 0.36 |

**Why the Jokic analysis prediction is reasonable:** The post cites a specific, verifiable statistic (5.8 A/TO ratio) and contextualizes it with a historical comparison ("best ever recorded for a center through 10+ games"). This is exactly the structure of `analysis` — specific evidence supporting a claim — and the model correctly identified it with reasonable confidence.

---

## Reflection: What the Model Learned vs. What I Intended

I intended the model to learn to distinguish posts based on **evidence quality** — whether claims are backed by verifiable data. What the model actually learned was **surface-level structural features**: posts with statistics → `analysis`, posts with all-caps and exclamation marks → `reaction`, everything else → `analysis` as a fallback.

The `hot_take` class sits between the other two structurally. Hot takes often use complete sentences, basketball vocabulary, and sometimes even analytical-sounding claims — they just don't provide evidence. The model never learned to ask "is this claim actually supported?" because that question requires world knowledge and pragmatic inference that 140 training examples cannot teach a model the size of DistilBERT.

The baseline's near-perfect performance (96.7%) on the same task reveals that this is not a hard classification problem for a model with broad language understanding — it's hard specifically because the signal is semantic (evidence quality) rather than lexical (word choice). Fine-tuning on 140 examples trained the model on surface patterns that approximate the labels most of the time but completely fail at the hardest boundary.

---

## Spec Reflection

**One way the spec helped:** The requirement to define a specific success threshold in planning before seeing results was valuable. I set "no single class with F1 < 0.55" as a hard requirement — this framing made it immediately clear when I saw the results that the model failed (hot_take F1 = 0.00), rather than letting the 66.7% overall accuracy obscure the failure.

**One way implementation diverged from spec:** The spec assumes fine-tuning will improve on the baseline, framing Section 6 as showing "improvement." My fine-tuned model regressed by 30 points. This was not a bug — it's a genuine finding about the limits of fine-tuning on small datasets for tasks where the signal is semantic rather than lexical. The baseline's strength reflects that llama-3.3-70b has internalized the `analysis` vs. `hot_take` distinction from its pretraining on internet text, including r/nba itself.

---

## AI Usage

**1. Label stress-testing (before annotation):** I directed Claude to generate 10–15 posts that sit at the boundary between `analysis` and `hot_take` using my label definitions. Several generated posts were ambiguous enough to require me to tighten the decision rule: I added the "≥2 specific verifiable data points = analysis" rule after seeing generated posts with one stat that I couldn't cleanly classify.

**2. Annotation assistance:** I used an LLM to pre-label batches of 30–40 posts at a time, providing my label definitions and asking for one label per post. I reviewed and corrected every pre-assigned label. The LLM's pre-labels agreed with mine approximately 80% of the time; most disagreements were on `hot_take` posts with analytical framing — the same boundary the fine-tuned model later failed on.

**3. Failure analysis:** After getting the wrong predictions from Section 4, I pasted all 10 misclassified examples into Claude and asked it to identify patterns. It identified the "analytical-framing hot take" pattern immediately. I verified this by re-reading all 10 examples — the pattern held for every single error. I used this finding directly in the systematic error pattern section above.
