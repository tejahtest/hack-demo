package com.docuvault.security;

import com.docuvault.util.VaultLogger;

/**
 * Scans uploaded content for malware before it is encrypted and stored.
 * A quarantined verdict blocks the upload so infected files never enter the vault.
 */
public class ThreatScanner {

    /** Scans raw upload content; throws if the file is judged unsafe. */
    public void scanUpload(String fileName, byte[] content) {
        VaultLogger.logInfo("ThreatScanner", "Scanning upload: " + fileName
                + " (" + (content == null ? 0 : content.length) + " bytes)");
        if (matchesKnownSignature(content)) {
            throw new SecurityException("Upload rejected: malware detected in " + fileName);
        }
    }

    /** Placeholder signature check for the demo corpus. */
    private boolean matchesKnownSignature(byte[] content) {
        return content != null && content.length >= 4
                && content[0] == 'X' && content[1] == '5' && content[2] == 'O' && content[3] == '!';
    }
}
