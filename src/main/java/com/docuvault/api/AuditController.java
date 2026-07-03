package com.docuvault.api;

import com.docuvault.service.AuditService;
import com.docuvault.util.VaultLogger;

import java.nio.file.Path;
import java.time.Instant;

/** Entry points for compliance reporting. */
public class AuditController {

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    /** A compliance officer exports the audit trail for a period. */
    public String handleGenerateReport(Instant from, Instant to) {
        VaultLogger.logInfo("AuditController", "Report request: " + from + " .. " + to);
        Path report = auditService.buildComplianceReport(from, to);
        return report.toString();
    }
}
