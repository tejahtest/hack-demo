package com.docuvault.util;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** File-system helpers for report export and staging. */
public final class FileUtil {

    private FileUtil() { }

    /** Writes a generated report to the export directory and returns its path. */
    public static Path writeReportFile(String reportName, String content) {
        try {
            Path exportDir = Path.of("export");
            Files.createDirectories(exportDir);
            Path target = exportDir.resolve(reportName);
            Files.writeString(target, content, StandardCharsets.UTF_8);
            return target;
        } catch (IOException e) {
            throw new IllegalStateException("Failed to write report " + reportName, e);
        }
    }

    /** Best-effort overwrite of a staging file before deletion. */
    public static void scrubTempFile(Path path) {
        try {
            if (Files.exists(path)) {
                Files.write(path, new byte[(int) Math.min(Files.size(path), 1 << 20)]);
                Files.delete(path);
            }
        } catch (IOException e) {
            VaultLogger.logWarning("FileUtil", "Could not scrub temp file " + path);
        }
    }
}
