package com.docuvault.service;

import com.docuvault.util.VaultLogger;

/** Sends user-facing notifications for vault events (email in production). */
public class NotificationService {

    /** Tells a recipient they were given access to a document. */
    public void sendShareInvite(String recipientEmail, String documentName, String grantorName) {
        deliverEmail(recipientEmail, "You have access to " + documentName,
                grantorName + " shared the protected document '" + documentName + "' with you.");
    }

    /** Tells a recipient their access to a document was withdrawn. */
    public void sendRevocationNotice(String recipientEmail, String documentName) {
        deliverEmail(recipientEmail, "Access withdrawn: " + documentName,
                "Your access to the protected document '" + documentName + "' has been revoked.");
    }

    /** Welcomes a newly registered vault user. */
    public void sendWelcomeEmail(String recipientEmail, String displayName) {
        deliverEmail(recipientEmail, "Welcome to DocuVault",
                "Hi " + displayName + ", your vault account is ready.");
    }

    private void deliverEmail(String to, String subject, String body) {
        VaultLogger.logInfo("NotificationService", "-> " + to + " | " + subject + " | " + body);
    }
}
