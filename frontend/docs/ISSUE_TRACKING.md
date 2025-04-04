# Issue Tracking Guidelines

## Overview

This document outlines the process for tracking issues, bugs, and technical debt during the frontend implementation. It establishes a consistent approach for documenting, categorizing, and prioritizing issues to ensure they are addressed efficiently.

## Issue Categories

Issues are categorized as follows:

### 1. Bug Categories

- **Critical Bug**: Prevents core functionality from working, no workaround available
- **Major Bug**: Significant impact on functionality, workaround may be available
- **Minor Bug**: Limited impact, doesn't affect core functionality
- **UI Bug**: Visual issues that don't affect functionality
- **Type Error**: TypeScript-related errors or type inconsistencies

### 2. Enhancement Categories

- **Feature Request**: New functionality
- **Performance Improvement**: Optimization for better performance
- **Usability Enhancement**: Improvements to user experience
- **Accessibility Improvement**: Better support for accessibility
- **Code Refactoring**: Restructuring code without changing behavior

### 3. Technical Debt Categories

- **Architecture Debt**: Suboptimal architectural decisions
- **Test Debt**: Missing or inadequate tests
- **Documentation Debt**: Missing or outdated documentation
- **Type Safety Debt**: Areas where type safety could be improved

## Issue Priority Levels

Issues are prioritized as follows:

1. **P0 - Critical**: Must be fixed immediately, blocking development
2. **P1 - High**: Should be fixed in the current sprint
3. **P2 - Medium**: Should be addressed soon, but not blocking
4. **P3 - Low**: Nice to have, can be addressed when time allows
5. **P4 - Backlog**: Tracked but not planned for immediate action

## Issue Tracking Process

### Creating an Issue

When creating a new issue, include:

1. **Title**: Clear, concise description of the issue
2. **Description**: Detailed explanation of the issue
3. **Steps to Reproduce**: For bugs, steps to reproduce the issue
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Screenshots/Videos**: Visual evidence if applicable
7. **Environment**: Browser, OS, etc. if relevant
8. **Related Code**: Files or components involved
9. **Category**: From the categories listed above
10. **Priority**: From the priority levels listed above

### Issue Template

```markdown
## Issue Description
[Detailed description of the issue]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [And so on...]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Browser: [e.g. Chrome 90]
- OS: [e.g. Windows 10]
- Screen size: [if relevant]

## Additional Context
[Any other relevant information]

## Suggested Solution (optional)
[If you have ideas on how to fix it]
```

### Bug Triage Process

1. **Initial Review**: New bugs are reviewed by the tech lead
2. **Reproduction**: Bugs are verified and reproduced
3. **Prioritization**: Priority is assigned based on impact
4. **Assignment**: Issues are assigned to team members
5. **Scheduling**: High-priority issues are scheduled for immediate fix

## Current Issues

### Critical Issues (P0)

1. **AI Mapping Response Format**
   - **Description**: AI mapping responses are not following the expected format defined in enos.json
   - **Category**: Bug
   - **Assigned To**: David
   - **Status**: In Progress
   - **Impact**: Affects core mapping functionality
   - **Solution**: Implementing structured JSON response format and validation

### High Priority Issues (P1)

1. **OpenAI Agents SDK Integration**
   - **Description**: Need to integrate and properly configure OpenAI Agents SDK for mapping
   - **Category**: Enhancement
   - **Assigned To**: David
   - **Status**: In Progress
   - **Impact**: Required for AI-assisted mapping functionality

2. **Mapping Validation Enhancement**
   - **Description**: Current mapping validation needs to be enhanced to handle new response format
   - **Category**: Enhancement
   - **Assigned To**: David
   - **Status**: In Progress
   - **Impact**: Affects mapping accuracy and reliability

3. **Schema Validation Implementation**
   - **Description**: Need to implement proper validation against enos.json schema
   - **Category**: Technical Debt
   - **Assigned To**: David
   - **Status**: In Progress
   - **Impact**: Critical for ensuring mapping quality

### Medium Priority Issues (P2)

1. **Batch Processing Status**
   - **Description**: Batch processing status updates are not properly reflected in UI
   - **Category**: Bug
   - **Assigned To**: Unassigned
   - **Status**: Open
   - **Impact**: Affects user experience during large mapping operations

2. **Error Message Localization**
   - **Description**: Error messages need to support both English and Chinese
   - **Category**: Enhancement
   - **Assigned To**: Unassigned
   - **Status**: Open
   - **Impact**: Affects user experience for Chinese users

3. **Generic Point Mapping**
   - **Description**: System falls back to generic point mapping too frequently
   - **Category**: Bug
   - **Assigned To**: David
   - **Status**: Under Investigation
   - **Impact**: Affects mapping quality

### Low Priority Issues (P3)

1. **Performance Optimization**
   - **Description**: Need to optimize performance for large datasets
   - **Category**: Enhancement
   - **Assigned To**: Unassigned
   - **Status**: Open
   - **Impact**: Affects performance with large point sets

2. **Documentation Updates**
   - **Description**: Need to update documentation with latest changes
   - **Category**: Documentation
   - **Assigned To**: Unassigned
   - **Status**: Open
   - **Impact**: Affects maintainability

## Issue Resolution Workflow

1. **Open**: Issue has been created and is awaiting triage
2. **Triaged**: Issue has been reviewed and prioritized
3. **In Progress**: Someone is actively working on the issue
4. **In Review**: A fix has been proposed and is under review
5. **Resolved**: The issue has been fixed
6. **Closed**: The issue resolution has been verified

## Technical Debt Management

Technical debt is managed with the following approach:

1. **Identification**: Technical debt is identified and documented
2. **Categorization**: Debt is categorized by type and impact
3. **Prioritization**: Debt is prioritized based on impact on development
4. **Allocation**: 20% of development time is allocated to addressing technical debt
5. **Tracking**: Technical debt reduction is tracked and reported

## Technical Debt Items

| ID | Description | Category | Priority | Status |
|----|-------------|----------|----------|--------|
| TD-1 | OpenAI Agents SDK Integration | Architecture | P1 | In Progress |
| TD-2 | Schema Validation | Type Safety | P1 | In Progress |
| TD-3 | Error Message Localization | Architecture | P2 | Open |
| TD-4 | Performance Optimization | Performance | P3 | Open |
| TD-5 | Documentation Updates | Documentation | P3 | Open |

## Current Quality Metrics

- **Open Issues**: 9
- **Critical Issues**: 1
- **High Priority Issues**: 3
- **Medium Priority Issues**: 3
- **Low Priority Issues**: 2
- **Technical Debt Items**: 5
- **Type Safety Score**: 90% (improved from 85%)

## Recent Challenges

1. **AI Integration**:
   - Integration with OpenAI Agents SDK requires careful configuration
   - Need to ensure proper error handling and retry logic
   - Response format needs standardization

2. **Validation Logic**:
   - Schema validation needs to be more robust
   - Need to handle various edge cases in point mapping
   - Better error reporting needed

3. **Performance**:
   - Large datasets can cause performance issues
   - Need to implement better pagination and lazy loading
   - Memory usage optimization needed

## Action Items

1. **Immediate Actions**:
   - Complete OpenAI Agents SDK integration
   - Implement structured response format
   - Enhance schema validation

2. **Short-term Actions**:
   - Address batch processing status issues
   - Implement error message localization
   - Optimize performance for large datasets

3. **Long-term Actions**:
   - Complete documentation updates
   - Implement comprehensive testing
   - Address remaining technical debt

## Issue Review Meetings

1. **Triage Meeting**: Weekly meeting to review and prioritize new issues
2. **Bug Bash**: Monthly session to find and document issues
3. **Technical Debt Review**: Bi-weekly review of technical debt items

## Reporting

Issue statistics are reported in weekly progress reports, including:

1. Number of issues opened/closed
2. Distribution of issues by category and priority
3. Progress on technical debt reduction
4. Key issues that require attention

## Tools and Integration

Issues are tracked using:

1. **GitHub Issues**: Primary issue tracking
2. **Pull Requests**: Linked to issues they resolve
3. **GitHub Projects**: For visual tracking of issues
4. **GitHub Actions**: For automated testing and verification

## Best Practices

1. **Clear Descriptions**: Write clear, detailed issue descriptions
2. **Reproducible Steps**: Include steps to reproduce bugs
3. **One Issue Per Report**: Don't combine multiple issues
4. **Link Related Issues**: Cross-reference related issues
5. **Update Status**: Keep issue status up to date
6. **Verify Fixes**: Thoroughly test and verify fixes
7. **Document Solutions**: Document the solution approach 