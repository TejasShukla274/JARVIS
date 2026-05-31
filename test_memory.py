"""Quick integration test for the memory system."""

import sys
sys.path.insert(0, ".")

# 1. Initialize MySQL
from database.mysql_connector import initialize_mysql
assert initialize_mysql(), "MySQL init failed"

# 2. Initialize MemoryManager
from memory.memory_manager import memory_manager
memory_manager.initialize()

# 3. Clean slate — delete test keys if they exist
for k in ["name", "home_city", "favorite_game", "college", "birthday"]:
    memory_manager.delete(k)

print("\n" + "=" * 60)
print("TEST 1: Save via voice command")
print("=" * 60)

from core.memory_handler import handle_memory_command

resp = handle_memory_command("my name is tejas")
print(f"  Input:    'my name is tejas'")
print(f"  Response: {resp}")
assert "saved" in resp.lower() or "tejas" in resp.lower(), f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 2: Read back")
print("=" * 60)

resp = handle_memory_command("what's my name")
print(f"  Input:    'what's my name'")
print(f"  Response: {resp}")
assert "Tejas" in resp, f"FAIL: {resp}"

resp = handle_memory_command("who am i")
print(f"  Input:    'who am i'")
print(f"  Response: {resp}")
assert "Tejas" in resp, f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 3: Save more memories")
print("=" * 60)

resp = handle_memory_command("i live in ayodhya")
print(f"  Input:    'i live in ayodhya'")
print(f"  Response: {resp}")
assert "saved" in resp.lower(), f"FAIL: {resp}"

resp = handle_memory_command("my favorite game is valorant")
print(f"  Input:    'my favorite game is valorant'")
print(f"  Response: {resp}")
assert "saved" in resp.lower(), f"FAIL: {resp}"

resp = handle_memory_command("i study in akgec")
print(f"  Input:    'i study in akgec'")
print(f"  Response: {resp}")
assert "saved" in resp.lower(), f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 4: Read them back")
print("=" * 60)

resp = handle_memory_command("where do i live")
print(f"  Input:    'where do i live'")
print(f"  Response: {resp}")
assert "Ayodhya" in resp, f"FAIL: {resp}"

resp = handle_memory_command("what is my favorite game")
print(f"  Input:    'what is my favorite game'")
print(f"  Response: {resp}")
assert "Valorant" in resp, f"FAIL: {resp}"

resp = handle_memory_command("what's my college")
print(f"  Input:    'what's my college'")
print(f"  Response: {resp}")
assert "Akgec" in resp, f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 5: Update with confirmation")
print("=" * 60)

resp = handle_memory_command("change my home city to delhi")
print(f"  Input:    'change my home city to delhi'")
print(f"  Response: {resp}")
assert "update" in resp.lower() or "currently" in resp.lower(), f"FAIL: {resp}"

resp = handle_memory_command("yes")
print(f"  Input:    'yes'")
print(f"  Response: {resp}")
assert "updated" in resp.lower() or "Delhi" in resp, f"FAIL: {resp}"

resp = handle_memory_command("where do i live")
print(f"  Input:    'where do i live'")
print(f"  Response: {resp}")
assert "Delhi" in resp, f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 6: List all memories")
print("=" * 60)

resp = handle_memory_command("what do you know about me")
print(f"  Input:    'what do you know about me'")
print(f"  Response: {resp}")
assert "memories" in resp.lower() or "personal" in resp.lower(), f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 7: Delete with confirmation")
print("=" * 60)

resp = handle_memory_command("forget my favorite game")
print(f"  Input:    'forget my favorite game'")
print(f"  Response: {resp}")
assert "sure" in resp.lower() or "forget" in resp.lower(), f"FAIL: {resp}"

resp = handle_memory_command("yes")
print(f"  Input:    'yes'")
print(f"  Response: {resp}")
assert "forgotten" in resp.lower(), f"FAIL: {resp}"

resp = handle_memory_command("what is my favorite game")
print(f"  Input:    'what is my favorite game'")
print(f"  Response: {resp}")
assert "don't know" in resp.lower(), f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 8: Non-memory command returns None")
print("=" * 60)

resp = handle_memory_command("play music")
print(f"  Input:    'play music'")
print(f"  Response: {resp}")
assert resp is None, f"FAIL: expected None, got {resp}"

resp = handle_memory_command("what is the weather today")
print(f"  Input:    'what is the weather today'")
print(f"  Response: {resp}")
assert resp is None, f"FAIL: expected None, got {resp}"

print("\n" + "=" * 60)
print("TEST 9: Set command syntax")
print("=" * 60)

resp = handle_memory_command("set my birthday to august 5")
print(f"  Input:    'set my birthday to august 5'")
print(f"  Response: {resp}")
assert "saved" in resp.lower(), f"FAIL: {resp}"

print("\n" + "=" * 60)
print("TEST 10: Verify MySQL persistence")
print("=" * 60)

from database.mysql_connector import get_mysql_connection
with get_mysql_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT memory_key, memory_value FROM memories WHERE user_id='default' ORDER BY memory_key")
    rows = cursor.fetchall()
    print(f"  Rows in MySQL: {len(rows)}")
    for row in rows:
        print(f"    {row['memory_key']} = {row['memory_value']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
