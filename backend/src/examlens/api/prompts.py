SYSTEM_PROMPT = """You are ExamLens, a local study assistant.
Use only the provided source context. Do not use outside knowledge.
If the answer is not supported by the sources, say: "Not found in the uploaded sources."
Be concise, exam-oriented, and structured.
Always include citations for factual statements.
Never invent facts or steps.
"""


def exam_writer_prompt(question: str, answer_mode: str, context: str) -> str:
    return f"""Write an exam-oriented answer using only the source context.

Question:
{question}

Answer mode:
{answer_mode}

Source context:
{context}

Rules:
- Use only facts supported by the source context.
- Keep the answer in the requested exam format.
- Include inline citations like [doc:page].
- If evidence is missing, say "Not found in the uploaded sources."
- Prefer short, high-value wording.

Return exactly:
Title:
Answer:
Citations:
"""


def notes_prompt(topic: str, context: str) -> str:
    return f"""Create study notes from the source context.

Topic:
{topic}

Source context:
{context}

Rules:
- Use Markdown.
- Include summary, key concepts, definitions, important points, formulas/steps, important questions, and viva questions.
- Keep it grounded in the sources.
- Add citations after each section.
"""


def diagram_prompt(topic: str, context: str, diagram_type: str) -> str:
    return f"""Generate Mermaid code grounded in the source context.

Task:
{diagram_type}

Topic:
{topic}

Source context:
{context}

Rules:
- Use only information found in the source context.
- Keep node labels short.
- Output valid Mermaid code only.
- If the source does not support a diagram, return: Not enough structured information for a reliable diagram.
"""

