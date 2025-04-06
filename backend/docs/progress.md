graph TD
    subgraph Phase 1: Foundation & Basic Tagging
        A[Define Standardization Schemas (JSONs)] --> B(Implement Tag Storage);
        A --> C(Develop Basic Tagging Rules - Point Type, Basic Resource);
        B --> D(Develop Basic Validation UI - View Tags);
        C --> E(Enhance Mapping Logic - Use Basic Tags);
    end

    subgraph Phase 2: Advanced Tagging & Grouping
        F[Implement Advanced Tagging - Resource, Sub-Resource, Phenomenon, Quantity, Unit] --> G(Implement Intelligent Grouping Module);
        F --> H(Build Comprehensive Tag Management UI - Edit/Validate Tags);
        G --> H;
        I[Develop Automated Testing Framework] --> H;
    end

    subgraph Phase 3: AI Integration & Optimization
        J[Integrate AI/ML for Tag Prediction/Suggestion] --> K(Refine Workflow - Agent-like structure);
        L[Implement Context-Aware Mapping] --> K;
        M[Performance Optimization] --> K;
        H --> J;  // UI feeds validation data back to AI
    end

    Phase1 --> Phase2;
    Phase2 --> Phase3;

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#f9f,stroke:#333,stroke-width:2px

    style F fill:#ccf,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
    style H fill:#ccf,stroke:#333,stroke-width:2px
    style I fill:#ccf,stroke:#333,stroke-width:2px

    style J fill:#9cf,stroke:#333,stroke-width:2px
    style K fill:#9cf,stroke:#333,stroke-width:2px
    style L fill:#9cf,stroke:#333,stroke-width:2px
    style M fill:#9cf,stroke:#333,stroke-width:2px
