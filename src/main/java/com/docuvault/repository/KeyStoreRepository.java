package com.docuvault.repository;

import com.docuvault.model.EncryptionKey;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Dedicated store for encryption keys — physically separate from document storage. */
public class KeyStoreRepository {

    private final Map<String, EncryptionKey> keysById = new ConcurrentHashMap<>();

    public void storeKey(EncryptionKey key) {
        keysById.put(key.getKeyId(), key);
    }

    public EncryptionKey loadKey(String keyId) {
        EncryptionKey key = keysById.get(keyId);
        if (key == null || key.isDestroyed()) {
            throw new IllegalStateException("Key not available: " + keyId);
        }
        return key;
    }

    public void deleteKey(String keyId) {
        EncryptionKey key = keysById.get(keyId);
        if (key != null) {
            key.markDestroyed();
        }
    }
}
