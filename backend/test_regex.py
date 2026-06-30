import re

relevant = "Thinking humanly(Cognitive Modeling Approach) Science of making machines that think like people Cognitive modelling approach (Thinking like a human) Human thinking can be studied in three main ways. • Introspection involves examining our own thoughts as they occur. • Psychological experiments study human behavior by observing people performing tasks. Limitations: 1. Human thinking is complex 2. Hard to accurately model"

formatted = re.sub(r'[•\-\*]\s+', '\n- ', relevant)
formatted = re.sub(r'\s+(\d+\.\s)', r'\n\n\1', formatted)

print(repr(formatted))
