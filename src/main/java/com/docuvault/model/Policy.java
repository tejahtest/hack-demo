package com.docuvault.model;

import java.time.Instant;

/** An access policy attached to a document: who may do what, until when. */
public class Policy {

    public enum Permission { VIEW, EDIT, FULL_CONTROL }

    private String policyId;
    private String documentId;
    private String granteeId;
    private Permission permission;
    private Instant expiresAt;
    private boolean revoked;

    public Policy(String policyId, String documentId, String granteeId, Permission permission) {
        this.policyId = policyId;
        this.documentId = documentId;
        this.granteeId = granteeId;
        this.permission = permission;
        this.revoked = false;
    }

    public String getPolicyId() { return policyId; }

    public String getDocumentId() { return documentId; }

    public String getGranteeId() { return granteeId; }

    public Permission getPermission() { return permission; }

    public Instant getExpiresAt() { return expiresAt; }

    public void setExpiresAt(Instant expiresAt) { this.expiresAt = expiresAt; }

    public boolean isRevoked() { return revoked; }

    public void markRevoked() { this.revoked = true; }

    public boolean isExpired() {
        return expiresAt != null && Instant.now().isAfter(expiresAt);
    }
}
