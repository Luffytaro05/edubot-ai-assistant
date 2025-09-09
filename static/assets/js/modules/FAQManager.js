/**
 * FAQManager - Manages frequently asked questions with categories, offices, and status management
 * Extends BaseManager for common CRUD operations and localStorage persistence
 */
class FAQManager extends BaseManager {
    constructor() {
        super('faqs');
        this.initializeDefaultFAQs();
    }

    /**
     * Initialize default FAQs for demonstration
     */
    initializeDefaultFAQs() {
        if (this.getAll().length === 0) {
            const defaultFAQs = [
                // Registrar FAQs
                {
                    id: 'faq-1',
                    office: 'Registrar',
                    question: 'How do I register for classes?',
                    answer: 'You can register for classes through the student portal during your assigned registration period. Make sure to meet with your academic advisor first to plan your course schedule.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-2',
                    office: 'Registrar',
                    question: 'What if a class is full?',
                    answer: 'If a class is full, you can add yourself to the waitlist or contact the department for permission to enroll. Waitlist positions are processed automatically as spots become available.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-3',
                    office: 'Registrar',
                    question: 'Can I drop a class after the semester starts?',
                    answer: 'Yes, you can drop classes within the first two weeks of the semester without penalty. After that, you may receive a W grade on your transcript.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-4',
                    office: 'Registrar',
                    question: 'How many credits can I take per semester?',
                    answer: 'Full-time students typically take 12-18 credits per semester. You can take up to 21 credits with advisor approval. Part-time students take 1-11 credits.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-5',
                    office: 'Registrar',
                    question: 'What are the prerequisites for advanced courses?',
                    answer: 'Prerequisites vary by course and are listed in the course catalog. You must complete prerequisites with a grade of C or better before enrolling in advanced courses.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-6',
                    office: 'Registrar',
                    question: 'How do I get an override for a course?',
                    answer: 'Course overrides can be requested through the department offering the course. You\'ll need to provide a reason and may need instructor permission.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-7',
                    office: 'Registrar',
                    question: 'What is the academic calendar?',
                    answer: 'The academic year consists of Fall (August-December), Spring (January-May), and Summer (May-August) semesters. Check the university calendar for specific dates and holidays.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-8',
                    office: 'Registrar',
                    question: 'How do I calculate my GPA?',
                    answer: 'GPA is calculated by dividing total grade points by total credit hours. A = 4.0, B = 3.0, C = 2.0, D = 1.0, F = 0.0. You can view your GPA on your academic transcript.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },

                // Admissions FAQs
                {
                    id: 'faq-9',
                    office: 'Admissions',
                    question: 'What are the admission requirements for undergraduate programs?',
                    answer: 'To be admitted to undergraduate programs, you need a high school diploma with at least 85% in Mathematics and English, SAT scores of 1200+, and a completed application form. The deadline for Fall 2024 is March 1st.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-10',
                    office: 'Admissions',
                    question: 'How do I apply for graduate programs?',
                    answer: 'Graduate program applications require a bachelor\'s degree with a minimum GPA of 3.0, GRE/GMAT scores, letters of recommendation, and a statement of purpose. Applications are accepted year-round.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-11',
                    office: 'Admissions',
                    question: 'What documents do I need for international student admission?',
                    answer: 'International students need a valid passport, academic transcripts (translated and evaluated), English proficiency test scores (TOEFL/IELTS), financial statements, and visa documentation.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-12',
                    office: 'Admissions',
                    question: 'Is there an application fee waiver available?',
                    answer: 'Application fee waivers are available for students with demonstrated financial need, veterans, and participants in certain programs like Upward Bound. Contact the admissions office for details.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-13',
                    office: 'Admissions',
                    question: 'How long does the admission process take?',
                    answer: 'The admission process typically takes 4-6 weeks for domestic students and 8-12 weeks for international students. Early applications are encouraged.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-14',
                    office: 'Admissions',
                    question: 'Can I transfer credits from another institution?',
                    answer: 'Yes, transfer credits are accepted for courses with a grade of C or better from accredited institutions. A maximum of 60 credits can be transferred for undergraduate programs.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },

                // Guidance FAQs
                {
                    id: 'faq-15',
                    office: 'Guidance',
                    question: 'How do I apply for financial aid?',
                    answer: 'Complete the FAFSA (Free Application for Federal Student Aid) online at fafsa.gov. The priority deadline is March 1st. You\'ll also need to complete any additional institutional forms.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-16',
                    office: 'Guidance',
                    question: 'What types of scholarships are available?',
                    answer: 'We offer merit-based scholarships, need-based grants, departmental scholarships, and external scholarships. Check our scholarship database for current opportunities.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-17',
                    office: 'Guidance',
                    question: 'How do student loans work?',
                    answer: 'Federal student loans are available to eligible students. You must complete the FAFSA and maintain satisfactory academic progress. Repayment begins 6 months after graduation.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-18',
                    office: 'Guidance',
                    question: 'Can I work on campus to help pay for school?',
                    answer: 'Yes, work-study positions are available for eligible students. These part-time jobs are typically 10-20 hours per week and pay minimum wage or higher.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-19',
                    office: 'Guidance',
                    question: 'What is the cost of attendance?',
                    answer: 'The total cost of attendance includes tuition, fees, room and board, books, and personal expenses. For the current academic year, it\'s approximately $25,000 for in-state students.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },

                // ICT Services FAQs
                {
                    id: 'faq-20',
                    office: 'ICT Services',
                    question: 'How do I reset my student portal password?',
                    answer: 'You can reset your password by visiting the IT help desk or using the "Forgot Password" link on the student portal login page. You\'ll need to provide your student ID and answer security questions.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-21',
                    office: 'ICT Services',
                    question: 'What software is available for students?',
                    answer: 'Students have access to Microsoft Office 365, Adobe Creative Suite, and various academic software through the university\'s software portal. Contact IT Services for installation assistance.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-22',
                    office: 'ICT Services',
                    question: 'How do I connect to campus WiFi?',
                    answer: 'Connect to the "EduChat-Student" network using your student credentials. For guest access, contact the IT help desk for temporary credentials.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-23',
                    office: 'ICT Services',
                    question: 'Where can I print on campus?',
                    answer: 'Printing is available in the library, computer labs, and student centers. You can use your student ID card or print credits. Color printing costs $0.25 per page.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },

                // OSA FAQs
                {
                    id: 'faq-24',
                    office: 'Office of Student Affairs (OSA)',
                    question: 'What housing options are available?',
                    answer: 'We offer traditional residence halls, apartment-style housing, and Greek housing. First-year students are required to live on campus. Housing applications open in February.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                },
                {
                    id: 'faq-25',
                    office: 'Office of Student Affairs (OSA)',
                    question: 'How do I get involved in student organizations?',
                    answer: 'There are over 200 student organizations on campus. You can browse them at the Student Activities Fair in September or visit the Student Life office for more information.',
                    status: 'published',
                    createdAt: new Date().toISOString()
                }
            ];

            defaultFAQs.forEach(faq => {
                this.addFAQ(faq);
            });
        }
    }

    /**
     * Get available offices
     * @returns {Array} Array of office names
     */
    getAvailableOffices() {
        return [
            'Registrar',
            'Admissions', 
            'Guidance',
            'ICT Services',
            'Office of Student Affairs (OSA)'
        ];
    }

    /**
     * Add a new FAQ
     * @param {Object} faqData - The FAQ data
     * @returns {Object} Result object with success status and message
     */
    addFAQ(faqData) {
        try {
            // Validate required fields
            if (!faqData.question || !faqData.answer || !faqData.office) {
                return { success: false, message: 'Question, answer, and office are required' };
            }

            // Validate office
            const validOffices = this.getAvailableOffices();
            if (!validOffices.includes(faqData.office)) {
                return { success: false, message: 'Invalid office' };
            }

            // Check for duplicate questions
            const existingFAQs = this.getAll();
            const duplicate = existingFAQs.find(faq => 
                faq.question.toLowerCase() === faqData.question.toLowerCase()
            );
            if (duplicate) {
                return { success: false, message: 'A FAQ with this question already exists' };
            }

            // Create new FAQ
            const newFAQ = {
                id: this.generateId(),
                office: faqData.office,
                question: faqData.question,
                answer: faqData.answer,
                status: faqData.status || 'draft',
                createdAt: new Date().toISOString()
            };

            existingFAQs.push(newFAQ);
            this.save(existingFAQs);

            return { success: true, message: 'FAQ added successfully' };
        } catch (error) {
            console.error('Error adding FAQ:', error);
            return { success: false, message: 'Failed to add FAQ' };
        }
    }

    /**
     * Update an existing FAQ
     * @param {string} id - The FAQ ID
     * @param {Object} updates - The updates to apply
     * @returns {Object} Result object with success status and message
     */
    updateFAQ(id, updates) {
        try {
            const faqs = this.getAll();
            const faqIndex = faqs.findIndex(faq => faq.id === id);
            
            if (faqIndex === -1) {
                return { success: false, message: 'FAQ not found' };
            }

            // Validate updates
            if (updates.question && updates.question.trim() === '') {
                return { success: false, message: 'Question cannot be empty' };
            }

            if (updates.answer && updates.answer.trim() === '') {
                return { success: false, message: 'Answer cannot be empty' };
            }

            if (updates.office) {
                const validOffices = this.getAvailableOffices();
                if (!validOffices.includes(updates.office)) {
                    return { success: false, message: 'Invalid office' };
                }
            }

            // Check for duplicate questions (excluding current FAQ)
            if (updates.question) {
                const duplicate = faqs.find(faq => 
                    faq.id !== id && faq.question.toLowerCase() === updates.question.toLowerCase()
                );
                if (duplicate) {
                    return { success: false, message: 'A FAQ with this question already exists' };
                }
            }

            // Apply updates
            Object.assign(faqs[faqIndex], updates);
            faqs[faqIndex].updatedAt = new Date().toISOString();

            this.save(faqs);
            return { success: true, message: 'FAQ updated successfully' };
        } catch (error) {
            console.error('Error updating FAQ:', error);
            return { success: false, message: 'Failed to update FAQ' };
        }
    }

    /**
     * Delete a FAQ
     * @param {string} id - The FAQ ID
     * @returns {Object} Result object with success status and message
     */
    deleteFAQ(id) {
        try {
            const faqs = this.getAll();
            const faqIndex = faqs.findIndex(faq => faq.id === id);
            
            if (faqIndex === -1) {
                return { success: false, message: 'FAQ not found' };
            }

            faqs.splice(faqIndex, 1);
            this.save(faqs);

            return { success: true, message: 'FAQ deleted successfully' };
        } catch (error) {
            console.error('Error deleting FAQ:', error);
            return { success: false, message: 'Failed to delete FAQ' };
        }
    }



    /**
     * Get FAQs by status
     * @param {string} status - The status to filter by
     * @returns {Array} Array of FAQs with the specified status
     */
    getByStatus(status) {
        const faqs = this.getAll();
        return faqs.filter(faq => faq.status === status);
    }

    /**
     * Get FAQs by office
     * @param {string} office - The office to filter by
     * @returns {Array} Array of FAQs in the specified office
     */
    getByOffice(office) {
        const faqs = this.getAll();
        return faqs.filter(faq => faq.office === office);
    }



    /**
     * Search FAQs
     * @param {string} query - The search query
     * @returns {Array} Array of matching FAQs
     */
    searchFAQs(query) {
        const faqs = this.getAll();
        const lowerQuery = query.toLowerCase();

        return faqs.filter(faq => {
            // Search in question
            if (faq.question.toLowerCase().includes(lowerQuery)) {
                return true;
            }

            // Search in answer
            if (faq.answer.toLowerCase().includes(lowerQuery)) {
                return true;
            }

            // Search in office
            if (faq.office && faq.office.toLowerCase().includes(lowerQuery)) {
                return true;
            }

            return false;
        });
    }

    /**
     * Get FAQ statistics
     * @returns {Object} Statistics object
     */
    getStats() {
        const faqs = this.getAll();
        const stats = {
            total: faqs.length,
            byOffice: {
                'Registrar': 0,
                'Admissions': 0,
                'Guidance': 0,
                'ICT Services': 0,
                'Office of Student Affairs (OSA)': 0
            },
            byStatus: {
                published: 0,
                draft: 0
            }
        };

        faqs.forEach(faq => {
            // Count by office
            if (faq.office && stats.byOffice[faq.office] !== undefined) {
                stats.byOffice[faq.office]++;
            }

            // Count by status
            const status = faq.status.toLowerCase();
            if (stats.byStatus[status] !== undefined) {
                stats.byStatus[status]++;
            }
        });

        return stats;
    }

    /**
     * Add a new category
     * @param {Object} categoryData - The category data
     * @returns {Object} Result object with success status and message
     */
    addCategory(categoryData) {
        try {
            // Validate required fields
            if (!categoryData.name || !categoryData.description) {
                return { success: false, message: 'Name and description are required' };
            }

            // In a real application, you would store categories separately
            // For this demo, we'll just return success
            return { success: true, message: 'Category added successfully' };
        } catch (error) {
            console.error('Error adding category:', error);
            return { success: false, message: 'Failed to add category' };
        }
    }

    /**
     * Get recent FAQs
     * @param {number} limit - Maximum number of FAQs to return
     * @returns {Array} Array of recent FAQs
     */
    getRecent(limit = 5) {
        const faqs = this.getAll();
        return faqs
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            .slice(0, limit);
    }

    /**
     * Get popular FAQs (based on views/clicks - simulated)
     * @param {number} limit - Maximum number of FAQs to return
     * @returns {Array} Array of popular FAQs
     */
    getPopular(limit = 5) {
        const faqs = this.getAll();
        // Simulate popularity by random selection
        return faqs
            .sort(() => Math.random() - 0.5)
            .slice(0, limit);
    }

    /**
     * Export FAQs to CSV
     * @param {Array} faqs - FAQs to export (optional, defaults to all)
     * @returns {string} CSV content
     */
    exportToCSV(faqs = null) {
        try {
            const data = faqs || this.getAll();
            
            if (data.length === 0) {
                return null;
            }

            // Define CSV headers
            const headers = [
                'ID',
                'Office',
                'Question',
                'Answer',
                'Status',
                'Created At'
            ];

            // Create CSV content
            let csvContent = headers.join(',') + '\n';

            data.forEach(faq => {
                const row = [
                    faq.id,
                    faq.office || '',
                    `"${faq.question.replace(/"/g, '""')}"`,
                    `"${faq.answer.replace(/"/g, '""')}"`,
                    faq.status,
                    faq.createdAt
                ];
                csvContent += row.join(',') + '\n';
            });

            return csvContent;
        } catch (error) {
            console.error('Error exporting FAQs to CSV:', error);
            return null;
        }
    }

    /**
     * Import FAQs from CSV
     * @param {string} csvData - CSV string of FAQs
     * @returns {Object} Result object with success status and message
     */
    importFromCSV(csvData) {
        try {
            const lines = csvData.split('\n');
            const headers = lines[0].split(',');
            const faqs = [];

            for (let i = 1; i < lines.length; i++) {
                if (lines[i].trim() === '') continue;

                const values = lines[i].split(',');
                const faq = {
                    id: this.generateId(),
                    office: values[1],
                    question: values[2].replace(/^"|"$/g, ''),
                    answer: values[3].replace(/^"|"$/g, ''),
                    status: values[4],
                    createdAt: new Date().toISOString()
                };

                faqs.push(faq);
            }

            const existingFAQs = this.getAll();
            existingFAQs.push(...faqs);
            this.save(existingFAQs);

            return { success: true, message: 'FAQs imported successfully' };
        } catch (error) {
            console.error('Error importing FAQs from CSV:', error);
            return { success: false, message: 'Failed to import FAQs' };
        }
    }

    /**
     * Get FAQs by search relevance
     * @param {string} query - The search query
     * @returns {Array} Array of FAQs sorted by relevance
     */
    searchByRelevance(query) {
        const faqs = this.getAll();
        const lowerQuery = query.toLowerCase();

        return faqs
            .map(faq => {
                let score = 0;
                
                // Question matches get higher score
                if (faq.question.toLowerCase().includes(lowerQuery)) {
                    score += 10;
                }
                
                // Answer matches get lower score
                if (faq.answer.toLowerCase().includes(lowerQuery)) {
                    score += 5;
                }
                
                // Office matches get lowest score
                if (faq.office && faq.office.toLowerCase().includes(lowerQuery)) {
                    score += 2;
                }

                return { ...faq, relevanceScore: score };
            })
            .filter(faq => faq.relevanceScore > 0)
            .sort((a, b) => b.relevanceScore - a.relevanceScore)
            .map(faq => {
                const { relevanceScore, ...faqWithoutScore } = faq;
                return faqWithoutScore;
            });
    }
}
