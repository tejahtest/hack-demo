package com.docuvault.model;

import java.time.Instant;

/** A per-document AES key. Stored only in the key store, never with the data. */
public class EncryptionKey {

    private final String keyId;
    private final String documentId;
    private final byte[] keyMaterial;
    private final int generation;
    private final Instant createdAt;
    private boolean destroyed;

    public EncryptionKey(String keyId, String documentId, byte[] keyMaterial, int generation) {
        this.keyId = keyId;
        this.documentId = documentId;
        this.keyMaterial = keyMaterial;
        this.generation = generation;
        this.createdAt = Instant.now();
        this.destroyed = false;
    }

    public String getKeyId() { return keyId; }

    public String getDocumentId() { return documentId; }

    public byte[] getKeyMaterial() { return keyMaterial; }

    public int getGeneration() { return generation; }

    public Instant getCreatedAt() { return createdAt; }

    public boolean isDestroyed() { return destroyed; }

    public void markDestroyed() { this.destroyed = true; }
}
