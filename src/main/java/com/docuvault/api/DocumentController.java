package com.docuvault.api;

import com.docuvault.model.Document;
import com.docuvault.service.DocumentService;
import com.docuvault.util.VaultLogger;

/** Entry points for document actions: upload, open, delete. */
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    /** A user uploads a file into the vault; it is protected before it is stored. */
    public String handleUploadDocument(String ownerId, String fileName, byte[] content) {
        VaultLogger.logInfo("DocumentController", "Upload request: " + fileName + " by " + ownerId);
        Document document = documentService.uploadDocument(ownerId, fileName, content);
        return document.getDocumentId();
    }

    /** A user opens a protected document; access is checked before decryption. */
    public byte[] handleOpenDocument(String documentId, String userId) {
        VaultLogger.logInfo("DocumentController", "Open request: " + documentId + " by " + userId);
        return documentService.openDocument(documentId, userId);
    }

    /** A user renames a document; the EDIT permission is checked before the change. */
    public String handleRenameDocument(String documentId, String userId, String newFileName) {
        VaultLogger.logInfo("DocumentController", "Rename request: " + documentId
                + " -> " + newFileName + " by " + userId);
        Document document = documentService.renameDocument(documentId, userId, newFileName);
        return document.getFileName();
    }

    /** A user deletes a document; its key is destroyed so the data is unrecoverable. */
    public void handleDeleteDocument(String documentId, String ownerId) {
        VaultLogger.logInfo("DocumentController", "Delete request: " + documentId + " by " + ownerId);
        documentService.deleteDocument(documentId, ownerId);
    }
}
