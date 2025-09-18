# tests/test_kvstore_basic.py

def test_a(testdata_store):
    """Writes a key into the shared KV store."""
    testdata_store.set("smoke", 1)

def test_b(testdata_store):
    """Reads the key written by test_a."""
    assert testdata_store.get("smoke") == 1

# run the below for debug
# pytest -q tests/test_kvstore_basic.py
