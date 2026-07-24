const apiStatus = document.getElementById("apiStatus");
const analyzeBtn = document.getElementById("analyzeBtn");
const loadSampleBtn = document.getElementById("loadSampleBtn");
const resumeText = document.getElementById("resumeText");
const jobDescription = document.getElementById("jobDescription");
const targetRole = document.getElementById("targetRole");
const resumeFile = document.getElementById("resumeFile");
const errorMessage = document.getElementById("errorMessage");

const sampleResume = `Rishita Sharma
Email: rishita@example.com | GitHub: https://github.com/RISHITASHARMA01 | LinkedIn: https://linkedin.com/in/rishita-sharma-87655b311

Summary
Computer Engineering student interested in full stack development, cybersecurity, and cloud security.

Education
B.Tech Computer Engineering, VIT

Skills
Java, Python, JavaScript, SQL, React, Spring Boot, REST APIs, Git, Linux, Docker, AWS, MySQL, Computer Networks, OOP, DSA

Projects
PlacementPilot Resume Analyzer
Built a Java and Python resume analyzer that extracts skills, compares resumes with job descriptions, and gives improvement suggestions.
Implemented a Java API server and integrated a Python analysis engine for scoring and skill-gap detection.

Cloudflare Zero Trust Lab
Designed a Zero Trust learning lab with Cloudflare tunnels, access policies, and security posture checks.

Experience
Developed academic projects using Java, Python, React, SQL, and Linux tools.
`;

const sampleJob = `We are hiring a Full Stack Developer with Java, Spring Boot, Python, REST APIs, React, SQL, PostgreSQL, Docker, AWS, Git, DSA, OOP, and microservices experience.`;

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) {
      throw new Error("API offline");
    }
    apiStatus.textContent = "API online";
    apiStatus.className = "status-pill online";
  } catch {
    apiStatus.textContent = "API offline";
    apiStatus.className = "status-pill offline";
  }
}

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze resume";
}

function clearError() {
  errorMessage.textContent = "";
}

function showError(message) {
  errorMessage.textContent = message;
}

function renderChips(elementId, values, type = "normal") {
  const element = document.getElementById(elementId);
  element.classList.remove("muted");
  if (!values || values.length === 0) {
    element.classList.add("muted");
    element.textContent = "None found";
    return;
  }
  element.innerHTML = values.map((value) => `<span class="chip ${type}">${escapeHtml(value)}</span>`).join("");
}

function renderDetectedSkills(skillsByCategory) {
  const element = document.getElementById("detectedSkills");
  element.classList.remove("muted");
  const categories = Object.entries(skillsByCategory || {});
  if (categories.length === 0) {
    element.classList.add("muted");
    element.textContent = "No technical skills detected";
    return;
  }

  element.innerHTML = categories
    .map(([category, skills]) => {
      const chips = skills.map((skill) => `<span class="chip">${escapeHtml(skill)}</span>`).join("");
      return `<div class="skill-group"><strong>${escapeHtml(category)}</strong><div class="chip-list">${chips}</div></div>`;
    })
    .join("");
}

function renderSections(sections) {
  const element = document.getElementById("sections");
  element.classList.remove("muted");
  if (!sections || sections.length === 0) {
    element.classList.add("muted");
    element.textContent = "No section data";
    return;
  }
  element.innerHTML = sections
    .map((section) => {
      const mark = section.present ? "Present" : "Missing";
      const className = section.present ? "section-item" : "section-item missing";
      return `<span class="${className}">${escapeHtml(section.name)}: ${mark}</span>`;
    })
    .join("");
}

function renderSuggestions(suggestions) {
  const element = document.getElementById("suggestions");
  element.classList.remove("muted");
  if (!suggestions || suggestions.length === 0) {
    element.classList.add("muted");
    element.innerHTML = "<li>No suggestions</li>";
    return;
  }
  element.innerHTML = suggestions.map((suggestion) => `<li>${escapeHtml(suggestion)}</li>`).join("");
}

function renderResult(result) {
  const score = Number(result.score || 0);
  document.getElementById("scoreRing").style.setProperty("--score", score);
  document.getElementById("scoreValue").textContent = score;
  document.getElementById("gradeValue").textContent = result.grade || "Grade";
  document.getElementById("resultTitle").textContent = result.target?.name || "Analysis complete";
  document.getElementById("resultSummary").textContent = result.summary || "Resume analyzed.";
  document.getElementById("skillCount").textContent = result.stats?.skillCount ?? 0;
  document.getElementById("wordCount").textContent = result.stats?.wordCount ?? 0;
  document.getElementById("actionCount").textContent = result.stats?.actionVerbCount ?? 0;
  document.getElementById("impactCount").textContent = result.stats?.quantifiedImpactCount ?? 0;

  renderChips("matchedSkills", result.matchedSkills);
  renderChips("missingSkills", result.missingSkills, "missing");
  renderDetectedSkills(result.detectedSkills);
  renderSections(result.sections);
  renderSuggestions(result.suggestions);
}

async function analyzeResume() {
  clearError();
  if (!resumeText.value.trim()) {
    showError("Paste resume text or upload a TXT resume.");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        resumeText: resumeText.value,
        jobDescription: jobDescription.value,
        targetRole: targetRole.value,
      }),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.error || "Analysis failed");
    }
    renderResult(result);
  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

resumeFile.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  resumeText.value = await file.text();
});

loadSampleBtn.addEventListener("click", () => {
  resumeText.value = sampleResume;
  jobDescription.value = sampleJob;
  targetRole.value = "Full Stack Java Python Developer";
});

analyzeBtn.addEventListener("click", analyzeResume);
checkHealth();
