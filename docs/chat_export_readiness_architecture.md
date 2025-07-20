# Chat-Based Export Readiness Architecture

## System Flow Diagram

```mermaid
graph TD
    A[User Input in Chat] --> B{Export Analysis Request?}
    
    B -->|No| C[Normal Chat Flow]
    B -->|Yes| D{Target Country Specified?}
    
    D -->|No| E[Show Country Selection Menu]
    D -->|Yes| F[Extract Business Profile from Memory Bot]
    
    C --> G[get_bot_response]
    G --> H[Gemini AI Business Profiling]
    H --> I[Extract Business Data]
    I --> J[Update Memory Bot]
    J --> K[Display Chat Response]
    
    E --> L[Wait for Country Selection]
    L --> M[User Specifies Country]
    M --> F
    
    F --> N[perform_chat_based_export_analysis]
    N --> O[Format Export Readiness Prompt]
    O --> P[Send to Gemini 2.0 Flash]
    P --> Q[Parse AI Response]
    Q --> R{JSON Format?}
    
    R -->|Yes| S[Format Structured Analysis]
    R -->|No| T[Format Raw Analysis]
    
    S --> U[Save Assessment to Memory Bot]
    T --> U
    U --> V[Display Formatted Results in Chat]
    
    V --> W[Assessment History Updated]
```

## Component Architecture

```mermaid
graph LR
    subgraph "Chat Interface"
        A[show_chat_interface]
        B[Chat Input Handler]
        C[Message Display]
    end
    
    subgraph "Export Analysis Engine"
        D[detect_export_analysis_request]
        E[perform_chat_based_export_analysis]
        F[Country Mapping System]
    end
    
    subgraph "AI Integration"
        G[Gemini 2.0 Flash API]
        H[EXPORT_READINESS_PROMPT]
        I[Response Parser]
    end
    
    subgraph "Data Management"
        J[Memory Bot]
        K[Assessment History]
        L[Business Profile Data]
    end
    
    A --> B
    B --> D
    D --> E
    E --> F
    E --> H
    H --> G
    G --> I
    I --> J
    J --> K
    J --> L
    E --> C
```

## Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Chat Interface
    participant D as Detection Engine
    participant A as Analysis Engine
    participant G as Gemini AI
    participant M as Memory Bot
    
    U->>C: Types "cek kesiapan ekspor Malaysia"
    C->>D: detect_export_analysis_request()
    D->>D: Parse keywords & extract country
    D-->>C: analysis_requested=True, target_country="Malaysia"
    
    C->>A: perform_chat_based_export_analysis()
    A->>M: Get business profile data
    M-->>A: Company, product, capacity data
    
    A->>A: Format prompt with business data
    A->>G: Send EXPORT_READINESS_PROMPT
    G-->>A: AI analysis response (JSON)
    
    A->>A: Parse & format for chat display
    A->>M: Save assessment to history
    A-->>C: Formatted analysis result
    
    C->>U: Display comprehensive export analysis
```

## Supported Countries & Difficulty Levels

```mermaid
graph TB
    subgraph "Export Target Countries"
        A[🇲🇾 Malaysia<br/>Difficulty: Low]
        B[🇸🇬 Singapore<br/>Difficulty: Medium]
        C[🇦🇺 Australia<br/>Difficulty: Medium]
        D[🇰🇷 South Korea<br/>Difficulty: Medium]
        E[🇺🇸 United States<br/>Difficulty: High]
        F[🇪🇺 European Union<br/>Difficulty: High]
        G[🇯🇵 Japan<br/>Difficulty: High]
        H[🇨🇳 China<br/>Difficulty: High]
    end
    
    subgraph "Analysis Categories"
        I[Regulatory Compliance<br/>25%]
        J[Market Viability<br/>25%]
        K[Documentation Readiness<br/>25%]
        L[Competitive Positioning<br/>25%]
    end
    
    A --> I
    B --> I
    C --> I
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    
    I --> M[Overall Score 0-100]
    J --> M
    K --> M
    L --> M
```

## Memory Bot Integration

```mermaid
graph TD
    subgraph "Memory Bot Data Structure"
        A[Business Profile]
        B[Export Readiness]
        C[Assessment History]
    end
    
    subgraph "Business Profile"
        D[Company Name]
        E[Product Details]
        F[Production Capacity]
        G[Location]
        H[Category]
    end
    
    subgraph "Export Readiness"
        I[Target Countries]
        J[Export Experience]
        K[Current Markets]
        L[Export Goals]
        M[Budget & Timeline]
    end
    
    subgraph "Assessment History"
        N[Country Assessed]
        O[Score Achieved]
        P[Timestamp]
        Q[Status]
        R[Product Info]
    end
    
    A --> D
    A --> E
    A --> F
    A --> G
    A --> H
    
    B --> I
    B --> J
    B --> K
    B --> L
    B --> M
    
    C --> N
    C --> O
    C --> P
    C --> Q
    C --> R
```

## User Interaction Patterns

```mermaid
journey
    title Export Readiness Assessment Journey
    section Business Profiling
      Start Chat: 5: User
      Share Company Info: 4: User
      Provide Product Details: 4: User
      Memory Bot Updates: 5: System
    
    section Export Analysis Request
      Request Analysis: 5: User
      Select Target Country: 4: User
      Trigger AI Analysis: 5: System
      
    section Analysis Results
      Receive Comprehensive Report: 5: User
      Review Action Items: 4: User
      Check Timeline: 4: User
      Save to History: 5: System
      
    section Follow-up
      Ask Questions: 4: User
      Request Different Country: 3: User
      Download Report: 4: User
```

## Keywords & Triggers

```mermaid
mindmap
  root((Export Analysis Triggers))
    Indonesian Keywords
      "cek kesiapan ekspor"
      "analisis ekspor"
      "siap ekspor"
      "kesiapan ekspor"
      "analisis kesiapan"
    English Keywords
      "export readiness"
      "ready to export"
      "export analysis"
    Country Keywords
      Amerika/US/USA
      Eropa/EU/Europe
      Jepang/Japan
      Singapura/Singapore
      Malaysia
      Australia
      Korea/South Korea
      China/Cina
```

---

## Technical Implementation

- **Framework**: Streamlit with Google Gemini AI
- **Language**: Python 3.13+
- **AI Model**: Gemini 2.0 Flash Experimental
- **Data Storage**: SQLite + Session State
- **Architecture**: Modular chat-based system

## Key Features

1. **Natural Language Processing** - Detects export analysis requests in conversation
2. **Contextual Analysis** - Uses existing business profile for personalized assessment
3. **Multi-Country Support** - 8 target countries with difficulty ratings
4. **Comprehensive Scoring** - 4 categories with 0-100 scoring system
5. **Memory Integration** - Automatic saving to assessment history
6. **Actionable Insights** - Specific steps, timelines, and recommendations