/// <summary>
/// C# User Management Service
/// Provides comprehensive user management functionality
/// </summary>

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;

namespace DocGenie.Example
{
    /// <summary>
    /// Represents a system user
    /// </summary>
    public class User
    {
        /// <summary>
        /// Unique identifier for the user
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// User's display name
        /// </summary>
        [Required]
        [StringLength(100)]
        public string Username { get; set; }

        /// <summary>
        /// User's email address
        /// </summary>
        [Required]
        [EmailAddress]
        public string Email { get; set; }

        /// <summary>
        /// Current status of the user
        /// </summary>
        public UserStatus Status { get; set; }

        /// <summary>
        /// Date when the user was created
        /// </summary>
        public DateTime CreatedAt { get; set; }

        /// <summary>
        /// Date when the user was last updated
        /// </summary>
        public DateTime UpdatedAt { get; set; }

        /// <summary>
        /// Roles assigned to the user
        /// </summary>
        public virtual ICollection<Role> Roles { get; set; }

        /// <summary>
        /// Constructor for User
        /// </summary>
        public User()
        {
            Roles = new List<Role>();
            CreatedAt = DateTime.UtcNow;
            UpdatedAt = DateTime.UtcNow;
            Status = UserStatus.Active;
        }
    }

    /// <summary>
    /// Enumeration for user status
    /// </summary>
    public enum UserStatus
    {
        /// <summary>
        /// User is active and can access the system
        /// </summary>
        Active = 1,

        /// <summary>
        /// User is inactive but not deleted
        /// </summary>
        Inactive = 2,

        /// <summary>
        /// User is suspended temporarily
        /// </summary>
        Suspended = 3,

        /// <summary>
        /// User account is pending activation
        /// </summary>
        Pending = 4
    }

    /// <summary>
    /// Represents a user role
    /// </summary>
    public class Role
    {
        /// <summary>
        /// Role identifier
        /// </summary>
        public int Id { get; set; }

        /// <summary>
        /// Role name
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// Role description
        /// </summary>
        public string Description { get; set; }

        /// <summary>
        /// Users assigned to this role
        /// </summary>
        public virtual ICollection<User> Users { get; set; }

        /// <summary>
        /// Constructor for Role
        /// </summary>
        public Role()
        {
            Users = new List<User>();
        }
    }

    /// <summary>
    /// Interface for user repository operations
    /// </summary>
    public interface IUserRepository
    {
        /// <summary>
        /// Get user by ID
        /// </summary>
        /// <param name="id">User identifier</param>
        /// <returns>User if found, null otherwise</returns>
        Task<User> GetByIdAsync(int id);

        /// <summary>
        /// Get all users
        /// </summary>
        /// <returns>Collection of all users</returns>
        Task<IEnumerable<User>> GetAllAsync();

        /// <summary>
        /// Add a new user
        /// </summary>
        /// <param name="user">User to add</param>
        /// <returns>Added user</returns>
        Task<User> AddAsync(User user);

        /// <summary>
        /// Update existing user
        /// </summary>
        /// <param name="user">User to update</param>
        /// <returns>Updated user</returns>
        Task<User> UpdateAsync(User user);

        /// <summary>
        /// Delete user
        /// </summary>
        /// <param name="id">User identifier</param>
        /// <returns>True if deleted successfully</returns>
        Task<bool> DeleteAsync(int id);
    }

    /// <summary>
    /// User management service providing business logic
    /// </summary>
    public class UserService : IUserService
    {
        private readonly IUserRepository _userRepository;
        private readonly ILogger<UserService> _logger;
        private static readonly object _lock = new object();

        /// <summary>
        /// Constructor for UserService
        /// </summary>
        /// <param name="userRepository">User repository instance</param>
        /// <param name="logger">Logger instance</param>
        public UserService(IUserRepository userRepository, ILogger<UserService> logger)
        {
            _userRepository = userRepository ?? throw new ArgumentNullException(nameof(userRepository));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        /// <summary>
        /// Create a new user
        /// </summary>
        /// <param name="username">Username</param>
        /// <param name="email">Email address</param>
        /// <returns>Created user</returns>
        /// <exception cref="ArgumentException">Thrown when parameters are invalid</exception>
        public async Task<User> CreateUserAsync(string username, string email)
        {
            if (string.IsNullOrWhiteSpace(username))
                throw new ArgumentException("Username cannot be null or empty", nameof(username));

            if (string.IsNullOrWhiteSpace(email))
                throw new ArgumentException("Email cannot be null or empty", nameof(email));

            if (!IsValidEmail(email))
                throw new ArgumentException("Invalid email format", nameof(email));

            var user = new User
            {
                Username = username,
                Email = email,
                Status = UserStatus.Active
            };

            try
            {
                var createdUser = await _userRepository.AddAsync(user);
                _logger.LogInformation("User created successfully: {UserId}", createdUser.Id);
                return createdUser;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error creating user: {Username}", username);
                throw;
            }
        }

        /// <summary>
        /// Get user by identifier
        /// </summary>
        /// <param name="userId">User identifier</param>
        /// <returns>User if found, null otherwise</returns>
        public async Task<User> GetUserAsync(int userId)
        {
            try
            {
                return await _userRepository.GetByIdAsync(userId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving user: {UserId}", userId);
                throw;
            }
        }

        /// <summary>
        /// Get all users
        /// </summary>
        /// <returns>Collection of users</returns>
        public async Task<IEnumerable<User>> GetAllUsersAsync()
        {
            try
            {
                return await _userRepository.GetAllAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving all users");
                throw;
            }
        }

        /// <summary>
        /// Update user information
        /// </summary>
        /// <param name="userId">User identifier</param>
        /// <param name="username">New username</param>
        /// <param name="email">New email</param>
        /// <returns>Updated user</returns>
        public async Task<User> UpdateUserAsync(int userId, string username, string email)
        {
            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null)
                throw new InvalidOperationException($"User not found: {userId}");

            if (!string.IsNullOrWhiteSpace(username))
                user.Username = username;

            if (!string.IsNullOrWhiteSpace(email))
            {
                if (!IsValidEmail(email))
                    throw new ArgumentException("Invalid email format", nameof(email));
                user.Email = email;
            }

            user.UpdatedAt = DateTime.UtcNow;

            try
            {
                var updatedUser = await _userRepository.UpdateAsync(user);
                _logger.LogInformation("User updated successfully: {UserId}", userId);
                return updatedUser;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error updating user: {UserId}", userId);
                throw;
            }
        }

        /// <summary>
        /// Change user status
        /// </summary>
        /// <param name="userId">User identifier</param>
        /// <param name="status">New status</param>
        /// <returns>Updated user</returns>
        public async Task<User> ChangeUserStatusAsync(int userId, UserStatus status)
        {
            var user = await _userRepository.GetByIdAsync(userId);
            if (user == null)
                throw new InvalidOperationException($"User not found: {userId}");

            user.Status = status;
            user.UpdatedAt = DateTime.UtcNow;

            try
            {
                var updatedUser = await _userRepository.UpdateAsync(user);
                _logger.LogInformation("User status changed: {UserId} -> {Status}", userId, status);
                return updatedUser;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error changing user status: {UserId}", userId);
                throw;
            }
        }

        /// <summary>
        /// Delete a user
        /// </summary>
        /// <param name="userId">User identifier</param>
        /// <returns>True if deleted successfully</returns>
        public async Task<bool> DeleteUserAsync(int userId)
        {
            try
            {
                var result = await _userRepository.DeleteAsync(userId);
                if (result)
                    _logger.LogInformation("User deleted successfully: {UserId}", userId);
                else
                    _logger.LogWarning("User not found for deletion: {UserId}", userId);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error deleting user: {UserId}", userId);
                throw;
            }
        }

        /// <summary>
        /// Get users by status
        /// </summary>
        /// <param name="status">User status to filter by</param>
        /// <returns>Users with specified status</returns>
        public async Task<IEnumerable<User>> GetUsersByStatusAsync(UserStatus status)
        {
            try
            {
                var allUsers = await _userRepository.GetAllAsync();
                return allUsers.Where(u => u.Status == status);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving users by status: {Status}", status);
                throw;
            }
        }

        /// <summary>
        /// Validate email format
        /// </summary>
        /// <param name="email">Email to validate</param>
        /// <returns>True if valid email format</returns>
        private static bool IsValidEmail(string email)
        {
            try
            {
                var addr = new System.Net.Mail.MailAddress(email);
                return addr.Address == email;
            }
            catch
            {
                return false;
            }
        }
    }

    /// <summary>
    /// Interface for user service operations
    /// </summary>
    public interface IUserService
    {
        Task<User> CreateUserAsync(string username, string email);
        Task<User> GetUserAsync(int userId);
        Task<IEnumerable<User>> GetAllUsersAsync();
        Task<User> UpdateUserAsync(int userId, string username, string email);
        Task<User> ChangeUserStatusAsync(int userId, UserStatus status);
        Task<bool> DeleteUserAsync(int userId);
        Task<IEnumerable<User>> GetUsersByStatusAsync(UserStatus status);
    }
}