package com.docuvault.repository;

import com.docuvault.model.Document;

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
