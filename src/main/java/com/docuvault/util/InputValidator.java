package com.docuvault.util;

import java.util.regex.Pattern;

/** Guards every request boundary: file names, emails, identifiers. */
public final class InputValidator {

    private static final Pattern EMAIL = Pattern.compile("^[\\w.+-]+@[\\w-]+\\.[\\w.]+$");
    private static final Pattern SAFE_FILE_NAME = Pattern.compile("^[\\w][\\w .()-]{0,254}$");
    private static final Pattern IDENTIFIER = Pattern.compile("^[A-Za-z0-9-]{6,64}$");

    private InputValidator() { }

    /** Rejects path traversal, control characters, and over-long names. */
    public static void validateFileName(String fileName) {
        if (fileName == null || !SAFE_FILE_NAME.matcher(fileName).matches()) {
            throw new IllegalArgumentException("Unsafe file name: " + fileName);
        }
        if (fileName.contains("..")) {
            throw new IllegalArgumentException("Path traversal rejected: " + fileName);
        }
    }

    public static void validateEmail(String email) {
        if (email == null || !EMAIL.matcher(email).matches()) {
            throw new IllegalArgumentException("Invalid email address: " + email);
        }
    }

    public static void validateIdentifier(String id) {
        if (id == null || !IDENTIFIER.matcher(id).matches()) {
            throw new IllegalArgumentException("Invalid identifier: " + id);
        }
    }
}
