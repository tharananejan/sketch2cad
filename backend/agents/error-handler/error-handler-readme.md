# Error Handler Agent

**Purpose:** Bounded Self-Healing Loop Agent.

**Note:** Catches stack traces from execution failures. Uses a local RAG fix-pattern lookup index to issue corrections back to the Code Generator. Must observe a strict loop repetition limit failsafe before aborting and passing control back to the user.
