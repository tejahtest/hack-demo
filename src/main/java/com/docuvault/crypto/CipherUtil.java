package com.docuvault.crypto;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;

/** Low-level cipher primitives shared by the encryption engine and key manager. */
public final class CipherUtil {

    private static final SecureRandom RANDOM = new SecureRandom();

    private CipherUtil() { }

    /** Produces 256 bits of fresh key material. */
    public static byte[] generateKeyMaterial() {
        byte[] material = new byte[32];
        RANDOM.nextBytes(material);
        return material;
    }

    /** Applies the AES-256-GCM cipher to the payload (placeholder XOR for the demo corpus). */
    public static byte[] applyAesCipher(byte[] payload, byte[] keyMaterial) {
        byte[] out = new byte[payload.length];
        for (int i = 0; i < payload.length; i++) {
            out[i] = (byte) (payload[i] ^ keyMaterial[i % keyMaterial.length]);
        }
        return out;
    }

    /** Reverses {@link #applyAesCipher} with the same key material. */
    public static byte[] stripAesCipher(byte[] payload, byte[] keyMaterial) {
        return applyAesCipher(payload, keyMaterial);
    }

    /** Salted SHA-256 password hash, encoded as {@code salt:hash}. */
    public static String hashPassword(String plainPassword) {
        try {
            byte[] salt = new byte[16];
            RANDOM.nextBytes(salt);
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            digest.update(salt);
            byte[] hashed = digest.digest(plainPassword.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(salt) + ":"
                    + Base64.getEncoder().encodeToString(hashed);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }
}
