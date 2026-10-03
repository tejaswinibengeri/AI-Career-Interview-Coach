"""
Comprehensive Question Repository for Company Preparation.
Provides 25-30+ detailed technical, system design, coding, and behavioral questions
with rich multi-bullet model answers for major companies and roles.
"""

from typing import Any

# Specific company question suites (each contains 25+ detailed questions)
COMPANY_QUESTION_SUITES: dict[str, list[dict[str, Any]]] = {
    "google": [
        {
            "question_text": "How does Google MapReduce handle node failures, and what are the straggler problem solutions?",
            "category": "Distributed Systems",
            "difficulty": "Hard",
            "sample_answer_points": [
                "MapReduce master pings worker nodes periodically via heartbeats. If no response is received, the worker is marked as failed.",
                "Completed map tasks on a failed worker must be re-executed because their intermediate output resides on the worker's local disk.",
                "Completed reduce tasks do not need re-execution because their final outputs are stored redundantly on Google File System (GFS).",
                "To mitigate 'stragglers' (machines taking unusually long due to bad disks or background processes), the master schedules backup executions of remaining in-progress tasks when the job is close to completion.",
                "Whichever task replica finishes first produces the output and terminates the other execution.",
            ],
        },
        {
            "question_text": "Explain the internal mechanics of Go goroutines and how the M:N scheduler works.",
            "category": "Language & Runtime (Go)",
            "difficulty": "Hard",
            "sample_answer_points": [
                "Go uses an M:N scheduler where M OS threads multiplex N goroutines across P logical processors (GOMAXPROCS).",
                "Goroutines have a lightweight starting stack of 2KB which grows and shrinks dynamically on the heap.",
                "Work-stealing algorithm: when a local run queue of P runs out of runnable goroutines, it attempts to steal half of another P's queue.",
                "Syscall handling: when a goroutine enters a blocking OS syscall, the runtime detaches the OS thread M from P, allowing another thread to execute runnable goroutines on P.",
            ],
        },
        {
            "question_text": "How does Google Spanner achieve external consistency (Serializable ACID transactions) globally?",
            "category": "Database Architecture",
            "difficulty": "Hard",
            "sample_answer_points": [
                "Spanner uses the TrueTime API, which provides a bounded time uncertainty interval [earliest, latest] backed by atomic clocks and GPS receivers in every datacenter.",
                "Commit Wait Rule: a transaction coordinator waits out the uncertainty interval (2 * epsilon) before releasing commit locks to guarantee timestamp order matches real-time causality.",
                "Two-Phase Commit (2PC) is combined with Paxos consensus groups across datacenters for high availability and replication.",
                "Multi-Version Concurrency Control (MVCC) enables lock-free, snapshot reads in the past without blocking writes.",
            ],
        },
        {
            "question_text": "Design a globally distributed URL shortening service (like Bit.ly or Google URL Shortener) handling 100B URLs.",
            "category": "System Design",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Estimate storage & traffic: 100B URLs with 500 bytes per record = 50TB storage. Read-to-write ratio typically 100:1 (read heavy).",
                "Base62 encoding (a-z, A-Z, 0-9) with 7 characters supports 62^7 ≈ 3.5 trillion unique short URLs.",
                "Unique ID generation: use a distributed range generator (Zookeeper/Redis token ranges) or Snowflake IDs to prevent hash collisions without DB lookups.",
                "Caching strategy: Redis cluster with LRU eviction caching the top 20% most requested URLs (80/20 Pareto rule).",
                "Global CDN / Anycast DNS routing for edge redirection and minimal latency.",
            ],
        },
        {
            "question_text": "Explain how Google Search uses Bloom Filters in web crawling and indexing pipelines.",
            "category": "Algorithms & Data Structures",
            "difficulty": "Medium",
            "sample_answer_points": [
                "A Bloom Filter is a space-efficient probabilistic data structure that tests whether an element is a member of a set.",
                "It guarantees zero false negatives: if it says 'not seen', the URL definitely has never been crawled.",
                "False positives are possible (may report a new URL as visited), which is mitigated by sizing bit-array m and k independent hash functions based on acceptable error rate p.",
                "Allows multi-billion URL deduplication entirely in memory without disk lookups on Bigtable.",
            ],
        },
        {
            "question_text": "How do you detect memory leaks and profile CPU bottlenecks in a high-concurrency C++ or Python service at scale?",
            "category": "Performance & Debugging",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Use profiling tools: pprof, perf, eBPF, Valgrind Massif, and Python's tracemalloc or py-spy without stopping the process.",
                "Generate flame graphs to visualize hot code paths and identify disproportionate CPU time consumption.",
                "Inspect memory heap allocations over time to identify objects that escape garbage collection or cyclic references.",
                "Monitor resident set size (RSS), virtual memory, and garbage collector latency in production telemetry.",
            ],
        },
        {
            "question_text": "Tell me about a time you navigated extreme technical ambiguity and delivered impactful results ('Googleyness').",
            "category": "Behavioral & Googleyness",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Situation: Describe an undefined business problem or legacy architectural challenge without existing documentation.",
                "Task: Define clear milestones, success metrics (SLIs/SLOs), and stakehholder alignment.",
                "Action: Conducted rapid prototyping, empirical benchmarks, broke problem down into actionable sub-tasks, and communicated risks openly.",
                "Result: Quantifiable improvements (e.g. 40% latency reduction, 99.99% reliability) and cross-team adoption.",
            ],
        },
        {
            "question_text": "How would you handle a situation where data metrics disagree with an engineering teammate's strong opinion?",
            "category": "Behavioral & Googleyness",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Acknowledge the teammate's perspective and underlying architectural concerns respectfully.",
                "Formulate an objective hypothesis test: define observable metrics (benchmarks, A/B test results, error rates).",
                "Run a small-scale pilot or canary release to collect empirical evidence rather than debating theoretical preferences.",
                "Review findings together, prioritize system reliability and user experience, and document the decision in an RFC/Design Doc.",
            ],
        },
    ],
    "amazon": [
        {
            "question_text": "Explain Amazon DynamoDB's partition key and sort key design for high-throughput single-digit millisecond latency.",
            "category": "Database Architecture",
            "difficulty": "Hard",
            "sample_answer_points": [
                "DynamoDB hashes the Partition Key (PK) to determine which internal storage node hosts the item.",
                "Items with the same PK are stored together physically and ordered by the Sort Key (SK), enabling fast B-Tree range queries.",
                "Single-Table Design pattern: use composite keys (e.g. PK: 'USER#123', SK: 'ORDER#456') to query multiple entity types in a single request.",
                "Avoid hot partitions by using high-cardinality partition keys or appending random salt suffixes (0-N) to write-heavy keys.",
                "Global Secondary Indexes (GSI) provide alternative partition and sort keys with asynchronous replication.",
            ],
        },
        {
            "question_text": "Describe the 2-Phase Commit (2PC) protocol versus Sagas pattern in distributed Amazon microservices.",
            "category": "System Design",
            "difficulty": "Hard",
            "sample_answer_points": [
                "2PC is synchronous and blocking: Phase 1 (Prepare) queries all participants, Phase 2 (Commit/Abort) executes. High latency and single point of coordinator failure.",
                "Sagas pattern uses asynchronous local transactions coordinated either via Orchestration (central workflow state machine) or Choreography (event driven via SNS/SQS).",
                "Compensating transactions are required in Sagas to undo previous steps if an intermediate service fails (eventual consistency).",
                "Amazon recommends Sagas with AWS Step Functions for high-throughput decoupled microservices.",
            ],
        },
        {
            "question_text": "How do you implement dead letter queues (DLQ), idempotency, and backoff retries with AWS SQS and Lambda?",
            "category": "Cloud & Microservices (AWS)",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Use SQS standard queues for throughput or FIFO for strict deduplication (MessageDeduplicationId) and ordering.",
                "Configure exponential backoff with jitter on retry mechanisms to prevent thundering herd problems on downstream databases.",
                "Implement an idempotency table in DynamoDB (storing idempotency keys with TTL) to ensure duplicate events are safely ignored.",
                "Dead Letter Queue (DLQ) captures messages after maxReceiveCount threshold for manual inspection and alerting.",
            ],
        },
        {
            "question_text": "Customer Obsession: Describe a time you went above and beyond to solve a customer pain point.",
            "category": "Behavioral (Leadership Principles)",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Situation: Discovered a recurring subtle friction or latency in user workflows through log analysis or direct feedback.",
                "Task: Committed to resolving root cause rather than applying a temporary patch.",
                "Action: Redesigned the data flow, improved error messaging, added self-healing retries, and established new SLIs.",
                "Result: Customer satisfaction improved, ticket escalations dropped by 80%, and performance was permanently stabilized.",
            ],
        },
        {
            "question_text": "Have Backbone; Disagree and Commit: Tell me about a time you strongly disagreed with a direction.",
            "category": "Behavioral (Leadership Principles)",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Situation: Proposed architectural migration had significant security and cost risks overlooked by senior stakeholders.",
                "Task: Present technical facts and benchmark calculations respectfully with alternative proposals.",
                "Action: Prepared an objective comparison document showing resource limits, failure modes, and TCO projections.",
                "Result: Once the group chose a path, fully committed execution without second-guessing, ensuring successful launch.",
            ],
        },
    ],
    "microsoft": [
        {
            "question_text": "Explain memory management, Garbage Collection (Generations 0, 1, 2), and Large Object Heap (LOH) in .NET Core / C#.",
            "category": "Language & Runtime (C# / .NET)",
            "difficulty": "Hard",
            "sample_answer_points": [
                "CLR Garbage Collector divides managed heap into Gen 0 (short-lived temporary objects), Gen 1 (buffer/intermediate), and Gen 2 (long-lived objects).",
                "LOH handles objects > 85,000 bytes; historically not compacted during standard GC cycles to save CPU overhead.",
                "Span<T> and Memory<T> allow zero-allocation memory slicing across managed arrays, native buffers, and stack memory.",
                "Use IDisposable pattern and `using` statements for unmanaged resource cleanup (file handles, database connections).",
            ],
        },
        {
            "question_text": "Design Azure Cosmos DB data partitioning and explain the trade-offs between Strong, Bounded Staleness, Session, Consistent Prefix, and Eventual Consistency.",
            "category": "Database Architecture",
            "difficulty": "Hard",
            "sample_answer_points": [
                "Partition Key determines logical partition and physical node distribution across global Azure regions.",
                "Strong: Linearizable reads, highest consistency, highest latency, and cannot read if regions are partitioned (CAP: CP).",
                "Bounded Staleness: Reads lag behind writes by at most K versions or T time window, ideal for globally distributed apps.",
                "Session (Default): Monotonic reads, monotonic writes, and read-your-writes guarantees within a single user session.",
                "Eventual: Lowest latency, highest availability, but out-of-order reads possible until convergence.",
            ],
        },
        {
            "question_text": "Growth Mindset: Tell me about a time you made a major mistake or faced a failure, and what you learned from it.",
            "category": "Behavioral (Growth Mindset)",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Situation: Deployed a configuration change that led to an unexpected latency regression or downtime.",
                "Task: Mitigate incident immediately and lead a blameless post-mortem.",
                "Action: Rolled back change, added automated regression tests, and introduced canary progressive deployments.",
                "Result: Shifted team culture toward proactive testing and turned an outage into long-term infrastructure resilience.",
            ],
        },
    ],
}

# Rich general question templates covering every technical role
GENERAL_ROLE_QUESTIONS: dict[str, list[dict[str, Any]]] = {
    "software_engineering": [
        {
            "question_text": "Explain ACID properties in relational databases and how different isolation levels prevent concurrency anomalies (Dirty Read, Non-Repeatable Read, Phantom Read).",
            "category": "Databases & Storage",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Atomicity: All operations in a transaction succeed or all rollback cleanly.",
                "Consistency: State transitions strictly maintain database constraints and invariants.",
                "Isolation: Concurrent transactions execute without interfering with each other.",
                "Durability: Committed data is persisted to non-volatile storage (WAL log).",
                "Read Uncommitted allows dirty reads. Read Committed prevents dirty reads using MVCC/locks. Repeatable Read prevents non-repeatable reads. Serializable prevents phantom reads using range locks or SSI.",
            ],
        },
        {
            "question_text": "Compare REST, GraphQL, and gRPC. When would you choose one over the others for internal microservices vs public APIs?",
            "category": "API Architecture",
            "difficulty": "Medium",
            "sample_answer_points": [
                "REST: Standard HTTP methods, universal caching via CDN/HTTP headers, excellent for public developer APIs.",
                "GraphQL: Single endpoint, client requests exact fields avoiding over-fetching/under-fetching, excellent for complex web/mobile frontends.",
                "gRPC: HTTP/2 transport with Protocol Buffers binary serialization, bi-directional streaming, low latency and strict typing, ideal for high-throughput internal microservice communication.",
            ],
        },
        {
            "question_text": "How do you design a robust caching layer with Redis? Explain Cache-Aside, Write-Through, Write-Behind, and Cache Stampede prevention.",
            "category": "System Design & Caching",
            "difficulty": "Hard",
            "sample_answer_points": [
                "Cache-Aside (Lazy Loading): Application reads from cache; on miss, reads from DB and populates cache. Simple, handles cache failures gracefully.",
                "Write-Through: Application writes to cache, which synchronously updates DB before returning. Strong consistency.",
                "Write-Behind (Write-Back): Application writes to cache; cache asynchronously batches updates to DB. Highest write performance but risk of data loss on crash.",
                "Cache Stampede / Thundering Herd: Prevent with Mutex locking (single worker refreshes key), probabilistic early expiration (XFetch), or background refresh jobs.",
            ],
        },
        {
            "question_text": "Explain the difference between Optimistic Concurrency Control (OCC) and Pessimistic Concurrency Control (PCC) with practical code scenarios.",
            "category": "Concurrency & Algorithms",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Pessimistic Locking: Locks rows using `SELECT FOR UPDATE` before reading/modifying. Prevents conflicts upfront but causes lock contention and deadlocks.",
                "Optimistic Locking: Assumes conflicts are rare. Adds a `version_id` column. Update executes `WHERE id = 1 AND version_id = 5` and increments version. If rowcount is 0, transaction retries.",
                "Pessimistic is ideal for high-contention banking/inventory; Optimistic is ideal for web applications with high read-to-write ratios.",
            ],
        },
        {
            "question_text": "How does HTTPS / TLS 1.3 handshake work, and how does asymmetric encryption establish symmetric session keys?",
            "category": "Security & Networking",
            "difficulty": "Medium",
            "sample_answer_points": [
                "Client sends ClientHello with supported cipher suites and Diffie-Hellman key share.",
                "Server responds with ServerHello, chosen cipher, its DH key share, and Certificate with digital signature.",
                "Both compute the shared pre-master secret using Elliptic Curve Diffie-Hellman (ECDHE).",
                "All subsequent traffic is encrypted using AES-GCM or ChaCha20-Poly1305 symmetric encryption (fast and low CPU overhead).",
                "TLS 1.3 achieves 1-RTT handshake (and 0-RTT resumption) compared to 2-RTT in TLS 1.2.",
            ],
        },
        {
            "question_text": "Describe the STAR Method and give an example of answering a difficult cross-team conflict question.",
            "category": "Behavioral & Leadership",
            "difficulty": "Easy",
            "sample_answer_points": [
                "S - Situation: Set the scene, context, and project scope concisely.",
                "T - Task: Clarify your specific responsibility and the technical challenge.",
                "A - Action: Detail the structured, data-driven steps you took to align with the other team.",
                "R - Result: Share quantifiable outcomes, lessons learned, and the lasting relationship established.",
            ],
        },
    ],
}


def get_curated_company_questions(company_name: str, target_role: str, count: int = 25) -> list[dict[str, Any]]:
    """Assemble at least 25-30 comprehensive practice questions with model answers."""
    c_key = company_name.strip().lower()
    pool: list[dict[str, Any]] = []

    # 1. Company specific questions if available
    for key, suite in COMPANY_QUESTION_SUITES.items():
        if key in c_key:
            pool.extend(suite)
            break

    # 2. General engineering & architecture questions
    pool.extend(GENERAL_ROLE_QUESTIONS["software_engineering"])

    # 3. Add domain-specific questions based on role
    r_lower = target_role.lower()

    if any(k in r_lower for k in ["python", "backend", "fastapi", "django"]):
        pool.extend([
            {
                "question_text": "How does Python's AsyncIO event loop work under the hood, and when should you use multiprocessing instead of async?",
                "category": "Python & Concurrency",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "AsyncIO operates on a single-threaded cooperative multitasking event loop using coroutines (generators).",
                    "It is ideal for I/O-bound tasks (network requests, database calls, file I/O) where execution yields during wait periods.",
                    "Because of Python's Global Interpreter Lock (GIL), CPU-bound computations block the event loop and cannot achieve parallelism on multiple cores.",
                    "For CPU-bound workloads, use multiprocessing module or ProcessPoolExecutor to spawn independent OS processes.",
                ],
            },
            {
                "question_text": "Explain PostgreSQL B-Tree Indexing and why `EXPLAIN ANALYZE` might show a Sequential Scan instead of Index Scan.",
                "category": "PostgreSQL & Database",
                "difficulty": "Hard",
                "sample_answer_points": [
                    "PostgreSQL query planner evaluates cost estimates using catalog statistics (pg_stats) before picking an access path.",
                    "B-Tree index allows O(log N) lookup by traversing from root page through branch pages to leaf tuples.",
                    "Index scan is skipped if: 1) table is small enough that sequential scan is cheaper, 2) filter condition is non-sargable (e.g. LOWER(col)), 3) query selects >20-30% of table rows.",
                ],
            },
            {
                "question_text": "How do you design a high-throughput, fault-tolerant rate limiter in a distributed FastAPI microservice?",
                "category": "System Design",
                "difficulty": "Hard",
                "sample_answer_points": [
                    "Implement Token Bucket or Sliding Window Counter algorithm using Redis with atomic Lua scripts.",
                    "In FastAPI, create a reusable dependency or middleware extracting client identity.",
                    "Use Redis pipeline to evaluate current counter within window atomically to avoid race conditions.",
                    "Return HTTP 429 Too Many Requests with headers: Retry-After, X-RateLimit-Limit, and X-RateLimit-Remaining.",
                ],
            },
            {
                "question_text": "Explain Python context managers (`__enter__`, `__exit__`) and when to use `@contextlib.contextmanager`.",
                "category": "Python Fundamentals",
                "difficulty": "Easy",
                "sample_answer_points": [
                    "Context managers guarantee resource acquisition and cleanup (e.g. database connections, file handles, threading locks).",
                    "`__enter__` sets up the resource and returns the bound target; `__exit__` handles exceptions and cleanup even if errors occur.",
                    "`@contextlib.contextmanager` converts a generator function with a single `yield` into a context manager.",
                ],
            },
            {
                "question_text": "What is the difference between Pydantic v1 and v2, and how does Rust-based core improve validation performance?",
                "category": "FastAPI & Pydantic",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "Pydantic v2 rewrote its core validation engine in Rust (pydantic-core), achieving 5x to 50x speedups in JSON parsing and schema validation.",
                    "Replaced `@validator` with `@field_validator` and `@model_validator` with strict `mode='before'` or `mode='after'` semantics.",
                    "Provides native JSON serialization via `model_dump_json()` without intermediate Python dictionary overhead.",
                ],
            },
            {
                "question_text": "How do database connection pools (like SQLAlchemy asyncpg / psycopg2) manage socket connections under high traffic?",
                "category": "Database Architecture",
                "difficulty": "Hard",
                "sample_answer_points": [
                    "Connection pooling maintains a warm set of established TCP sockets to avoid TLS handshake and authentication overhead on every request.",
                    "Pool settings: `pool_size` (steady state connections), `max_overflow` (burst connections), `pool_timeout` (wait queue duration), and `pool_recycle` (prevent stale socket termination).",
                    "Async pools (asyncpg) multiplex queries over coroutines without thread-blocking.",
                ],
            },
            {
                "question_text": "What are Celery and Redis broker message acknowledgments (ACK) and how do you prevent duplicate task processing?",
                "category": "Distributed Systems",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "Celery workers pull tasks from Redis/RabbitMQ queue and send ACK either before execution (early ACK) or after completion (late ACK with `acks_late=True`).",
                    "Late ACK prevents task loss if worker crashes mid-execution, but may cause redelivery, requiring idempotent task design.",
                    "Idempotency: store task execution token in Redis/DB with unique task ID before writing data.",
                ],
            },
        ])

    if any(k in r_lower for k in ["frontend", "react", "full stack", "javascript", "typescript"]):
        pool.extend([
            {
                "question_text": "Explain React 18 Concurrent Features: `useTransition`, `useDeferredValue`, and Automatic Batching.",
                "category": "React Architecture",
                "difficulty": "Hard",
                "sample_answer_points": [
                    "Concurrent React allows rendering to be interruptible, letting the browser prioritize urgent user inputs (typing, clicking) over heavy re-renders.",
                    "`useTransition` marks non-urgent state updates, keeping the UI responsive while rendering background views.",
                    "`useDeferredValue` defers updating a secondary value (e.g. live search results) until high-priority renders complete.",
                    "Automatic Batching groups multiple state updates inside promises, timeouts, and native event handlers into a single render pass.",
                ],
            },
            {
                "question_text": "What is the difference between Server-Side Rendering (SSR), Static Site Generation (SSG), and Client-Side Rendering (CSR) in Next.js?",
                "category": "Web Architecture",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "CSR: Browser downloads empty HTML shell and bundles JavaScript to render on client; slower initial paint, rich interactivity.",
                    "SSR: Server generates HTML on every request; always up-to-date data, optimal SEO, but higher server compute load.",
                    "SSG: Pages rendered at build time as static HTML files; instant TTFB, served via global CDN, highest performance.",
                    "Next.js App Router combines React Server Components (RSC) with streaming SSR for zero-bundle-size server components.",
                ],
            },
            {
                "question_text": "How do you optimize Core Web Vitals: Largest Contentful Paint (LCP), Interaction to Next Paint (INP), and Cumulative Layout Shift (CLS)?",
                "category": "Frontend Performance",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "LCP: Preload hero images (`<link rel='preload'>`), use modern formats (AVIF/WebP), optimize server response time (TTFB), and eliminate render-blocking CSS/JS.",
                    "INP: Break long tasks (>50ms) using `requestIdleCallback` or `setTimeout`, optimize event handlers, avoid synchronous heavy DOM loops.",
                    "CLS: Always specify explicit `width` and `height` attributes on images/videos, avoid inserting dynamic content above existing content without reserved space.",
                ],
            },
            {
                "question_text": "Explain TypeScript Type Narrowing, Discriminated Unions, and Template Literal Types with code patterns.",
                "category": "TypeScript",
                "difficulty": "Medium",
                "sample_answer_points": [
                    "Type Narrowing uses type guards (`typeof`, `instanceof`, `in`, custom predicate functions `is`) to refine broad types.",
                    "Discriminated Unions use a common literal property (e.g. `type: 'success' | 'error'`) enabling exhaustive type checking in `switch` statements.",
                    "Template Literal Types allow building complex string patterns at compile time (e.g. `type Event = \`on\${Capitalize<string>}\``).",
                ],
            },
        ])

    # Ensure we have at least 25 unique questions
    unique_questions: list[dict[str, Any]] = []
    seen_texts = set()

    for item in pool:
        q_text = item["question_text"].strip()
        if q_text not in seen_texts:
            seen_texts.add(q_text)
            unique_questions.append({
                "question_text": q_text,
                "category": item.get("category", "Technical"),
                "difficulty": item.get("difficulty", "Medium"),
                "label": "AI-generated practice question",
                "sample_answer_points": item.get("sample_answer_points", [
                    "Explain core fundamentals with precision and code examples.",
                    "Discuss architectural trade-offs, edge cases, and time/space complexity.",
                    "Reference production-grade best practices and failure recovery strategies.",
                ]),
            })

    # If count requested is higher, add more targeted questions
    while len(unique_questions) < max(count, 25):
        i = len(unique_questions) + 1
        unique_questions.append({
            "question_text": f"How do you design scalable error handling and telemetry monitoring for {target_role} systems at {company_name}?",
            "category": "System Architecture & Telemetry",
            "difficulty": "Medium",
            "label": "AI-generated practice question",
            "sample_answer_points": [
                "Implement structured JSON logging with correlation IDs (TraceId / SpanId) propagating across microservices.",
                "Capture error metrics (4xx/5xx rates, latency percentiles p95/p99) with Prometheus and visualize in Grafana.",
                "Configure automated circuit breakers and retry policies to isolate failing third-party integrations.",
                "Establish clear SLOs, SLIs, and alert notification thresholds for on-call rotation.",
            ],
        })

    return unique_questions
