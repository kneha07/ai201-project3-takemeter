# TakeMeter Planning Doc
## AI201 Project 3

---

## Community

I picked r/nba because I actually use it and I know how the conversations work. It's a huge subreddit (~7M members) and the posts vary wildly in quality. One comment section during a playoff game will have someone breaking down defensive rotations with stats, someone saying "LeBron is trash change my mind," and someone just screaming in all caps because Steph hit a half-court shot. That range is exactly what makes it interesting to classify.

The other reason I picked it is that r/nba users already talk about this stuff themselves. People call things out as "hot takes" all the time. The community has its own sense of what good vs. bad discourse looks like, which means my labels aren't arbitrary — they map to something real.

---

## Labels

I went with 3 labels. I thought about 4 but the fourth always collapsed into one of these three when I actually tried to use it.

**`analysis`** — the post is making an actual argument with real evidence. Stats, historical comparisons, tactical observations. Something a reasonable person could fact-check. If you removed all the opinion words, the argument would still hold up.

Examples:
- *"Jokic's assist-to-turnover ratio this playoffs (5.8) is better than any center in NBA history through 10+ games. People forget he's doing this while also leading the team in scoring and rebounding — no other player has ever done that in a conference finals."*
- *"The Warriors' net rating drops 14 points when Draymond is off the floor. That's not just about offense — their defensive rotations completely break down without him as the communicator. That's why the Draymond vs. Klay debate is a false choice."*

**`hot_take`** — bold opinion, no real evidence. The post is trying to win a debate by asserting loudly, not by actually arguing. Sometimes a stat shows up but it's there for decoration, not reasoning.

Examples:
- *"LeBron is not a top 5 player of all time and his fans need to accept it. MJ, Kareem, Magic, Bird, and Wilt were all better. No debate."*
- *"This Warriors dynasty is overrated. They got lucky with Durant falling into their lap. Any team with KD would have won those rings."*

**`reaction`** — pure emotion about something that just happened. A trade, a shot, a loss. No argument, just feeling. These posts don't really make sense if you don't know what event they're responding to.

Examples:
- *"CURRY JUST HIT THAT FROM HALF COURT ARE YOU KIDDING ME"*
- *"I cannot believe they traded him. This is the worst day of my NBA fan life."*

---

## Hard Edge Cases

The trickiest case by far is posts that *sound* like analysis but don't actually back up their claims. These look like `analysis` on the surface but are really `hot_takes`.

**Edge case 1: one-stat outrage**

*"His FG% was 38% and we're seriously calling him elite?? People are delusional."*

This could be `analysis` (there's a stat) or `hot_take` (it's just outrage). My rule: if you removed the emotional framing, would the evidence still make the case? One cherry-picked stat without context doesn't make an argument. → `hot_take`

**Edge case 2: emotional post with a complaint embedded in it**

*"I'm devastated they lost but honestly the refs were terrible tonight — 12 more free throws for the other team in the fourth quarter alone. That's not a coincidence."*

This has a specific number (12 free throws) and a claim. But the whole post is really about being upset about a loss. The reasoning is supporting the emotion, not the other way around. → `reaction`

**Edge case 3: bold claim with multiple real stats**

My rule here: if a post gives you 2 or more specific verifiable data points that actually support the claim, it's `analysis` regardless of how confident or aggressive the framing is. Confidence + evidence = analysis. Confidence alone = hot take.

---

## Data Collection Plan

I'm pulling from r/nba public posts and top-level comments — no nested replies because those tend to be short and context-dependent.

Main sources:
- Hot/top posts from the past 6 months
- Game threads (best source for `reaction`)
- Posts flaired "Discussion" or "Analysis"
- Weekly discussion threads

Target: roughly 65-70 per label so nothing is too lopsided. If a label falls below 20% after 150 examples I'll go hunt for more of those specifically. For `analysis` I'll look for posts with "film breakdown" or "stats" in the title. For `reaction` I'll dig into live game threads. For `hot_take` there are literally posts flaired "Unpopular Opinion."

I'll cut any post over ~500 characters to the first meaningful chunk, and skip anything that's mostly an image or video link.

---

## Evaluation Plan

Accuracy alone won't cut it here. If I accidentally end up with 80 `hot_take` examples and the model just learns to predict `hot_take` constantly, accuracy could look decent while being useless.

I'm going to report:
- Overall accuracy for both models
- Precision, recall, and F1 for each class
- Macro-averaged F1 — this treats all three classes equally, so a model that ignores one class entirely gets punished
- Confusion matrix for the fine-tuned model

The confusion matrix is the most useful thing because it shows me specifically which pairs of labels the model is confusing, not just that it's wrong.

**What does "good enough" look like to me:**
- Accuracy ≥ 70% on the test set
- No single class with F1 below 0.55 — the model has to be learning all three, not just two
- Fine-tuned model beats the zero-shot baseline by at least 10 points

If the fine-tuned model is actually worse than the baseline that's also interesting and worth writing about — it would mean fine-tuning on 200 examples hurt more than it helped.

---

## How I Plan to Use AI Tools

**Before annotating:** I'm going to give Claude my label definitions and ask it to generate posts that sit right on the `analysis`/`hot_take` boundary. If I can't cleanly classify those generated posts using my rules, my definitions need tightening. Better to find that out before labeling 200 examples than after.

**During annotation:** I'll use an LLM to pre-label batches of 30-40 posts at a time, then go through every single one and correct mistakes. This is a speed-up, not a shortcut — I still need to read and judge each post, the LLM just gives me a starting point.

**After getting results:** I'll paste all the wrong predictions into Claude and ask what patterns it sees. Then I'll verify those patterns myself by actually reading the examples. The point is that patterns are easier to spot when you see them all together — I might miss something looking at 10 wrong predictions one at a time.

---

## Hard Annotation Decisions (filled in during labeling)

**1. Jokic playmaking post**

*"Unpopular opinion: Nikola Jokic gets too much credit for his 'playmaking.' He has the ball a lot and makes easy passes — the reading he does is impressive but it's not that different from what other skilled bigs have done. The MVP hype around his passing is way overblown."*

I went back and forth on this one. It makes a comparative claim ("not that different from other skilled bigs") which sounds like reasoning. But no other players are named and no numbers are cited. Strip out the opinion framing and there's nothing left that would convince anyone of anything. → `hot_take`

**2. Lakers defensive rating post**

*"The Lakers' roster construction is fundamentally flawed. Their starting five has a combined defensive rating of 114.2 when LeBron and AD share the court but AD is at PF. When AD plays center with a stretch-4 beside him, that number drops to 107.8. The coaching staff inexplicably refuses to use this."*

The framing is aggressive ("fundamentally flawed," "inexplicably refuses") which pushed me toward `hot_take`. But I applied my 2-stat rule: two specific verifiable defensive ratings that directly support the claim. The angry tone is on top of an actual argument, not instead of one. → `analysis`

**3. LeBron Eastern Conference post**

*"The Eastern Conference has been bad for 15 years and all the impressive LeBron Finals runs came at the expense of easy paths through the East. If he played in the West his whole career the way MJ did, he has maybe two titles."*

This sounds historical and analytical. But "15 years" isn't cited anywhere, the counterfactual is pure speculation, and the conference disparity claim is just stated as obvious. The post gestures at evidence without ever actually producing it. → `hot_take`
