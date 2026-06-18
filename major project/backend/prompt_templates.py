SUGGESTION_PROMPT = """You are an expert career counselor. Analyze the student feedback and provide actionable improvement strategies in valid JSON format.

FEEDBACK: {feedback_text}
SENTIMENT: {sentiment}
DOMAIN: {domain}
DOMAIN NOTE: {domain_note}

Generate this exact JSON structure with ALL fields (ensure proper closing of all brackets). All content MUST be specific to the DOMAIN above — use domain terminology, relevant tasks, and domain-appropriate resources only. Keep each list to EXACTLY 3 concise, high-quality items to minimize length and latency:

{{
    "title": "Specific improvement focus area",
    "primary_focus": "technical_skills|communication|time_management|leadership",
    "urgency": "high|medium|low",
    "immediate_actions": [
        "Action 1: Clear step with implementation details and outcome",
        "Action 2: Concrete action with next steps",
        "Action 3: Practical step with resources"
    ],
    "weekly_goals": [
        "Week 1-2: Goals with specific tasks and milestones",
        "Week 3-4: Intermediate goals with exercises",
        "Week 5-6: Advanced objectives with projects"
    ],
    "resources": [
        "Specific platform/course: Name the exact resource with URL or platform",
        "Tool/software: Name specific tools with key features to learn",
        "Online community or book/tutorial: Provide actual title or forum/group"
    ],
    "success_metrics": [
        "Measurable indicator: e.g., '80% score on practice tests'",
        "Skill assessment: e.g., 'Complete 3 projects demonstrating X skill'",
        "Time-based or portfolio goal: e.g., 'Reduce task time by 30%'"
    ],
    "timeline": "6-8 weeks with daily practice"
}}

IMPORTANT REQUIREMENTS:
- Every section must be clearly tied to the DOMAIN. Avoid generic cross-domain advice.
- Use domain vocabulary and examples. For law: IPC sections, case briefs, Bare Acts; for medical: clinical terminology, case studies, labs; for engineering: coding platforms, projects, frameworks; for management: case frameworks, analytics, dashboards.
- Make "resources" SPECIFIC with actual platform names (e.g., "Codecademy Python Course", "LeetCode for algorithms", "Stack Overflow community")
- Make "success_metrics" MEASURABLE with actual numbers and clear criteria
- Include primary_focus and urgency fields
- Output ONLY valid, complete JSON. Close all strings, arrays, and objects properly."""

QUALITY_CHECK = """Evaluate the generated suggestion against these strict quality standards:

1. DETAIL & DEPTH:
   - Are immediate actions 2-3 sentences each with clear reasoning?
   - Are weekly goals comprehensive paragraphs (not one-liners)?
   - Do resources include specific names, platforms, and modules?
   
2. SPECIFICITY:
   - Are all suggestions actionable with concrete steps?
   - Do metrics include actual numbers and timeframes?
   - Are examples industry-relevant and modern?
   
3. COMPREHENSIVENESS:
   - Does it cover technical AND soft skills?
   - Are there at least 4-5 immediate actions?
   - Are there 4 weekly goal periods with detailed tasks?
   - Are there 5+ specific resources with implementation guidance?
   
4. PERSONALIZATION:
   - Does it directly address the feedback provided?
   - Is it appropriate for the {level} student level?
   - Does it consider the specific domain context?
   
5. PRACTICALITY:
   - Can a student follow this plan step-by-step?
   - Are timeframes realistic (8-week focus)?
   - Are resources accessible and available?

REJECT AND REGENERATE if:
- Any section has generic or vague advice
- Immediate actions are less than 2 sentences each
- Weekly goals are one-liners instead of detailed paragraphs
- Resources lack specific names or implementation details
- Success metrics aren't quantifiable with numbers

The suggestion must be comprehensive enough to serve as a complete development roadmap."""
