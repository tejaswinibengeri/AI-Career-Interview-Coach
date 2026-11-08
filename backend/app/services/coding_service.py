"""
Coding Challenge System Service (Module 12).
Manages problem repository seeding, sandbox execution orchestration, submission logging, and Ollama AI assistance.
"""

import asyncio
import logging
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.integrations.ai import get_ai_provider
from app.integrations.ai.base import AIProvider
from app.models.coding import CodingChallenge, CodingResult, CodingSubmission
from app.models.user import User
from app.schemas.coding import (
    AIHintResponse,
    CodingChallengeResponse,
    CodingResultResponse,
    CodingSubmissionResponse,
    SubmitCodeRequest,
)
from app.services.code_executor import execute_code_safely

logger = logging.getLogger(__name__)

import time
import uuid

STANDARD_CODING_CHALLENGES = [
    {
        "title": "Two Sum",
        "slug": "two-sum",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.",
        "starter_code": "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Write your solution here\n    pass\n",
        "examples": [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0, 1]",
                "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1].",
            },
            {
                "input": "nums = [3,2,4], target = 6",
                "output": "[1, 2]",
                "explanation": "Because nums[1] + nums[2] == 6, we return [1, 2].",
            },
        ],
        "test_cases": [
            {"input": "nums = [2, 7, 11, 15]\ntarget = 9", "expected_output": "[0, 1]"},
            {"input": "nums = [3, 2, 4]\ntarget = 6", "expected_output": "[1, 2]"},
            {"input": "nums = [3, 3]\ntarget = 6", "expected_output": "[0, 1]"},
        ],
        "explanation": "Use a hash map to store seen values and their indices. For each number x, check if (target - x) is present in map.",
    },
    {
        "title": "Valid Palindrome",
        "slug": "valid-palindrome",
        "category": "Python",
        "difficulty": "Easy",
        "language": "python",
        "description": "A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward.\n\nReturn `True` if it is a palindrome, or `False` otherwise.",
        "starter_code": "def is_palindrome(s: str) -> bool:\n    # Write your solution here\n    pass\n",
        "examples": [
            {
                "input": "s = 'A man, a plan, a canal: Panama'",
                "output": "True",
                "explanation": "'amanaplanacanalpanama' is a palindrome.",
            },
            {
                "input": "s = 'race a car'",
                "output": "False",
                "explanation": "'raceacar' is not a palindrome.",
            },
        ],
        "test_cases": [
            {"input": "s = 'A man, a plan, a canal: Panama'", "expected_output": "True"},
            {"input": "s = 'race a car'", "expected_output": "False"},
            {"input": "s = ' '", "expected_output": "True"},
        ],
        "explanation": "Filter alphanumeric characters in lowercase using `[c.lower() for c in s if c.isalnum()]` and compare with its reverse.",
    },
    {
        "title": "Binary Search",
        "slug": "binary-search",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "Given an array of integers `nums` which is sorted in ascending order, and an integer `target`, write a function to search `target` in `nums`. If `target` exists, then return its index. Otherwise, return `-1`.\n\nYou must write an algorithm with `O(log n)` runtime complexity.",
        "starter_code": "def search(nums: list[int], target: int) -> int:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"}
        ],
        "test_cases": [
            {"input": "nums = [-1,0,3,5,9,12]\ntarget = 9", "expected_output": "4"},
            {"input": "nums = [-1,0,3,5,9,12]\ntarget = 2", "expected_output": "-1"},
            {"input": "nums = [5]\ntarget = 5", "expected_output": "0"}
        ],
        "explanation": "Initialize left = 0 and right = len(nums) - 1. Loop while left <= right, compute mid = (left + right) // 2 and adjust bounds.",
    },
    {
        "title": "Maximum Subarray (Kadane's Algorithm)",
        "slug": "maximum-subarray",
        "category": "DSA",
        "difficulty": "Medium",
        "language": "python",
        "description": "Given an integer array `nums`, find the subarray with the largest sum, and return its sum.",
        "starter_code": "def max_sub_array(nums: list[int]) -> int:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "The subarray [4,-1,2,1] has the largest sum 6."}
        ],
        "test_cases": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "expected_output": "6"},
            {"input": "nums = [1]", "expected_output": "1"},
            {"input": "nums = [5,4,-1,7,8]", "expected_output": "23"}
        ],
        "explanation": "Keep track of current_max and global_max. At each element x, update current_max = max(x, current_max + x) and global_max = max(global_max, current_max).",
    },
    {
        "title": "Valid Parentheses",
        "slug": "valid-parentheses",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\nAn input string is valid if open brackets are closed by the same type of brackets in the correct order.",
        "starter_code": "def is_valid(s: str) -> bool:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "s = '()[]{}'", "output": "True"},
            {"input": "s = '(]'", "output": "False"}
        ],
        "test_cases": [
            {"input": "s = '()[]{}'", "expected_output": "True"},
            {"input": "s = '(]'", "expected_output": "False"},
            {"input": "s = '([)]'", "expected_output": "False"},
            {"input": "s = '{[]}'", "expected_output": "True"}
        ],
        "explanation": "Use a stack. Push opening brackets, and for closing brackets, pop and verify matching pair.",
    },
    {
        "title": "Contains Duplicate",
        "slug": "contains-duplicate",
        "category": "Python",
        "difficulty": "Easy",
        "language": "python",
        "description": "Given an integer array `nums`, return `True` if any value appears at least twice in the array, and return `False` if every element is distinct.",
        "starter_code": "def contains_duplicate(nums: list[int]) -> bool:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "nums = [1,2,3,1]", "output": "True"},
            {"input": "nums = [1,2,3,4]", "output": "False"}
        ],
        "test_cases": [
            {"input": "nums = [1,2,3,1]", "expected_output": "True"},
            {"input": "nums = [1,2,3,4]", "expected_output": "False"},
            {"input": "nums = [1,1,1,3,3,4,3,2,4,2]", "expected_output": "True"}
        ],
        "explanation": "Compare len(nums) with len(set(nums)) or check membership in a seen set while iterating.",
    },
    {
        "title": "Best Time to Buy and Sell Stock",
        "slug": "best-time-to-buy-and-sell-stock",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "You are given an array `prices` where `prices[i]` is the price of a given stock on the `i-th` day.\n\nYou want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.\n\nReturn the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.",
        "starter_code": "def max_profit(prices: list[int]) -> int:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "prices = [7,1,5,3,6,4]", "output": "5", "explanation": "Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5."}
        ],
        "test_cases": [
            {"input": "prices = [7,1,5,3,6,4]", "expected_output": "5"},
            {"input": "prices = [7,6,4,3,1]", "expected_output": "0"}
        ],
        "explanation": "Maintain min_price seen so far and max_profit. Iterate through prices updating min_price and max_profit = max(max_profit, price - min_price).",
    },
    {
        "title": "Group Anagrams",
        "slug": "group-anagrams",
        "category": "Python",
        "difficulty": "Medium",
        "language": "python",
        "description": "Given an array of strings `strs`, group the anagrams together. You can return the answer in any order.",
        "starter_code": "def group_anagrams(strs: list[str]) -> list[list[str]]:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "strs = ['eat','tea','tan','ate','nat','bat']", "output": "[['bat'],['nat','tan'],['ate','eat','tea']]"}
        ],
        "test_cases": [
            {"input": "strs = ['eat','tea','tan','ate','nat','bat']", "expected_output": "[['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]"},
            {"input": "strs = ['']", "expected_output": "[['']]"},
            {"input": "strs = ['a']", "expected_output": "[['a']]"}
        ],
        "explanation": "Use a defaultdict(list) where key is tuple(sorted(word)) or character frequency count.",
    },
    {
        "title": "Climbing Stairs",
        "slug": "climbing-stairs",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "You are climbing a staircase. It takes `n` steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
        "starter_code": "def climb_stairs(n: int) -> int:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "n = 2", "output": "2"},
            {"input": "n = 3", "output": "3"}
        ],
        "test_cases": [
            {"input": "n = 2", "expected_output": "2"},
            {"input": "n = 3", "expected_output": "3"},
            {"input": "n = 5", "expected_output": "8"}
        ],
        "explanation": "This follows the Fibonacci recurrence relation dp[i] = dp[i-1] + dp[i-2].",
    },
    {
        "title": "Longest Common Prefix",
        "slug": "longest-common-prefix",
        "category": "Python",
        "difficulty": "Easy",
        "language": "python",
        "description": "Write a function to find the longest common prefix string amongst an array of strings. If there is no common prefix, return an empty string `''`.",
        "starter_code": "def longest_common_prefix(strs: list[str]) -> str:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "strs = ['flower','flow','flight']", "output": "'fl'"},
            {"input": "strs = ['dog','racecar','car']", "output": "''"}
        ],
        "test_cases": [
            {"input": "strs = ['flower','flow','flight']", "expected_output": "fl"},
            {"input": "strs = ['dog','racecar','car']", "expected_output": ""}
        ],
        "explanation": "Iterate character by character across all strings or sort array and compare first and last strings.",
    },
    {
        "title": "Department Highest Salary",
        "slug": "department-highest-salary",
        "category": "SQL",
        "difficulty": "Medium",
        "language": "sql",
        "description": "Write a SQL query to find employees who have the highest salary in each of the departments.\n\nReturn the result table with columns: `Department`, `Employee`, `Salary`.",
        "starter_code": "-- Write your SQL solution below\nSELECT Department.name AS Department, Employee.name AS Employee, Employee.salary AS Salary\nFROM Employee\nJOIN Department ON Employee.department_id = Department.id\nWHERE ...\n",
        "sql_schema": """
CREATE TABLE Department (id INT, name VARCHAR(50));
CREATE TABLE Employee (id INT, name VARCHAR(50), salary INT, department_id INT);

INSERT INTO Department VALUES (1, 'IT'), (2, 'Sales');
INSERT INTO Employee VALUES (1, 'Joe', 70000, 1), (2, 'Jim', 90000, 1), (3, 'Henry', 80000, 2), (4, 'Sam', 60000, 2), (5, 'Max', 90000, 1);
""",
        "examples": [
            {
                "input": "Department: IT, Sales\nEmployee: Joe (70k), Jim (90k), Henry (80k), Max (90k)",
                "output": "[['IT', 'Jim', 90000], ['IT', 'Max', 90000], ['Sales', 'Henry', 80000]]",
                "explanation": "Jim and Max have the highest salary in IT (90k); Henry has highest in Sales (80k).",
            }
        ],
        "test_cases": [
            {
                "input": "Department & Employee Data",
                "expected_output": '[["IT", "Jim", 90000], ["IT", "Max", 90000], ["Sales", "Henry", 80000]]',
            }
        ],
        "explanation": "Use a subquery or `WHERE (department_id, salary) IN (SELECT department_id, MAX(salary) FROM Employee GROUP BY department_id)`.",
    },
    {
        "title": "Second Highest Salary",
        "slug": "second-highest-salary",
        "category": "SQL",
        "difficulty": "Medium",
        "language": "sql",
        "description": "Write a SQL query to find the second highest distinct salary from the `Employee` table. If there is no second highest salary, return `NULL`.",
        "starter_code": "-- Write your SQL solution below\nSELECT MAX(salary) AS SecondHighestSalary\nFROM Employee\nWHERE ...\n",
        "sql_schema": """
CREATE TABLE Employee (id INT, salary INT);
INSERT INTO Employee VALUES (1, 100), (2, 200), (3, 300);
""",
        "examples": [
            {"input": "Employee: 100, 200, 300", "output": "200"}
        ],
        "test_cases": [
            {"input": "Employee Table Data", "expected_output": "[[200]]"}
        ],
        "explanation": "SELECT MAX(salary) FROM Employee WHERE salary < (SELECT MAX(salary) FROM Employee);",
    },
    {
        "title": "Reverse Array In-Place",
        "slug": "reverse-array",
        "category": "DSA",
        "difficulty": "Easy",
        "language": "python",
        "description": "Given an array `arr` of integers, return a new array with elements in reversed order.",
        "starter_code": "def reverse_array(arr: list[int]) -> list[int]:\n    # Write your solution here\n    pass\n",
        "examples": [
            {"input": "arr = [1, 2, 3, 4, 5]", "output": "[5, 4, 3, 2, 1]"}
        ],
        "test_cases": [
            {"input": "arr = [1, 2, 3, 4, 5]", "expected_output": "[5, 4, 3, 2, 1]"},
            {"input": "arr = [10, 20]", "expected_output": "[20, 10]"},
        ],
        "explanation": "Use two pointers moving inward swapping elements `left` and `right`, or return `arr[::-1]`.",
    },
]


async def seed_standard_challenges_if_empty(db: AsyncSession) -> None:
    """Seed standard initial coding challenges if missing."""
    for item in STANDARD_CODING_CHALLENGES:
        query = select(CodingChallenge).where(CodingChallenge.slug == item["slug"])
        res = await db.execute(query)
        if not res.scalar_one_or_none():
            ch = CodingChallenge(
                title=item["title"],
                slug=item["slug"],
                category=item["category"],
                difficulty=item["difficulty"],
                language=item["language"],
                description=item["description"],
                starter_code=item["starter_code"],
                examples=item.get("examples", []),
                test_cases=item.get("test_cases", []),
                explanation=item.get("explanation"),
                sql_schema=item.get("sql_schema"),
            )
            db.add(ch)
    await db.commit()


def format_challenge_response(
    ch: CodingChallenge, is_solved: bool = False
) -> CodingChallengeResponse:
    """Format CodingChallenge ORM into response schema with public sample tests."""
    sample_tests = ch.test_cases[:2] if ch.test_cases else []
    return CodingChallengeResponse(
        id=ch.id,
        title=ch.title,
        slug=ch.slug,
        category=ch.category,
        difficulty=ch.difficulty,
        description=ch.description,
        starter_code=ch.starter_code,
        language=ch.language,
        examples=ch.examples or [],
        sample_test_cases=sample_tests,
        explanation=ch.explanation,
        sql_schema=ch.sql_schema,
        is_solved=is_solved,
        created_at=ch.created_at,
    )


GENERATE_CODING_PROMPT = """You are an expert Technical Interviewer and Algorithm Designer.
Generate an accurate, well-specified coding challenge testing: "{topic}".

SPECIFICATIONS:
- Topic / Concept: {topic}
- Category: {category}
- Difficulty: {difficulty}

REQUIREMENTS:
1. Provide a clear, unambiguous problem description with constraints, input/output types, and edge cases.
2. The starter_code MUST define a valid function with type hints and a docstring.
3. The examples must include concrete inputs and expected outputs with clear explanations.
4. test_cases must contain at least 2 distinct valid test cases with "input" and "expected_output".
5. The explanation must explain the optimal algorithmic approach and state time and space complexity.

OUTPUT MUST BE VALID JSON ONLY matching this exact structure:
{{
  "title": "Clear Problem Title",
  "category": "{category}",
  "difficulty": "{difficulty}",
  "language": "python",
  "description": "Clear problem statement describing the task, inputs, and expected outputs.",
  "starter_code": "def solution(...):\n    # Write your code here\n    pass\n",
  "examples": [
    {{"input": "sample input", "output": "expected output", "explanation": "step by step explanation"}}
  ],
  "test_cases": [
    {{"input": "input_val_1", "expected_output": "output_val_1"}},
    {{"input": "input_val_2", "expected_output": "output_val_2"}}
  ],
  "explanation": "High-level algorithmic explanation or hint for solving this problem."
}}
"""


async def generate_ai_coding_challenge(
    db: AsyncSession,
    topic: str,
    category: str = "Python",
    difficulty: str = "Medium",
    ai_provider: AIProvider | None = None,
) -> CodingChallengeResponse:
    """Generate a custom coding challenge using Ollama AI or robust topic fallbacks."""
    import re, time, uuid
    from app.integrations.ai.json_utils import extract_and_parse_json

    clean_topic = topic.strip()
    clean_cat = category.strip() if category else "Python"
    clean_diff = difficulty.strip() if difficulty else "Medium"
    lang = "sql" if clean_cat.lower() == "sql" else "python"

    provider = ai_provider or get_ai_provider()
    prompt = GENERATE_CODING_PROMPT.format(topic=clean_topic, category=clean_cat, difficulty=clean_diff)

    parsed = None
    try:
        raw_json = await asyncio.wait_for(
            provider.generate(
                prompt,
                format="json",
                options={"num_predict": 1000, "num_ctx": 4096, "temperature": 0.2},
            ),
            timeout=90.0,
        )
        parsed = extract_and_parse_json(raw_json)
    except Exception as exc:
        logger.warning("Ollama call for custom coding challenge had an issue: %s", exc)

    if not isinstance(parsed, dict) or not parsed.get("title") or not parsed.get("starter_code"):
        # Construct realistic domain-aligned challenge tailored to topic
        slug_topic = re.sub(r"[^a-z0-9]+", "-", clean_topic.lower()).strip("-") or "custom"
        func_name = slug_topic.replace("-", "_")

        if lang == "sql":
            starter = f"-- Write your SQL solution below for {clean_topic}\n-- Tables: records(id INT, name VARCHAR, value NUMERIC, status VARCHAR)\nSELECT id, name, value\nFROM records\nWHERE status = 'active'\nORDER BY value DESC;\n"
            examples = [{"input": "records table with active and inactive rows", "output": "Filtered rows where status = 'active' ordered by value", "explanation": f"Evaluates query filtering and ordering for {clean_topic}."}]
            test_cases = [{"input": "Table Dataset", "expected_output": "Filtered Result Set"}]
        else:
            starter = f"def {func_name}(nums: list[int], k: int = 1) -> list[int]:\n    \"\"\"Solve {clean_topic} optimal problem.\n    \n    Args:\n        nums: Input integer list\n        k: Parameter constraint\n    Returns:\n        Processed output list\n    \"\"\"\n    # Implement optimal algorithm\n    pass\n"
            examples = [{"input": "nums = [4, 2, 1, 7, 8, 1, 2, 8, 1, 0], k = 3", "output": "[7, 8, 8]", "explanation": f"Applies optimal {clean_topic} window processing."}]
            test_cases = [
                {"input": "nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3", "expected_output": "[3, 3, 5, 5, 6, 7]"},
                {"input": "nums = [1], k = 1", "expected_output": "[1]"},
            ]

        parsed = {
            "title": f"{clean_topic.title()} Algorithm",
            "category": clean_cat,
            "difficulty": clean_diff,
            "language": lang,
            "description": f"### Problem Statement\nImplement an optimal algorithm for **{clean_topic}**.\n\n### Task\nGiven input parameters, process the dataset adhering strictly to optimal time and space constraints.\n\n### Constraints\n- Time Complexity: O(N) or O(N log N)\n- Space Complexity: O(N) or O(1) auxiliary",
            "starter_code": starter,
            "examples": examples,
            "test_cases": test_cases,
            "explanation": f"Analyze problem invariants, evaluate data structures (such as hash maps, two pointers, or sliding windows), and optimize for both runtime and memory overhead.",
        }

    title = str(parsed.get("title", f"{clean_topic} Challenge")).strip()
    slug_base = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
    unique_suffix = f"{int(time.time())}-{uuid.uuid4().hex[:4]}"
    slug_str = f"{slug_base}-{unique_suffix}"

    ch = CodingChallenge(
        title=title,
        slug=slug_str,
        category=str(parsed.get("category", clean_cat)),
        difficulty=str(parsed.get("difficulty", clean_diff)),
        language=str(parsed.get("language", lang)),
        description=str(parsed.get("description", f"Coding problem for {clean_topic}.")),
        starter_code=str(parsed.get("starter_code", f"# Write solution for {clean_topic}\npass\n")),
        examples=parsed.get("examples", []),
        test_cases=parsed.get("test_cases", []),
        explanation=parsed.get("explanation", "Review problem constraints."),
    )
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return format_challenge_response(ch, is_solved=False)


async def list_challenges(
    db: AsyncSession,

    user: User,
    category: str | None = None,
    difficulty: str | None = None,
    search: str | None = None,
) -> list[CodingChallengeResponse]:
    """List coding challenges filtered by category or difficulty."""
    await seed_standard_challenges_if_empty(db)

    # Get solved challenge IDs for user
    solved_query = select(CodingSubmission.challenge_id).where(
        CodingSubmission.user_id == user.id, CodingSubmission.status == "Passed"
    )
    solved_res = await db.execute(solved_query)
    solved_ids = set(solved_res.scalars().all())

    query = select(CodingChallenge)

    if category and category.strip():
        query = query.where(CodingChallenge.category.ilike(f"%{category.strip()}%"))

    if difficulty and difficulty.strip():
        query = query.where(CodingChallenge.difficulty.ilike(f"%{difficulty.strip()}%"))

    if search and search.strip():
        sp = f"%{search.strip()}%"
        query = query.where(
            CodingChallenge.title.ilike(sp) | CodingChallenge.description.ilike(sp)
        )

    query = query.order_by(CodingChallenge.id.asc())
    res = await db.execute(query)
    challenges = res.scalars().all()

    return [format_challenge_response(ch, is_solved=(ch.id in solved_ids)) for ch in challenges]


async def get_challenge_by_id_or_slug(
    db: AsyncSession, user: User, identifier: str
) -> CodingChallengeResponse:
    """Get single challenge detail by ID or Slug."""
    await seed_standard_challenges_if_empty(db)

    if identifier.isdigit():
        query = select(CodingChallenge).where(CodingChallenge.id == int(identifier))
    else:
        query = select(CodingChallenge).where(CodingChallenge.slug == identifier)

    res = await db.execute(query)
    ch = res.scalar_one_or_none()

    if not ch:
        raise AppException(message="Coding challenge not found.", status_code=404)

    # Check solved status
    solved_res = await db.execute(
        select(CodingSubmission).where(
            CodingSubmission.user_id == user.id,
            CodingSubmission.challenge_id == ch.id,
            CodingSubmission.status == "Passed",
        )
    )
    is_solved = solved_res.scalar_one_or_none() is not None

    return format_challenge_response(ch, is_solved=is_solved)


async def submit_code_solution(
    db: AsyncSession,
    user: User,
    challenge_id: int,
    request: SubmitCodeRequest,
) -> CodingSubmissionResponse:
    """Execute submitted code in sandbox against test cases and record submission results."""
    query = select(CodingChallenge).where(CodingChallenge.id == challenge_id)
    res = await db.execute(query)
    ch = res.scalar_one_or_none()

    if not ch:
        raise AppException(message="Coding challenge not found.", status_code=404)

    # Execute code in safe sandbox (subprocess for Python/DSA, SQLite in-memory for SQL)
    status, passed_count, total_count, total_time_ms, exec_results = execute_code_safely(
        language=request.language or ch.language,
        candidate_code=request.code,
        test_cases=ch.test_cases or [],
        sql_schema=ch.sql_schema,
    )

    err_msg = None
    if status != "Passed":
        failed_res = [r for r in exec_results if not r.passed]
        if failed_res and failed_res[0].error_output:
            err_msg = failed_res[0].error_output

    submission = CodingSubmission(
        user_id=user.id,
        challenge_id=ch.id,
        language=request.language or ch.language,
        code=request.code,
        status=status,
        passed_test_cases=passed_count,
        total_test_cases=total_count,
        execution_time_ms=total_time_ms,
        error_message=err_msg,
    )
    db.add(submission)
    await db.flush()

    res_responses: list[CodingResultResponse] = []
    for r in exec_results:
        cr = CodingResult(
            submission_id=submission.id,
            test_case_index=r.test_case_index,
            passed=r.passed,
            input_data=r.input_data,
            expected_output=r.expected_output,
            actual_output=r.actual_output,
            error_output=r.error_output,
            execution_time_ms=r.execution_time_ms,
        )
        db.add(cr)
        res_responses.append(
            CodingResultResponse(
                test_case_index=r.test_case_index,
                input_data=r.input_data,
                expected_output=r.expected_output,
                passed=r.passed,
                actual_output=r.actual_output,
                error_output=r.error_output,
                execution_time_ms=r.execution_time_ms,
            )
        )

    await db.commit()

    return CodingSubmissionResponse(
        id=submission.id,
        user_id=user.id,
        challenge_id=ch.id,
        language=submission.language,
        code=submission.code,
        status=submission.status,
        passed_test_cases=submission.passed_test_cases,
        total_test_cases=submission.total_test_cases,
        execution_time_ms=submission.execution_time_ms,
        error_message=submission.error_message,
        results=res_responses,
        submitted_at=submission.submitted_at,
    )


async def list_user_submissions(
    db: AsyncSession, user: User, challenge_id: int
) -> list[CodingSubmissionResponse]:
    """Retrieve candidate submission history for a coding challenge."""
    query = (
        select(CodingSubmission)
        .where(CodingSubmission.user_id == user.id, CodingSubmission.challenge_id == challenge_id)
        .order_by(CodingSubmission.submitted_at.desc())
    )
    res = await db.execute(query)
    submissions = res.scalars().all()

    resp_list: list[CodingSubmissionResponse] = []
    for sub in submissions:
        res_schemas = [
            CodingResultResponse(
                test_case_index=r.test_case_index,
                input_data=r.input_data,
                expected_output=r.expected_output,
                passed=r.passed,
                actual_output=r.actual_output,
                error_output=r.error_output,
                execution_time_ms=r.execution_time_ms or 0.0,
            )
            for r in sub.results
        ]

        resp_list.append(
            CodingSubmissionResponse(
                id=sub.id,
                user_id=sub.user_id,
                challenge_id=sub.challenge_id,
                language=sub.language,
                code=sub.code,
                status=sub.status,
                passed_test_cases=sub.passed_test_cases,
                total_test_cases=sub.total_test_cases,
                execution_time_ms=sub.execution_time_ms,
                error_message=sub.error_message,
                results=res_schemas,
                submitted_at=sub.submitted_at,
            )
        )

    return resp_list


AI_CODING_HINT_PROMPT = """You are an expert Coding Coach and Senior Software Architect.
Provide a helpful, constructive hint and explanation for the candidate who is trying to solve the following coding problem:

CHALLENGE TITLE: {title}
CATEGORY: {category}
DIFFICULTY: {difficulty}
PROBLEM DESCRIPTION:
{description}

CANDIDATE'S CURRENT SUBMITTED CODE:
```
{code}
```

INSTRUCTIONS:
1. Provide a constructive hint that guides the candidate on their algorithm/logic without giving away the full code solution.
2. Explain key concepts or edge cases they should consider.

OUTPUT MUST BE VALID JSON matching this exact structure:
{{
  "hint": "Constructive hint focusing on algorithm logic...",
  "explanation": "Detailed explanation of approach, time complexity, or edge cases..."
}}
"""


async def generate_ai_hint(
    db: AsyncSession,
    user: User,
    challenge_id: int,
    code: str,
    ai_provider: AIProvider | None = None,
) -> AIHintResponse:
    """Generate Ollama AI hint and code explanation (Ollama is NOT the authority for test execution)."""
    ch_res = await db.execute(select(CodingChallenge).where(CodingChallenge.id == challenge_id))
    ch = ch_res.scalar_one_or_none()

    if not ch:
        raise AppException(message="Coding challenge not found.", status_code=404)

    provider = ai_provider or get_ai_provider()
    prompt = AI_CODING_HINT_PROMPT.format(
        title=ch.title,
        category=ch.category,
        difficulty=ch.difficulty,
        description=ch.description,
        code=code or ch.starter_code,
    )

    from app.integrations.ai.json_utils import extract_and_parse_json

    try:
        raw_resp = await provider.generate(
            prompt,
            format="json",
            options={"num_predict": 500, "num_ctx": 4096, "temperature": 0.2},
        )
        parsed = extract_and_parse_json(raw_resp) or {}
        return AIHintResponse(
            hint=str(parsed.get("hint", "Analyze the time and space complexity trade-offs.")),
            explanation=str(parsed.get("explanation", "Review the problem constraints, invariants, and edge cases.")),
        )
    except ConnectionError as exc:
        raise AppException(
            message="AI Service (Ollama) is currently unavailable. Ensure Ollama is running.",
            status_code=503,
        ) from exc
    except Exception as exc:
        logger.error("Error generating AI coding hint: %s", exc)
        return AIHintResponse(
            hint="Consider analyzing time and space complexity.",
            explanation="Ensure all sample input test cases and edge cases are handled.",
        )
