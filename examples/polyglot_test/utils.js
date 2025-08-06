/**
 * JavaScript utility functions for data manipulation
 * @author DocGenie Team
 */

const fs = require('fs');
const path = require('path');

/**
 * Utility class for string operations
 */
class StringUtils {
    /**
     * Constructor for StringUtils
     * @param {Object} options - Configuration options
     */
    constructor(options = {}) {
        this.options = options;
        this.cache = new Map();
    }

    /**
     * Capitalize the first letter of a string
     * @param {string} str - Input string
     * @returns {string} Capitalized string
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    /**
     * Convert string to camelCase
     * @param {string} str - Input string
     * @returns {string} CamelCase string
     */
    toCamelCase(str) {
        return str.replace(/[-_\s]+(.)?/g, (_, c) => c ? c.toUpperCase() : '');
    }

    /**
     * Asynchronously process multiple strings
     * @param {Array<string>} strings - Array of strings to process
     * @returns {Promise<Array<string>>} Processed strings
     */
    async processStrings(strings) {
        const results = await Promise.all(
            strings.map(str => this.processString(str))
        );
        return results;
    }

    /**
     * Process a single string
     * @param {string} str - String to process
     * @returns {Promise<string>} Processed string
     */
    async processString(str) {
        // Simulate async processing
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(this.capitalize(str));
            }, 10);
        });
    }
}

/**
 * Calculate array statistics
 * @param {Array<number>} numbers - Array of numbers
 * @returns {Object} Statistics object
 */
function calculateStats(numbers) {
    if (!numbers || numbers.length === 0) {
        return { count: 0, sum: 0, average: 0 };
    }

    const sum = numbers.reduce((acc, num) => acc + num, 0);
    return {
        count: numbers.length,
        sum: sum,
        average: sum / numbers.length,
        min: Math.min(...numbers),
        max: Math.max(...numbers)
    };
}

/**
 * File utility functions
 */
const FileUtils = {
    /**
     * Read file asynchronously
     * @param {string} filePath - Path to file
     * @returns {Promise<string>} File contents
     */
    async readFile(filePath) {
        return fs.promises.readFile(filePath, 'utf8');
    },

    /**
     * Write file asynchronously
     * @param {string} filePath - Path to file
     * @param {string} content - Content to write
     * @returns {Promise<void>}
     */
    async writeFile(filePath, content) {
        await fs.promises.writeFile(filePath, content, 'utf8');
    }
};

// Arrow function examples
const multiply = (a, b) => a * b;
const square = x => x * x;
const greet = name => `Hello, ${name}!`;

// Export statements
module.exports = {
    StringUtils,
    calculateStats,
    FileUtils,
    multiply,
    square,
    greet
};