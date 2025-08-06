/**
 * Java user management system
 * 
 * @author DocGenie Team
 * @version 1.0
 */

package com.docgenie.example;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import java.time.LocalDateTime;

/**
 * User entity class representing a system user
 */
public class User {
    private final Long id;
    private String username;
    private String email;
    private UserStatus status;
    private LocalDateTime createdAt;
    private Set<Role> roles;

    /**
     * Constructor for User
     * 
     * @param id       Unique user identifier
     * @param username User's username
     * @param email    User's email address
     */
    public User(Long id, String username, String email) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.status = UserStatus.ACTIVE;
        this.createdAt = LocalDateTime.now();
        this.roles = new HashSet<>();
    }

    // Getters and setters
    public Long getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public UserStatus getStatus() {
        return status;
    }

    public void setStatus(UserStatus status) {
        this.status = status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public Set<Role> getRoles() {
        return roles;
    }

    public void setRoles(Set<Role> roles) {
        this.roles = roles;
    }
}

/**
 * Enumeration for user status
 */
public enum UserStatus {
    ACTIVE("Active"),
    INACTIVE("Inactive"),
    SUSPENDED("Suspended"),
    PENDING("Pending Activation");

    private final String description;

    UserStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}

/**
 * Role entity representing user permissions
 */
public class Role {
    private final Long id;
    private String name;
    private String description;
    private List<Permission> permissions;

    /**
     * Constructor for Role
     * 
     * @param id          Role identifier
     * @param name        Role name
     * @param description Role description
     */
    public Role(Long id, String name, String description) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.permissions = new ArrayList<>();
    }

    // Getters and setters
    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public List<Permission> getPermissions() {
        return permissions;
    }

    public void setPermissions(List<Permission> permissions) {
        this.permissions = permissions;
    }
}

/**
 * User management service providing CRUD operations
 */
public class UserManager {
    private final Map<Long, User> users;
    private final Map<Long, Role> roles;
    private static final int MAX_USERS = 10000;

    /**
     * Default constructor
     */
    public UserManager() {
        this.users = new ConcurrentHashMap<>();
        this.roles = new ConcurrentHashMap<>();
        initializeDefaultRoles();
    }

    /**
     * Initialize default system roles
     */
    private void initializeDefaultRoles() {
        Role adminRole = new Role(1L, "ADMIN", "System administrator");
        Role userRole = new Role(2L, "USER", "Regular user");
        Role moderatorRole = new Role(3L, "MODERATOR", "Content moderator");

        roles.put(adminRole.getId(), adminRole);
        roles.put(userRole.getId(), userRole);
        roles.put(moderatorRole.getId(), moderatorRole);
    }

    /**
     * Create a new user
     * 
     * @param username User's username
     * @param email    User's email
     * @return Created user
     * @throws IllegalArgumentException if parameters are invalid
     * @throws IllegalStateException    if maximum users exceeded
     */
    public User createUser(String username, String email) {
        if (username == null || username.trim().isEmpty()) {
            throw new IllegalArgumentException("Username cannot be null or empty");
        }
        if (email == null || !isValidEmail(email)) {
            throw new IllegalArgumentException("Invalid email address");
        }
        if (users.size() >= MAX_USERS) {
            throw new IllegalStateException("Maximum number of users exceeded");
        }

        Long userId = generateUserId();
        User user = new User(userId, username, email);

        // Assign default user role
        Role defaultRole = roles.get(2L);
        if (defaultRole != null) {
            user.getRoles().add(defaultRole);
        }

        users.put(userId, user);
        return user;
    }

    /**
     * Find user by ID
     * 
     * @param userId User identifier
     * @return User if found, null otherwise
     */
    public User findUserById(Long userId) {
        return users.get(userId);
    }

    /**
     * Find users by status
     * 
     * @param status User status to filter by
     * @return List of users with specified status
     */
    public List<User> findUsersByStatus(UserStatus status) {
        return users.values().stream()
                .filter(user -> user.getStatus() == status)
                .collect(Collectors.toList());
    }

    /**
     * Update user status
     * 
     * @param userId    User identifier
     * @param newStatus New status to set
     * @return Updated user or null if not found
     */
    public User updateUserStatus(Long userId, UserStatus newStatus) {
        User user = users.get(userId);
        if (user != null) {
            user.setStatus(newStatus);
        }
        return user;
    }

    /**
     * Assign role to user
     * 
     * @param userId User identifier
     * @param roleId Role identifier
     * @return True if successful, false otherwise
     */
    public boolean assignRoleToUser(Long userId, Long roleId) {
        User user = users.get(userId);
        Role role = roles.get(roleId);

        if (user != null && role != null) {
            user.getRoles().add(role);
            return true;
        }
        return false;
    }

    /**
     * Get total user count
     * 
     * @return Number of registered users
     */
    public int getUserCount() {
        return users.size();
    }

    /**
     * Validate email format
     * 
     * @param email Email to validate
     * @return True if valid email format
     */
    private boolean isValidEmail(String email) {
        return email != null && email.contains("@") && email.contains(".");
    }

    /**
     * Generate unique user ID
     * 
     * @return New unique user ID
     */
    private Long generateUserId() {
        return System.currentTimeMillis() + (long) (Math.random() * 1000);
    }
}