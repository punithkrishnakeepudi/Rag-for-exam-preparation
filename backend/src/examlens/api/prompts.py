SYSTEM_PROMPT = """You are ExamLens, a local study assistant.
Use only provided context. If context is insufficient, say "Not found in sources."
Be concise, exam-oriented, and structured. Always cite sources as [doc_id:page].
"""

def exam_writer_prompt(question: str, answer_mode: str, context: str) -> str:
    # Mode-specific instruction augmentation
    mode_map = {
        "2-mark": "Write a 2-mark answer: 1 clear definition and 2 supporting bullet points.",
        "5-mark": "Write a 5-mark answer: Introduction, 5 structured bullet points, and a concluding sentence.",
        "10-mark": "Write a 10-mark long-form answer: Detailed introduction, multiple themed sections with bullet points, and a summary.",
        "comparison": "Create a comparison table between the main entities mentioned.",
        "definition": "Provide a precise 1-sentence definition followed by a brief explanation.",
    }
    mode_instr = mode_map.get(answer_mode, f"Format the answer for {answer_mode}.")

    return f"""TASK: {mode_instr}
QUESTION: {question}
CONTEXT:
{context}

RULES:
1. Use ONLY context.
2. Structure with headings and bullets.
3. Citation format: [doc_id:page].
4. Return Answer ONLY.
"""

def notes_prompt(topic: str, context: str) -> str:
    return f"""Generate structured study notes for: {topic}
CONTEXT:
{context}

STRUCTURE:
# {topic}
## Summary
## Key Concepts
## Important Questions (Exam-style)
## Viva Questions

RULES: Use Markdown. Ground every claim in context.
"""

def diagram_prompt(topic: str, context: str, diagram_type: str) -> str:
    return f"""Task: Create a Mermaid.js {diagram_type} for {topic}.
CONTEXT:
{context}

RULES:
1. Output ONLY Mermaid code block.
2. Keep node labels under 5 words.
3. If context lacks process/hierarchy, say "Not enough info."
"""
