package com.docuvault.model;

import java.time.Instant;

/** One immutable entry in the vault's audit trail. */
public class AuditEvent {

    public enum EventType {
        DOCUMENT_UPLOADED, DOCUMENT_OPENED, DOCUMENT_RENAMED, DOCUMENT_DELETED,
        DOCUMENT_TAGGED, DOCUMENT_UNTAGGED,
        RETENTION_EXPIRED,
        ACCESS_GRANTED, ACCESS_REVOKED, ACCESS_DENIED,
        USER_REGISTERED, REPORT_GENERATED
    }

    private final String eventId;
    private final EventType type;
    private final String actorId;
    private final String documentId;
    private final String detail;
    private final Instant occurredAt;

    public AuditEvent(String eventId, EventType type, String actorId,
                      String documentId, String detail) {
        this.eventId = eventId;
        this.type = type;
        this.actorId = actorId;
        this.documentId = documentId;
        this.detail = detail;
        this.occurredAt = Instant.now();
    }

    public String getEventId() { return eventId; }

    public EventType getType() { return type; }

    public String getActorId() { return actorId; }

    public String getDocumentId() { return documentId; }

    public String getDetail() { return detail; }

    public Instant getOccurredAt() { return occurredAt; }
}
