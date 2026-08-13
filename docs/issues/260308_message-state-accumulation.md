## 260328
* messages랑 classify intent가 계속 쌓인다.
* claude 답변

두 가지 문제가 보입니다.

### 문제 1: messages 중복 축적
messages에 add_messages reducer가 붙어있어서 append 방식으로 쌓입니다. 그런데 classify_intent에서 원본 HumanMessage가 있는데, 분기된 intent별 sub-query를 또 HumanMessage로 추가하고 있어서 중복이 생깁니다.


* classify_intent에서 이걸 추가함
```
"messages": [HumanMessage(content=first_intent["query_related_to_intent"])],
```
* route_next_intent에서도 또 추가함
```
"messages": [HumanMessage(content=next_intent["query_related_to_intent"])],
```

### 문제 2: classification/remaining_intents 안 사라짐
* classification과 remaining_intents는 reducer가 없는 단순 필드라 덮어쓰기는 되지만, checkpointer 쓸 때 다음 턴에도 이전 값이 남아있습니다. classify_intent 진입 시 초기화가 필요합니다.

#### 수정 방향
* graph.py의 classify_intent:
```

return Command(
    update={
        "classification": intents,
        "remaining_intents": remaining,
        "draft_response": None,  # 이전 턴 결과 초기화
        # messages에 sub-query 따로 추가하지 말고
        # 원본 메시지 그대로 각 노드에서 사용
    },
    goto=INTENT_TO_NODE[first_intent["intent"]],
)
```
그리고 book_search, book_recommendation 노드에서 state["messages"] 대신 분류된 query를 사용하도록:

```
def book_search(state: OverallState) -> dict:
    model_with_tools = llm.bind_tools([basic_book_search, price_description_book_search])
    # classification에서 해당 intent의 query를 꺼내서 사용
    query = next(c["query_related_to_intent"] for c in state["classification"] if c["intent"] == "book_search")
    response = model_with_tools.invoke([HumanMessage(content=query)])
    return {"messages": [response]}
```
이렇게 하면 messages에는 원본 대화만 쌓이고, sub-query는 classification에서 참조하게 됩니다.

수정해드릴까요?