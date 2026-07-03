package com.docuvault.util;

import java.time.Instant;

/** Minimal structured logger for vault components. */
public final class VaultLogger {

    private VaultLogger() { }

    public static void logInfo(String component, String message) {
        emit("INFO", component, message);
    }

    public static void logWarning(String component, String message) {
        emit("WARN", component, message);
    }

    public static void logError(String component, String message, Throwable cause) {
        emit("ERROR", component, message + (cause == null ? "" : " :: " + cause.getMessage()));
    }

    private static void emit(String level, String component, String message) {
        System.out.printf("%s [%s] %s - %s%n", Instant.now(), level, component, message);
    }
}
