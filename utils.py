from vectorDocumentStore import VectorDocumentStore
from app import logger

def add_sample_documents(doc_store: VectorDocumentStore):
    """Add some sample documents for demonstration"""
   
    finance_docs = [
        {
            "title": "Quarterly Financial Report Q3 2023",
            "content": """
            # Q3 2023 Financial Report
            
            ## Executive Summary
            The third quarter of 2023 showed a 12% increase in revenue compared to Q2, with total revenue reaching $5.2 million.
            
            ## Key Financial Metrics
            - Revenue: $5.2M (↑12% QoQ)
            - Operating Expenses: $3.1M (↑5% QoQ)
            - Net Profit: $1.4M (↑24% QoQ)
            - Cash Reserves: $8.7M
            
            ## Department Breakdown
            - Sales: $3.2M (↑15%)
            - Services: $1.5M (↑8%)
            - Licensing: $0.5M (↑5%)
            
            ## Projections for Q4
            We anticipate Q4 revenue to reach $5.8M with continued growth in the Sales department.
            """
        },
        {
            "title": "2024 Budget Planning Guidelines",
            "content": """
            # Budget Planning Guidelines for 2024
            
            ## Overview
            This document outlines the process and requirements for departmental budget submissions for fiscal year 2024.
            
            ## Timeline
            - Budget templates distributed: October 1, 2023
            - Initial submissions due: October 31, 2023
            - Review meetings: November 7-18, 2023
            - Final approvals: December 15, 2023
            
            ## Budget Constraints
            - Total budget increase capped at 8% over 2023
            - New headcount requests limited to critical roles only
            - Capital expenditures require ROI analysis for amounts over $25,000
            
            ## Required Documentation
            1. Completed budget template
            2. Headcount justification form (if applicable)
            3. Capital expenditure requests with ROI analysis
            4. Revenue projections (for revenue-generating departments)
            
            ## Approval Process
            All budgets require approval from the department head, finance director, and appropriate VP.
            """
        }
    ]
    
    engineering_docs = [
        {
            "title": "System Architecture Overview",
            "content": """
            # System Architecture Overview
            
            ## Core Components
            Our system consists of the following key components:
            
            1. **Frontend Layer**
               - React.js based SPA
               - Responsive design using Material-UI
               - Client-side state management with Redux
            
            2. **API Gateway**
               - AWS API Gateway
               - Authentication and request routing
               - Rate limiting and caching
            
            3. **Microservices**
               - User Service (Node.js)
               - Product Service (Python/Django)
               - Order Service (Java/Spring Boot)
               - Notification Service (Go)
            
            4. **Data Layer**
               - Primary database: PostgreSQL
               - Caching: Redis
               - Search: Elasticsearch
               - Data warehouse: Snowflake
            
            5. **Infrastructure**
               - AWS Cloud (primary)
               - Kubernetes for container orchestration
               - CI/CD through GitHub Actions
               - Terraform for infrastructure as code
            
            ## Communication Patterns
            - Synchronous: REST APIs, gRPC
            - Asynchronous: Kafka for event streaming
            
            ## Security Measures
            - JWT-based authentication
            - HTTPS everywhere
            - WAF for API endpoints
            - Regular security audits
            """
        },
        {
            "title": "Development Workflow Guidelines",
            "content": """
            # Development Workflow Guidelines
            
            ## Git Workflow
            
            We follow a modified Git Flow with the following branches:
            
            - `main`: Production code
            - `develop`: Integration branch for features
            - `feature/*`: New features
            - `bugfix/*`: Bug fixes
            - `release/*`: Release candidates
            - `hotfix/*`: Production fixes
            
            ## Pull Request Process
            
            1. Create a feature/bugfix branch from `develop`
            2. Implement your changes with appropriate tests
            3. Open a PR to `develop` with:
               - Clear description
               - Linked issues
               - Tests passing
               - Coverage requirements met
            4. Obtain at least two code reviews
            5. Address review comments
            6. Merge when approved and CI passes
            
            ## Coding Standards
            
            - Follow language-specific style guides:
              - JavaScript: Airbnb style guide
              - Python: PEP 8
              - Java: Google Java Style
            - Document public APIs
            - Write unit tests for all new code
            - Maintain minimum 80% code coverage
            
            ## Deployment Process
            
            1. Changes merged to `develop` are auto-deployed to the staging environment
            2. QA performs testing in staging
            3. Release branch created for production deployment
            4. Final testing on pre-production
            5. Release manager approves and merges to `main`
            6. CI/CD pipeline deploys to production
            """
        }
    ]
    
    for doc in finance_docs:
        doc_store.add_document("finance", doc["title"], doc["content"])
    
    for doc in engineering_docs:
        doc_store.add_document("engineering", doc["title"], doc["content"])
    
    logger.info("Added sample documents")
