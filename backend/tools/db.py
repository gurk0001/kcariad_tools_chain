import psycopg
from typing import Dict, Any
import mysql.connector

# 1. Database Connection Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",        # Change to your MySQL username
    "password": "root@123", # Change to your MySQL password
    "database": "kcariad"
}

def init_db():
    """Bootstraps table schemas inside the live database automatically on server start."""
    try:
        print("Connecting to database and verifying schema mapping.")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. Ensure chat_history exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                thread_id VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_thread (thread_id)
            );
        """)

        # 🎯 FIX SCHEMA: Add custom_type safely if it doesn't exist yet
        # This prevents breaking an active table with historical developer logs
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
              AND TABLE_NAME = 'chat_history' 
              AND COLUMN_NAME = 'custom_type';
        """)
        column_exists = cursor.fetchone()[0]

        if not column_exists:
            print("Adding polymorphic column 'custom_type' to chat_history table architecture.")
            cursor.execute("""
                ALTER TABLE chat_history 
                ADD COLUMN custom_type VARCHAR(50) DEFAULT 'text';
            """)

        # 2. Tools Master Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                tool_id VARCHAR(50) PRIMARY KEY,
                tool_name VARCHAR(100) NOT NULL,
                version VARCHAR(30)
            );
        """)

        # 3. Use Cases Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS use_cases (
                usecase_id INT AUTO_INCREMENT PRIMARY KEY,
                tool_id VARCHAR(50),
                usecase_name VARCHAR(255) NOT NULL,
                UNIQUE KEY unique_tool_usecase (tool_id, usecase_name),
                FOREIGN KEY (tool_id) REFERENCES tools(tool_id) ON DELETE CASCADE
            );
        """)

        # 4. Error Codes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_codes (
                error_id INT AUTO_INCREMENT PRIMARY KEY,
                usecase_id INT,
                error_code VARCHAR(100) NOT NULL,
                error_description TEXT,
                UNIQUE KEY unique_usecase_error (usecase_id, error_code),
                FOREIGN KEY (usecase_id) REFERENCES use_cases(usecase_id) ON DELETE CASCADE
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("Successfully connected to Docker MySQL and verified schema mapping.")
    except Exception as e:
        print(f"Database initialization warning (Is your Docker container up?): {e}")



def get_db_history(thread_id: str):
    """Retrieves existing chat messages including custom structural types from MySQL to construct memory context."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT role, content, custom_type  FROM chat_history WHERE thread_id = %s ORDER BY id ASC", 
        (thread_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Pass dictionary format down to maintain custom layout visibility rules
    return [{"role": r["role"], "content": r["content"], "custom_type": r["custom_type"]} for r in rows]


def delete_db_history(thread_id: str = None) -> bool:
    """
    Deletes chat history entries from MySQL.
    If a thread_id is passed, it removes only that thread.
    If no thread_id is passed, it clears the entire chat_history table.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        if thread_id:
            # Delete historical rows for a specific session thread
            query = "DELETE FROM chat_history WHERE thread_id = %s"
            cursor.execute(query, (thread_id,))
            print(f"🗑️ Cleared database chat history logs for thread: {thread_id}")
        else:
            # Absolute truncate purge command clearing the entire history log table
            query = "TRUNCATE TABLE chat_history"
            cursor.execute(query)
            print("🗑️ Absolute database purge executed: All chat logs cleared.")
            
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Critical error executing history data deletion query: {e}")
        return False


def save_db_message(thread_id: str, role: str, content: str, custom_type: str = "text"):
    """Saves a singular message exchange chunk, tracking structural form flags to the MySQL engine."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (thread_id, role, content, custom_type) VALUES (%s, %s, %s, %s)",
        (thread_id, role, content, custom_type)
    )
    conn.commit()
    cursor.close()
    conn.close()


def upsert_tools_data(grouped_tools: Dict[str, Dict[str, Any]]):
    """
    Safely inserts or updates tools data in MySQL using standard MySQL syntax.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    # Using buffered=True to protect against cursor out-of-sync states during iteration loops
    cursor = conn.cursor(buffered=True)
    
    try:
        for tool_id, info in grouped_tools.items():
            
            # 1. Tool Upsert (MySQL syntax uses ON DUPLICATE KEY UPDATE)
            cursor.execute("""
                INSERT INTO tools (tool_id, tool_name, version)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    tool_name = VALUES(tool_name), 
                    version = VALUES(version);
            """, (tool_id, info["tool"], info["version"]))
            
            # 2. Process Use Cases
            for usecase_name in info["use_cases"]:
                cursor.execute("""
                    INSERT INTO use_cases (tool_id, usecase_name)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE usecase_name = usecase_name; 
                """, (tool_id, usecase_name))
                
                # Fetch the ID of the row we just inserted or touched
                cursor.execute("""
                    SELECT usecase_id FROM use_cases 
                    WHERE tool_id = %s AND usecase_name = %s
                """, (tool_id, usecase_name))
                res = cursor.fetchone()
                usecase_id = res[0] if res else None
                
                if usecase_id is None:
                    continue

                # 3. Process Error Codes
                mock_errors = [
                    {"code": f"ERR_{tool_id}_01", "desc": f"Updated description for {usecase_name}"},
                ]
                
                for err in mock_errors:
                    cursor.execute("""
                        INSERT INTO error_codes (usecase_id, error_code, error_description)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            error_description = VALUES(error_description);
                    """, (usecase_id, err["code"], err["desc"]))
        
        conn.commit()
        print("Database synchronization completed smoothly (Inserted/Updated via MySQL).")
    except Exception as e:
        conn.rollback()
        print(f"Error synchronization failed: {e}")
    finally:
        cursor.close()
        conn.close()

def get_tools_and_usecases_from_db() -> Dict[str, Dict[str, Any]]:
    """
    Retrieves grouped tools and use cases.
    """
    
    grouped_tools: Dict[str, Dict[str, Any]] = {}
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # Using dictionary=True makes rows accessible via column names like row['tool_id']
        cursor = conn.cursor(dictionary=True)
        
        # SQL query joining tools and their use cases
        query = """
            SELECT 
                t.tool_id, 
                t.tool_name, 
                t.version,
                u.usecase_name
            FROM tools t
            LEFT JOIN use_cases u ON t.tool_id = u.tool_id
            ORDER BY t.tool_id ASC, u.usecase_name ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # 3. Process database results into structured dict format
        for row in rows:
            tool_id = row["tool_id"]
            
            if not tool_id:
                continue
                
            # Initialize tool object if not seen yet
            if tool_id not in grouped_tools:
                grouped_tools[tool_id] = {
                    "tool_id": tool_id,
                    "tool": row["tool_name"],
                    "version": row["version"],
                    "use_cases": []
                }
            
            # Append usecase if it exists (handling tools that might have 0 use cases cleanly)
            if row["usecase_name"]:
                grouped_tools[tool_id]["use_cases"].append(row["usecase_name"])
                
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return {}

    return grouped_tools