from dotenv import load_dotenv
load_dotenv()

from book_chatbot.agent import book_memo_agent, book_memo
from book_chatbot.tool_schema import BookMemoRecord


def test_book_memo_agent():
    query = (
        "내가 생각을 넓혀주는 독서법 31페이지까지 읽었는데 "
        "깨달음에 의한 배움과 교육에 의한 배움에 차이가 있다는 부분이 인상적이었어"
    )

    result = book_memo_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    record: BookMemoRecord = result["structured_response"]

    print("도서명:", record.book.title)
    print("저자:", record.book.author)
    print("출판사:", record.book.publisher)
    print("ISBN:", record.book.isbn)
    print("읽은 페이지:", record.memo.pages_read)
    print("감상:", record.memo.impression)

    assert record.book.title
    assert record.memo.pages_read == 31
    assert record.memo.impression


# def test_book_memo_tool():
#     query = (
#         "히가시노 게이고의 용의자X의 헌신을 120페이지까지 읽었는데 "
#         "반전이 정말 인상 깊었어"
#     )

#     output = book_memo.invoke({"request": query})
#     print(output)


if __name__ == "__main__":
    test_book_memo_agent()
    print("-" * 40)
    # test_book_memo_tool()
