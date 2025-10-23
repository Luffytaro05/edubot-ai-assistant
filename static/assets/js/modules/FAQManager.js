/**
 * FAQManager.js - Handles FAQ management operations
 * Extends BaseManager for CRUD operations with FAQ-specific functionality
 */

class FAQManager extends BaseManager {
    constructor() {
        super();
        this.baseUrl = '/api/faqs';
        this.currentOffice = 'all';
    }

    /**
     * Get all FAQs or filter by office
     * @param {string} office - Office filter (optional)
     * @returns {Promise<Object>} API response
     */
    async getFAQs(office = null) {
        try {
            const url = office ? `${this.baseUrl}?office=${encodeURIComponent(office)}` : this.baseUrl;
            const response = await this.makeRequest('GET', url);
            return response;
        } catch (error) {
            console.error('Error fetching FAQs:', error);
            return { success: false, message: 'Failed to fetch FAQs', faqs: [] };
        }
    }

    /**
     * Add a new FAQ
     * @param {Object} faqData - FAQ data (office, question, answer, status)
     * @returns {Promise<Object>} API response
     */
    async addFAQ(faqData) {
        try {
            // Validate required fields
            if (!faqData.office || !faqData.question || !faqData.answer) {
                return {
                    success: false,
                    message: 'Office, question, and answer are required'
                };
            }

            const response = await this.makeRequest('POST', this.baseUrl, faqData);
            return response;
        } catch (error) {
            console.error('Error adding FAQ:', error);
            return { success: false, message: 'Failed to add FAQ' };
        }
    }

    /**
     * Update an existing FAQ
     * @param {string} faqId - FAQ ID
     * @param {Object} updateData - Updated FAQ data
     * @returns {Promise<Object>} API response
     */
    async updateFAQ(faqId, updateData) {
        try {
            if (!faqId) {
                return { success: false, message: 'FAQ ID is required' };
            }

            const response = await this.makeRequest('PUT', `${this.baseUrl}/${faqId}`, updateData);
            return response;
        } catch (error) {
            console.error('Error updating FAQ:', error);
            return { success: false, message: 'Failed to update FAQ' };
        }
    }

    /**
     * Delete an FAQ
     * @param {string} faqId - FAQ ID
     * @returns {Promise<Object>} API response
     */
    async deleteFAQ(faqId) {
        try {
            if (!faqId) {
                return { success: false, message: 'FAQ ID is required' };
            }

            const response = await this.makeRequest('DELETE', `${this.baseUrl}/${faqId}`);
            return response;
        } catch (error) {
            console.error('Error deleting FAQ:', error);
            return { success: false, message: 'Failed to delete FAQ' };
        }
    }

    /**
     * Get a specific FAQ by ID
     * @param {string} faqId - FAQ ID
     * @returns {Promise<Object>} API response
     */
    async getFAQById(faqId) {
        try {
            if (!faqId) {
                return { success: false, message: 'FAQ ID is required' };
            }

            const response = await this.makeRequest('GET', `${this.baseUrl}/${faqId}`);
            return response;
        } catch (error) {
            console.error('Error fetching FAQ:', error);
            return { success: false, message: 'Failed to fetch FAQ' };
        }
    }

    /**
     * Search FAQs using vector similarity
     * @param {string} query - Search query
     * @param {string} office - Office filter (optional)
     * @param {number} topK - Number of results to return
     * @returns {Promise<Object>} API response
     */
    async searchFAQs(query, office = null, topK = 5) {
        try {
            if (!query || !query.trim()) {
                return { success: false, message: 'Search query is required', results: [] };
            }

            const searchData = {
                query: query.trim(),
                top_k: topK
            };

            if (office && office !== 'all') {
                searchData.office = office;
            }

            const response = await this.makeRequest('POST', `${this.baseUrl}/search`, searchData);
            return response;
        } catch (error) {
            console.error('Error searching FAQs:', error);
            return { success: false, message: 'Failed to search FAQs', results: [] };
        }
    }

    /**
     * Set current office filter
     * @param {string} office - Office name
     */
    setCurrentOffice(office) {
        this.currentOffice = office;
    }

    /**
     * Get current office filter
     * @returns {string} Current office
     */
    getCurrentOffice() {
        return this.currentOffice;
    }

    /**
     * Format FAQ data for display
     * @param {Object} faq - FAQ object
     * @returns {Object} Formatted FAQ
     */
    formatFAQ(faq) {
        return {
            id: faq._id,
            office: faq.office || 'Not Assigned',
            question: faq.question || '',
            answer: faq.answer || '',
            status: faq.status || 'published',
            created_at: faq.created_at,
            updated_at: faq.updated_at
        };
    }

    /**
     * Validate FAQ data
     * @param {Object} faqData - FAQ data to validate
     * @returns {Object} Validation result
     */
    validateFAQData(faqData) {
        const errors = [];

        if (!faqData.office || faqData.office.trim() === '') {
            errors.push('Office is required');
        }

        if (!faqData.question || faqData.question.trim() === '') {
            errors.push('Question is required');
        }

        if (!faqData.answer || faqData.answer.trim() === '') {
            errors.push('Answer is required');
        }

        if (faqData.question && faqData.question.length > 500) {
            errors.push('Question must be less than 500 characters');
        }

        if (faqData.answer && faqData.answer.length > 2000) {
            errors.push('Answer must be less than 2000 characters');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Get office statistics
     * @param {Array} faqs - Array of FAQ objects
     * @returns {Object} Statistics by office
     */
    getOfficeStats(faqs) {
        const stats = {
            total: faqs.length,
            byOffice: {},
            byStatus: {
                published: 0,
                draft: 0
            }
        };

        faqs.forEach(faq => {
            // Count by office
            const office = faq.office || 'Not Assigned';
            stats.byOffice[office] = (stats.byOffice[office] || 0) + 1;

            // Count by status
            const status = faq.status || 'published';
            stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;
        });

        return stats;
    }

    /**
     * Filter FAQs by office
     * @param {Array} faqs - Array of FAQ objects
     * @param {string} office - Office filter
     * @returns {Array} Filtered FAQs
     */
    filterFAQsByOffice(faqs, office) {
        if (!office || office === 'all') {
            return faqs;
        }
        return faqs.filter(faq => faq.office === office);
    }

    /**
     * Search FAQs locally (client-side filtering)
     * @param {Array} faqs - Array of FAQ objects
     * @param {string} query - Search query
     * @returns {Array} Filtered FAQs
     */
    searchFAQsLocally(faqs, query) {
        if (!query || query.trim() === '') {
            return faqs;
        }

        const searchTerm = query.toLowerCase();
        return faqs.filter(faq => 
            faq.question.toLowerCase().includes(searchTerm) ||
            faq.answer.toLowerCase().includes(searchTerm) ||
            (faq.office && faq.office.toLowerCase().includes(searchTerm))
        );
    }

    /**
     * Get version history for an FAQ
     * @param {string} faqId - FAQ ID
     * @returns {Promise<Object>} API response with versions array
     */
    async getFAQVersions(faqId) {
        try {
            if (!faqId) {
                return { success: false, message: 'FAQ ID is required', versions: [] };
            }

            const response = await this.makeRequest('GET', `${this.baseUrl}/${faqId}/versions`);
            return response;
        } catch (error) {
            console.error('Error fetching FAQ versions:', error);
            return { success: false, message: 'Failed to fetch version history', versions: [] };
        }
    }

    /**
     * Rollback FAQ to a specific version
     * @param {string} faqId - FAQ ID
     * @param {number} versionNumber - Version number to rollback to
     * @returns {Promise<Object>} API response
     */
    async rollbackFAQ(faqId, versionNumber) {
        try {
            if (!faqId) {
                return { success: false, message: 'FAQ ID is required' };
            }
            if (!versionNumber || versionNumber < 1) {
                return { success: false, message: 'Valid version number is required' };
            }

            const response = await this.makeRequest('POST', `${this.baseUrl}/${faqId}/rollback/${versionNumber}`);
            return response;
        } catch (error) {
            console.error('Error rolling back FAQ:', error);
            return { success: false, message: 'Failed to rollback FAQ' };
        }
    }

    /**
     * Format version timestamp for display
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted timestamp
     */
    formatVersionTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FAQManager;
}