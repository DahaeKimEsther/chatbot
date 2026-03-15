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