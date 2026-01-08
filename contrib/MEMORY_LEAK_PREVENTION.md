# Memory Leak Prevention Guide for Bittensor Validators

This document explains common memory leak patterns in Bittensor validators and how to avoid them.

## Table of Contents

- [Overview](#overview)
- [Pattern 1: deepcopy of Metagraph](#pattern-1-deepcopy-of-metagraph)
- [Pattern 2: Creating Metagraph in Loops](#pattern-2-creating-metagraph-in-loops)
- [Pattern 3: Creating Subtensor in Loops](#pattern-3-creating-subtensor-in-loops)
- [Pattern 4: Cached Subtensor with TTL Expiry](#pattern-4-cached-subtensor-with-ttl-expiry)
- [Pattern 5: Not Closing WebSocket Before Discarding Subtensor](#pattern-5-not-closing-websocket-before-discarding-subtensor)
- [Memory Impact Reference](#memory-impact-reference)
- [Testing for Memory Leaks](#testing-for-memory-leaks)

## Overview

Bittensor validators running for extended periods (hours/days) can experience out-of-memory (OOM) errors due to memory leaks. The most common cause is the **scalecodec type registration** that happens when creating or deep-copying metagraph/subtensor objects.

### Why This Happens

When you create a new `bt.metagraph()` or `bt.subtensor()`, or use `copy.deepcopy()` on these objects, the bittensor SDK internally registers scalecodec types with the substrate interface. These type registrations accumulate and are never garbage collected, causing memory to grow over time.

**Key insight**: The `metagraph.sync()` method updates the existing metagraph in-place WITHOUT triggering new type registrations, making it safe to call repeatedly.

---

## Pattern 1: deepcopy of Metagraph

### ❌ Bad Pattern (leaks ~50MB per call)

```python
def resync_metagraph(self):
    # This creates a full deep copy, triggering scalecodec type registration
    previous_metagraph = copy.deepcopy(self.metagraph)
    
    self.metagraph.sync(subtensor=self.subtensor)
    
    if previous_metagraph.axons == self.metagraph.axons:
        return
    # ...
```

### ✅ Good Pattern (no leak)

```python
def resync_metagraph(self):
    # Only copy what you need - a shallow copy of the list is sufficient
    previous_axons = list(self.metagraph.axons)
    
    self.metagraph.sync(subtensor=self.subtensor)
    
    if previous_axons == list(self.metagraph.axons):
        return
    # ...
```

### What to Copy Instead

| Need to Compare | Use This (Safe) | NOT This (Leaks) |
|-----------------|-----------------|------------------|
| Axons | `list(metagraph.axons)` | `copy.deepcopy(metagraph)` |
| Hotkeys | `list(metagraph.hotkeys)` | `copy.deepcopy(metagraph.hotkeys)` |
| Stakes | `metagraph.S.copy()` | `copy.deepcopy(metagraph)` |
| UIDs | `list(metagraph.uids)` | - |

---

## Pattern 2: Creating Metagraph in Loops

### ❌ Bad Pattern

```python
while True:
    # Creates new metagraph and registers scalecodec types each iteration
    self.metagraph = bt.metagraph(netuid=self.netuid, network="finney")
    await asyncio.sleep(600)
```

### ✅ Good Pattern

```python
# Create once in __init__
self.subtensor = bt.subtensor(network="finney")
self.metagraph = self.subtensor.metagraph(self.netuid)

# In loop - use sync() to refresh data
while True:
    self.metagraph.sync(subtensor=self.subtensor)  # Updates in-place, no leak
    await asyncio.sleep(600)
```

### Why `sync()` is Safe

The `metagraph.sync()` method:
1. Uses the existing metagraph object
2. Only fetches new data from the chain
3. Updates internal arrays in-place
4. Does NOT trigger scalecodec type registration

---

## Pattern 3: Creating Subtensor in Loops

### ❌ Bad Pattern

```python
while True:
    subtensor = bt.subtensor(network="finney")  # New WebSocket + type registration
    metagraph = subtensor.metagraph(netuid)
    # ...
```

### ✅ Good Pattern

```python
# Create once, reuse forever
self.subtensor = bt.subtensor(network="finney")
self.metagraph = self.subtensor.metagraph(self.netuid)

while True:
    self.metagraph.sync(subtensor=self.subtensor)
    # ...
```

---

## Pattern 4: Cached Subtensor with TTL Expiry

This is a subtle pattern often found in utility functions.

### ❌ Bad Pattern

```python
@lru_cache(maxsize=1)
def get_subtensor():
    # When cache expires and is recreated, old subtensor leaks
    return bt.Subtensor(network="finney")

# Or with TTL cache
_cache = {}
def get_metagraph():
    if time.time() - _cache.get('time', 0) > 120:
        subtensor = bt.Subtensor(...)  # Old one not cleaned up!
        _cache['metagraph'] = subtensor.metagraph(netuid)
        _cache['time'] = time.time()
    return _cache['metagraph']
```

### ✅ Good Pattern

```python
# Singleton pattern - created once, never expires
_subtensor_instance = None

def _get_subtensor():
    global _subtensor_instance
    if _subtensor_instance is None:
        _subtensor_instance = bt.Subtensor(network="finney")
    return _subtensor_instance

def get_metagraph(netuid):
    subtensor = _get_subtensor()
    metagraph = subtensor.metagraph(netuid)
    metagraph.sync(subtensor=subtensor, lite=True)
    return metagraph
```

---

## Pattern 5: Not Closing WebSocket Before Discarding Subtensor

If you must replace a subtensor (e.g., reconnecting after network issues), close the WebSocket first.

### ❌ Bad Pattern

```python
def _reset_subtensor():
    global _subtensor
    _subtensor = None  # WebSocket stays open, leaking memory
```

### ✅ Good Pattern

```python
def _reset_subtensor():
    global _subtensor
    if _subtensor is not None:
        try:
            if hasattr(_subtensor, 'substrate') and _subtensor.substrate:
                _subtensor.substrate.close()
        except Exception:
            pass
    _subtensor = None
```

---

## Memory Impact Reference

| Pattern | Memory Leak per Occurrence | With 10min Loop | Time to 2GB OOM |
|---------|---------------------------|-----------------|-----------------|
| `copy.deepcopy(metagraph)` | ~50 MB | 300 MB/hour | ~6-8 hours |
| New `bt.metagraph()` in loop | ~50 MB | 300 MB/hour | ~6-8 hours |
| New `bt.subtensor()` in loop | ~20 MB | 120 MB/hour | ~12-16 hours |
| Cached subtensor with 2min TTL | ~50 MB per expiry | 1.5 GB/hour | ~1-2 hours |
| Unclosed WebSocket | ~5-10 MB | Slow accumulation | Days |

---

## Testing for Memory Leaks

### Quick Memory Check

Add this to your validator to log memory usage:

```python
import psutil
import os

def log_memory():
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    bt.logging.info(f"Memory usage: {mem_mb:.1f} MB")

# Call in your main loop
while True:
    log_memory()
    # ... your validation logic ...
```

### What to Look For

1. **Stable memory**: Good validators should stabilize at a consistent memory level
2. **Growing memory**: If memory increases by 50-100MB every 10-30 minutes, you likely have a leak
3. **OOM crashes**: If your validator crashes after 6-12 hours with OOM, check for these patterns

### Using Memory Profilers

```python
# Add this for detailed memory profiling
import tracemalloc

tracemalloc.start()

# ... run your code ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 memory allocations ]")
for stat in top_stats[:10]:
    print(stat)
```

---

## Summary of Best Practices

1. **Create subtensor and metagraph ONCE** in `__init__`
2. **Use `metagraph.sync()`** to refresh data instead of creating new objects
3. **Never use `copy.deepcopy()`** on metagraph or subtensor objects
4. **Copy only what you need**: `list(metagraph.hotkeys)`, `metagraph.S.copy()`
5. **Close WebSocket** before discarding subtensor objects
6. **Avoid TTL caches** that recreate subtensor/metagraph on expiry
7. **Monitor memory** in production to catch leaks early
