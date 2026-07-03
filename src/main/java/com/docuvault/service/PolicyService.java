package com.docuvault.service;

import com.docuvault.model.Policy;
import com.docuvault.repository.PolicyRepository;
import com.docuvault.util.VaultLogger;

import java.util.Optional;
import java.util.UUID;

/** Decides who may do what: creates share policies and evaluates them on access. */
public class PolicyService {

    private final PolicyRepository policyRepository;

    public PolicyService(PolicyRepository policyRepository) {
        this.policyRepository = policyRepository;
    }

    /** Evaluates whether a user currently holds the required permission on a document. */
    public boolean evaluatePolicy(String documentId, String userId, Policy.Permission required) {
        Optional<Policy> policy = policyRepository.findPolicyForUser(documentId, userId);
        if (policy.isEmpty()) {
            return false;
        }
        boolean allowed = policy.get().getPermission().ordinal() >= required.ordinal();
        if (!allowed) {
            VaultLogger.logWarning("PolicyService", "Permission "
                    + required + " denied for " + userId + " on " + documentId);
        }
        return allowed;
    }

    /** Creates and stores the policy that backs a new share grant. */
    public Policy createSharePolicy(String documentId, String granteeId, Policy.Permission permission) {
        Policy policy = new Policy(UUID.randomUUID().toString(), documentId, granteeId, permission);
        policyRepository.savePolicy(policy);
        return policy;
    }

    /** Marks every policy a user holds on a document as revoked. */
    public int revokePoliciesForUser(String documentId, String userId) {
        int revoked = 0;
        for (Policy policy : policyRepository.findPoliciesForDocument(documentId)) {
            if (policy.getGranteeId().equals(userId) && !policy.isRevoked()) {
                policy.markRevoked();
                revoked++;
            }
        }
        return revoked;
    }
}
