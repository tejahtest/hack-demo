package com.docuvault.model;

import java.time.Instant;

/** A vault account. Passwords are stored only as salted hashes. */
public class User {

    private String userId;
    private String email;
    private String displayName;
    private String passwordHash;
    private Instant registeredAt;
    private boolean active;

    public User(String userId, String email, String displayName) {
        this.userId = userId;
        this.email = email;
        this.displayName = displayName;
        this.registeredAt = Instant.now();
        this.active = true;
    }

    public String getUserId() { return userId; }

    public String getEmail() { return email; }

    public String getDisplayName() { return displayName; }

    public String getPasswordHash() { return passwordHash; }

    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public Instant getRegisteredAt() { return registeredAt; }

    public boolean isActive() { return active; }

    public void deactivate() { this.active = false; }
}
