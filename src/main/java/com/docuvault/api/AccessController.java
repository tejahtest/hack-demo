package com.docuvault.api;

import com.docuvault.model.AccessGrant;
import com.docuvault.model.Policy;
import com.docuvault.service.AccessService;
import com.docuvault.util.VaultLogger;

/** Entry points for sharing: grant access and revoke it. */
public class AccessController {

    private final AccessService accessService;

    public AccessController(AccessService accessService) {
        this.accessService = accessService;
    }

    /** An owner shares a protected document with another user. */
    public String handleShareDocument(String documentId, String grantorId,
                                      String granteeId, String permissionName) {
        VaultLogger.logInfo("AccessController", "Share request: " + documentId
                + " " + grantorId + " -> " + granteeId + " (" + permissionName + ")");
        Policy.Permission permission = Policy.Permission.valueOf(permissionName);
        AccessGrant grant = accessService.grantAccess(documentId, grantorId, granteeId, permission);
        return grant.getGrantId();
    }

    /** An owner revokes a user's access; the document key is rotated immediately. */
    public void handleRevokeAccess(String documentId, String ownerId, String granteeId) {
        VaultLogger.logInfo("AccessController", "Revoke request: " + documentId
                + " for " + granteeId);
        accessService.revokeAccess(documentId, ownerId, granteeId);
    }
}
