# TakeMeter — r/nba Discourse Classifier

I built a classifier that reads r/nba posts and labels them as analysis, hot takes, or reactions. The idea came from noticing how different the posts in the same thread can be — someone writes a whole breakdown with stats, the next person just yells in all caps, and someone else posts a confident opinion with zero evidence. I wanted to see if a model could learn to tell those apart.

---

## The short version

| Model | Accuracy |
|-------|----------|
| Groq zero-shot baseline | 96.7% |
| Fine-tuned DistilBERT | 66.7% |

The fine-tuned model lost to the baseline by 30 points. That's the most interesting result, and the failure analysis section explains what happened.

---

## Why r/nba

r/nba is huge (~7M members) and the conversations are genuinely varied. During a playoff game the same thread will have someone citing defensive ratings, someone saying "LeBron is overrated change my mind," and someone just screaming because Steph hit a wild shot. The community also uses the term "hot take" themselves, so the labels aren't something I invented — they map to how people in the community actually talk about discourse quality.

---

## The three labels

**analysis** — makes a real argument with actual evidence. Stats, historical comparisons, tactical observations. If you removed the opinion framing, the argument would still hold up on its own.

> *"Jokic's assist-to-turnover ratio this playoff run (5.8) is the best ever recorded for a center through 10+ games. He's simultaneously leading the team in scoring, rebounding, and assists — no player in NBA history has done that across a full conference finals."*

> *"The Warriors' net rating drops 14.2 points per 100 possessions when Draymond is off the floor. Their entire defensive communication system collapses without him — this is why the Draymond vs. Klay debate is a false choice."*

**hot_take** — bold opinion with no real supporting evidence. The post asserts rather than argues. Sometimes a stat shows up but it's there to sound credible, not to actually reason.

> *"LeBron is not a top 5 player of all time and his fans need to accept it. Jordan, Kareem, Magic, Bird, and Wilt were all better. No debate."*

> *"This Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings."*

**reaction** — pure emotion about something that just happened. A shot, a trade, a bad loss. No argument, just feeling. These posts don't really make sense if you don't know what event triggered them.

> *"CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME"*

> *"I cannot believe they traded him. This is the worst day of my NBA fan life."*

---

## The data

200 posts and comments collected from r/nba — hot/top posts, game threads, discussion-flaired posts, weekly threads. I read every post myself and labeled it. I used an LLM to give me a starting label on batches of 30-40 at a time, but I reviewed and corrected every single one.

| Label | Count |
|-------|-------|
| analysis | 66 |
| hot_take | 62 |
| reaction | 72 |

Split 70/15/15 into train, validation, and test sets.

### Three posts that were genuinely hard to label

**"He has the ball a lot and makes easy passes"**
> *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done."*

This sounds like it's reasoning because it makes a comparative claim. But no players are named and no numbers are cited. Strip the opinion framing and there's nothing left. → `hot_take`

**"That number drops to 107.8"**
> *"The Lakers' roster construction is fundamentally flawed. Their starting five has a combined defensive rating of 114.2 when LeBron and AD share the court but AD is at PF. When AD plays center with a stretch-4 beside him, that number drops to 107.8."*

The framing is really aggressive, which made me want to call it a hot take. But there are two specific verifiable numbers that directly support the claim. Angry tone on top of real evidence is still evidence. → `analysis`

**"If he played in the West his whole career"**
> *"The Eastern Conference has been bad for 15 years and all the impressive LeBron Finals runs came at the expense of easy paths through the East. If he played in the West his whole career the way MJ did, he has maybe two titles."*

Sounds historical. But "15 years" isn't backed up anywhere, and the counterfactual is pure speculation. The post sounds like it's about to make an argument and then never actually does. → `hot_take`

---

## Training

Base model: `distilbert-base-uncased`

I kept the defaults mostly — 3 epochs, learning rate 2e-5, batch size 16. The main decision I made was to not increase epochs past 3. Validation accuracy hit 70% at epoch 2 and didn't move in epoch 3, which told me the model had learned what it could from 140 training examples. More epochs would have just overfit.

| Epoch | Val Accuracy |
|-------|-------------|
| 1 | 60% |
| 2 | 70% |
| 3 | 70% |

---

## Baseline

Zero-shot Groq using `llama-3.3-70b-versatile`. I gave it the community name, a one-sentence definition of each label, one example post per label, and told it to output only the label name. Temperature 0.

---

## Results

### Accuracy

| Model | Accuracy |
|-------|----------|
| Groq zero-shot | **96.7%** |
| Fine-tuned DistilBERT | **66.7%** |

### Fine-tuned model per-class breakdown

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| analysis | 0.56 | 1.00 | 0.71 |
| hot_take | 0.00 | 0.00 | 0.00 |
| reaction | 0.83 | 1.00 | 0.91 |

### Baseline per-class breakdown

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| analysis | 0.91 | 1.00 | 0.95 |
| hot_take | 1.00 | 0.90 | 0.95 |
| reaction | 1.00 | 1.00 | 1.00 |

### Confusion matrix (fine-tuned model)

|  | → analysis | → hot_take | → reaction |
|--|:----------:|:----------:|:----------:|
| **analysis** | **10** | 0 | 0 |
| **hot_take** | 8 | **0** | 2 |
| **reaction** | 0 | 0 | **10** |

The model got every analysis and reaction right. It got zero hot takes right — 8 were predicted as analysis, 2 as reaction.

---

## Why it failed on hot takes

All 10 wrong predictions are the same mistake: a `hot_take` post getting classified as `analysis`. Here are three of them.

**Wrong #1**
> *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from other skilled bigs."*
- True: hot_take | Predicted: analysis (0.37 confidence)
- It uses analytical-sounding sentence structure and basketball vocabulary. The model picked up on those surface features and called it analysis. It can't tell that the comparative claim has no actual backing.

**Wrong #2**
> *"Hot take: Giannis will never win a championship without a legitimate second star. He's too one-dimensional offensively. He's Karl Malone 2.0."*
- True: hot_take | Predicted: analysis (0.38 confidence)
- The historical analogy (Karl Malone) looks like reasoning. The model associates historical comparisons with analysis. But naming a player isn't evidence — it's just a comparison.

**Wrong #3**
> *"The Warriors dynasty is overrated. They got lucky with Durant falling into their lap after blowing a 3-1 lead. Any team with KD would have won those rings."*
- True: hot_take | Predicted: analysis (0.34 confidence)
- "Any team with KD would have won" looks like a reasoned argument. It's actually just a counterfactual with nothing backing it up.

**The pattern:** Every single error is a hot take that sounds analytical. The model learned that statistics → analysis, all-caps → reaction, and everything else → analysis as a default. It never learned to ask whether a claim is actually backed up. That's the key thing missing — 140 training examples aren't enough to teach a model to evaluate evidence quality rather than surface structure.

---

## Sample predictions

| Post | True label | Predicted | Confidence |
|------|-----------|-----------|------------|
| "Jokic's assist-to-turnover ratio (5.8) is the best ever recorded for a center..." | analysis | ✅ analysis | 0.38 |
| "CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME..." | reaction | ✅ reaction | 0.38 |
| "I cannot believe they traded him. This is the worst day of my NBA fan life." | reaction | ✅ reaction | 0.37 |
| "LeBron is not a top 5 player of all time. Jordan, Kareem, Magic, Bird, Wilt were better." | hot_take | ❌ analysis | 0.35 |
| "Giannis will never win a championship without a legitimate second star. Karl Malone 2.0." | hot_take | ❌ analysis | 0.36 |

The Jokic prediction makes sense — there's a specific stat (5.8 A/TO ratio) with a historical comparison, which is exactly what analysis looks like. The model got it right. The hot take predictions fail because both posts have the structure of an argument without the substance.

---

## What the model actually learned vs. what I wanted

I wanted it to learn evidence quality — is this claim backed by real data? What it actually learned was surface structure — does this post look like it's making an argument?

Those two things overlap most of the time. Analysis posts do tend to have more complex sentence structures and basketball-specific vocabulary. Hot takes also sometimes have those features, but lack the actual evidence. That's the gap the model couldn't bridge with 140 training examples.

The Groq baseline didn't have this problem because llama-3.3-70b has seen millions of posts like these during pretraining, including probably r/nba itself. It already knows what a hot take looks like. DistilBERT started from scratch on my 140 examples and learned the easy signals but not the hard one.

---

## Spec reflection

The requirement to write success criteria before seeing the results was genuinely useful. I wrote "no single class with F1 below 0.55" as a hard requirement. When I saw hot_take F1 = 0.00 it was immediately clear the model failed in a specific way, rather than looking at 66.7% accuracy and wondering if that's okay.

The part that diverged from the spec: the spec frames Section 6 as showing improvement over the baseline. My model regressed by 30 points. That's not a mistake — it's actually the most interesting finding. Small fine-tuning datasets help when the signal is lexical. When the task requires semantic judgment, a large pretrained model beats a small fine-tuned one.

---

## AI tools I used

**Testing my label definitions:** Before annotating anything, I gave Claude my definitions and asked it to generate posts that sit on the analysis/hot_take boundary. A few of them I couldn't cleanly classify, which told me my definitions needed tightening. That's how I landed on the "2+ specific verifiable data points = analysis" rule.

**Speeding up annotation:** I used an LLM to pre-label batches of 30-40 posts, then went through every one myself and corrected mistakes. Agreement was around 80%. The disagreements were almost all on analytical-framing hot takes — the same ones the fine-tuned model later got wrong.

**Finding patterns in the errors:** After getting my wrong predictions I pasted all 10 into Claude and asked what patterns it saw. It spotted the "sounds analytical but isn't" pattern right away. I went back through all 10 manually to check — it held for every single one.
