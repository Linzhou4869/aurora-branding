# Concurrency Control Protocol — Vendor Buffer Updates

**Document ID:** CCP-VND-001  
**Version:** 1.0  
**Effective Date:** 2026-03-29  
**Applies To:** Production vendor configuration updates

---

## 1. Overview

This protocol defines the concurrency control mechanism for preventing race conditions when multiple planners attempt to modify vendor buffer configurations simultaneously. The protocol uses **advisory file locking** with **atomic operations** and **timeout-based deadlock prevention**.

---

## 2. Lock File Specification

### 2.1 Lock File Location

```
/var/locks/vendor_config/<VENDOR_ID>.lock
```

Example: `/var/locks/vendor_config/VND-SE-001.lock`

### 2.2 Lock File Structure

```json
{
  "lock_id": "<UUID-v4>",
  "vendor_id": "<VENDOR_ID>",
  "acquired_by": "<PLANNER_USER_ID>",
  "acquired_at": "<ISO-8601_TIMESTAMP>",
  "expires_at": "<ISO-8601_TIMESTAMP>",
  "operation": "<OPERATION_TYPE>",
  "hostname": "<HOST_FQDN>",
  "pid": <PROCESS_ID>
}
```

### 2.3 Lock Expiration

- **Default TTL:** 300 seconds (5 minutes)
- **Maximum hold time:** 600 seconds (10 minutes)
- Stale locks (past `expires_at`) are considered abandoned and may be reclaimed

---

## 3. Lock Acquisition Protocol

### 3.1 Algorithm

```
FUNCTION acquire_lock(vendor_id, planner_id, timeout_seconds=30):
    lock_file = "/var/locks/vendor_config/{vendor_id}.lock"
    start_time = current_timestamp()
    lock_id = generate_uuid_v4()
    
    WHILE (current_timestamp() - start_time) < timeout_seconds:
        # Step 1: Check for existing lock
        IF NOT exists(lock_file):
            # Step 2: Atomic creation with O_EXCL
            TRY:
                fd = open(lock_file, O_CREAT | O_EXCL | O_WRONLY, 0640)
                write_lock_metadata(fd, lock_id, planner_id, vendor_id)
                close(fd)
                # Step 3: Verify ownership
                IF verify_lock_ownership(lock_file, lock_id):
                    RETURN SUCCESS(lock_id)
                ELSE:
                    cleanup_failed_lock(lock_file)
            EXCEPT FileExistsError:
                # Race condition - another process won
                CONTINUE
        
        # Step 4: Check if existing lock is stale
        existing_lock = read_lock_metadata(lock_file)
        IF is_lock_stale(existing_lock):
            TRY:
                # Atomic lock break with flock
                IF atomic_lock_break(lock_file, existing_lock, lock_id, planner_id):
                    RETURN SUCCESS(lock_id)
            EXCEPT LockBreakFailed:
                PASS
        
        # Step 5: Wait before retry (exponential backoff)
        sleep_time = calculate_backoff(attempt_number)
        sleep(min(sleep_time, 2.0))  # Cap at 2 seconds
        attempt_number += 1
    
    # Timeout exceeded
    RAISE LockAcquisitionTimeout(
        vendor_id=vendor_id,
        timeout=timeout_seconds,
        held_by=existing_lock.acquired_by
    )
```

### 3.2 Atomic Operations

| Operation | Method | Purpose |
|-----------|--------|---------|
| Lock creation | `open(O_CREAT \| O_EXCL)` | Atomic file creation |
| Lock verification | `flock(LOCK_EX \| LOCK_NB)` | Non-blocking exclusive lock |
| Lock break | `flock(LOCK_UN)` + recreate | Reclaim stale locks |

### 3.3 Backoff Strategy

```
attempt 1: 0.1s
attempt 2: 0.2s
attempt 3: 0.4s
attempt 4: 0.8s
attempt 5+: 1.5s (capped)
```

---

## 4. Timeout Behavior

### 4.1 30-Second Timeout Policy

When lock acquisition exceeds **30 seconds**:

1. **Raise `LockAcquisitionTimeout` exception**
2. **Log incident** to audit log with:
   - Vendor ID
   - Requesting planner ID
   - Current lock holder (if known)
   - Wait duration
   - Hostname/PID

3. **Notify planner** with structured error:

```json
{
  "error": "LOCK_ACQUISITION_TIMEOUT",
  "vendor_id": "VND-SE-001",
  "timeout_seconds": 30,
  "held_by": {
    "planner_id": "PLANNER-042",
    "acquired_at": "2026-03-29T03:45:00Z",
    "hostname": "planner-workstation-07.example.com"
  },
  "retry_after_seconds": 60,
  "escalation_path": "operations-lead@example.com"
}
```

### 4.2 Escalation Triggers

| Condition | Action |
|-----------|--------|
| Timeout > 30s | Notify requesting planner |
| Same lock contested > 3 times in 5 min | Alert operations team |
| Lock held > 10 min | Auto-break with audit trail |
| Lock break fails | Page on-call engineer |

---

## 5. Lock Release Protocol

### 5.1 Normal Release

```
FUNCTION release_lock(lock_file, lock_id):
    # Step 1: Verify ownership
    current_lock = read_lock_metadata(lock_file)
    IF current_lock.lock_id != lock_id:
        RAISE LockOwnershipError("Lock ID mismatch")
    
    # Step 2: Remove lock file atomically
    TRY:
        os.unlink(lock_file)
    EXCEPT FileNotFoundError:
        # Already removed - idempotent
        PASS
    
    # Step 3: Log release
    audit_log("LOCK_RELEASED", lock_id, current_lock.vendor_id)
```

### 5.2 Exception-Safe Release (Context Manager)

```python
class VendorLock:
    def __init__(self, vendor_id, planner_id, timeout=30):
        self.vendor_id = vendor_id
        self.planner_id = planner_id
        self.timeout = timeout
        self.lock_id = None
        self.lock_file = f"/var/locks/vendor_config/{vendor_id}.lock"
    
    def __enter__(self):
        self.lock_id = acquire_lock(self.vendor_id, self.planner_id, self.timeout)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        release_lock(self.lock_file, self.lock_id)
        return False  # Don't suppress exceptions

# Usage:
try:
    with VendorLock("VND-SE-001", "PLANNER-001") as lock:
        # Critical section - safe to modify vendor config
        update_vendor_buffer(vendor_id, new_buffer_days)
except LockAcquisitionTimeout as e:
    handle_timeout(e)
```

---

## 6. Race Condition Prevention

### 6.1 Two-Phase Commit for Config Updates

```
PHASE 1: LOCK ACQUISITION
├─ Acquire vendor-specific lock (30s timeout)
├─ Read current config into memory
└─ Validate update constraints

PHASE 2: ATOMIC WRITE
├─ Write to temp file: vendor_config.json.tmp.<PID>
├─ fsync() to ensure disk flush
├─ Atomic rename: mv temp_file vendor_config.json
├─ Release lock
└─ Log audit trail
```

### 6.2 Version Vector Validation

```json
{
  "vendor_id": "VND-SE-001",
  "config_version": "2.1.0",
  "version_vector": {
    "PLANNER-001": 15,
    "PLANNER-042": 12
  },
  "last_modified_by": "PLANNER-001",
  "last_modified_at": "2026-03-29T03:48:10Z"
}
```

Before applying update:
1. Read current `version_vector`
2. Increment own counter
3. Verify no conflicting increments since read
4. Write new vector atomically with config

---

## 7. Audit Logging

### 7.1 Required Log Events

| Event | Fields |
|-------|--------|
| `LOCK_REQUESTED` | vendor_id, planner_id, hostname, pid |
| `LOCK_ACQUIRED` | lock_id, vendor_id, planner_id, timestamp |
| `LOCK_RELEASED` | lock_id, vendor_id, duration_seconds |
| `LOCK_TIMEOUT` | vendor_id, planner_id, wait_duration, held_by |
| `LOCK_BREAK` | lock_id, original_holder, breaker_id, reason |
| `CONFIG_UPDATED` | vendor_id, field, old_value, new_value, planner_id |

### 7.2 Log Storage

- **Primary:** `/var/log/vendor_config/audit.log` (JSON Lines format)
- **Retention:** 90 days
- **Alerting:** Real-time stream to SIEM for `LOCK_TIMEOUT` and `LOCK_BREAK`

---

## 8. Implementation Checklist

- [ ] Create `/var/locks/vendor_config/` directory with mode 0750
- [ ] Implement `acquire_lock()` with 30s timeout
- [ ] Implement `release_lock()` with ownership verification
- [ ] Add context manager wrapper for exception safety
- [ ] Implement atomic write (temp file + rename)
- [ ] Add version vector tracking to config schema
- [ ] Configure audit log rotation
- [ ] Set up alerting for timeout/break events
- [ ] Document rollback procedure
- [ ] Load test with 10+ concurrent planners

---

## 9. Rollback Procedure

If concurrent update causes corruption:

1. **Stop all planner processes** accessing vendor config
2. **Restore from last known-good backup:**
   ```bash
   cp /var/backups/vendor_config/vendor_config.json.<timestamp> \
      /etc/vendor_config/vendor_config.json
   ```
3. **Clear all stale locks:**
   ```bash
   rm -f /var/locks/vendor_config/*.lock
   ```
4. **Verify config integrity** with schema validation
5. **Resume operations** with single-planner mode for 5 minutes
6. **Post-incident review** within 24 hours

---

**Approved By:** Operations Architecture Review Board  
**Next Review:** 2026-Q2
