# PlacementPilot Resume Analyzer

A full-stack resume analyzer built for placement preparation. The Java backend serves the app and exposes an analysis API. The Python engine extracts skills, compares them with a target role or job description, scores the resume, and returns specific improvement suggestions.

## Why this project is placement-ready

- Java backend with HTTP APIs and static frontend serving.
- Python analysis engine for resume scoring and skill-gap detection.
- Clean separation between product UI, API layer, and intelligence layer.
- No external dependencies required for the MVP, so it is easy to demo.
- Clear upgrade path to Spring Boot, FastAPI, PostgreSQL, authentication, and PDF parsing.

## Architecture

```text
Browser UI
   |
Java API server
   |
Python resume analyzer
```

## Features

- Paste resume text or upload a text resume.
- Optional job description matching.
- Target-role matching when no job description is provided.
- Skill extraction by category.
- Resume score and grade.
- Missing skill detection.
- Section checks for education, skills, projects, experience, and certifications.
- Suggestions based on missing evidence, weak sections, and keyword gaps.

## Run locally

```bash
bash scripts/run-local.sh
```

Then open:

```text
http://localhost:8080
```

Use another port if needed:

```bash
bash scripts/run-local.sh 9090
```

## Run tests

```bash
python3 -m unittest tests/test_analyzer.py
```

## API example

```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  --data '{"resumeText":"Java Python SQL Spring Boot projects internship AWS Docker","jobDescription":"Looking for Java Spring Boot Python SQL Docker AWS developer"}'
```

## Interview explanation

You can describe it like this:

> I built a resume analyzer using a Java API layer and a Python intelligence engine. Java handles the web server, API routing, CORS, and frontend delivery. Python handles resume parsing logic, skill extraction, keyword matching, scoring, and improvement recommendations. The system is structured so it can later be upgraded into Spring Boot and FastAPI microservices with PostgreSQL.

## Future upgrades

- Add Spring Boot, JWT authentication, and user accounts.
- Add FastAPI around the Python analyzer.
- Store resume history in PostgreSQL.
- Add PDF parsing with `pypdf`.
- Add admin dashboard for placement-cell filtering.
- Add Docker Compose for Java, Python, and database services.
