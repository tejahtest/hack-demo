package com.docuvault.repository;

import com.docuvault.model.Document;

import java.time.Instant;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Stores encrypted documents. Plaintext never reaches this layer. */
public class DocumentRepository {

    private final Map<String, Document> documentsById = new ConcurrentHashMap<>();

    public void saveDocument(Document document) {
        documentsById.put(document.getDocumentId(), document);
    }

    public Document findDocument(String documentId) {
        Document document = documentsById.get(documentId);
        if (document == null || document.isShredded()) {
            throw new IllegalStateException("Document not found: " + documentId);
        }
        return document;
    }

    /** Records the moment a document was last opened, for access auditing. */
    public void touchLastAccessed(String documentId) {
        Document document = documentsById.get(documentId);
        if (document != null) {
            document.setLastAccessedAt(Instant.now());
        }
    }

    /** Records the moment a document was shredded, for deletion auditing. */
    public void recordShred(String documentId) {
        Document document = documentsById.get(documentId);
        if (document != null) {
            document.setShreddedAt(Instant.now());
        }
    }

    /** Snapshot of every live document, used by retention sweeps. */
    public Collection<Document> findAllDocuments() {
        return List.copyOf(documentsById.values());
    }

    public void removeDocument(String documentId) {
        Document document = documentsById.get(documentId);
        if (document != null) {
            document.markShredded();
            documentsById.remove(documentId);
        }
    }
}
