package com.docuvault.repository;

import com.docuvault.model.User;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/** Stores vault accounts, indexed by id and by email. */
public class UserRepository {

    private final Map<String, User> usersById = new ConcurrentHashMap<>();
    private final Map<String, String> idsByEmail = new ConcurrentHashMap<>();

    public void saveUser(User user) {
        usersById.put(user.getUserId(), user);
        idsByEmail.put(user.getEmail().toLowerCase(), user.getUserId());
    }

    public User findUser(String userId) {
        User user = usersById.get(userId);
        if (user == null) {
            throw new IllegalStateException("User not found: " + userId);
        }
        return user;
    }

    public Optional<User> findUserByEmail(String email) {
        String id = idsByEmail.get(email.toLowerCase());
        return id == null ? Optional.empty() : Optional.of(usersById.get(id));
    }
}
