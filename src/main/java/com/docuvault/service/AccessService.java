package com.docuvault.service;

import com.docuvault.crypto.KeyManager;
import com.docuvault.model.AccessGrant;
import com.docuvault.model.AuditEvent;
import com.docuvault.model.Document;
import com.docuvault.model.Policy;
import com.docuvault.model.User;
import com.docuvault.repository.DocumentRepository;
import com.docuvault.repository.UserRepository;
import com.docuvault.util.InputValidator;

import java.util.UUID;

/** Governs sharing: grants access, checks it on every open, and revokes it instantly. */
public class AccessService {

    private final PolicyService policyService;
    private final DocumentRepository documentRepository;
    private final UserRepository userRepository;
    private final KeyManager keyManager;
    private final NotificationService notificationService;
    private final AuditService auditService;

    public AccessService(PolicyService policyService,
                         DocumentRepository documentRepository,
                         UserRepository userRepository,
                         KeyManager keyManager,
                         NotificationService notificationService,
                         AuditService auditService) {
        this.policyService = policyService;
        this.documentRepository = documentRepository;
        this.userRepository = userRepository;
        this.keyManager = keyManager;
        this.notificationService = notificationService;
        this.auditService = auditService;
    }

    /** Grants a recipient access to a document and notifies them. */
    public AccessGrant grantAccess(String documentId, String grantorId,
                                   String granteeId, Policy.Permission permission) {
        InputValidator.validateIdentifier(documentId);
        Document document = documentRepository.findDocument(documentId);
        User grantor = userRepository.findUser(grantorId);
        User grantee = userRepository.findUser(granteeId);

        Policy policy = policyService.createSharePolicy(documentId, granteeId, permission);
        AccessGrant grant = new AccessGrant(UUID.randomUUID().toString(),
                documentId, grantorId, granteeId, policy.getPolicyId());

        notificationService.sendShareInvite(grantee.getEmail(),
                document.getFileName(), grantor.getDisplayName());
        auditService.recordEvent(AuditEvent.EventType.ACCESS_GRANTED, grantorId,
                documentId, "granted " + permission + " to " + granteeId);
        return grant;
    }

    /** Checks whether a user may perform an action on a document right now. */
    public boolean checkAccess(String documentId, String userId, Policy.Permission required) {
        Document document = documentRepository.findDocument(documentId);
        if (document.getOwnerId().equals(userId)) {
            return true;
        }
        boolean allowed = policyService.evaluatePolicy(documentId, userId, required);
        if (!allowed) {
            auditService.recordEvent(AuditEvent.EventType.ACCESS_DENIED, userId,
                    documentId, "required " + required);
        }
        return allowed;
    }

    /** Revokes a user's access and rotates the document key so old copies go dark. */
    public void revokeAccess(String documentId, String ownerId, String granteeId) {
        Document document = documentRepository.findDocument(documentId);
        User grantee = userRepository.findUser(granteeId);

        int revoked = policyService.revokePoliciesForUser(documentId, granteeId);
        if (revoked > 0) {
            keyManager.rotateKey(documentId, document.getKeyId());
            notificationService.sendRevocationNotice(grantee.getEmail(), document.getFileName());
        }
        auditService.recordEvent(AuditEvent.EventType.ACCESS_REVOKED, ownerId,
                documentId, "revoked " + revoked + " policies for " + granteeId);
    }
}
