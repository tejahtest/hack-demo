package com.docuvault.service;

import com.docuvault.crypto.CipherUtil;
import com.docuvault.model.AuditEvent;
import com.docuvault.model.User;
import com.docuvault.repository.UserRepository;
import com.docuvault.util.InputValidator;

import java.util.UUID;

/** Manages vault accounts. */
public class UserService {

    private final UserRepository userRepository;
    private final NotificationService notificationService;
    private final AuditService auditService;

    public UserService(UserRepository userRepository,
                       NotificationService notificationService,
                       AuditService auditService) {
        this.userRepository = userRepository;
        this.notificationService = notificationService;
        this.auditService = auditService;
    }

    /** Registers a new account with a salted password hash and welcomes the user. */
    public User registerUser(String email, String displayName, String plainPassword) {
        InputValidator.validateEmail(email);
        if (userRepository.findUserByEmail(email).isPresent()) {
            throw new IllegalStateException("Account already exists for " + email);
        }
        User user = new User(UUID.randomUUID().toString(), email, displayName);
        user.setPasswordHash(CipherUtil.hashPassword(plainPassword));
        userRepository.saveUser(user);
        notificationService.sendWelcomeEmail(email, displayName);
        userRepository.recordWelcomeSent(user.getUserId());
        auditService.recordEvent(AuditEvent.EventType.USER_REGISTERED, user.getUserId(),
                null, email);
        return user;
    }
}
