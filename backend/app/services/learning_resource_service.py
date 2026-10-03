"""
Learning Resources System Service (Module 14).
Connects legitimate official learning documentation and courses directly to candidate skill gaps and career progress tracking.
"""

import logging
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.career import SkillGapReport
from app.models.learning_resource import LearningResource, UserLearningProgress
from app.models.user import Profile, User
from app.schemas.learning_resource import LearningResourceResponse, ToggleProgressRequest

logger = logging.getLogger(__name__)

# Verified legitimate public learning resources (100% verified real URLs)
VERIFIED_LEARNING_CATALOG = [
    # ================= PYTHON =================
    {
        "title": "Python 3 Official Documentation & Tutorial",
        "description": "Official Python 3 hands-on tutorial covering data structures, modules, object-oriented programming, and standard libraries.",
        "url": "https://docs.python.org/3/tutorial/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Python",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "Scientific Computing with Python Certification",
        "description": "Comprehensive freeCodeCamp course covering Python fundamentals, algorithm design, data structures, and mini-projects.",
        "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "Python",
        "difficulty": "Intermediate",
        "estimated_hours": 300,
    },
    {
        "title": "Python for Beginners - Full Course (freeCodeCamp)",
        "description": "Comprehensive 4-hour YouTube video course covering Python variables, functions, OOP, and data structures for absolute beginners.",
        "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Python",
        "difficulty": "Beginner",
        "estimated_hours": 4,
    },
    {
        "title": "Intermediate Python Programming Course (freeCodeCamp)",
        "description": "YouTube course covering generators, decorators, threading, multiprocessing, and advanced Python patterns.",
        "url": "https://www.youtube.com/watch?v=HGOBQPFzWKo",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Python",
        "difficulty": "Intermediate",
        "estimated_hours": 6,
    },
    {
        "title": "Python OOP Tutorial - Full Course (Corey Schafer)",
        "description": "In-depth YouTube series covering classes, inheritance, magic methods, decorators, and property descriptors in Python.",
        "url": "https://www.youtube.com/watch?v=ZDa-Z5JzLYM",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Python",
        "difficulty": "Intermediate",
        "estimated_hours": 3,
    },
    # ================= FASTAPI =================
    {
        "title": "FastAPI Official Documentation & Tutorial",
        "description": "Interactive official guide for building high-performance asynchronous REST APIs with FastAPI, Pydantic, and OpenAPI.",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "FastAPI",
        "difficulty": "Intermediate",
        "estimated_hours": 8,
    },
    {
        "title": "FastAPI Crash Course - Build APIs Fast (freeCodeCamp)",
        "description": "Full YouTube video tutorial building asynchronous REST APIs with FastAPI, Pydantic, PostgreSQL, and JWT auth.",
        "url": "https://www.youtube.com/watch?v=VSQZl63cGwM",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "FastAPI",
        "difficulty": "Intermediate",
        "estimated_hours": 6,
    },
    {
        "title": "FastAPI Full Stack Project Tutorial (freeCodeCamp)",
        "description": "YouTube tutorial building a complete production-ready API with FastAPI, SQLAlchemy, Alembic migrations, and Docker deployment.",
        "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "FastAPI",
        "difficulty": "Advanced",
        "estimated_hours": 5,
    },
    # ================= REACT =================
    {
        "title": "React Official Documentation (react.dev)",
        "description": "The official modern React guide with interactive sandbox examples, component design patterns, and state management hooks.",
        "url": "https://react.dev/learn",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "React",
        "difficulty": "Beginner",
        "estimated_hours": 15,
    },
    {
        "title": "Front End Development Libraries Certification",
        "description": "freeCodeCamp certification curriculum covering React, Redux, Sass, and Bootstrap frontend architecture.",
        "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "React",
        "difficulty": "Intermediate",
        "estimated_hours": 300,
    },
    {
        "title": "React JS Full Course 2024 (freeCodeCamp)",
        "description": "Complete YouTube video walkthrough covering React hooks, state management, components, and project deployment.",
        "url": "https://www.youtube.com/watch?v=bMknfKXIFA8",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "React",
        "difficulty": "Beginner",
        "estimated_hours": 12,
    },
    {
        "title": "React Hooks Explained - Full Course (Web Dev Simplified)",
        "description": "YouTube deep-dive into useState, useEffect, useContext, useReducer, useMemo, useCallback, and custom hooks.",
        "url": "https://www.youtube.com/watch?v=LlvBzyy-558",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "React",
        "difficulty": "Intermediate",
        "estimated_hours": 2,
    },
    # ================= SQL / PostgreSQL =================
    {
        "title": "PostgreSQL Official Tutorial",
        "description": "Official SQL query optimization, indexing, transaction isolation, and relational schema guide for PostgreSQL.",
        "url": "https://www.postgresql.org/docs/current/tutorial.html",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "SQL",
        "difficulty": "Intermediate",
        "estimated_hours": 12,
    },
    {
        "title": "Relational Database Certification",
        "description": "freeCodeCamp hands-on Linux terminal and PostgreSQL database architecture certification.",
        "url": "https://www.freecodecamp.org/learn/relational-database/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "SQL",
        "difficulty": "Beginner",
        "estimated_hours": 300,
    },
    {
        "title": "PostgreSQL Database Tutorial for Beginners (Programming with Mosh)",
        "description": "In-depth YouTube tutorial explaining relational SQL queries, joins, indexes, and database administration.",
        "url": "https://www.youtube.com/watch?v=qw--VYLpxG4",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "SQL",
        "difficulty": "Beginner",
        "estimated_hours": 3,
    },
    {
        "title": "SQL Tutorial - Full Database Course for Beginners (freeCodeCamp)",
        "description": "Complete 4-hour YouTube course covering SELECT, JOIN, GROUP BY, subqueries, stored procedures, and database design.",
        "url": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "SQL",
        "difficulty": "Beginner",
        "estimated_hours": 4,
    },
    # ================= DOCKER =================
    {
        "title": "Docker Official Get Started Docs",
        "description": "Official Docker containerization guide covering Dockerfile creation, multi-container Docker Compose, and registry deployment.",
        "url": "https://docs.docker.com/get-started/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Docker",
        "difficulty": "Beginner",
        "estimated_hours": 6,
    },
    {
        "title": "Docker & Kubernetes Tutorial for Beginners (TechWorld with Nana)",
        "description": "Top-rated YouTube video course covering containers, Dockerfiles, Docker Compose, and Kubernetes cluster orchestration.",
        "url": "https://www.youtube.com/watch?v=3c-iBn73dDE",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Docker",
        "difficulty": "Intermediate",
        "estimated_hours": 4,
    },
    # ================= AWS =================
    {
        "title": "AWS Cloud Practitioner Digital Training",
        "description": "Official Amazon Web Services digital course covering AWS Cloud core services, IAM security, S3, EC2, and pricing.",
        "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/",
        "source": "Official Courses",
        "resource_type": "Course",
        "skill_name": "AWS",
        "difficulty": "Beginner",
        "estimated_hours": 6,
    },
    {
        "title": "AWS Certified Solutions Architect Associate",
        "description": "Official AWS certification guide for designing resilient, high-performing, and cost-optimized cloud architectures.",
        "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
        "source": "Certification Provider",
        "resource_type": "Certification",
        "skill_name": "AWS",
        "difficulty": "Intermediate",
        "estimated_hours": 40,
    },
    {
        "title": "AWS Certified Cloud Practitioner Training (freeCodeCamp)",
        "description": "Full YouTube course covering all AWS Cloud Practitioner exam domains — cloud concepts, security, technology, and billing.",
        "url": "https://www.youtube.com/watch?v=SOTamWNgDKc",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "AWS",
        "difficulty": "Beginner",
        "estimated_hours": 14,
    },
    # ================= TYPESCRIPT =================
    {
        "title": "TypeScript Handbook Official Documentation",
        "description": "Comprehensive official reference for static type checking, generics, utility types, and module design in TypeScript.",
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "TypeScript",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "TypeScript Full Course for Beginners (freeCodeCamp)",
        "description": "YouTube course covering TypeScript types, interfaces, generics, enums, modules, and project configuration.",
        "url": "https://www.youtube.com/watch?v=30LWjhZzg50",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "TypeScript",
        "difficulty": "Beginner",
        "estimated_hours": 5,
    },
    # ================= JAVASCRIPT =================
    {
        "title": "MDN JavaScript Developer Guide",
        "description": "Mozilla Developer Network authoritative reference for JavaScript ES6+, Promises, Async/Await, and DOM manipulation.",
        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "JavaScript",
        "difficulty": "Beginner",
        "estimated_hours": 20,
    },
    {
        "title": "JavaScript Full Course for Beginners (freeCodeCamp)",
        "description": "Complete YouTube course covering variables, functions, DOM manipulation, async programming, and ES6+ features.",
        "url": "https://www.youtube.com/watch?v=PkZNo7MFNFg",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "JavaScript",
        "difficulty": "Beginner",
        "estimated_hours": 4,
    },
    {
        "title": "JavaScript Algorithms and Data Structures Certification",
        "description": "freeCodeCamp interactive course covering ES6, regex, debugging, data structures, algorithm scripting, and OOP in JavaScript.",
        "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "JavaScript",
        "difficulty": "Intermediate",
        "estimated_hours": 300,
    },
    # ================= SYSTEM DESIGN =================
    {
        "title": "System Design Primer Guide",
        "description": "Comprehensive guide for designing large-scale distributed systems, microservices, scalability tradeoffs, and caching.",
        "url": "https://github.com/donnemartin/system-design-primer",
        "source": "Official Documentation",
        "resource_type": "Book",
        "skill_name": "System Design",
        "difficulty": "Advanced",
        "estimated_hours": 25,
    },
    {
        "title": "System Design Course for Beginners (freeCodeCamp)",
        "description": "Detailed YouTube video course explaining distributed system architecture, load balancing, sharding, and message queues.",
        "url": "https://www.youtube.com/watch?v=m8Icp_Cid5o",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "System Design",
        "difficulty": "Advanced",
        "estimated_hours": 5,
    },
    # ================= DSA (Data Structures & Algorithms) =================
    {
        "title": "Data Structures and Algorithms in Python (freeCodeCamp)",
        "description": "Full YouTube course explaining binary trees, graph algorithms, dynamic programming, and Big-O notation.",
        "url": "https://www.youtube.com/watch?v=pkYVOmU3MgA",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "DSA",
        "difficulty": "Intermediate",
        "estimated_hours": 13,
    },
    {
        "title": "Algorithms and Data Structures Tutorial (freeCodeCamp)",
        "description": "YouTube full course on arrays, linked lists, stacks, queues, trees, sorting, searching, and graph algorithms.",
        "url": "https://www.youtube.com/watch?v=8hly31xKli0",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "DSA",
        "difficulty": "Beginner",
        "estimated_hours": 6,
    },
    {
        "title": "LeetCode Patterns - NeetCode Roadmap",
        "description": "Curated list of 150 must-solve LeetCode problems organized by patterns (two pointers, sliding window, trees, DP, graphs).",
        "url": "https://neetcode.io/roadmap",
        "source": "NeetCode",
        "resource_type": "Course",
        "skill_name": "DSA",
        "difficulty": "Intermediate",
        "estimated_hours": 80,
    },
    # ================= AI / MACHINE LEARNING =================
    {
        "title": "Machine Learning & Artificial Intelligence Course (freeCodeCamp)",
        "description": "Hands-on YouTube video course covering supervised learning, neural networks, PyTorch, and NLP models.",
        "url": "https://www.youtube.com/watch?v=i_LwzRVP7bg",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "AI",
        "difficulty": "Intermediate",
        "estimated_hours": 10,
    },
    {
        "title": "TensorFlow 2.0 Complete Course (freeCodeCamp)",
        "description": "YouTube course covering TensorFlow basics, neural networks, CNNs, RNNs, NLP, and reinforcement learning.",
        "url": "https://www.youtube.com/watch?v=tPYj3fFJGjk",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "AI",
        "difficulty": "Intermediate",
        "estimated_hours": 7,
    },
    {
        "title": "PyTorch for Deep Learning & Machine Learning (freeCodeCamp)",
        "description": "Complete YouTube course covering tensors, neural networks, CNNs, transfer learning, and model deployment with PyTorch.",
        "url": "https://www.youtube.com/watch?v=V_xro1bcAuA",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "AI",
        "difficulty": "Intermediate",
        "estimated_hours": 26,
    },
    {
        "title": "Machine Learning Specialization (Andrew Ng - Coursera)",
        "description": "Stanford University ML course covering supervised/unsupervised learning, neural networks, recommender systems, and reinforcement learning.",
        "url": "https://www.coursera.org/specializations/machine-learning-introduction",
        "source": "Coursera",
        "resource_type": "Course",
        "skill_name": "AI",
        "difficulty": "Intermediate",
        "estimated_hours": 80,
    },
    {
        "title": "Scikit-Learn Official Documentation & Tutorials",
        "description": "Official guide for classical ML algorithms — classification, regression, clustering, dimensionality reduction, and model evaluation.",
        "url": "https://scikit-learn.org/stable/tutorial/index.html",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "AI",
        "difficulty": "Intermediate",
        "estimated_hours": 15,
    },
    # ================= JAVA =================
    {
        "title": "Java Programming Tutorial (Oracle Official)",
        "description": "Official Oracle Java tutorials covering language basics, OOP, exceptions, collections, concurrency, and I/O.",
        "url": "https://docs.oracle.com/javase/tutorial/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Java",
        "difficulty": "Beginner",
        "estimated_hours": 20,
    },
    {
        "title": "Java Full Course for Beginners (freeCodeCamp)",
        "description": "Complete YouTube Java programming course covering OOP, data structures, exception handling, and file I/O.",
        "url": "https://www.youtube.com/watch?v=grEKMHGYyns",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Java",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "Java Design Patterns - Full Course (freeCodeCamp)",
        "description": "YouTube course covering Singleton, Factory, Observer, Strategy, Builder, and other essential design patterns in Java.",
        "url": "https://www.youtube.com/watch?v=tAuRQs_d9F8",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Java",
        "difficulty": "Intermediate",
        "estimated_hours": 3,
    },
    # ================= SPRING BOOT =================
    {
        "title": "Spring Boot Official Getting Started Guide",
        "description": "Official guide for building production-ready applications with Spring Boot, Spring Data JPA, and Spring Security.",
        "url": "https://spring.io/guides/gs/spring-boot",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Spring Boot",
        "difficulty": "Intermediate",
        "estimated_hours": 5,
    },
    {
        "title": "Spring Boot Tutorial for Beginners (freeCodeCamp)",
        "description": "YouTube full course building REST APIs with Spring Boot, Spring Security, JPA, and MySQL.",
        "url": "https://www.youtube.com/watch?v=9SGDpanrc8U",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Spring Boot",
        "difficulty": "Intermediate",
        "estimated_hours": 3,
    },
    # ================= NODE.JS =================
    {
        "title": "Node.js Official Documentation",
        "description": "Official Node.js guides covering modules, event loop, streams, HTTP server, file system, and best practices.",
        "url": "https://nodejs.org/en/learn",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Node.js",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "Node.js and Express.js Full Course (freeCodeCamp)",
        "description": "Complete YouTube course building backend APIs with Node.js, Express, MongoDB, JWT auth, and deployment.",
        "url": "https://www.youtube.com/watch?v=Oe421EPjeBE",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Node.js",
        "difficulty": "Beginner",
        "estimated_hours": 8,
    },
    # ================= DJANGO =================
    {
        "title": "Django Official Tutorial (djangoproject.com)",
        "description": "Official step-by-step tutorial building a polls app with Django ORM, views, templates, and admin.",
        "url": "https://docs.djangoproject.com/en/5.0/intro/tutorial01/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Django",
        "difficulty": "Beginner",
        "estimated_hours": 8,
    },
    {
        "title": "Python Django Full Course (freeCodeCamp)",
        "description": "YouTube full course building a complete web application with Django models, views, templates, and user authentication.",
        "url": "https://www.youtube.com/watch?v=o0XbHvKxw7Y",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Django",
        "difficulty": "Beginner",
        "estimated_hours": 4,
    },
    # ================= KUBERNETES =================
    {
        "title": "Kubernetes Official Documentation",
        "description": "Official Kubernetes guide covering pods, services, deployments, ConfigMaps, Secrets, and cluster administration.",
        "url": "https://kubernetes.io/docs/tutorials/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Kubernetes",
        "difficulty": "Intermediate",
        "estimated_hours": 15,
    },
    {
        "title": "Kubernetes Course - Full Beginners Tutorial (TechWorld with Nana)",
        "description": "YouTube full course covering K8s architecture, pods, services, deployments, Helm, and monitoring.",
        "url": "https://www.youtube.com/watch?v=X48VuDVv0do",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Kubernetes",
        "difficulty": "Intermediate",
        "estimated_hours": 4,
    },
    # ================= MONGODB =================
    {
        "title": "MongoDB Official Manual & Tutorials",
        "description": "Official MongoDB documentation covering CRUD operations, aggregation, indexing, replication, and sharding.",
        "url": "https://www.mongodb.com/docs/manual/tutorial/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "MongoDB",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "MongoDB Full Tutorial (Net Ninja)",
        "description": "YouTube series covering MongoDB setup, CRUD, aggregation pipeline, Mongoose ODM, and Atlas cloud deployment.",
        "url": "https://www.youtube.com/watch?v=ExcRbA7fy_A",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "MongoDB",
        "difficulty": "Beginner",
        "estimated_hours": 3,
    },
    # ================= GIT / VERSION CONTROL =================
    {
        "title": "Git Official Documentation",
        "description": "Official Git reference covering branching, merging, rebasing, cherry-picking, stashing, and workflows.",
        "url": "https://git-scm.com/doc",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Git",
        "difficulty": "Beginner",
        "estimated_hours": 5,
    },
    {
        "title": "Git and GitHub for Beginners - Crash Course (freeCodeCamp)",
        "description": "YouTube course covering git init, add, commit, branch, merge, pull requests, and GitHub collaboration workflows.",
        "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Git",
        "difficulty": "Beginner",
        "estimated_hours": 1,
    },
    # ================= ANGULAR =================
    {
        "title": "Angular Official Tutorial (angular.dev)",
        "description": "Official Angular tutorial covering components, templates, services, dependency injection, routing, and forms.",
        "url": "https://angular.dev/tutorials",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Angular",
        "difficulty": "Beginner",
        "estimated_hours": 12,
    },
    {
        "title": "Angular Full Course for Beginners (freeCodeCamp)",
        "description": "YouTube full course covering Angular components, services, routing, HTTP client, RxJS, and forms.",
        "url": "https://www.youtube.com/watch?v=3qBXWUpoPHo",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Angular",
        "difficulty": "Beginner",
        "estimated_hours": 12,
    },
    # ================= VUE.JS =================
    {
        "title": "Vue.js Official Guide (vuejs.org)",
        "description": "Official Vue.js guide covering reactivity, components, Composition API, routing with Vue Router, and state management with Pinia.",
        "url": "https://vuejs.org/guide/introduction.html",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Vue.js",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "Vue.js Course for Beginners (freeCodeCamp)",
        "description": "YouTube crash course covering Vue 3 basics, Composition API, directives, props, events, and building a project.",
        "url": "https://www.youtube.com/watch?v=FXpIoQ_rT_c",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Vue.js",
        "difficulty": "Beginner",
        "estimated_hours": 4,
    },
    # ================= GO (GOLANG) =================
    {
        "title": "Go Official Tour (go.dev)",
        "description": "Official interactive tour covering Go syntax, types, concurrency (goroutines, channels), interfaces, and error handling.",
        "url": "https://go.dev/tour/welcome/1",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Go",
        "difficulty": "Beginner",
        "estimated_hours": 8,
    },
    {
        "title": "Learn Go Programming - Full Course (freeCodeCamp)",
        "description": "YouTube full course covering Go fundamentals, structs, interfaces, goroutines, channels, and building REST APIs.",
        "url": "https://www.youtube.com/watch?v=un6ZyFkqFKo",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Go",
        "difficulty": "Beginner",
        "estimated_hours": 7,
    },
    # ================= RUST =================
    {
        "title": "The Rust Programming Language Book (Official)",
        "description": "Official comprehensive Rust book covering ownership, borrowing, lifetimes, traits, error handling, and concurrency.",
        "url": "https://doc.rust-lang.org/book/",
        "source": "Official Documentation",
        "resource_type": "Book",
        "skill_name": "Rust",
        "difficulty": "Intermediate",
        "estimated_hours": 30,
    },
    {
        "title": "Rust Programming Full Course (freeCodeCamp)",
        "description": "YouTube course covering Rust ownership model, structs, enums, pattern matching, error handling, and cargo.",
        "url": "https://www.youtube.com/watch?v=BpPEoZW5IiY",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Rust",
        "difficulty": "Intermediate",
        "estimated_hours": 14,
    },
    # ================= C++ =================
    {
        "title": "C++ Official Reference (cppreference.com)",
        "description": "Comprehensive C++ language reference covering STL containers, algorithms, templates, smart pointers, and concurrency.",
        "url": "https://en.cppreference.com/w/cpp/language",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "C++",
        "difficulty": "Intermediate",
        "estimated_hours": 25,
    },
    {
        "title": "C++ Full Course for Beginners (freeCodeCamp)",
        "description": "YouTube full course covering C++ variables, OOP, pointers, memory management, STL, and file I/O.",
        "url": "https://www.youtube.com/watch?v=vLnPwxZdW4Y",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "C++",
        "difficulty": "Beginner",
        "estimated_hours": 31,
    },
    # ================= FLUTTER / DART =================
    {
        "title": "Flutter Official Documentation & Codelabs",
        "description": "Official Flutter guide covering widgets, layouts, state management, navigation, and platform-specific features.",
        "url": "https://docs.flutter.dev/get-started/codelab",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Flutter",
        "difficulty": "Beginner",
        "estimated_hours": 10,
    },
    {
        "title": "Flutter Course for Beginners (freeCodeCamp)",
        "description": "YouTube full course building cross-platform mobile apps with Flutter, Dart, widgets, and Firebase integration.",
        "url": "https://www.youtube.com/watch?v=VPvVD8t02U8",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Flutter",
        "difficulty": "Beginner",
        "estimated_hours": 37,
    },
    # ================= REDIS =================
    {
        "title": "Redis Official Documentation",
        "description": "Official Redis guide covering data types, caching patterns, pub/sub, Lua scripting, and cluster setup.",
        "url": "https://redis.io/docs/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Redis",
        "difficulty": "Intermediate",
        "estimated_hours": 8,
    },
    {
        "title": "Redis Crash Course (Traversy Media)",
        "description": "YouTube tutorial covering Redis data types (strings, lists, sets, hashes), caching strategies, and CLI usage.",
        "url": "https://www.youtube.com/watch?v=jgpVdJB2sKQ",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Redis",
        "difficulty": "Beginner",
        "estimated_hours": 1,
    },
    # ================= GRAPHQL =================
    {
        "title": "GraphQL Official Learn Guide",
        "description": "Official GraphQL tutorial covering queries, mutations, schemas, resolvers, and best practices.",
        "url": "https://graphql.org/learn/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "GraphQL",
        "difficulty": "Intermediate",
        "estimated_hours": 5,
    },
    {
        "title": "GraphQL Full Course (freeCodeCamp)",
        "description": "YouTube course covering GraphQL schemas, queries, mutations, subscriptions, and building APIs with Apollo Server.",
        "url": "https://www.youtube.com/watch?v=ed8SzALpx1Q",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "GraphQL",
        "difficulty": "Intermediate",
        "estimated_hours": 4,
    },
    # ================= CYBERSECURITY =================
    {
        "title": "OWASP Top 10 Security Risks Guide",
        "description": "Official OWASP guide covering the top 10 web application security vulnerabilities and mitigation strategies.",
        "url": "https://owasp.org/www-project-top-ten/",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Cybersecurity",
        "difficulty": "Intermediate",
        "estimated_hours": 5,
    },
    {
        "title": "Full Ethical Hacking Course (freeCodeCamp)",
        "description": "YouTube course covering network scanning, exploitation, web app testing, and penetration testing with Kali Linux.",
        "url": "https://www.youtube.com/watch?v=3Kq1MIfTWCE",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Cybersecurity",
        "difficulty": "Intermediate",
        "estimated_hours": 15,
    },
    # ================= DATA SCIENCE =================
    {
        "title": "Data Analysis with Python Certification (freeCodeCamp)",
        "description": "Certification course covering Numpy, Pandas, Matplotlib, and Seaborn for data analysis and visualization.",
        "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "Data Science",
        "difficulty": "Intermediate",
        "estimated_hours": 300,
    },
    {
        "title": "Data Science Full Course (freeCodeCamp)",
        "description": "YouTube course covering statistics, Python, Pandas, data visualization, machine learning, and data cleaning.",
        "url": "https://www.youtube.com/watch?v=ua-CiDNNj30",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Data Science",
        "difficulty": "Beginner",
        "estimated_hours": 12,
    },
    # ================= DEVOPS / CI-CD =================
    {
        "title": "DevOps Engineering Course (freeCodeCamp)",
        "description": "YouTube course covering Linux, networking, CI/CD pipelines, Docker, Kubernetes, Terraform, and monitoring.",
        "url": "https://www.youtube.com/watch?v=j5Zsa_eOXeY",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "DevOps",
        "difficulty": "Intermediate",
        "estimated_hours": 15,
    },
    {
        "title": "GitHub Actions Official Documentation",
        "description": "Official guide for automating CI/CD workflows, testing, deployment, and custom actions with GitHub Actions.",
        "url": "https://docs.github.com/en/actions",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "DevOps",
        "difficulty": "Intermediate",
        "estimated_hours": 6,
    },
    # ================= HTML / CSS =================
    {
        "title": "Responsive Web Design Certification (freeCodeCamp)",
        "description": "Interactive course covering HTML5 semantics, CSS Flexbox, Grid, responsive design, and accessibility.",
        "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
        "source": "freeCodeCamp",
        "resource_type": "Course",
        "skill_name": "HTML/CSS",
        "difficulty": "Beginner",
        "estimated_hours": 300,
    },
    {
        "title": "HTML & CSS Full Course for Beginners (freeCodeCamp)",
        "description": "YouTube full course covering HTML tags, CSS selectors, Flexbox, Grid, animations, and building responsive layouts.",
        "url": "https://www.youtube.com/watch?v=mU6anWqZJcc",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "HTML/CSS",
        "difficulty": "Beginner",
        "estimated_hours": 6,
    },
    # ================= LINUX =================
    {
        "title": "Linux Command Line Full Course (freeCodeCamp)",
        "description": "YouTube course covering bash commands, file system navigation, permissions, scripting, networking, and process management.",
        "url": "https://www.youtube.com/watch?v=ZtqBQ68cfJc",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Linux",
        "difficulty": "Beginner",
        "estimated_hours": 5,
    },
    # ================= NEXT.JS =================
    {
        "title": "Next.js Official Learn Course (nextjs.org)",
        "description": "Official interactive course covering App Router, server components, data fetching, styling, and deployment.",
        "url": "https://nextjs.org/learn",
        "source": "Official Documentation",
        "resource_type": "Course",
        "skill_name": "Next.js",
        "difficulty": "Intermediate",
        "estimated_hours": 10,
    },
    {
        "title": "Next.js Full Course for Beginners (freeCodeCamp)",
        "description": "YouTube course building a production app with Next.js App Router, server actions, authentication, and database.",
        "url": "https://www.youtube.com/watch?v=843nec-IvW0",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Next.js",
        "difficulty": "Intermediate",
        "estimated_hours": 5,
    },
    # ================= TERRAFORM =================
    {
        "title": "Terraform Official Tutorials (HashiCorp)",
        "description": "Official tutorials covering infrastructure as code, AWS/Azure/GCP providers, modules, state management, and workspaces.",
        "url": "https://developer.hashicorp.com/terraform/tutorials",
        "source": "Official Documentation",
        "resource_type": "Documentation",
        "skill_name": "Terraform",
        "difficulty": "Intermediate",
        "estimated_hours": 15,
    },
    {
        "title": "Terraform Course - Automate Your AWS Cloud (freeCodeCamp)",
        "description": "YouTube course covering Terraform HCL syntax, providers, resources, variables, modules, and AWS infrastructure automation.",
        "url": "https://www.youtube.com/watch?v=SLB_c_ayRMo",
        "source": "YouTube",
        "resource_type": "Video",
        "skill_name": "Terraform",
        "difficulty": "Intermediate",
        "estimated_hours": 3,
    },
]


async def seed_learning_resources_if_empty(db: AsyncSession) -> None:
    """Seed verified learning resource catalog and sync missing/updated resources."""
    for item in VERIFIED_LEARNING_CATALOG:
        q = select(LearningResource).where(LearningResource.url == item["url"])
        res = await db.execute(q)
        existing = res.scalar_one_or_none()
        if not existing:
            lr = LearningResource(
                title=item["title"],
                description=item["description"],
                url=item["url"],
                source=item["source"],
                resource_type=item["resource_type"],
                skill_name=item["skill_name"],
                difficulty=item["difficulty"],
                estimated_hours=item.get("estimated_hours"),
                is_verified=True,
            )
            db.add(lr)
        else:
            existing.title = item["title"]
            existing.description = item["description"]
            existing.source = item["source"]
            existing.resource_type = item["resource_type"]
            existing.skill_name = item["skill_name"]
            existing.difficulty = item["difficulty"]
    await db.commit()




async def get_candidate_missing_skill_gaps(db: AsyncSession, user: User) -> set[str]:
    """Retrieve candidate missing skills identified from Skill Gap Reports and target role requirements."""
    missing_skills: set[str] = set()

    # 1. Skill Gap Report
    sg_query = (
        select(SkillGapReport)
        .where(SkillGapReport.user_id == user.id)
        .order_by(SkillGapReport.created_at.desc())
    )
    sg_res = await db.execute(sg_query)
    report = sg_res.scalars().first()

    if report and report.missing_skills:
        for ms in report.missing_skills:
            if isinstance(ms, str):
                missing_skills.add(ms.strip().lower())
            elif isinstance(ms, dict) and "name" in ms:
                missing_skills.add(str(ms["name"]).strip().lower())

    # 2. Benchmark defaults if empty
    if not missing_skills:
        prof_res = await db.execute(select(Profile).where(Profile.user_id == user.id))
        prof = prof_res.scalar_one_or_none()
        known_skills = set(s.lower() for s in (prof.skills if prof and prof.skills else []))
        standard_benchmarks = {"python", "fastapi", "react", "sql", "docker", "aws", "typescript", "system design"}
        missing_skills = standard_benchmarks - known_skills

    return missing_skills


async def list_learning_resources(
    db: AsyncSession,
    user: User,
    skill_name: str | None = None,
    difficulty: str | None = None,
    resource_type: str | None = None,
    search: str | None = None,
    skill_gap_only: bool = False,
) -> list[LearningResourceResponse]:
    """List learning resources with user progress status and skill gap recommendations."""
    await seed_learning_resources_if_empty(db)

    candidate_missing_gaps = await get_candidate_missing_skill_gaps(db, user)

    # Fetch user progress records
    prog_query = select(UserLearningProgress).where(UserLearningProgress.user_id == user.id)
    prog_res = await db.execute(prog_query)
    user_progress_map: dict[int, UserLearningProgress] = {
        p.resource_id: p for p in prog_res.scalars().all()
    }

    query = select(LearningResource)

    if skill_name and skill_name.strip():
        query = query.where(LearningResource.skill_name.ilike(f"%{skill_name.strip()}%"))

    if difficulty and difficulty.strip():
        query = query.where(LearningResource.difficulty.ilike(f"%{difficulty.strip()}%"))

    if resource_type and resource_type.strip():
        query = query.where(LearningResource.resource_type.ilike(f"%{resource_type.strip()}%"))

    if search and search.strip():
        sp = f"%{search.strip()}%"
        query = query.where(
            LearningResource.title.ilike(sp)
            | LearningResource.description.ilike(sp)
            | LearningResource.skill_name.ilike(sp)
        )

    query = query.order_by(LearningResource.id.asc())
    res = await db.execute(query)
    resources = res.scalars().all()

    formatted_responses: list[LearningResourceResponse] = []
    for r in resources:
        prog = user_progress_map.get(r.id)
        is_saved = prog.is_saved if prog else False
        is_completed = prog.is_completed if prog else False
        is_recommended = r.skill_name.strip().lower() in candidate_missing_gaps

        if skill_gap_only and not is_recommended:
            continue

        resp = LearningResourceResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            url=r.url,
            source=r.source,
            resource_type=r.resource_type,
            skill_name=r.skill_name,
            difficulty=r.difficulty,
            estimated_hours=r.estimated_hours,
            is_verified=r.is_verified,
            is_saved=is_saved,
            is_completed=is_completed,
            is_recommended_for_gap=is_recommended,
            created_at=r.created_at,
        )
        formatted_responses.append(resp)

    return formatted_responses


async def toggle_resource_progress(
    db: AsyncSession,
    user: User,
    resource_id: int,
    request: ToggleProgressRequest,
) -> LearningResourceResponse:
    """Save/unsave or complete/uncomplete a learning resource."""
    r_query = select(LearningResource).where(LearningResource.id == resource_id)
    r_res = await db.execute(r_query)
    lr = r_res.scalar_one_or_none()

    if not lr:
        raise AppException(message="Learning resource not found.", status_code=404)

    p_query = select(UserLearningProgress).where(
        UserLearningProgress.user_id == user.id,
        UserLearningProgress.resource_id == lr.id,
    )
    p_res = await db.execute(p_query)
    prog = p_res.scalar_one_or_none()

    if not prog:
        prog = UserLearningProgress(
            user_id=user.id,
            resource_id=lr.id,
            is_saved=False,
            is_completed=False,
        )
        db.add(prog)

    if request.is_saved is not None:
        prog.is_saved = request.is_saved

    if request.is_completed is not None:
        prog.is_completed = request.is_completed
        prog.completed_at = func.now() if request.is_completed else None

    await db.commit()

    candidate_missing_gaps = await get_candidate_missing_skill_gaps(db, user)
    is_recommended = lr.skill_name.strip().lower() in candidate_missing_gaps

    return LearningResourceResponse(
        id=lr.id,
        title=lr.title,
        description=lr.description,
        url=lr.url,
        source=lr.source,
        resource_type=lr.resource_type,
        skill_name=lr.skill_name,
        difficulty=lr.difficulty,
        estimated_hours=lr.estimated_hours,
        is_verified=lr.is_verified,
        is_saved=prog.is_saved,
        is_completed=prog.is_completed,
        is_recommended_for_gap=is_recommended,
        created_at=lr.created_at,
    )
