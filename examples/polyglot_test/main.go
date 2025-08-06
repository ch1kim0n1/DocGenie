// Package main demonstrates Go language parsing capabilities
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/redis/go-redis/v9"
)

// User represents a system user
type User struct {
	ID        int64     `json:"id" db:"id"`
	Username  string    `json:"username" db:"username"`
	Email     string    `json:"email" db:"email"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

// UserService provides user management functionality
type UserService struct {
	users  map[int64]*User
	mutex  sync.RWMutex
	nextID int64
}

// NewUserService creates a new user service instance
func NewUserService() *UserService {
	return &UserService{
		users:  make(map[int64]*User),
		mutex:  sync.RWMutex{},
		nextID: 1,
	}
}

// CreateUser creates a new user
func (s *UserService) CreateUser(username, email string) (*User, error) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if username == "" || email == "" {
		return nil, fmt.Errorf("username and email are required")
	}

	user := &User{
		ID:        s.nextID,
		Username:  username,
		Email:     email,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	s.users[s.nextID] = user
	s.nextID++

	return user, nil
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(id int64) (*User, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	user, exists := s.users[id]
	if !exists {
		return nil, fmt.Errorf("user not found")
	}

	return user, nil
}

// GetAllUsers returns all users
func (s *UserService) GetAllUsers() []*User {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	users := make([]*User, 0, len(s.users))
	for _, user := range s.users {
		users = append(users, user)
	}

	return users
}

// UpdateUser updates an existing user
func (s *UserService) UpdateUser(id int64, username, email string) (*User, error) {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	user, exists := s.users[id]
	if !exists {
		return nil, fmt.Errorf("user not found")
	}

	if username != "" {
		user.Username = username
	}
	if email != "" {
		user.Email = email
	}
	user.UpdatedAt = time.Now()

	return user, nil
}

// DeleteUser removes a user
func (s *UserService) DeleteUser(id int64) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if _, exists := s.users[id]; !exists {
		return fmt.Errorf("user not found")
	}

	delete(s.users, id)
	return nil
}

// CacheService provides Redis caching functionality
type CacheService struct {
	client *redis.Client
}

// NewCacheService creates a new cache service
func NewCacheService(redisURL string) *CacheService {
	rdb := redis.NewClient(&redis.Options{
		Addr: redisURL,
	})

	return &CacheService{
		client: rdb,
	}
}

// Set stores a value in cache
func (c *CacheService) Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error {
	jsonValue, err := json.Marshal(value)
	if err != nil {
		return err
	}

	return c.client.Set(ctx, key, jsonValue, expiration).Err()
}

// Get retrieves a value from cache
func (c *CacheService) Get(ctx context.Context, key string, dest interface{}) error {
	val, err := c.client.Get(ctx, key).Result()
	if err != nil {
		return err
	}

	return json.Unmarshal([]byte(val), dest)
}

// HTTPHandler handles HTTP requests
type HTTPHandler struct {
	userService  *UserService
	cacheService *CacheService
}

// NewHTTPHandler creates a new HTTP handler
func NewHTTPHandler(userService *UserService, cacheService *CacheService) *HTTPHandler {
	return &HTTPHandler{
		userService:  userService,
		cacheService: cacheService,
	}
}

// GetUsers handles GET /users
func (h *HTTPHandler) GetUsers(w http.ResponseWriter, r *http.Request) {
	users := h.userService.GetAllUsers()
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(users)
}

// GetUser handles GET /users/{id}
func (h *HTTPHandler) GetUser(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]
	
	// Convert string to int64
	userID := int64(0) // Simplified for demo
	
	user, err := h.userService.GetUser(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

// CreateUser handles POST /users
func (h *HTTPHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Username string `json:"username"`
		Email    string `json:"email"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	user, err := h.userService.CreateUser(req.Username, req.Email)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(user)
}

// setupRoutes configures HTTP routes
func setupRoutes(handler *HTTPHandler) *mux.Router {
	r := mux.NewRouter()
	
	r.HandleFunc("/users", handler.GetUsers).Methods("GET")
	r.HandleFunc("/users/{id}", handler.GetUser).Methods("GET")
	r.HandleFunc("/users", handler.CreateUser).Methods("POST")
	
	return r
}

// main function - application entry point
func main() {
	// Initialize services
	userService := NewUserService()
	cacheService := NewCacheService("localhost:6379")
	handler := NewHTTPHandler(userService, cacheService)

	// Setup routes
	router := setupRoutes(handler)

	// Create some sample users
	userService.CreateUser("alice", "alice@example.com")
	userService.CreateUser("bob", "bob@example.com")

	// Start server
	fmt.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", router))
}

// Helper functions

// validateEmail checks if email format is valid
func validateEmail(email string) bool {
	// Simplified email validation
	return len(email) > 0 && contains(email, "@")
}

// contains checks if string contains substring
func contains(str, substr string) bool {
	return len(str) >= len(substr) && str[len(str)-len(substr):] == substr
}

// calculateHash generates a simple hash for a string
func calculateHash(input string) int {
	hash := 0
	for _, char := range input {
		hash += int(char)
	}
	return hash
}