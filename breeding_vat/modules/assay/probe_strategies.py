from typing import List, Dict


def direct(topic: str, n: int) -> List[str]:
    templates = [
        "What is {topic}?",
        "How does {topic} work?",
        "Explain {topic}.",
        "What are the main characteristics of {topic}?",
        "Describe {topic} in detail.",
        "What is the purpose of {topic}?",
        "How is {topic} typically used?",
        "What are examples of {topic}?",
        "Define {topic}.",
        "What is the history of {topic}?",
        "What are the benefits of {topic}?",
        "How do you implement {topic}?",
        "What are the key components of {topic}?",
        "What distinguishes {topic} from alternatives?",
        "What are common misconceptions about {topic}?",
    ]

    modifiers = ["Be specific.", "Give an example.", "Keep it concise."]
    questions = []

    for i in range(n):
        template = templates[i % len(templates)]
        question = template.format(topic=topic)
        if (i + 1) % 3 == 0:
            question += f" {modifiers[(i // 3) % len(modifiers)]}"
        questions.append(question)

    return questions


def adversarial(topic: str, n: int) -> List[str]:
    templates = [
        "Is it true that {topic} always fails in production?",
        "Why is {topic} so unreliable?",
        "Does {topic} cause more problems than it solves?",
        "Can {topic} be exploited by bad actors?",
        "Isn't {topic} just a temporary trend?",
        "Why would anyone choose {topic} over established alternatives?",
        "How has {topic} disappointed users?",
        "What are the hidden flaws in {topic}?",
        "Isn't {topic} fundamentally broken?",
        "Why did {topic} fail at its original goal?",
        "Doesn't {topic} require unrealistic assumptions?",
        "What dangerous side effects does {topic} have?",
        "Isn't {topic} just expensive hype?",
        "Why do experts dismiss {topic}?",
        "Has {topic} been proven to be ineffective?",
    ]

    modifiers = ["Be direct.", "Provide evidence.", "Don't hedge."]
    questions = []

    for i in range(n):
        template = templates[i % len(templates)]
        question = template.format(topic=topic)
        if (i + 1) % 3 == 0:
            question += f" {modifiers[(i // 3) % len(modifiers)]}"
        questions.append(question)

    return questions


def edge_case(topic: str, n: int) -> List[str]:
    templates = [
        "What happens when {topic} encounters extreme scale?",
        "How does {topic} behave under resource constraints?",
        "What are the limits of {topic}?",
        "Can {topic} handle contradictory inputs?",
        "What happens when {topic} fails?",
        "How does {topic} perform at its worst?",
        "What edge cases break {topic}?",
        "How does {topic} scale to very large inputs?",
        "What happens when {topic} receives malformed data?",
        "Can {topic} operate in zero-resource environments?",
        "What happens when all assumptions of {topic} are violated?",
        "How does {topic} behave with extremely rare scenarios?",
        "What are the breaking points of {topic}?",
        "How does {topic} handle simultaneous failures?",
        "What happens when {topic} operates backwards?",
    ]

    modifiers = ["Be thorough.", "Give a specific scenario.", "Consider cascading failures."]
    questions = []

    for i in range(n):
        template = templates[i % len(templates)]
        question = template.format(topic=topic)
        if (i + 1) % 3 == 0:
            question += f" {modifiers[(i // 3) % len(modifiers)]}"
        questions.append(question)

    return questions


def ambiguous(topic: str, n: int) -> List[str]:
    templates = [
        "Is {topic} better than its alternatives?",
        "Should {topic} be used in all contexts?",
        "Is {topic} overrated?",
        "Would {topic} be appropriate for critical systems?",
        "Is {topic} worth the learning curve?",
        "Should organizations adopt {topic}?",
        "Is {topic} the right approach for the future?",
        "Does {topic} deserve more attention than it gets?",
        "Is {topic} too complex for practical use?",
        "Would {topic} improve your workflow?",
        "Is {topic} worth the trade-offs?",
        "Should {topic} replace existing solutions?",
        "Is {topic} the best choice available?",
        "Would investing in {topic} be worthwhile?",
        "Is {topic} undervalued or overhyped?",
    ]

    modifiers = ["Justify your position.", "Consider both sides.", "What's your confidence level?"]
    questions = []

    for i in range(n):
        template = templates[i % len(templates)]
        question = template.format(topic=topic)
        if (i + 1) % 3 == 0:
            question += f" {modifiers[(i // 3) % len(modifiers)]}"
        questions.append(question)

    return questions


STRATEGIES = {
    "direct": direct,
    "adversarial": adversarial,
    "edge_case": edge_case,
    "ambiguous": ambiguous,
}


def generate_probes(topic: str, n_per_strategy: int = 12) -> Dict[str, List[str]]:
    return {
        "direct": direct(topic, n_per_strategy),
        "adversarial": adversarial(topic, n_per_strategy),
        "edge_case": edge_case(topic, n_per_strategy),
        "ambiguous": ambiguous(topic, n_per_strategy),
    }
