import os
import bcrypt
import psycopg2

def get_conn():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="localhost",
        port=os.getenv("POSTGRES_PORT", "5432"),
    )

def get_user(username: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()

def create_user(username: str, password: str) -> int:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, password_hash)
            )
            return cur.fetchone()[0]

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def save_message(thread_id: str, user_id: int, role: str, content: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (thread_id, user_id, role, content) VALUES (%s, %s, %s, %s)",
                (thread_id, user_id, role, content)
            )

def load_messages(thread_id: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT role, content FROM conversations WHERE thread_id = %s ORDER BY created_at",
                (thread_id,)
            )
            return [{"role": row[0], "content": row[1]} for row in cur.fetchall()]

def get_threads(user_id: int) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT thread_id,
                       (SELECT content FROM conversations c2
                        WHERE c2.thread_id = c1.thread_id AND c2.role = 'user'
                        ORDER BY c2.created_at ASC LIMIT 1) as title,
                       MAX(created_at) as last_active
                FROM conversations c1
                WHERE user_id = %s
                GROUP BY thread_id
                ORDER BY last_active DESC
            """, (user_id,))
            return [
                {
                    "thread_id": row[0],
                    "title": (row[1][:25] + "...") if row[1] and len(row[1]) > 25 else (row[1] or "새 대화"),
                }
                for row in cur.fetchall()
            ]
