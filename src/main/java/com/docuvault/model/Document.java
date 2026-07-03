package com.docuvault.model;

import java.time.Instant;

/** A file stored in the vault. Content is always held encrypted at rest. */
public class Document {

    private String documentId;
    private String fileName;
    private String ownerId;
    private String keyId;
    private byte[] encryptedContent;
    private long sizeBytes;
    private Instant uploadedAt;
    private boolean shredded;

    public Document(String documentId, String fileName, String ownerId) {
        this.documentId = documentId;
        this.fileName = fileName;
        this.ownerId = ownerId;
        this.uploadedAt = Instant.now();
        this.shredded = false;
    }

    public String getDocumentId() { return documentId; }

    public String getFileName() { return fileName; }

    public void setFileName(String fileName) { this.fileName = fileName; }

    public String getOwnerId() { return ownerId; }

    public String getKeyId() { return keyId; }

    public void setKeyId(String keyId) { this.keyId = keyId; }

    public byte[] getEncryptedContent() { return encryptedContent; }

    public void setEncryptedContent(byte[] encryptedContent) {
        this.encryptedContent = encryptedContent;
        this.sizeBytes = encryptedContent == null ? 0 : encryptedContent.length;
    }

    public long getSizeBytes() { return sizeBytes; }

    public Instant getUploadedAt() { return uploadedAt; }

    public boolean isShredded() { return shredded; }

    public void markShredded() { this.shredded = true; }
}
