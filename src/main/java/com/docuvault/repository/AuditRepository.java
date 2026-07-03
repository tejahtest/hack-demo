package com.docuvault.repository;

import com.docuvault.model.AuditEvent;

import java.time.Instant;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/** Append-only store for the audit trail. */
public class AuditRepository {

    private final List<AuditEvent> events = new CopyOnWriteArrayList<>();

    public void appendEvent(AuditEvent event) {
        events.add(event);
    }

    public List<AuditEvent> findEventsInRange(Instant from, Instant to) {
        return events.stream()
                .filter(e -> !e.getOccurredAt().isBefore(from) && !e.getOccurredAt().isAfter(to))
                .toList();
    }

    public List<AuditEvent> findEventsForDocument(String documentId) {
        return events.stream()
                .filter(e -> documentId.equals(e.getDocumentId()))
                .toList();
    }
}
