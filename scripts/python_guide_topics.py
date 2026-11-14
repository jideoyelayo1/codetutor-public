"""Original executable micro-labs. Cases and semantic mutations are authored with each topic."""
TOPICS = []
def add(stage, key, title, explanation, pitfall, body, cases, mutation, imports="", *, supplemental=False, independent=False):
    assert mutation[0] in body, (key, mutation)
    TOPICS.append(dict(stage=stage, key=key, title=title, explanation=explanation, pitfall=pitfall,
                       body=body, cases=cases, mutation=mutation, imports=imports,
                       **({"supplemental":True} if supplemental else {}), **({"independent":True} if independent else {})))

add(1, "first-expression", "Run a first expression", "An expression computes a value. Python evaluates multiplication before addition; parentheses make a different grouping explicit. Assigning the result binds a name that print can display.", "Grouping addition before multiplication changes this contract.", "result = data[0] + data[1] * data[2]", [([2,3,4],14),([5,2,3],11),([0,4,0],0)], ("data[0] + data[1] * data[2]", "(data[0] + data[1]) * data[2]"))


TOPICS[0]['introParagraphs'] = [
    "No programming experience is assumed. Read this guide in order, predict the examples, then try the implementation and debugging problems before revealing answers. Lessons, quizzes and saved notes work offline. The Lab needs your configured personal execution server; an unavailable server does not prevent reading or practice notes.",
    "On a computer with Python 3.13 installed, open a terminal and check python3 --version. Create a plain-text file hello.py containing print('Hello, Python'), then run python3 hello.py from that file's directory. The terminal runs commands; the Python prompt evaluates Python. Exit the interactive prompt before trying a terminal command.",
    "The examples use data as the input name and result as the computed output. Square brackets hold an ordered list; data[0] selects its first item. The import json and final print lines are a shared display wrapper. Start by tracing the arithmetic between them; later stages explain modules, files and functions in detail."
]

import python_guide_core
import python_guide_advanced
import python_guide_scientific
import python_guide_ml
import python_guide_torch
import python_guide_systems

from python_guide_book_topics import register as register_book_topics
register_book_topics(add)
