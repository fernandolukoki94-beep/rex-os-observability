const DB_NAME = "rex-mine-intelligence";
const STORE_NAME = "operational-events";
const DB_VERSION = 1;
const META_STORE = "metadata";
const INCIDENTS_FALLBACK_KEY = "rex_incidents_v1";
const SEQUENCE_FALLBACK_KEY = "rex_event_sequence_v1";

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined" || !window.indexedDB) {
      reject(new Error("IndexedDB indisponível"));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "id" });
      }
      if (!database.objectStoreNames.contains(META_STORE)) {
        database.createObjectStore(META_STORE, { keyPath: "key" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("Não foi possível abrir IndexedDB"));
  });
}

export async function readDurableEvents<T extends { id: string }>(fallback: T[]): Promise<T[]> {
  try {
    const database = await openDatabase();
    return await new Promise<T[]>((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, "readonly");
      const request = transaction.objectStore(STORE_NAME).getAll();
      request.onsuccess = () => {
        const records = request.result as T[];
        resolve(records.length > 0 ? records : fallback);
      };
      request.onerror = () => reject(request.error ?? new Error("Não foi possível ler IndexedDB"));
      transaction.oncomplete = () => database.close();
    });
  } catch {
    try {
      const raw = window.localStorage.getItem(INCIDENTS_FALLBACK_KEY);
      return raw ? (JSON.parse(raw) as T[]) : fallback;
    } catch {
      return fallback;
    }
  }
}

export async function persistDurableEvents<T extends { id: string }>(events: T[]): Promise<boolean> {
  try {
    const database = await openDatabase();
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, "readwrite");
      const store = transaction.objectStore(STORE_NAME);
      store.clear();
      events.forEach((event) => store.put(event));
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error ?? new Error("Não foi possível guardar IndexedDB"));
      transaction.onabort = () => reject(transaction.error ?? new Error("Transacção IndexedDB abortada"));
    });
    database.close();
    return true;
  } catch {
    try {
      window.localStorage.setItem(INCIDENTS_FALLBACK_KEY, JSON.stringify(events));
    } catch {
      // O estado React continua disponível mesmo em armazenamento read-only.
    }
    return false;
  }
}

export async function nextDurableEventId(): Promise<string> {
  const fallbackCurrent = Number(window.localStorage.getItem(SEQUENCE_FALLBACK_KEY) || "184");
  try {
    const database = await openDatabase();
    return await new Promise<string>((resolve, reject) => {
      const transaction = database.transaction(META_STORE, "readwrite");
      const store = transaction.objectStore(META_STORE);
      const request = store.get("event-sequence");
      request.onsuccess = () => {
        const next = Number(request.result?.value || fallbackCurrent) + 1;
        store.put({ key: "event-sequence", value: next });
        transaction.oncomplete = () => {
          database.close();
          resolve(`REX-EVT-${new Date().getFullYear()}-${String(next).padStart(6, "0")}`);
        };
      };
      request.onerror = () => reject(request.error ?? new Error("Não foi possível ler a sequência"));
      transaction.onerror = () => reject(transaction.error ?? new Error("Não foi possível guardar a sequência"));
    });
  } catch {
    const next = fallbackCurrent + 1;
    window.localStorage.setItem(SEQUENCE_FALLBACK_KEY, String(next));
    return `REX-EVT-${new Date().getFullYear()}-${String(next).padStart(6, "0")}`;
  }
}

export async function clearDurableEvents(): Promise<void> {
  try {
    const database = await openDatabase();
    await new Promise<void>((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, "readwrite");
      transaction.objectStore(STORE_NAME).clear();
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
    database.close();
  } catch {
    // O localStorage continua a ser a camada de fallback da demonstração.
  }
}
