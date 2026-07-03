package com.docuvault.service;

import com.docuvault.crypto.KeyManager;
import com.docuvault.model.AuditEvent;
import com.docuvault.model.Document;
import com.docuvault.repository.DocumentRepository;
import com.docuvault.util.VaultLogger;

import java.time.Duration;
import java.time.Instant;

/**
 * Enforces the vault's retention policy: documents older than the retention
 * period are cryptographically shredded so expired content cannot be recovered.
 */
public class RetentionService {

    private final DocumentRepository documentRepository;
    private final KeyManager keyManager;
    private final AuditService auditService;
    private final Duration retentionPeriod;

    public RetentionService(DocumentRepository documentRepository,
                            KeyManager keyManager,
                            AuditService auditService,
                            Duration retentionPeriod) {
        this.documentRepository = documentRepository;
        this.keyManager = keyManager;
        this.auditService = auditService;
        this.retentionPeriod = retentionPeriod;
    }

    /** Sweeps the vault and shreds every document past retention; returns the shred count. */
    public int sweepExpiredDocuments() {
        Instant cutoff = Instant.now().minus(retentionPeriod);
        int shredded = 0;
        for (Document document : documentRepository.findAllDocuments()) {
            if (document.getUploadedAt().isBefore(cutoff)) {
                shredExpired(document);
                shredded++;
            }
        }
        VaultLogger.logInfo("RetentionService", "Retention sweep complete: "
                + shredded + " document(s) shredded (cutoff " + cutoff + ")");
        return shredded;
    }

    /** Destroys the document's key and removes it — the standard cryptographic shred. */
    private void shredExpired(Document document) {
        keyManager.destroyKey(document.getKeyId());
        documentRepository.removeDocument(document.getDocumentId());
        auditService.recordEvent(AuditEvent.EventType.RETENTION_EXPIRED, "system",
                document.getDocumentId(), document.getFileName() + " exceeded retention period");
    }
}
