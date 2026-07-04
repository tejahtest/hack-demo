package com.docuvault.service;

import com.docuvault.model.AuditEvent;
import com.docuvault.model.Document;
import com.docuvault.model.Policy;
import com.docuvault.repository.DocumentRepository;
import com.docuvault.repository.TagRepository;
import com.docuvault.util.InputValidator;

import java.util.ArrayList;
import java.util.List;

/** Organises documents with free-form tags and resolves tag lookups. */
public class TagService {

    private final TagRepository tagRepository;
    private final DocumentRepository documentRepository;
    private final AccessService accessService;
    private final AuditService auditService;

    public TagService(TagRepository tagRepository,
                      DocumentRepository documentRepository,
                      AccessService accessService,
                      AuditService auditService) {
        this.tagRepository = tagRepository;
        this.documentRepository = documentRepository;
        this.accessService = accessService;
        this.auditService = auditService;
    }

    /** Tags a document after an EDIT access check; the label is recorded in the audit trail. */
    public void tagDocument(String documentId, String userId, String tag) {
        InputValidator.validateIdentifier(documentId);
        if (!accessService.checkAccess(documentId, userId, Policy.Permission.EDIT)) {
            throw new SecurityException("Tagging denied for document " + documentId);
        }
        Document document = documentRepository.findDocument(documentId);
        tagRepository.addTag(documentId, tag);
        auditService.recordEvent(AuditEvent.EventType.DOCUMENT_TAGGED, userId,
                documentId, document.getFileName() + " #" + tag);
    }

    /** Removes a tag from a document after an EDIT access check. */
    public void untagDocument(String documentId, String userId, String tag) {
        InputValidator.validateIdentifier(documentId);
        if (!accessService.checkAccess(documentId, userId, Policy.Permission.EDIT)) {
            throw new SecurityException("Untagging denied for document " + documentId);
        }
        tagRepository.removeTag(documentId, tag);
        auditService.recordEvent(AuditEvent.EventType.DOCUMENT_UNTAGGED, userId,
                documentId, "#" + tag);
    }

    /** Lists the documents a user is allowed to view under a given tag. */
    public List<String> listDocumentsByTag(String userId, String tag) {
        List<String> matches = tagRepository.findDocumentsByTag(tag);
        List<String> visible = new ArrayList<>();
        for (String documentId : matches) {
            if (accessService.checkAccess(documentId, userId, Policy.Permission.VIEW)) {
                visible.add(documentId);
            }
        }
        return visible;
    }
}
