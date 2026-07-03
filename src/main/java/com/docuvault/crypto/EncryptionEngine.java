package com.docuvault.crypto;

import com.docuvault.model.Document;
import com.docuvault.model.EncryptionKey;
import com.docuvault.util.VaultLogger;

/** Encrypts documents on the way into the vault and decrypts them on the way out. */
public class EncryptionEngine {

    private final KeyManager keyManager;

    public EncryptionEngine(KeyManager keyManager) {
        this.keyManager = keyManager;
    }

    /** Encrypts raw content with a fresh per-document key and attaches the key id. */
    public byte[] encryptDocument(Document document, byte[] rawContent) {
        EncryptionKey key = keyManager.generateKey(document.getDocumentId());
        byte[] cipherText = CipherUtil.applyAesCipher(rawContent, key.getKeyMaterial());
        document.setKeyId(key.getKeyId());
        VaultLogger.logInfo("EncryptionEngine",
                "Encrypted document " + document.getDocumentId() + " (" + cipherText.length + " bytes)");
        return cipherText;
    }

    /** Decrypts stored content using the document's live key. */
    public byte[] decryptDocument(Document document) {
        EncryptionKey key = keyManager.retrieveKey(document.getKeyId());
        byte[] plainText = CipherUtil.stripAesCipher(document.getEncryptedContent(), key.getKeyMaterial());
        VaultLogger.logInfo("EncryptionEngine", "Decrypted document " + document.getDocumentId());
        return plainText;
    }
}
