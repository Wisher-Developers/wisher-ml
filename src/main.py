import psycopg2
from config import host, user, password, db_name
from embedding_util import create_single_embedding

def run():
    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=5432,
        database=db_name
    )

    # Create a cursor to execute SQL commands
    cur = conn.cursor()

    try:
        sentences = [
            "Удобное одеяло комфорта"
        ]

        # Insert sentences into the items table
        for sentence in sentences:
            embedding = create_single_embedding(sentence)
            cur.execute(
                "INSERT INTO items (content, embedding) VALUES (%s, %s)",
                (sentence, embedding)
            )

    except Exception as e:
        print("Error executing query", str(e))
    finally:
        # Close communication with the PostgreSQL database server
        cur.close()
        conn.close()

# This check ensures that the function is only run when the script is executed directly, not when it's imported as a module.
if __name__ == "__main__":
    run()
