package com.docuvault.api;

import com.docuvault.service.RetentionService;
import com.docuvault.util.VaultLogger;

/** Entry points for scheduled vault maintenance jobs. */
public class MaintenanceController {

    private final RetentionService retentionService;

    public MaintenanceController(RetentionService retentionService) {
        this.retentionService = retentionService;
    }

    /** The scheduler triggers a retention sweep; expired documents are shredded. */
    public int handleRetentionSweep() {
        VaultLogger.logInfo("MaintenanceController", "Retention sweep requested");
        return retentionService.sweepExpiredDocuments();
    }
}
