package com.docuvault.service;

import com.docuvault.model.AuditEvent;
import com.docuvault.repository.AuditRepository;
import com.docuvault.util.FileUtil;
import com.docuvault.util.VaultLogger;

import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

/** Records every vault action and turns the trail into compliance reports. */
public class AuditService {

    private final AuditRepository auditRepository;

    public AuditService(AuditRepository auditRepository) {
        this.auditRepository = auditRepository;
    }

    /** Appends one immutable event to the audit trail. */
    public void recordEvent(AuditEvent.EventType type, String actorId,
                            String documentId, String detail) {
        AuditEvent event = new AuditEvent(UUID.randomUUID().toString(), type, actorId, documentId, detail);
        auditRepository.appendEvent(event);
        VaultLogger.logInfo("AuditService", type + " by " + actorId + " on " + documentId);
    }

    /** Builds a compliance report for the period and writes it to the export directory. */
    public Path buildComplianceReport(Instant from, Instant to) {
        List<AuditEvent> events = auditRepository.findEventsInRange(from, to);
        StringBuilder report = new StringBuilder();
        report.append("DocuVault Compliance Report\n");
        report.append("Period: ").append(from).append(" .. ").append(to).append('\n');
        report.append("Events: ").append(events.size()).append("\n\n");
        for (AuditEvent event : events) {
            report.append(event.getOccurredAt()).append("  ")
                  .append(event.getType()).append("  actor=")
                  .append(event.getActorId()).append("  doc=")
                  .append(event.getDocumentId()).append("  ")
                  .append(event.getDetail()).append('\n');
        }
        String reportName = "compliance-" + from.getEpochSecond() + "-" + to.getEpochSecond() + ".txt";
        return FileUtil.writeReportFile(reportName, report.toString());
    }
}
