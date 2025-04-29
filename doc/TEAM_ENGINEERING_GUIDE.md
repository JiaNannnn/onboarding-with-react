# BMS to EnOS Onboarding Tool - Team Engineering Guide

## Project Overview

This document serves as the central reference and progress tracking document for the three virtual engineers responsible for developing the BMS to EnOS Onboarding Tool. Each engineer should use this document to track their progress, document decisions, and communicate direction to other team members.

## Team Structure & Responsibilities

### 1. Frontend Engineer

**Area of Responsibility:** React application, UI/UX, client-side integration

**Current Focus:**
- Implementing the multi-step onboarding workflow
- Creating reusable UI components
- Optimizing state management with Context API
- Building interactive mapping interfaces

**Next Milestones:**
- [ ] Complete TypeScript migration
- [ ] Implement drag-and-drop functionality for grouping
- [ ] Create interactive visualization for point relationships
- [ ] Improve error handling and loading states

**Recent Progress:**
- N/A - Initial setup

### 2. Backend Engineer

**Area of Responsibility:** Flask API, data processing, system integration

**Current Focus:**
- Structuring the Flask application using best practices
- Implementing core API endpoints
- Optimizing batch processing for large datasets
- Setting up comprehensive logging

**Next Milestones:**
- [ ] Complete application factory implementation
- [ ] Implement batch processing with memory management
- [ ] Create centralized error handling
- [ ] Add data validation middleware

**Recent Progress:**
- N/A - Initial setup

### 3. AI/LLM Engineer

**Area of Responsibility:** Agent-based pipeline, LLM integration, intelligent processing

**Current Focus:**
- Designing the multi-agent architecture
- Creating specialized prompts for different tasks
- Implementing pattern recognition algorithms
- Developing confidence scoring for mapping suggestions

**Next Milestones:**
- [ ] Implement Grouping Agent with pattern recognition
- [ ] Create Tagging Agent with ontology integration
- [ ] Develop Mapping Agent with confidence scoring
- [ ] Optimize token usage and implement caching

**Recent Progress:**
- N/A - Initial setup

## Development Standards

### Documentation Requirements

All engineers should adhere to these documentation standards:

1. **Code Documentation:**
   - Add docstrings to all functions, classes, and methods
   - Include type hints for parameters and return values
   - Document complex algorithms with clear explanations

2. **Change Documentation:**
   - Document significant changes in this file under your section
   - Include rationale for architectural decisions
   - Note performance improvements and benchmarks

3. **Progress Updates:**
   - Update your section weekly with completed items
   - Mark completed milestones and add new ones
   - Document any blockers or issues

### Collaboration Guidelines

1. **API Contracts:**
   - Frontend and Backend engineers must agree on API contracts before implementation
   - Document API changes in a shared specification

2. **Performance Considerations:**
   - Document performance implications for significant changes
   - Include before/after metrics when optimizing code

3. **Cross-functional Testing:**
   - Test integration points between different system components
   - Document test scenarios and expected outcomes

## Development Workflow

### Feature Implementation Process

1. **Planning:**
   - Document the feature design in this file
   - Get implicit approval from other virtual engineers

2. **Implementation:**
   - Develop the feature according to the documented design
   - Follow code style and standards in CLAUDE.md

3. **Testing:**
   - Add appropriate tests (unit, integration, etc.)
   - Test integration with other components

4. **Documentation:**
   - Update this document with completed work
   - Add technical documentation as needed

### Progress Tracking

Engineers should update their progress by:
1. Marking completed milestones with [x]
2. Adding date and description to "Recent Progress"
3. Adding new milestones as needed

## Technical Decisions & Architecture

### Frontend Architecture

- React functional components with hooks
- Material UI for design system
- Context API for state management
- React Router for navigation
- Axios for API communication

### Backend Architecture

- Flask application factory pattern
- Blueprints for API resources
- Service layer for business logic
- Data access layer for file operations
- Comprehensive logging and diagnostics

### AI/LLM Architecture

- Multi-agent pipeline (Grouping, Tagging, Mapping)
- GPT-4o integration with specialized prompts
- Memory-efficient processing with batching
- Ontology versioning and caching
- Confidence scoring for mapping suggestions

## Technical Debt & Known Issues

Document any technical debt or known issues that need attention:

1. TBD - This section will be populated as work progresses

## Integration Points

Document critical integration points between components:

1. **Frontend ↔ Backend:**
   - API endpoints for data exchange
   - Error handling coordination
   - Data format specifications

2. **Backend ↔ AI/LLM:**
   - Agent invocation interfaces
   - Data transformation between stages
   - Error handling and recovery

3. **AI/LLM ↔ Frontend:**
   - Confidence score visualization
   - Mapping suggestion presentation
   - Feedback mechanisms for improving suggestions

---

*Last updated: March 20, 2025*

*Note: Each virtual engineer should update their respective sections as they make progress on the project.*