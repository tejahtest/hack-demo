package com.docuvault.crypto;

import com.docuvault.model.EncryptionKey;
import com.docuvault.repository.KeyStoreRepository;
import com.docuvault.util.VaultLogger;

import java.util.UUID;

/** Owns the lifecycle of per-document keys: create, fetch, rotate, destroy. */
public class KeyManager {

    private final KeyStoreRepository keyStore;

    public KeyManager(KeyStoreRepository keyStore) {
        this.keyStore = keyStore;
    }

    /** Creates a fresh first-generation key for a document and stores it. */
    public EncryptionKey generateKey(String documentId) {
        byte[] material = CipherUtil.generateKeyMaterial();
        EncryptionKey key = new EncryptionKey(UUID.randomUUID().toString(), documentId, material, 1);
        keyStore.storeKey(key);
        VaultLogger.logInfo("KeyManager", "Generated key for document " + documentId);
        return key;
    }

    /** Fetches the live key for decryption; fails if it was destroyed. */
    public EncryptionKey retrieveKey(String keyId) {
        return keyStore.loadKey(keyId);
    }

    /**
     * Rotates the document key after a revocation: the old generation is
     * destroyed so previously shared material can no longer decrypt.
     */
    public EncryptionKey rotateKey(String documentId, String oldKeyId) {
        EncryptionKey old = keyStore.loadKey(oldKeyId);
        byte[] material = CipherUtil.generateKeyMaterial();
        EncryptionKey next = new EncryptionKey(
                UUID.randomUUID().toString(), documentId, material, old.getGeneration() + 1);
        keyStore.storeKey(next);
        keyStore.deleteKey(oldKeyId);
        VaultLogger.logInfo("KeyManager", "Rotated key for document " + documentId
                + " to generation " + next.getGeneration());
        return next;
    }

    /** Destroys a key permanently as part of document shredding. */
    public void destroyKey(String keyId) {
        keyStore.deleteKey(keyId);
        VaultLogger.logInfo("KeyManager", "Destroyed key " + keyId);
    }
}
