# Architecture

See the root [README](../README.md), Section 3, for the agreed architecture.

```text
Frontend (HTML/CSS/JS)
        |
      FastAPI
        |
 NLP condition interpreter
        |
   RAG retrieval
        |
  TM machine builder
        |
 Rule parser + validator
        |
  TM execution engine
        |
 ACCEPT / REJECT + trace
```

The TM execution engine is the only component that determines acceptance.
RAG provides supporting construction knowledge; it does not decide the result.
