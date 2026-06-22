# TakeMeter — Planning Document
## AI201 Project 3 | r/nba Discourse Quality Classifier

---

## Community

**Community:** r/nba (NBA basketball subreddit, ~7M members)

r/nba is one of the most active sports communities on Reddit, generating thousands of posts and comments daily surrounding games, trades, player performance, and league news. The discourse quality varies enormously — a single game thread can contain rigorous tactical breakdowns, bald-faced hot takes, and pure emotional reactions all in the same comment section. This variability makes it ideal for a classification task: the distinctions are meaningful to community members (r/nba regulars regularly call out "hot takes" and distinguish them from "actual analysis"), the text is rich and varied, and the labels have real cultural grounding in how the community talks about itself.

**Why it's a good fit:** The community has developed shared vocabulary and norms around discourse quality. The phrase "hot take" is used self-referentially by r/nba users. Posts range from multi-paragraph stat-backed arguments to single-sentence reactions — enough diversity for a model to learn genuine distinctions.

---

## Label Taxonomy

### Labels (3 total)

**`analysis`**
A post that makes a structured argument backed by statistics, historical comparison, or tactical/strategic observation. The evidence is specific and verifiable — someone could fact-check it. The argument could stand on its own if you removed the opinion framing.

Examples:
- *"Jokic's assist-to-turnover ratio this playoffs (5.8) is better than any center in NBA history through 10+ games. People forget he's doing this while also leading the team in scoring and rebounding — no other player has ever done that in a conference finals."*
- *"The Warriors' net rating drops 14 points when Draymond is off the floor. That's not just about offense — their defensive rotations completely break down without him as the communicator. That's why the Draymond vs. Klay debate is a false choice; the team simply doesn't work without Draymond."*

**`hot_take`**
A bold, confident opinion stated without meaningful supporting evidence. The claim may be true or false, but the post asserts rather than argues. The framing is often provocative or designed to generate debate. A stat may appear, but it's decorative rather than genuinely supporting the argument.

Examples:
- *"LeBron is not a top 5 player of all time and his fans need to accept it. MJ, Kareem, Magic, Bird, and Wilt were all better. No debate."*
- *"This Warriors dynasty is overrated. They got lucky with Durant falling into their lap. Any team with KD would have won those rings."*

**`reaction`**
An immediate emotional response to a specific game event, play, trade, or news. Little to no argument — the post is expressing a feeling in the moment. The content is event-anchored and would lose most of its meaning without knowing what just happened.

Examples:
- *"CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME"*
- *"I cannot believe they traded him. This is the worst day of my NBA fan life."*

---

## Hard Edge Cases

**Anticipated ambiguous case:** A post that includes one specific stat but is framed as outrage or bold assertion.

Example: *"His FG% was 38% and we're seriously calling him elite?? People are delusional."*

**Decision rule:** If the evidence genuinely supports the claim even without the emotional framing (i.e., a reasonable person would find the evidence compelling on its own), label it `analysis`. If the stat is cherry-picked, presented without context, or decorative — included to sound credible rather than to actually reason — label it `hot_take`. The one-stat outrage post above uses a stat as ammunition, not as part of an argument. → `hot_take`.

**Second edge case:** Long reaction posts that include some reasoning.

Example: *"I'm devastated they lost but honestly the refs were terrible tonight — 12 more free throws for the other team in the fourth quarter alone. That's not a coincidence."*

**Decision rule:** If the post's primary purpose is expressing an emotional state about a specific event, and any reasoning is subordinate to that emotional expression, label it `reaction`. If the reasoning is the main point and the emotion is context, label it `analysis` or `hot_take` depending on whether it's evidenced. The example above is primarily an emotional response with a supporting complaint — → `reaction`.

**Third edge case:** Posts that make a bold claim but also cite multiple pieces of evidence.

**Decision rule:** If the post provides ≥2 specific, verifiable data points that genuinely support the claim (not just two stats selected to sound good), label it `analysis` regardless of the confident framing. Strong confidence + actual evidence = `analysis`.

---

## Data Collection Plan

**Source:** Reddit r/nba — public posts and top-level comments collected from:
- Hot/top posts from the past 6 months
- Game threads (for reactions)
- Discussion/analysis flaired posts
- Weekly discussion threads

**Target distribution:** ~70 `analysis`, ~80 `hot_take`, ~70 `reaction` (roughly balanced, no label above 40% of total)

**Collection method:** Using the Reddit JSON API (no authentication required for public posts) or manual copy-paste from the subreddit. Posts and top-level comments only — nested replies tend to be shorter and context-dependent.

**If a label is underrepresented after 150 examples:** Search specifically for that label's characteristic posts. For `analysis`, look at posts with "film breakdown," "stats," or "advanced metrics" in the title. For `reaction`, pull from live game threads. For `hot_take`, search for "unpopular opinion" or "hot take" flaired posts.

**Text preprocessing:** Trim posts longer than 512 characters to the first complete sentence under that limit. Remove posts that are primarily images or video links with no substantive text.

---

## Evaluation Metrics

**Primary metric: Per-class F1 score**

Accuracy alone is insufficient for this task because:
1. A class-imbalanced dataset can produce high accuracy while failing entire label categories.
2. The cost of different errors is not equal — confusing `analysis` with `hot_take` is a more meaningful error than any confusion involving `reaction` (which tends to be more lexically distinct).

**Metrics I will report:**
- Overall accuracy (both models)
- Precision, Recall, and F1 per class (both models)
- Macro-averaged F1 (treats all classes equally regardless of size)
- Confusion matrix (fine-tuned model)

**Why macro F1 specifically:** With ~equal class sizes, macro F1 gives an unweighted average across all three classes — if the model collapses to predicting one class, macro F1 catches it where weighted F1 might not.

---

## Definition of Success

**Threshold for "good enough":**
- Fine-tuned model accuracy ≥ 0.70 on the test set
- No single class with F1 < 0.55 (the model must be learning all three distinctions)
- Fine-tuned model outperforms zero-shot baseline by ≥ 0.10 accuracy

**What would make this genuinely useful:** A classifier hitting 0.72+ accuracy with all per-class F1s above 0.60 could be embedded in a browser extension or subreddit tool that flags posts by type — useful for community moderators or researchers studying discourse quality.

**What I'd accept as deployment-ready:** Accuracy ≥ 0.72, macro F1 ≥ 0.70, and no class F1 below 0.60.

---

## AI Tool Plan

**1. Label stress-testing (before annotation):**
Give Claude the label definitions and edge case rules and ask it to generate 10–15 posts that sit at the boundary between `analysis` and `hot_take` (the hardest boundary). If I can't cleanly classify the generated posts using my definitions, I'll tighten the rules before annotating 200 examples.

**2. Annotation assistance:**
Use an LLM to pre-label batches of 30–40 posts at a time using my label definitions. I'll review and correct every pre-assigned label — pre-labeling is a speed-up, not a replacement for human judgment. All pre-labeled examples will be noted in a `notes` column in the CSV and disclosed here.

**3. Failure analysis:**
After getting wrong predictions from the notebook, paste all misclassified examples into Claude and ask: "What patterns do you see across these wrong predictions? Are there systematic linguistic or structural features that distinguish them?" Then verify each pattern by re-reading the examples myself before including it in the evaluation report.

---

## Hard Annotation Decisions (updated during Milestone 3)

1. **Stat-decorated assertion about Jokic's playmaking**

   Post: *"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done. The MVP hype around his passing is way overblown."*

   Could belong to: `hot_take` or `analysis` — the post acknowledges something verifiable ("he has the ball a lot") and makes a comparative claim about "other skilled bigs," which sounds like it's reasoning.

   Decision: → `hot_take`. The comparative claim ("not that different from other skilled bigs") is asserted without any actual evidence — no players are named, no numbers are cited. The structure is "I acknowledge the thing exists, but it's overhyped" which is the archetypal decorative-qualification hot take. Applying the decision rule from the Edge Cases section: remove the opinion framing and there's no argument left standing on its own.

2. **Bold claim + real statistic about roster construction**

   Post: *"The Lakers' roster construction is fundamentally flawed. Their starting five has a combined defensive rating of 114.2 when LeBron and AD share the court but AD is at PF — the worst configuration. When AD plays center with a stretch-4 beside him, that number drops to 107.8. The coaching staff inexplicably refuses to use this."*

   Could belong to: `hot_take` or `analysis` — the framing is accusatory ("inexplicably refuses," "fundamentally flawed") which reads like a hot take, but the post contains two specific, verifiable defensive ratings and a testable positional claim.

   Decision: → `analysis`. Applying the ≥2 specific verifiable data points rule: the post cites two distinct lineup defensive ratings (114.2 vs. 107.8) that directly support the claim. The emotional framing ("inexplicably refuses") is commentary on top of an actual argument, not a substitute for one. This was the clearest application of the "strong confidence + actual evidence = analysis" rule in the dataset.

3. **Era comparison with implicit but unverified claim**

   Post: *"The Eastern Conference has been bad for 15 years and all the impressive LeBron Finals runs came at the expense of easy paths through the East. If he played in the West his whole career the way MJ did, he has maybe two titles. The conference disparity is real and it matters."*

   Could belong to: `hot_take` or `analysis` — the claim about conference disparity is empirically checkable (win differential between conferences is a real statistic), and "15 years" sounds like a historical claim. But no actual data is cited.

   Decision: → `hot_take`. The "15 years" is rhetorical, not a verified figure. The counterfactual ("he has maybe two titles") is pure speculation. The conference disparity claim, while plausible, is stated as self-evident rather than supported. The post gestures at evidence without producing any. This is the pattern where a post sounds analytical because it references history and makes a comparative claim, but on inspection every statement is asserted rather than argued.
