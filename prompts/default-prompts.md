# Thematic analysis prompts

# 1-Open codes

You are a senior user researcher and product strategy leader assisting with qualitative analysis.

I am uploading a single interview transcript for open coding. Please develop a detailed initial coding framework for this transcript.

**Instructions:**

1. Read the transcript carefully and identify meaningful segments.
2. For each code, provide:
   - **Code name**: A concise descriptive label
   - **Verbatim quote(s)**: The exact word-for-word text from the transcript that supports this code. Do not paraphrase, summarize, or create representative quotes.
   - **Speaker**: Who said it (participant name, not the moderator)
3. Only code statements from the participant. Do not code the moderator's questions or comments.

About the research team: The following people are part of the research team and should NOT be coded as participants: {{TEAM_MEMBERS}}. Only code statements from the interview participant.

**At the end of your analysis, provide a clean numbered list of all code names only** (no quotes, no speaker attribution — just the code labels). This list will be used for cross-transcript synthesis.

---

# 2-Axial/Focus coding

We are now moving to stage 2 of the analysis. Now group all codes that belong to the same topic, and merge duplicates. The goal is to group the existing codes into coherent thematic clusters based on shared meaning.

**\*Instructions\***

**1.Grouping Logic**

\-Group codes that reflect the same underlying concept, issue, or phenomenon.

\-Do not group codes based on superficial similarity in wording. Focus on meaning.

\-Avoid overly broad clusters. Each group must be conceptually coherent.

**2.Merging Duplicates**

\-Identify and merge duplicate or highly overlapping codes.

\-When merging, retain the most precise and descriptive label.

\-List all original codes that were merged.

**3.Cluster Construction**

\-Each cluster should represent a distinct topic.

\-A code should appear in only one cluster unless there is a strong justification for overlap (flag explicitly if so).

**4.Standalone Codes**

\-If a code does not meaningfully relate to others, keep it as a standalone cluster.

\-Do not force grouping.

**5.Quality Control**

\-Ensure internal coherence (codes in a cluster clearly belong together)

\-Ensure external distinction (clusters are meaningfully different from each other)

**\*Output Format\***

For each cluster:

\-Cluster Name: \[Concise descriptive label\]

\-Core Concept: \[1–2 sentence explanation of shared meaning\]

For merged Codes (if applicable):

\-Original → Final label

---

# 3- "What" \-Develop themes

Develop a thematic framework that answers the following research questions:

{{RESEARCH_QUESTIONS}}

**\*Instructions\***

**1.Theme Construction**

\-Develop higher-order themes by synthesizing clusters of codes.

\-Each theme must represent a pattern of shared meaning relevant to the research questions (not just a topic label).

\-Avoid purely descriptive themes—prioritize interpretive/analytical themes.

**2.Link to Research Questions**

\-Explicitly indicate which research question(s) each theme addresses.

\-Themes may address multiple questions, but this must be justified.

**3.Hierarchy**

Ensure clear hierarchical relationships, not flat lists. Organize into:

\-Main themes (broad, central patterns)

\-Sub-themes (more specific dimensions within each theme)

\-Add supporting verbatim quotes and specify who said it.

4\.**Use of Codes**

Show how themes are grounded in data by:

\-Listing representative codes for each (sub-)theme

You may merge, rename, or reorganize codes, but:

\-Preserve conceptual meaning

\-Avoid unnecessary loss of nuance

**5.Refinement Criteria**

Ensure:

\-Internal coherence (elements within a theme fit together)

\-External distinction (themes are meaningfully different)

\-Analytical usefulness (themes help answer the research questions)

**6\. Interpretive Layer**

Go beyond categorization:

\-Identify patterns, tensions, or contradictions

\-Highlight processes (e.g., how bias emerges, is negotiated, or mitigated)

---

# 4-"So what?" \- Why it matters

Now act as a senior product strategy advisor translating qualitative research findings into business and product implications.

Interpret the thematic findings to explain:

* **Why these insights matter for the business**
* **Why product leaders should care**
* **How these insights should shape product strategy, decisions, and priorities**

**\*Business context\***

{{BUSINESS_CONTEXT}}

**\*Instructions\***

**1.Translate Themes → Business Impact**

For each major theme:

\-Explain the practical consequence for product development, user experience, or market positioning

\-Focus on risk, opportunity, and trade-offs

**2.Focus on Product-Relevant Dimensions**
 Where applicable, connect insights to:

\-Model performance & reliability

\-User trust & adoption

\-Global scalability / localization

\-Data strategy & annotation pipelines

\-Compliance, policy, and reputational risk

**3.Make It Decision-Oriented**

Avoid abstract statements (e.g., "bias is important"). Instead, frame insights as:

\-What product leaders may be getting wrong or overlooking

\-Where current approaches are insufficient

\-What decisions need to change

**4.Surface Strategic Tensions**

\-Highlight trade-offs (e.g., speed vs. cultural nuance, scale vs. localization)

\-Identify where different stakeholders (engineers, annotators, policymakers) are misaligned

**5.Actionable Framing**

Translate insights into:

\-Strategic priorities

\-Product design considerations

\-Organizational implications (e.g., workflows, roles, incentives)

**6.No Generic Ethics Language**

\-Ground everything in product and business consequences

\-Avoid vague recommendations unless tied to concrete impact

**\*Output Format\***

**1\. Executive Summary (5–7 sentences)**

* Clear, high-level articulation of why this matters for the business

**2\. Strategic Implications by Theme**

**For each theme:**

**Theme:**
 **Why It Matters (Business Impact):**

* How this affects product outcomes, risk, or growth

**Implications for Product Leaders:**

* What they should start/stop/change

**Key Trade-offs / Tensions:**

* Any conflicting priorities revealed

**3\. Cross-Cutting Strategic Insights**

* 3–5 high-level insights that cut across themes
   (e.g., systemic risks, organizational blind spots)

**4\. Recommended Strategic Priorities**

* Priority 1:
* Priority 2:
* Priority 3:

---

# 5-"Then what?" \- Recommendations

* Move from **insight → execution**

Acting as a senior product strategy leader defining concrete next steps based on qualitative research insights. Translate the thematic findings and strategic implications into **clear, prioritized, and actionable recommendations** for product and organizational action.

Focus on:

\-What should be done **next**

\-How it should be done

\-Who should own it

\-Why it is strategically important

\*Instructions\*

1.Prioritize Ruthlessly

\-Recommend **3–5 high-impact actions max**

\-Focus on what will materially change product outcomes or risk exposure

\-Avoid "nice-to-have" recommendations

\-Avoid "doing more research" as a next step.

**2.Be Concrete and Operational**
 For each recommendation, specify:

\-What exactly should be done

\-How it would be implemented (process, system, or change)

\-Who should own it (e.g., Product, Eng, Data, Policy)

**3.Tie to Business Impact**

Explicitly connect each recommendation to:

\-Risk reduction

\-Product quality / performance

\-User trust / market impact

**4.Incorporate Time Horizons**

Classify actions as:

\-Immediate (0–3 months)

\-Mid-term (3–9 months)

\-Long-term (9+ months)

**5.Address Strategic Tensions**

\-Where relevant, acknowledge trade-offs

\-Indicate what is being optimized vs. deprioritized

**6.Feasibility and Leverage**

\-Prioritize actions that are implementable within a product org

\-Avoid recommendations that require unrealistic structural change unless flagged as long-term

**\*Output Format\***

1\. Executive Direction (3–5 sentences)

* Overall strategic posture (e.g., "shift from reactive bias mitigation to proactive design")

2\. Priority Recommendations

For each recommendation:

**Recommendation Title**:
 **What to Do**: (specific action)
 **Why It Matters**: (business/product impact)
 **How to Execute**: (concrete steps or mechanism)
 **Owner(s)**: (team/function)
 **Time Horizon**: (Immediate / Mid / Long-term)
 **Key Trade-offs**: (if any)

3\. Sequencing / Roadmap Logic

* Brief explanation of what should happen first and why

4\. Risks of Inaction

* 2–3 concise statements about what happens if these actions are not taken

---

# 6-Find the gaps (do after 3 or at the end?)

Now identify unanswered questions, limitations, and research gaps based on the study's research questions, dataset, and thematic findings.

**\*Instructions\***

**1.Assess Coverage of Research Questions**

For each research question:

\-Evaluate how fully it is answered by the themes

\-Identify partial answers, weak coverage, or missing dimensions

**2.Identify Types of Gaps:**
Distinguish clearly between:

\-Empirical gaps: e.g., Missing perspectives, stakeholders, or contexts

\-Conceptual gaps: e.g., Aspects of cultural bias or related constructs not explored

\-Process gaps: e.g., Stages of AI development insufficiently examined

\-Comparative gaps: e.g., Lack of contrast across groups

\-Methodological gaps: e.g., Limits caused by data type, sampling, or approach

**3.Unanswered or Emergent Questions**

Generate specific, researchable questions that arise from:

\-Tensions or contradictions in the themes

\-Areas where themes are underdeveloped

\-Implicit issues not directly addressed

**4.Grounding Requirement**

Every identified gap must be:

\-Linked to specific themes or missing areas in the analysis

\-Linked to the research questions

\-Not generic

**5.Prioritization**

Indicate which gaps are:

\-Critical (undermine core findings)

\-Important (limit depth or scope)

\-Future research opportunities

**\*Output Format\***

**1\. Coverage Assessment by Research Question**

\-RQ1: \[Assessment \+ gaps\]

\-RQ2: …

**2\. Identified Gaps**

For each gap:

Gap Type: (empirical / conceptual / etc.)
 Description:
 What is Missing:
 Linked Theme(s):
 Why It Matters:

**3\. Unanswered / Emerging Research Questions**

\-Question 1

\-Question 2

\-…

**4\. Priority Summary**

\-Critical gaps:

\-Important gaps:

\-Future research directions:

---

# 7-Reporting

Now, synthesize the full analysis into a concise, executive-ready report (maximum \~6 pages) that communicates the most important insights, implications, and recommendations.

Produce a clear, tightly structured report that:

* Answers the research questions
* Highlights the most important themes and insights
* Explains why findings matter for the business
* Provides concrete, prioritized recommendations

**\*Instructions\***

**1.Prioritize Ruthlessly, force compression without sacrificing meaning**

\-Include only the most important insights

\-Remove redundancy or duplicates across sections

\-Do not repeat the same idea in multiple places

**2.Narrative Flow**

\-Ensure a logical progression:
Context/Findings → Business implications/Why it matters → What to do next/Recommendations

\-Avoid "stage-by-stage" structure, no mention of coding.

**3\. Analytical Density**

\-Favor insight-rich synthesis over descriptive summaries

\-Each paragraph should deliver a distinct point

**4\. Audience Calibration**

Write for product leaders / decision-makers and emphasize:

\-Business impact

\-Product risk/opportunity

\-Strategic trade-offs

**5.Conciseness Constraints**

\-Target \~6-10 pages equivalent (word, google docs)

\-Use tight language; avoid filler, and academic hedging

\-Avoid generic language

**\*Output Structure\***

**Insights**

3–5 major themes, for each, structure each as as "what \- findings" → "So what \- why this matters" → "Then what \- recommendations"

**Findings:**
\-Clear analytical insight (not just description)

\-What's actually happening

\-Any key tension or contradiction

**Why This Matters:**

\-Business and product implications

\-Risk exposure

\-Impact on product quality, trust, scalability

\-Highlight what product teams are likely underestimating or missing

**Recommendations:**

\-Prioritized actions

\-What to do

\-Why it matters

\-High-level execution approach

**Then Gaps & Open Questions (½–1 page)**

\-Most critical gaps only, frame them as:

\-What we still don't understand

\-Why that uncertainty matters for decisions

---

# Fetch information

I will attach X transcripts. Across all of them, I will ask you to find specific meaning, quotes, and themes.

Remember that verbatim quotes must be word for word text from the doc I uploaded. Do not create representative quotes or passages or summarize them.

About the research team: The following people are part of the research team and should NOT be treated as participants: {{TEAM_MEMBERS}}. Only extract quotes from interview participants.

---
