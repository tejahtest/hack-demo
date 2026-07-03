package com.docuvault.model;

import java.time.Instant;

/** The outcome of a share action: a grant issued to a recipient for a document. */
public class AccessGrant {

    private String grantId;
    private String documentId;
    private String grantorId;
    private String granteeId;
    private String policyId;
    private Instant grantedAt;

    public AccessGrant(String grantId, String documentId, String grantorId,
                       String granteeId, String policyId) {
        this.grantId = grantId;
        this.documentId = documentId;
        this.grantorId = grantorId;
        this.granteeId = granteeId;
        this.policyId = policyId;
        this.grantedAt = Instant.now();
    }

    public String getGrantId() { return grantId; }

    public String getDocumentId() { return documentId; }

    public String getGrantorId() { return grantorId; }

    public String getGranteeId() { return granteeId; }

    public String getPolicyId() { return policyId; }

    public Instant getGrantedAt() { return grantedAt; }
}
