package com.docuvault.repository;

import com.docuvault.model.Policy;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

/** Stores access policies, indexed by document. */
public class PolicyRepository {

    private final Map<String, List<Policy>> policiesByDocument = new ConcurrentHashMap<>();

    public void savePolicy(Policy policy) {
        policiesByDocument
                .computeIfAbsent(policy.getDocumentId(), id -> new CopyOnWriteArrayList<>())
                .add(policy);
    }

    /** The active (non-revoked, non-expired) policy for a user on a document, if any. */
    public Optional<Policy> findPolicyForUser(String documentId, String userId) {
        return policiesByDocument.getOrDefault(documentId, List.of()).stream()
                .filter(p -> p.getGranteeId().equals(userId))
                .filter(p -> !p.isRevoked() && !p.isExpired())
                .findFirst();
    }

    public List<Policy> findPoliciesForDocument(String documentId) {
        return List.copyOf(policiesByDocument.getOrDefault(documentId, List.of()));
    }
}
