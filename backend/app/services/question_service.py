"""
Interview Question Bank Service.
Manages curated question repositories, seeding standard questions, user bookmarking,
and generating AI practice questions via Ollama (marked as 'AI-generated practice question').
"""

import asyncio
import json
import logging
import re
from typing import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai.ollama import OllamaProvider
from app.models.question import Question, SavedQuestion
from app.models.user import User
from app.schemas.question import (
    AIGeneratedQuestionsPayload,
    AIQuestionItemPayload,
    GenerateQuestionsRequest,
    QuestionResponse,
)

logger = logging.getLogger(__name__)

STANDARD_SEED_QUESTIONS = [
    # Technical
    {
        "question": "Explain the difference between a Process and a Thread in modern operating systems.",
        "category": "Technical",
        "difficulty": "Medium",
        "role": "Software Engineer",
        "tags": ["Operating Systems", "Concurrency", "System Architecture"],
        "source_type": "standard",
        "explanation": "A Process is an executing instance of an application with its own isolated memory space. A Thread is a lightweight subset of execution within a process that shares memory and resources with sibling threads.",
    },
    {
        "question": "What is Dependency Injection and why is it useful in software architecture?",
        "category": "Technical",
        "difficulty": "Medium",
        "role": "Software Engineer",
        "tags": ["Design Patterns", "Clean Code", "OOP"],
        "source_type": "standard",
        "explanation": "Dependency Injection (DI) is a design pattern where an object receives its dependencies from an external provider rather than creating them internally, enhancing testability and loose coupling.",
    },
    {
        "question": "How do distributed caches like Redis handle cache invalidation and cache penetration?",
        "category": "Technical",
        "difficulty": "Hard",
        "role": "Backend Engineer",
        "tags": ["Distributed Systems", "Caching", "Redis", "Scalability"],
        "source_type": "standard",
        "explanation": "Cache invalidation uses strategies like write-through, write-behind, and TTL-based eviction. Cache penetration is mitigated using Bloom filters to check key existence or caching null values with short expiration.",
    },
    {
        "question": "Explain the event loop in Node.js / JavaScript and how asynchronous operations are handled.",
        "category": "Technical",
        "difficulty": "Easy",
        "role": "Frontend Engineer",
        "tags": ["JavaScript", "Async", "Event Loop"],
        "source_type": "standard",
        "explanation": "The event loop is a single-threaded loop that monitors the Call Stack and Task Queues (Microtasks and Macrotasks). Microtasks (Promises) run before Macrotasks (setTimeout, setInterval).",
    },
    # Behavioral
    {
        "question": "Tell me about a time you had a technical disagreement with a teammate and how you resolved it.",
        "category": "Behavioral",
        "difficulty": "Medium",
        "role": "General",
        "tags": ["Soft Skills", "Conflict Resolution", "Collaboration"],
        "source_type": "standard",
        "explanation": "Use the STAR method (Situation, Task, Action, Result). Focus on objective criteria, benchmark testing, and reaching a constructive compromise based on engineering data.",
    },
    {
        "question": "Describe a situation where you had to meet a tight deadline and unexpected roadblocks occurred.",
        "category": "Behavioral",
        "difficulty": "Medium",
        "role": "General",
        "tags": ["Time Management", "Problem Solving", "Adaptability"],
        "source_type": "standard",
        "explanation": "Detail how you reprioritized critical path deliverables, communicated transparently with stakeholders, and delivered a high-quality MVP on schedule.",
    },
    {
        "question": "Tell me about an instance where a production system failed because of your code and how you handled the post-mortem.",
        "category": "Behavioral",
        "difficulty": "Hard",
        "role": "Software Engineer",
        "tags": ["Accountability", "Incident Response", "Blameless Post-Mortem"],
        "source_type": "standard",
        "explanation": "Demonstrate ownership, rapid mitigation/rollback, root cause analysis (5 Whys), and implementing automated guardrails to prevent recurrence.",
    },
    # DSA
    {
        "question": "How do you detect a cycle in a singly linked list efficiently?",
        "category": "DSA",
        "difficulty": "Easy",
        "role": "Software Engineer",
        "tags": ["Data Structures", "Algorithms", "Pointers"],
        "source_type": "standard",
        "explanation": "Use Floyd's Cycle-Finding Algorithm (Tortoise and Hare technique) using slow and fast pointers. If fast and slow pointers meet, a cycle exists. Time complexity O(N), space O(1).",
    },
    {
        "question": "Explain how Dijkstra's algorithm finds the shortest path in a weighted graph and its time complexity.",
        "category": "DSA",
        "difficulty": "Medium",
        "role": "Software Engineer",
        "tags": ["Graphs", "Shortest Path", "Greedy"],
        "source_type": "standard",
        "explanation": "Dijkstra uses a Min-Heap priority queue to greedily expand the nearest unvisited node, relaxing neighbor edge weights. Time complexity is O((V + E) log V) with a binary heap.",
    },
    {
        "question": "How would you design an LRU (Least Recently Used) Cache with O(1) get and put operations?",
        "category": "DSA",
        "difficulty": "Hard",
        "role": "Software Engineer",
        "tags": ["Data Structures", "Hash Map", "Doubly Linked List"],
        "source_type": "standard",
        "explanation": "Combine a Hash Map with a Doubly Linked List. The hash map maps keys to list nodes for O(1) lookup. The doubly linked list maintains access order; accessing a node moves it to head, evictions remove from tail.",
    },
    # SQL
    {
        "question": "What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN in SQL?",
        "category": "SQL",
        "difficulty": "Easy",
        "role": "Data Engineer",
        "tags": ["SQL", "Databases", "Queries"],
        "source_type": "standard",
        "explanation": "INNER JOIN returns matching rows from both tables. LEFT JOIN returns all rows from the left table and matched right rows. FULL OUTER JOIN returns all rows from both tables, filling missing values with NULL.",
    },
    {
        "question": "Explain indexing strategies: when should you use a Composite Index versus separate Single-Column Indexes?",
        "category": "SQL",
        "difficulty": "Medium",
        "role": "Backend Engineer",
        "tags": ["SQL", "Indexing", "Performance Optimization"],
        "source_type": "standard",
        "explanation": "A composite index (A, B) supports queries filtering on A or both (A, B) due to the leftmost prefix rule. Separate single-column indexes are used when columns are filtered independently across different queries.",
    },
    {
        "question": "How do Database Transaction Isolation Levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) prevent concurrency anomalies?",
        "category": "SQL",
        "difficulty": "Hard",
        "role": "Backend Engineer",
        "tags": ["Databases", "ACID", "Transactions", "Concurrency"],
        "source_type": "standard",
        "explanation": "Dirty reads are prevented by Read Committed. Non-repeatable reads are prevented by Repeatable Read using snapshot isolation. Phantom reads and write skew are prevented by Serializable isolation.",
    },
    # HR
    {
        "question": "Why do you want to work for our company and what uniquely qualifies you for this position?",
        "category": "HR",
        "difficulty": "Easy",
        "role": "General",
        "tags": ["Career Goals", "Motivation", "Culture Fit"],
        "source_type": "standard",
        "explanation": "Demonstrate knowledge of company mission, tech stack, and recent achievements. Relate your relevant background skills directly to how you can add immediate value.",
    },
    {
        "question": "Where do you see yourself professionally in the next 3 to 5 years?",
        "category": "HR",
        "difficulty": "Medium",
        "role": "General",
        "tags": ["Career Progression", "Ambition", "Growth"],
        "source_type": "standard",
        "explanation": "Articulate a trajectory showing continuous technical deepening, system architecture ownership, and mentoring junior engineers aligned with company milestones.",
    },
    # Coding
    {
        "question": "Write a function to check if a string is a valid palindrome, ignoring non-alphanumeric characters.",
        "category": "Coding",
        "difficulty": "Easy",
        "role": "Software Engineer",
        "tags": ["Coding", "Strings", "Two Pointers"],
        "source_type": "standard",
        "explanation": "Filter non-alphanumeric characters or use two pointers moving inwards, comparing characters in lowercase until left >= right.",
    },
    {
        "question": "Implement a function to find the maximum sum contiguous subarray in an integer array (Kadane's Algorithm).",
        "category": "Coding",
        "difficulty": "Medium",
        "role": "Software Engineer",
        "tags": ["Coding", "Arrays", "Dynamic Programming"],
        "source_type": "standard",
        "explanation": "Keep track of current_max = max(nums[i], current_max + nums[i]) and update global_max. Achieves O(N) time and O(1) auxiliary space.",
    },
    {
        "question": "Implement a function to serialize and deserialize a binary tree to and from a string representation.",
        "category": "Coding",
        "difficulty": "Hard",
        "role": "Software Engineer",
        "tags": ["Coding", "Binary Trees", "Recursion"],
        "source_type": "standard",
        "explanation": "Use preorder traversal with a delimiter (e.g. commas) and sentinel tokens (like '#') for null nodes. Deserialize by splitting tokens into an iterator and recursively reconstructing tree nodes.",
    },
    # Aptitude
    {
        "question": "A car travels at 60 km/h for the first half of a distance and 40 km/h for the second half. What is the average speed?",
        "category": "Aptitude",
        "difficulty": "Easy",
        "role": "General",
        "tags": ["Aptitude", "Quantitative", "Speed & Distance"],
        "source_type": "standard",
        "explanation": "Average speed = 2 * v1 * v2 / (v1 + v2) = (2 * 60 * 40) / (60 + 40) = 4800 / 100 = 48 km/h. It is the harmonic mean of speeds, not arithmetic mean.",
    },
    {
        "question": "You have 8 balls of identical appearance, one of which is slightly heavier. Using a balance scale only twice, how do you find the heavy ball?",
        "category": "Aptitude",
        "difficulty": "Medium",
        "role": "General",
        "tags": ["Aptitude", "Logic Puzzles", "Critical Thinking"],
        "source_type": "standard",
        "explanation": "Divide balls into 3, 3, and 2. Weigh 3 vs 3. If balanced, weigh the remaining 2 against each other. If unbalanced, pick the heavier group of 3, weigh 1 vs 1; if equal, the unweighed 3rd ball is the heavier one.",
    },
    {
        "question": "What is the probability of obtaining at least one six when throwing four fair dice?",
        "category": "Aptitude",
        "difficulty": "Hard",
        "role": "General",
        "tags": ["Aptitude", "Probability", "Combinatorics"],
        "source_type": "standard",
        "explanation": "Calculate the complementary probability of getting no sixes on all 4 dice: (5/6)^4 = 625/1296 ≈ 0.482. Therefore, P(at least one six) = 1 - 0.482 = 0.518 (51.8%).",
    },
    # Role-specific
    {
        "question": "In React, explain the differences between Client Components and Server Components (RSC) and when to use each.",
        "category": "Role-specific",
        "difficulty": "Medium",
        "role": "Frontend Engineer",
        "tags": ["Frontend", "React", "Server Components", "Performance"],
        "source_type": "standard",
        "explanation": "Server Components execute solely on the server, reducing bundle size and enabling direct database/backend access without extra API roundtrips. Client Components provide browser interactivity, event listeners, and React state.",
    },
    {
        "question": "How do you design an idempotent payment processing API to prevent duplicate charges during network timeouts?",
        "category": "Role-specific",
        "difficulty": "Hard",
        "role": "Backend Engineer",
        "tags": ["Backend", "Payments", "API Design", "Idempotency"],
        "source_type": "standard",
        "explanation": "Require client to send an Idempotency-Key header (UUID). Store the key with request fingerprint in a distributed lock or database unique constraint with a short TTL before processing. Return the cached result on duplicate keys.",
    },
    {
        "question": "What metrics and observability signals would you establish to monitor an automated machine learning model pipeline in production?",
        "category": "Role-specific",
        "difficulty": "Hard",
        "role": "Machine Learning Engineer",
        "tags": ["AI/ML", "MLOps", "Model Monitoring", "Data Drift"],
        "source_type": "standard",
        "explanation": "Monitor feature distribution shifts (data drift using KS tests or PSI), prediction distribution changes (concept drift), inference latency (p95/p99), ground truth accuracy lag, and data schema violations.",
    },
]


async def seed_standard_questions_if_empty(db: AsyncSession) -> None:
    """Seed standard initial question bank items across all categories if missing."""
    existing_res = await db.execute(select(Question.question))
    existing_questions = set(existing_res.scalars().all())

    to_add = []
    for item in STANDARD_SEED_QUESTIONS:
        if item["question"] not in existing_questions:
            q_orm = Question(
                question=item["question"],
                category=item["category"],
                difficulty=item["difficulty"],
                role=item["role"],
                tags=item["tags"],
                source_type=item["source_type"],
                explanation=item["explanation"],
            )
            to_add.append(q_orm)
            existing_questions.add(item["question"])

    if to_add:
        logger.info("Seeding %d standard interview questions...", len(to_add))
        db.add_all(to_add)
        await db.commit()


def format_question_response(q: Question, is_saved: bool = False) -> QuestionResponse:
    """Format Question ORM into response schema with explicit AI source labeling."""
    source_label = (
        "AI-generated practice question"
        if q.source_type == "ai_generated"
        else "Standard Interview Question"
    )
    return QuestionResponse(
        id=q.id,
        question=q.question,
        category=q.category,
        difficulty=q.difficulty,
        role=q.role,
        tags=q.tags or [],
        source_type=q.source_type,
        source_label=source_label,
        explanation=q.explanation,
        is_saved=is_saved,
        created_at=q.created_at,
    )


async def list_questions(
    db: AsyncSession,
    user: User,
    category: str | None = None,
    difficulty: str | None = None,
    role: str | None = None,
    q: str | None = None,
    source_type: str | None = None,
    saved_only: bool = False,
    page: int = 1,
    limit: int = 20,
) -> list[QuestionResponse]:
    """Search and filter interview question bank."""
    await seed_standard_questions_if_empty(db)

    # User saved IDs
    saved_query = select(SavedQuestion.question_id).where(SavedQuestion.user_id == user.id)
    saved_res = await db.execute(saved_query)
    saved_ids = set(saved_res.scalars().all())

    query = select(Question)

    if saved_only:
        query = query.where(Question.id.in_(saved_ids))

    if category and category.strip():
        query = query.where(Question.category.ilike(f"%{category.strip()}%"))

    if difficulty and difficulty.strip():
        query = query.where(Question.difficulty.ilike(f"%{difficulty.strip()}%"))

    if role and role.strip():
        query = query.where(Question.role.ilike(f"%{role.strip()}%"))

    if source_type and source_type.strip():
        query = query.where(Question.source_type == source_type.strip())

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.where(
            Question.question.ilike(search_pattern) | Question.explanation.ilike(search_pattern)
        )

    query = query.order_by(Question.created_at.desc()).offset((page - 1) * limit).limit(limit)
    res = await db.execute(query)
    questions = res.scalars().all()

    return [format_question_response(item, is_saved=(item.id in saved_ids)) for item in questions]


async def get_random_question(
    db: AsyncSession,
    user: User,
    category: str | None = None,
    difficulty: str | None = None,
    role: str | None = None,
) -> QuestionResponse:
    """Get a random practice question from the question bank."""
    await seed_standard_questions_if_empty(db)

    saved_query = select(SavedQuestion.question_id).where(SavedQuestion.user_id == user.id)
    saved_res = await db.execute(saved_query)
    saved_ids = set(saved_res.scalars().all())

    query = select(Question)
    if category and category.strip():
        query = query.where(Question.category.ilike(f"%{category.strip()}%"))
    if difficulty and difficulty.strip():
        query = query.where(Question.difficulty.ilike(f"%{difficulty.strip()}%"))
    if role and role.strip():
        query = query.where(Question.role.ilike(f"%{role.strip()}%"))

    query = query.order_by(func.random()).limit(1)
    res = await db.execute(query)
    q_item = res.scalar_one_or_none()

    if not q_item:
        # Fallback to absolute random question
        res_fallback = await db.execute(select(Question).order_by(func.random()).limit(1))
        q_item = res_fallback.scalar_one_or_none()

    if not q_item:
        raise AppException(message="No practice questions available in the question bank.", status_code=404)

    return format_question_response(q_item, is_saved=(q_item.id in saved_ids))


async def get_question_by_id(db: AsyncSession, question_id: int, user_id: int) -> QuestionResponse:
    """Get single question by ID."""
    res = await db.execute(select(Question).where(Question.id == question_id))
    q_item = res.scalar_one_or_none()
    if not q_item:
        raise AppException(message="Interview question not found.", status_code=404)

    saved_res = await db.execute(
        select(SavedQuestion).where(SavedQuestion.user_id == user_id, SavedQuestion.question_id == question_id)
    )
    is_saved = saved_res.scalar_one_or_none() is not None
    return format_question_response(q_item, is_saved=is_saved)


GENERATE_QUESTIONS_PROMPT = """You are an expert Technical Interviewer assessing a candidate for the {role} position.
Generate {count} technically accurate, realistic interview questions specifically focusing on the topic: "{topic}".

INTERVIEW SPECIFICATIONS:
- Target Role: {role}
- Category: {category}
- Difficulty: {difficulty}
- Technical Topic: {topic}

CRITICAL ACCURACY RULES:
1. Every question must directly test practical technical competency, implementation patterns, edge cases, and trade-offs of "{topic}".
2. Do NOT generate generic or placeholder questions. Questions must be concrete, realistic interview questions asked by top engineering teams.
3. The explanation MUST provide the correct, accurate technical answer, key concepts, and best practices.

OUTPUT FORMAT (JSON only):
{{
  "questions": [
    {{
      "question": "Concrete, technically precise interview question about {topic}?",
      "category": "{category}",
      "difficulty": "{difficulty}",
      "role": "{role}",
      "tags": ["{category}", "{topic}"],
      "explanation": "Factually accurate, thorough technical answer guide explaining the core concepts, implementation details, and trade-offs."
    }}
  ]
}}
"""


def generate_fallback_questions(
    role: str,
    category: str,
    difficulty: str,
    topic: str,
    count: int = 5,
) -> list[AIQuestionItemPayload]:
    """Generate rich, realistic practice questions tailored to category, role, and topic."""
    cat_lower = category.lower()
    t_clean = topic.strip() if topic else "Core Engineering Principles"
    r_clean = role.strip() if role else "Software Engineer"
    d_clean = difficulty.strip() if difficulty else "Medium"

    question_templates: list[tuple[str, str, list[str]]] = []

    if "sql" in cat_lower:
        question_templates = [
            (
                f"How would you optimize a slow query involving {t_clean} and large table joins in PostgreSQL / MySQL?",
                f"Analyze EXPLAIN ANALYZE execution plans, identify sequential table scans vs index scans, verify index selectivity on {t_clean}, and consider partitioning or materializing common subquery tables.",
                ["SQL", "Query Optimization", "Indexing"],
            ),
            (
                f"Explain how window functions (like ROW_NUMBER, RANK, and DENSE_RANK) differ and how you would use them for {t_clean}.",
                f"ROW_NUMBER assigns distinct sequential integers. RANK assigns the same rank to ties leaving gaps. DENSE_RANK assigns identical ranks without gaps. Useful for top-N analysis on {t_clean} datasets.",
                ["SQL", "Window Functions", "Analytics"],
            ),
            (
                f"When working with {t_clean}, how do you ensure ACID transactional consistency during concurrent write operations?",
                f"Use appropriate transaction isolation levels (Repeatable Read or Serializable), implement pessimistic row locking (SELECT ... FOR UPDATE) or optimistic concurrency control with version timestamps.",
                ["SQL", "Transactions", "ACID", "Concurrency"],
            ),
            (
                f"What are common anti-patterns in database schema design for {t_clean} and how do you resolve them?",
                f"Avoid unindexed foreign keys, excessive denormalization without caching, EAV (Entity-Attribute-Value) anti-patterns, and improper data types that cause table bloat and cache thrashing.",
                ["SQL", "Database Design", "Architecture"],
            ),
            (
                f"How does composite B-tree indexing work when querying columns related to {t_clean}?",
                f"Follow the leftmost prefix rule. An index on (A, B, C) accelerates queries filtering on (A), (A, B), or (A, B, C), but not (B, C) alone. Range filters must be placed on the trailing index column.",
                ["SQL", "B-Tree Indexing", "Performance"],
            ),
        ]
    elif "dsa" in cat_lower:
        question_templates = [
            (
                f"Describe an optimal algorithmic approach for solving problems involving {t_clean}, including time and space complexity.",
                f"Identify problem invariants, evaluate two-pointer vs hash map vs divide-and-conquer approaches. Strive for O(N) or O(N log N) runtime with O(1) or O(N) memory overhead.",
                ["DSA", "Algorithms", "Complexity Analysis"],
            ),
            (
                f"How would you detect edge cases and handle boundary constraints when implementing {t_clean} data structures?",
                f"Account for empty inputs, single-element collections, integer overflow boundaries, cyclical references, and duplicate keys. Verify termination conditions in loops and recursions.",
                ["DSA", "Edge Cases", "Data Structures"],
            ),
            (
                f"Compare the trade-offs between a recursive approach and an iterative approach with explicit stacks for {t_clean}.",
                f"Recursive implementations are concise and readable but risk stack overflow on deep recursion (O(N) call stack). Iterative approaches with manual stacks provide tighter memory boundaries and better CPU cache locality.",
                ["DSA", "Recursion", "Memory Optimization"],
            ),
            (
                f"How do you choose between Breadth-First Search (BFS) and Depth-First Search (DFS) for {t_clean} graph or tree problems?",
                f"BFS is ideal for finding the shortest path or level-by-level traversal in unweighted graphs using a queue (O(V+E) time, O(V) space). DFS is ideal for topological sort, cycle detection, and backtracking paths using recursion or a stack.",
                ["DSA", "Graphs", "BFS/DFS"],
            ),
            (
                f"Explain how Dynamic Programming (DP) state formulation and memoization apply to optimal substructures in {t_clean}.",
                f"Break down overlapping subproblems, define dp[i] state transition relations, identify base cases, and optimize space by storing only the required preceding states (e.g. O(1) space instead of O(N)).",
                ["DSA", "Dynamic Programming", "Optimization"],
            ),
        ]
    elif "coding" in cat_lower:
        question_templates = [
            (
                f"Write an efficient algorithm to process input streams for {t_clean} while minimizing memory allocation.",
                f"Utilize generator pipelines, in-place array transformations, or sliding window buffers to maintain O(1) memory overhead and process stream elements in O(N) linear time.",
                ["Coding", "Clean Code", "Efficiency"],
            ),
            (
                f"Implement a robust error-handling wrapper around operations involving {t_clean} to guarantee fault tolerance.",
                f"Use structured exception handling, retry policies with exponential backoff and jitter, defensive input sanitization, and detailed context logging to prevent cascading failures.",
                ["Coding", "Error Handling", "Fault Tolerance"],
            ),
            (
                f"How would you refactor legacy code dealing with {t_clean} to make it modular and unit-testable?",
                f"Apply SOLID principles: decouple business logic from external I/O using dependency inversion, write pure deterministic functions, and inject mockable interfaces for unit test coverage.",
                ["Coding", "Refactoring", "Unit Testing", "SOLID"],
            ),
            (
                f"Write a solution to identify and deduplicate records based on {t_clean} criteria in linear time.",
                f"Use a hash set or hash table to track seen signatures in O(1) average time per element, filtering duplicates while preserving original sequence order in O(N) overall time.",
                ["Coding", "Data Structures", "Deduplication"],
            ),
            (
                f"How do you implement thread-safe or asynchronous concurrency primitives when working with {t_clean}?",
                f"In Python use asyncio locks and semaphores; in compiled languages use mutexes or atomic operations. Prevent deadlocks by enforcing consistent lock acquisition ordering.",
                ["Coding", "Concurrency", "Async"],
            ),
        ]
    elif "behavioral" in cat_lower:
        question_templates = [
            (
                f"Tell me about a time you introduced an architectural improvement or tool for {t_clean} that elevated team productivity.",
                f"Use the STAR format: Explain the legacy bottleneck (Situation), your targeted objective (Task), how you built consensus, created documentation, and implemented the solution (Action), and quantifiable productivity gains achieved (Result).",
                ["Behavioral", "Leadership", "Technical Innovation"],
            ),
            (
                f"Describe a situation where a critical incident occurred with {t_clean} in production. How did you diagnose and resolve it?",
                f"Detail incident triage: alerting team members, rolling back safely or deploying hotfixes, communicating incident status with stakeholders, and authoring a blameless post-mortem with preventative actions.",
                ["Behavioral", "Incident Management", "Accountability"],
            ),
            (
                f"Give an example of a technical disagreement regarding {t_clean} with a peer or senior engineer. How did you find common ground?",
                f"Describe how you separated personal preference from engineering metrics, designed a quick prototype or benchmark test to gather objective data, and agreed on the outcome aligned with product goals.",
                ["Behavioral", "Collaboration", "Conflict Resolution"],
            ),
            (
                f"Tell me about a project involving {t_clean} where scope changed unexpectedly midway through development.",
                f"Highlight adaptability: re-evaluating milestones, trimming non-essential features, realigning deliverable deadlines with management, and successfully shipping the core value proposition on time.",
                ["Behavioral", "Adaptability", "Project Delivery"],
            ),
            (
                f"How do you mentor junior developers or onboard new teammates on {t_clean} best practices?",
                f"Discuss pair programming, creating clear runbooks and architectural diagrams, providing constructive and encouraging code reviews, and fostering psychological safety for technical questions.",
                ["Behavioral", "Mentorship", "Team Culture"],
            ),
        ]
    elif "hr" in cat_lower:
        question_templates = [
            (
                f"Why are you passionate about working as a {r_clean}, and how does your experience with {t_clean} fit into your career trajectory?",
                f"Connect your past accomplishments and technical passions directly with the team's mission. Highlight how continuous learning in {t_clean} prepares you to drive meaningful impact.",
                ["HR", "Career Motivation", "Role Fit"],
            ),
            (
                f"What type of work culture and engineering environment empowers you to do your best work with {t_clean}?",
                f"Discuss appreciation for collaborative, transparent engineering cultures, blameless learning environments, autonomy with high accountability, and open feedback loops.",
                ["HR", "Workplace Culture", "Values"],
            ),
            (
                f"How do you maintain continuous learning and stay current with modern advancements in {t_clean} and {r_clean} domains?",
                f"Mention reputable industry engineering blogs, contributing to open-source, experimenting with side projects, reading technical whitepapers, and actively participating in tech communities.",
                ["HR", "Continuous Learning", "Professional Development"],
            ),
            (
                f"Tell me about a professional achievement in your {r_clean} career that you are most proud of.",
                f"Select a high-impact initiative: outline the initial challenge, explain your personal role and dedication, and share quantifiable positive impact on users, performance, or team velocity.",
                ["HR", "Achievements", "Impact"],
            ),
            (
                f"How do you manage stress and prioritize competing deadlines when multiple high-priority tasks arrive simultaneously?",
                f"Detail your prioritization framework (e.g. Eisenhower Matrix, impact vs urgency), clear communication with team leadership regarding trade-offs, and disciplined time management.",
                ["HR", "Stress Management", "Prioritization"],
            ),
        ]
    elif "aptitude" in cat_lower:
        question_templates = [
            (
                f"How would you calculate the throughput and concurrency requirements for a service handling {t_clean} given target latency and peak QPS?",
                f"Calculate Little's Law: Concurrency (L) = Arrival Rate (lambda) * Average Response Time (W). Size worker threads and database connection pools accordingly with a 2-3x peak multiplier.",
                ["Aptitude", "Capacity Planning", "System Metrics"],
            ),
            (
                f"In a high-availability cluster handling {t_clean} with 5 redundant nodes each with 99% uptime probability, what is the probability that at least 4 nodes are operational?",
                f"Use Binomial probability: P(4 nodes) = 5 * (0.99)^4 * 0.01 ≈ 0.0480. P(5 nodes) = (0.99)^5 ≈ 0.9510. Total P(>=4) = 0.0480 + 0.9510 = 0.9990 (99.9%).",
                ["Aptitude", "Probability", "Reliability Engineering"],
            ),
            (
                f"Explain how you would estimate the storage and bandwidth requirements for a service processing {t_clean} at 10M daily active users.",
                f"Perform Fermi estimation: 10M DAU * 10 actions/day = 100M actions/day. If each payload is 1KB, daily storage is 100GB. Bandwidth = 100GB / 86400s ≈ 1.15 MB/s average, with 3x peak buffer (3.5 MB/s).",
                ["Aptitude", "Fermi Estimation", "System Capacity"],
            ),
            (
                f"Analyze the time and space complexity trade-offs when caching {t_clean} data using an in-memory LRU cache vs distributed cache.",
                f"In-memory caches (LRU via HashMap + DoublyLinkedList) offer sub-millisecond O(1) latency but consume app memory and lack cross-process sharing. Distributed caches (Redis) add network hops (1-2ms) but provide shared state and horizontal scalability.",
                ["Aptitude", "System Design", "Complexity Analysis"],
            ),
            (
                f"Given an SLA of 99.99% availability ('four nines') for a service handling {t_clean}, what is the maximum permissible annual downtime, and how do you architect for it?",
                f"Annual allowable downtime is 52.6 minutes (8.6 seconds/day). Requires multi-region active-passive or active-active failover, automated health checks, zero-downtime rolling deployments, and automated circuit breaking.",
                ["Aptitude", "SLA", "High Availability"],
            ),
        ]
    else:  # Technical / Role-specific
        question_templates = [
            (
                f"Explain how {t_clean} works in {r_clean} architectures, including key performance considerations.",
                f"Demonstrate core principles of {t_clean}, trade-offs, edge cases, and best practices relevant to {r_clean} positions. Discuss caching, network latency, and memory footprint.",
                ["Technical", r_clean, t_clean],
            ),
            (
                f"What are common pitfalls, memory bottlenecks, and error scenarios when working with {t_clean} in production?",
                f"Discuss telemetry, error boundaries, monitoring metrics, thread contention, resource leakage, and recovery strategies for {t_clean} at scale.",
                ["Technical", "Production Safety", "Performance"],
            ),
            (
                f"How would you design a highly scalable and fault-tolerant system component centered around {t_clean}?",
                f"Detail component boundaries: load balancing, stateless worker pools, idempotent processing queues, circuit breakers, and read replicas for high availability.",
                ["Technical", "System Design", "Scalability"],
            ),
            (
                f"Compare synchronous vs asynchronous communication patterns when integrating {t_clean} with downstream microservices.",
                f"Synchronous REST/gRPC provides immediate response confirmation but introduces tight coupling and cascading latency. Asynchronous message queues (Kafka, RabbitMQ) provide decoupling and backpressure tolerance.",
                ["Technical", "Microservices", "Messaging"],
            ),
            (
                f"How do you implement comprehensive telemetry, logging, and metrics instrumentation for {t_clean}?",
                f"Instrument structured JSON logging with correlation IDs, capture RED metrics (Rate, Errors, Duration) via Prometheus, and trace end-to-end distributed spans using OpenTelemetry.",
                ["Technical", "Observability", "Telemetry"],
            ),
            (
                f"What security practices, authentication mechanisms, and data encryption strategies should be enforced when deploying {t_clean}?",
                f"Enforce least-privilege access, encrypt data at rest (AES-256) and in transit (TLS 1.3), sanitize user inputs to prevent injection, and store secrets securely in vault managers rather than code.",
                ["Technical", "Security", "Encryption"],
            ),
        ]

    results: list[AIQuestionItemPayload] = []
    num_templates = len(question_templates)
    for idx in range(count):
        q_text, expl, tags = question_templates[idx % num_templates]
        if idx >= num_templates:
            suffix_num = (idx // num_templates) + 1
            q_text = f"{q_text[:-1]} (Scenario {suffix_num})?"

        results.append(
            AIQuestionItemPayload(
                question=q_text,
                category=category,
                difficulty=difficulty,
                role=role,
                tags=tags,
                explanation=expl,
            )
        )
    return results


async def generate_ai_questions(
    db: AsyncSession,
    user: User,
    request: GenerateQuestionsRequest,
    ai_provider: OllamaProvider | None = None,
) -> list[QuestionResponse]:
    """Generate personalized practice questions via Ollama or robust AI question synthesis."""
    provider = ai_provider or OllamaProvider()
    prompt = GENERATE_QUESTIONS_PROMPT.format(
        count=request.count,
        role=request.role,
        category=request.category,
        difficulty=request.difficulty,
        topic=request.topic or "Core Concepts",
    )

    raw_response = None
    try:
        raw_response = await asyncio.wait_for(
            provider.generate(
                prompt,
                format="json",
                options={"num_predict": 1000, "num_ctx": 4096, "temperature": 0.2},
            ),
            timeout=90.0,
        )
    except Exception as exc:
        logger.warning("Ollama AI question generation call failed or timed out: %s", exc)

    from app.integrations.ai.json_utils import extract_and_parse_json

    items: list[AIQuestionItemPayload] = []
    if raw_response:
        try:
            parsed = extract_and_parse_json(raw_response)
            raw_list = []
            if isinstance(parsed, dict) and "questions" in parsed and isinstance(parsed["questions"], list):
                raw_list = parsed["questions"]
            elif isinstance(parsed, list):
                raw_list = parsed
            elif isinstance(parsed, dict):
                raw_list = [v for v in parsed.values() if isinstance(v, (dict, str))]

            for entry in raw_list:
                try:
                    if isinstance(entry, dict):
                        item_obj = AIQuestionItemPayload.model_validate(entry)
                        if item_obj.question:
                            if not item_obj.category:
                                item_obj.category = request.category
                            if not item_obj.difficulty:
                                item_obj.difficulty = request.difficulty
                            if not item_obj.role:
                                item_obj.role = request.role
                            if not item_obj.explanation:
                                item_obj.explanation = (
                                    f"Key preparation question on {request.topic or 'core concepts'} for {request.role}. "
                                    "Evaluates implementation patterns, edge cases, and architectural best practices."
                                )
                            items.append(item_obj)
                    elif isinstance(entry, str) and entry.strip():
                        items.append(
                            AIQuestionItemPayload(
                                question=entry.strip(),
                                category=request.category,
                                difficulty=request.difficulty,
                                role=request.role,
                                tags=[request.category, request.difficulty],
                                explanation=f"Key preparation question on {request.topic or 'core principles'} for {request.role}.",
                            )
                        )
                except Exception as entry_exc:
                    logger.debug("Skipping unparseable question entry: %s", entry_exc)
        except Exception as parse_exc:
            logger.warning("Parsing AI questions response failed: %s", parse_exc)

    # Supplement or generate if fewer than requested count
    if len(items) < request.count:
        needed = request.count - len(items)
        existing_texts = {i.question.lower().strip() for i in items}
        fallbacks = generate_fallback_questions(
            role=request.role,
            category=request.category,
            difficulty=request.difficulty,
            topic=request.topic or "Core Concepts",
            count=needed + 5,
        )
        for fb in fallbacks:
            if fb.question.lower().strip() not in existing_texts:
                items.append(fb)
                existing_texts.add(fb.question.lower().strip())
            if len(items) >= request.count:
                break

    saved_ids_res = await db.execute(select(SavedQuestion.question_id).where(SavedQuestion.user_id == user.id))
    saved_ids = set(saved_ids_res.scalars().all())

    created_responses: list[QuestionResponse] = []
    for item in items[: request.count]:
        q_orm = Question(
            question=item.question,
            category=item.category or request.category,
            difficulty=item.difficulty or request.difficulty,
            role=item.role or request.role,
            tags=item.tags or [request.category, request.difficulty],
            source_type="ai_generated",  # MUST mark source type as AI-generated
            explanation=item.explanation,
        )
        db.add(q_orm)
        await db.flush()
        created_responses.append(format_question_response(q_orm, is_saved=(q_orm.id in saved_ids)))

    await db.commit()
    return created_responses


async def save_question_for_user(db: AsyncSession, user: User, question_id: int) -> QuestionResponse:
    """Save/bookmark an interview question for the user."""
    q_resp = await get_question_by_id(db, question_id, user_id=user.id)

    saved_query = select(SavedQuestion).where(
        SavedQuestion.user_id == user.id, SavedQuestion.question_id == question_id
    )
    saved_res = await db.execute(saved_query)
    existing = saved_res.scalar_one_or_none()

    if not existing:
        saved_entry = SavedQuestion(user_id=user.id, question_id=question_id)
        db.add(saved_entry)
        await db.commit()

    q_resp.is_saved = True
    return q_resp


async def unsave_question_for_user(db: AsyncSession, user: User, question_id: int) -> QuestionResponse:
    """Remove an interview question bookmark."""
    q_resp = await get_question_by_id(db, question_id, user_id=user.id)

    stmt = delete(SavedQuestion).where(
        SavedQuestion.user_id == user.id, SavedQuestion.question_id == question_id
    )
    await db.execute(stmt)
    await db.commit()

    q_resp.is_saved = False
    return q_resp
