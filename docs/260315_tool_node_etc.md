### tool node의 동작
1. 전제: 다른 노드에서 model.bind_tools()를 사용해 state["messages"]에 tool_calls가 포함된 AIMessage를 append
```
def book_search(state: OverallState) -> dict:
    """LLM이 어느 tool 노드로 갈지, 혹은 둘 다 갈지 결정."""
    model_with_tools = llm.bind_tools([basic_book_search, price_description_book_search])
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}
```
2. tool node가 tool_calls의 내용을 읽고 tool 실행
3. ToolMessage 출력한 후 state["messages"]에 append

### tool condition의 동작과 model.bind_tools() 와 ToolNode의 상호작용
```
builder = StateGraph(OverallState)

builder.add_node("classify_intent", classify_intent)
builder.add_node("book_search", book_search)
builder.add_node("book_search_tool_node", book_search_tool_node)
builder.add_node("draft_response", draft_response)

builder.add_edge(START, "classify_intent")
builder.add_conditional_edges("book_search", tools_condition, {"tools": "book_search_tool_node", END: "draft_response"})
builder.add_edge("book_search_tool_node", "book_search")
builder.add_edge("draft_response", END)
```
`builder.add_conditional_edges("book_search", tools_condition, {"tools": "book_search_tool_node", END: "draft_response"})`: state["messages"][-1]이 tool_calls를 가지고 있으면 "tools"에 해당하는 노드로 이동, tool calls 없으면 END로 이동
- book_search 노드는 state["messages"]만 보고 tool_calls를 더 할지 말지 판단함.
`builder.add_edge("book_search_tool_node", "book_search")`: book_search_tool_node의 결과가 state["messages"]에 저장되고 book_search 노드는 다시 그것을 이용함

### 기타
```
builder.add_conditional_edges("book_recommendation", tools_condition, {"tools": "book_recommendation_tool_node", "__end__": "draft_response"})
```
- "\_\_end\_\_"를 "END"로 쓰지 말것; langgraph-cli가 처리를 못함

### Command Literal을 통해 노드와 노드사이를 이어주기
- 노드와 노드는 edge를 통해서 이을 수도 있지만
- 노드의 output값에 Command를 넣어서 이을 수도 있다.
- 근데 이렇게 하면 가독성이 떨어지는 것 같아서, 좀 조사해보고 edge로 통일할 생각이다.
- claude답변
```
Command가 유리한 경우와 edge가 유리한 경우가 다릅니다.

Command가 더 나은 경우

classify_intent처럼 state 업데이트 + 동적 라우팅을 동시에 해야 할 때
런타임에 어디로 갈지 결정되는 경우
edge가 더 나은 경우

book_search → book_search_tool_node처럼 항상 고정된 경로일 때
tools_condition처럼 조건 로직이 노드와 분리되는 게 명확할 때
현재 코드에서 classify_intent는 Command가 적합하고, book_recommendation은 아까 버그처럼 Command 어노테이션만 붙이고 실제로는 dict를 반환해서 문제가 됐죠.

통일보다는 용도에 맞게 구분해서 쓰는 게 더 명확할 것 같습니다.
```
