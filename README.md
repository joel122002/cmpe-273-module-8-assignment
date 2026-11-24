# Replicated Inventory Consistency Lab

This project simulates one primary replica, one secondary replica, and a client that reads from either replica. Updates are written to the primary and asynchronously copied to the secondary.

## Architecture

```text
                 update(stock)
       Client ----------------------> Primary
         |                              |
         | read                         | asynchronous replication
         v                              v
      Secondary <-----------------------+
         |
         +-- read(stock)
```

## Run

Requires Python 3.10 or newer. From the repository directory, run:

```text
python inventory_replication.py
```

The program uses only the Python standard library and contains assertions for each required consistency result.

## Evidence

The following output was produced by running `python inventory_replication.py`:

```text
=== Replication test ===
Initial: Primary=10, Secondary=10
Primary received update: 12
After replication: Primary=12, Secondary=12

=== Stale read test ===
Primary after update: 9
Secondary during delay: 12 (stale)

=== Recovery and convergence ===
After recovery: Primary=9, Secondary=9
PASS: replicas converged to stock=9
```

This demonstrates that the primary receives an update, the secondary catches up, replication can be paused to expose a stale read, and the secondary converges after replication resumes.

## Reflection

Reading from a nearby replica is fast and distributes load, but asynchronous replication means that replica may briefly return an older value. Reading from the primary, or waiting for a replica to catch up, provides a stronger guarantee that the latest write is visible. The tradeoff is higher latency and potentially less availability during primary or network problems. This simulation makes that consistency-versus-latency choice visible by pausing replication.
