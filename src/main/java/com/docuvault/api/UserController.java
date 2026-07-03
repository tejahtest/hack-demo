package com.docuvault.api;

import com.docuvault.model.User;
import com.docuvault.service.UserService;
import com.docuvault.util.VaultLogger;

/** Entry points for account management. */
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /** A new user signs up for a vault account. */
    public String handleRegisterUser(String email, String displayName, String password) {
        VaultLogger.logInfo("UserController", "Register request: " + email);
        User user = userService.registerUser(email, displayName, password);
        return user.getUserId();
    }
}
