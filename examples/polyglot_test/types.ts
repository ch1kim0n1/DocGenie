/**
 * TypeScript type definitions and utility functions
 */

import { EventEmitter } from 'events';

// Type definitions
export interface User {
    id: number;
    name: string;
    email: string;
    roles: Role[];
    createdAt: Date;
}

export interface Role {
    id: number;
    name: string;
    permissions: Permission[];
}

export interface Permission {
    id: number;
    action: string;
    resource: string;
}

// Type aliases
export type UserStatus = 'active' | 'inactive' | 'pending';
export type EventCallback<T> = (data: T) => void;
export type ApiResponse<T> = {
    success: boolean;
    data?: T;
    error?: string;
};

// Enums
export enum UserRole {
    ADMIN = 'admin',
    USER = 'user',
    MODERATOR = 'moderator'
}

export enum HttpStatus {
    OK = 200,
    CREATED = 201,
    BAD_REQUEST = 400,
    UNAUTHORIZED = 401,
    NOT_FOUND = 404,
    INTERNAL_ERROR = 500
}

// Namespace
export namespace ApiTypes {
    export interface Request {
        method: string;
        url: string;
        headers: Record<string, string>;
        body?: any;
    }

    export interface Response {
        status: number;
        headers: Record<string, string>;
        body: any;
    }
}

/**
 * Generic user service class
 */
export class UserService<T extends User> extends EventEmitter {
    private users: Map<number, T> = new Map();
    private readonly maxUsers: number;

    /**
     * Constructor for UserService
     * @param maxUsers Maximum number of users allowed
     */
    constructor(maxUsers: number = 1000) {
        super();
        this.maxUsers = maxUsers;
    }

    /**
     * Add a new user
     * @param user User to add
     * @returns Promise resolving to the added user
     */
    async addUser(user: T): Promise<T> {
        if (this.users.size >= this.maxUsers) {
            throw new Error('Maximum users exceeded');
        }

        this.users.set(user.id, user);
        this.emit('userAdded', user);
        return user;
    }

    /**
     * Get user by ID
     * @param id User ID
     * @returns User if found, undefined otherwise
     */
    getUser(id: number): T | undefined {
        return this.users.get(id);
    }

    /**
     * Update user status
     * @param id User ID
     * @param status New status
     * @returns Updated user or undefined if not found
     */
    updateUserStatus(id: number, status: UserStatus): T | undefined {
        const user = this.users.get(id);
        if (user) {
            (user as any).status = status;
            this.emit('userUpdated', user);
        }
        return user;
    }

    /**
     * Get all users with a specific role
     * @param role Role to filter by
     * @returns Array of users with the specified role
     */
    getUsersByRole(role: UserRole): T[] {
        return Array.from(this.users.values()).filter(user => 
            user.roles.some(r => r.name === role)
        );
    }
}

/**
 * Utility functions
 */
export class ApiUtils {
    /**
     * Create a standardized API response
     * @param success Whether the operation was successful
     * @param data Response data
     * @param error Error message if any
     * @returns Formatted API response
     */
    static createResponse<T>(
        success: boolean, 
        data?: T, 
        error?: string
    ): ApiResponse<T> {
        return { success, data, error };
    }

    /**
     * Validate user data
     * @param userData User data to validate
     * @returns True if valid, false otherwise
     */
    static validateUser(userData: Partial<User>): boolean {
        return !!(userData.name && userData.email && userData.id);
    }

    /**
     * Format user for API response
     * @param user User to format
     * @returns Formatted user data
     */
    static formatUser(user: User): Omit<User, 'roles'> & { roleNames: string[] } {
        const { roles, ...userWithoutRoles } = user;
        return {
            ...userWithoutRoles,
            roleNames: roles.map(role => role.name)
        };
    }
}

// Function overloads
export function processData(data: string): string;
export function processData(data: number): number;
export function processData(data: boolean): boolean;
export function processData(data: any): any {
    if (typeof data === 'string') {
        return data.toUpperCase();
    } else if (typeof data === 'number') {
        return data * 2;
    } else if (typeof data === 'boolean') {
        return !data;
    }
    return data;
}