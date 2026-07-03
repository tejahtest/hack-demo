package com.docuvault.service;

import com.docuvault.crypto.EncryptionEngine;
import com.docuvault.crypto.KeyManager;
import com.docuvault.model.AuditEvent;
import com.docuvault.model.Document;
import com.docuvault.model.Policy;
import com.docuvault.repository.DocumentRepository;
import com.docuvault.util.InputValidator;

import java.util.UUID;

/** The document lifecycle: protect on upload, decrypt on open, shred on delete. */
public class DocumentService {

    private final DocumentRepository documentRepository;
    private final EncryptionEngine encryptionEngine;
    private final KeyManager keyManager;
    private final AccessService accessService;
    private final AuditService auditService;

    public DocumentService(DocumentRepository documentRepository,
                           EncryptionEngine encryptionEngine,
                           KeyManager keyManager,
                           AccessService accessService,
                           AuditService auditService) {
        this.documentRepository = documentRepository;
        this.encryptionEngine = encryptionEngine;
        this.keyManager = keyManager;
        this.accessService = accessService;
        this.auditService = auditService;
    }

    /** Validates, encrypts, and stores an incoming file; the vault never keeps plaintext. */
    public Document uploadDocument(String ownerId, String fileName, byte[] rawContent) {
        InputValidator.validateFileName(fileName);
        Document document = new Document(UUID.randomUUID().toString(), fileName, ownerId);
        byte[] cipherText = encryptionEngine.encryptDocument(document, rawContent);
        document.setEncryptedContent(cipherText);
        documentRepository.saveDocument(document);
        auditService.recordEvent(AuditEvent.EventType.DOCUMENT_UPLOADED, ownerId,
                document.getDocumentId(), fileName + " (" + cipherText.length + " bytes)");
        return document;
    }

    /** Opens a protected document after an access check; returns decrypted content. */
    public byte[] openDocument(String documentId, String userId) {
        if (!accessService.checkAccess(documentId, userId, Policy.Permission.VIEW)) {
            throw new SecurityException("Access denied to document " + documentId);
        }
        Document document = documentRepository.findDocument(documentId);
        byte[] plainText = encryptionEngine.decryptDocument(document);
        auditService.recordEvent(AuditEvent.EventType.DOCUMENT_OPENED, userId,
                documentId, document.getFileName());
        return plainText;
    }

    /** Deletes a document and destroys its key — a cryptographic shred. */
    public void deleteDocument(String documentId, String ownerId) {
        Document document = documentRepository.findDocument(documentId);
        keyManager.destroyKey(document.getKeyId());
        documentRepository.removeDocument(documentId);
        auditService.recordEvent(AuditEvent.EventType.DOCUMENT_DELETED, ownerId,
                documentId, document.getFileName());
    }
}
