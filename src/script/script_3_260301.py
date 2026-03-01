from langchain_core.messages import HumanMessage
from src.graph import graph

queries = [
    "히가시노 게이고 신간 책 알려줘",
    "파친코 책 최저가랑 내용 알려줘",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    for chunk in graph.stream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
    ):
        for node, data in chunk.items():
            print(f"\n[{node}]")
            if "classification" in data:
                c = data["classification"]
                print(f"  intent: {c.get('intent')}")
                print(f"  query : {c.get('query_related_to_intent')}")
            if "search_results" in data:
                for r in data["search_results"]:
                    print(f"  tool  : {r.get('tool')}")
                    print(f"  data  : {r.get('data')}")
            if "draft_response" in data:
                print(f"  response: {data['draft_response']}")
