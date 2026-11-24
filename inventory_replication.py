"""Small primary/secondary inventory replication simulation."""

from __future__ import annotations

import queue
import threading
import time


class Replica:
    def __init__(self, name: str, stock: int) -> None:
        self.name = name
        self._stock = stock
        self._lock = threading.Lock()

    def read(self) -> int:
        with self._lock:
            return self._stock

    def write(self, stock: int) -> None:
        with self._lock:
            self._stock = stock


class ReplicatedInventory:
    def __init__(self, initial_stock: int = 10, replication_delay: float = 0.15) -> None:
        self.primary = Replica("Primary", initial_stock)
        self.secondary = Replica("Secondary", initial_stock)
        self.replication_delay = replication_delay
        self._paused = threading.Event()
        self._updates: queue.Queue[int | None] = queue.Queue()
        self._worker = threading.Thread(target=self._replicate, daemon=True)
        self._worker.start()

    def update_primary(self, stock: int) -> None:
        self.primary.write(stock)
        self._updates.put(stock)

    def pause_replication(self) -> None:
        self._paused.set()

    def resume_replication(self) -> None:
        self._paused.clear()

    def wait_for_convergence(self, timeout: float = 2.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.primary.read() == self.secondary.read() and self._updates.empty():
                return True
            time.sleep(0.01)
        return False

    def close(self) -> None:
        self._updates.put(None)
        self._worker.join(timeout=1)

    def _replicate(self) -> None:
        while True:
            stock = self._updates.get()
            if stock is None:
                return
            while self._paused.is_set():
                time.sleep(0.01)
            time.sleep(self.replication_delay)
            self.secondary.write(stock)


def main() -> None:
    inventory = ReplicatedInventory()
    try:
        print("=== Replication test ===")
        print(f"Initial: Primary={inventory.primary.read()}, Secondary={inventory.secondary.read()}")
        inventory.update_primary(12)
        print(f"Primary received update: {inventory.primary.read()}")
        assert inventory.wait_for_convergence()
        print(f"After replication: Primary={inventory.primary.read()}, Secondary={inventory.secondary.read()}")

        print("\n=== Stale read test ===")
        inventory.pause_replication()
        inventory.update_primary(9)
        print(f"Primary after update: {inventory.primary.read()}")
        print(f"Secondary during delay: {inventory.secondary.read()} (stale)")
        assert inventory.primary.read() == 9
        assert inventory.secondary.read() == 12

        print("\n=== Recovery and convergence ===")
        inventory.resume_replication()
        assert inventory.wait_for_convergence()
        print(f"After recovery: Primary={inventory.primary.read()}, Secondary={inventory.secondary.read()}")
        assert inventory.primary.read() == inventory.secondary.read() == 9
        print("PASS: replicas converged to stock=9")
    finally:
        inventory.close()


if __name__ == "__main__":
    main()
