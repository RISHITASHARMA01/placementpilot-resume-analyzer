import json
import re
import sys
from typing import Dict, Iterable, List, Set, Tuple


SKILLS: Dict[str, Dict[str, List[str]]] = {
    "Programming": {
        "Java": ["java", "core java"],
        "Python": ["python"],
        "JavaScript": ["javascript", "js"],
        "TypeScript": ["typescript", "ts"],
        "C++": ["c++", "cpp"],
        "SQL": ["sql"],
    },
    "Backend": {
        "Spring Boot": ["spring boot", "springboot", "spring"],
        "REST APIs": ["rest api", "rest apis", "restful api", "rest"],
        "FastAPI": ["fastapi", "fast api"],
        "Flask": ["flask"],
        "Node.js": ["node.js", "nodejs", "node js"],
        "JWT": ["jwt", "json web token"],
        "Microservices": ["microservices", "microservice"],
    },
    "Frontend": {
        "React": ["react", "react.js", "reactjs"],
        "HTML": ["html", "html5"],
        "CSS": ["css", "css3"],
        "Tailwind CSS": ["tailwind", "tailwind css"],
    },
    "Database": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql"],
        "MongoDB": ["mongodb", "mongo db"],
        "Redis": ["redis"],
    },
    "Cloud and DevOps": {
        "Docker": ["docker", "containerization", "container"],
        "Git": ["git"],
        "GitHub Actions": ["github actions", "ci/cd", "cicd"],
        "AWS": ["aws", "amazon web services"],
        "Linux": ["linux", "ubuntu"],
        "Cloudflare": ["cloudflare"],
    },
    "Cybersecurity": {
        "OWASP": ["owasp"],
        "SOC": ["soc", "security operations center"],
        "Threat Detection": ["threat detection"],
        "Zero Trust": ["zero trust"],
        "Nmap": ["nmap"],
        "Wireshark": ["wireshark"],
    },
    "CS Fundamentals": {
        "DSA": ["dsa", "data structures", "algorithms"],
        "OOP": ["oop", "object oriented programming", "object-oriented"],
        "DBMS": ["dbms", "database management"],
        "Operating Systems": ["operating systems", "os"],
        "Computer Networks": ["computer networks", "networking", "cn"],
    },
}

ROLE_PROFILES: Dict[str, List[str]] = {
    "Full Stack Java Python Developer": [
        "Java",
        "Python",
        "Spring Boot",
        "FastAPI",
        "REST APIs",
        "React",
        "SQL",
        "PostgreSQL",
        "Docker",
        "Git",
        "DSA",
        "OOP",
    ],
    "Cybersecurity Analyst": [
        "Python",
        "Linux",
        "SOC",
        "Threat Detection",
        "OWASP",
        "Nmap",
        "Wireshark",
        "Computer Networks",
        "Zero Trust",
        "Git",
    ],
    "Backend Developer": [
        "Java",
        "Python",
        "Spring Boot",
        "FastAPI",
        "REST APIs",
        "SQL",
        "PostgreSQL",
        "Docker",
        "Microservices",
        "JWT",
    ],
}

ACTION_VERBS = {
    "built",
    "designed",
    "developed",
    "implemented",
    "deployed",
    "optimized",
    "automated",
    "integrated",
    "created",
    "secured",
    "analyzed",
    "reduced",
    "improved",
    "led",
    "tested",
}

SECTION_PATTERNS = {
    "Contact": r"(@|linkedin|github|phone|email|\+?\d[\d\s-]{8,})",
    "Summary": r"\b(summary|profile|objective)\b",
    "Skills": r"\b(skills|technical skills|tech stack|technologies)\b",
    "Projects": r"\b(projects|project experience|academic projects)\b",
    "Experience": r"\b(experience|internship|work experience|employment)\b",
    "Education": r"\b(education|degree|university|college|bachelor|b\.tech|btech)\b",
    "Certifications": r"\b(certifications|certificates|certified)\b",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def term_exists(text: str, term: str) -> bool:
    escaped = re.escape(term.lower())
    pattern = rf"(?<![a-z0-9+#.]){escaped}(?![a-z0-9+#.])"
    return re.search(pattern, text) is not None


def detect_skills(text: str) -> Tuple[Dict[str, List[str]], Set[str]]:
    normalized = normalize(text)
    by_category: Dict[str, List[str]] = {}
    detected: Set[str] = set()

    for category, skills in SKILLS.items():
        matches = []
        for skill, aliases in skills.items():
            if any(term_exists(normalized, alias) for alias in aliases):
                matches.append(skill)
                detected.add(skill)
        if matches:
            by_category[category] = sorted(matches)

    return by_category, detected


def choose_role(target_role: str) -> str:
    normalized = normalize(target_role)
    if "cyber" in normalized or "security" in normalized or "soc" in normalized:
        return "Cybersecurity Analyst"
    if "backend" in normalized:
        return "Backend Developer"
    return "Full Stack Java Python Developer"


def target_skills(job_description: str, target_role: str) -> Tuple[str, Set[str], str]:
    _, job_skills = detect_skills(job_description)
    if len(job_description.strip()) > 40 and job_skills:
        return "Custom Job Description", job_skills, "job-description"

    role = choose_role(target_role)
    return role, set(ROLE_PROFILES[role]), "role-profile"


def section_presence(text: str) -> Dict[str, bool]:
    normalized = normalize(text)
    return {
        section: re.search(pattern, normalized, re.IGNORECASE) is not None
        for section, pattern in SECTION_PATTERNS.items()
    }


def count_action_verbs(text: str) -> int:
    words = set(re.findall(r"\b[a-z]+\b", normalize(text)))
    return len(words.intersection(ACTION_VERBS))


def count_quantified_impacts(text: str) -> int:
    percentage_count = len(re.findall(r"\b\d+(\.\d+)?\s?%", text))
    numeric_impact_count = len(
        re.findall(
            r"\b(reduced|improved|increased|optimized|saved|handled|processed|served)\s+\w*\s*\d+",
            normalize(text),
        )
    )
    return percentage_count + numeric_impact_count


def contact_quality(text: str) -> Dict[str, bool]:
    normalized = normalize(text)
    return {
        "email": re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text) is not None,
        "phone": re.search(r"(\+?\d[\d\s-]{8,})", text) is not None,
        "linkedin": "linkedin.com" in normalized,
        "github": "github.com" in normalized,
    }


def grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "Needs Work"


def build_strengths(
    detected: Set[str],
    matched: Set[str],
    sections: Dict[str, bool],
    contacts: Dict[str, bool],
    quantified_impacts: int,
) -> List[str]:
    strengths = []
    if detected:
        strengths.append(f"Detected {len(detected)} technical skills across the resume.")
    if matched:
        strengths.append(f"Matched {len(matched)} skills from the target requirement.")
    if sections.get("Projects"):
        strengths.append("Project section is present, which helps fresher resumes stand out.")
    if sections.get("Experience"):
        strengths.append("Experience or internship section is present.")
    if contacts.get("github") or contacts.get("linkedin"):
        strengths.append("Professional profile links are included.")
    if quantified_impacts:
        strengths.append("Some measurable impact is included.")
    return strengths or ["The resume has enough text to begin analysis."]


def build_suggestions(
    missing: Iterable[str],
    sections: Dict[str, bool],
    contacts: Dict[str, bool],
    action_verbs: int,
    quantified_impacts: int,
    word_count: int,
    source: str,
) -> List[str]:
    suggestions: List[str] = []
    missing_list = list(missing)

    if missing_list:
        suggestions.append("Add evidence for these target skills if you have used them: " + ", ".join(missing_list[:8]) + ".")
    if not sections.get("Projects"):
        suggestions.append("Add a Projects section with problem statement, tech stack, features, and outcome.")
    if not sections.get("Skills"):
        suggestions.append("Add a dedicated Skills section grouped by languages, backend, database, tools, and cloud.")
    if not sections.get("Education"):
        suggestions.append("Add Education with degree, college, graduation year, and relevant coursework.")
    if not sections.get("Experience"):
        suggestions.append("Add internships, open-source work, freelancing, or strong academic projects if formal experience is not available.")
    if not contacts.get("github"):
        suggestions.append("Add a GitHub link so recruiters can verify your projects.")
    if not contacts.get("linkedin"):
        suggestions.append("Add a LinkedIn link for recruiter follow-up.")
    if action_verbs < 4:
        suggestions.append("Start bullet points with action verbs like built, implemented, optimized, deployed, or automated.")
    if quantified_impacts < 2:
        suggestions.append("Add numbers where possible, such as users served, latency reduced, files processed, or accuracy improved.")
    if word_count < 220:
        suggestions.append("The resume looks short; add more project depth, responsibilities, and measurable outcomes.")
    if source == "role-profile":
        suggestions.append("Paste a real job description for sharper keyword matching before applying.")

    return suggestions[:10]


def analyze(payload: Dict[str, str]) -> Dict[str, object]:
    resume_text = str(payload.get("resumeText") or payload.get("resume") or "").strip()
    job_description = str(payload.get("jobDescription") or "").strip()
    target_role_input = str(payload.get("targetRole") or "").strip()

    if not resume_text:
        return {
            "ok": False,
            "error": "Resume text is required.",
        }

    detected_by_category, detected = detect_skills(resume_text)
    role, required_skills, source = target_skills(job_description, target_role_input)
    matched = detected.intersection(required_skills)
    missing = required_skills.difference(detected)
    sections = section_presence(resume_text)
    contacts = contact_quality(resume_text)
    word_count = len(re.findall(r"\b\w+\b", resume_text))
    action_verbs = count_action_verbs(resume_text)
    quantified_impacts = count_quantified_impacts(resume_text)

    skill_score = (len(matched) / len(required_skills)) * 45 if required_skills else 0
    important_sections = ["Contact", "Skills", "Projects", "Education"]
    section_score = (sum(1 for section in important_sections if sections.get(section)) / len(important_sections)) * 20
    evidence_score = min(action_verbs / 8, 1) * 7 + min(quantified_impacts / 4, 1) * 8
    depth_score = min(len(detected) / 12, 1) * 6 + min(word_count / 450, 1) * 4
    contact_score = (sum(1 for present in contacts.values() if present) / len(contacts)) * 10
    score = int(round(skill_score + section_score + evidence_score + depth_score + contact_score))

    sorted_missing = sorted(missing)
    sorted_matched = sorted(matched)

    return {
        "ok": True,
        "score": score,
        "grade": grade(score),
        "target": {
            "name": role,
            "source": source,
            "requiredSkillCount": len(required_skills),
        },
        "summary": f"Matched {len(matched)} of {len(required_skills)} target skills for {role}.",
        "detectedSkills": detected_by_category,
        "matchedSkills": sorted_matched,
        "missingSkills": sorted_missing,
        "sections": [{"name": name, "present": present} for name, present in sections.items()],
        "contacts": contacts,
        "stats": {
            "wordCount": word_count,
            "skillCount": len(detected),
            "actionVerbCount": action_verbs,
            "quantifiedImpactCount": quantified_impacts,
        },
        "strengths": build_strengths(detected, matched, sections, contacts, quantified_impacts),
        "suggestions": build_suggestions(
            sorted_missing,
            sections,
            contacts,
            action_verbs,
            quantified_impacts,
            word_count,
            source,
        ),
    }


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        result = analyze(payload)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": f"Invalid JSON: {exc}"}))
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
