import os
os.environ["PYDEVD_USE_SYS_MONITORING"] = "0"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langchain_core.messages import HumanMessage
from src.graph import graph

queries = [
    "히가시노 게이고 신간 책이랑 파친코 책 최저가를 알려줘"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    for chunk in graph.stream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()
